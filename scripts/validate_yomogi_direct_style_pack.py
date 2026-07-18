# -*- coding: utf-8 -*-
"""Validate the complete Yomogi direct-centreline build and formal pack."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build" / "glyph-proof-yomogi-direct-full"
FORMAL = ROOT / "data" / "stroke_styles" / "yomogi"
GENERATOR = ROOT / "scripts" / "generate_yomogi_direct_style_pack.py"
EXPECTED_APPROVED = 191
NUMBER_RE = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_hashes(root: Path) -> dict[str, str]:
    return {path.relative_to(root).as_posix(): sha256(path) for path in sorted(root.rglob("*")) if path.is_file()}


def approved_geometry() -> dict[int, list[str]]:
    roots = (
        ROOT / "build" / "glyph-proof-yomogi-direct-kana-review" / "candidates",
        ROOT / "build" / "glyph-proof-yomogi-direct-kanji-pilot" / "candidates",
        ROOT / "build" / "glyph-proof-yomogi-direct-kanji-batch2" / "candidates",
    )
    result = {}
    for folder in roots:
        for path in sorted(folder.glob("*.svg")):
            result[int(path.stem, 16)] = [node.attrib["d"] for node in ET.parse(path).getroot().iter() if node.tag.endswith("path")]
    if len(result) != EXPECTED_APPROVED:
        raise RuntimeError(f"Approved geometry count drifted: {len(result)}")
    return result


def validate_svg(name: str, data: bytes) -> list[str]:
    root = ET.fromstring(data)
    expected = {
        "viewBox": "0 0 109 109",
        "data-source-style": "yomogi",
        "data-path-semantics": "visual-centerline",
        "data-order-semantics": "none",
        "data-runtime-mode": "direct",
    }
    for key, value in expected.items():
        if root.attrib.get(key) != value:
            raise RuntimeError(f"SVG metadata mismatch {key}: {name}")
    geometry = []
    for node in root.iter():
        if not node.tag.endswith("path"):
            continue
        data_value = node.attrib.get("d", "")
        if not re.fullmatch(r"M[-+0-9., eEL]+", data_value):
            raise RuntimeError(f"SVG is not M/L-only: {name}")
        values = [float(value) for value in NUMBER_RE.findall(data_value)]
        points = list(zip(values[::2], values[1::2]))
        if len(points) < 2 or any(a == b for a, b in zip(points, points[1:])):
            raise RuntimeError(f"Invalid path points: {name}")
        if sum(math.dist(a, b) for a, b in zip(points, points[1:])) < 3.0 - 1e-9:
            raise RuntimeError(f"Micro path: {name}")
        geometry.append(data_value)
    if not geometry:
        raise RuntimeError(f"Empty SVG: {name}")
    return geometry


def validate() -> dict[str, object]:
    manifest = json.loads((FORMAL / "manifest.json").read_text(encoding="utf-8"))
    conversion = manifest["conversion"]
    aggregate = manifest["quality"]["aggregate"]
    expected_counts = {
        "catalog_codepoints": 6702,
        "catalog_eligible_glyphs": 6606,
        "eligible_glyphs": 6608,
        "approved_geometry_glyphs": 191,
        "fallback_glyphs": 96,
        "source_font_missing_glyphs": 87,
        "conversion_ineligible_glyphs": 9,
    }
    for key, value in expected_counts.items():
        if conversion[key] != value:
            raise RuntimeError(f"Manifest conversion count mismatch {key}: {conversion[key]}")
    if aggregate["hard_failure_glyphs"] != 0 or aggregate["missing_source_components"] != 0:
        raise RuntimeError("Formal aggregate contains a hard failure")
    if aggregate["minimum_coverage_1_5px"] < 0.99 or not aggregate["all_within_outline_or_0_5"]:
        raise RuntimeError("Formal aggregate geometry gate failed")
    fallback = json.loads((FORMAL / "fallback.json").read_text(encoding="utf-8"))
    if len(fallback) != 96:
        raise RuntimeError("Fallback count drifted")
    reasons = {}
    for row in fallback:
        reasons[row["reason"]] = reasons.get(row["reason"], 0) + 1
    if reasons != {"source-font-missing": 87, "source-component-loss": 6, "empty-centerline": 3}:
        raise RuntimeError(f"Fallback reasons drifted: {reasons}")
    archive_path = FORMAL / "strokes.zip"
    if sha256(archive_path) != manifest["strokes_archive_sha256"]:
        raise RuntimeError("Formal archive hash mismatch")
    approved = approved_geometry()
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        if len(names) != 6608 or names != sorted(names):
            raise RuntimeError("Formal archive member count/order mismatch")
        for name in names:
            codepoint = int(Path(name).stem, 16)
            geometry = validate_svg(name, archive.read(name))
            if codepoint in approved and geometry != approved[codepoint]:
                raise RuntimeError(f"Approved geometry drifted: U+{codepoint:04X}")
    with (BUILD / "metrics.csv").open(encoding="utf-8-sig", newline="") as stream:
        metrics = list(csv.DictReader(stream))
    if len(metrics) != 6608 or sum(row["approved_geometry"] == "True" for row in metrics) != 191:
        raise RuntimeError("Build metrics count drifted")
    for row in metrics:
        if int(row["missing_source_components"]) != 0 or float(row["coverage_1_5px"]) < 0.99:
            raise RuntimeError(f"Build metric hard failure: {row['codepoint']}")
        if float(row["within_outline_or_0_5"]) != 1.0:
            raise RuntimeError(f"Build outline support failure: {row['codepoint']}")
    with (BUILD / "hard_failures.csv").open(encoding="utf-8-sig", newline="") as stream:
        if list(csv.DictReader(stream)):
            raise RuntimeError("Build hard-failure report is not empty")
    recorded_hashes = json.loads((BUILD / "artifact_hashes.json").read_text(encoding="utf-8"))
    for relative, digest in recorded_hashes.items():
        if sha256(BUILD / relative) != digest:
            raise RuntimeError(f"Build artifact hash mismatch: {relative}")
    for review in (BUILD / "review" / "approved-191.png", BUILD / "review" / "priority-flags.png"):
        if not review.is_file():
            raise RuntimeError(f"Review artifact missing: {review}")
    return {
        "generated_glyphs": 6608,
        "catalog_glyphs": 6606,
        "style_only_glyphs": 2,
        "fallback_glyphs": 96,
        "approved_geometry_glyphs": 191,
        "flagged_glyphs": aggregate["flagged_glyphs"],
        "minimum_coverage_1_5px": aggregate["minimum_coverage_1_5px"],
        "archive_sha256": manifest["strokes_archive_sha256"],
    }


def reproduce(workers: int) -> None:
    build = ROOT / "build" / "yomogi-direct-reproduction"
    formal = ROOT / "build" / "yomogi-direct-reproduction-formal"
    for path in (build, formal):
        resolved = path.resolve()
        if ROOT.resolve() not in resolved.parents or (ROOT / "build").resolve() not in (resolved, *resolved.parents):
            raise RuntimeError(f"Unsafe reproduction path: {path}")
        if path.exists():
            shutil.rmtree(path)
    command = [
        sys.executable,
        str(GENERATOR),
        "--build-dir", str(build),
        "--formal-dir", str(formal),
        "--workers", str(workers),
        "--promote",
    ]
    completed = subprocess.run(command, cwd=ROOT)
    if completed.returncode != 0:
        raise RuntimeError("Yomogi reproduction generator failed")
    if tree_hashes(formal) != tree_hashes(FORMAL):
        raise RuntimeError("Formal pack is not reproducible")
    for relative in (
        "strokes.zip", "metrics.csv", "metrics.json", "fallback.csv", "fallback.json",
        "manifest.json", "review/approved-191.png", "review/priority-flags.png",
    ):
        if sha256(build / relative) != sha256(BUILD / relative):
            raise RuntimeError(f"Build artifact is not reproducible: {relative}")
    shutil.rmtree(build)
    shutil.rmtree(formal)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reproduce", action="store_true")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args(argv)
    result = validate()
    if args.reproduce:
        reproduce(args.workers)
        result["reproducible"] = True
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
