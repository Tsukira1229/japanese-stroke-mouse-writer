from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from collections import OrderedDict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "data" / "symbol_manifest.json"
DEFAULT_CANDIDATES = ROOT / "data" / "symbol_candidates.csv"
DEFAULT_DOCUMENT = ROOT / "SUPPORTED_SYMBOLS.md"
ALLOWED_GROUPS = {"emoticon", "common_variant", "box_drawing"}
ALLOWED_STATUSES = {"candidate", "accepted", "in_progress", "verified", "deferred"}
ALLOWED_VERTICAL_MODES = {"preserve", "rotate"}
ALLOWED_DRAWING_STYLES = {"centerline", "filled_approximation"}


def slugify(label: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
    if not slug:
        raise ValueError(f"Category cannot be converted to an id: {label!r}")
    return slug


def svg_stroke_count(path: Path) -> int:
    root = ET.parse(path).getroot()
    return sum(1 for element in root.iter() if element.tag.endswith("path"))


def _existing_emoticon_categories(document: Path, expected: frozenset[str]) -> OrderedDict[str, list[str]]:
    categories: OrderedDict[str, list[str]] = OrderedDict()
    current: str | None = None
    for raw_line in document.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line == "## Unicode Box Drawing (U+2500-U+257F)":
            break
        if line.startswith("## "):
            current = line[3:]
            categories[current] = []
            continue
        if current and line and not line.startswith("#"):
            tokens = line.split()
            if tokens and all(len(token) == 1 for token in tokens):
                categories[current].extend(tokens)
    found = frozenset(char for chars in categories.values() for char in chars)
    if found != expected:
        missing = "".join(sorted(expected - found, key=ord))
        extra = "".join(sorted(found - expected, key=ord))
        raise ValueError(f"Documentation categories do not match emoticon registry; missing={missing!r}, extra={extra!r}")
    return categories


def bootstrap_manifest(output: Path) -> None:
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing manifest: {output}")
    sys.path.insert(0, str(ROOT))
    import mouse_writer_pro as writer

    emoticon_categories = _existing_emoticon_categories(DEFAULT_DOCUMENT, writer.SUPPORTED_EMOTICON_SYMBOLS)
    category_specs: list[dict[str, object]] = []
    category_chars: list[tuple[str, str, str, list[str]]] = []
    for order, (label, chars) in enumerate(emoticon_categories.items(), start=1):
        category_id = slugify(label)
        category_specs.append({"id": category_id, "label": label, "group": "emoticon", "order": order})
        category_chars.append((category_id, label, "emoticon", chars))

    category_specs.extend(
        [
            {
                "id": "unicode-box-drawing",
                "label": "Unicode Box Drawing (U+2500-U+257F)",
                "group": "box_drawing",
                "order": 100,
                "description": "All 128 Unicode Box Drawing characters are supported with direct code-point SVG resources. Light lines use one stroke, heavy lines use three close parallel strokes, and double lines use two separated strokes. Set character gap and line gap to `0 px` when adjacent cells must connect.",
            },
            {
                "id": "common-unicode-symbol-variants",
                "label": "Common Unicode symbol variants",
                "group": "common_variant",
                "order": 110,
                "description": "Each of these 89 characters has its own direct code-point SVG. Filled geometric shapes use an outer boundary plus sparse diagonal hatching. Brackets rotate in vertical layout; arrows preserve their semantic direction.",
            },
        ]
    )
    category_chars.extend(
        [
            ("unicode-box-drawing", "Unicode Box Drawing (U+2500-U+257F)", "box_drawing", sorted(writer.BOX_DRAWING_SYMBOLS, key=ord)),
            ("common-unicode-symbol-variants", "Common Unicode symbol variants", "common_variant", sorted(writer.COMMON_SYMBOL_VARIANTS, key=ord)),
        ]
    )

    filled = frozenset("•♥✦✪●■▪◼◾◆♦▲▼▶◀▴▸▾◂★⭐⭑")
    symbols: list[dict[str, object]] = []
    seen: set[str] = set()
    for category_id, _label, group, chars in category_chars:
        for char in chars:
            if char in seen:
                raise ValueError(f"Duplicate symbol while bootstrapping: U+{ord(char):04X}")
            seen.add(char)
            filename = f"{ord(char):05x}.svg"
            svg_path = ROOT / "data" / "custom_strokes" / filename
            if not svg_path.is_file():
                raise FileNotFoundError(svg_path)
            symbols.append(
                {
                    "codepoint": f"U+{ord(char):04X}",
                    "symbol": char,
                    "unicode_name": unicodedata.name(char, "UNNAMED CHARACTER"),
                    "group": group,
                    "category": category_id,
                    "cell_span": 0.5 if unicodedata.east_asian_width(char) in {"Na", "H"} else 1.0,
                    "vertical_mode": "rotate" if char in writer.VERTICAL_COMMON_BRACKETS else "preserve",
                    "drawing_style": "filled_approximation" if char in filled else "centerline",
                    "expected_strokes": svg_stroke_count(svg_path),
                    "svg": f"data/custom_strokes/{filename}",
                    "status": "verified",
                    "batch": "baseline-v2.6.0",
                }
            )
    expected = writer.SUPPORTED_EMOTICON_SYMBOLS | writer.COMMON_SYMBOL_VARIANTS | writer.BOX_DRAWING_SYMBOLS
    if seen != expected:
        raise ValueError("Bootstrapped symbols do not match the current runtime registry")
    payload = {"schema_version": 1, "catalog_version": writer.APP_VERSION, "categories": category_specs, "symbols": symbols}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(symbols)} symbols to {output}")


