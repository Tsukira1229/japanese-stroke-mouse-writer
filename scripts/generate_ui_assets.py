from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageDraw
from svg.path import parse_path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "data" / "ui" / "icons" / "source"
OUTPUT_DIR = ROOT / "data" / "ui" / "icons"
PALETTES = {
    "light": "#3E373D",
    "dark": "#F4F0E7",
}
ICON_SIZE = 18
SUPERSAMPLE = 4


def _points(value: str) -> list[tuple[float, float]]:
    numbers = [float(item) for item in value.replace(",", " ").split()]
    return list(zip(numbers[::2], numbers[1::2]))


def _scaled(points: list[tuple[float, float]], scale: float) -> list[tuple[float, float]]:
    return [(x * scale, y * scale) for x, y in points]


def render_lucide(source: Path, destination: Path, color: str) -> None:
    scale = ICON_SIZE * SUPERSAMPLE / 24
    image = Image.new("RGBA", (ICON_SIZE * SUPERSAMPLE, ICON_SIZE * SUPERSAMPLE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    width = max(1, round(2 * scale))
    root = ET.parse(source).getroot()
    for element in root:
        tag = element.tag.rsplit("}", 1)[-1]
        points: list[tuple[float, float]] = []
        closed = False
        if tag == "path":
            path = parse_path(element.attrib["d"])
            samples = max(24, len(path) * 18)
            points = [(path.point(index / samples).real, path.point(index / samples).imag) for index in range(samples + 1)]
        elif tag == "line":
            points = [
                (float(element.attrib["x1"]), float(element.attrib["y1"])),
                (float(element.attrib["x2"]), float(element.attrib["y2"])),
            ]
        elif tag in {"polyline", "polygon"}:
            points = _points(element.attrib["points"])
            closed = tag == "polygon"
        elif tag == "circle":
            cx = float(element.attrib["cx"])
            cy = float(element.attrib["cy"])
            radius = float(element.attrib["r"])
            box = tuple(value * scale for value in (cx - radius, cy - radius, cx + radius, cy + radius))
            draw.ellipse(box, outline=color, width=width)
            continue
        elif tag == "rect":
            x = float(element.attrib.get("x", "0"))
            y = float(element.attrib.get("y", "0"))
            w = float(element.attrib["width"])
            h = float(element.attrib["height"])
            radius = float(element.attrib.get("rx", "0")) * scale
            draw.rounded_rectangle(tuple(value * scale for value in (x, y, x + w, y + h)), radius=radius, outline=color, width=width)
            continue
        if points:
            if closed:
                points.append(points[0])
            draw.line(_scaled(points, scale), fill=color, width=width, joint="curve")
            radius = width / 2
            for x, y in (points[0], points[-1]):
                draw.ellipse(((x * scale) - radius, (y * scale) - radius, (x * scale) + radius, (y * scale) + radius), fill=color)
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.resize((ICON_SIZE, ICON_SIZE), Image.Resampling.LANCZOS).save(destination)


def generate_app_icon() -> None:
    size = 256
    image = Image.new("RGBA", (size, size), "#FBF7EE")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((28, 28, 228, 228), radius=42, fill="#FFFCF4", outline="#6F946D", width=12)
    draw.line((72, 74, 184, 74), fill="#6F946D", width=8)
    draw.line((72, 124, 184, 124), fill="#D5CCC0", width=6)
    draw.line((72, 174, 184, 174), fill="#D5CCC0", width=6)
    draw.line((96, 58, 96, 196), fill="#D5CCC0", width=6)
    draw.line((148, 58, 148, 196), fill="#D5CCC0", width=6)
    draw.line((92, 88, 150, 105, 116, 142, 174, 169), fill="#B94C63", width=15, joint="curve")
    draw.line((194, 44, 194, 70), fill="#A999BD", width=7)
    draw.line((181, 57, 207, 57), fill="#A999BD", width=7)
    draw.line((185, 48, 203, 66), fill="#A999BD", width=5)
    draw.line((203, 48, 185, 66), fill="#A999BD", width=5)
    icon_dir = ROOT / "data" / "ui"
    icon_dir.mkdir(parents=True, exist_ok=True)
    image.save(icon_dir / "app-icon.png")
    image.save(icon_dir / "JapaneseStrokeMouseWriter.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])


def main() -> None:
    for theme, color in PALETTES.items():
        for source in sorted(SOURCE_DIR.glob("*.svg")):
            render_lucide(source, OUTPUT_DIR / theme / f"{source.stem}.png", color)
    generate_app_icon()


if __name__ == "__main__":
    main()
