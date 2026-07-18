# -*- coding: utf-8 -*-

from __future__ import annotations

import hashlib
import json
import math
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from unittest.mock import patch

import mouse_writer_pro as core
from mouse_writer_pro import (
    BUNDLE_DIR,
    DEFAULT_KANJIVG_DIR,
    EnvironmentSettings,
    GeneralSettings,
    LayoutSettings,
    Orientation,
    StrokeStyleResourceError,
    build_layout,
    load_glyph_paths,
    load_kanjivg_strokes,
    sample_svg_path,
)
from stroke_styles import DEFAULT_STROKE_STYLE_ID, discover_stroke_styles


PACK_DIR = BUNDLE_DIR / "data" / "stroke_styles" / "yomogi"
REVIEWED_PACKS = {
    "zen-kurenaido": {"generated": 6591, "fallback": 111, "archive": "be8bc959480909f88a203f817ba546314ec49b4b9282d6252885923413c0b3c5"},
    "hachi-maru-pop": {"generated": 6608, "fallback": 94, "archive": "f532cad5a310239553db7252e0abaeaed4fcbd7df116e477948e6709027e223e"},
}
NUMBER_RE = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")


class YomogiDirectStyleTests(unittest.TestCase):
    def test_formal_pack_provenance_and_counts(self) -> None:
        styles = discover_stroke_styles(BUNDLE_DIR)
        self.assertEqual(
            [style.id for style in styles],
            [DEFAULT_STROKE_STYLE_ID, "yomogi", "zen-kurenaido", "hachi-maru-pop"],
        )
        style = styles[1]
        self.assertEqual(style.runtime_mode, "direct")
        self.assertEqual(style.generated_glyphs, 6608)
        self.assertEqual(len(style.fallback_codepoints), 96)
        self.assertEqual(style.style_only_codepoints, frozenset({0x309F, 0x30FF}))
        self.assertEqual(style.view_box, (0.0, 0.0, 109.0, 109.0))
        manifest = json.loads((PACK_DIR / "manifest.json").read_text(encoding="utf-8"))
        conversion = manifest["conversion"]
        self.assertEqual(conversion["catalog_codepoints"], 6702)
        self.assertEqual(conversion["catalog_eligible_glyphs"], 6606)
        self.assertEqual(conversion["style_only_codepoints"], ["U+309F", "U+30FF"])
        self.assertEqual(conversion["eligible_glyphs"], 6608)
        self.assertEqual(conversion["approved_geometry_glyphs"], 191)
        self.assertEqual(conversion["fallback_glyphs"], 96)
        self.assertEqual(conversion["source_font_missing_glyphs"], 87)
        self.assertEqual(conversion["conversion_ineligible_glyphs"], 9)
        archive = PACK_DIR / manifest["strokes_archive"]
        self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), manifest["strokes_archive_sha256"])
        self.assertIn("SIL Open Font License", (PACK_DIR / "OFL.txt").read_text(encoding="utf-8"))
        source = (PACK_DIR / "SOURCE.md").read_text(encoding="utf-8")
        self.assertIn("Original copyright:", source)
        self.assertIn("no KanjiVG projection", source)

    def test_every_archived_svg_follows_direct_contract(self) -> None:
        with zipfile.ZipFile(PACK_DIR / "strokes.zip") as archive:
            names = archive.namelist()
            self.assertEqual(len(names), 6608)
            self.assertEqual(names, sorted(names))
            self.assertIn("strokes/0309f.svg", names)
            self.assertIn("strokes/030ff.svg", names)
            for name in names:
                self.assertRegex(name, r"^strokes/[0-9a-f]{5}\.svg$")
                root = ET.fromstring(archive.read(name))
                self.assertEqual(root.attrib.get("viewBox"), "0 0 109 109")
                self.assertEqual(root.attrib.get("data-runtime-mode"), "direct")
                self.assertEqual(root.attrib.get("data-path-semantics"), "visual-centerline")
                self.assertEqual(root.attrib.get("data-order-semantics"), "none")
                paths = [node for node in root.iter() if node.tag.endswith("path")]
                self.assertTrue(paths)
                for node in paths:
                    data = node.attrib["d"]
                    self.assertTrue(set(re.findall(r"[A-Za-z]", data)) <= {"M", "L"})
                    values = [float(value) for value in NUMBER_RE.findall(data)]
                    points = list(zip(values[::2], values[1::2]))
                    self.assertGreaterEqual(len(points), 2)
                    self.assertFalse(any(a == b for a, b in zip(points, points[1:])))
                    self.assertGreaterEqual(sum(math.dist(a, b) for a, b in zip(points, points[1:])), 3.0 - 1e-9)

    def test_runtime_loads_direct_svg_without_kanjivg_projection(self) -> None:
        char = "龍"
        loaded = load_glyph_paths(char, DEFAULT_KANJIVG_DIR, 2.0, stroke_style="yomogi")
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded.actual_source, "yomogi")
        self.assertFalse(loaded.fallback_used)
        self.assertEqual(loaded.source_bounds, (0.0, 0.0, 109.0, 109.0))
        with zipfile.ZipFile(PACK_DIR / "strokes.zip") as archive:
            root = ET.fromstring(archive.read("strokes/09f8d.svg"))
        expected = [
            sample_svg_path(node.attrib["d"], 2.0)
            for node in root.iter()
            if node.tag.endswith("path")
        ]
        self.assertEqual(loaded.paths, expected)
        base = load_kanjivg_strokes(char, DEFAULT_KANJIVG_DIR, 2.0)
        self.assertIsNotNone(base)
        assert base is not None
        self.assertNotEqual(len(loaded.paths), len(base))

    def test_all_96_manifest_fallbacks_equal_base_kanjivg(self) -> None:
        fallback = json.loads((PACK_DIR / "fallback.json").read_text(encoding="utf-8"))
        self.assertEqual(len(fallback), 96)
        self.assertEqual(sum(row["reason"] == "source-font-missing" for row in fallback), 87)
        for row in fallback:
            char = chr(int(row["codepoint"][2:], 16))
            base = load_kanjivg_strokes(char, DEFAULT_KANJIVG_DIR, 2.0)
            styled = load_glyph_paths(char, DEFAULT_KANJIVG_DIR, 2.0, stroke_style="yomogi")
            self.assertIsNotNone(base, row["codepoint"])
            self.assertIsNotNone(styled, row["codepoint"])
            assert styled is not None
            self.assertTrue(styled.fallback_used)
            self.assertEqual(styled.actual_source, DEFAULT_STROKE_STYLE_ID)
            self.assertEqual(styled.paths, base)

    def test_style_only_kana_load_without_kanjivg_baseline(self) -> None:
        for char in "ゟヿ":
            self.assertIsNone(load_kanjivg_strokes(char, DEFAULT_KANJIVG_DIR, 2.0))
            styled = load_glyph_paths(char, DEFAULT_KANJIVG_DIR, 2.0, stroke_style="yomogi")
            self.assertIsNotNone(styled)
            assert styled is not None
            self.assertFalse(styled.fallback_used)

    def test_layout_preserves_full_109_viewbox(self) -> None:
        char = "區"
        loaded = load_glyph_paths(char, DEFAULT_KANJIVG_DIR, 2.0, stroke_style="yomogi")
        assert loaded is not None
        for orientation in Orientation:
            result = build_layout(
                char,
                DEFAULT_KANJIVG_DIR,
                LayoutSettings(start_x=0, start_y=0, general=GeneralSettings(font_size=109, orientation=orientation, stroke_style="yomogi")),
                EnvironmentSettings(sample_spacing=2.0),
            )
            self.assertEqual(result.paths, loaded.paths)
            self.assertFalse(result.style_fallback_chars)

    def test_missing_expected_archive_member_is_not_silent_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            bundle = Path(temporary)
            pack = bundle / "data" / "stroke_styles" / "yomogi"
            pack.mkdir(parents=True)
            with zipfile.ZipFile(pack / "strokes.zip", "w"):
                pass
            (pack / "fallback.json").write_text("[]\n", encoding="utf-8")
            (pack / "manifest.json").write_text(json.dumps({
                "id": "yomogi", "display_order": 10, "labels": {"en": "Yomogi"},
                "runtime_mode": "direct", "view_box": "0 0 109 109", "strokes_archive": "strokes.zip",
                "fallback_codepoints_file": "fallback.json", "fallback_style": "kanjivg",
                "source": {"font_name": "Yomogi Regular"}, "license": {"id": "OFL-1.1"},
                "conversion": {"eligible_glyphs": 1, "style_only_codepoints": ["U+309F"]},
            }), encoding="utf-8")
            core._open_stroke_style_archive.cache_clear()
            with patch.object(core, "BUNDLE_DIR", bundle):
                with self.assertRaises(StrokeStyleResourceError):
                    load_glyph_paths("日", DEFAULT_KANJIVG_DIR, 2.0, stroke_style="yomogi")
                with self.assertRaises(StrokeStyleResourceError):
                    load_glyph_paths("ゟ", DEFAULT_KANJIVG_DIR, 2.0, stroke_style="yomogi")
            core._open_stroke_style_archive.cache_clear()


