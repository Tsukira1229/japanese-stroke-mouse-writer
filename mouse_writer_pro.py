# -*- coding: utf-8 -*-
"""Japanese kana and kanji stroke-order layout and mouse automation."""

from __future__ import annotations

import argparse
import ctypes
import sys
import time
import unicodedata
import xml.etree.ElementTree as ET
from collections.abc import Callable, Iterable
from ctypes import wintypes
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from localization import Language, LocalizedOSError, LocalizedValueError, tr

Point = tuple[float, float]
PathList = list[list[Point]]
PathBounds = tuple[float, float, float, float]

APP_VERSION = "2.2.0"
SCRIPT_DIR = Path(__file__).resolve().parent
BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", SCRIPT_DIR))
EXECUTABLE_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else SCRIPT_DIR
DEFAULT_KANJIVG_DIR = BUNDLE_DIR / "data/kanjivg/20250816/main/kanji"
DEFAULT_CUSTOM_STROKE_DIR = BUNDLE_DIR / "data/custom_strokes"
ASCII_ALNUM = frozenset(chr(codepoint) for codepoint in range(0x21, 0x7F) if chr(codepoint).isalnum())
ASCII_PUNCTUATION = frozenset(chr(codepoint) for codepoint in range(0x21, 0x7F) if not chr(codepoint).isalnum())
FULLWIDTH_ALNUM = frozenset(chr(ord(char) + 0xFEE0) for char in ASCII_ALNUM)
FULLWIDTH_PUNCTUATION = frozenset(chr(ord(char) + 0xFEE0) for char in ASCII_PUNCTUATION)
JAPANESE_PUNCTUATION = frozenset("、､。｡・･ーｰ")
SUPPORTED_SYMBOLS = ASCII_PUNCTUATION | FULLWIDTH_PUNCTUATION | JAPANESE_PUNCTUATION
SMALL_KANA = frozenset("ぁぃぅぇぉっゃゅょゎゕゖァィゥェォッャュョヮヵヶ")
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
}
KANJIVG_VIEWBOX: PathBounds = (0.0, 0.0, 109.0, 109.0)
NATIVE_VIEWBOX_CHARS = SUPPORTED_SYMBOLS | SMALL_KANA | ASCII_ALNUM | FULLWIDTH_ALNUM


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
class GlyphPlacement:
    char: str
    source_index: int
    x: float
    y: float
    span: float = 1.0
    subcells: int = 1
    is_whitespace: bool = False
    automatic_wrap_before: bool = False


@dataclass
class LayoutResult:
    paths: PathList = field(default_factory=list)
    placements: list[GlyphPlacement] = field(default_factory=list)
    kanjivg_chars: list[str] = field(default_factory=list)
    automatic_wraps: list[int] = field(default_factory=list)
    explicit_wraps: list[int] = field(default_factory=list)
    canvas_bounds: tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0)


BuildResult = LayoutResult


class LayoutError(LocalizedValueError):
    pass


class LayoutOverflowError(LayoutError):
    pass


class UnsupportedCharacterError(LayoutError):
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
) -> PathList:
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
) -> PathList | None:
    svg_path = stroke_file_for_char(char, kanjivg_dir, custom_stroke_dir)
    if not svg_path.exists():
        return None
    root = ET.parse(svg_path).getroot()
    strokes: PathList = []
    for element in root.iter():
        if not element.tag.endswith("path"):
            continue
        path_data = element.attrib.get("d")
        if not path_data:
            continue
        sampled = sample_svg_path(path_data, sample_spacing)
        if len(sampled) >= 2:
            strokes.append(sampled)
    return strokes


def transform_kanjivg(
    strokes: PathList,
    origin_x: float,
    origin_y: float,
    box_width: float,
    box_height: float,
    preserve_aspect: bool,
    point_step: int,
    source_bounds: PathBounds | None = None,
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
    )


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
    return 0.5 if is_halfwidth_char(char) else 1.0


def _token_subcells(char: str) -> int:
    return 4 if char == "\t" else 1


def _token_extent(span: float, subcells: int, size: float, gap: float) -> float:
    return span * size + max(0, subcells - 1) * gap


