from __future__ import annotations

import sys
import unicodedata
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from mouse_writer_pro import (
    ASCII_ALNUM,
    ASCII_PUNCTUATION,
    DEFAULT_KANJIVG_DIR,
    FULLWIDTH_ALNUM,
    FULLWIDTH_PUNCTUATION,
    HALFWIDTH_KATAKANA,
    HALFWIDTH_VOICING_MARKS,
    JAPANESE_BRACKETS,
    JAPANESE_PUNCTUATION,
    KANJIVG_VIEWBOX,
    SMALL_KANA,
    STROKE_ALIASES,
    SUPPORTED_SYMBOLS,
    VERTICAL_CORNER_PUNCTUATION,
    VERTICAL_ROTATE_CHARS,
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
    is_halfwidth_char,
    is_supported_writing_char,
    load_kanjivg_strokes,
    tokenize_writing_text,
)

ASCII_ALNUM_TEXT = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
FULLWIDTH_ALNUM_TEXT = "".join(chr(ord(char) + 0xFEE0) for char in ASCII_ALNUM_TEXT)
ASCII_PUNCTUATION_TEXT = "".join(
    chr(codepoint)
    for codepoint in range(0x21, 0x7F)
    if not chr(codepoint).isalnum()
)
FULLWIDTH_PUNCTUATION_TEXT = "".join(chr(ord(char) + 0xFEE0) for char in ASCII_PUNCTUATION_TEXT)
JAPANESE_PUNCTUATION_TEXT = "、､。｡・･ーｰ「」『』【】〈〉《》〔〕｢｣"
SYMBOL_PAIR_TEXT = ASCII_PUNCTUATION_TEXT + FULLWIDTH_PUNCTUATION_TEXT + JAPANESE_PUNCTUATION_TEXT


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

    def test_left_layout_accepts_half_cell_but_rejects_smaller_range(self) -> None:
        result = build_layout(
            "A",
            DEFAULT_KANJIVG_DIR,
            LayoutSettings(
                start_x=300,
                start_y=100,
                end_x=250,
                end_y=300,
                general=GeneralSettings(font_size=100, flow=FlowDirection.LEFT),
            ),
        )
        self.assertEqual(result.placements[0].x, 250)
        with self.assertRaises(ValueError):
            build_layout(
                "A",
                DEFAULT_KANJIVG_DIR,
                LayoutSettings(
                    start_x=300,
                    start_y=100,
                    end_x=251,
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
        self.assertEqual(result.placements[1].span, 0.5)
        self.assertEqual(result.placements[3].span, 2.0)
        self.assertEqual(result.placements[3].subcells, 4)
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
                "©",
                DEFAULT_KANJIVG_DIR,
                LayoutSettings(start_x=0, start_y=0, general=GeneralSettings(font_size=100)),
            )

    def test_latin_numbers_and_symbols_have_stroke_paths(self) -> None:
        characters = ASCII_ALNUM_TEXT + FULLWIDTH_ALNUM_TEXT + SYMBOL_PAIR_TEXT
        self.assertEqual(ASCII_ALNUM, frozenset(ASCII_ALNUM_TEXT))
        self.assertEqual(FULLWIDTH_ALNUM, frozenset(FULLWIDTH_ALNUM_TEXT))
        self.assertEqual(ASCII_PUNCTUATION, frozenset(ASCII_PUNCTUATION_TEXT))
        self.assertEqual(FULLWIDTH_PUNCTUATION, frozenset(FULLWIDTH_PUNCTUATION_TEXT))
        self.assertEqual(JAPANESE_PUNCTUATION, frozenset(JAPANESE_PUNCTUATION_TEXT))
        self.assertEqual(SUPPORTED_SYMBOLS, frozenset(SYMBOL_PAIR_TEXT))
        self.assertEqual(len(SUPPORTED_SYMBOLS), 86)
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

    def test_project_authored_ascii_punctuation_resources(self) -> None:
        expected_stroke_counts = {
            '"': 2, "#": 4, "$": 2, "%": 3, "&": 1, "'": 1,
            "(": 1, ")": 1, "*": 3, "+": 2, "-": 1, "/": 1,
            "<": 1, "=": 2, ">": 1, "[": 1, "\\": 1, "]": 1,
            "^": 1, "_": 1, "`": 1, "{": 1, "|": 1, "}": 1,
        }
        custom_dir = Path(__file__).resolve().parents[1] / "data" / "custom_strokes"
        self.assertEqual(len(list(custom_dir.glob("*.svg"))), 38)
        for char, stroke_count in expected_stroke_counts.items():
            with self.subTest(char=char):
                path = custom_dir / f"{ord(char):05x}.svg"
                self.assertTrue(path.is_file())
                strokes = load_kanjivg_strokes(char, DEFAULT_KANJIVG_DIR, 2.0) or []
                self.assertEqual(len(strokes), stroke_count)

    def test_project_authored_japanese_bracket_resources(self) -> None:
        expected_stroke_counts = {
            "「": 1, "」": 1, "『": 2, "』": 2,
            "【": 1, "】": 1, "〈": 1, "〉": 1,
            "《": 2, "》": 2, "〔": 1, "〕": 1,
        }
        custom_dir = Path(__file__).resolve().parents[1] / "data" / "custom_strokes"
        for char, stroke_count in expected_stroke_counts.items():
            with self.subTest(char=char):
                self.assertTrue((custom_dir / f"{ord(char):05x}.svg").is_file())
                strokes = load_kanjivg_strokes(char, DEFAULT_KANJIVG_DIR, 2.0) or []
                self.assertEqual(len(strokes), stroke_count)
        self.assertEqual(
            load_kanjivg_strokes("｢", DEFAULT_KANJIVG_DIR, 2.0),
            load_kanjivg_strokes("「", DEFAULT_KANJIVG_DIR, 2.0),
        )
        self.assertEqual(
            load_kanjivg_strokes("｣", DEFAULT_KANJIVG_DIR, 2.0),
            load_kanjivg_strokes("」", DEFAULT_KANJIVG_DIR, 2.0),
        )

    def test_all_halfwidth_katakana_resolve_to_strokes(self) -> None:
        self.assertEqual(len(HALFWIDTH_KATAKANA), 56)
        self.assertEqual(HALFWIDTH_VOICING_MARKS, frozenset("ﾞﾟ"))
        for char in HALFWIDTH_KATAKANA | HALFWIDTH_VOICING_MARKS:
            with self.subTest(char=char):
                self.assertTrue(is_supported_writing_char(char))
                self.assertTrue(load_kanjivg_strokes(char, DEFAULT_KANJIVG_DIR, 2.0))

    def test_halfwidth_voiced_pairs_are_single_half_cell_tokens(self) -> None:
        tokens = tokenize_writing_text("ｶﾞ ﾊﾟ ｳﾞ ﾜﾞ ｦﾞ")
        written = [token for token in tokens if not token.is_whitespace]
        self.assertEqual([token.text for token in written], ["ｶﾞ", "ﾊﾟ", "ｳﾞ", "ﾜﾞ", "ｦﾞ"])
        self.assertTrue(all(token.source_length == 2 for token in written))
        self.assertTrue(all(token.span == 0.5 for token in written))
        self.assertEqual([token.resource_char for token in written], ["ガ", "パ", "ヴ", "ヷ", "ヺ"])

        result = build_layout(
            "ｶﾞﾊﾟ",
            DEFAULT_KANJIVG_DIR,
            LayoutSettings(start_x=0, start_y=0, general=GeneralSettings(font_size=100, char_gap=10)),
        )
        self.assertEqual([item.char for item in result.placements], ["ｶﾞ", "ﾊﾟ"])
        self.assertEqual([item.source_index for item in result.placements], [0, 2])
        self.assertEqual([item.x for item in result.placements], [0, 60])

        valid_pairs = []
        for base in HALFWIDTH_KATAKANA:
            for mark in HALFWIDTH_VOICING_MARKS:
                pair = base + mark
                if len(unicodedata.normalize("NFKC", pair)) == 1:
                    valid_pairs.append(pair)
        self.assertEqual(len(valid_pairs), 28)
        for pair in valid_pairs:
            with self.subTest(pair=pair):
                token = tokenize_writing_text(pair)[0]
                self.assertEqual(token.text, pair)
                self.assertEqual(token.source_length, 2)
                self.assertEqual(token.span, 0.5)
                self.assertTrue(load_kanjivg_strokes(token.resource_char, DEFAULT_KANJIVG_DIR, 2.0))

    def test_invalid_halfwidth_voicing_pair_stays_separate(self) -> None:
        tokens = tokenize_writing_text("ｱﾞ")
        self.assertEqual([token.text for token in tokens], ["ｱ", "ﾞ"])
        self.assertEqual([token.resource_char for token in tokens], ["ア", "゛"])
        self.assertEqual([token.source_index for token in tokens], [0, 1])
        self.assertEqual([token.span for token in tokens], [0.5, 0.5])

    def test_half_and_fullwidth_pairs_share_source_strokes(self) -> None:
        self.assertEqual(len(STROKE_ALIASES), 157)
        for alias, canonical in STROKE_ALIASES.items():
            with self.subTest(alias=alias, canonical=canonical):
                alias_strokes = load_kanjivg_strokes(alias, DEFAULT_KANJIVG_DIR, 2.0)
                canonical_strokes = load_kanjivg_strokes(canonical, DEFAULT_KANJIVG_DIR, 2.0)
                self.assertEqual(alias_strokes, canonical_strokes)

    def test_horizontal_symbols_preserve_native_viewbox_coordinates(self) -> None:
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
                        end_x=218,
                        end_y=109,
                        general=GeneralSettings(font_size=109),
                    ),
                )
                for actual, expected in zip(result.paths, source, strict=True):
                    self.assertEqual(len(actual), len(expected))
                    for actual_point, expected_point in zip(actual, expected, strict=True):
                        expected_x = expected_point[0] * (0.5 if is_halfwidth_char(char) else 1.0)
                        self.assertAlmostEqual(actual_point[0], expected_x)
                        self.assertAlmostEqual(actual_point[1], expected_point[1])

    def test_vertical_rotation_matches_clockwise_source_transform(self) -> None:
        characters = "AＡ1１()（）[]［］{}｛｝ーｰ-－_＿~～" + "".join(JAPANESE_BRACKETS)
        self.assertTrue(set(characters) <= VERTICAL_ROTATE_CHARS)
        for char in characters:
            with self.subTest(char=char):
                source = load_kanjivg_strokes(char, DEFAULT_KANJIVG_DIR, 2.0) or []
                vertical = build_layout(
                    char,
                    DEFAULT_KANJIVG_DIR,
                    LayoutSettings(
                        start_x=0,
                        start_y=0,
                        end_x=109,
                        end_y=218,
                        general=GeneralSettings(font_size=109, orientation=Orientation.VERTICAL),
                    ),
                )
                for actual, expected in zip(vertical.paths, source, strict=True):
                    for actual_point, expected_point in zip(actual, expected, strict=True):
                        expected_x = 109.0 - expected_point[1]
                        expected_y = expected_point[0] * (0.5 if is_halfwidth_char(char) else 1.0)
                        self.assertAlmostEqual(actual_point[0], expected_x)
                        self.assertAlmostEqual(actual_point[1], expected_y)
                self.assertEqual(vertical.placements[0].rotation_degrees, 90)

    def test_vertical_japanese_punctuation_moves_to_upper_right(self) -> None:
        self.assertEqual(VERTICAL_CORNER_PUNCTUATION, frozenset("、､。｡"))
        for char in VERTICAL_CORNER_PUNCTUATION:
            with self.subTest(char=char):
                horizontal = build_layout(
                    char,
                    DEFAULT_KANJIVG_DIR,
                    LayoutSettings(start_x=0, start_y=0, general=GeneralSettings(font_size=109)),
                )
                vertical = build_layout(
                    char,
                    DEFAULT_KANJIVG_DIR,
                    LayoutSettings(
                        start_x=0,
                        start_y=0,
                        general=GeneralSettings(font_size=109, orientation=Orientation.VERTICAL),
                    ),
                )
                horizontal_bounds = bounds(horizontal.paths)
                vertical_bounds = bounds(vertical.paths)
                self.assertGreater(vertical_bounds[0], horizontal_bounds[0])
                self.assertLess(vertical_bounds[1], horizontal_bounds[1])
                horizontal_width = horizontal_bounds[2] - horizontal_bounds[0]
                horizontal_height = horizontal_bounds[3] - horizontal_bounds[1]
                self.assertAlmostEqual(
                    vertical_bounds[2] - vertical_bounds[0],
                    horizontal_width * (2 if is_halfwidth_char(char) else 1),
                    delta=0.01,
                )
                self.assertAlmostEqual(
                    vertical_bounds[3] - vertical_bounds[1],
                    horizontal_height * (0.5 if is_halfwidth_char(char) else 1),
                    delta=0.01,
                )

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
                expected_center_x = 27.25 if is_halfwidth_char(char) else 54.5
                expected_width = 6.0 if is_halfwidth_char(char) else 12.0
                self.assertAlmostEqual((min_x + max_x) / 2, expected_center_x)
                self.assertAlmostEqual((min_y + max_y) / 2, 53.0)
                self.assertAlmostEqual(max_x - min_x, expected_width)
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
                            end_y=2000,
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

    def test_halfwidth_and_fullwidth_alphanumeric_spans(self) -> None:
        result = build_layout(
            "AＢ1２",
            DEFAULT_KANJIVG_DIR,
            LayoutSettings(
                start_x=0,
                start_y=0,
                end_x=400,
                end_y=200,
                general=GeneralSettings(font_size=100, char_gap=10),
            ),
        )
        self.assertEqual([placement.span for placement in result.placements], [0.5, 1.0, 0.5, 1.0])
        self.assertEqual([placement.x for placement in result.placements], [0, 60, 170, 230])

        vertical = build_layout(
            "AＢ1２",
            DEFAULT_KANJIVG_DIR,
            LayoutSettings(
                start_x=0,
                start_y=0,
                end_x=200,
                end_y=400,
                general=GeneralSettings(font_size=100, char_gap=10, orientation=Orientation.VERTICAL),
            ),
        )
        self.assertEqual([placement.y for placement in vertical.placements], [0, 60, 170, 230])

    def test_left_flow_uses_each_character_actual_extent(self) -> None:
        result = build_layout(
            "AＢ1２",
            DEFAULT_KANJIVG_DIR,
            LayoutSettings(
                start_x=400,
                start_y=0,
                end_x=0,
                end_y=200,
                general=GeneralSettings(font_size=100, char_gap=10, flow=FlowDirection.LEFT),
            ),
        )
        self.assertEqual([placement.x for placement in result.placements], [350, 240, 180, 70])

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
                        cell_width = 109 * (placement.span if orientation is Orientation.HORIZONTAL else 1.0)
                        cell_height = 109 * (placement.span if orientation is Orientation.VERTICAL else 1.0)
                        self.assertTrue(
                            all(
                                placement.x <= x <= placement.x + cell_width
                                and placement.y <= y <= placement.y + cell_height
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
                end_x=2000,
                end_y=2000,
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
