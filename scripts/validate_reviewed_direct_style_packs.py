# -*- coding: utf-8 -*-
"""Validate and reproduce the Zen Kurenaido and Hachi Maru Pop formal packs."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from promote_reviewed_direct_style_packs import PACKS


ROOT = Path(__file__).resolve().parents[1]
FORMAL_ROOT = ROOT / "data" / "stroke_styles"
PROMOTER = ROOT / "scripts" / "promote_reviewed_direct_style_packs.py"
NUMBER_RE = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_hashes(path: Path) -> dict[str, str]:
    return {item.relative_to(path).as_posix(): sha256(item) for item in sorted(path.rglob("*")) if item.is_file()}


def validate_svg(config_id: str, name: str, data: bytes) -> list[str]:
    root = ET.fromstring(data)
    expected = {
        "viewBox": "0 0 109 109",
        "data-source-style": config_id,
        "data-path-semantics": "visual-centerline",
        "data-order-semantics": "none",
        "data-runtime-mode": "direct",
    }
    for key, value in expected.items():
        if root.attrib.get(key) != value:
            raise RuntimeError(f"SVG metadata mismatch {key}: {name}")
    result = []
    for node in root.iter():
        if not node.tag.endswith("path"):
            continue
        path_data = node.attrib.get("d", "")
        if set(re.findall(r"[A-Za-z]", path_data)) - {"M", "L"}:
            raise RuntimeError(f"Non-M/L path: {name}")
        values = [float(value) for value in NUMBER_RE.findall(path_data)]
        points = list(zip(values[::2], values[1::2]))
        if len(points) < 2 or any(a == b for a, b in zip(points, points[1:])):
            raise RuntimeError(f"Invalid path points: {name}")
        if sum(math.dist(a, b) for a, b in zip(points, points[1:])) < 3.0 - 1e-9:
            raise RuntimeError(f"Micro path: {name}")
        result.append(path_data)
    if not result:
        raise RuntimeError(f"Empty SVG: {name}")
    return result


def validate_pack(config) -> dict[str, object]:
    pack = FORMAL_ROOT / config.id
    manifest = json.loads((pack / "manifest.json").read_text(encoding="utf-8"))
    conversion = manifest["conversion"]
    expected = {
        "catalog_codepoints": 6702,
        "eligible_glyphs": config.generated,
        "approved_geometry_glyphs": 389,
        "fallback_glyphs": config.fallback,
        "source_font_missing_glyphs": config.source_missing,
        "conversion_ineligible_glyphs": config.conversion_ineligible,
    }
    for key, value in expected.items():
        if conversion[key] != value:
            raise RuntimeError(f"Manifest count mismatch {config.id}/{key}")
    if sha256(pack / "strokes.zip") != config.archive_sha256:
        raise RuntimeError(f"Archive hash mismatch: {config.id}")
    fallback = json.loads((pack / "fallback.json").read_text(encoding="utf-8"))
    if len(fallback) != config.fallback:
        raise RuntimeError(f"Fallback count mismatch: {config.id}")
    review = json.loads((pack / "HUMAN_REVIEW.json").read_text(encoding="utf-8"))
    if review["approved_glyphs"] != 389 or review["source_archive_sha256"] != config.archive_sha256:
        raise RuntimeError(f"Review lock mismatch: {config.id}")
    approved = {int(row["codepoint"][2:], 16): row["path_d"] for row in review["glyphs"]}
    if len(approved) != 389:
        raise RuntimeError(f"Duplicate approval: {config.id}")
    with zipfile.ZipFile(pack / "strokes.zip") as archive:
        names = archive.namelist()
        if len(names) != config.generated or names != sorted(names):
            raise RuntimeError(f"Archive member count/order mismatch: {config.id}")
        for name in names:
            actual = validate_svg(config.id, name, archive.read(name))
            codepoint = int(Path(name).stem, 16)
            if codepoint in approved and approved[codepoint] != actual:
                raise RuntimeError(f"Approved geometry drift U+{codepoint:04X}: {config.id}")
    return {
        "style": config.id,
        "generated": config.generated,
        "fallback": config.fallback,
        "approved": 389,
        "archive_sha256": config.archive_sha256,
    }


def reproduce() -> None:
    with tempfile.TemporaryDirectory(prefix="direct-style-reproduce-", dir=ROOT / "build") as temporary:
        destination = Path(temporary)
        completed = subprocess.run(
            [sys.executable, str(PROMOTER), "--destination-root", str(destination)],
            cwd=ROOT,
            check=False,
        )
        if completed.returncode:
            raise RuntimeError("Reviewed style promotion reproduction failed")
        for config in PACKS:
            if tree_hashes(destination / config.id) != tree_hashes(FORMAL_ROOT / config.id):
                raise RuntimeError(f"Formal pack reproduction mismatch: {config.id}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reproduce", action="store_true")
    args = parser.parse_args(argv)
    result = [validate_pack(config) for config in PACKS]
    if args.reproduce:
        reproduce()
    print(json.dumps({"packs": result, "reproducible": args.reproduce}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