def load_manifest(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def sync_stroke_counts(path: Path) -> int:
    payload = load_manifest(path)
    symbols = payload.get("symbols")
    if not isinstance(symbols, list):
        raise ValueError("symbols must be a list")
    changed = 0
    for record in symbols:
        if not isinstance(record, dict) or not isinstance(record.get("svg"), str):
            raise ValueError("symbol records must contain an SVG path")
        svg_path = ROOT / record["svg"]
        count = svg_stroke_count(svg_path)
        if record.get("expected_strokes") != count:
            record["expected_strokes"] = count
            changed += 1
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
    return changed


def validate_manifest(path: Path) -> list[str]:
    payload = load_manifest(path)
    errors: list[str] = []
    if payload.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if not isinstance(payload.get("catalog_version"), str) or not payload.get("catalog_version"):
        errors.append("catalog_version must be a non-empty string")
    categories = payload.get("categories")
    symbols = payload.get("symbols")
    if not isinstance(categories, list) or not isinstance(symbols, list):
        return [*errors, "categories and symbols must be lists"]
    category_ids: set[str] = set()
    for category in categories:
        if not isinstance(category, dict):
            errors.append("category records must be objects")
            continue
        category_id = category.get("id")
        if not isinstance(category_id, str) or not category_id:
            errors.append("category id must be a non-empty string")
        elif category_id in category_ids:
            errors.append(f"duplicate category id: {category_id}")
        else:
            category_ids.add(category_id)
        if category.get("group") not in ALLOWED_GROUPS:
            errors.append(f"invalid category group: {category.get('group')!r}")

    seen_codepoints: set[int] = set()
    seen_svg: set[str] = set()
    for index, record in enumerate(symbols, start=1):
        prefix = f"symbols[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{prefix} must be an object")
            continue
        char = record.get("symbol")
        if not isinstance(char, str) or len(char) != 1:
            errors.append(f"{prefix}.symbol must contain one Unicode code point")
            continue
        codepoint = ord(char)
        if record.get("codepoint") != f"U+{codepoint:04X}":
            errors.append(f"{prefix}.codepoint does not match {char!r}")
        if codepoint in seen_codepoints:
            errors.append(f"duplicate codepoint: U+{codepoint:04X}")
        seen_codepoints.add(codepoint)
        group = record.get("group")
        if group not in ALLOWED_GROUPS:
            errors.append(f"{prefix}.group is invalid")
        if record.get("category") not in category_ids:
            errors.append(f"{prefix}.category is not declared")
        if record.get("cell_span") not in {0.5, 1.0}:
            errors.append(f"{prefix}.cell_span must be 0.5 or 1.0")
        if record.get("vertical_mode") not in ALLOWED_VERTICAL_MODES:
            errors.append(f"{prefix}.vertical_mode is invalid")
        if record.get("drawing_style") not in ALLOWED_DRAWING_STYLES:
            errors.append(f"{prefix}.drawing_style is invalid")
        if record.get("status") not in ALLOWED_STATUSES:
            errors.append(f"{prefix}.status is invalid")
        svg = record.get("svg")
        expected_svg = f"data/custom_strokes/{codepoint:05x}.svg"
        if svg != expected_svg:
            errors.append(f"{prefix}.svg must be {expected_svg}")
            continue
        if svg in seen_svg:
            errors.append(f"duplicate SVG path: {svg}")
        seen_svg.add(svg)
        svg_path = ROOT / svg
        if not svg_path.is_file():
            errors.append(f"missing SVG: {svg}")
            continue
        try:
            root = ET.parse(svg_path).getroot()
            if root.attrib.get("viewBox") != "0 0 109 109":
                errors.append(f"{svg}: viewBox must be 0 0 109 109")
            paths = [element for element in root.iter() if element.tag.endswith("path")]
            if not paths:
                errors.append(f"{svg}: must contain at least one path")
            if record.get("expected_strokes") != len(paths):
                errors.append(f"{svg}: expected_strokes does not match path count")
            expected_ids = [f"custom:{codepoint:05x}-s{i}" for i in range(1, len(paths) + 1)]
            actual_ids = [element.attrib.get("id") for element in paths]
            if actual_ids != expected_ids:
                errors.append(f"{svg}: stroke ids are not continuous")
            for element in paths:
                data = element.attrib.get("d", "")
                if len(re.findall(r"(?<![A-Za-z])M", data)) != 1 or not data.startswith("M"):
                    errors.append(f"{svg}: each path must contain one absolute M command")
                    break
                if any(command not in {"M", "L", "C"} for command in re.findall(r"[A-Za-z]", data)):
                    errors.append(f"{svg}: paths may use only absolute M, L, and C commands")
                    break
                values = [float(value) for value in re.findall(r"-?\d+(?:\.\d+)?", data)]
                if not values or any(value < 0.0 or value > 109.0 for value in values):
                    errors.append(f"{svg}: path coordinates must remain inside 0..109")
                    break
        except (ET.ParseError, ValueError) as exc:
            errors.append(f"{svg}: {exc}")
    return errors


