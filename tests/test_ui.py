from __future__ import annotations

import runpy
import time
import tkinter as tk
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UI_NAMESPACE = runpy.run_path(ROOT / "mouse_writer_ui.pyw", run_name="mouse_writer_ui_test")
JapaneseWriterApp = UI_NAMESPACE["JapaneseWriterApp"]


class JapaneseWriterUiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = JapaneseWriterApp(self.root)
        self.root.update_idletasks()

    def tearDown(self) -> None:
        self.root.destroy()

    def test_default_settings_build_japanese_paths(self) -> None:
        text, settings, countdown, point_delay, stroke_delay = self.app.read_settings()
        result, _, _, _ = self.app.build_result()

        self.assertEqual(text, "こんにちは日本語")
        self.assertEqual(settings.char_width, 150)
        self.assertEqual(countdown, 5)
        self.assertEqual(point_delay, 0.008)
        self.assertEqual(stroke_delay, 0.03)
        self.assertGreater(len(result.paths), 0)

    def test_non_japanese_text_is_rejected(self) -> None:
        self.app.text_input.delete("1.0", "end")
        self.app.text_input.insert("1.0", "A")

        with self.assertRaises(SystemExit):
            self.app.build_result()

    def test_preview_completes_and_updates_summary(self) -> None:
        self.app.generate_preview()
        deadline = time.time() + 15
        while self.app.busy and time.time() < deadline:
            self.root.update()
            time.sleep(0.02)

        self.assertFalse(self.app.busy, "Preview generation timed out")
        self.assertIsNotNone(self.app.preview_image)
        self.assertIn("筆", self.app.summary.get())


if __name__ == "__main__":
    unittest.main()
