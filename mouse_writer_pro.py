# -*- coding: utf-8 -*-
"""Japanese kana and kanji stroke-order layout and mouse automation."""

from __future__ import annotations

import argparse
import ctypes
import sys
import time
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from collections.abc import Callable, Iterable
from ctypes import wintypes
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from pathlib import Path

from localization import Language, LocalizedOSError, LocalizedValueError, tr
from stroke_styles import DEFAULT_STROKE_STYLE_ID, StrokeStyle, discover_stroke_styles, style_by_id
from symbol_catalog import load_symbol_catalog

Point = tuple[float, float]
PathList = list[list[Point]]
PathBounds = tuple[float, float, float, float]

APP_VERSION = "2.6.2"
SCRIPT_DIR = Path(__file__).resolve().parent
BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", SCRIPT_DIR))
EXECUTABLE_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else SCRIPT_DIR
DEFAULT_KANJIVG_DIR = BUNDLE_DIR / "data/kanjivg/20250816/main/kanji"
DEFAULT_CUSTOM_STROKE_DIR = BUNDLE_DIR / "data/custom_strokes"
SYMBOL_MANIFEST_PATH = BUNDLE_DIR / "data/symbol_manifest.json"
SYMBOL_CATALOG = load_symbol_catalog(SYMBOL_MANIFEST_PATH)
ASCII_ALNUM = frozenset(chr(codepoint) for codepoint in range(0x21, 0x7F) if chr(codepoint).isalnum())
ASCII_PUNCTUATION = frozenset(chr(codepoint) for codepoint in range(0x21, 0x7F) if not chr(codepoint).isalnum())
FULLWIDTH_ALNUM = frozenset(chr(ord(char) + 0xFEE0) for char in ASCII_ALNUM)
FULLWIDTH_PUNCTUATION = frozenset(chr(ord(char) + 0xFEE0) for char in ASCII_PUNCTUATION)
JAPANESE_BRACKETS = frozenset("「」『』【】〈〉《》〔〕｢｣")
JAPANESE_PUNCTUATION = frozenset("、､。｡・･ーｰ") | JAPANESE_BRACKETS
VARIATION_SELECTORS = frozenset("\ufe0e\ufe0f")
BOX_DRAWING_SYMBOLS = SYMBOL_CATALOG.group_chars("box_drawing")
COMMON_SYMBOL_VARIANTS = SYMBOL_CATALOG.group_chars("common_variant")
SUPPORTED_EMOTICON_SYMBOLS = SYMBOL_CATALOG.group_chars("emoticon")
VERTICAL_COMMON_BRACKETS = SYMBOL_CATALOG.vertical_rotating
SYMBOL_CELL_SPANS = SYMBOL_CATALOG.cell_spans
SUPPORTED_SYMBOLS = (
    ASCII_PUNCTUATION
    | FULLWIDTH_PUNCTUATION
    | JAPANESE_PUNCTUATION
    | BOX_DRAWING_SYMBOLS
    | COMMON_SYMBOL_VARIANTS
    | SUPPORTED_EMOTICON_SYMBOLS
)
SMALL_KANA = frozenset("ぁぃぅぇぉっゃゅょゎゕゖァィゥェォッャュョヮヵヶ")
HALFWIDTH_KATAKANA = frozenset(chr(codepoint) for codepoint in range(0xFF66, 0xFF9E))
HALFWIDTH_VOICING_MARKS = frozenset("ﾞﾟ")
HALFWIDTH_KATAKANA_ALIASES = {
    char: unicodedata.normalize("NFKC", char)
    for char in HALFWIDTH_KATAKANA
}
STROKE_ALIASES = {
    **{
        chr(ord(char) + 0xFEE0): char
        for char in ASCII_ALNUM | ASCII_PUNCTUATION
        if char != "~"
    },
    "~": "～",
    "､": "、",
    "｡": "。",
    "･": "・",
    "ｰ": "ー",
    "｢": "「",
    "｣": "」",
    "ﾞ": "゛",
    "ﾟ": "゜",
    **HALFWIDTH_KATAKANA_ALIASES,
}
KANJIVG_VIEWBOX: PathBounds = (0.0, 0.0, 109.0, 109.0)
NATIVE_VIEWBOX_CHARS = SUPPORTED_SYMBOLS | SMALL_KANA | ASCII_ALNUM | FULLWIDTH_ALNUM
VERTICAL_ROTATE_CHARS = (
    ASCII_ALNUM
    | FULLWIDTH_ALNUM
    | JAPANESE_BRACKETS
    | VERTICAL_COMMON_BRACKETS
    | frozenset("()（）[]［］{}｛｝ーｰ-－_＿~～")
)
VERTICAL_CORNER_PUNCTUATION = frozenset("、､。｡")


def configure_console_encoding() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


configure_console_encoding()


