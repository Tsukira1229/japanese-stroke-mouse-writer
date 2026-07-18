# -*- coding: utf-8 -*-
"""Deterministic Yomogi outline-to-centreline conversion helpers."""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt, label
from scipy.spatial import cKDTree
from skimage.morphology import skeletonize


SCALE = 4
GRID = 109
CANVAS = GRID * SCALE
FONT_SIZE = 436
PRUNE_LENGTH = 2.5
RDP_TOLERANCE = 0.75
MIN_PATH_LENGTH = 3.0
SOURCE_NEIGHBOURHOOD = 0.5

Point = tuple[float, float]
PathList = list[list[Point]]


def polyline_length(points: list[Point]) -> float:
    return sum(math.dist(a, b) for a, b in zip(points, points[1:]))


def build_graph(mask: np.ndarray) -> dict[tuple[int, int], set[tuple[int, int]]]:
    pixels = {tuple(point) for point in np.argwhere(mask)}
    graph = {point: set() for point in pixels}
    for y, x in pixels:
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if not (dy or dx):
                    continue
                neighbour = (y + dy, x + dx)
                if neighbour not in pixels:
                    continue
                if dy and dx and ((y + dy, x) in pixels or (y, x + dx) in pixels):
                    continue
                graph[(y, x)].add(neighbour)
    return graph


def prune_spurs(mask: np.ndarray, max_length: float = PRUNE_LENGTH) -> np.ndarray:
    result = mask.copy()
    limit = max_length * SCALE
    while True:
        graph = build_graph(result)
        removed: set[tuple[int, int]] = set()
        for start, neighbours in graph.items():
            if len(neighbours) != 1:
                continue
            path = [start]
            previous = None
            current = start
            length = 0.0
            while True:
                candidates = [point for point in graph[current] if point != previous]
                if not candidates:
                    break
                following = candidates[0]
                length += math.dist(current, following)
                previous, current = current, following
                if len(graph[current]) != 2:
                    break
                path.append(current)
            if len(graph.get(current, ())) > 2 and length <= limit:
                removed.update(path)
        if not removed:
            return result
        for y, x in removed:
            result[y, x] = False


def render_source_mask(font: ImageFont.FreeTypeFont, char: str) -> np.ndarray:
    canvas = Image.new("L", (CANVAS, CANVAS), 0)
    ImageDraw.Draw(canvas).text((CANVAS / 2, 200), char, font=font, fill=255, anchor="mm")
    return np.asarray(canvas) >= 128


def skeleton_for_mask(source_mask: np.ndarray) -> np.ndarray:
    return prune_spurs(skeletonize(source_mask), PRUNE_LENGTH)


