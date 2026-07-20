from __future__ import annotations

import csv
import importlib.util
import json
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from mouse_writer_pro import (
    BOX_DRAWING_SYMBOLS,
    COMMON_SYMBOL_VARIANTS,
    SUPPORTED_EMOTICON_SYMBOLS,
    SYMBOL_CATALOG,
    VERTICAL_COMMON_BRACKETS,
    load_kanjivg_strokes,
    stroke_file_for_char,
    DEFAULT_KANJIVG_DIR,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "symbol_manifest.json"
CANDIDATES = ROOT / "data" / "symbol_candidates.csv"
DOCUMENT = ROOT / "SUPPORTED_SYMBOLS.md"
MANAGER_PATH = ROOT / "scripts" / "manage_symbol_catalog.py"
GENERATOR_PATH = ROOT / "scripts" / "generate_symbol_comparisons.py"


def load_script(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load symbol catalog manager")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class SymbolCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.records = cls.payload["symbols"]

    def test_manifest_is_the_exact_runtime_source(self) -> None:
        self.assertEqual(self.payload["schema_version"], 1)
        self.assertEqual(self.payload["catalog_version"], "2.7.2")
        self.assertEqual(len(self.records), len({record["symbol"] for record in self.records}))
        groups: dict[str, set[str]] = {}
        for record in self.records:
            groups.setdefault(record["group"], set()).add(record["symbol"])
        self.assertEqual(frozenset(groups["emoticon"]), SUPPORTED_EMOTICON_SYMBOLS)
        self.assertEqual(frozenset(groups["common_variant"]), COMMON_SYMBOL_VARIANTS)
        self.assertEqual(frozenset(groups["box_drawing"]), BOX_DRAWING_SYMBOLS)
        self.assertEqual(VERTICAL_COMMON_BRACKETS, SYMBOL_CATALOG.vertical_rotating)

    def test_manifest_and_candidate_list_pass_strict_validation(self) -> None:
        manager = load_script("manage_symbol_catalog", MANAGER_PATH)
        self.assertEqual(manager.validate_manifest(MANIFEST), [])
        self.assertEqual(manager.validate_candidates(CANDIDATES), [])

    def test_supported_document_is_generated_without_drift(self) -> None:
        manager = load_script("manage_symbol_catalog", MANAGER_PATH)
        with tempfile.TemporaryDirectory() as directory:
            generated = Path(directory) / "SUPPORTED_SYMBOLS.md"
            manager.render_document(MANIFEST, generated)
            self.assertEqual(generated.read_bytes(), DOCUMENT.read_bytes())

    def test_stroke_count_sync_updates_stale_metadata(self) -> None:
        manager = load_script("manage_symbol_catalog_sync", MANAGER_PATH)
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "symbol_manifest.json"
            payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
            payload["symbols"][0]["expected_strokes"] = -1
            manifest.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            self.assertEqual(manager.sync_stroke_counts(manifest), 1)
            synchronized = json.loads(manifest.read_text(encoding="utf-8"))
            expected = manager.svg_stroke_count(ROOT / synchronized["symbols"][0]["svg"])
            self.assertEqual(synchronized["symbols"][0]["expected_strokes"], expected)

    def test_manifest_resources_and_expected_strokes_are_consistent(self) -> None:
        codepoints: set[int] = set()
        svg_paths: set[str] = set()
        for record in self.records:
            char = record["symbol"]
            codepoint = ord(char)
            with self.subTest(codepoint=record["codepoint"]):
                self.assertEqual(len(char), 1)
                self.assertEqual(record["codepoint"], f"U+{codepoint:04X}")
                self.assertNotIn(codepoint, codepoints)
                self.assertNotIn(record["svg"], svg_paths)
                codepoints.add(codepoint)
                svg_paths.add(record["svg"])
                svg_path = ROOT / record["svg"]
                root = ET.parse(svg_path).getroot()
                self.assertEqual(root.attrib.get("viewBox"), "0 0 109 109")
                paths = [element for element in root.iter() if element.tag.endswith("path")]
                self.assertEqual(len(paths), record["expected_strokes"])
                self.assertEqual(stroke_file_for_char(char, DEFAULT_KANJIVG_DIR), svg_path)
                self.assertTrue(load_kanjivg_strokes(char, DEFAULT_KANJIVG_DIR, 1.5))

    def test_disconnected_marks_remain_separate_mouse_strokes(self) -> None:
        expected_counts = {"¨": 2, "∷": 4, "ᐕ": 4, "ᐖ": 4}
        for char, expected in expected_counts.items():
            with self.subTest(char=char):
                svg_path = ROOT / "data" / "custom_strokes" / f"{ord(char):05x}.svg"
                root = ET.parse(svg_path).getroot()
                path_data = [element.attrib["d"] for element in root.iter() if element.tag.endswith("path")]
                self.assertEqual(len(path_data), expected)
                self.assertTrue(all(data.count("M") == 1 for data in path_data))
                self.assertEqual(len(load_kanjivg_strokes(char, DEFAULT_KANJIVG_DIR, 1.5) or []), expected)

    def test_candidate_list_has_stable_workflow_columns(self) -> None:
        with CANDIDATES.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            self.assertEqual(
                reader.fieldnames,
                ["symbol", "codepoint", "category", "status", "family", "use_case", "reason", "notes"],
            )

    def test_comparison_generator_uses_fixed_card_and_valid_links(self) -> None:
        generator = load_script("generate_symbol_comparisons", GENERATOR_PATH)
        record = next(record for record in self.records if record["symbol"] == "¨")
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            card, font_name = generator.make_card(record, 1, output / "cards" / "001-u00a8.png")
            generator.make_overview([card], output / "overview.png")
            generator.write_checklist([record], [card], [font_name], output / "checklist.md", "test")
            with Image.open(card) as image:
                self.assertEqual(image.size, (510, 230))
            with Image.open(output / "overview.png") as image:
                self.assertEqual(image.size, (1280, 72))
            checklist = (output / "checklist.md").read_text(encoding="utf-8")
            self.assertIn("cards/001-u00a8.png", checklist)
            self.assertIn("Pending", checklist)
            self.assertTrue(card.is_file())

    def test_comparison_link_falls_back_to_file_uri_across_drives(self) -> None:
        generator = load_script("generate_symbol_comparisons_cross_drive", GENERATOR_PATH)
        target = ROOT / "data" / "custom_strokes" / "000a8.svg"
        with patch.object(generator.os.path, "relpath", side_effect=ValueError):
            link = generator.markdown_link_path(target, Path(tempfile.gettempdir()))
        self.assertTrue(link.startswith("file:///"), link)


if __name__ == "__main__":
    unittest.main()