class Orientation(str, Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class FlowDirection(str, Enum):
    RIGHT = "right"
    LEFT = "left"


@dataclass(frozen=True)
class GeneralSettings:
    font_size: float = 150.0
    char_gap: float = 12.0
    line_gap: float = 24.0
    orientation: Orientation = Orientation.HORIZONTAL
    flow: FlowDirection = FlowDirection.RIGHT
    stroke_style: str = DEFAULT_STROKE_STYLE_ID


@dataclass(frozen=True)
class EnvironmentSettings:
    countdown: int = 5
    sample_spacing: float = 2.0
    point_delay: float = 0.008
    move_duration: float = 0.0
    stroke_delay: float = 0.03


@dataclass(frozen=True)
class LayoutSettings:
    start_x: float
    start_y: float
    end_x: float | None = None
    end_y: float | None = None
    general: GeneralSettings = field(default_factory=GeneralSettings)
    point_step: int = 1
    preserve_aspect: bool = True


@dataclass(frozen=True)
class DrawSettings:
    """V1-compatible settings accepted by build_paths()."""

    start_x: float
    start_y: float
    char_width: float
    char_height: float
    char_gap: float
    line_gap: float
    point_step: int
    sample_spacing: float
    preserve_aspect: bool


@dataclass(frozen=True)
class WritingToken:
    text: str
    resource_char: str
    source_index: int
    source_length: int = 1
    span: float = 1.0
    subcells: int = 1
    is_whitespace: bool = False


@dataclass(frozen=True)
class GlyphPlacement:
    char: str
    resource_char: str
    source_index: int
    source_length: int
    x: float
    y: float
    span: float = 1.0
    subcells: int = 1
    box_width: float = 0.0
    box_height: float = 0.0
    rotation_degrees: int = 0
    is_whitespace: bool = False
    automatic_wrap_before: bool = False


@dataclass
class LayoutResult:
    paths: PathList = field(default_factory=list)
    placements: list[GlyphPlacement] = field(default_factory=list)
    kanjivg_chars: list[str] = field(default_factory=list)
    style_fallback_chars: list[str] = field(default_factory=list)
    automatic_wraps: list[int] = field(default_factory=list)
    explicit_wraps: list[int] = field(default_factory=list)
    canvas_bounds: tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0)


BuildResult = LayoutResult


@dataclass(frozen=True)
class LoadedGlyph:
    paths: PathList
    source_bounds: PathBounds | None
    actual_source: str
    fallback_used: bool = False


class LayoutError(LocalizedValueError):
    pass


class LayoutOverflowError(LayoutError):
    pass


class UnsupportedCharacterError(LayoutError):
    pass


class StrokeStyleResourceError(LocalizedOSError):
    pass


class WritingCancelled(RuntimeError):
    def __init__(self, message_key: str) -> None:
        self.message_key = message_key
        self.message_values: dict[str, object] = {}
        super().__init__(tr(message_key, Language.TRADITIONAL_CHINESE))


def require_svg_path():
    try:
        from svg.path import parse_path
    except ModuleNotFoundError as exc:
        raise SystemExit("缺少套件 svg.path。請先安裝 requirements.txt。") from exc
    return parse_path


def bounds(paths: Iterable[Iterable[Point]]) -> tuple[float, float, float, float]:
    points = [point for path in paths for point in path]
    if not points:
        return 0.0, 0.0, 1.0, 1.0
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    return min_x, min_y, max(max_x, min_x + 1), max(max_y, min_y + 1)


def decimate(path: list[Point], point_step: int) -> list[Point]:
    if point_step <= 1 or len(path) <= 2:
        return path
    reduced = path[::point_step]
    if reduced[-1] != path[-1]:
        reduced.append(path[-1])
    return reduced


def transform_paths(
    paths: PathList,
    origin_x: float,
    origin_y: float,
    box_width: float,
    box_height: float,
    preserve_aspect: bool,
    flip_y: bool,
    point_step: int,
    source_bounds: PathBounds | None = None,
    rotation_degrees: int = 0,
) -> PathList:
    if rotation_degrees not in {0, 90, 180, 270}:
        raise ValueError("rotation_degrees must be 0, 90, 180, or 270")
    min_x, min_y, max_x, max_y = source_bounds or bounds(paths)
    source_width = max_x - min_x
    source_height = max_y - min_y
    if preserve_aspect:
        scale = min(box_width / source_width, box_height / source_height)
        used_width = source_width * scale
        used_height = source_height * scale
        pad_x = (box_width - used_width) / 2
        pad_y = (box_height - used_height) / 2
        scale_x = scale_y = scale
    else:
        pad_x = pad_y = 0.0
        scale_x = box_width / source_width
        scale_y = box_height / source_height

    transformed: PathList = []
    for path in paths:
        if len(path) < 2:
            continue
        screen_path: list[Point] = []
        for x, y in decimate(path, point_step):
            if rotation_degrees:
                center_x = (min_x + max_x) / 2
                center_y = (min_y + max_y) / 2
                relative_x = x - center_x
                relative_y = y - center_y
                if rotation_degrees == 90:
                    x, y = center_x - relative_y, center_y + relative_x
                elif rotation_degrees == 180:
                    x, y = center_x - relative_x, center_y - relative_y
                else:
                    x, y = center_x + relative_y, center_y - relative_x
            sx = origin_x + pad_x + (x - min_x) * scale_x
            sy = (
                origin_y + box_height - (pad_y + (y - min_y) * scale_y)
                if flip_y
                else origin_y + pad_y + (y - min_y) * scale_y
            )
            screen_path.append((sx, sy))
        transformed.append(screen_path)
    return transformed