def abstract_edges(mask: np.ndarray):
    graph = build_graph(mask)
    junctions = {point for point, neighbours in graph.items() if len(neighbours) > 2}
    nodes: dict[int, set[tuple[int, int]]] = {}
    if junctions:
        junction_mask = np.zeros(mask.shape, dtype=np.uint8)
        for point in junctions:
            junction_mask[point] = 1
        labels, count = label(junction_mask, structure=np.ones((3, 3), dtype=int))
        for index in range(1, count + 1):
            pixels = {tuple(point) for point in np.argwhere(labels == index)}
            nodes[len(nodes)] = pixels
    for point, neighbours in graph.items():
        if len(neighbours) <= 1:
            nodes[len(nodes)] = {point}
    node_of = {point: node_id for node_id, pixels in nodes.items() for point in pixels}
    centres = {
        node_id: (
            sum(point[0] for point in pixels) / len(pixels),
            sum(point[1] for point in pixels) / len(pixels),
        )
        for node_id, pixels in nodes.items()
    }
    visited: set[frozenset[tuple[int, int]]] = set()
    edges = []

    def mark(a, b) -> None:
        visited.add(frozenset((a, b)))

    for node_id, pixels in nodes.items():
        for point in pixels:
            for neighbour in graph[point]:
                if node_of.get(neighbour) == node_id or frozenset((point, neighbour)) in visited:
                    continue
                chain = [centres[node_id], neighbour]
                mark(point, neighbour)
                previous, current = point, neighbour
                end = None
                while True:
                    if current in node_of:
                        end = node_of[current]
                        chain[-1] = centres[end]
                        break
                    candidates = [
                        candidate for candidate in graph[current]
                        if candidate != previous and frozenset((current, candidate)) not in visited
                    ]
                    if not candidates:
                        break
                    following = candidates[0]
                    mark(current, following)
                    chain.append(following)
                    previous, current = current, following
                if len(chain) >= 2 and (end != node_id or polyline_length(chain) > 1):
                    edges.append({"a": node_id, "b": end, "points": chain})

    for point, neighbours in graph.items():
        for neighbour in neighbours:
            if frozenset((point, neighbour)) in visited:
                continue
            chain = [point, neighbour]
            mark(point, neighbour)
            previous, current = point, neighbour
            while True:
                candidates = [
                    candidate for candidate in graph[current]
                    if candidate != previous and frozenset((current, candidate)) not in visited
                ]
                if not candidates:
                    break
                following = candidates[0]
                mark(current, following)
                chain.append(following)
                previous, current = current, following
                if current == point:
                    break
            edges.append({"a": None, "b": None, "points": chain})
    return edges, nodes


def merge_straightest(edges, nodes) -> list[list[tuple[float, float]]]:
    incidents: dict[int, list[int]] = defaultdict(list)
    for edge_id, edge in enumerate(edges):
        if edge["a"] is not None:
            incidents[edge["a"]].append(edge_id)
        if edge["b"] is not None and edge["b"] != edge["a"]:
            incidents[edge["b"]].append(edge_id)
    pairing: dict[tuple[int, int], int] = {}

    def outward(edge_id: int, node_id: int) -> np.ndarray:
        edge = edges[edge_id]
        points = edge["points"] if edge["a"] == node_id else list(reversed(edge["points"]))
        origin = np.asarray(points[0], dtype=float)
        target = np.asarray(points[min(len(points) - 1, 12)], dtype=float)
        vector = target - origin
        norm = np.linalg.norm(vector)
        return vector / norm if norm else vector

    for node_id, edge_ids in incidents.items():
        remaining = set(edge_ids)
        choices = []
        for index, first in enumerate(edge_ids):
            first_vector = outward(first, node_id)
            for second in edge_ids[index + 1:]:
                choices.append((float(np.dot(first_vector, outward(second, node_id))), first, second))
        for _, first, second in sorted(choices):
            if first in remaining and second in remaining:
                pairing[(first, node_id)] = second
                pairing[(second, node_id)] = first
                remaining.remove(first)
                remaining.remove(second)

    used: set[int] = set()
    paths: list[list[tuple[float, float]]] = []

    def walk(start_edge: int, start_node: int):
        edge_id, node_id = start_edge, start_node
        combined = []
        while edge_id not in used:
            used.add(edge_id)
            edge = edges[edge_id]
            points = edge["points"] if edge["a"] == node_id else list(reversed(edge["points"]))
            combined.extend(points[1:] if combined and combined[-1] == points[0] else points)
            other = edge["b"] if edge["a"] == node_id else edge["a"]
            if other is None:
                break
            following = pairing.get((edge_id, other))
            if following is None or following in used:
                break
            edge_id, node_id = following, other
        return combined

    starts = [
        (edge_id, node_id)
        for node_id, edge_ids in incidents.items()
        for edge_id in edge_ids
        if (edge_id, node_id) not in pairing
    ]
    for edge_id, node_id in starts:
        if edge_id not in used:
            paths.append(walk(edge_id, node_id))
    for edge_id, edge in enumerate(edges):
        if edge_id in used:
            continue
        if edge["a"] is None:
            used.add(edge_id)
            paths.append(edge["points"])
        else:
            paths.append(walk(edge_id, edge["a"]))
    return paths


