from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mouse_writer_pro import (  # noqa: E402
    DEFAULT_KANJIVG_DIR,
    EnvironmentSettings,
    GeneralSettings,
    LayoutSettings,
    build_layout,
)


MANIFEST = ROOT / "data" / "symbol_manifest.json"
FONT_DIR = Path("C:/Windows/Fonts")
FONT_CANDIDATES = (
    ("Yu Gothic UI", "YuGothR.ttc"),
    ("Segoe UI Symbol", "seguisym.ttf"),
    ("Segoe UI", "segoeui.ttf"),
    ("Noto Sans JP", "NotoSansJP-VF.ttf"),
    ("Noto Sans TC", "NotoSansTC-VF.ttf"),
    ("Nirmala UI", "Nirmala.ttc"),
    ("Gadugi", "gadugi.ttf"),
    ("Leelawadee UI", "LeelawUI.ttf"),
    ("Malgun Gothic", "malgun.ttf"),
    ("MS Gothic", "msgothic.ttc"),
)
CARD_WIDTH = 510
CARD_HEIGHT = 230
PANEL_SIZE = 150
PANEL_TOP = 54
PANEL_LEFTS = (20, 180, 340)
LOGICAL_SIZE = 109.0
CELL_INSET = 10
CELL_PIXELS = PANEL_SIZE - CELL_INSET * 2


@dataclass(frozen=True)
class ReferenceFont:
    name: str
    path: Path
    font: ImageFont.FreeTypeFont


def _glyph_signature(font: ImageFont.FreeTypeFont, char: str) -> tuple[tuple[int, int, int, int] | None, bytes]:
    mask = font.getmask(char, mode="L")
    return font.getbbox(char), bytes(mask)


def _font_has_glyph(font: ImageFont.FreeTypeFont, char: str) -> bool:
    bbox, bitmap = _glyph_signature(font, char)
    if bbox is None or not bitmap or max(bitmap, default=0) == 0:
        return False
    for missing_char in ("\ufffd", "\u0000"):
        try:
            if (bbox, bitmap) == _glyph_signature(font, missing_char):
                return False
        except (OSError, ValueError):
            pass
    return True


def select_reference_font(char: str, size: int) -> ReferenceFont:
    attempted: list[str] = []
    for name, filename in FONT_CANDIDATES:
        path = FONT_DIR / filename
        if not path.is_file():
            continue
        attempted.append(name)
        try:
            font = ImageFont.truetype(str(path), size=size)
        except OSError:
            continue
        if _font_has_glyph(font, char):
            return ReferenceFont(name, path, font)
    raise RuntimeError(f"No reference font can display U+{ord(char):04X}; tried {', '.join(attempted)}")


def load_records(path: Path) -> tuple[dict[str, object], list[dict[str, object]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload, list(payload["symbols"])


def select_records(
    records: list[dict[str, object]],
    batch: str | None,
    symbols: str | None,
    status: str | None,
) -> list[dict[str, object]]:
    selected = records
    if batch:
        selected = [record for record in selected if record["batch"] == batch]
    if status:
        selected = [record for record in selected if record["status"] == status]
    if symbols:
        requested = list(symbols)
        if len(set(requested)) != len(requested):
            raise ValueError("--symbols contains duplicates")
        by_char = {str(record["symbol"]): record for record in records}
        missing = [char for char in requested if char not in by_char]
        if missing:
            raise ValueError("Symbols are not present in the manifest: " + " ".join(missing))
        requested_set = set(requested)
        selected = [record for record in selected if record["symbol"] in requested_set]
    if not selected:
        raise ValueError("No manifest records matched the requested review selection")
    return selected


def panel_point(panel_left: int, x: float, y: float) -> tuple[float, float]:
    scale = CELL_PIXELS / LOGICAL_SIZE
    return panel_left + CELL_INSET + x * scale, PANEL_TOP + CELL_INSET + y * scale


def draw_grid(draw: ImageDraw.ImageDraw, panel_left: int, span: float) -> None:
    x0, y0 = panel_point(panel_left, 0, 0)
    x1, y1 = panel_point(panel_left, LOGICAL_SIZE, LOGICAL_SIZE)
    draw.rectangle((x0, y0, x1, y1), outline="#8793a1", width=1)
    for fraction in (0.25, 0.5, 0.75):
        x, _ = panel_point(panel_left, LOGICAL_SIZE * fraction, 0)
        _, y = panel_point(panel_left, 0, LOGICAL_SIZE * fraction)
        color = "#cbd2da" if fraction != 0.5 else "#aeb8c3"
        draw.line((x, y0, x, y1), fill=color, width=1)
        draw.line((x0, y, x1, y), fill=color, width=1)
    _, baseline = panel_point(panel_left, 0, 82)
    draw.line((x0, baseline, x1, baseline), fill="#879fba", width=1)
    active_x, _ = panel_point(panel_left, LOGICAL_SIZE * span, 0)
    if span == 0.5:
        draw.line((active_x, y0, active_x, y1), fill="#526d89", width=2)


def draw_reference(
    image: Image.Image,
    panel_left: int,
    char: str,
    span: float,
    font: ImageFont.FreeTypeFont,
    fill: str,
) -> None:
    draw = ImageDraw.Draw(image)
    center_x, baseline = panel_point(panel_left, LOGICAL_SIZE * span / 2, 82)
    draw.text((center_x, baseline), char, font=font, fill=fill, anchor="ms")


def draw_paths(
    draw: ImageDraw.ImageDraw,
    panel_left: int,
    paths: list[list[tuple[float, float]]],
    show_order: bool,
) -> None:
    label_font = ImageFont.load_default()
    for index, path in enumerate(paths, start=1):
        points = [panel_point(panel_left, x, y) for x, y in path]
        if len(points) >= 2:
            draw.line(points, fill="#15191e", width=2, joint="curve")
        if show_order and points:
            x, y = points[0]
            draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill="#d33b35")
            draw.text((x + 4, y - 8), str(index), font=label_font, fill="#b32320")


def build_paths(char: str) -> list[list[tuple[float, float]]]:
    result = build_layout(
        char,
        DEFAULT_KANJIVG_DIR,
        LayoutSettings(start_x=0, start_y=0, general=GeneralSettings(font_size=109)),
        EnvironmentSettings(sample_spacing=1.5),
    )
    if not result.paths:
        raise RuntimeError(f"build_layout returned no paths for U+{ord(char):04X}")
    return result.paths


def make_card(record: dict[str, object], number: int, output: Path) -> tuple[Path, str]:
    char = str(record["symbol"])
    span = float(record["cell_span"])
    reference = select_reference_font(char, 108)
    paths = build_paths(char)
    image = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), "white")
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.load_default(size=18)
    small_font = ImageFont.load_default(size=12)
    header_char_font = ImageFont.truetype(str(reference.path), size=24)
    draw.text((20, 12), f"{number:03d}", fill="#17212b", font=title_font)
    draw.text((66, 24), char, fill="#17212b", font=header_char_font, anchor="mm")
    draw.text((84, 12), f"{record['codepoint']}  {record['unicode_name']}", fill="#17212b", font=title_font)
    draw.text((20, 35), f"{record['category']} | span {span:g} | {len(paths)} strokes | {reference.name}", fill="#536170", font=small_font)
    labels = ("Reference glyph", "Mouse path", "Overlay")
    for panel_left, label in zip(PANEL_LEFTS, labels):
        draw.text((panel_left + PANEL_SIZE / 2, 211), label, fill="#354250", font=small_font, anchor="mm")
        draw_grid(draw, panel_left, span)
    draw_reference(image, PANEL_LEFTS[0], char, span, reference.font, "#24313d")
    draw_paths(draw, PANEL_LEFTS[1], paths, show_order=True)
    draw_reference(image, PANEL_LEFTS[2], char, span, reference.font, "#aebfd0")
    draw_paths(draw, PANEL_LEFTS[2], paths, show_order=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)
    return output, reference.name


