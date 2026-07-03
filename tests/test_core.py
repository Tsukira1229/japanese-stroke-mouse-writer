from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from mouse_writer_pro import (
    DEFAULT_KANJIVG_DIR,
    SUPPORTED_SYMBOLS,
    EnvironmentSettings,
    FlowDirection,
    GeneralSettings,
    LayoutOverflowError,
    LayoutSettings,
    Orientation,
    UnsupportedCharacterError,
    WritingCancelled,
    build_layout,
    draw_with_mouse,
    interruptible_sleep,
    is_supported_writing_char,
    load_kanjivg_strokes,
)


class LayoutTests(unittest.TestCase):
    def layout(self, orientation: Orientation, flow: FlowDirection):
        start_x = 300 if flow is FlowDirection.LEFT else 100
        if orientation is Orientation.HORIZONTAL:
            end_x = 80 if flow is FlowDirection.LEFT else 310
        else:
            end_x = 60 if flow is FlowDirection.LEFT else 320
        return build_layout(
            "あいう",
            DEFAULT_KANJIVG_DIR,
            LayoutSettings(
                start_x=start_x,
                start_y=100,
                end_x=end_x,
                end_y=400,
                general=GeneralSettings(
                    font_size=100,
                    char_gap=10,
                    line_gap=20,
                    orientation=orientation,
                    flow=flow,
                ),
            ),
        )

    def test_horizontal_right_wraps_down(self) -> None:
        result = self.layout(Orientation.HORIZONTAL, FlowDirection.RIGHT)
        self.assertEqual([(p.x, p.y) for p in result.placements], [(100, 100), (210, 100), (100, 220)])
        self.assertEqual(result.automatic_wraps, [2])

    def test_horizontal_left_wraps_down(self) -> None:
        result = self.layout(Orientation.HORIZONTAL, FlowDirection.LEFT)
        self.assertEqual([(p.x, p.y) for p in result.placements], [(200, 100), (90, 100), (200, 220)])
        self.assertTrue(all(80 <= x <= 300 for path in result.paths for x, _y in path))

    def test_vertical_right_wraps_to_next_column(self) -> None:
        result = self.layout(Orientation.VERTICAL, FlowDirection.RIGHT)
        self.assertEqual([(p.x, p.y) for p in result.placements], [(100, 100), (100, 210), (220, 100)])

    def test_vertical_left_wraps_to_previous_column(self) -> None:
        result = self.layout(Orientation.VERTICAL, FlowDirection.LEFT)
        self.assertEqual([(p.x, p.y) for p in result.placements], [(200, 100), (200, 210), (80, 100)])
        self.assertTrue(all(60 <= x <= 300 for path in result.paths for x, _y in path))

    def test_left_layout_requires_one_full_cell_width(self) -> None:
        with self.assertRaisesRegex(ValueError, "至少需要容納一個字格"):
            build_layout(
                "あ",
                DEFAULT_KANJIVG_DIR,
                LayoutSettings(
                    start_x=300,
                    start_y=100,
                    end_x=201,
                    end_y=300,
                    general=GeneralSettings(font_size=100, flow=FlowDirection.LEFT),
                ),
            )

    def test_left_layout_preserves_space_tab_and_wrap_bounds(self) -> None:
        result = build_layout(
            "あ \tい\nう",
            DEFAULT_KANJIVG_DIR,
            LayoutSettings(
                start_x=600,
                start_y=0,
                end_x=0,
                end_y=300,
                general=GeneralSettings(
                    font_size=80,
                    char_gap=5,
                    line_gap=10,
                    flow=FlowDirection.LEFT,
                ),
            ),
        )
        self.assertEqual([p.char for p in result.placements], ["あ", " ", "\t", "い", "う"])
        self.assertTrue(all(0 <= p.x and p.x + 80 <= 600 for p in result.placements))

    def test_spaces_tabs_and_explicit_newlines_are_preserved(self) -> None:
        result = build_layout(
            "あ い\n\tう",
            DEFAULT_KANJIVG_DIR,
            LayoutSettings(
                start_x=0,
                start_y=0,
                end_x=800,
                end_y=400,
                general=GeneralSettings(font_size=80, char_gap=5, line_gap=10),
            ),
        )
        self.assertEqual([p.char for p in result.placements], ["あ", " ", "い", "\t", "う"])
        self.assertEqual(result.placements[3].span, 4)
        self.assertEqual(result.explicit_wraps, [3])

    def test_secondary_overflow_stops_before_drawing(self) -> None:
        with self.assertRaises(LayoutOverflowError):
            build_layout(
                "あいう",
                DEFAULT_KANJIVG_DIR,
                LayoutSettings(
                    start_x=0,
                    start_y=0,
                    end_x=210,
                    end_y=100,
                    general=GeneralSettings(font_size=100, char_gap=10),
                ),
            )

    def test_unsupported_text_is_rejected(self) -> None:
        with self.assertRaises(UnsupportedCharacterError):
            build_layout(
                "$",
                DEFAULT_KANJIVG_DIR,
                LayoutSettings(start_x=0, start_y=0, general=GeneralSettings(font_size=100)),
            )

    def test_latin_numbers_and_symbols_have_stroke_paths(self) -> None:
        characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789" + "".join(SUPPORTED_SYMBOLS)
        self.assertTrue(all(is_supported_writing_char(char) for char in characters))
        for char in characters:
            with self.subTest(char=char):
                strokes = load_kanjivg_strokes(char, DEFAULT_KANJIVG_DIR, 2.0)
                self.assertTrue(strokes)

    def test_custom_and_aliased_symbol_strokes(self) -> None:
        ascii_comma = load_kanjivg_strokes(",", DEFAULT_KANJIVG_DIR, 2.0)
        fullwidth_comma = load_kanjivg_strokes("，", DEFAULT_KANJIVG_DIR, 2.0)
        self.assertEqual(fullwidth_comma, ascii_comma)
        self.assertEqual(len(load_kanjivg_strokes("～", DEFAULT_KANJIVG_DIR, 2.0) or []), 1)
        at_sign = load_kanjivg_strokes("@", DEFAULT_KANJIVG_DIR, 2.0) or []
        self.assertEqual(len(at_sign), 3)
        self.assertEqual(
            [(round(stroke[0][0]), round(stroke[0][1])) for stroke in at_sign],
            [(61, 43), (62, 43), (82, 76)],
        )

    def test_mixed_text_layout_in_all_directions(self) -> None:
        text = "日本語 Abc 123，。、～@"
        for orientation in Orientation:
            for flow in FlowDirection:
                with self.subTest(orientation=orientation, flow=flow):
                    start_x = 1000 if flow is FlowDirection.LEFT else 0
                    end_x = 0 if flow is FlowDirection.LEFT else 1000
                    result = build_layout(
                        text,
                        DEFAULT_KANJIVG_DIR,
                        LayoutSettings(
                            start_x=start_x,
                            start_y=0,
                            end_x=end_x,
                            end_y=1000,
                            general=GeneralSettings(
                                font_size=50,
                                char_gap=5,
                                line_gap=10,
                                orientation=orientation,
                                flow=flow,
                            ),
                        ),
                    )
                    self.assertEqual("".join(item.char for item in result.placements), text)
                    self.assertEqual(result.kanjivg_chars, [char for char in text if not char.isspace()])