def dense_polyline(path: list[Point], spacing: float) -> list[Point]:
    result = [path[0]]
    for start, end in zip(path, path[1:]):
        length = math.dist(start, end)
        steps = max(1, math.ceil(length / spacing))
        for index in range(1, steps + 1):
            ratio = index / steps
            result.append((
                start[0] + (end[0] - start[0]) * ratio,
                start[1] + (end[1] - start[1]) * ratio,
            ))
    return result


def mask_distance(distance: np.ndarray, point: Point) -> float:
    x, y = point
    row = max(0, min(distance.shape[0] - 1, round(y * SCALE)))
    column = max(0, min(distance.shape[1] - 1, round(x * SCALE)))
    return float(distance[row, column])


def perpendicular_distance(point: Point, start: Point, end: Point) -> float:
    first = np.asarray(start, dtype=float)
    last = np.asarray(end, dtype=float)
    current = np.asarray(point, dtype=float)
    direction = last - first
    if np.allclose(direction, 0):
        return float(np.linalg.norm(current - first))
    offset = current - first
    signed_area = direction[0] * offset[1] - direction[1] * offset[0]
    return float(abs(signed_area) / np.linalg.norm(direction))


def segment_supported(start: Point, end: Point, distance: np.ndarray) -> bool:
    return max(mask_distance(distance, point) for point in dense_polyline([start, end], 0.125)) <= SOURCE_NEIGHBOURHOOD + 1e-9


def constrained_rdp(points: list[Point], distance: np.ndarray) -> list[Point]:
    if len(points) <= 2:
        return points
    deviations = [perpendicular_distance(point, points[0], points[-1]) for point in points[1:-1]]
    maximum = max(deviations, default=0.0)
    if maximum <= RDP_TOLERANCE and segment_supported(points[0], points[-1], distance):
        return [points[0], points[-1]]
    split = deviations.index(maximum) + 1 if maximum > RDP_TOLERANCE else len(points) // 2
    return constrained_rdp(points[:split + 1], distance)[:-1] + constrained_rdp(points[split:], distance)


def normalize_point(point: Point) -> Point:
    return tuple(round(max(0.0, min(float(GRID), float(value))), 3) for value in point)  # type: ignore[return-value]


def order_by_nearest_endpoint(paths: PathList) -> PathList:
    remaining = list(enumerate(paths))
    endpoints = []
    for index, path in remaining:
        endpoints.extend(((path[0][1], path[0][0], index, False), (path[-1][1], path[-1][0], index, True)))
    _, _, first_index, reverse = min(endpoints)
    selected = next(path for index, path in remaining if index == first_index)
    result = [list(reversed(selected)) if reverse else selected]
    remaining = [(index, path) for index, path in remaining if index != first_index]
    while remaining:
        current = result[-1][-1]
        choices = []
        for index, path in remaining:
            choices.extend(((math.dist(current, path[0]), index, False, path), (math.dist(current, path[-1]), index, True, path)))
        _, selected_index, reverse, selected = min(choices, key=lambda item: (item[0], item[1], item[2]))
        result.append(list(reversed(selected)) if reverse else selected)
        remaining = [(index, path) for index, path in remaining if index != selected_index]
    return result


def generate_paths(skeleton: np.ndarray, source_distance: np.ndarray) -> PathList:
    edges, nodes = abstract_edges(skeleton)
    paths = []
    for raw in merge_straightest(edges, nodes):
        points = []
        for y, x in raw:
            point = normalize_point((x / SCALE, y / SCALE))
            if not points or points[-1] != point:
                points.append(point)
        if len(points) < 2:
            continue
        simplified = [normalize_point(point) for point in constrained_rdp(points, source_distance)]
        if len(simplified) >= 2 and polyline_length(simplified) >= MIN_PATH_LENGTH:
            paths.append(simplified)
    if not paths:
        raise RuntimeError("Skeleton produced no candidate paths")
    return order_by_nearest_endpoint(paths)