def build_layout(
    text: str,
    kanjivg_dir: Path,
    settings: LayoutSettings,
    environment: EnvironmentSettings | None = None,
) -> LayoutResult:
    if not text or not any(not char.isspace() for char in text):
        raise LayoutError("layout_text_empty")
    _validate_layout_settings(settings)
    environment = environment or EnvironmentSettings()
    general = settings.general
    size = general.font_size
    secondary_step = size + general.line_gap
    bounded = settings.end_x is not None and settings.end_y is not None
    result = LayoutResult()
    cursor_x = (
        settings.start_x - size
        if general.orientation is Orientation.VERTICAL and general.flow is FlowDirection.LEFT
        else settings.start_x
    )
    cursor_y = settings.start_y
    units_on_line = 0.0

    def secondary_fits() -> bool:
        if not bounded:
            return True
        assert settings.end_x is not None and settings.end_y is not None
        if general.orientation is Orientation.HORIZONTAL:
            return cursor_y + size <= settings.end_y
        if general.flow is FlowDirection.RIGHT:
            return cursor_x + size <= settings.end_x
        return cursor_x >= settings.end_x

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
        nonlocal cursor_x, cursor_y, units_on_line
        if general.orientation is Orientation.HORIZONTAL:
            cursor_x = settings.start_x
            cursor_y += secondary_step
        else:
            cursor_y = settings.start_y
            cursor_x += secondary_step if general.flow is FlowDirection.RIGHT else -secondary_step
        units_on_line = 0.0
        (result.explicit_wraps if explicit else result.automatic_wraps).append(source_index)
        if not secondary_fits():
            raise LayoutOverflowError("layout_wrap_overflow", index=source_index + 1)

    for source_index, char in enumerate(text):
        if char == "\r":
            continue
        if char == "\n":
            wrap(source_index, explicit=True)
            continue

        span = _token_span(char)
        subcells = _token_subcells(char)
        extent = _token_extent(span, subcells, size, general.char_gap)
        automatic_wrap = False
        if not primary_fits(extent):
            if units_on_line == 0:
                raise LayoutOverflowError("layout_primary_overflow", index=source_index + 1)
            wrap(source_index, explicit=False)
            automatic_wrap = True
            if not primary_fits(extent):
                raise LayoutOverflowError("layout_wrap_still_overflow", index=source_index + 1)
        if not secondary_fits():
            raise LayoutOverflowError("layout_character_overflow", index=source_index + 1)

        placement_x = (
            cursor_x - extent
            if general.orientation is Orientation.HORIZONTAL and general.flow is FlowDirection.LEFT
            else cursor_x
        )

        placement = GlyphPlacement(
            char=char,
            source_index=source_index,
            x=placement_x,
            y=cursor_y,
            span=span,
            subcells=subcells,
            is_whitespace=char.isspace(),
            automatic_wrap_before=automatic_wrap,
        )
        result.placements.append(placement)

        if not char.isspace():
            if not is_supported_writing_char(char):
                raise UnsupportedCharacterError("unsupported_character", index=source_index + 1, char=char)
            strokes = load_kanjivg_strokes(char, kanjivg_dir, environment.sample_spacing)
            if not strokes:
                raise UnsupportedCharacterError("missing_character", index=source_index + 1, char=char)
            result.paths.extend(
                transform_kanjivg(
                    strokes,
                    placement_x,
                    cursor_y,
                    extent if general.orientation is Orientation.HORIZONTAL else size,
                    size if general.orientation is Orientation.HORIZONTAL else extent,
                    False if is_halfwidth_char(char) else settings.preserve_aspect,
                    settings.point_step,
                    KANJIVG_VIEWBOX if char in NATIVE_VIEWBOX_CHARS else None,
                )
            )
            result.kanjivg_chars.append(char)

        if general.orientation is Orientation.HORIZONTAL:
            cursor_x += extent + general.char_gap if general.flow is FlowDirection.RIGHT else -(extent + general.char_gap)
        else:
            cursor_y += extent + general.char_gap
        units_on_line += span

    if bounded:
        assert settings.end_x is not None and settings.end_y is not None
        min_x = min(settings.start_x, settings.end_x)
        max_x = max(settings.start_x, settings.end_x)
        result.canvas_bounds = (min_x, settings.start_y, max_x, settings.end_y)
    elif result.placements:
        def placement_extent(placement: GlyphPlacement) -> float:
            return _token_extent(placement.span, placement.subcells, size, general.char_gap)

        placement_min_x = min(p.x for p in result.placements)
        placement_max_x = max(
            p.x + (placement_extent(p) if general.orientation is Orientation.HORIZONTAL else size)
            for p in result.placements
        )
        placement_max_y = max(
            p.y + (size if general.orientation is Orientation.HORIZONTAL else placement_extent(p))
            for p in result.placements
        )
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
