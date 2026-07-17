# -*- coding: utf-8 -*-
"""Create fixed-cell visual review sheets for generated stroke-style packs."""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mouse_writer_pro import (  # noqa: E402
    DEFAULT_KANJIVG_DIR,
    load_kanjivg_strokes,
    project_strokes_to_style,
    sample_svg_path,
)
DEFAULT_SAMPLE = "あいうえおアイウエオ永愛語日空明朝夢心「」、。Ａｱ"
CELL = 132
HEADER = 38
RASTER_SIZE = 436
RASTER_SCALE = 4
SOURCE_ROOT = ROOT / "build" / "glyph-proof-first-batch" / "sources"
PANEL_TITLES = ("KanjiVG", "source font", "OFL skeleton", "runtime fit")


def font_baseline(font: TTFont) -> int:
    units_per_em = font["head"].unitsPerEm
    ascender = font["OS/2"].sTypoAscender
    return round(ascender / units_per_em * RASTER_SIZE)


def render_glyph_mask(char: str, pil_font: ImageFont.FreeTypeFont, baseline: int) -> np.ndarray:
    image = Image.new("L", (RASTER_SIZE, RASTER_SIZE), 0)
    ImageDraw.Draw(image).text((0, baseline), char, font=pil_font, fill=255, anchor="ls")
    high_resolution = np.asarray(image) > 96
    coverage = high_resolution.reshape(109, RASTER_SCALE, 109, RASTER_SCALE).mean((1, 3))
    return coverage > 0.22


def load_paths(svg_bytes: bytes) -> list[list[tuple[float, float]]]:
    root = ET.fromstring(svg_bytes)
    result: list[list[tuple[float, float]]] = []
    for element in root.iter():
        if not element.tag.endswith("path") or not element.attrib.get("d"):
            continue
        points = sample_svg_path(element.attrib["d"], 1.2)
        if len(points) >= 2:
            result.append(points)
    return result


def draw_paths(
    draw: ImageDraw.ImageDraw,
    paths: list[list[tuple[float, float]]],
    left: int,
    top: int,
    colour: str,
    width: int = 2,
) -> None:
    scale = (CELL - 20) / 109
    for path in paths:
        points = [(left + 10 + x * scale, top + 10 + y * scale) for x, y in path]
        draw.line(points, fill=colour, width=width, joint="curve")
        draw.ellipse((points[0][0] - 2, points[0][1] - 2, points[0][0] + 2, points[0][1] + 2), fill=colour)


def review_pack(pack_dir: Path, cache_dir: Path, output_dir: Path, sample: str) -> Path:
    manifest = json.loads((pack_dir / "manifest.json").read_text(encoding="utf-8"))
    style_id = manifest["id"]
    source = manifest["source"]
    font_path = SOURCE_ROOT / style_id / source["filename"]
    if not font_path.is_file():
        font_path = cache_dir / style_id / source["filename"]
    if not font_path.is_file():
        raise RuntimeError(f"Pinned source font is unavailable for review: {font_path}")
    font = TTFont(font_path)
    pil_font = ImageFont.truetype(str(font_path), RASTER_SIZE)
    baseline = font_baseline(font)
    with zipfile.ZipFile(pack_dir / manifest["strokes_archive"]) as archive:
        available = set(archive.namelist())
        rows = [char for char in sample if f"strokes/{ord(char):05x}.svg" in available]
    canvas = Image.new("RGB", (CELL * len(PANEL_TITLES), HEADER + CELL * len(rows)), "white")
    draw = ImageDraw.Draw(canvas)
    for column, title in enumerate(PANEL_TITLES):
        draw.text((column * CELL + 8, 11), title, fill="#111827")
    for row, char in enumerate(rows):
        top = HEADER + row * CELL
        for column in range(len(PANEL_TITLES)):
            left = column * CELL
            draw.rectangle((left, top, left + CELL - 1, top + CELL - 1), outline="#d1d5db")
        base = load_kanjivg_strokes(char, DEFAULT_KANJIVG_DIR, 1.2) or []
        with zipfile.ZipFile(pack_dir / manifest["strokes_archive"]) as archive:
            skeleton = load_paths(archive.read(f"strokes/{ord(char):05x}.svg"))
        fitted = project_strokes_to_style(base, skeleton)
        draw_paths(draw, base, 0, top, "#2563eb")
        mask = Image.fromarray((render_glyph_mask(char, pil_font, baseline) * 210).astype("uint8"), "L")
        mask = mask.resize((CELL - 20, CELL - 20), Image.Resampling.NEAREST)
        ink = Image.new("RGB", mask.size, "#111827")
        canvas.paste(ink, (CELL + 10, top + 10), mask)
        draw_paths(draw, skeleton, CELL * 2, top, "#7c3aed")
        canvas.paste(ink, (CELL * 3 + 10, top + 10), mask.point(lambda value: value // 4))
        draw_paths(draw, fitted, CELL * 3, top, "#dc2626", 2)
        draw.text((4, top + 4), f"U+{ord(char):04X}", fill="#111827")

    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"{style_id}.png"
    canvas.save(output)
    checklist = output_dir / f"{style_id}.md"
    checklist.write_text(
        "\n".join(
            (
                f"# Review: {source['font_name']}",
                "",
                f"- Source version: {manifest['source']['font_version']}",
                f"- Source commit: `{manifest['source']['commit']}`",
                f"- Source SHA-256: `{manifest['source']['sha256']}`",
                f"- Original copyright: {manifest['source']['copyright']}",
                f"- License: {manifest['license']['id']} (`OFL.txt`)",
                f"- Generated skeletons: {manifest['conversion']['generated_glyphs']}",
                f"- Fallback glyphs: {manifest['conversion']['fallback_glyphs']}",
                f"- Fixed-cell samples reviewed: {''.join(rows)}",
                "",
                "Columns show independent base strokes, source-font ink, OFL-only skeleton data, and the runtime projection overlay.",
                "",
            )
        ),
        encoding="utf-8",
    )
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-dir", type=Path, default=ROOT / "data/stroke_styles")
    parser.add_argument("--cache-dir", type=Path, default=ROOT / "build/font-sources")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "build/font-style-review")
    parser.add_argument("--sample", default=DEFAULT_SAMPLE)
    args = parser.parse_args()
    for manifest_path in sorted(args.candidate_dir.glob("*/manifest.json")):
        print(review_pack(manifest_path.parent, args.cache_dir, args.output_dir, args.sample))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
