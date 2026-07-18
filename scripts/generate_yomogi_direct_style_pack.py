# -*- coding: utf-8 -*-
"""Generate and optionally promote the complete Yomogi direct-centreline pack."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import multiprocessing
import re
import shutil
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

from yomogi_direct_centerline import FONT_SIZE, convert_glyph, path_data_from_svg


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FONT = ROOT / "build" / "glyph-proof-first-batch" / "sources" / "yomogi" / "Yomogi-Regular.ttf"
DEFAULT_OFL = DEFAULT_FONT.parent / "OFL.txt"
DEFAULT_KVG = ROOT / "data" / "kanjivg" / "20250816" / "main" / "kanji"
DEFAULT_BUILD = ROOT / "build" / "glyph-proof-yomogi-direct-full"
DEFAULT_FORMAL = ROOT / "data" / "stroke_styles" / "yomogi"
SOURCE_VERSION = "Version 3.100"
SOURCE_COMMIT = "2dcc1a21e9ee7cb66606d0be9099752504efe559"
SOURCE_SHA256 = "3424e34bb951e89bf5dd2554a65d8964335ea3c0560f8d1ea9aa3591ef73cba9"
SOURCE_COPYRIGHT = "Copyright 2020 The Yomogi Project Authors (https://github.com/satsuyako/YomogiFont), all rights reserved."
CATALOG_NAME = "kanjivg-20250816"
GENERATED_DATE = "2026-07-18"
EXPECTED_CATALOG = 6702
EXPECTED_CATALOG_ELIGIBLE = 6606
STYLE_ONLY_EXTRAS = (0x309F, 0x30FF)
EXPECTED_ELIGIBLE = EXPECTED_CATALOG_ELIGIBLE + len(STYLE_ONLY_EXTRAS)
EXPECTED_FALLBACK = 96
EXPECTED_APPROVED = 191
CONVERSION_FALLBACKS = {
    0x0021: "source-component-loss",
    0x002E: "empty-centerline",
    0x003A: "empty-centerline",
    0x003B: "source-component-loss",
    0x003F: "source-component-loss",
    0x0069: "source-component-loss",
    0x006A: "source-component-loss",
    0x30FB: "empty-centerline",
    0xFF01: "source-component-loss",
}
METRIC_FIELDS = (
    "character", "codepoint", "filename", "paths", "points", "source_components",
    "missing_source_components", "coverage_1_5px", "uncovered_p90", "within_outline_or_0_5",
    "within_outline_or_1_0", "maximum_outline_distance", "minimum_path_length",
    "maximum_path_length", "approved_geometry", "flags",
)
_WORKER_FONT: ImageFont.FreeTypeFont | None = None
NUMBER_RE = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def reset_build(path: Path) -> None:
    if ROOT / "build" not in path.resolve().parents:
        raise RuntimeError(f"Refusing to reset non-build path: {path}")
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def initialize_worker(font_path: str) -> None:
    global _WORKER_FONT
    _WORKER_FONT = ImageFont.truetype(font_path, FONT_SIZE)


def convert_worker(codepoint: int):
    if _WORKER_FONT is None:
        raise RuntimeError("Worker font is not initialized")
    svg, record = convert_glyph(_WORKER_FONT, codepoint)
    return codepoint, svg, record


def unicode_cmap(font_path: Path) -> set[int]:
    font = TTFont(font_path, lazy=True)
    try:
        return set().union(*(table.cmap.keys() for table in font["cmap"].tables if table.isUnicode()))
    finally:
        font.close()


def catalog_codepoints(kvg_root: Path) -> list[int]:
    result = []
    for path in kvg_root.glob("*.svg"):
        try:
            result.append(int(path.stem, 16))
        except ValueError:
            continue
    return sorted(set(result))


def approved_geometry() -> dict[int, list[str]]:
    roots = (
        ROOT / "build" / "glyph-proof-yomogi-direct-kana-review" / "candidates",
        ROOT / "build" / "glyph-proof-yomogi-direct-kanji-pilot" / "candidates",
        ROOT / "build" / "glyph-proof-yomogi-direct-kanji-batch2" / "candidates",
    )
    approvals = (
        ROOT / "build" / "glyph-proof-yomogi-direct-kana-review" / "APPROVAL_HISTORY.md",
        ROOT / "build" / "glyph-proof-yomogi-direct-kanji-pilot" / "APPROVAL_HISTORY.md",
        ROOT / "build" / "glyph-proof-yomogi-direct-kanji-batch2" / "APPROVAL_HISTORY.md",
    )
    markers = (
        "all 19 complete six-column review pages",
        "the requested kanji review page was manually approved",
        "second requested kanji review page was manually approved",
    )
    for path, marker in zip(approvals, markers):
        if marker not in path.read_text(encoding="utf-8"):
            raise RuntimeError(f"Approval prerequisite is missing: {path}")
    result: dict[int, list[str]] = {}
    for folder in roots:
        for path in sorted(folder.glob("*.svg")):
            codepoint = int(path.stem, 16)
            geometry = path_data_from_svg(path)
            if codepoint in result and result[codepoint] != geometry:
                raise RuntimeError(f"Conflicting approved geometry: U+{codepoint:04X}")
            result[codepoint] = geometry
    if len(result) != EXPECTED_APPROVED:
        raise RuntimeError(f"Approved geometry count must be {EXPECTED_APPROVED}, got {len(result)}")
    return result


def geometry_from_bytes(svg: bytes) -> list[str]:
    return [
        node.attrib["d"]
        for node in ET.fromstring(svg).iter()
        if node.tag.endswith("path")
    ]


def flags_for(record: dict[str, object]) -> list[str]:
    flags = []
    if float(record["coverage_1_5px"]) < 0.995:
        flags.append("coverage-review")
    if int(record["paths"]) > 24:
        flags.append("path-density-review")
    return flags


def hard_failures(record: dict[str, object]) -> list[str]:
    failures = []
    if int(record["missing_source_components"]) != 0:
        failures.append("missing-source-component")
    if float(record["coverage_1_5px"]) < 0.99:
        failures.append("coverage-below-99-percent")
    if float(record["within_outline_or_0_5"]) != 1.0:
        failures.append("outside-outline-neighbourhood")
    if float(record["within_outline_or_1_0"]) != 1.0:
        failures.append("outside-one-unit-neighbourhood")
    if float(record["minimum_path_length"]) < 3.0 - 1e-9:
        failures.append("micro-path")
    return failures


def write_csv(path: Path, rows: list[dict[str, object]], fields) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row[field] for field in fields} for row in rows)


def deterministic_zip(path: Path, members: list[tuple[str, bytes]]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(members):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            info.create_system = 3
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def source_record(manifest: dict[str, object]) -> str:
    conversion = manifest["conversion"]
    assert isinstance(conversion, dict)
    return "\n".join((
        "# Yomogi direct-centreline formal style pack",
        "",
        "- Source font: Yomogi Regular",
        f"- Source version: {SOURCE_VERSION}",
        "- Source repository: https://github.com/satsuyako/YomogiFont",
        f"- Pinned source commit: `{SOURCE_COMMIT}`",
        f"- Source TTF SHA-256: `{SOURCE_SHA256}`",
        f"- Original copyright: {SOURCE_COPYRIGHT}",
        "- Source and derived centreline license: SIL Open Font License 1.1 (`OFL.txt`)",
        "",
        "## Conversion record",
        "",
        f"- Base target catalog: {CATALOG_NAME}, {EXPECTED_CATALOG} codepoints",
        f"- Font-derived direct-centreline SVGs: {EXPECTED_ELIGIBLE} ({EXPECTED_CATALOG_ELIGIBLE} catalog glyphs + 2 approved Yomogi-only kana)",
        f"- Human-approved geometry locked byte-for-byte at path-data level: {EXPECTED_APPROVED}",
        "- KanjiVG fallbacks: 96 total (87 source-font-missing; 9 unable to pass direct-centreline component/empty-path gates)",
        "- Geometry: Yomogi source outline skeleton only",
        "- Runtime mode: direct; no KanjiVG projection, order, direction, or path-count input",
        "- View box: 0 0 109 109; commands: M/L",
        f"- Generator: `{conversion['converter']}`",
        f"- Generated at: {GENERATED_DATE}",
        f"- Formal archive SHA-256: `{manifest['strokes_archive_sha256']}`",
        "",
        "## Quality status",
        "",
        "- All generated glyphs pass component, 99% skeleton-coverage, and 0.5-unit outline-support gates.",
        "- Path order is optimized for cursor travel and does not represent traditional stroke order.",
        "- Writing speed and line width remain user-adjustable.",
        "- Release status: feature branch only; not merged, pushed, versioned, or published.",
        "",
    ))


def formal_manifest(archive_hash: str, fallback: list[int], aggregate: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": 3,
        "id": "yomogi",
        "display_order": 10,
        "labels": {"zh-Hant": "Yomogi直繪中心線", "zh-Hans": "Yomogi直绘中心线", "ja": "Yomogi直接中心線", "en": "Yomogi Direct Centreline"},
        "runtime_mode": "direct",
        "view_box": "0 0 109 109",
        "path_semantics": "visual-centerline",
        "order_semantics": "none",
        "strokes_archive": "strokes.zip",
        "strokes_archive_sha256": archive_hash,
        "fallback_style": "kanjivg",
        "fallback_codepoints_file": "fallback.json",
        "supports_horizontal": True,
        "supports_vertical": True,
        "source": {
            "font_name": "Yomogi Regular",
            "font_version": SOURCE_VERSION,
            "repository": "https://github.com/satsuyako/YomogiFont",
            "commit": SOURCE_COMMIT,
            "sha256": SOURCE_SHA256,
            "copyright": SOURCE_COPYRIGHT,
            "filename": "Yomogi-Regular.ttf",
        },
        "license": {"id": "OFL-1.1", "file": "OFL.txt", "derivative_data_license": "OFL-1.1"},
        "conversion": {
            "converter": "scripts/generate_yomogi_direct_style_pack.py",
            "generated_at": GENERATED_DATE,
            "catalog": CATALOG_NAME,
            "catalog_codepoints": EXPECTED_CATALOG,
            "style_only_codepoints": [f"U+{codepoint:04X}" for codepoint in STYLE_ONLY_EXTRAS],
            "catalog_eligible_glyphs": EXPECTED_CATALOG_ELIGIBLE,
            "eligible_glyphs": EXPECTED_ELIGIBLE,
            "approved_geometry_glyphs": EXPECTED_APPROVED,
            "fallback_glyphs": len(fallback),
            "source_font_missing_glyphs": len(fallback) - len(CONVERSION_FALLBACKS),
            "conversion_ineligible_glyphs": len(CONVERSION_FALLBACKS),
            "source_geometry": "Yomogi source font outlines only",
            "runtime_mode": "direct",
            "view_box": "0 0 109 109",
            "path_commands": ["M", "L"],
        },
        "quality": {
            "status": "formal-automatic-gates-with-191-human-approved",
            "hard_gates": {"minimum_coverage_1_5px": 0.99, "missing_source_components": 0, "all_within_outline_or_0_5": True},
            "aggregate": aggregate,
            "usage_notice": "Visual centreline only; path order is not traditional stroke order. The 96 explicitly listed source-missing or conversion-ineligible glyphs fall back to KanjiVG.",
        },
    }


def promote(formal_dir: Path, build_dir: Path, manifest: dict[str, object]) -> None:
    staging = build_dir / "formal-staging"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir()
    shutil.copyfile(build_dir / "strokes.zip", staging / "strokes.zip")
    shutil.copyfile(build_dir / "fallback.json", staging / "fallback.json")
    shutil.copyfile(build_dir / "fallback.csv", staging / "fallback.csv")
    shutil.copyfile(DEFAULT_OFL, staging / "OFL.txt")
    (staging / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    (staging / "SOURCE.md").write_text(source_record(manifest), encoding="utf-8", newline="\n")
    if formal_dir.exists():
        shutil.rmtree(formal_dir)
    formal_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(staging, formal_dir)


def svg_paths(svg: bytes) -> list[list[tuple[float, float]]]:
    result = []
    for node in ET.fromstring(svg).iter():
        if not node.tag.endswith("path"):
            continue
        values = [float(value) for value in NUMBER_RE.findall(node.attrib.get("d", ""))]
        result.append(list(zip(values[::2], values[1::2])))
    return result


def render_review_sheet(path: Path, rows: list[dict[str, object]], svg_by_codepoint: dict[int, bytes], columns: int) -> None:
    cell_width, cell_height, header = 130, 140, 48
    sheet_rows = max(1, (len(rows) + columns - 1) // columns)
    image = Image.new("RGB", (columns * cell_width, header + sheet_rows * cell_height), "white")
    draw = ImageDraw.Draw(image)
    try:
        title_font = ImageFont.truetype(r"C:\Windows\Fonts\meiryob.ttc", 18)
        label_font = ImageFont.truetype(r"C:\Windows\Fonts\meiryo.ttc", 10)
    except OSError:
        title_font = label_font = ImageFont.load_default()
    draw.text((8, 8), f"Yomogi direct centreline review · {len(rows)} glyphs", font=title_font, fill="#172033")
    colors = ("#e52521", "#225de8", "#0c9b45", "#8b2be2", "#ef5a00", "#0095ad", "#b50045", "#5d9700", "#6b3b1e", "#00716c", "#d11e78", "#222222")
    for index, row in enumerate(rows):
        left = index % columns * cell_width
        top = header + index // columns * cell_height
        draw.rectangle((left, top, left + cell_width - 1, top + cell_height - 1), outline="#ccd5e3")
        codepoint = int(str(row["codepoint"])[2:], 16)
        suffix = " approved" if row.get("approved_geometry") else f" {row.get('flags', '')}"
        draw.text((left + 5, top + 4), f"U+{codepoint:04X}{suffix}", font=label_font, fill="#39465e")
        for path_index, points in enumerate(svg_paths(svg_by_codepoint[codepoint])):
            translated = [(left + 10 + x, top + 25 + y) for x, y in points]
            draw.line(translated, fill=colors[path_index % len(colors)], width=3, joint="curve")
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font", type=Path, default=DEFAULT_FONT)
    parser.add_argument("--kvg-root", type=Path, default=DEFAULT_KVG)
    parser.add_argument("--build-dir", type=Path, default=DEFAULT_BUILD)
    parser.add_argument("--formal-dir", type=Path, default=DEFAULT_FORMAL)
    parser.add_argument("--workers", type=int, default=min(4, multiprocessing.cpu_count()))
    parser.add_argument("--promote", action="store_true")
    args = parser.parse_args(argv)
    if sha256(args.font) != SOURCE_SHA256:
        raise RuntimeError("Pinned Yomogi source font hash mismatch")
    if not DEFAULT_OFL.is_file():
        raise RuntimeError("Yomogi OFL.txt is missing")
    catalog = catalog_codepoints(args.kvg_root)
    cmap = unicode_cmap(args.font)
    catalog_eligible = [codepoint for codepoint in catalog if codepoint in cmap and codepoint not in CONVERSION_FALLBACKS]
    eligible = sorted(catalog_eligible + list(STYLE_ONLY_EXTRAS))
    fallback = [codepoint for codepoint in catalog if codepoint not in eligible]
    if (len(catalog), len(catalog_eligible), len(eligible), len(fallback)) != (EXPECTED_CATALOG, EXPECTED_CATALOG_ELIGIBLE, EXPECTED_ELIGIBLE, EXPECTED_FALLBACK):
        raise RuntimeError(f"Catalog/source counts drifted: {len(catalog)}/{len(catalog_eligible)}/{len(eligible)}/{len(fallback)}")
    approved = approved_geometry()
    if not set(approved) <= set(eligible):
        raise RuntimeError("Approved geometry contains a source-missing codepoint")
    reset_build(args.build_dir)
    records: list[dict[str, object]] = []
    archive_members: list[tuple[str, bytes]] = []
    hard_failure_rows: list[dict[str, object]] = []
    context = multiprocessing.get_context("spawn")
    with context.Pool(max(1, args.workers), initializer=initialize_worker, initargs=(str(args.font),)) as pool:
        for count, (codepoint, svg, record) in enumerate(pool.imap(convert_worker, eligible, chunksize=8), 1):
            expected = approved.get(codepoint)
            if expected is not None and geometry_from_bytes(svg) != expected:
                raise RuntimeError(f"Approved path geometry drifted: U+{codepoint:04X}")
            record["approved_geometry"] = expected is not None
            record["flags"] = ";".join(flags_for(record))
            failures = hard_failures(record)
            if failures:
                hard_failure_rows.append({"character": chr(codepoint), "codepoint": f"U+{codepoint:04X}", "failures": ";".join(failures)})
            records.append(record)
            archive_members.append((f"strokes/{codepoint:05x}.svg", svg))
            if count % 100 == 0 or count == len(eligible):
                print(f"generated {count}/{len(eligible)}", flush=True)
    deterministic_zip(args.build_dir / "strokes.zip", archive_members)
    svg_by_codepoint = {int(Path(name).stem, 16): svg for name, svg in archive_members}
    fallback_rows = [
        {
            "character": chr(codepoint),
            "codepoint": f"U+{codepoint:04X}",
            "reason": CONVERSION_FALLBACKS.get(codepoint, "source-font-missing"),
        }
        for codepoint in fallback
    ]
    write_csv(args.build_dir / "metrics.csv", records, METRIC_FIELDS)
    (args.build_dir / "metrics.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    write_csv(args.build_dir / "fallback.csv", fallback_rows, ("character", "codepoint", "reason"))
    (args.build_dir / "fallback.json").write_text(json.dumps(fallback_rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    write_csv(args.build_dir / "hard_failures.csv", hard_failure_rows, ("character", "codepoint", "failures"))
    render_review_sheet(
        args.build_dir / "review" / "approved-191.png",
        [record for record in records if record["approved_geometry"]],
        svg_by_codepoint,
        10,
    )
    flagged_rows = [record for record in records if record["flags"]]
    render_review_sheet(args.build_dir / "review" / "priority-flags.png", flagged_rows, svg_by_codepoint, 5)
    aggregate = {
        "catalog_codepoints": len(catalog),
        "catalog_generated_glyphs": len(catalog_eligible),
        "style_only_glyphs": len(STYLE_ONLY_EXTRAS),
        "generated_glyphs": len(records),
        "fallback_glyphs": len(fallback),
        "approved_geometry_glyphs": sum(bool(record["approved_geometry"]) for record in records),
        "flagged_glyphs": sum(bool(record["flags"]) for record in records),
        "hard_failure_glyphs": len(hard_failure_rows),
        "missing_source_components": sum(int(record["missing_source_components"]) for record in records),
        "minimum_coverage_1_5px": min(float(record["coverage_1_5px"]) for record in records),
        "all_within_outline_or_0_5": all(float(record["within_outline_or_0_5"]) == 1.0 for record in records),
        "total_paths": sum(int(record["paths"]) for record in records),
        "total_points": sum(int(record["points"]) for record in records),
    }
    archive_hash = sha256(args.build_dir / "strokes.zip")
    manifest = formal_manifest(archive_hash, fallback, aggregate)
    (args.build_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    (args.build_dir / "SOURCE.md").write_text(source_record(manifest), encoding="utf-8", newline="\n")
    shutil.copyfile(DEFAULT_OFL, args.build_dir / "OFL.txt")
    (args.build_dir / "artifact_hashes.json").write_text(json.dumps({
        path.relative_to(args.build_dir).as_posix(): sha256(path)
        for path in sorted(args.build_dir.rglob("*")) if path.is_file() and path.name != "artifact_hashes.json" and "formal-staging" not in path.parts
    }, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"aggregate": aggregate, "archive_sha256": archive_hash}, ensure_ascii=False, indent=2))
    if hard_failure_rows:
        print(f"Formal promotion blocked by {len(hard_failure_rows)} hard failures", file=sys.stderr)
        return 2
    if args.promote:
        promote(args.formal_dir, args.build_dir, manifest)
        print(f"Promoted formal pack to {args.formal_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
