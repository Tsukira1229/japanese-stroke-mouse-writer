from __future__ import annotations

import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from mouse_writer_pro import (
    COMMON_SYMBOL_VARIANTS,
    DEFAULT_KANJIVG_DIR,
    EnvironmentSettings,
    FlowDirection,
    GeneralSettings,
    LayoutSettings,
    Orientation,
    STROKE_ALIASES,
    SUPPORTED_SYMBOLS,
    VERTICAL_COMMON_BRACKETS,
    build_layout,
    is_supported_writing_char,
    load_kanjivg_strokes,
    stroke_file_for_char,
    tokenize_writing_text,
)


ROOT = Path(__file__).resolve().parents[1]
CUSTOM_DIR = ROOT / "data/custom_strokes"
EXPECTED = frozenset(
    "☆★⚝⭐⭑⭒"
    "○●◯◦"
    "■▪▫◻◼◽◾"
    "◆◈♢♦"
    "△▲▼▷▶◁◀▴▵▸▹▾▿◂◃"
    "✓✔✕✖✗✘"
    "←↑→↓↔↕↖↗↘↙⇐⇑⇒⇓⇔⇕"
    "⁅⁆❨❩❪❫❬❭❰❱❲❳❴❵"
    "±×÷≤≥∞√∏∫∂∆∈∉∋∅⊕⊗"
)
ARROWS = frozenset("←↑→↓↔↕↖↗↘↙⇐⇑⇒⇓⇔⇕")


class CommonSymbolVariantTests(unittest.TestCase):
    def test_exact_set_uses_direct_codepoint_resources(self) -> None:
        self.assertEqual(len(EXPECTED), 89)
        self.assertEqual(COMMON_SYMBOL_VARIANTS, EXPECTED)
        self.assertTrue(EXPECTED <= SUPPORTED_SYMBOLS)
        self.assertTrue(EXPECTED.isdisjoint(STROKE_ALIASES))
        for char in EXPECTED:
            with self.subTest(char=char):
                path = stroke_file_for_char(char, DEFAULT_KANJIVG_DIR)
                self.assertEqual(path, CUSTOM_DIR / f"{ord(char):05x}.svg")
                self.assertTrue(path.is_file())
                self.assertTrue(is_supported_writing_char(char))
        self.assertEqual(stroke_file_for_char("☆", DEFAULT_KANJIVG_DIR).name, "02606.svg")

    def test_svg_contract_and_stroke_ids(self) -> None:
        for char in EXPECTED:
            with self.subTest(char=char):
                root = ET.parse(CUSTOM_DIR / f"{ord(char):05x}.svg").getroot()
                self.assertEqual(root.attrib.get("viewBox"), "0 0 109 109")
                strokes = [element for element in root.iter() if element.tag.endswith("path")]
                self.assertTrue(strokes)
                self.assertEqual(
                    [stroke.attrib.get("id") for stroke in strokes],
                    [f"custom:{ord(char):05x}-s{index}" for index in range(1, len(strokes) + 1)],
                )
                for stroke in strokes:
                    data = stroke.attrib.get("d", "")
                    self.assertEqual(len(re.findall(r"(?<![A-Za-z])M", data)), 1)
                    self.assertRegex(data, r"^M")
                    values = [float(value) for value in re.findall(r"-?\d+(?:\.\d+)?", data)]
                    self.assertTrue(values)
                    self.assertTrue(all(0.0 <= value <= 109.0 for value in values))

    def test_filled_shapes_have_more_pen_strokes_than_outline_variants(self) -> None:
        pairs = [
            ("☆", "★"), ("○", "●"), ("▫", "▪"), ("◻", "◼"),
            ("◽", "◾"), ("♢", "♦"), ("△", "▲"), ("▵", "▴"),
            ("▹", "▸"), ("▿", "▾"), ("◃", "◂"),
        ]
        for outline, filled in pairs:
            with self.subTest(outline=outline, filled=filled):
                outline_paths = load_kanjivg_strokes(outline, DEFAULT_KANJIVG_DIR, 2.0) or []
                filled_paths = load_kanjivg_strokes(filled, DEFAULT_KANJIVG_DIR, 2.0) or []
                self.assertGreater(len(filled_paths), len(outline_paths))

    def test_variation_selector_uses_same_star_resource_and_one_cell(self) -> None:
        plain = tokenize_writing_text("⭐")
        emoji_style = tokenize_writing_text("⭐\ufe0f")
        text_style = tokenize_writing_text("⭐\ufe0e")
        self.assertEqual(len(plain), 1)
        self.assertEqual(len(emoji_style), 1)
        self.assertEqual(len(text_style), 1)
        self.assertEqual(plain[0].resource_char, "⭐")
        self.assertEqual(emoji_style[0].resource_char, "⭐")
        self.assertEqual(text_style[0].resource_char, "⭐")
        self.assertEqual(emoji_style[0].span, plain[0].span)
        self.assertEqual(text_style[0].span, plain[0].span)

    def test_vertical_rotation_is_limited_to_new_brackets(self) -> None:
        for char in EXPECTED:
            with self.subTest(char=char):
                result = build_layout(
                    char,
                    DEFAULT_KANJIVG_DIR,
                    LayoutSettings(
                        start_x=0,
                        start_y=0,
                        general=GeneralSettings(font_size=109, orientation=Orientation.VERTICAL),
                    ),
                    EnvironmentSettings(sample_spacing=2.0),
                )
                expected_rotation = 90 if char in VERTICAL_COMMON_BRACKETS else 0
                self.assertEqual(result.placements[0].rotation_degrees, expected_rotation)
                if char in ARROWS:
                    self.assertEqual(result.placements[0].rotation_degrees, 0)

    def test_every_symbol_builds_nonempty_in_all_layout_directions(self) -> None:
        for char in EXPECTED:
            for orientation in Orientation:
                for flow in FlowDirection:
                    with self.subTest(char=char, orientation=orientation, flow=flow):
                        result = build_layout(
                            char,
                            DEFAULT_KANJIVG_DIR,
                            LayoutSettings(
                                start_x=109 if flow is FlowDirection.LEFT else 0,
                                start_y=0,
                                general=GeneralSettings(
                                    font_size=109,
                                    char_gap=0,
                                    line_gap=0,
                                    orientation=orientation,
                                    flow=flow,
                                ),
                            ),
                            EnvironmentSettings(sample_spacing=2.0),
                        )
                        self.assertTrue(result.paths)
                        min_x, min_y, max_x, max_y = result.canvas_bounds
                        self.assertTrue(
                            all(
                                min_x - 0.01 <= x <= max_x + 0.01
                                and min_y - 0.01 <= y <= max_y + 0.01
                                for path in result.paths
                                for x, y in path
                            )
                        )


if __name__ == "__main__":
    unittest.main()
