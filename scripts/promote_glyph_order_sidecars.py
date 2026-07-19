# -*- coding: utf-8 -*-
"""Promote the three approved best-effort drawing-order sidecars."""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class SidecarConfig:
    style_id: str
    source_sha256: str
    archive_sha256: str
    eligible_maps: int
    missing_kvg_strokes: int


SIDECARS = (
    SidecarConfig(
        "yomogi",
        "64969ec274424e3f0f2a9cce9208c1a7d5102f878ebf4ce1c4cd31cdabec40c6",
        "cd1f778ff2793c737d3b0908976dddfa95a7d9bb991b345eb44e21ac1bfec331",
        6606,
        0,
    ),
    SidecarConfig(
        "zen-kurenaido",
        "be8bc959480909f88a203f817ba546314ec49b4b9282d6252885923413c0b3c5",
        "209caf2a443060b4fd5c4d4107f4004c1810f138cb2087e349c117101d895fe1",
        6591,
        0,
    ),
    SidecarConfig(
        "hachi-maru-pop",
        "f532cad5a310239553db7252e0abaeaed4fcbd7df116e477948e6709027e223e",
        "bafada4c7571940c771a55a0af30ef708df143b745c9dc2b99f1e91edf927b94",
        6608,
        2,
    ),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    for config in SIDECARS:
        source = ROOT / "data" / "stroke_styles" / config.style_id / "strokes.zip"
        candidate = ROOT / "build" / f"glyph-proof-{config.style_id}-order-sidecar-full" / "orders-all-candidates.zip"
        destination = source.parent / "orders.zip"
        manifest_path = source.parent / "manifest.json"
        if sha256(source) != config.source_sha256:
            raise RuntimeError(f"Source style archive drift: {config.style_id}")
        if sha256(candidate) != config.archive_sha256:
            raise RuntimeError(f"Approved order archive drift: {config.style_id}")
        with zipfile.ZipFile(candidate) as archive:
            names = archive.namelist()
            if len(names) != config.eligible_maps or names != sorted(names) or len(set(names)) != len(names):
                raise RuntimeError(f"Order archive member drift: {config.style_id}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("strokes_archive_sha256") != config.source_sha256:
            raise RuntimeError(f"Manifest source hash drift: {config.style_id}")
        manifest["drawing_order"] = {
            "archive": "orders.zip",
            "sha256": config.archive_sha256,
            "eligible_maps": config.eligible_maps,
            "semantics": "best-effort-kanjivg-guided",
            "authoritative_japanese_stroke_order": False,
            "missing_kvg_strokes": config.missing_kvg_strokes,
            "geometry_contract": (
                "frozen M/L points; each source edge used exactly once; "
                "reorder, reverse, and split at existing points only"
            ),
            "fallback": "original direct SVG path order",
        }
        shutil.copyfile(candidate, destination)
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(f"promoted {config.style_id}: {config.eligible_maps} best-effort order maps")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
