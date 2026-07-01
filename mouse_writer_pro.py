# -*- coding: utf-8 -*-
"""
Mouse writer for Japanese kana and kanji.

All non-space characters are drawn from KanjiVG stroke-order SVG data.
"""

from __future__ import annotations

import argparse
import ctypes
import sys
import time
import xml.etree.ElementTree as ET
from ctypes import wintypes
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

Point = tuple[float, float]
PathList = list[list[Point]]

APP_VERSION = "1.0"
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_KANJIVG_DIR = SCRIPT_DIR / "data/kanjivg/20250816/main/kanji"


def configure_console_encoding() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


configure_console_encoding()


@dataclass(frozen=True)
class DrawSettings:
    start_x: float
    start_y: float
    char_width: float
    char_height: float
    char_gap: float
    line_gap: float
    point_step: int
    sample_spacing: float
    preserve_aspect: bool


@dataclass
class BuildResult:
    paths: PathList = field(default_factory=list)
    kanjivg_chars: list[str] = field(default_factory=list)
    unsupported_chars: list[str] = field(default_factory=list)
    missing_chars: list[str] = field(default_factory=list)


def require_svg_path():
    try:
        from svg.path import parse_path
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "缺少套件 svg.path。請先執行：python -m pip install -r requirements.txt"
        ) from exc

    return parse_path


def bounds(paths: Iterable[Iterable[Point]]) -> tuple[float, float, float, float]:
    points = [point for path in paths for point in path]
    if not points:
        return 0.0, 0.0, 1.0, 1.0

    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    if max_x == min_x:
        max_x += 1.0
    if max_y == min_y:
        max_y += 1.0
    return min_x, min_y, max_x, max_y


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
) -> PathList:
    min_x, min_y, max_x, max_y = bounds(paths)
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

        screen_path = []
        for x, y in decimate(path, point_step):
            sx = origin_x + pad_x + (x - min_x) * scale_x
            if flip_y:
                sy = origin_y + box_height - (pad_y + (y - min_y) * scale_y)
            else:
                sy = origin_y + pad_y + (y - min_y) * scale_y
            screen_path.append((sx, sy))
        transformed.append(screen_path)

    return transformed


def kanjivg_file_for_char(char: str, kanjivg_dir: Path) -> Path:
    return kanjivg_dir / f"{ord(char):05x}.svg"


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


def path_sample_count(segment, sample_spacing: float) -> int:
    try:
        segment_length = float(segment.length(error=1e-4))
    except Exception:
        start = segment.point(0)
        end = segment.point(1)
        segment_length = abs(end - start)
    return max(1, int(segment_length / max(sample_spacing, 0.1)))


def sample_svg_path(path_data: str, sample_spacing: float) -> list[Point]:
    parse_path = require_svg_path()
    parsed = parse_path(path_data)
    points: list[Point] = []

    for segment in parsed:
        steps = path_sample_count(segment, sample_spacing)
        for index in range(steps + 1):
            if points and index == 0:
                continue
            point = segment.point(index / steps)
            points.append((float(point.real), float(point.imag)))

    return points


def load_kanjivg_strokes(char: str, kanjivg_dir: Path, sample_spacing: float) -> PathList | None:
    svg_path = kanjivg_file_for_char(char, kanjivg_dir)
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
) -> PathList:
    # KanjiVG already uses SVG/screen-like coordinates: x rightward, y downward.
    return transform_paths(
        strokes,
        origin_x,
        origin_y,
        box_width,
        box_height,
        preserve_aspect,
        flip_y=False,
        point_step=point_step,
    )


def build_paths(
    text: str,
    kanjivg_dir: Path,
    settings: DrawSettings,
) -> BuildResult:
    result = BuildResult()
    cursor_x = settings.start_x
    cursor_y = settings.start_y

    for char in text:
        if char == "\n":
            cursor_x = settings.start_x
            cursor_y += settings.char_height + settings.line_gap
            continue
        if char.isspace():
            cursor_x += settings.char_width + settings.char_gap
            continue

        if not is_japanese_writing_char(char):
            result.unsupported_chars.append(char)
            cursor_x += settings.char_width + settings.char_gap
            continue

        strokes = load_kanjivg_strokes(char, kanjivg_dir, settings.sample_spacing)
        if strokes:
            result.paths.extend(
                transform_kanjivg(
                    strokes,
                    cursor_x,
                    cursor_y,
                    settings.char_width,
                    settings.char_height,
                    settings.preserve_aspect,
                    settings.point_step,
                )
            )
            result.kanjivg_chars.append(char)
        else:
            result.missing_chars.append(char)

        cursor_x += settings.char_width + settings.char_gap

    if result.unsupported_chars or result.missing_chars:
        if result.unsupported_chars:
            unique = "".join(dict.fromkeys(result.unsupported_chars))
            print(f"不支援的非日文書寫字元：{unique}", file=sys.stderr)
        unique = "".join(dict.fromkeys(result.missing_chars))
        if unique:
            print(f"找不到這些字的 KanjiVG 筆順資料：{unique}", file=sys.stderr)
        raise SystemExit("此工具僅支援有 KanjiVG 筆順資料的平假名、片假名與漢字。")

    return result


