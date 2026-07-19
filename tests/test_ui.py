from __future__ import annotations

import ctypes
import json
import runpy
import sys
import tempfile
import time
import tkinter as tk
import ttkbootstrap as tb
import unittest
from pathlib import Path
from tkinter import ttk
from ttkbootstrap.publisher import Publisher
from unittest.mock import patch

from localization import LANGUAGE_OPTIONS, Language
from mouse_writer_pro import WritingCancelled


ROOT = Path(__file__).resolve().parents[1]
UI_NAMESPACE = runpy.run_path(ROOT / "mouse_writer_ui.pyw", run_name="mouse_writer_ui_test")
JapaneseWriterApp = UI_NAMESPACE["JapaneseWriterApp"]
screen_geometry = UI_NAMESPACE["_screen_geometry"]
ScreenRect = UI_NAMESPACE["_ScreenRect"]
USER32 = UI_NAMESPACE["_USER32"]


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
        Publisher.clear_subscribers()
        tb.Style.instance = None
        self.root.update_idletasks()
        self.root.destroy()
        self.temp.cleanup()

    def test_four_application_areas_exist(self) -> None:
        self.assertEqual(self.app.notebook.index("end"), 4)
        self.assertEqual(self.app.text_input.cget("wrap"), "none")
        self.assertFalse(
            any(isinstance(child, ttk.Scrollbar) for child in self.app.text_input.master.winfo_children())
        )

    def test_new_session_defaults_to_light_theme(self) -> None:
        self.assertFalse(self.app.palette.dark)
        self.assertEqual(self.app.appearance_selection.get(), self.app.t("appearance_light"))
        self.assertEqual(self.app.t("appearance_light"), "亮色主題")
        self.assertEqual(self.app.t("appearance_dark"), "暗色主題")

    def test_all_direct_styles_are_selectable(self) -> None:
        labels = self.app._stroke_style_labels()
        self.assertEqual(set(labels.values()), {"kanjivg", "yomogi", "zen-kurenaido", "hachi-maru-pop"})
        self.assertIn("KanjiVG (預設)", labels)
        self.assertIn("Yomogi", labels)
        self.assertFalse(any("直繪中心線" in label for label in labels))
        for style_id in ("yomogi", "zen-kurenaido", "hachi-maru-pop"):
            selected = next(label for label, value in labels.items() if value == style_id)
            self.app.stroke_style.set(selected)
            self.assertEqual(self.app.read_general().stroke_style, style_id)

    def test_named_preset_restores_writing_style(self) -> None:
        labels = self.app._stroke_style_labels()
        hachi_label = next(label for label, value in labels.items() if value == "hachi-maru-pop")
        self.app.stroke_style.set(hachi_label)
        preset = self.app.store.add_preset("Hachi", self.app.read_general())
        self.app.refresh_preset_list(preset.id)
        self.app.stroke_style.set(next(label for label, value in labels.items() if value == "kanjivg"))
        self.app.load_selected_preset()
        self.assertEqual(self.app.read_general().stroke_style, "hachi-maru-pop")

    def test_emergency_hint_uses_previous_status_bar_style(self) -> None:
        self.assertIs(self.app.emergency_label.master, self.app.status_bar)
        self.assertEqual(self.app.emergency_label.pack_info()["side"], "right")
        self.assertIn("ESC", self.app.emergency_label.cget("text"))
        self.assertEqual(self.app.emergency_label.cget("style"), "Subtitle.TLabel")

    def test_help_tab_contains_operation_only_guidance(self) -> None:
        self.assertIn("使用說明", self.app.notebook.tab(3, "text"))
        self.assertEqual(self.app.help_text.cget("state"), "disabled")
        help_text = self.app.help_text.get("1.0", "end-1c")
        self.assertIn("起始座標", help_text)
        self.assertIn("末端座標", help_text)
        self.assertIn("十字線", help_text)
        self.assertIn("預計書寫矩形", help_text)
        self.assertIn("顏文字", help_text)
        self.assertIn("特殊符號", help_text)
        self.assertIn("KanjiVG (預設)", help_text)
        self.assertIn("最佳努力", help_text)
        self.assertIn("Zen Kurenaido", help_text)
        self.assertIn("Hachi Maru Pop", help_text)
        self.assertIn("不保證正統日文筆順", help_text)
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

    def test_coordinate_detection_withdraws_main_window(self) -> None:
        with (
            patch.object(self.root, "state", return_value="zoomed"),
            patch.object(self.root, "withdraw") as withdraw,
            patch.object(self.root, "iconify") as iconify,
        ):
            self.app._hide_for_coordinate_detection()

        self.assertEqual(self.app.window_state_before_operation, "zoomed")
        withdraw.assert_called_once_with()
        iconify.assert_not_called()

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
        self.assertIn("Content & Preview", self.app.notebook.tab(0, "text"))
        self.assertIn("Help", self.app.notebook.tab(3, "text"))
        self.assertIn("start and end coordinates", self.app.help_text.get("1.0", "end-1c"))
        self.assertEqual(self.app.orientation.get(), "Horizontal")
        self.assertIn("language", self.app.status.get().lower())
        self.assertEqual(
            json.loads((Path(self.temp.name) / "user_data/settings.json").read_text(encoding="utf-8"))["language"],
            "en",
        )

    def test_theme_switch_preserves_session_and_persists_mode(self) -> None:
        content = "日本語 ABC"
        self.app.text_input.delete("1.0", "end")
        self.app.text_input.insert("1.0", content)
        self.app.start_x.set("321")
        self.app.appearance_selection.set(self.app.t("appearance_dark"))
        self.app._appearance_selected()
        self.assertTrue(self.app.palette.dark)
        self.assertEqual(self.app.text_input.get("1.0", "end-1c"), content)
        self.assertEqual(self.app.start_x.get(), "321")
        self.assertEqual(self.app.preview_canvas.cget("background"), self.app.palette.canvas)
        payload = json.loads((Path(self.temp.name) / "user_data/settings.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["appearance_mode"], "dark")

    def test_language_then_theme_switch_does_not_reference_destroyed_widgets(self) -> None:
        self.app.language_selection.set(dict(LANGUAGE_OPTIONS)[Language.JAPANESE])
        self.app._language_selected()
        self.app.appearance_selection.set(self.app.t("appearance_dark"))
        self.app._appearance_selected()
        self.root.update_idletasks()
        self.assertIs(self.app.language, Language.JAPANESE)
        self.assertTrue(self.app.palette.dark)

    def test_orientation_and_flow_use_segmented_controls(self) -> None:
        self.assertEqual(len(self.app.orientation_segments), 2)
        self.assertEqual(len(self.app.flow_segments), 2)
        self.app.orientation_segments[1].invoke()
        self.app.flow_segments[1].invoke()
        self.assertEqual(self.app.orientation.get(), self.app.t("vertical"))
        self.assertEqual(self.app.flow.get(), self.app.t("left"))

    def test_error_status_uses_error_indicator(self) -> None:
        self.app._set_status_text("error", "error")
        self.assertEqual(self.app.status_kind, "error")
        self.assertEqual(self.app.status_mark.cget("foreground"), self.app.ERROR)

    def test_rebuild_closes_visible_tooltips(self) -> None:
        tooltip = self.app.tooltips[0]
        tooltip._show()
        self.assertIsNotNone(tooltip.window)
        self.app._rebuild_layout()
        self.assertIsNone(tooltip.window)

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

    def test_coordinate_overlay_tracks_pointer_on_negative_monitor(self) -> None:
        overlay_globals = JapaneseWriterApp._refresh_detection_crosshair.__globals__
        with patch.dict(
            overlay_globals,
            {
                "_cursor_position": lambda: (-500, 300),
                "_monitor_bounds_for_point": lambda _x, _y: (-1920, 0, 0, 1080),
            },
        ):
            self.app._show_detection_overlay("偵測起始座標", "start")
            self.root.update_idletasks()
            self.assertEqual(self.app.detection_monitor_bounds, (-1920, 0, 0, 1080))
            self.assertEqual(screen_geometry((-1920, 0, 0, 1080)), "1920x1080-1920+0")
            self.assertTrue(
                {"crosshair-horizontal", "crosshair-vertical", "crosshair-center", "crosshair-label"}
                <= self.app.detection_overlay.parts.keys()
            )
            horizontal = self.app.detection_overlay.parts["crosshair-horizontal"]
            vertical = self.app.detection_overlay.parts["crosshair-vertical"]
            self.assertEqual(horizontal["rect"], (-1920, 299, 0, 301))
            self.assertEqual(vertical["rect"], (-501, 0, -499, 1080))
            overlay_text = str(self.app.detection_overlay.parts["crosshair-label"]["text"])
            self.assertIn("X=-500", overlay_text)
            self.assertIn("Y=300", overlay_text)
            self.assertIn("3", overlay_text)
            self.assertTrue(
                all(
                    (part["rect"][2] - part["rect"][0]) < 1920
                    or (part["rect"][3] - part["rect"][1]) < 1080
                    for part in self.app.detection_overlay.parts.values()
                )
            )
            self.app._close_detection_overlay()

        self.assertFalse(self.app.detection_active)
        self.assertEqual(self.app.detection_overlay.handles, {})
        self.assertEqual(self.app.detection_overlay.parts, {})
        self.assertIsNone(self.app.detection_after_id)

    @unittest.skipUnless(sys.platform == "win32", "Windows coordinate binding regression")
    def test_coordinate_binding_does_not_break_pyautogui_position(self) -> None:
        import pyautogui

        position = pyautogui.position()
        self.assertIsInstance(position.x, int)
        self.assertIsInstance(position.y, int)

    @unittest.skipUnless(sys.platform == "win32", "Windows native overlay regression")
    def test_coordinate_guides_are_ownerless_native_windows_with_exact_bounds(self) -> None:
        overlay_globals = JapaneseWriterApp._refresh_detection_crosshair.__globals__
        with patch.dict(
            overlay_globals,
            {
                "_cursor_position": lambda: (500, 300),
                "_monitor_bounds_for_point": lambda _x, _y: (0, 0, 2560, 1440),
            },
        ):
            try:
                self.app._show_detection_overlay("偵測起始座標", "start")
                total_area = 0
                for key, hwnd in self.app.detection_overlay.handles.items():
                    self.assertFalse(USER32.GetWindow(hwnd, 4), key)
                    native_rect = ScreenRect()
                    self.assertTrue(USER32.GetWindowRect(hwnd, ctypes.byref(native_rect)), key)
                    actual = (native_rect.left, native_rect.top, native_rect.right, native_rect.bottom)
                    expected = self.app.detection_overlay.parts[key]["rect"]
                    self.assertEqual(actual, expected, key)
                    total_area += (actual[2] - actual[0]) * (actual[3] - actual[1])
                self.assertLess(total_area, 2560 * 1440 * 0.02)
            finally:
                self.app._close_detection_overlay()

    def test_end_coordinate_overlay_shows_start_reference_and_rectangle(self) -> None:
        self.app.start_x.set("-1800")
        self.app.start_y.set("100")
        overlay_globals = JapaneseWriterApp._refresh_detection_crosshair.__globals__
        with patch.dict(
            overlay_globals,
            {
                "_cursor_position": lambda: (-500, 300),
                "_monitor_bounds_for_point": lambda _x, _y: (-1920, 0, 0, 1080),
            },
        ):
            self.app._show_detection_overlay("偵測末端座標", "end")
            self.root.update_idletasks()
            expected = {
                "start-horizontal",
                "start-vertical",
                "start-center",
                "start-label",
                "rectangle-top",
                "rectangle-bottom",
                "rectangle-left",
                "rectangle-right",
            }
            self.assertTrue(expected <= self.app.detection_overlay.parts.keys())
            start_text = str(self.app.detection_overlay.parts["start-label"]["text"])
            self.assertIn("X=-1800", start_text)
            self.assertIn("Y=100", start_text)
            self.app._close_detection_overlay()

    def test_start_reference_remains_visible_on_another_monitor(self) -> None:
        self.app.start_x.set("-1800")
        self.app.start_y.set("100")

        def monitor_bounds(x: int, _y: int) -> tuple[int, int, int, int]:
            return (-1920, 0, 0, 1080) if x < 0 else (0, 0, 2560, 1440)

        overlay_globals = JapaneseWriterApp._refresh_detection_crosshair.__globals__
        with patch.dict(
            overlay_globals,
            {
                "_cursor_position": lambda: (500, 300),
                "_monitor_bounds_for_point": monitor_bounds,
            },
        ):
            self.app._show_detection_overlay("偵測末端座標", "end")
            self.root.update_idletasks()
            self.assertTrue(
                {"start-horizontal", "start-vertical", "start-center", "start-label"}
                <= self.app.detection_overlay.parts.keys()
            )
            self.assertFalse(any(key.startswith("rectangle-") for key in self.app.detection_overlay.parts))
            self.app._close_detection_overlay()

        self.assertEqual(self.app.detection_overlay.handles, {})
        self.assertEqual(self.app.detection_overlay.parts, {})

    def test_escape_cancel_keeps_existing_coordinates(self) -> None:
        before = (self.app.start_x.get(), self.app.start_y.get())
        self.app._restore_after_operation(WritingCancelled("cancelled"))
        self.assertEqual((self.app.start_x.get(), self.app.start_y.get()), before)
        self.assertIn("ESC", self.app.status.get())


if __name__ == "__main__":
    unittest.main()
