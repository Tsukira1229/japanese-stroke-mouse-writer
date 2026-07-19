# -*- coding: utf-8 -*-
"""Promote the reviewed Zen Kurenaido and Hachi Maru Pop build archives."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATED_DATE = "2026-07-18"


@dataclass(frozen=True)
class PackConfig:
    id: str
    build_name: str
    display_order: int
    font_name: str
    font_version: str
    repository: str
    commit: str
    source_sha256: str
    copyright: str
    source_filename: str
    archive_sha256: str
    generated: int
    fallback: int
    source_missing: int
    conversion_ineligible: int
    labels: dict[str, str]
    order_archive_sha256: str
    order_maps: int
    missing_kvg_strokes: int
    source_box: dict[str, object] | None = None


PACKS = (
    PackConfig(
        id="zen-kurenaido",
        build_name="zen-kurenaido",
        display_order=20,
        font_name="Zen Kurenaido Regular",
        font_version="Version 1.001",
        repository="https://github.com/googlefonts/zen-kurenaido",
        commit="2edac135aa83e34640ec569d1d27520c3400e9b7",
        source_sha256="58b8d930d9fc10c8a5810c085bae378dacb98d0779073ee6d53d919f19ee6a4f",
        copyright="Copyright 2021 The Zen Kurenaido Project Authors (https://github.com/googlefonts/zen-kurenaido)",
        source_filename="ZenKurenaido-Regular.ttf",
        archive_sha256="be8bc959480909f88a203f817ba546314ec49b4b9282d6252885923413c0b3c5",
        generated=6591,
        fallback=111,
        source_missing=88,
        conversion_ineligible=23,
        labels={"zh-Hant": "Zen Kurenaido", "zh-Hans": "Zen Kurenaido", "ja": "Zen Kurenaido", "en": "Zen Kurenaido"},
        order_archive_sha256="209caf2a443060b4fd5c4d4107f4004c1810f138cb2087e349c117101d895fe1",
        order_maps=6591,
        missing_kvg_strokes=0,
    ),
    PackConfig(
        id="hachi-maru-pop",
        build_name="hachi-maru-pop",
        display_order=30,
        font_name="Hachi Maru Pop Regular",
        font_version="Version 1.300",
        repository="https://github.com/noriokanisawa/HachiMaruPop",
        commit="252adbcc5e3722bd514c424c4a4395127f18d73c",
        source_sha256="78408910c8f1a2f174a279cbc1484b48b71780039eba3fe1be2bfcc5d4df3f98",
        copyright="Copyright 2020 The Hachi Maru Pop Project Authors (https://github.com/noriokanisawa/HachiMaruPop)",
        source_filename="HachiMaruPop-Regular.ttf",
        archive_sha256="f532cad5a310239553db7252e0abaeaed4fcbd7df116e477948e6709027e223e",
        generated=6608,
        fallback=94,
        source_missing=88,
        conversion_ineligible=6,
        labels={"zh-Hant": "Hachi Maru Pop", "zh-Hans": "Hachi Maru Pop", "ja": "Hachi Maru Pop", "en": "Hachi Maru Pop"},
        order_archive_sha256="bafada4c7571940c771a55a0af30ef708df143b745c9dc2b99f1e91edf927b94",
        order_maps=6608,
        missing_kvg_strokes=2,
        source_box={
            "font_size_px": 390,
            "anchor_y_px": 182,
            "canvas_px": 436,
            "boundary_contact_allowed": False,
        },
    ),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def geometry(svg: bytes) -> list[str]:
    return [node.attrib["d"] for node in ET.fromstring(svg).iter() if node.tag.endswith("path")]


def merged_review_lock(config: PackConfig, archive_path: Path) -> dict[str, object]:
    base = ROOT / "build"
    sources = (
        (base / f"glyph-proof-{config.build_name}-direct-kana-review" / "approved_geometry.json", 179, "complete-kana"),
        (base / f"glyph-proof-{config.build_name}-direct-kanji-anchors" / "approved_geometry.json", 10, "requested-kanji-anchors"),
        (base / f"glyph-proof-{config.build_name}-direct-random-200" / "approved_geometry.json", 200, "fixed-seed-random-han"),
    )
    glyphs: dict[int, dict[str, object]] = {}
    groups = []
    for path, expected, group in sources:
        payload = load_json(path)
        if int(payload["approved_glyphs"]) != expected:
            raise RuntimeError(f"Approval count drift: {path}")
        if group == "fixed-seed-random-han" and payload.get("source_archive_sha256") != config.archive_sha256:
            raise RuntimeError(f"Random review archive drift: {config.id}")
        groups.append({"id": group, "approved_glyphs": expected})
        for row in payload["glyphs"]:
            codepoint = int(str(row["codepoint"])[2:], 16)
            if codepoint in glyphs:
                raise RuntimeError(f"Overlapping approval U+{codepoint:04X}: {config.id}")
            glyphs[codepoint] = {
                "character": row["character"],
                "codepoint": f"U+{codepoint:04X}",
                "path_d": row["path_d"],
                "review_group": group,
            }
    if len(glyphs) != 389:
        raise RuntimeError(f"Expected 389 approvals for {config.id}, got {len(glyphs)}")
    with zipfile.ZipFile(archive_path) as archive:
        for codepoint, row in glyphs.items():
            actual = geometry(archive.read(f"strokes/{codepoint:05x}.svg"))
            if actual != row["path_d"]:
                raise RuntimeError(f"Approved geometry drift U+{codepoint:04X}: {config.id}")
    return {
        "schema_version": 1,
        "status": "human-approved-geometry-lock",
        "approved_glyphs": len(glyphs),
        "review_date": GENERATED_DATE,
        "source_archive_sha256": config.archive_sha256,
        "groups": groups,
        "glyphs": [glyphs[codepoint] for codepoint in sorted(glyphs)],
    }


def source_record(config: PackConfig, aggregate: dict[str, object]) -> str:
    source_box = ""
    if config.source_box:
        source_box = (
            f"- Source box: {config.source_box['canvas_px']} px canvas, "
            f"font size {config.source_box['font_size_px']} px, anchor Y {config.source_box['anchor_y_px']} px; "
            "boundary contact rejected\n"
        )
    return (
        f"# {config.font_name} direct-centreline formal style pack\n\n"
        f"- Source font: {config.font_name}\n"
        f"- Source version: {config.font_version}\n"
        f"- Source repository: {config.repository}\n"
        f"- Pinned source commit: `{config.commit}`\n"
        f"- Source TTF SHA-256: `{config.source_sha256}`\n"
        f"- Original copyright: {config.copyright}\n"
        "- Source and derived centreline license: SIL Open Font License 1.1 (`OFL.txt`)\n"
        f"{source_box}\n"
        "## Conversion record\n\n"
        "- Base target catalog: kanjivg-20250816, 6,702 codepoints\n"
        f"- Font-derived direct-centreline SVGs: {config.generated}\n"
        f"- Explicit KanjiVG fallbacks: {config.fallback} ({config.source_missing} source-font-missing; "
        f"{config.conversion_ineligible} conversion-ineligible)\n"
        "- Geometry: source font outline skeleton only\n"
        "- Runtime mode: direct; no KanjiVG projection, order, direction, or path-count input\n"
        "- View box: 0 0 109 109; commands: M/L\n"
        "- Conversion cleanup: 4x skeletonization, spur pruning, straightest continuation, "
        "outline-constrained RDP 0.75, minimum path 3 units\n"
        f"- Generated at: {GENERATED_DATE}\n"
        f"- Formal archive SHA-256: `{config.archive_sha256}`\n\n"
        "## Quality status\n\n"
        "- 179 kana, 10 requested kanji anchors, and 200 fixed-seed random kanji were manually approved.\n"
        "- Exact path data for all 389 approvals is stored in `HUMAN_REVIEW.json`.\n"
        f"- Minimum 1.5-unit skeleton coverage: {float(aggregate['minimum_coverage_1_5px']):.6f}.\n"
        "- All generated dense samples remain inside the source shape or its 0.5-unit neighbourhood.\n"
        "- Path order is optimized for cursor travel and does not represent traditional stroke order.\n"
        "- Release status: feature branch handoff only; not merged, pushed, or published.\n"
    )


def manifest(config: PackConfig, aggregate: dict[str, object], fallback: list[dict[str, object]]) -> dict[str, object]:
    formal_aggregate = dict(aggregate)
    formal_aggregate["approved_geometry_glyphs"] = 389
    payload: dict[str, object] = {
        "schema_version": 3,
        "id": config.id,
        "display_order": config.display_order,
        "labels": config.labels,
        "runtime_mode": "direct",
        "view_box": "0 0 109 109",
        "path_semantics": "visual-centerline",
        "order_semantics": "best-effort-kanjivg-guided",
        "strokes_archive": "strokes.zip",
        "strokes_archive_sha256": config.archive_sha256,
        "fallback_style": "kanjivg",
        "fallback_codepoints_file": "fallback.json",
        "supports_horizontal": True,
        "supports_vertical": True,
        "source": {
            "font_name": config.font_name,
            "font_version": config.font_version,
            "repository": config.repository,
            "commit": config.commit,
            "sha256": config.source_sha256,
            "copyright": config.copyright,
            "filename": config.source_filename,
        },
        "license": {"id": "OFL-1.1", "file": "OFL.txt", "derivative_data_license": "OFL-1.1"},
        "conversion": {
            "converter": "reviewed build generator recorded in SOURCE.md",
            "promoter": "scripts/promote_reviewed_direct_style_packs.py",
            "generated_at": GENERATED_DATE,
            "catalog": "kanjivg-20250816",
            "catalog_codepoints": 6702,
            "style_only_codepoints": [],
            "catalog_eligible_glyphs": config.generated,
            "eligible_glyphs": config.generated,
            "approved_geometry_glyphs": 389,
            "fallback_glyphs": config.fallback,
            "source_font_missing_glyphs": config.source_missing,
            "conversion_ineligible_glyphs": config.conversion_ineligible,
            "source_geometry": f"{config.font_name} source font outlines only",
            "runtime_mode": "direct",
            "view_box": "0 0 109 109",
            "path_commands": ["M", "L"],
        },
        "quality": {
            "status": "formal-automatic-gates-with-389-human-approved",
            "hard_gates": {"minimum_coverage_1_5px": 0.99, "missing_source_components": 0, "all_within_outline_or_0_5": True},
            "aggregate": formal_aggregate,
            "human_review_file": "HUMAN_REVIEW.json",
            "usage_notice": (
                "Visual centreline with a locked best-effort drawing order; not authoritative Japanese stroke order. "
                f"The {len(fallback)} explicitly listed source-missing or conversion-ineligible glyphs fall back to KanjiVG."
            ),
        },
        "drawing_order": {
            "archive": "orders.zip",
            "sha256": config.order_archive_sha256,
            "eligible_maps": config.order_maps,
            "semantics": "best-effort-kanjivg-guided",
            "authoritative_japanese_stroke_order": False,
            "missing_kvg_strokes": config.missing_kvg_strokes,
            "geometry_contract": "frozen M/L points; each source edge used exactly once; reorder, reverse, and split at existing points only",
            "fallback": "original direct SVG path order",
        },
    }
    if config.source_box:
        payload["source_box"] = config.source_box
    return payload


def promote(config: PackConfig, destination_root: Path) -> None:
    build = ROOT / "build" / f"glyph-proof-{config.build_name}-direct-full"
    archive = build / "strokes.zip"
    if sha256(archive) != config.archive_sha256:
        raise RuntimeError(f"Reviewed archive hash mismatch: {config.id}")
    build_manifest = load_json(build / "manifest.json")
    aggregate = build_manifest["aggregate"]
    if int(aggregate["generated_glyphs"]) != config.generated or int(aggregate["fallback_glyphs"]) != config.fallback:
        raise RuntimeError(f"Reviewed build count drift: {config.id}")
    if int(aggregate["conversion_hard_failure_glyphs"]) or int(aggregate["missing_source_components"]):
        raise RuntimeError(f"Reviewed build contains hard failures: {config.id}")
    fallback = load_json(build / "fallback.json")
    if len(fallback) != config.fallback:
        raise RuntimeError(f"Fallback count drift: {config.id}")
    reasons: dict[str, int] = {}
    for row in fallback:
        reasons[row["reason"]] = reasons.get(row["reason"], 0) + 1
    if reasons.get("source-font-missing", 0) != config.source_missing:
        raise RuntimeError(f"Source-missing count drift: {config.id}")
    if sum(count for reason, count in reasons.items() if reason != "source-font-missing") != config.conversion_ineligible:
        raise RuntimeError(f"Conversion fallback count drift: {config.id}")
    destination = destination_root / config.id
    order_source = ROOT / "data" / "stroke_styles" / config.id / "orders.zip"
    if not order_source.is_file() or sha256(order_source) != config.order_archive_sha256:
        raise RuntimeError(f"Formal drawing-order sidecar is missing or changed: {config.id}")
    order_data = order_source.read_bytes()
    review = merged_review_lock(config, archive)
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    shutil.copyfile(archive, destination / "strokes.zip")
    shutil.copyfile(build / "fallback.json", destination / "fallback.json")
    shutil.copyfile(build / "fallback.csv", destination / "fallback.csv")
    shutil.copyfile(build / "OFL.txt", destination / "OFL.txt")
    (destination / "orders.zip").write_bytes(order_data)
    (destination / "HUMAN_REVIEW.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    payload = manifest(config, aggregate, fallback)
    (destination / "manifest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    (destination / "SOURCE.md").write_text(source_record(config, aggregate), encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination-root", type=Path, default=ROOT / "data" / "stroke_styles")
    args = parser.parse_args(argv)
    for config in PACKS:
        promote(config, args.destination_root)
        print(f"promoted {config.id}: {config.generated} direct / {config.fallback} fallback / 389 approved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
