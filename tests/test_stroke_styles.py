# -*- coding: utf-8 -*-

from __future__ import annotations

import hashlib
import json
import re
import unittest
import xml.etree.ElementTree as ET
import zipfile

from mouse_writer_pro import (
    BUNDLE_DIR,
    DEFAULT_KANJIVG_DIR,
    EnvironmentSettings,
    GeneralSettings,
    LayoutSettings,
    Orientation,
    build_layout,
    load_kanjivg_strokes,
)
from stroke_styles import DEFAULT_STROKE_STYLE_ID, discover_stroke_styles


EXPECTED_STYLES = {
    "zen-kurenaido": {
        "version": "Version 1.001",
        "commit": "2edac135aa83e34640ec569d1d27520c3400e9b7",
        "font_sha256": "58b8d930d9fc10c8a5810c085bae378dacb98d0779073ee6d53d919f19ee6a4f",
        "archive_sha256": "c97e1f5efe171dd01df4dd96fb0e7f1eb16d9e36c2a0b1f7f24ec03b87670b83",
        "glyphs": 6591,
        "fallback": 111,
    },
    "hachi-maru-pop": {
        "version": "Version 1.300",
        "commit": "252adbcc5e3722bd514c424c4a4395127f18d73c",
        "font_sha256": "78408910c8f1a2f174a279cbc1484b48b71780039eba3fe1be2bfcc5d4df3f98",
        "archive_sha256": "69f92d37a0a3711ccd0cf1ae9d28be02a5246c6f1749cc2a11c453da0b21f065",
        "glyphs": 6609,
        "fallback": 93,
    },
    "yomogi": {
        "version": "Version 3.100",
        "commit": "2dcc1a21e9ee7cb66606d0be9099752504efe559",
        "font_sha256": "3424e34bb951e89bf5dd2554a65d8964335ea3c0560f8d1ea9aa3591ef73cba9",
        "archive_sha256": "073f83a6f6351f3d1c7400cd4253473a5ec21a22d787ca0fa98156781205812d",
        "glyphs": 6606,
        "fallback": 96,
    },
}


class StrokeStylePackTests(unittest.TestCase):
    def test_formal_three_fonts_are_discoverable_with_ofl_provenance(self) -> None:
        discovered = discover_stroke_styles(BUNDLE_DIR)
        styles = {style.id: style for style in discovered}
        self.assertEqual(set(styles), {DEFAULT_STROKE_STYLE_ID, *EXPECTED_STYLES})
        self.assertEqual([style.id for style in discovered], [DEFAULT_STROKE_STYLE_ID, *EXPECTED_STYLES])
        for style_id, expected in EXPECTED_STYLES.items():
            pack_dir = BUNDLE_DIR / "data/stroke_styles" / style_id
            manifest = json.loads((pack_dir / "manifest.json").read_text(encoding="utf-8"))
            archive = pack_dir / manifest["strokes_archive"]
            self.assertEqual(manifest["license"]["id"], "OFL-1.1")
            self.assertEqual(manifest["license"]["derivative_data_license"], "OFL-1.1")
            self.assertEqual(manifest["source"]["font_version"], expected["version"])
            self.assertEqual(manifest["source"]["commit"], expected["commit"])
            self.assertEqual(manifest["source"]["sha256"], expected["font_sha256"])
            self.assertEqual(manifest["conversion"]["generated_glyphs"], expected["glyphs"])
            self.assertEqual(manifest["conversion"]["fallback_glyphs"], expected["fallback"])
            self.assertEqual(manifest["conversion"]["source_geometry"], "source font outlines only")
            self.assertFalse(manifest["conversion"]["geometry_changed_during_promotion"])
            self.assertEqual(manifest["quality"]["status"], "formal-with-limited-human-review")
            self.assertEqual(manifest["quality"]["human_approved_characters_total"], 863)
            self.assertFalse(manifest["quality"]["image_reconstruction_r1_overrides_included"])
            license_text = (pack_dir / "OFL.txt").read_text(encoding="utf-8")
            self.assertIn(manifest["source"]["copyright"], license_text)
            self.assertIn("SIL Open Font License", license_text)
            self.assertIn("Original copyright:", (pack_dir / "SOURCE.md").read_text(encoding="utf-8"))
            self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), manifest["strokes_archive_sha256"])
            self.assertEqual(manifest["strokes_archive_sha256"], expected["archive_sha256"])

    def test_every_archived_svg_follows_font_skeleton_contract(self) -> None:
        filename_pattern = re.compile(r"strokes/[0-9a-f]{5}\.svg\Z")
        for style_id, expected in EXPECTED_STYLES.items():
            pack_dir = BUNDLE_DIR / "data/stroke_styles" / style_id
            manifest = json.loads((pack_dir / "manifest.json").read_text(encoding="utf-8"))
            with zipfile.ZipFile(pack_dir / manifest["strokes_archive"]) as archive:
                names = archive.namelist()
                self.assertEqual(len(names), expected["glyphs"])
                self.assertEqual(names, sorted(names))
                for name in names:
                    self.assertRegex(name, filename_pattern)
                    root = ET.fromstring(archive.read(name))
                    self.assertEqual(root.attrib.get("viewBox"), "0 0 109 109")
                    paths = [element for element in root.iter() if element.tag.endswith("path")]
                    self.assertTrue(paths)
                    for element in paths:
                        self.assertRegex(element.attrib.get("id", ""), rf"^{re.escape(style_id)}:[0-9a-f]{{5}}-full-n[1-9][0-9]*$")
                        commands = re.findall(r"[A-Za-z]", element.attrib.get("d", ""))
                        self.assertTrue(commands)
                        self.assertTrue(set(commands) <= {"M", "L"})

    def test_runtime_fit_retains_base_stroke_count_and_changes_geometry(self) -> None:
        for style_id in EXPECTED_STYLES:
            for char in "あ永語日":
                base = load_kanjivg_strokes(char, DEFAULT_KANJIVG_DIR, 1.2)
                styled = load_kanjivg_strokes(char, DEFAULT_KANJIVG_DIR, 1.2, stroke_style=style_id)
                self.assertIsNotNone(base)
                self.assertIsNotNone(styled)
                assert base is not None and styled is not None
                self.assertEqual(len(styled), len(base))
                self.assertNotEqual(styled, base)

    def test_all_styles_build_horizontal_and_vertical_layouts(self) -> None:
        for style_id in EXPECTED_STYLES:
            for orientation in Orientation:
                result = build_layout(
                    "あ永語日",
                    DEFAULT_KANJIVG_DIR,
                    LayoutSettings(
                        start_x=0,
                        start_y=0,
                        general=GeneralSettings(
                            font_size=109,
                            orientation=orientation,
                            stroke_style=style_id,
                        ),
                    ),
                    EnvironmentSettings(sample_spacing=2.0),
                )
                self.assertTrue(result.paths)
                self.assertEqual(len(result.placements), 4)


if __name__ == "__main__":
    unittest.main()
