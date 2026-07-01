# -*- coding: utf-8 -*-
"""Download and install KanjiVG stroke-order SVG data."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

KANJIVG_VERSION = "20250816"
KANJIVG_TAG = f"r{KANJIVG_VERSION}"
KANJIVG_ZIP_NAME = f"kanjivg-{KANJIVG_VERSION}-main.zip"
KANJIVG_URL = (
    f"https://github.com/KanjiVG/kanjivg/releases/download/{KANJIVG_TAG}/{KANJIVG_ZIP_NAME}"
)
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_BASE_DIR = SCRIPT_DIR / "data/kanjivg" / KANJIVG_VERSION


def configure_console_encoding() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


configure_console_encoding()


def download_file(url: str, destination: Path, force: bool) -> None:
    if destination.exists() and not force:
        print(f"已存在下載檔：{destination}")
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    print(f"下載 KanjiVG：{url}")
    with urllib.request.urlopen(url) as response, destination.open("wb") as output:
        shutil.copyfileobj(response, output)
    print(f"已下載：{destination}")


def verify_zip(zip_path: Path) -> None:
    print("驗證 zip 完整性...")
    with zipfile.ZipFile(zip_path) as archive:
        bad_file = archive.testzip()
    if bad_file:
        raise SystemExit(f"KanjiVG zip 驗證失敗：{bad_file}")
    print("zip 驗證通過。")


def install_zip(zip_path: Path, install_dir: Path, force: bool) -> Path:
    if install_dir.exists() and force:
        shutil.rmtree(install_dir)
    install_dir.mkdir(parents=True, exist_ok=True)

    print(f"解壓縮到：{install_dir}")
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(install_dir)

    kanji_dir = install_dir / "kanji"
    if kanji_dir.exists():
        return kanji_dir

    candidates = [path for path in install_dir.rglob("kanji") if path.is_dir()]
    if not candidates:
        raise SystemExit("解壓後找不到 KanjiVG kanji 資料夾。")

    source_kanji_dir = candidates[0]
    print(f"整理 kanji 資料夾：{source_kanji_dir} -> {kanji_dir}")
    if kanji_dir.exists():
        shutil.rmtree(kanji_dir)
    shutil.move(str(source_kanji_dir), str(kanji_dir))
    return kanji_dir


def write_metadata(base_dir: Path, kanji_dir: Path) -> None:
    metadata = {
        "source": "KanjiVG",
        "website": "https://kanjivg.tagaini.net/",
        "repository": "https://github.com/KanjiVG/kanjivg",
        "version": KANJIVG_VERSION,
        "tag": KANJIVG_TAG,
        "download_url": KANJIVG_URL,
        "kanji_dir": str(kanji_dir),
        "license": "Creative Commons Attribution-Share Alike 3.0",
        "installed_at": datetime.now(timezone.utc).isoformat(),
    }
    metadata_path = base_dir / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已寫入 metadata：{metadata_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="下載並安裝 KanjiVG 筆順 SVG 資料。")
    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR), help="KanjiVG 版本資料根目錄。")
    parser.add_argument("--force", action="store_true", help="重新下載並覆蓋已解壓資料。")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base_dir = Path(args.base_dir)
    zip_path = base_dir / KANJIVG_ZIP_NAME
    install_dir = base_dir / "main"

    download_file(KANJIVG_URL, zip_path, args.force)
    verify_zip(zip_path)
    kanji_dir = install_zip(zip_path, install_dir, args.force)

    sample = kanji_dir / "065e5.svg"
    if not sample.exists():
        raise SystemExit(f"安裝後找不到測試檔：{sample}")

    write_metadata(base_dir, kanji_dir)
    zip_path.unlink(missing_ok=True)
    print(f"已刪除安裝壓縮檔：{zip_path}")
    print(f"KanjiVG 安裝完成。測試檔存在：{sample}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
