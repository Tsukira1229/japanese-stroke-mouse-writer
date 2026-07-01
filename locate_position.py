# -*- coding: utf-8 -*-
"""Print or capture the current mouse position for canvas calibration."""

from __future__ import annotations

import argparse
import sys
import time


def configure_console_encoding() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


configure_console_encoding()


def require_pyautogui():
    try:
        import pyautogui
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "缺少套件 pyautogui。請先執行：python -m pip install -r requirements.txt"
        ) from exc
    return pyautogui


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="取得目前滑鼠座標。")
    parser.add_argument("--interval", type=float, default=0.25, help="連續顯示座標的更新間隔秒數。")
    parser.add_argument("--snapshot-after", type=int, default=0, help="倒數幾秒後只輸出一次座標。")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pyautogui = require_pyautogui()

    if args.snapshot_after > 0:
        print(f"{args.snapshot_after} 秒後讀取滑鼠座標，請把滑鼠移到畫布起點。")
        for remaining in range(args.snapshot_after, 0, -1):
            print(remaining)
            time.sleep(1)
        print(pyautogui.position())
        return 0

    print("連續顯示滑鼠座標。按 Ctrl+C 結束。")
    try:
        while True:
            print(pyautogui.position())
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n結束。")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