def kanjivg_file_for_char(char: str, kanjivg_dir: Path) -> Path:
    return kanjivg_dir / f"{ord(char):05x}.svg"


def stroke_file_for_char(
    char: str,
    kanjivg_dir: Path,
    custom_stroke_dir: Path = DEFAULT_CUSTOM_STROKE_DIR,
) -> Path:
    resolved = STROKE_ALIASES.get(char, char)
    custom_path = custom_stroke_dir / f"{ord(resolved):05x}.svg"
    if custom_path.exists():
        return custom_path
    return kanjivg_file_for_char(resolved, kanjivg_dir)


@lru_cache(maxsize=4)
def _open_stroke_style_archive(archive_path: Path) -> zipfile.ZipFile:
    return zipfile.ZipFile(archive_path)


def stroke_style_svg_for_char(char: str, style: StrokeStyle) -> bytes | None:
    resolved = STROKE_ALIASES.get(char, char)
    filename = f"{ord(resolved):05x}.svg"
    if style.strokes_dir is not None:
        style_path = style.strokes_dir / filename
        return style_path.read_bytes() if style_path.is_file() else None
    if style.strokes_archive is not None:
        try:
            return _open_stroke_style_archive(style.strokes_archive).read(f"strokes/{filename}")
        except KeyError:
            return None
        except (OSError, zipfile.BadZipFile) as exc:
            raise StrokeStyleResourceError("stroke_style_resource", style=style.id, char=resolved) from exc
    return None


def _sample_svg_root(root: ET.Element, sample_spacing: float) -> PathList:
    paths: PathList = []
    for element in root.iter():
        if not element.tag.endswith("path"):
            continue
        path_data = element.attrib.get("d")
        if not path_data:
            continue
        sampled = sample_svg_path(path_data, sample_spacing)
        if len(sampled) >= 2:
            paths.append(sampled)
    return paths


def _load_base_glyph(
    char: str,
    kanjivg_dir: Path,
    sample_spacing: float,
    custom_stroke_dir: Path,
    fallback_used: bool,
) -> LoadedGlyph | None:
    svg_path = stroke_file_for_char(char, kanjivg_dir, custom_stroke_dir)
    if not svg_path.is_file():
        return None
    paths = _sample_svg_root(ET.parse(svg_path).getroot(), sample_spacing)
    return LoadedGlyph(paths, None, DEFAULT_STROKE_STYLE_ID, fallback_used) if paths else None


def load_glyph_paths(
    char: str,
    kanjivg_dir: Path,
    sample_spacing: float,
    custom_stroke_dir: Path = DEFAULT_CUSTOM_STROKE_DIR,
    stroke_style: str = DEFAULT_STROKE_STYLE_ID,
) -> LoadedGlyph | None:
    """Load a direct style glyph, with explicit fallback only where allowed."""
    resolved = STROKE_ALIASES.get(char, char)
    style = style_by_id(BUNDLE_DIR, stroke_style)
    if style.id == DEFAULT_STROKE_STYLE_ID:
        return _load_base_glyph(resolved, kanjivg_dir, sample_spacing, custom_stroke_dir, False)
    style_svg = stroke_style_svg_for_char(resolved, style)
    if style_svg is not None:
        root = ET.fromstring(style_svg)
        if (
            root.attrib.get("data-runtime-mode") != "direct"
            or root.attrib.get("data-path-semantics") != "visual-centerline"
            or root.attrib.get("viewBox") != "0 0 109 109"
        ):
            raise StrokeStyleResourceError("stroke_style_resource", style=style.id, char=resolved)
        paths = _sample_svg_root(root, sample_spacing)
        if not paths:
            raise StrokeStyleResourceError("stroke_style_resource", style=style.id, char=resolved)
        return LoadedGlyph(paths, style.view_box, style.id, False)
    base_path = stroke_file_for_char(resolved, kanjivg_dir, custom_stroke_dir)
    is_custom = base_path.parent.resolve() == custom_stroke_dir.resolve()
    if ord(resolved) in style.fallback_codepoints or is_custom:
        return _load_base_glyph(resolved, kanjivg_dir, sample_spacing, custom_stroke_dir, True)
    if base_path.is_file() or ord(resolved) in style.style_only_codepoints:
        raise StrokeStyleResourceError("stroke_style_resource", style=style.id, char=resolved)
    return None