def path_stats(paths: PathList) -> tuple[int, int]:
    return len(paths), sum(len(path) for path in paths)


def preview_paths(paths: PathList, output: Path) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "缺少套件 matplotlib。請先執行：python -m pip install -r requirements.txt"
        ) from exc

    if not paths:
        raise SystemExit("沒有可預覽的筆跡路徑。")

    min_x, min_y, max_x, max_y = bounds(paths)
    padding = 20

    fig_width = max(4, (max_x - min_x + padding * 2) / 120)
    fig_height = max(3, (max_y - min_y + padding * 2) / 120)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=120)

    for index, path in enumerate(paths, start=1):
        xs = [point[0] for point in path]
        ys = [point[1] for point in path]
        ax.plot(xs, ys, color="black", linewidth=1.4)
        ax.text(xs[0], ys[0], str(index), fontsize=8, color="#b00020")

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
    """Inject uncoalesced absolute mouse events through the Windows API."""

    MOUSEEVENTF_MOVE = 0x0001
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004
    MOUSEEVENTF_MOVE_NOCOALESCE = 0x2000
    MOUSEEVENTF_VIRTUALDESK = 0x4000
    MOUSEEVENTF_ABSOLUTE = 0x8000

    def __init__(self) -> None:
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.send_input = self.user32.SendInput
        self.send_input.argtypes = (
            wintypes.UINT,
            ctypes.POINTER(_Input),
            ctypes.c_int,
        )
        self.send_input.restype = wintypes.UINT

        self.virtual_left = self.user32.GetSystemMetrics(76)
        self.virtual_top = self.user32.GetSystemMetrics(77)
        self.virtual_width = self.user32.GetSystemMetrics(78)
        self.virtual_height = self.user32.GetSystemMetrics(79)
        if self.virtual_width <= 1 or self.virtual_height <= 1:
            raise OSError("無法取得 Windows 虛擬螢幕尺寸。")

    def absolute_coordinates(self, x: int, y: int) -> tuple[int, int]:
        absolute_x = round((x - self.virtual_left) * 65535 / (self.virtual_width - 1))
        absolute_y = round((y - self.virtual_top) * 65535 / (self.virtual_height - 1))
        return absolute_x, absolute_y

    def send(self, flags: int, x: int = 0, y: int = 0) -> None:
        event = _Input(
            type=0,
            data=_InputUnion(
                mi=_MouseInput(
                    dx=x,
                    dy=y,
                    mouseData=0,
                    dwFlags=flags,
                    time=0,
                    dwExtraInfo=0,
                )
            ),
        )
        sent = self.send_input(1, ctypes.byref(event), ctypes.sizeof(_Input))
        if sent != 1:
            error = ctypes.get_last_error()
            raise OSError(error, "Windows SendInput 滑鼠事件傳送失敗。")

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


def validate_screen_bounds(paths: PathList, allow_offscreen: bool) -> None:
    if allow_offscreen:
        return

    try:
        import pyautogui
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "缺少套件 pyautogui。請先執行：python -m pip install -r requirements.txt"
        ) from exc

    screen_width, screen_height = pyautogui.size()
    offscreen = [
        (x, y)
        for path in paths
        for x, y in path
        if x < 0 or y < 0 or x >= screen_width or y >= screen_height
    ]
    if offscreen:
        sample_x, sample_y = offscreen[0]
        raise SystemExit(
            "有筆跡座標超出螢幕範圍："
            f"({sample_x:.0f}, {sample_y:.0f})，螢幕大小 {screen_width}x{screen_height}。"
            "請調整 --start-x、--start-y、--char-width、--char-height，"
            "或確認後加上 --allow-offscreen。"
        )


