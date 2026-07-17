# -*- coding: utf-8 -*-
"""Promote the reviewed full-three-font build artifacts into formal OFL packs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATE_ROOT = ROOT / "build" / "glyph-proof-full-three-fonts"
DEFAULT_OUTPUT_ROOT = ROOT / "data" / "stroke_styles"
PROMOTION_DATE = "2026-07-17"
PATH_COMMAND_RE = re.compile(r"[A-Za-z]")


@dataclass(frozen=True)
class PackSpec:
    id: str
    candidate_id: str
    font_filename: str
    display_order: int
    labels: dict[str, str]
    archive_sha256: str
    generated_glyphs: int
    fallback_glyphs: int


PACKS = (
    PackSpec(
        id="zen-kurenaido",
        candidate_id="zen-kurenaido-complete-kvg-candidate",
        font_filename="ZenKurenaido-Regular.ttf",
        display_order=10,
        labels={
            "zh-Hant": "Zen Kurenaido",
            "zh-Hans": "Zen Kurenaido",
            "ja": "Zen Kurenaido",
            "en": "Zen Kurenaido",
        },
        archive_sha256="c97e1f5efe171dd01df4dd96fb0e7f1eb16d9e36c2a0b1f7f24ec03b87670b83",
        generated_glyphs=6591,
        fallback_glyphs=111,
    ),
    PackSpec(
        id="hachi-maru-pop",
        candidate_id="hachi-maru-pop-complete-kvg-candidate",
        font_filename="HachiMaruPop-Regular.ttf",
        display_order=20,
        labels={
            "zh-Hant": "Hachi Maru Pop",
            "zh-Hans": "Hachi Maru Pop",
            "ja": "Hachi Maru Pop",
            "en": "Hachi Maru Pop",
        },
        archive_sha256="69f92d37a0a3711ccd0cf1ae9d28be02a5246c6f1749cc2a11c453da0b21f065",
        generated_glyphs=6609,
        fallback_glyphs=93,
    ),
    PackSpec(
        id="yomogi",
        candidate_id="yomogi-complete-kvg-candidate",
        font_filename="Yomogi-Regular.ttf",
        display_order=30,
        labels={
            "zh-Hant": "Yomogi",
            "zh-Hans": "Yomogi",
            "ja": "Yomogi",
            "en": "Yomogi",
        },
        archive_sha256="073f83a6f6351f3d1c7400cd4253473a5ec21a22d787ca0fa98156781205812d",
        generated_glyphs=6606,
        fallback_glyphs=96,
    ),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_archive(spec: PackSpec, archive_path: Path) -> None:
    if sha256(archive_path) != spec.archive_sha256:
        raise RuntimeError(f"Candidate archive SHA-256 mismatch: {archive_path}")
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        if len(names) != spec.generated_glyphs or names != sorted(names):
            raise RuntimeError(f"Candidate archive order/count mismatch: {archive_path}")
        for name in names:
            if not re.fullmatch(r"strokes/[0-9a-f]{5}\.svg", name):
                raise RuntimeError(f"Unexpected candidate archive member: {name}")
            root = ET.fromstring(archive.read(name))
            if root.attrib.get("viewBox") != "0 0 109 109":
                raise RuntimeError(f"Unexpected SVG viewBox: {name}")
            paths = [node for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "path"]
            if not paths:
                raise RuntimeError(f"Candidate SVG contains no paths: {name}")
            for node in paths:
                commands = PATH_COMMAND_RE.findall(node.attrib.get("d", ""))
                if not commands or not set(commands) <= {"M", "L"}:
                    raise RuntimeError(f"Candidate SVG is not M/L-only: {name}")


def formal_manifest(spec: PackSpec, candidate: dict, archive_hash: str) -> dict:
    source = dict(candidate["source"])
    source["filename"] = spec.font_filename
    conversion = dict(candidate["conversion"])
    conversion.update({
        "generated_glyphs": spec.generated_glyphs,
        "promotion_converter": "scripts/promote_full_three_font_style_packs.py",
        "promoted_at": PROMOTION_DATE,
        "promoted_from": f"build/glyph-proof-full-three-fonts/{spec.id}",
        "geometry_changed_during_promotion": False,
    })
    return {
        "schema_version": 2,
        "id": spec.id,
        "display_order": spec.display_order,
        "labels": spec.labels,
        "strokes_archive": "strokes.zip",
        "strokes_archive_sha256": archive_hash,
        "fallback_style": "kanjivg",
        "supports_horizontal": True,
        "supports_vertical": True,
        "source": source,
        "license": candidate["license"],
        "conversion": conversion,
        "quality": {
            "status": "formal-with-limited-human-review",
            "catalog_characters": 6702,
            "previously_approved_characters": 821,
            "newly_human_approved_characters": 42,
            "human_approved_characters_total": 863,
            "priority_review_characters": 1300,
            "pending_priority_review_characters": 1258,
            "deferred_path_excess_characters": 165,
            "image_reconstruction_r1_overrides_included": False,
            "runtime_policy": "Use the promoted skeleton when available; only the existing missing-glyph or low-confidence projection rules fall back to KanjiVG.",
            "usage_notice_locations": [
                "localization.py help_content",
                "complete-guide.md",
                "complete-guide.en.md",
                "complete-guide.ja.md",
            ],
        },
    }


def source_record(spec: PackSpec, manifest: dict) -> str:
    source = manifest["source"]
    conversion = manifest["conversion"]
    quality = manifest["quality"]
    return "\n".join((
        f"# {spec.labels['en']} formal centerline style pack",
        "",
        f"- Source font: {source['font_name']}",
        f"- Source version: {source['font_version']}",
        f"- Source repository: {source['repository']}",
        f"- Pinned source commit: `{source['commit']}`",
        f"- Source TTF SHA-256: `{source['sha256']}`",
        f"- Original copyright: {source['copyright']}",
        "- Source and derived centreline license: SIL Open Font License 1.1 (`OFL.txt`)",
        "",
        "## Conversion and promotion record",
        "",
        f"- Target catalog: {conversion['catalog']}, {conversion['catalog_codepoints']} codepoints",
        f"- Font-derived centerline SVGs: {conversion['eligible_glyphs']}",
        f"- Existing manually approved geometry retained: {conversion['approved_prior_glyphs']}",
        f"- Newly generated geometry: {conversion['bulk_generated_glyphs']}",
        f"- Missing source glyphs falling back to KanjiVG: {conversion['fallback_glyphs']}",
        f"- Original converter: `{conversion['converter']}`",
        f"- Formal promotion: `{conversion['promotion_converter']}` on {conversion['promoted_at']}",
        "- Promotion geometry change: none; the candidate `strokes.zip` bytes are preserved exactly",
        f"- Formal archive SHA-256: `{manifest['strokes_archive_sha256']}`",
        "- KanjiVG role: runtime stroke order/direction and fallback only; its geometry is not stored in this OFL archive",
        "",
        "## Quality status",
        "",
        f"- Human-approved catalog characters: {quality['human_approved_characters_total']}",
        f"- Pending priority-review characters: {quality['pending_priority_review_characters']}",
        f"- Deferred path-excess characters: {quality['deferred_path_excess_characters']}",
        "- The 16 image-reconstruction R1 experimental overrides are intentionally excluded",
        "- User-facing limitations are documented in the in-app help and complete guides",
        "- Release status: included in the V2.7.0 release",
        "",
    ))


def validate_candidate(spec: PackSpec, candidate_dir: Path) -> dict:
    manifest_path = candidate_dir / "manifest.json"
    archive_path = candidate_dir / "strokes.zip"
    license_path = candidate_dir / "OFL.txt"
    if not all(path.is_file() for path in (manifest_path, archive_path, license_path)):
        raise RuntimeError(f"Incomplete candidate pack: {candidate_dir}")
    candidate = json.loads(manifest_path.read_text(encoding="utf-8"))
    if candidate.get("id") != spec.candidate_id:
        raise RuntimeError(f"Unexpected candidate id: {candidate_dir}")
    if candidate.get("license", {}).get("id") != "OFL-1.1":
        raise RuntimeError(f"Candidate is not OFL-1.1: {candidate_dir}")
    conversion = candidate.get("conversion", {})
    if conversion.get("eligible_glyphs") != spec.generated_glyphs:
        raise RuntimeError(f"Candidate glyph count mismatch: {candidate_dir}")
    if conversion.get("fallback_glyphs") != spec.fallback_glyphs:
        raise RuntimeError(f"Candidate fallback count mismatch: {candidate_dir}")
    validate_archive(spec, archive_path)
    return candidate


def safe_replace_output(output_root: Path) -> None:
    resolved_root = ROOT.resolve()
    resolved = output_root.resolve()
    if resolved == resolved_root or resolved_root not in resolved.parents:
        raise RuntimeError(f"Refusing to replace output outside workspace: {resolved}")
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True)


def promote(candidate_root: Path, output_root: Path) -> list[dict]:
    candidates = {
        spec.id: validate_candidate(spec, candidate_root / spec.id)
        for spec in PACKS
    }
    safe_replace_output(output_root)
    manifests = []
    for spec in PACKS:
        candidate_dir = candidate_root / spec.id
        pack_dir = output_root / spec.id
        pack_dir.mkdir()
        shutil.copyfile(candidate_dir / "strokes.zip", pack_dir / "strokes.zip")
        shutil.copyfile(candidate_dir / "OFL.txt", pack_dir / "OFL.txt")
        archive_hash = sha256(pack_dir / "strokes.zip")
        manifest = formal_manifest(spec, candidates[spec.id], archive_hash)
        (pack_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        (pack_dir / "SOURCE.md").write_text(
            source_record(spec, manifest), encoding="utf-8", newline="\n"
        )
        manifests.append(manifest)
    return manifests


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-root", type=Path, default=DEFAULT_CANDIDATE_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_ROOT)
    args = parser.parse_args()
    manifests = promote(args.candidate_root, args.output_dir)
    print(json.dumps({"packs": manifests}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
