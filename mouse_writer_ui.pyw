# -*- coding: utf-8 -*-
"""Tkinter interface for the Japanese stroke-order mouse writer."""

from __future__ import annotations

import math
import queue
import tempfile
import threading
import time
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import messagebox, ttk

from mouse_writer_pro import (
    APP_VERSION,
    DEFAULT_KANJIVG_DIR,
    BuildResult,
    DrawSettings,
    build_paths,
    draw_with_mouse,
    path_stats,
    preview_paths,
)


class JapaneseWriterApp:
    BACKGROUND = "#f3f5f7"
    SURFACE = "#ffffff"
    TEXT = "#17212b"
    MUTED = "#5d6875"
    BORDER = "#d8dee5"
    PRIMARY = "#176b87"
    PRIMARY_ACTIVE = "#12566d"
    ACCENT = "#b4512f"

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.busy = False
        self.preview_image: tk.PhotoImage | None = None
        self.ui_events: queue.Queue[
            tuple[Callable[..., None], tuple[object, ...]]
        ] = queue.Queue()

        root.title(f"日文筆順書寫工具 V{APP_VERSION}")
        root.geometry("1120x800")
        root.minsize(980, 720)
        root.configure(background=self.BACKGROUND)
        root.protocol("WM_DELETE_WINDOW", self.on_close)

        self._configure_styles()
        self._create_variables()
        self._build_layout()
        self.root.after(40, self._drain_ui_events)
        self.root.after(150, self.generate_preview)

    def _post_ui(self, callback: Callable[..., None], *args: object) -> None:
        self.ui_events.put((callback, args))

    def _drain_ui_events(self) -> None:
        while True:
            try:
                callback, args = self.ui_events.get_nowait()
            except queue.Empty:
                break
            callback(*args)
        self.root.after(40, self._drain_ui_events)

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("App.TFrame", background=self.BACKGROUND)
        style.configure("Surface.TFrame", background=self.SURFACE)
        style.configure(
            "Title.TLabel",
            background=self.BACKGROUND,
            foreground=self.TEXT,
            font=("Microsoft JhengHei UI", 19, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background=self.BACKGROUND,
            foreground=self.MUTED,
            font=("Microsoft JhengHei UI", 10),
        )
        style.configure(
            "Section.TLabel",
            background=self.SURFACE,
            foreground=self.TEXT,
            font=("Microsoft JhengHei UI", 11, "bold"),
        )
        style.configure(
            "Field.TLabel",
            background=self.SURFACE,
            foreground=self.MUTED,
            font=("Microsoft JhengHei UI", 9),
        )
        style.configure(
            "Status.TLabel",
            background=self.SURFACE,
            foreground=self.MUTED,
            font=("Microsoft JhengHei UI", 9),
        )
        style.configure(
            "Primary.TButton",
            background=self.PRIMARY,
            foreground="white",
            borderwidth=0,
            padding=(18, 10),
            font=("Microsoft JhengHei UI", 10, "bold"),
        )
        style.map(
            "Primary.TButton",
            background=[("active", self.PRIMARY_ACTIVE), ("disabled", "#9caab2")],
        )
        style.configure(
            "Secondary.TButton",
            background="#e9eef1",
            foreground=self.TEXT,
            borderwidth=0,
            padding=(14, 9),
            font=("Microsoft JhengHei UI", 10),
        )
        style.map("Secondary.TButton", background=[("active", "#dce5e9")])
        style.configure("TEntry", padding=7, fieldbackground="#fbfcfd")
        style.configure("TSpinbox", padding=6, fieldbackground="#fbfcfd")

    def _create_variables(self) -> None:
        self.start_x = tk.StringVar(value="877")
        self.start_y = tk.StringVar(value="325")
        self.char_width = tk.StringVar(value="150")
        self.char_height = tk.StringVar(value="150")
        self.char_gap = tk.StringVar(value="12")
        self.line_gap = tk.StringVar(value="24")
        self.countdown = tk.StringVar(value="5")
        self.point_delay = tk.StringVar(value="0.008")
        self.stroke_delay = tk.StringVar(value="0.03")
        self.sample_spacing = tk.StringVar(value="2.0")
        self.status = tk.StringVar(value="準備就緒")
        self.summary = tk.StringVar(value="")

    def _build_layout(self) -> None:
        outer = ttk.Frame(self.root, style="App.TFrame", padding=(22, 10, 22, 8))
        outer.pack(fill="both", expand=True)

        header = ttk.Frame(outer, style="App.TFrame")
        header.pack(fill="x", pady=(0, 12))
        ttk.Label(header, text="日文筆順書寫工具", style="Title.TLabel").pack(side="left")
        ttk.Label(
            header,
            text=f"V{APP_VERSION}  ·  平假名 / 片假名 / 漢字",
            style="Subtitle.TLabel",
        ).pack(side="left", padx=(14, 0), pady=(8, 0))

        body = ttk.Frame(outer, style="App.TFrame")
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, minsize=390)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        controls = ttk.Frame(body, style="Surface.TFrame", padding=16)
        controls.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        preview = ttk.Frame(body, style="Surface.TFrame", padding=20)
        preview.grid(row=0, column=1, sticky="nsew")

        self._build_controls(controls)
        self._build_preview(preview)

    def _build_controls(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)

        ttk.Label(parent, text="書寫文字", style="Section.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        self.text_input = tk.Text(
            parent,
            width=1,
            height=2,
            wrap="word",
            relief="solid",
            borderwidth=1,
            highlightthickness=0,
            font=("Yu Gothic UI", 15),
            foreground=self.TEXT,
            background="#fbfcfd",
            insertbackground=self.TEXT,
            padx=10,
            pady=8,
        )
        self.text_input.insert("1.0", "こんにちは日本語")
        self.text_input.grid(row=1, column=0, sticky="ew", pady=(8, 14))

        position_header = ttk.Frame(parent, style="Surface.TFrame")
        position_header.grid(row=2, column=0, sticky="ew")
        ttk.Label(position_header, text="書寫起點", style="Section.TLabel").pack(side="left")
        self.capture_button = ttk.Button(
            position_header,
            text="擷取滑鼠位置",
            style="Secondary.TButton",
            command=self.capture_position,
        )
        self.capture_button.pack(side="right")

        position_grid = ttk.Frame(parent, style="Surface.TFrame")
        position_grid.grid(row=3, column=0, sticky="ew", pady=(8, 14))
        position_grid.columnconfigure((0, 1), weight=1)
        self._field(position_grid, 0, 0, "X 座標", self.start_x)
        self._field(position_grid, 0, 1, "Y 座標", self.start_y)

        ttk.Label(parent, text="文字配置", style="Section.TLabel").grid(
            row=4, column=0, sticky="w"
        )
        size_grid = ttk.Frame(parent, style="Surface.TFrame")
        size_grid.grid(row=5, column=0, sticky="ew", pady=(8, 14))
        size_grid.columnconfigure((0, 1), weight=1)
        self._field(size_grid, 0, 0, "字寬", self.char_width)
        self._field(size_grid, 0, 1, "字高", self.char_height)
        self._field(size_grid, 2, 0, "字距", self.char_gap)
        self._field(size_grid, 2, 1, "行距", self.line_gap)

        ttk.Label(parent, text="書寫速度", style="Section.TLabel").grid(
            row=6, column=0, sticky="w"
        )
        speed_grid = ttk.Frame(parent, style="Surface.TFrame")
        speed_grid.grid(row=7, column=0, sticky="ew", pady=(8, 14))
        speed_grid.columnconfigure((0, 1), weight=1)
        self._field(speed_grid, 0, 0, "開始倒數（秒）", self.countdown)
        self._field(speed_grid, 0, 1, "取樣點停頓", self.point_delay)
        self._field(speed_grid, 2, 0, "筆畫停頓", self.stroke_delay)
        self._field(speed_grid, 2, 1, "曲線精細度", self.sample_spacing)

        action_row = ttk.Frame(parent, style="Surface.TFrame")
        action_row.grid(row=8, column=0, sticky="ew", pady=(4, 0))
        action_row.columnconfigure((0, 1), weight=1)
        self.preview_button = ttk.Button(
            action_row,
            text="產生預覽",
            style="Secondary.TButton",
            command=self.generate_preview,
        )
        self.preview_button.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.execute_button = ttk.Button(
            action_row,
            text="開始書寫",
            style="Primary.TButton",
            command=self.start_writing,
        )
        self.execute_button.grid(row=0, column=1, sticky="ew", padx=(5, 0))

    def _field(
        self,
        parent: ttk.Frame,
        row: int,
        column: int,
        label: str,
        variable: tk.StringVar,
    ) -> None:
        container = ttk.Frame(parent, style="Surface.TFrame")
        container.grid(row=row, column=column, sticky="ew", padx=(0 if column == 0 else 6, 6 if column == 0 else 0), pady=(0, 6))
        ttk.Label(container, text=label, style="Field.TLabel").pack(anchor="w", pady=(0, 4))
        ttk.Entry(container, textvariable=variable).pack(fill="x")

    def _build_preview(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        preview_header = ttk.Frame(parent, style="Surface.TFrame")
        preview_header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        ttk.Label(preview_header, text="筆順預覽", style="Section.TLabel").pack(side="left")
        ttk.Label(preview_header, textvariable=self.summary, style="Status.TLabel").pack(side="right")

        preview_border = tk.Frame(parent, background=self.BORDER, padx=1, pady=1)
        preview_border.grid(row=1, column=0, sticky="nsew")
        self.preview_label = tk.Label(
            preview_border,
            text="正在建立預覽…",
            background="#ffffff",
            foreground=self.MUTED,
            font=("Microsoft JhengHei UI", 11),
        )
        self.preview_label.pack(fill="both", expand=True)

        status_row = ttk.Frame(parent, style="Surface.TFrame")
        status_row.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        self.status_mark = tk.Label(
            status_row,
            text="●",
            background=self.SURFACE,
            foreground=self.PRIMARY,
            font=("Microsoft JhengHei UI", 9),
        )
        self.status_mark.pack(side="left", padx=(0, 7))
        ttk.Label(status_row, textvariable=self.status, style="Status.TLabel").pack(side="left")
        ttk.Label(
            status_row,
            text="緊急停止：將滑鼠移到螢幕左上角",
            style="Status.TLabel",
        ).pack(side="right")

    def _number(self, variable: tk.StringVar, label: str, minimum: float = 0) -> float:
        try:
            value = float(variable.get().strip())
        except ValueError as exc:
            raise ValueError(f"「{label}」必須是數字。") from exc
        if not math.isfinite(value) or value < minimum:
            raise ValueError(f"「{label}」不可小於 {minimum}。")
        return value

    def _integer(self, variable: tk.StringVar, label: str, minimum: int = 0) -> int:
        value = self._number(variable, label, minimum)
        if not value.is_integer():
            raise ValueError(f"「{label}」必須是整數。")
        return int(value)

    def read_settings(self) -> tuple[str, DrawSettings, int, float, float]:
        text = self.text_input.get("1.0", "end-1c")
        if not text.strip():
            raise ValueError("請輸入要書寫的日文文字。")

        settings = DrawSettings(
            start_x=self._number(self.start_x, "X 座標"),
            start_y=self._number(self.start_y, "Y 座標"),
            char_width=self._number(self.char_width, "字寬", 10),
            char_height=self._number(self.char_height, "字高", 10),
            char_gap=self._number(self.char_gap, "字距"),
            line_gap=self._number(self.line_gap, "行距"),
            point_step=1,
            sample_spacing=self._number(self.sample_spacing, "曲線精細度", 0.1),
            preserve_aspect=True,
        )
        countdown = self._integer(self.countdown, "開始倒數", 0)
        point_delay = self._number(self.point_delay, "取樣點停頓")
        stroke_delay = self._number(self.stroke_delay, "筆畫停頓")
        return text, settings, countdown, point_delay, stroke_delay

    def build_result(self) -> tuple[BuildResult, int, float, float]:
        text, settings, countdown, point_delay, stroke_delay = self.read_settings()
        result = build_paths(text, DEFAULT_KANJIVG_DIR, settings)
        return result, countdown, point_delay, stroke_delay

    def set_busy(self, busy: bool, status: str) -> None:
        self.busy = busy
        state = "disabled" if busy else "normal"
        for button in (self.capture_button, self.preview_button, self.execute_button):
            button.configure(state=state)
        self.status.set(status)
        self.status_mark.configure(foreground=self.ACCENT if busy else self.PRIMARY)

    def show_error(self, error: BaseException) -> None:
        self.set_busy(False, "操作未完成")
        message = str(error).strip() or error.__class__.__name__
        messagebox.showerror("無法執行", message, parent=self.root)

    def generate_preview(self) -> None:
        if self.busy:
            return
        try:
            text, settings, _, _, _ = self.read_settings()
        except ValueError as exc:
            self.show_error(exc)
            return

        self.set_busy(True, "正在建立筆順預覽…")

        def worker() -> None:
            output = Path(tempfile.gettempdir()) / "japanese-writer-preview.png"
            try:
                result = build_paths(text, DEFAULT_KANJIVG_DIR, settings)
                preview_paths(result.paths, output)
                stroke_count, point_count = path_stats(result.paths)
                self._post_ui(self._show_preview, output, stroke_count, point_count)
            except BaseException as exc:
                self._post_ui(self.show_error, exc)

        threading.Thread(target=worker, daemon=True).start()

    def _show_preview(self, output: Path, stroke_count: int, point_count: int) -> None:
        try:
            image = tk.PhotoImage(file=str(output))
            max_width = max(420, self.preview_label.winfo_width() - 36)
            max_height = max(320, self.preview_label.winfo_height() - 36)
            factor = max(1, math.ceil(max(image.width() / max_width, image.height() / max_height)))
            if factor > 1:
                image = image.subsample(factor, factor)
            self.preview_image = image
            self.preview_label.configure(image=image, text="")
            self.summary.set(f"{stroke_count} 筆 · {point_count} 個取樣點")
            self.set_busy(False, "預覽已更新")
        except BaseException as exc:
            self.show_error(exc)
        finally:
            output.unlink(missing_ok=True)

    def capture_position(self) -> None:
        if self.busy:
            return
        self.set_busy(True, "3 秒後擷取滑鼠位置…")
        self.root.iconify()

        def worker() -> None:
            try:
                import pyautogui

                for remaining in range(3, 0, -1):
                    self._post_ui(self.status.set, f"{remaining} 秒後擷取滑鼠位置…")
                    time.sleep(1)
                x, y = pyautogui.position()
                self._post_ui(self._position_captured, x, y)
            except BaseException as exc:
                self._post_ui(self._restore_with_error, exc)

        threading.Thread(target=worker, daemon=True).start()

    def _position_captured(self, x: int, y: int) -> None:
        self.start_x.set(str(x))
        self.start_y.set(str(y))
        self.root.deiconify()
        self.root.lift()
        self.set_busy(False, f"已擷取起點：X={x}，Y={y}")

    def start_writing(self) -> None:
        if self.busy:
            return
        try:
            result, countdown, point_delay, stroke_delay = self.build_result()
        except BaseException as exc:
            self.show_error(exc)
            return

        stroke_count, point_count = path_stats(result.paths)
        self.summary.set(f"{stroke_count} 筆 · {point_count} 個取樣點")
        self.set_busy(True, "準備開始書寫…")
        self.root.iconify()

        def worker() -> None:
            try:
                draw_with_mouse(
                    result.paths,
                    countdown=countdown,
                    move_duration=0,
                    point_delay=point_delay,
                    stroke_delay=stroke_delay,
                    allow_offscreen=False,
                )
                self._post_ui(self._writing_complete)
            except BaseException as exc:
                self._post_ui(self._restore_with_error, exc)

        threading.Thread(target=worker, daemon=True).start()

    def _writing_complete(self) -> None:
        self.root.deiconify()
        self.root.lift()
        self.set_busy(False, "書寫完成")
        messagebox.showinfo("完成", "文字已依筆順書寫完成。", parent=self.root)

    def _restore_with_error(self, error: BaseException) -> None:
        self.root.deiconify()
        self.root.lift()
        self.show_error(error)

    def on_close(self) -> None:
        if self.busy:
            messagebox.showwarning(
                "操作進行中",
                "請先等待目前操作完成；緊急停止時可將滑鼠移到螢幕左上角。",
                parent=self.root,
            )
            return
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    JapaneseWriterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
