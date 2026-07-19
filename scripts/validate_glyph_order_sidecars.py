# -*- coding: utf-8 -*-
"""Validate all formal drawing-order sidecars against their frozen SVG archives."""

from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from stroke_order import ordered_source_paths  # noqa: E402
from promote_glyph_order_sidecars import SIDECARS  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    results = []
    for config in SIDECARS:
        pack = ROOT / "data" / "stroke_styles" / config.style_id
        source_path = pack / "strokes.zip"
        order_path = pack / "orders.zip"
        manifest = json.loads((pack / "manifest.json").read_text(encoding="utf-8"))
        order_manifest = manifest["drawing_order"]
        if sha256(source_path) != config.source_sha256 or sha256(order_path) != config.archive_sha256:
            raise RuntimeError(f"Formal archive hash mismatch: {config.style_id}")
        if (
            order_manifest["sha256"] != config.archive_sha256
            or order_manifest["eligible_maps"] != config.eligible_maps
            or order_manifest["authoritative_japanese_stroke_order"] is not False
        ):
            raise RuntimeError(f"Drawing-order manifest mismatch: {config.style_id}")
        with zipfile.ZipFile(source_path) as source, zipfile.ZipFile(order_path) as orders:
            names = orders.namelist()
            if len(names) != config.eligible_maps or names != sorted(names):
                raise RuntimeError(f"Drawing-order member mismatch: {config.style_id}")
            for index, name in enumerate(names, 1):
                codepoint = int(Path(name).stem, 16)
                svg_data = source.read(f"strokes/{codepoint:05x}.svg")
                ordered_source_paths(
                    svg_data,
                    orders.read(name),
                    character=chr(codepoint),
                    style_id=config.style_id,
                    source_archive_sha256=config.source_sha256,
                )
                if index % 1000 == 0:
                    print(f"validated {config.style_id}: {index}/{len(names)}", flush=True)
        results.append({"style": config.style_id, "order_maps": config.eligible_maps, "sha256": config.archive_sha256})
    print(json.dumps({"drawing_order_sidecars": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
