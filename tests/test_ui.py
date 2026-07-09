from __future__ import annotations

import json
import runpy
import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path
from tkinter import ttk
from unittest.mock import patch

from localization import LANGUAGE_OPTIONS, Language
from mouse_writer_pro import WritingCancelled


ROOT = Path(__file__).resolve().parents[1]
UI_NAMESPACE = runpy.run_path(ROOT / "mouse_writer_ui.pyw", run_name="mouse_writer_ui_test")
JapaneseWriterApp = UI_NAMESPACE["JapaneseWriterApp"]


class JapaneseWriterUiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = tk.Tk()
        self.root.withdraw()
        with patch("localization._system_locale_name", return_value="zh-TW"):
            self.app = JapaneseWriterApp(
                self.root,
                settings_path=Path(self.temp.name) / "user_data/settings.json",
            )
        self.root.update_idletasks()

    def tearDown(self) -> None:
        self.app.closing = True
        self.app.cancel_scheduled_callbacks()
        self.root.destroy()
        self.temp.cleanup()

    def test_four_application_areas_exist(self) -> None:
        self.assertEqual(self.app.notebook.index("end"), 4)
        self.assertEqual(self.app.text_input.cget("wrap"), "none")
        self.assertFalse(
            any(isinstance(child, ttk.Scrollbar) for child in self.app.text_input.master.winfo_children())
        )

    def test_emergency_hint_uses_previous_status_bar_style(self) -> None:
        self.assertIs(self.app.emergency_label.master, self.app.status_bar)
        self.assertEqual(self.app.emergency_label.pack_info()["side"], "right")
        self.assertIn("ESC", self.app.emergency_label.cget("text"))
        self.assertEqual(self.app.emergency_label.cget("style"), "Subtitle.TLabel")

    def test_help_tab_contains_operation_only_guidance(self) -> None:
        self.assertEqual(self.app.notebook.tab(3, "text"), "使用說明")
        self.assertEqual(self.app.help_text.cget("state"), "disabled")
        help_text = self.app.help_text.get("1.0", "end-1c")
        self.assertIn("起始座標", help_text)
        self.assertIn("末端座標", help_text)
        self.assertIn("顏文字", help_text)
        self.assertIn("中心線符號", help_text)
        self.assertIn("左上角", help_text)
        self.assertIn("右上角", help_text)
        self.assertIn("ESC", help_text)
        self.assertNotIn("安裝", help_text)
        self.assertNotIn("SmartScreen", help_text)

    def test_kaomoji_picker_is_removed(self) -> None:
        self.assertFalse(hasattr(self.app, "kaomoji_category"))
        self.assertFalse(hasattr(self.app, "kaomoji_list"))
        self.assertFalse(hasattr(self.app, "insert_selected_kaomoji"))

    def test_startup_and_operation_restore_zoomed_state(self) -> None:
        with patch.object(self.root, "state") as state:
            self.app._maximize_window()
            state.assert_called_once_with("zoomed")
        self.app.window_state_before_operation = "zoomed"
        with (
            patch.object(self.root, "deiconify") as deiconify,
            patch.object(self.root, "state") as state,
            patch.object(self.root, "lift") as lift,
        ):
            self.app._restore_main_window()
            deiconify.assert_called_once_with()
            state.assert_called_once_with("zoomed")
            lift.assert_called_once_with()

    def test_environment_fields_are_numeric_spinboxes(self) -> None:
        self.assertEqual(len(self.app.numeric_inputs), 3)
        self.assertTrue(all(control.widget.winfo_class() == "TSpinbox" for control in self.app.numeric_inputs))
        curve_control = self.app.numeric_inputs[1]
        self.assertFalse(curve_control._validate("２。５"))
        self.root.update()
        self.assertEqual(curve_control.variable.get(), "2.5")
        self.assertFalse(curve_control._validate("2a"))

    def test_numeric_control_reverts_invalid_range(self) -> None:
        delay_control = self.app.numeric_inputs[2]
        previous = delay_control.variable.get()
        delay_control.variable.set("0")
        delay_control._commit()
        self.assertEqual(delay_control.variable.get(), previous)

    def test_language_switch_is_immediate_and_preserves_session_data(self) -> None:
        content = "あ ア\n日本語"
        self.app.text_input.delete("1.0", "end")
        self.app.text_input.insert("1.0", content)
        self.app.start_x.set("432")
        english_label = dict(LANGUAGE_OPTIONS)[Language.ENGLISH]
        self.app.language_selection.set(english_label)
        self.app._language_selected()
        self.assertIs(self.app.language, Language.ENGLISH)
        self.assertEqual(self.app.text_input.get("1.0", "end-1c"), content)
        self.assertEqual(self.app.start_x.get(), "432")
        self.assertEqual(self.app.notebook.tab(0, "text"), "Content & Preview")
        self.assertEqual(self.app.notebook.tab(3, "text"), "Help")
        self.assertIn("start and end coordinates", self.app.help_text.get("1.0", "end-1c"))
        self.assertEqual(self.app.orientation.get(), "Horizontal")
        self.assertIn("language", self.app.status.get().lower())
        self.assertEqual(
            json.loads((Path(self.temp.name) / "user_data/settings.json").read_text(encoding="utf-8"))["language"],
            "en",
        )

    def test_default_layout_builds_paths(self) -> None:
        result, environment = self.app.build_result()
        self.assertGreater(len(result.paths), 0)
        self.assertEqual(environment.countdown, 5)
        self.assertEqual(environment.point_delay, 0.008)
        self.assertEqual(environment.move_duration, 0.0)

    def test_environment_uses_milliseconds_without_speed_control(self) -> None:
        texts: list[str] = []

        def collect(widget: tk.Misc) -> None:
            try:
                text = widget.cget("text")
            except tk.TclError:
                text = ""
            if text:
                texts.append(str(text))
            for child in widget.winfo_children():
                collect(child)

        collect(self.app.environment_tab)
        self.assertTrue(any("取樣點停頓（毫秒）" in text for text in texts))
        self.assertTrue(any("0.1–20" in text for text in texts))
        self.assertFalse(any("書寫速度" in text for text in texts))

    def test_environment_boundaries(self) -> None:
        for milliseconds in ("1", "8", "1000"):
            with self.subTest(milliseconds=milliseconds):
                self.app.point_delay_ms.set(milliseconds)
                self.assertEqual(self.app.read_environment().point_delay, float(milliseconds) / 1000)
        for milliseconds in ("0", "0.9", "1000.1"):
            with self.subTest(milliseconds=milliseconds):
                self.app.point_delay_ms.set(milliseconds)
                with self.assertRaises(ValueError):
                    self.app.read_environment()
        for spacing in ("0.1", "20"):
            self.app.point_delay_ms.set("8")
            self.app.sample_spacing.set(spacing)
            self.assertEqual(self.app.read_environment().sample_spacing, float(spacing))
        for spacing in ("0.09", "20.1"):
            self.app.sample_spacing.set(spacing)
            with self.assertRaises(ValueError):
                self.app.read_environment()

    def test_loaded_seconds_are_displayed_as_milliseconds(self) -> None:
        environment_type = type(self.app.read_environment())
        self.app._apply_environment(environment_type(point_delay=0.012))
        self.assertEqual(self.app.point_delay_ms.get(), "12")

    def test_preview_completes_on_canvas(self) -> None:
        self.app.refresh_preview()
        deadline = time.time() + 15
        while self.app.current_layout is None and time.time() < deadline:
            self.root.update()
            time.sleep(0.02)
        self.assertIsNotNone(self.app.current_layout)
        self.assertIn("筆", self.app.summary.get())

    def test_preview_draws_tab_as_four_half_cells(self) -> None:
        self.app.text_input.delete("1.0", "end")
        self.app.text_input.insert("1.0", "A\tＢ")
        self.app.current_layout = None
        self.app.refresh_preview()
        deadline = time.time() + 15
        while self.app.current_layout is None and time.time() < deadline:
            self.root.update()
            time.sleep(0.02)
        self.root.update_idletasks()
        self.app._draw_current_layout()
        placements = self.app.current_layout.placements
        self.assertEqual([item.span for item in placements], [0.5, 2.0, 1.0])
        self.assertEqual(placements[1].subcells, 4)
        self.assertEqual([item.x for item in placements], [100, 181, 511])
        rectangles = [
            item
            for item in self.app.preview_canvas.find_all()
            if self.app.preview_canvas.type(item) == "rectangle"
        ]
        self.assertEqual(len(rectangles), 1 + 1 + 4 + 1)

    def test_coordinate_detection_can_overwrite_values(self) -> None:
        self.app._coordinate_detected("start", -200, 50)
        self.app._coordinate_detected("start", -100, 70)
        self.app._coordinate_detected("end", 900, 700)
        self.assertEqual((self.app.start_x.get(), self.app.start_y.get()), ("-100", "70"))
        self.assertEqual((self.app.end_x.get(), self.app.end_y.get()), ("900", "700"))

    def test_escape_cancel_keeps_existing_coordinates(self) -> None:
        before = (self.app.start_x.get(), self.app.start_y.get())
        self.app._restore_after_operation(WritingCancelled("cancelled"))
        self.assertEqual((self.app.start_x.get(), self.app.start_y.get()), before)
        self.assertIn("ESC", self.app.status.get())


if __name__ == "__main__":
    unittest.main()