def validate_candidates(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.is_file():
        return [f"missing candidate list: {path}"]
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"symbol", "codepoint", "category", "status", "family", "use_case", "reason", "notes"}
        if set(reader.fieldnames or ()) != required:
            return [f"candidate columns must be: {', '.join(sorted(required))}"]
        seen: set[int] = set()
        for row_number, row in enumerate(reader, start=2):
            symbol = row["symbol"]
            if len(symbol) != 1:
                errors.append(f"candidate row {row_number}: symbol must contain one code point")
                continue
            codepoint = ord(symbol)
            if row["codepoint"] != f"U+{codepoint:04X}":
                errors.append(f"candidate row {row_number}: codepoint mismatch")
            if codepoint in seen:
                errors.append(f"candidate row {row_number}: duplicate codepoint")
            seen.add(codepoint)
            if row["status"] not in ALLOWED_STATUSES:
                errors.append(f"candidate row {row_number}: invalid status")
    return errors


def render_document(manifest: Path, output: Path) -> None:
    payload = load_manifest(manifest)
    categories = sorted(payload["categories"], key=lambda item: int(item["order"]))
    symbols = payload["symbols"]
    by_category: dict[str, list[dict[str, object]]] = {}
    for record in symbols:
        by_category.setdefault(str(record["category"]), []).append(record)
    lines = [
        "# Supported Centerline Symbols",
        "",
        f"V{payload['catalog_version']} supports these centerline symbols for users who want to assemble kaomoji and line drawings manually.",
        "",
        f"Total additional centerline symbols: {len(symbols)}",
        "",
        "This list is generated from `data/symbol_manifest.json`; edit the manifest and run `python scripts/manage_symbol_catalog.py generate-docs`.",
        "For the complete addition and review procedure, see [Special-symbol development workflow](SYMBOL_DEVELOPMENT.md).",
        "",
    ]
    for category in categories:
        records = by_category.get(str(category["id"]), [])
        lines.extend([f"## {category['label']}", ""])
        if category.get("description"):
            lines.extend([str(category["description"]), ""])
        chars = [str(record["symbol"]) for record in records]
        if category["group"] in {"box_drawing", "common_variant"}:
            lines.append("```text")
            for index in range(0, len(chars), 16):
                lines.append("".join(chars[index:index + 16]))
            lines.extend(["```", ""])
        else:
            lines.extend([" ".join(chars), ""])
    lines.extend(
        [
            "## Representative supported kaomoji",
            "",
            "```text",
            "(^O^)",
            "(≧▽≦)",
            "m(_ _)m",
            "(/ω\\)",
            "¯\\_(ツ)_/¯",
            "(╯°□°)╯︵ ┻━┻",
            "ฅ^•ﻌ•^ฅ",
            "(˶ᵔ ᵕ ᵔ˶)",
            "ლ(ಠ益ಠ)ლ",
            "ʕ•ᴥ•ʔ",
            "ᕕ(ᐛ)ᕗ",
            "(ㅠ﹏ㅠ)",
            "ʚ(˶◜ᵕ◝˶)ɞ",
            "⸜(｡˃ ᵕ ˂ )⸝",
            "```",
            "",
            "These symbols are written as normal characters. They do not create a single protected kaomoji run, and they do not use font-dependent drawing. Combining marks, emoji, keycap sequences, ZWJ sequences, and unsupported pictorial symbols are rejected before mouse movement.",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {len(symbols)} symbols to {output}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage the special-symbol source-of-truth manifest.")
    parser.add_argument("command", choices=("bootstrap", "sync-stroke-counts", "validate", "generate-docs"))
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--document", type=Path, default=DEFAULT_DOCUMENT)
    args = parser.parse_args()
    if args.command == "bootstrap":
        bootstrap_manifest(args.manifest)
        return 0
    if args.command == "sync-stroke-counts":
        changed = sync_stroke_counts(args.manifest)
        print(f"Updated stroke counts for {changed} symbols")
    errors = [*validate_manifest(args.manifest), *validate_candidates(args.candidates)]
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    if args.command == "generate-docs":
        render_document(args.manifest, args.document)
    else:
        print(f"Validated {len(load_manifest(args.manifest)['symbols'])} symbols")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