def is_japanese_writing_char(char: str) -> bool:
    codepoint = ord(char)
    return (
        0x3000 <= codepoint <= 0x303F
        or 0x3040 <= codepoint <= 0x309F
        or 0x30A0 <= codepoint <= 0x30FF
        or 0x31F0 <= codepoint <= 0x31FF
        or 0x3400 <= codepoint <= 0x4DBF
        or 0x4E00 <= codepoint <= 0x9FFF
        or 0xF900 <= codepoint <= 0xFAFF
        or 0xFF65 <= codepoint <= 0xFF9F
        or 0x20000 <= codepoint <= 0x2A6DF
        or 0x2A700 <= codepoint <= 0x2B73F
        or 0x2B740 <= codepoint <= 0x2B81F
        or 0x2B820 <= codepoint <= 0x2CEAF
        or 0x2CEB0 <= codepoint <= 0x2EBEF
        or 0x30000 <= codepoint <= 0x323AF
    )


def is_supported_writing_char(char: str) -> bool:
    return (
        is_japanese_writing_char(char)
        or (char.isascii() and char.isalnum())
        or char in FULLWIDTH_ALNUM
        or char in SUPPORTED_SYMBOLS
    )


def path_sample_count(segment, sample_spacing: float) -> int:
    try:
        segment_length = float(segment.length(error=1e-4))
    except Exception:
        segment_length = abs(segment.point(1) - segment.point(0))
    return max(1, int(segment_length / max(sample_spacing, 0.1)))


def sample_svg_path(path_data: str, sample_spacing: float) -> list[Point]:
    parsed = require_svg_path()(path_data)
    points: list[Point] = []
    for segment in parsed:
        steps = path_sample_count(segment, sample_spacing)
        for index in range(steps + 1):
            if points and index == 0:
                continue
            point = segment.point(index / steps)
            points.append((float(point.real), float(point.imag)))
    return points


def load_kanjivg_strokes(
    char: str,
    kanjivg_dir: Path,
    sample_spacing: float,
    custom_stroke_dir: Path = DEFAULT_CUSTOM_STROKE_DIR,
    stroke_style: str = DEFAULT_STROKE_STYLE_ID,
) -> PathList | None:
    loaded = load_glyph_paths(char, kanjivg_dir, sample_spacing, custom_stroke_dir, stroke_style)
    return loaded.paths if loaded is not None else None


def transform_kanjivg(
    strokes: PathList,
    origin_x: float,
    origin_y: float,
    box_width: float,
    box_height: float,
    preserve_aspect: bool,
    point_step: int,
    source_bounds: PathBounds | None = None,
    rotation_degrees: int = 0,
) -> PathList:
    return transform_paths(
        strokes,
        origin_x,
        origin_y,
        box_width,
        box_height,
        preserve_aspect,
        flip_y=False,
        point_step=point_step,
        source_bounds=source_bounds,
        rotation_degrees=rotation_degrees,
    )


def move_paths_to_opposite_corner(paths: PathList, source_bounds: PathBounds) -> PathList:
    min_x, min_y, max_x, max_y = bounds(paths)
    source_min_x, source_min_y, source_max_x, source_max_y = source_bounds
    dx = source_min_x + source_max_x - min_x - max_x
    dy = source_min_y + source_max_y - min_y - max_y
    return [[(x + dx, y + dy) for x, y in path] for path in paths]


def _validate_layout_settings(settings: LayoutSettings) -> None:
    general = settings.general
    if not 10 <= general.font_size <= 1000:
        raise LayoutError("layout_font_range")
    if general.char_gap < 0 or general.line_gap < 0:
        raise LayoutError("layout_gap_negative")
    if (settings.end_x is None) != (settings.end_y is None):
        raise LayoutError("layout_end_pair")
    if settings.end_x is None:
        return

    size = general.font_size
    minimum_x = size / 2 if general.orientation is Orientation.HORIZONTAL else size
    minimum_y = size if general.orientation is Orientation.HORIZONTAL else size / 2
    if settings.end_y < settings.start_y + minimum_y:
        raise LayoutError("layout_vertical_small")
    if general.flow is FlowDirection.RIGHT and settings.end_x < settings.start_x + minimum_x:
        raise LayoutError("layout_right_small")
    if general.flow is FlowDirection.LEFT and settings.end_x > settings.start_x - minimum_x:
        raise LayoutError("layout_left_small")


def is_halfwidth_char(char: str) -> bool:
    return unicodedata.east_asian_width(char) in {"Na", "H"}


def _token_span(char: str) -> float:
    if char == "\t":
        return 2.0
    if char in SYMBOL_CELL_SPANS:
        return SYMBOL_CELL_SPANS[char]
    return 0.5 if is_halfwidth_char(char) else 1.0


def _token_subcells(char: str) -> int:
    return 4 if char == "\t" else 1


def _token_extent(span: float, subcells: int, size: float, gap: float) -> float:
    return span * size + max(0, subcells - 1) * gap * 0.5


def _uses_halfwidth_spacing(token: WritingToken) -> bool:
    return token.span == 0.5 or token.subcells > 1


def _gap_between_tokens(previous: WritingToken, current: WritingToken, gap: float) -> float:
    if _uses_halfwidth_spacing(previous) and _uses_halfwidth_spacing(current):
        return gap * 0.5
    return gap