class CancellationTests(unittest.TestCase):
    def test_interruptible_sleep_raises_on_stop(self) -> None:
        with self.assertRaises(WritingCancelled):
            interruptible_sleep(1, lambda: True)

    def test_cancelled_drawing_always_releases_mouse(self) -> None:
        calls: list[tuple[object, ...]] = []

        class FakeMouse:
            screen_bounds = (-1000, -1000, 2000, 2000)

            def move_to(self, x: int, y: int) -> None:
                calls.append(("move", x, y))

            def left_down(self) -> None:
                calls.append(("down",))

            def left_up(self) -> None:
                calls.append(("up",))

        fake_pyautogui = SimpleNamespace(
            FAILSAFE=False,
            PAUSE=0,
            FAILSAFE_POINTS=[],
            position=lambda: (10, 10),
            MINIMUM_DURATION=0.1,
            FailSafeException=RuntimeError,
        )
        def stop_requested() -> bool:
            moved_inside_stroke = ("down",) in calls and ("move", 11, 11) in calls
            return moved_inside_stroke

        with patch.dict(sys.modules, {"pyautogui": fake_pyautogui}), patch(
            "mouse_writer_pro.WindowsSendInputMouse", FakeMouse
        ):
            with self.assertRaises(WritingCancelled):
                draw_with_mouse(
                    [[(10, 10), (11, 11), (12, 12)]],
                    countdown=0,
                    move_duration=0,
                    point_delay=0,
                    stroke_delay=0,
                    allow_offscreen=False,
                    stop_requested=stop_requested,
                )
        self.assertIn(("down",), calls)
        self.assertEqual(calls[-1], ("up",))

    def test_layout_paths_are_sent_to_mouse_without_coordinate_changes(self) -> None:
        result = build_layout(
            "A1～@",
            DEFAULT_KANJIVG_DIR,
            LayoutSettings(
                start_x=100,
                start_y=100,
                end_x=800,
                end_y=400,
                general=GeneralSettings(font_size=80, char_gap=5),
            ),
        )
        calls: list[tuple[object, ...]] = []

        class FakeMouse:
            screen_bounds = (-1000, -1000, 3000, 3000)

            def move_to(self, x: int, y: int) -> None:
                calls.append(("move", x, y))

            def left_down(self) -> None:
                calls.append(("down",))

            def left_up(self) -> None:
                calls.append(("up",))

        fake_pyautogui = SimpleNamespace(
            FAILSAFE=False,
            PAUSE=0,
            FAILSAFE_POINTS=[],
            position=lambda: (10, 10),
            MINIMUM_DURATION=0.1,
            FailSafeException=RuntimeError,
        )
        with patch.dict(sys.modules, {"pyautogui": fake_pyautogui}), patch(
            "mouse_writer_pro.WindowsSendInputMouse", FakeMouse
        ):
            draw_with_mouse(
                result.paths,
                countdown=0,
                move_duration=0,
                point_delay=0,
                stroke_delay=0,
                allow_offscreen=False,
                stop_requested=lambda: False,
            )

        actual_points = [(call[1], call[2]) for call in calls if call[0] == "move"]
        expected_points = [(round(x), round(y)) for path in result.paths for x, y in path]
        self.assertEqual(actual_points, expected_points)
        self.assertEqual(calls[-1], ("up",))


if __name__ == "__main__":
    unittest.main()
