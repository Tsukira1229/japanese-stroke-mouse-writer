from __future__ import annotations

import argparse
import runpy
import tempfile
import time
import tkinter as tk
import sys
from pathlib import Path

from PIL import ImageGrab

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from appearance import AppearanceMode
from localization import LANGUAGE_OPTIONS, Language


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", choices=[item.value for item in Language], required=True)
    parser.add_argument("--theme", choices=[AppearanceMode.LIGHT.value, AppearanceMode.DARK.value], required=True)
    parser.add_argument("--size", choices=["1000x700", "maximized"], required=True)
    parser.add_argument("--tab", type=int, choices=range(4), default=0)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    namespace = runpy.run_path(ROOT / "mouse_writer_ui.pyw", run_name="ui_preview_capture")
    app_type = namespace["JapaneseWriterApp"]
    language = Language(args.language)
    appearance = AppearanceMode(args.theme)

    with tempfile.TemporaryDirectory(prefix="jsmw-ui-preview-") as temporary:
        root = tk.Tk()
        app = app_type(root, Path(temporary) / "user_data" / "settings.json")
        if app.maximize_after_id:
            root.after_cancel(app.maximize_after_id)
            app.maximize_after_id = None

        app.language_selection.set(dict(LANGUAGE_OPTIONS)[language])
        app._language_selected()
        appearance_label = next(label for label, value in app._appearance_labels().items() if value is appearance)
        app.appearance_selection.set(appearance_label)
        app._appearance_selected()
        app.text_input.delete("1.0", "end")
        app.text_input.insert("1.0", "日本語 ABCＡＢＣ 123１２３ ☆\n┏━┷━┓\n┃　　┃\n┗━━━┛")
        app.refresh_preview()
        app.notebook.select(args.tab)

        if args.size == "maximized":
            root.state("zoomed")
        else:
            root.state("normal")
            root.geometry("1000x700+80+40")
        root.attributes("-topmost", True)
        root.deiconify()
        root.lift()
        root.focus_force()

        deadline = time.time() + 20
        while time.time() < deadline:
            root.update()
            if app.current_layout is not None and not app.status.get().endswith("..."):
                break
            time.sleep(0.04)
        root.update()
        time.sleep(0.2)

        x = root.winfo_rootx()
        y = root.winfo_rooty()
        width = root.winfo_width()
        height = root.winfo_height()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        ImageGrab.grab((x, y, x + width, y + height), all_screens=True).save(args.output)

        app.closing = True
        app.cancel_scheduled_callbacks()
        root.destroy()


if __name__ == "__main__":
    main()