def tokenize_writing_text(text: str) -> list[WritingToken]:
    tokens: list[WritingToken] = []
    source_index = 0
    while source_index < len(text):
        char = text[source_index]
        if char in VARIATION_SELECTORS:
            source_index += 1
            continue
        if char == "\r":
            source_index += 1
            continue
        if char == "\n":
            tokens.append(WritingToken(char, char, source_index, is_whitespace=True))
            source_index += 1
            continue

        if (
            char in HALFWIDTH_KATAKANA
            and source_index + 1 < len(text)
            and text[source_index + 1] in HALFWIDTH_VOICING_MARKS
        ):
            pair = text[source_index : source_index + 2]
            normalized = unicodedata.normalize("NFKC", pair)
            if len(normalized) == 1:
                tokens.append(
                    WritingToken(
                        text=pair,
                        resource_char=normalized,
                        source_index=source_index,
                        source_length=2,
                        span=0.5,
                    )
                )
                source_index += 2
                continue

        span = _token_span(char)
        subcells = _token_subcells(char)
        tokens.append(
            WritingToken(
                text=char,
                resource_char=STROKE_ALIASES.get(char, char),
                source_index=source_index,
                span=span,
                subcells=subcells,
                is_whitespace=char.isspace(),
            )
        )
        source_index += 1
    return tokens


def vertical_rotation_for_token(token: WritingToken, orientation: Orientation) -> int:
    if orientation is not Orientation.VERTICAL:
        return 0
    return 90 if token.text in VERTICAL_ROTATE_CHARS else 0


def build_layout(
    text: str,
    kanjivg_dir: Path,
    settings: LayoutSettings,
    environment: EnvironmentSettings | None = None,
) -> LayoutResult:
    tokens = tokenize_writing_text(text)
    if not tokens or not any(not token.is_whitespace for token in tokens):
        raise LayoutError("layout_text_empty")
    _validate_layout_settings(settings)
    environment = environment or EnvironmentSettings()
    general = settings.general
    size = general.font_size
    bounded = settings.end_x is not None and settings.end_y is not None
    result = LayoutResult()
    cursor_x = (
        settings.start_x - size
        if general.orientation is Orientation.VERTICAL and general.flow is FlowDirection.LEFT
        else settings.start_x
    )
    cursor_y = settings.start_y
    units_on_line = 0.0
    previous_token: WritingToken | None = None
    line_cross_extent = size

    def secondary_fits(cross_extent: float = size) -> bool:
        if not bounded:
            return True
        assert settings.end_x is not None and settings.end_y is not None
        if general.orientation is Orientation.HORIZONTAL:
            return cursor_y + cross_extent <= settings.end_y
        if general.flow is FlowDirection.RIGHT:
            return cursor_x + cross_extent <= settings.end_x
        return cursor_x + size - cross_extent >= settings.end_x

    def primary_fits(extent: float) -> bool:
        if not bounded:
            return True
        assert settings.end_x is not None and settings.end_y is not None
        if general.orientation is Orientation.VERTICAL:
            return cursor_y + extent <= settings.end_y
        if general.flow is FlowDirection.RIGHT:
            return cursor_x + extent <= settings.end_x
        return cursor_x - extent >= settings.end_x

    def wrap(source_index: int, explicit: bool) -> None:
        nonlocal cursor_x, cursor_y, units_on_line, previous_token, line_cross_extent
        if general.orientation is Orientation.HORIZONTAL:
            cursor_x = settings.start_x
            cursor_y += line_cross_extent + general.line_gap
        else:
            cursor_y = settings.start_y
            step = line_cross_extent + general.line_gap
            cursor_x += step if general.flow is FlowDirection.RIGHT else -step
        units_on_line = 0.0
        previous_token = None
        line_cross_extent = size
        (result.explicit_wraps if explicit else result.automatic_wraps).append(source_index)
        if not secondary_fits():
            raise LayoutOverflowError("layout_wrap_overflow", index=source_index + 1)

    for token in tokens:
        if token.text == "\n":
            wrap(token.source_index, explicit=True)
            continue

        span = token.span
        subcells = token.subcells
        extent = _token_extent(span, subcells, size, general.char_gap)
        box_width = extent if general.orientation is Orientation.HORIZONTAL else size
        box_height = size if general.orientation is Orientation.HORIZONTAL else extent
        cross_extent = box_height if general.orientation is Orientation.HORIZONTAL else box_width
        gap_before = (
            _gap_between_tokens(previous_token, token, general.char_gap)
            if previous_token is not None
            else 0.0
        )
        required_extent = gap_before + extent
        automatic_wrap = False
        if not primary_fits(required_extent):
            if units_on_line == 0:
                raise LayoutOverflowError("layout_primary_overflow", index=token.source_index + 1)
            wrap(token.source_index, explicit=False)
            automatic_wrap = True
            gap_before = 0.0
            required_extent = extent
            if not primary_fits(required_extent):
                raise LayoutOverflowError("layout_wrap_still_overflow", index=token.source_index + 1)
        if not secondary_fits(cross_extent):
            raise LayoutOverflowError("layout_character_overflow", index=token.source_index + 1)

        if general.orientation is Orientation.HORIZONTAL:
            placement_x = (
                cursor_x - gap_before - extent
                if general.flow is FlowDirection.LEFT
                else cursor_x + gap_before
            )
            placement_y = cursor_y
        else:
            placement_x = cursor_x
            placement_y = cursor_y + gap_before

        rotation_degrees = vertical_rotation_for_token(token, general.orientation)
        placement = GlyphPlacement(
            char=token.text,
            resource_char=token.resource_char,
            source_index=token.source_index,
            source_length=token.source_length,
            x=placement_x,
            y=placement_y,
            span=span,
            subcells=subcells,
            box_width=box_width,
            box_height=box_height,
            rotation_degrees=rotation_degrees,
            is_whitespace=token.is_whitespace,
            automatic_wrap_before=automatic_wrap,
        )
        result.placements.append(placement)

        if not token.is_whitespace:
            if not is_supported_writing_char(token.resource_char):
                raise UnsupportedCharacterError(
                    "unsupported_character",
                    index=token.source_index + 1,
                    char=token.text,
                )
            loaded = load_glyph_paths(
                token.resource_char,
                kanjivg_dir,
                environment.sample_spacing,
                stroke_style=general.stroke_style,
            )
            if not loaded or not loaded.paths:
                raise UnsupportedCharacterError(
                    "missing_character",
                    index=token.source_index + 1,
                    char=token.text,
                )
            strokes = loaded.paths
            if loaded.fallback_used:
                result.style_fallback_chars.append(token.text)
            if general.orientation is Orientation.VERTICAL and token.text in VERTICAL_CORNER_PUNCTUATION:
                strokes = move_paths_to_opposite_corner(strokes, loaded.source_bounds or KANJIVG_VIEWBOX)
            use_native_viewbox = token.span == 0.5 or token.resource_char in NATIVE_VIEWBOX_CHARS
            result.paths.extend(
                transform_kanjivg(
                    strokes,
                    placement_x,
                    placement_y,
                    extent if general.orientation is Orientation.HORIZONTAL else size,
                    size if general.orientation is Orientation.HORIZONTAL else extent,
                    False if token.span == 0.5 else settings.preserve_aspect,
                    settings.point_step,
                    loaded.source_bounds or (KANJIVG_VIEWBOX if use_native_viewbox else None),
                    rotation_degrees=rotation_degrees,
                )
            )
            result.kanjivg_chars.append(token.text)

        if general.orientation is Orientation.HORIZONTAL:
            cursor_x += required_extent if general.flow is FlowDirection.RIGHT else -required_extent
        else:
            cursor_y += required_extent
        units_on_line += span
        previous_token = token
        line_cross_extent = max(line_cross_extent, cross_extent)

    if bounded:
        assert settings.end_x is not None and settings.end_y is not None
        min_x = min(settings.start_x, settings.end_x)
        max_x = max(settings.start_x, settings.end_x)
        result.canvas_bounds = (min_x, settings.start_y, max_x, settings.end_y)
    elif result.placements:
        def placement_extent(placement: GlyphPlacement) -> float:
            return _token_extent(placement.span, placement.subcells, size, general.char_gap)

        placement_min_x = min(p.x for p in result.placements)
        placement_max_x = max(p.x + (p.box_width or placement_extent(p)) for p in result.placements)
        placement_max_y = max(p.y + (p.box_height or size) for p in result.placements)
        result.canvas_bounds = (placement_min_x, settings.start_y, placement_max_x, placement_max_y)
    return result


