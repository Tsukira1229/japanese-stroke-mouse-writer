from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class SymbolRecord:
    codepoint: str
    symbol: str
    unicode_name: str
    group: str
    category: str
    cell_span: float
    vertical_mode: str
    drawing_style: str
    expected_strokes: int
    svg: str
    status: str
    batch: str


@dataclass(frozen=True)
class SymbolCatalog:
    records: tuple[SymbolRecord, ...]
    by_group: Mapping[str, frozenset[str]]
    cell_spans: Mapping[str, float]
    vertical_rotating: frozenset[str]

    def group_chars(self, group: str) -> frozenset[str]:
        return self.by_group.get(group, frozenset())


def load_symbol_catalog(path: Path) -> SymbolCatalog:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Unable to load symbol manifest: {path}") from exc
    if payload.get("schema_version") != 1 or not isinstance(payload.get("symbols"), list):
        raise RuntimeError(f"Unsupported symbol manifest schema: {path}")

    records: list[SymbolRecord] = []
    groups: dict[str, set[str]] = {}
    cell_spans: dict[str, float] = {}
    vertical_rotating: set[str] = set()
    seen: set[str] = set()
    for raw in payload["symbols"]:
        try:
            record = SymbolRecord(
                codepoint=str(raw["codepoint"]),
                symbol=str(raw["symbol"]),
                unicode_name=str(raw["unicode_name"]),
                group=str(raw["group"]),
                category=str(raw["category"]),
                cell_span=float(raw["cell_span"]),
                vertical_mode=str(raw["vertical_mode"]),
                drawing_style=str(raw["drawing_style"]),
                expected_strokes=int(raw["expected_strokes"]),
                svg=str(raw["svg"]),
                status=str(raw["status"]),
                batch=str(raw["batch"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise RuntimeError(f"Invalid symbol record in {path}") from exc
        if len(record.symbol) != 1 or record.codepoint != f"U+{ord(record.symbol):04X}":
            raise RuntimeError(f"Invalid symbol/codepoint pair in {path}: {record.symbol!r}")
        if record.symbol in seen:
            raise RuntimeError(f"Duplicate symbol in {path}: {record.codepoint}")
        if record.cell_span not in {0.5, 1.0}:
            raise RuntimeError(f"Invalid cell span in {path}: {record.codepoint}")
        seen.add(record.symbol)
        records.append(record)
        groups.setdefault(record.group, set()).add(record.symbol)
        cell_spans[record.symbol] = record.cell_span
        if record.vertical_mode == "rotate":
            vertical_rotating.add(record.symbol)

    return SymbolCatalog(
        records=tuple(records),
        by_group=MappingProxyType({group: frozenset(chars) for group, chars in groups.items()}),
        cell_spans=MappingProxyType(cell_spans),
        vertical_rotating=frozenset(vertical_rotating),
    )