def make_overview(cards: list[Path], output: Path, columns: int = 8) -> None:
    thumb_size = (160, 72)
    rows = math.ceil(len(cards) / columns)
    overview = Image.new("RGB", (columns * thumb_size[0], rows * thumb_size[1]), "#dde3e9")
    for index, card_path in enumerate(cards):
        with Image.open(card_path) as card:
            thumb = card.resize(thumb_size, Image.Resampling.LANCZOS)
        overview.paste(thumb, ((index % columns) * thumb_size[0], (index // columns) * thumb_size[1]))
    output.parent.mkdir(parents=True, exist_ok=True)
    overview.save(output)


def write_checklist(
    records: list[dict[str, object]],
    cards: list[Path],
    fonts: list[str],
    output: Path,
    title: str,
) -> None:
    lines = [
        f"# Symbol SVG comparison checklist: {title}",
        "",
        f"Items: {len(records)}",
        "",
        "Review each fixed-cell overlay for topology, position, extent, curvature, start point, direction, and disconnected marks.",
        "",
    ]
    for number, (record, card, font_name) in enumerate(zip(records, cards, fonts), start=1):
        relative_card = card.relative_to(output.parent).as_posix()
        relative_svg = (ROOT / str(record["svg"])).relative_to(output.parent, walk_up=True).as_posix()
        lines.extend(
            [
                f"## {number:03d}. {record['symbol']} — {record['codepoint']}",
                "",
                f"![{record['codepoint']} comparison]({relative_card})",
                "",
                f"- Unicode name: {record['unicode_name']}",
                f"- Category: `{record['category']}`",
                f"- Cell span: `{record['cell_span']}`",
                f"- Expected strokes: `{record['expected_strokes']}`",
                f"- Reference font: `{font_name}`",
                f"- SVG: [{record['svg']}]({relative_svg})",
                f"- Manifest status: `{record['status']}`",
                "- Review status: [ ] Pending  [ ] Pass  [ ] Needs changes",
                "- Issue type: [ ] Position  [ ] Length  [ ] Shape  [ ] Direction  [ ] Missing component",
                "- Modification notes:",
                "",
            ]
        )
    output.write_text("\n".join(lines), encoding="utf-8")


def safe_label(value: str) -> str:
    label = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-").lower()
    return label or "selection"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate fixed-cell special-symbol comparison cards.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--batch", help="Select one manifest batch id.")
    parser.add_argument("--symbols", help="Select literal single-code-point symbols.")
    parser.add_argument("--status", choices=("candidate", "accepted", "in_progress", "verified", "deferred"))
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    _payload, records = load_records(args.manifest)
    selected = select_records(records, args.batch, args.symbols, args.status)
    selection_name = args.batch or ("symbols-" + "-".join(f"u{ord(char):04x}" for char in args.symbols or "")) or args.status or "all"
    output_dir = (args.output_dir or ROOT / "build" / "symbol-review" / safe_label(selection_name)).resolve()
    cards_dir = output_dir / "cards"
    cards: list[Path] = []
    fonts: list[str] = []
    for number, record in enumerate(selected, start=1):
        card = cards_dir / f"{number:03d}-u{ord(str(record['symbol'])):04x}.png"
        card_path, font_name = make_card(record, number, card)
        cards.append(card_path)
        fonts.append(font_name)
    make_overview(cards, output_dir / "overview.png")
    write_checklist(selected, cards, fonts, output_dir / "checklist.md", selection_name)
    print(f"Generated {len(cards)} cards in {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
