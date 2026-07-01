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
