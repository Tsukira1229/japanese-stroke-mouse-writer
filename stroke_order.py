# -*- coding: utf-8 -*-
"""Validate and apply best-effort drawing-order sidecars to direct SVG paths."""

from __future__ import annotations

import hashlib
import json
import math
import xml.etree.ElementTree as ET
from collections import Counter

from svg.path import Line, Move, parse_path


Point = tuple[float, float]
PathList = list[list[Point]]


class StrokeOrderSidecarError(ValueError):
    pass


def _point(value: complex) -> Point:
    return float(value.real), float(value.imag)


def direct_svg_source_paths(svg_data: bytes) -> PathList:
    """Return the original M/L vertices without adding or moving points."""
    try:
        root = ET.fromstring(svg_data)
    except ET.ParseError as exc:
        raise StrokeOrderSidecarError("invalid direct SVG") from exc
    result: PathList = []
    for element in root.iter():
        if not element.tag.endswith("path"):
            continue
        path_data = element.attrib.get("d", "")
        if not path_data:
            raise StrokeOrderSidecarError("empty direct path")
        points: list[Point] = []
        try:
            segments = parse_path(path_data)
        except Exception as exc:
            raise StrokeOrderSidecarError("invalid direct path") from exc
        for segment in segments:
            if isinstance(segment, Move):
                if points:
                    raise StrokeOrderSidecarError("multiple subpaths in one direct path")
                points.append(_point(segment.end))
                continue
            if not isinstance(segment, Line):
                raise StrokeOrderSidecarError("direct path is not M/L-only")
            start = _point(segment.start)
            end = _point(segment.end)
            if not points:
                points.append(start)
            elif points[-1] != start:
                raise StrokeOrderSidecarError("disconnected direct path")
            if end == points[-1]:
                raise StrokeOrderSidecarError("zero-length direct edge")
            points.append(end)
        if len(points) < 2:
            raise StrokeOrderSidecarError("direct path has no drawable edge")
        result.append(points)
    if not result:
        raise StrokeOrderSidecarError("direct SVG has no paths")
    return result


def ordered_source_paths(
    svg_data: bytes,
    order_data: bytes,
    *,
    character: str,
    style_id: str,
    source_archive_sha256: str,
) -> PathList:
    """Apply a sidecar while proving that every frozen source edge is used once."""
    try:
        payload = json.loads(order_data)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StrokeOrderSidecarError("invalid order sidecar JSON") from exc
    if not isinstance(payload, dict):
        raise StrokeOrderSidecarError("invalid order sidecar payload")
    if (
        payload.get("schema_version") != 1
        or payload.get("character") != character
        or payload.get("codepoint") != f"U+{ord(character):04X}"
        or payload.get("source_style") != style_id
        or payload.get("source_archive_sha256") != source_archive_sha256
        or payload.get("source_svg_sha256") != hashlib.sha256(svg_data).hexdigest()
        or payload.get("path_semantics") != "visual-centerline"
        or payload.get("order_semantics") != "kanjivg-guided"
    ):
        raise StrokeOrderSidecarError("order sidecar source contract mismatch")

    source_paths = direct_svg_source_paths(svg_data)
    source_rows = payload.get("source_paths")
    if not isinstance(source_rows, list) or len(source_rows) != len(source_paths):
        raise StrokeOrderSidecarError("order sidecar source path count mismatch")
    for index, (row, points) in enumerate(zip(source_rows, source_paths), 1):
        if not isinstance(row, dict) or row.get("index") != index or row.get("point_count") != len(points):
            raise StrokeOrderSidecarError("order sidecar source path metadata mismatch")

    expected = Counter(
        (path_index, edge_index)
        for path_index, points in enumerate(source_paths, 1)
        for edge_index in range(len(points) - 1)
    )
    actual: Counter[tuple[int, int]] = Counter()
    ordered: PathList = []
    logical_rows = payload.get("logical_strokes")
    if not isinstance(logical_rows, list):
        raise StrokeOrderSidecarError("order sidecar logical strokes are missing")
    logical_indices: list[int] = []
    for logical in logical_rows:
        if not isinstance(logical, dict) or not isinstance(logical.get("segments"), list):
            raise StrokeOrderSidecarError("invalid logical stroke")
        logical_indices.append(int(logical.get("logical_stroke_index", -1)))
        for segment in logical["segments"]:
            if not isinstance(segment, dict):
                raise StrokeOrderSidecarError("invalid physical segment")
            path_index = int(segment.get("source_path_index", 0))
            start = int(segment.get("from_point_index", -1))
            end = int(segment.get("to_point_index", -1))
            if not 1 <= path_index <= len(source_paths):
                raise StrokeOrderSidecarError("physical segment path index is out of range")
            points = source_paths[path_index - 1]
            if not 0 <= start < end < len(points) or int(segment.get("edge_count", -1)) != end - start:
                raise StrokeOrderSidecarError("physical segment point range is invalid")
            part = list(points[start:end + 1])
            if segment.get("reverse") is True:
                part.reverse()
            elif segment.get("reverse") is not False:
                raise StrokeOrderSidecarError("physical segment direction is invalid")
            ordered.append(part)
            for edge_index in range(start, end):
                actual[(path_index, edge_index)] += 1

    if logical_indices != list(range(1, len(logical_indices) + 1)) or actual != expected or not ordered:
        raise StrokeOrderSidecarError("order sidecar does not cover every source edge exactly once")
    metrics = payload.get("metrics")
    if not isinstance(metrics, dict) or (
        metrics.get("source_edges") != sum(expected.values())
        or metrics.get("missing_edges") != 0
        or metrics.get("duplicate_edges") != 0
    ):
        raise StrokeOrderSidecarError("order sidecar metrics mismatch")
    return ordered


def sample_polylines(paths: PathList, sample_spacing: float) -> PathList:
    """Sample M/L polylines with the same per-edge spacing rule as the SVG loader."""
    spacing = max(sample_spacing, 0.1)
    sampled_paths: PathList = []
    for source in paths:
        sampled: list[Point] = []
        for start, end in zip(source, source[1:]):
            steps = max(1, int(math.dist(start, end) / spacing))
            for index in range(steps + 1):
                if sampled and index == 0:
                    continue
                ratio = index / steps
                sampled.append((
                    start[0] + (end[0] - start[0]) * ratio,
                    start[1] + (end[1] - start[1]) * ratio,
                ))
        if len(sampled) >= 2:
            sampled_paths.append(sampled)
    return sampled_paths
