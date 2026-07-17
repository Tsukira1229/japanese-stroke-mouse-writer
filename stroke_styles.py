# -*- coding: utf-8 -*-
"""Discover bundled centerline stroke-style packs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from localization import Language


DEFAULT_STROKE_STYLE_ID = "kanjivg"


@dataclass(frozen=True)
class StrokeStyle:
    id: str
    labels: dict[str, str]
    strokes_dir: Path | None
    strokes_archive: Path | None
    source_name: str
    license_id: str
    generated_glyphs: int
    display_order: int

    def label(self, language: Language) -> str:
        return self.labels.get(language.value) or self.labels.get("en") or self.id


def _default_style() -> StrokeStyle:
    return StrokeStyle(
        id=DEFAULT_STROKE_STYLE_ID,
        labels={
            "zh-Hant": "KanjiVG 原始筆跡",
            "zh-Hans": "KanjiVG 原始笔迹",
            "ja": "KanjiVG オリジナル",
            "en": "KanjiVG Original",
        },
        strokes_dir=None,
        strokes_archive=None,
        source_name="KanjiVG",
        license_id="CC-BY-SA-3.0",
        generated_glyphs=0,
        display_order=0,
    )


def discover_stroke_styles(bundle_dir: Path) -> tuple[StrokeStyle, ...]:
    styles = [_default_style()]
    root = bundle_dir / "data" / "stroke_styles"
    if not root.is_dir():
        return tuple(styles)
    for manifest_path in sorted(root.glob("*/manifest.json")):
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            style_id = str(payload["id"])
            if style_id == DEFAULT_STROKE_STYLE_ID:
                continue
            strokes_dir = manifest_path.parent / str(payload.get("strokes_dir", "strokes"))
            strokes_archive = manifest_path.parent / str(payload.get("strokes_archive", "strokes.zip"))
            if not strokes_dir.is_dir() and not strokes_archive.is_file():
                continue
            styles.append(
                StrokeStyle(
                    id=style_id,
                    labels={str(key): str(value) for key, value in dict(payload["labels"]).items()},
                    strokes_dir=strokes_dir if strokes_dir.is_dir() else None,
                    strokes_archive=strokes_archive if strokes_archive.is_file() else None,
                    source_name=str(payload["source"]["font_name"]),
                    license_id=str(payload["license"]["id"]),
                    generated_glyphs=int(payload["conversion"]["generated_glyphs"]),
                    display_order=int(payload.get("display_order", 100)),
                )
            )
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            continue
    return tuple(sorted(styles, key=lambda style: (style.display_order, style.id)))


def style_by_id(bundle_dir: Path, style_id: str) -> StrokeStyle:
    return next(
        (style for style in discover_stroke_styles(bundle_dir) if style.id == style_id),
        _default_style(),
    )


def normalize_stroke_style_id(bundle_dir: Path, style_id: str) -> str:
    return style_by_id(bundle_dir, style_id).id
