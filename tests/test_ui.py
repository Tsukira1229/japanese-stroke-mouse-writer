from __future__ import annotations

import runpy
import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path

from mouse_writer_pro import WritingCancelled


ROOT = Path(__file__).resolve().parents[1]
UI_NAMESPACE = runpy.run_path(ROOT / "mouse_writer_ui.pyw", run_name="mouse_writer_ui_test")
JapaneseWriterApp = UI_NAMESPACE["JapaneseWriterApp"]


class JapaneseWriterUiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = tk.Tk()
        self.root.withdraw()
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

    def test_three_configuration_areas_exist(self) -> None:
        self.assertEqual(self.app.notebook.index("end"), 3)
        self.assertEqual(self.app.text_input.cget("wrap"), "none")

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