class ReviewedDirectStyleTests(unittest.TestCase):
    def test_pack_counts_provenance_and_human_locks(self) -> None:
        styles = {style.id: style for style in discover_stroke_styles(BUNDLE_DIR)}
        for style_id, expected in REVIEWED_PACKS.items():
            with self.subTest(style=style_id):
                pack = BUNDLE_DIR / "data" / "stroke_styles" / style_id
                style = styles[style_id]
                self.assertEqual(style.generated_glyphs, expected["generated"])
                self.assertEqual(len(style.fallback_codepoints), expected["fallback"])
                self.assertEqual(style.view_box, (0.0, 0.0, 109.0, 109.0))
                self.assertEqual(style.style_only_codepoints, frozenset())
                self.assertEqual(hashlib.sha256((pack / "strokes.zip").read_bytes()).hexdigest(), expected["archive"])
                manifest = json.loads((pack / "manifest.json").read_text(encoding="utf-8"))
                self.assertEqual(manifest["conversion"]["approved_geometry_glyphs"], 389)
                review = json.loads((pack / "HUMAN_REVIEW.json").read_text(encoding="utf-8"))
                self.assertEqual(review["approved_glyphs"], 389)
                self.assertIn("SIL Open Font License", (pack / "OFL.txt").read_text(encoding="utf-8"))
                self.assertIn("Original copyright:", (pack / "SOURCE.md").read_text(encoding="utf-8"))

    def test_runtime_direct_loading_fallback_and_layout(self) -> None:
        for style_id in REVIEWED_PACKS:
            with self.subTest(style=style_id):
                loaded = load_glyph_paths("區", DEFAULT_KANJIVG_DIR, 2.0, stroke_style=style_id)
                self.assertIsNotNone(loaded)
                assert loaded is not None
                self.assertEqual(loaded.actual_source, style_id)
                self.assertFalse(loaded.fallback_used)
                self.assertEqual(loaded.source_bounds, (0.0, 0.0, 109.0, 109.0))
                result = build_layout(
                    "區",
                    DEFAULT_KANJIVG_DIR,
                    LayoutSettings(start_x=0, start_y=0, general=GeneralSettings(font_size=109, stroke_style=style_id)),
                    EnvironmentSettings(sample_spacing=2.0),
                )
                self.assertEqual(result.paths, loaded.paths)
                fallback = json.loads(
                    (BUNDLE_DIR / "data" / "stroke_styles" / style_id / "fallback.json").read_text(encoding="utf-8")
                )
                row = fallback[0]
                char = chr(int(row["codepoint"][2:], 16))
                styled = load_glyph_paths(char, DEFAULT_KANJIVG_DIR, 2.0, stroke_style=style_id)
                self.assertIsNotNone(styled)
                assert styled is not None
                self.assertTrue(styled.fallback_used)
                self.assertEqual(styled.actual_source, DEFAULT_STROKE_STYLE_ID)


if __name__ == "__main__":
    unittest.main()