def component_metrics(source_mask: np.ndarray, skeleton: np.ndarray, paths: PathList) -> dict[str, float | int]:
    source_labels, component_count = label(source_mask, structure=np.ones((3, 3), dtype=np.uint8))
    distance = distance_transform_edt(~source_mask) / SCALE
    samples = [point for path in paths for point in dense_polyline(path, 0.25)]
    candidate = np.asarray(samples)
    skeleton_points = np.argwhere(skeleton)[:, ::-1] / SCALE
    skeleton_distances = cKDTree(candidate).query(skeleton_points)[0]
    outline_distances = np.asarray([mask_distance(distance, point) for point in samples])
    represented = set()
    for x, y in samples:
        row = max(0, min(source_labels.shape[0] - 1, round(y * SCALE)))
        column = max(0, min(source_labels.shape[1] - 1, round(x * SCALE)))
        if source_labels[row, column]:
            represented.add(int(source_labels[row, column]))
    return {
        "source_components": int(component_count),
        "missing_source_components": int(component_count - len(represented)),
        "coverage_1_5px": float(np.mean(skeleton_distances <= 1.5)),
        "uncovered_p90": float(np.percentile(skeleton_distances, 90)),
        "within_outline_or_0_5": float(np.mean(outline_distances <= SOURCE_NEIGHBOURHOOD + 1e-9)),
        "within_outline_or_1_0": float(np.mean(outline_distances <= 1.0 + 1e-9)),
        "maximum_outline_distance": float(np.max(outline_distances)),
    }


def path_data(points: list[Point]) -> str:
    def format_value(value: float) -> str:
        text = f"{value:.3f}".rstrip("0").rstrip(".")
        return text if text not in {"", "-0"} else "0"
    return "M" + " L".join(f"{format_value(x)},{format_value(y)}" for x, y in points)


def svg_bytes(codepoint: int, paths: PathList) -> bytes:
    root = ET.Element("svg", {
        "xmlns": "http://www.w3.org/2000/svg",
        "viewBox": "0 0 109 109",
        "data-source-style": "yomogi",
        "data-path-semantics": "visual-centerline",
        "data-order-semantics": "none",
        "data-runtime-mode": "direct",
        "data-geometry-source": "Yomogi outline skeleton only",
        "data-kanjivg-role": "fallback only; no geometry, order, direction, or path-count input",
        "data-cleanup": "4x skeletonize; spur-prune-2.5; no-corner-cut graph; straightest continuation; constrained-rdp-0.75; min-path-3.0",
    })
    for index, points in enumerate(paths, 1):
        ET.SubElement(root, "path", {
            "id": f"yomogi:{codepoint:05x}-direct-p{index}",
            "d": path_data(points),
            "data-path-index": str(index),
        })
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def convert_glyph(font: ImageFont.FreeTypeFont, codepoint: int) -> tuple[bytes, dict[str, object]]:
    source_mask = render_source_mask(font, chr(codepoint))
    skeleton = skeleton_for_mask(source_mask)
    source_distance = distance_transform_edt(~source_mask) / SCALE
    paths = generate_paths(skeleton, source_distance)
    metrics = component_metrics(source_mask, skeleton, paths)
    lengths = [polyline_length(path) for path in paths]
    record: dict[str, object] = {
        "character": chr(codepoint),
        "codepoint": f"U+{codepoint:04X}",
        "filename": f"{codepoint:05x}.svg",
        "paths": len(paths),
        "points": sum(len(path) for path in paths),
        "minimum_path_length": round(min(lengths), 6),
        "maximum_path_length": round(max(lengths), 6),
    }
    record.update({key: round(value, 6) if isinstance(value, float) else value for key, value in metrics.items()})
    return svg_bytes(codepoint, paths), record


def path_data_from_svg(path: Path) -> list[str]:
    return [
        node.attrib["d"]
        for node in ET.parse(path).getroot().iter()
        if node.tag.endswith("path")
    ]
