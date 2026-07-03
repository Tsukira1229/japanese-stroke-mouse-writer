from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from mouse_writer_pro import (
    DEFAULT_KANJIVG_DIR,
    KANJIVG_VIEWBOX,
    SMALL_KANA,
    STROKE_ALIASES,
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
    bounds,
    draw_with_mouse,
    interruptible_sleep,
    is_supported_writing_char,
    load_kanjivg_strokes,
)

SYMBOL_PAIR_TEXT = ",，.．!！?？:：;；@＠~～、､。｡・･ーｰ"


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
                "#",
                DEFAULT_KANJIVG_DIR,
                LayoutSettings(start_x=0, start_y=0, general=GeneralSettings(font_size=100)),
            )

    def test_latin_numbers_and_symbols_have_stroke_paths(self) -> None:
        characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789" + "".join(SUPPORTED_SYMBOLS)
        self.assertEqual(SUPPORTED_SYMBOLS, frozenset(SYMBOL_PAIR_TEXT))
        self.assertEqual(len(SUPPORTED_SYMBOLS), 24)
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

    def test_half_and_fullwidth_pairs_share_stroke_and_layout_paths(self) -> None:
        self.assertEqual(len(STROKE_ALIASES), 12)
        for alias, canonical in STROKE_ALIASES.items():
            with self.subTest(alias=alias, canonical=canonical):
                alias_strokes = load_kanjivg_strokes(alias, DEFAULT_KANJIVG_DIR, 2.0)
                canonical_strokes = load_kanjivg_strokes(canonical, DEFAULT_KANJIVG_DIR, 2.0)
                self.assertEqual(alias_strokes, canonical_strokes)
                alias_layout = build_layout(
                    alias,
                    DEFAULT_KANJIVG_DIR,
                    LayoutSettings(start_x=100, start_y=100, general=GeneralSettings(font_size=109)),
                )
                canonical_layout = build_layout(
                    canonical,
                    DEFAULT_KANJIVG_DIR,
                    LayoutSettings(start_x=100, start_y=100, general=GeneralSettings(font_size=109)),
                )
                self.assertEqual(alias_layout.paths, canonical_layout.paths)

    def test_supported_symbols_preserve_native_109_viewbox_coordinates(self) -> None:
        self.assertEqual(KANJIVG_VIEWBOX, (0.0, 0.0, 109.0, 109.0))
        for char in SUPPORTED_SYMBOLS:
            with self.subTest(char=char):
                source = load_kanjivg_strokes(char, DEFAULT_KANJIVG_DIR, 2.0) or []
                result = build_layout(
                    char,
                    DEFAULT_KANJIVG_DIR,
                    LayoutSettings(
                        start_x=0,
                        start_y=0,
                        end_x=109,
                        end_y=109,
                        general=GeneralSettings(font_size=109),
                    ),
                )
                for actual, expected in zip(result.paths, source, strict=True):
                    self.assertEqual(len(actual), len(expected))
                    for actual_point, expected_point in zip(actual, expected, strict=True):
                        self.assertAlmostEqual(actual_point[0], expected_point[0])
                        self.assertAlmostEqual(actual_point[1], expected_point[1])

    def test_compact_punctuation_stays_small_and_lower_in_cell(self) -> None:
        for char in ",，.．、､。｡":
            with self.subTest(char=char):
                result = build_layout(
                    char,
                    DEFAULT_KANJIVG_DIR,
                    LayoutSettings(start_x=0, start_y=0, general=GeneralSettings(font_size=109)),
                )
                min_x, min_y, max_x, max_y = bounds(result.paths)
                self.assertLessEqual(max_x - min_x, 24)
                self.assertLessEqual(max_y - min_y, 24)
                self.assertGreaterEqual(min_y, 72)

    def test_middle_dot_stays_centered(self) -> None:
        for char in "・･":
            with self.subTest(char=char):
                result = build_layout(
                    char,
                    DEFAULT_KANJIVG_DIR,
                    LayoutSettings(start_x=0, start_y=0, general=GeneralSettings(font_size=109)),
                )
                min_x, min_y, max_x, max_y = bounds(result.paths)
                self.assertAlmostEqual((min_x + max_x) / 2, 54.5)
                self.assertAlmostEqual((min_y + max_y) / 2, 53.0)
                self.assertAlmostEqual(max_x - min_x, 12.0)
                self.assertAlmostEqual(max_y - min_y, 12.0)

    def test_all_symbol_pairs_wrap_in_all_directions(self) -> None:
        for orientation in Orientation:
            for flow in FlowDirection:
                with self.subTest(orientation=orientation, flow=flow):
                    start_x = 400 if flow is FlowDirection.LEFT else 0
                    end_x = 0 if flow is FlowDirection.LEFT else 400
                    result = build_layout(
                        SYMBOL_PAIR_TEXT,
                        DEFAULT_KANJIVG_DIR,
                        LayoutSettings(
                            start_x=start_x,
                            start_y=0,
                            end_x=end_x,
                            end_y=400,
                            general=GeneralSettings(
                                font_size=50,
                                char_gap=5,
                                line_gap=10,
                                orientation=orientation,
                                flow=flow,
                            ),
                        ),
                    )
                    self.assertEqual("".join(item.char for item in result.placements), SYMBOL_PAIR_TEXT)
                    self.assertEqual(result.kanjivg_chars, list(SYMBOL_PAIR_TEXT))
                    self.assertTrue(result.automatic_wraps)

    def test_letters_numbers_and_japanese_keep_bounds_based_scaling(self) -> None:
        for char in "A1あ":
            with self.subTest(char=char):
                result = build_layout(
                    char,
                    DEFAULT_KANJIVG_DIR,
                    LayoutSettings(start_x=0, start_y=0, general=GeneralSettings(font_size=109)),
                )
                _min_x, min_y, _max_x, max_y = bounds(result.paths)
                self.assertAlmostEqual(min_y, 0.0)
                self.assertAlmostEqual(max_y, 109.0)

    def test_supported_symbols_stay_inside_cells_in_all_directions(self) -> None:
        for char in SUPPORTED_SYMBOLS:
            for orientation in Orientation:
                for flow in FlowDirection:
                    with self.subTest(char=char, orientation=orientation, flow=flow):
                        start_x = 300 if flow is FlowDirection.LEFT else 100
                        end_x = 0 if flow is FlowDirection.LEFT else 400
                        result = build_layout(
                            char,
                            DEFAULT_KANJIVG_DIR,
                            LayoutSettings(
                                start_x=start_x,
                                start_y=100,
                                end_x=end_x,
                                end_y=400,
                                general=GeneralSettings(
                                    font_size=109,
                                    orientation=orientation,
                                    flow=flow,
                                ),
                            ),
                        )
                        placement = result.placements[0]
                        self.assertTrue(
                            all(
                                placement.x <= x <= placement.x + 109
                                and placement.y <= y <= placement.y + 109
                                for path in result.paths
                                for x, y in path
                            )
                        )

    def test_small_kana_preserve_native_109_viewbox_coordinates(self) -> None:
        self.assertEqual(len(SMALL_KANA), 24)
        for char in SMALL_KANA:
            with self.subTest(char=char):
                source = load_kanjivg_strokes(char, DEFAULT_KANJIVG_DIR, 2.0) or []
                self.assertTrue(source)
                result = build_layout(
                    char,
                    DEFAULT_KANJIVG_DIR,
                    LayoutSettings(
                        start_x=0,
                        start_y=0,
                        end_x=109,
                        end_y=109,
                        general=GeneralSettings(font_size=109),
                    ),
                )
                for actual, expected in zip(result.paths, source, strict=True):
                    self.assertEqual(len(actual), len(expected))
                    for actual_point, expected_point in zip(actual, expected, strict=True):
                        self.assertAlmostEqual(actual_point[0], expected_point[0])
                        self.assertAlmostEqual(actual_point[1], expected_point[1])

    def test_small_kana_are_smaller_than_full_sized_forms(self) -> None:
        pairs = (
            ("ぁ", "あ"), ("ぃ", "い"), ("ぅ", "う"), ("ぇ", "え"), ("ぉ", "お"),
            ("っ", "つ"), ("ゃ", "や"), ("ゅ", "ゆ"), ("ょ", "よ"), ("ゎ", "わ"),
            ("ゕ", "か"), ("ゖ", "け"), ("ァ", "ア"), ("ィ", "イ"), ("ゥ", "ウ"),
            ("ェ", "エ"), ("ォ", "オ"), ("ッ", "ツ"), ("ャ", "ヤ"), ("ュ", "ユ"),
            ("ョ", "ヨ"), ("ヮ", "ワ"), ("ヵ", "カ"), ("ヶ", "ケ"),
        )
        for small, full in pairs:
            with self.subTest(small=small, full=full):
                small_result = build_layout(
                    small,
                    DEFAULT_KANJIVG_DIR,
                    LayoutSettings(start_x=0, start_y=0, general=GeneralSettings(font_size=109)),
                )
                full_result = build_layout(
                    full,
                    DEFAULT_KANJIVG_DIR,
                    LayoutSettings(start_x=0, start_y=0, general=GeneralSettings(font_size=109)),
                )
                small_bounds = bounds(small_result.paths)
                full_bounds = bounds(full_result.paths)
                small_extent = max(small_bounds[2] - small_bounds[0], small_bounds[3] - small_bounds[1])
                full_extent = max(full_bounds[2] - full_bounds[0], full_bounds[3] - full_bounds[1])
                self.assertLess(small_extent, full_extent)

    def test_small_kana_words_layout_in_all_directions(self) -> None:
        text = "ちょこ ましょう きゃっか キャット"
        for orientation in Orientation:
            for flow in FlowDirection:
                with self.subTest(orientation=orientation, flow=flow):
                    start_x = 1600 if flow is FlowDirection.LEFT else 0
                    end_x = 0 if flow is FlowDirection.LEFT else 1600
                    result = build_layout(
                        text,
                        DEFAULT_KANJIVG_DIR,
                        LayoutSettings(
                            start_x=start_x,
                            start_y=0,
                            end_x=end_x,
                            end_y=1600,
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
                    self.assertTrue(all(char in result.kanjivg_chars for char in "ょゃっャッ"))

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
            "A1ょっ" + SYMBOL_PAIR_TEXT,
            DEFAULT_KANJIVG_DIR,
            LayoutSettings(
                start_x=100,
                start_y=100,
                end_x=800,
                end_y=600,
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