def build_paths(text: str, kanjivg_dir: Path, settings: DrawSettings) -> BuildResult:
    general = GeneralSettings(
        font_size=min(settings.char_width, settings.char_height),
        char_gap=settings.char_gap,
        line_gap=settings.line_gap,
    )
    layout = LayoutSettings(
        start_x=settings.start_x,
        start_y=settings.start_y,
        general=general,
        point_step=settings.point_step,
        preserve_aspect=settings.preserve_aspect,
    )
    environment = EnvironmentSettings(sample_spacing=settings.sample_spacing)
    return build_layout(text, kanjivg_dir, layout, environment)


def path_stats(paths: PathList) -> tuple[int, int]:
    return len(paths), sum(len(path) for path in paths)


def preview_paths(paths: PathList, output: Path) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ModuleNotFoundError as exc:
        raise SystemExit("缺少套件 matplotlib。請先安裝 requirements.txt。") from exc
    if not paths:
        raise SystemExit("沒有可預覽的筆跡路徑。")
    min_x, min_y, max_x, max_y = bounds(paths)
    padding = 20
    fig, ax = plt.subplots(
        figsize=(max(4, (max_x - min_x + padding * 2) / 120), max(3, (max_y - min_y + padding * 2) / 120)),
        dpi=120,
    )
    for index, path in enumerate(paths, start=1):
        ax.plot([p[0] for p in path], [p[1] for p in path], color="black", linewidth=1.4)
        ax.text(path[0][0], path[0][1], str(index), fontsize=8, color="#b00020")
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(min_x - padding, max_x + padding)
    ax.set_ylim(max_y + padding, min_y - padding)
    ax.axis("off")
    fig.savefig(output, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)


