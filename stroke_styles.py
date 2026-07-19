# -*- coding: utf-8 -*-
"""Discover bundled direct-centreline writing styles."""

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
    order_archive: Path | None
    strokes_archive_sha256: str | None
    order_archive_sha256: str | None
    order_maps: int
    source_name: str
    license_id: str
    generated_glyphs: int
    display_order: int
    runtime_mode: str
    view_box: tuple[float, float, float, float] | None
    fallback_style: str | None
    fallback_codepoints: frozenset[int]
    style_only_codepoints: frozenset[int]

    def label(self, language: Language) -> str:
        return self.labels.get(language.value) or self.labels.get("en") or self.id


def _default_style() -> StrokeStyle:
    return StrokeStyle(
        id=DEFAULT_STROKE_STYLE_ID,
        labels={
            "zh-Hant": "KanjiVG (預設)",
            "zh-Hans": "KanjiVG (默认)",
            "ja": "KanjiVG (既定)",
            "en": "KanjiVG (Default)",
        },
        strokes_dir=None,
        strokes_archive=None,
        order_archive=None,
        strokes_archive_sha256=None,
        order_archive_sha256=None,
        order_maps=0,
        source_name="KanjiVG",
        license_id="CC-BY-SA-3.0",
        generated_glyphs=0,
        display_order=0,
        runtime_mode="base",
        view_box=None,
        fallback_style=None,
        fallback_codepoints=frozenset(),
        style_only_codepoints=frozenset(),
    )


def _parse_view_box(value: object) -> tuple[float, float, float, float]:
    parts = [float(part) for part in str(value).split()]
    if len(parts) != 4 or parts[2] <= parts[0] or parts[3] <= parts[1]:
        raise ValueError("invalid style view box")
    return parts[0], parts[1], parts[2], parts[3]


def _fallback_codepoints(manifest_path: Path, payload: dict[str, object]) -> frozenset[int]:
    filename = str(payload.get("fallback_codepoints_file", ""))
    if not filename:
        return frozenset()
    rows = json.loads((manifest_path.parent / filename).read_text(encoding="utf-8"))
    return frozenset(int(str(row["codepoint"])[2:], 16) for row in rows)


def discover_stroke_styles(bundle_dir: Path) -> tuple[StrokeStyle, ...]:
    styles = [_default_style()]
    root = bundle_dir / "data" / "stroke_styles"
    if not root.is_dir():
        return tuple(styles)
    for manifest_path in sorted(root.glob("*/manifest.json")):
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            style_id = str(payload["id"])
            if style_id == DEFAULT_STROKE_STYLE_ID or payload.get("runtime_mode") != "direct":
                continue
            strokes_dir = manifest_path.parent / str(payload.get("strokes_dir", "strokes"))
            strokes_archive = manifest_path.parent / str(payload.get("strokes_archive", "strokes.zip"))
            order_payload = dict(payload.get("drawing_order", {}))
            order_archive = manifest_path.parent / str(order_payload.get("archive", "orders.zip"))
            if not strokes_dir.is_dir() and not strokes_archive.is_file():
                continue
            conversion = dict(payload["conversion"])
            styles.append(StrokeStyle(
                id=style_id,
                labels={str(key): str(value) for key, value in dict(payload["labels"]).items()},
                strokes_dir=strokes_dir if strokes_dir.is_dir() else None,
                strokes_archive=strokes_archive if strokes_archive.is_file() else None,
                order_archive=order_archive if order_archive.is_file() else None,
                strokes_archive_sha256=str(payload.get("strokes_archive_sha256", "")) or None,
                order_archive_sha256=str(order_payload.get("sha256", "")) or None,
                order_maps=int(order_payload.get("eligible_maps", 0)),
                source_name=str(dict(payload["source"])["font_name"]),
                license_id=str(dict(payload["license"])["id"]),
                generated_glyphs=int(conversion["eligible_glyphs"]),
                display_order=int(payload.get("display_order", 100)),
                runtime_mode="direct",
                view_box=_parse_view_box(payload["view_box"]),
                fallback_style=str(payload.get("fallback_style", DEFAULT_STROKE_STYLE_ID)),
                fallback_codepoints=_fallback_codepoints(manifest_path, payload),
                style_only_codepoints=frozenset(
                    int(str(codepoint)[2:], 16)
                    for codepoint in conversion.get("style_only_codepoints", [])
                ),
            ))
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            continue
    return tuple(sorted(styles, key=lambda style: (style.display_order, style.id)))


def style_by_id(bundle_dir: Path, style_id: str) -> StrokeStyle:
    return next((style for style in discover_stroke_styles(bundle_dir) if style.id == style_id), _default_style())


def normalize_stroke_style_id(bundle_dir: Path, style_id: str) -> str:
    return style_by_id(bundle_dir, style_id).id