def draw_with_mouse(
    paths: PathList,
    countdown: int,
    move_duration: float,
    point_delay: float,
    stroke_delay: float,
    allow_offscreen: bool,
) -> None:
    try:
        import pyautogui
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "缺少套件 pyautogui。請先執行：python -m pip install -r requirements.txt"
        ) from exc

    validate_screen_bounds(paths, allow_offscreen)

    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0
    move_duration = max(0.0, move_duration)
    point_delay = max(0.0, point_delay)
    stroke_delay = max(0.0, stroke_delay)
    windows_mouse = WindowsSendInputMouse() if sys.platform == "win32" else None

    if windows_mouse:
        print("滑鼠輸入：Windows SendInput（已禁止合併移動事件）")
    else:
        print("滑鼠輸入：PyAutoGUI")

    def check_failsafe() -> None:
        if pyautogui.position() in pyautogui.FAILSAFE_POINTS:
            raise pyautogui.FailSafeException("滑鼠已移到安全停止角落，書寫已中止。")

    def move_to_sample(x: float, y: float) -> None:
        check_failsafe()
        if windows_mouse:
            windows_mouse.move_to(round(x), round(y))
            if move_duration:
                time.sleep(move_duration)
            return

        if move_duration >= pyautogui.MINIMUM_DURATION:
            pyautogui.moveTo(round(x), round(y), duration=move_duration)
            return

        # PyAutoGUI ignores sub-threshold durations. Send the point immediately,
        # then wait explicitly so Windows does not merge the mouse events.
        pyautogui.moveTo(round(x), round(y), duration=0)
        if move_duration:
            time.sleep(move_duration)

    print(f"{countdown} 秒後開始移動滑鼠。請切到畫布並選好鉛筆或筆刷，不要選直線工具。")
    print("緊急停止：把滑鼠快速移到螢幕左上角。")
    for remaining in range(countdown, 0, -1):
        print(remaining)
        time.sleep(1)

    for index, path in enumerate(paths, start=1):
        if len(path) < 2:
            continue
        start_x, start_y = path[0]
        try:
            move_to_sample(start_x, start_y)
            time.sleep(max(stroke_delay, 0.02))
            if windows_mouse:
                windows_mouse.left_down()
            else:
                pyautogui.mouseDown()
            for x, y in path[1:]:
                move_to_sample(x, y)
                if point_delay:
                    time.sleep(point_delay)
        finally:
            if windows_mouse:
                windows_mouse.left_up()
            else:
                pyautogui.mouseUp()

        if stroke_delay:
            time.sleep(stroke_delay)
        if index % 20 == 0:
            print(f"已完成 {index}/{len(paths)} 筆路徑")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="用滑鼠在小畫家或相似畫布程式中依筆順書寫日文假名與漢字。"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {APP_VERSION}")
    parser.add_argument("--text", default="こんにちは", help="要寫的日文文字，可包含平假名、片假名、漢字與換行。")
    parser.add_argument("--kanjivg-dir", default=str(DEFAULT_KANJIVG_DIR), help="KanjiVG kanji SVG 資料夾。")
    parser.add_argument("--start-x", type=float, default=877, help="第一個字左上角的螢幕 X 座標。")
    parser.add_argument("--start-y", type=float, default=325, help="第一個字左上角的螢幕 Y 座標。")
    parser.add_argument("--char-width", type=float, default=150, help="每個字的寬度，單位像素。")
    parser.add_argument("--char-height", type=float, default=150, help="每個字的高度，單位像素。")
    parser.add_argument("--char-gap", type=float, default=12, help="字與字之間的間距，單位像素。")
    parser.add_argument("--line-gap", type=float, default=24, help="換行間距，單位像素。")
    parser.add_argument("--point-step", type=int, default=1, help="每隔幾個點取樣一次；1 最細但最慢。")
    parser.add_argument("--sample-spacing", type=float, default=2.0, help="KanjiVG 曲線取樣間距；越小越細但越慢。")
    parser.add_argument("--no-preserve-aspect", action="store_true", help="允許字形拉伸填滿設定寬高。")
    parser.add_argument("--preview", nargs="?", const="preview.png", help="輸出筆跡預覽圖，不移動滑鼠。")
    parser.add_argument("--execute", action="store_true", help="真的移動滑鼠開始書寫。")
    parser.add_argument("--countdown", type=int, default=5, help="開始前倒數秒數。")
    parser.add_argument("--move-duration", type=float, default=0.0, help="每個取樣點的移動時間。太快漏畫可調高。")
    parser.add_argument("--point-delay", type=float, default=0.008, help="每個取樣點送出後的停頓秒數。")
    parser.add_argument("--stroke-delay", type=float, default=0.03, help="每條筆畫之間的停頓秒數。")
    parser.add_argument("--allow-offscreen", action="store_true", help="允許座標超出螢幕範圍。")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    kanjivg_dir = Path(args.kanjivg_dir)
    settings = DrawSettings(
        start_x=args.start_x,
        start_y=args.start_y,
        char_width=args.char_width,
        char_height=args.char_height,
        char_gap=args.char_gap,
        line_gap=args.line_gap,
        point_step=max(1, args.point_step),
        sample_spacing=max(0.1, args.sample_spacing),
        preserve_aspect=not args.no_preserve_aspect,
    )

    result = build_paths(args.text, kanjivg_dir, settings)
    stroke_count, point_count = path_stats(result.paths)
    print(f"KanjiVG 資料夾：{kanjivg_dir.resolve()}")
    print("筆跡來源：KanjiVG 筆順資料")
    print(f"文字：{args.text}")
    print(f"產生 {stroke_count} 條筆畫路徑、{point_count} 個滑鼠點。")
    print(f"KanjiVG 真筆順字數：{len(result.kanjivg_chars)}")
    if result.kanjivg_chars:
        print(f"KanjiVG：{''.join(result.kanjivg_chars)}")

    if args.preview:
        preview_output = Path(args.preview)
        preview_paths(result.paths, preview_output)
        print(f"已輸出預覽圖：{preview_output.resolve()}")

    if args.execute:
        draw_with_mouse(
            result.paths,
            countdown=args.countdown,
            move_duration=args.move_duration,
            point_delay=args.point_delay,
            stroke_delay=args.stroke_delay,
            allow_offscreen=args.allow_offscreen,
        )
        print("完成。")
    elif not args.preview:
        print("這次沒有移動滑鼠。要實際書寫請加上 --execute；要先看效果請加上 --preview。")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