class _MouseInput(ctypes.Structure):
    _fields_ = (
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", wintypes.WPARAM),
    )


class _InputUnion(ctypes.Union):
    _fields_ = (("mi", _MouseInput),)


class _Input(ctypes.Structure):
    _anonymous_ = ("data",)
    _fields_ = (("type", wintypes.DWORD), ("data", _InputUnion))


class WindowsSendInputMouse:
    MOUSEEVENTF_MOVE = 0x0001
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004
    MOUSEEVENTF_MOVE_NOCOALESCE = 0x2000
    MOUSEEVENTF_VIRTUALDESK = 0x4000
    MOUSEEVENTF_ABSOLUTE = 0x8000

    def __init__(self) -> None:
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.send_input = self.user32.SendInput
        self.send_input.argtypes = (wintypes.UINT, ctypes.POINTER(_Input), ctypes.c_int)
        self.send_input.restype = wintypes.UINT
        self.virtual_left = self.user32.GetSystemMetrics(76)
        self.virtual_top = self.user32.GetSystemMetrics(77)
        self.virtual_width = self.user32.GetSystemMetrics(78)
        self.virtual_height = self.user32.GetSystemMetrics(79)
        if self.virtual_width <= 1 or self.virtual_height <= 1:
            raise LocalizedOSError("virtual_screen_error")

    @property
    def screen_bounds(self) -> tuple[int, int, int, int]:
        return (
            self.virtual_left,
            self.virtual_top,
            self.virtual_left + self.virtual_width,
            self.virtual_top + self.virtual_height,
        )

    def absolute_coordinates(self, x: int, y: int) -> tuple[int, int]:
        return (
            round((x - self.virtual_left) * 65535 / (self.virtual_width - 1)),
            round((y - self.virtual_top) * 65535 / (self.virtual_height - 1)),
        )

    def send(self, flags: int, x: int = 0, y: int = 0) -> None:
        event = _Input(
            type=0,
            data=_InputUnion(mi=_MouseInput(x, y, 0, flags, 0, 0)),
        )
        if self.send_input(1, ctypes.byref(event), ctypes.sizeof(_Input)) != 1:
            raise LocalizedOSError("send_input_error", code=ctypes.get_last_error())

    def move_to(self, x: int, y: int) -> None:
        absolute_x, absolute_y = self.absolute_coordinates(x, y)
        self.send(
            self.MOUSEEVENTF_MOVE
            | self.MOUSEEVENTF_MOVE_NOCOALESCE
            | self.MOUSEEVENTF_VIRTUALDESK
            | self.MOUSEEVENTF_ABSOLUTE,
            absolute_x,
            absolute_y,
        )

    def left_down(self) -> None:
        self.send(self.MOUSEEVENTF_LEFTDOWN)

    def left_up(self) -> None:
        self.send(self.MOUSEEVENTF_LEFTUP)


def escape_pressed() -> bool:
    if sys.platform != "win32":
        return False
    return bool(ctypes.windll.user32.GetAsyncKeyState(0x1B) & 0x8000)


def interruptible_sleep(seconds: float, stop_requested: Callable[[], bool] | None = None) -> None:
    deadline = time.monotonic() + max(0.0, seconds)
    while True:
        if stop_requested and stop_requested():
            raise WritingCancelled("escape_operation")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return
        time.sleep(min(0.02, remaining))


def validate_screen_bounds(paths: PathList, allow_offscreen: bool) -> None:
    if allow_offscreen or not paths:
        return
    if sys.platform == "win32":
        min_x, min_y, max_x, max_y = WindowsSendInputMouse().screen_bounds
    else:
        import pyautogui

        width, height = pyautogui.size()
        min_x, min_y, max_x, max_y = 0, 0, width, height
    for path in paths:
        for x, y in path:
            if not (min_x <= x < max_x and min_y <= y < max_y):
                raise LayoutError(
                    "screen_overflow",
                    x=x,
                    y=y,
                    min_x=min_x,
                    min_y=min_y,
                    max_x=max_x - 1,
                    max_y=max_y - 1,
                )


