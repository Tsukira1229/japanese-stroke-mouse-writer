from __future__ import annotations

import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from mouse_writer_pro import (
    BOX_DRAWING_SYMBOLS,
    DEFAULT_KANJIVG_DIR,
    EnvironmentSettings,
    FlowDirection,
    GeneralSettings,
    LayoutSettings,
    Orientation,
    STROKE_ALIASES,
    SUPPORTED_SYMBOLS,
    build_layout,
    is_supported_writing_char,
    load_kanjivg_strokes,
    stroke_file_for_char,
    tokenize_writing_text,
)


ROOT = Path(__file__).resolve().parents[1]
CUSTOM_DIR = ROOT / "data/custom_strokes"


class BoxDrawingTests(unittest.TestCase):
    def test_complete_unicode_block_is_registered_with_direct_resources(self) -> None:
        expected = frozenset(chr(codepoint) for codepoint in range(0x2500, 0x2580))
        self.assertEqual(BOX_DRAWING_SYMBOLS, expected)
        self.assertTrue(expected <= SUPPORTED_SYMBOLS)
        self.assertTrue(expected.isdisjoint(STROKE_ALIASES))
        for char in expected:
            with self.subTest(char=char):
                expected_name = f"{ord(char):05x}.svg"
                path = stroke_file_for_char(char, DEFAULT_KANJIVG_DIR)
                self.assertEqual(path.name, expected_name)
                self.assertEqual(path.parent.resolve(), CUSTOM_DIR.resolve())
                self.assertTrue(is_supported_writing_char(char))

    def test_all_svg_resources_follow_the_centerline_contract(self) -> None:
        for codepoint in range(0x2500, 0x2580):
            with self.subTest(codepoint=f"U+{codepoint:04X}"):
                path = CUSTOM_DIR / f"{codepoint:05x}.svg"
                root = ET.parse(path).getroot()
                self.assertEqual(root.attrib.get("viewBox"), "0 0 109 109")
                strokes = [element for element in root.iter() if element.tag.endswith("path")]
                self.assertTrue(strokes)
                self.assertEqual(
                    [stroke.attrib.get("id") for stroke in strokes],
                    [f"custom:{codepoint:05x}-s{index}" for index in range(1, len(strokes) + 1)],
                )
                for stroke in strokes:
                    data = stroke.attrib.get("d", "")
                    self.assertEqual(len(re.findall(r"(?<![A-Za-z])M", data)), 1)
                    self.assertRegex(data, r"^M")
                    values = [float(value) for value in re.findall(r"-?\d+(?:\.\d+)?", data)]
                    self.assertTrue(values)
                    self.assertTrue(all(0.0 <= value <= 109.0 for value in values))

    def test_line_styles_have_distinct_stroke_counts(self) -> None:
        expected_counts = {
            "─": 1, "━": 3, "═": 2,
            "│": 1, "┃": 3, "║": 2,
            "┄": 3, "┅": 9, "┈": 4, "┉": 12,
            "╌": 2, "╍": 6,
            "┌": 2, "┏": 6, "╔": 4,
            "╱": 1, "╳": 2, "╴": 1, "╸": 3,
        }
        for char, expected in expected_counts.items():
            with self.subTest(char=char):
                strokes = load_kanjivg_strokes(char, DEFAULT_KANJIVG_DIR, 2.0) or []
                self.assertEqual(len(strokes), expected)

    def test_box_drawing_symbols_keep_full_cell_and_semantic_orientation(self) -> None:
        tokens = tokenize_writing_text("┏┷┓┃┗━")
        self.assertTrue(all(token.span == 1.0 for token in tokens))
        for orientation in Orientation:
            for flow in FlowDirection:
                with self.subTest(orientation=orientation, flow=flow):
                    result = build_layout(
                        "┏┷┓┃┗━",
                        DEFAULT_KANJIVG_DIR,
                        LayoutSettings(
                            start_x=700 if flow is FlowDirection.LEFT else 0,
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
                    self.assertTrue(all(item.rotation_degrees == 0 for item in result.placements))

    def test_every_symbol_builds_nonempty_paths_in_all_directions(self) -> None:
        for char in BOX_DRAWING_SYMBOLS:
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

    def test_zero_spacing_multiline_frame_uses_adjacent_full_cells(self) -> None:
        result = build_layout(
            "┏━┷━┓\n┃　　　┃\n┗━━━┛",
            DEFAULT_KANJIVG_DIR,
            LayoutSettings(
                start_x=0,
                start_y=0,
                general=GeneralSettings(font_size=109, char_gap=0, line_gap=0),
            ),
            EnvironmentSettings(sample_spacing=2.0),
        )
        rows: dict[float, list[float]] = {}
        for placement in result.placements:
            rows.setdefault(placement.y, []).append(placement.x)
        self.assertEqual(sorted(rows), [0, 109, 218])
        self.assertEqual(rows[0], [0, 109, 218, 327, 436])
        self.assertEqual(rows[109], [0, 109, 218, 327, 436])
        self.assertEqual(rows[218], [0, 109, 218, 327, 436])


if __name__ == "__main__":
    unittest.main()
