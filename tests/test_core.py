from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from mouse_writer_pro import (
    DEFAULT_KANJIVG_DIR,
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
)


class LayoutTests(unittest.TestCase):
    def layout(self, orientation: Orientation, flow: FlowDirection):
        start_x = 300 if flow is FlowDirection.LEFT else 100
        if orientation is Orientation.HORIZONTAL:
            end_x = 190 if flow is FlowDirection.LEFT else 310
        else:
            end_x = 180 if flow is FlowDirection.LEFT else 320
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
        self.assertEqual([(p.x, p.y) for p in result.placements], [(300, 100), (190, 100), (300, 220)])

    def test_vertical_right_wraps_to_next_column(self) -> None:
        result = self.layout(Orientation.VERTICAL, FlowDirection.RIGHT)
        self.assertEqual([(p.x, p.y) for p in result.placements], [(100, 100), (100, 210), (220, 100)])

    def test_vertical_left_wraps_to_previous_column(self) -> None:
        result = self.layout(Orientation.VERTICAL, FlowDirection.LEFT)
        self.assertEqual([(p.x, p.y) for p in result.placements], [(300, 100), (300, 210), (180, 100)])

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

    def test_non_japanese_text_is_rejected(self) -> None:
        with self.assertRaises(UnsupportedCharacterError):
            build_layout(
                "A",
                DEFAULT_KANJIVG_DIR,
                LayoutSettings(start_x=0, start_y=0, general=GeneralSettings(font_size=100)),
            )


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


if __name__ == "__main__":
    unittest.main()