def draw_with_mouse(
    paths: PathList,
    countdown: int,
    move_duration: float,
    point_delay: float,
    stroke_delay: float,
    allow_offscreen: bool,
    stop_requested: Callable[[], bool] | None = None,
) -> None:
    try:
        import pyautogui
    except ModuleNotFoundError as exc:
        raise SystemExit("缺少套件 pyautogui。請先安裝 requirements.txt。") from exc

    validate_screen_bounds(paths, allow_offscreen)
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0
    stop_requested = stop_requested or escape_pressed
    move_duration = max(0.0, move_duration)
    point_delay = max(0.0, point_delay)
    stroke_delay = max(0.0, stroke_delay)
    windows_mouse = WindowsSendInputMouse() if sys.platform == "win32" else None
    button_down = False

    def check_stop() -> None:
        if stop_requested and stop_requested():
            raise WritingCancelled("escape_writing")
        if pyautogui.position() in pyautogui.FAILSAFE_POINTS:
            raise WritingCancelled("failsafe_stop")

    def move_to_sample(x: float, y: float) -> None:
        check_stop()
        if windows_mouse:
            windows_mouse.move_to(round(x), round(y))
            interruptible_sleep(move_duration, stop_requested)
        elif move_duration >= pyautogui.MINIMUM_DURATION:
            pyautogui.moveTo(round(x), round(y), duration=move_duration)
        else:
            pyautogui.moveTo(round(x), round(y), duration=0)
            interruptible_sleep(move_duration, stop_requested)

    try:
        for remaining in range(max(0, countdown), 0, -1):
            print(remaining)
            interruptible_sleep(1, stop_requested)

        for path in paths:
            if len(path) < 2:
                continue
            move_to_sample(*path[0])
            interruptible_sleep(max(stroke_delay, 0.02), stop_requested)
            if windows_mouse:
                windows_mouse.left_down()
            else:
                pyautogui.mouseDown()
            button_down = True
            try:
                for x, y in path[1:]:
                    move_to_sample(x, y)
                    interruptible_sleep(point_delay, stop_requested)
            finally:
                if windows_mouse:
                    windows_mouse.left_up()
                else:
                    pyautogui.mouseUp()
                button_down = False
            interruptible_sleep(stroke_delay, stop_requested)
    finally:
        if button_down:
            if windows_mouse:
                windows_mouse.left_up()
            else:
                pyautogui.mouseUp()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="依 KanjiVG 筆順控制滑鼠書寫日文。")
    parser.add_argument("--version", action="version", version=f"%(prog)s {APP_VERSION}")
    parser.add_argument("--text", default="こんにちは")
    parser.add_argument("--kanjivg-dir", default=str(DEFAULT_KANJIVG_DIR))
    parser.add_argument("--start-x", type=float, default=877)
    parser.add_argument("--start-y", type=float, default=325)
    parser.add_argument("--end-x", type=float)
    parser.add_argument("--end-y", type=float)
    parser.add_argument("--font-size", type=float)
    parser.add_argument("--char-width", type=float, default=150)
    parser.add_argument("--char-height", type=float, default=150)
    parser.add_argument("--char-gap", type=float, default=12)
    parser.add_argument("--line-gap", type=float, default=24)
    parser.add_argument("--orientation", choices=[item.value for item in Orientation], default="horizontal")
    parser.add_argument("--flow", choices=[item.value for item in FlowDirection], default="right")
    parser.add_argument(
        "--stroke-style",
        choices=[style.id for style in discover_stroke_styles(BUNDLE_DIR)],
        default=DEFAULT_STROKE_STYLE_ID,
    )
    parser.add_argument("--point-step", type=int, default=1)
    parser.add_argument("--sample-spacing", type=float, default=2.0)
    parser.add_argument("--no-preserve-aspect", action="store_true")
    parser.add_argument("--preview", nargs="?", const="preview.png")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--countdown", type=int, default=5)
    parser.add_argument("--move-duration", type=float, default=0.0)
    parser.add_argument("--point-delay", type=float, default=0.008)
    parser.add_argument("--stroke-delay", type=float, default=0.03)
    parser.add_argument("--allow-offscreen", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    font_size = args.font_size or min(args.char_width, args.char_height)
    general = GeneralSettings(
        font_size=font_size,
        char_gap=args.char_gap,
        line_gap=args.line_gap,
        orientation=Orientation(args.orientation),
        flow=FlowDirection(args.flow),
        stroke_style=args.stroke_style,
    )
    environment = EnvironmentSettings(
        countdown=max(0, args.countdown),
        sample_spacing=max(0.1, args.sample_spacing),
        point_delay=max(0.0, args.point_delay),
        move_duration=max(0.0, args.move_duration),
        stroke_delay=max(0.0, args.stroke_delay),
    )
    layout = LayoutSettings(
        start_x=args.start_x,
        start_y=args.start_y,
        end_x=args.end_x,
        end_y=args.end_y,
        general=general,
        point_step=max(1, args.point_step),
        preserve_aspect=not args.no_preserve_aspect,
    )
    result = build_layout(args.text, Path(args.kanjivg_dir), layout, environment)
    stroke_count, point_count = path_stats(result.paths)
    print(f"文字：{args.text}")
    print(f"產生 {stroke_count} 條筆畫路徑、{point_count} 個滑鼠點。")
    if args.preview:
        preview_paths(result.paths, Path(args.preview))
        print(f"已輸出預覽圖：{Path(args.preview).resolve()}")
    if args.execute:
        draw_with_mouse(
            result.paths,
            countdown=environment.countdown,
            move_duration=environment.move_duration,
            point_delay=environment.point_delay,
            stroke_delay=environment.stroke_delay,
            allow_offscreen=args.allow_offscreen,
        )
    elif not args.preview:
        print("未移動滑鼠；請使用 --preview 或 --execute。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
