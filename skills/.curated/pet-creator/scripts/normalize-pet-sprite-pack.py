#!/usr/bin/env python3
"""Build a Codex pet sprite pack from a generated PNG sprite sheet."""

from __future__ import annotations

import argparse
import json
import struct
import zlib
from collections import deque
from pathlib import Path

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
STATES = ("idle", "working", "needsUserInput", "ready")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract sprite rows into a Codex pet pack draft.",
    )
    parser.add_argument("source_image", type=Path)
    parser.add_argument("pack_dir", type=Path)
    parser.add_argument("--pack-id", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--revision", type=int, default=1)
    parser.add_argument("--row-frame-counts", default="4,4,4,4")
    parser.add_argument("--frame-duration-ms", default="240,160,120,160")
    parser.add_argument("--cell-width", type=int, default=192)
    parser.add_argument("--cell-height", type=int, default=208)
    parser.add_argument("--component-threshold", type=int, default=22)
    parser.add_argument("--large-component-area", type=int, default=12000)
    parser.add_argument("--row-tolerance", type=int, default=120)
    parser.add_argument("--crop-margin-x", type=int, default=22)
    parser.add_argument("--crop-margin-top", type=int, default=2)
    parser.add_argument("--crop-margin-bottom", type=int, default=12)
    parser.add_argument("--paste-bottom-margin", type=int, default=4)
    parser.add_argument("--alpha-zero", type=int, default=14)
    parser.add_argument("--alpha-full", type=int, default=56)
    return parser.parse_args()


def read_rgb_png(path: Path) -> tuple[int, int, list[list[tuple[int, int, int]]]]:
    data = path.read_bytes()
    if data[:8] != PNG_SIGNATURE:
        raise ValueError(f"{path} is not a PNG file")

    width = 0
    height = 0
    bit_depth = 0
    color_type = -1
    idat_chunks: list[bytes] = []
    offset = 8

    while offset < len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        chunk_payload = data[offset + 8 : offset + 8 + length]
        offset += 12 + length

        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, _, _, _ = struct.unpack(
                ">IIBBBBB",
                chunk_payload,
            )
        elif chunk_type == b"IDAT":
            idat_chunks.append(chunk_payload)
        elif chunk_type == b"IEND":
            break

    if bit_depth != 8 or color_type not in (2, 6):
        raise ValueError(
            f"{path} must be an 8-bit RGB/RGBA PNG, got {(bit_depth, color_type)}",
        )

    bytes_per_pixel = 4 if color_type == 6 else 3
    stride = width * bytes_per_pixel
    raw = zlib.decompress(b"".join(idat_chunks))
    previous_row = [0] * stride
    source_offset = 0
    rows: list[list[int]] = []

    for _ in range(height):
        filter_type = raw[source_offset]
        source_offset += 1
        row = list(raw[source_offset : source_offset + stride])
        source_offset += stride

        if filter_type == 1:
            for index in range(stride):
                left = row[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
                row[index] = (row[index] + left) & 255
        elif filter_type == 2:
            for index in range(stride):
                row[index] = (row[index] + previous_row[index]) & 255
        elif filter_type == 3:
            for index in range(stride):
                left = row[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
                up = previous_row[index]
                row[index] = (row[index] + ((left + up) >> 1)) & 255
        elif filter_type == 4:
            for index in range(stride):
                left = row[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
                up = previous_row[index]
                upper_left = (
                    previous_row[index - bytes_per_pixel]
                    if index >= bytes_per_pixel
                    else 0
                )
                row[index] = (row[index] + paeth_predictor(left, up, upper_left)) & 255
        elif filter_type != 0:
            raise ValueError(f"Unsupported PNG filter {filter_type}")

        rows.append(row)
        previous_row = row

    return width, height, [
        [
            tuple(row[x * bytes_per_pixel : x * bytes_per_pixel + 3])
            for x in range(width)
        ]
        for row in rows
    ]


def paeth_predictor(left: int, up: int, upper_left: int) -> int:
    estimate = left + up - upper_left
    left_distance = abs(estimate - left)
    up_distance = abs(estimate - up)
    diagonal_distance = abs(estimate - upper_left)

    if left_distance <= up_distance and left_distance <= diagonal_distance:
        return left
    if up_distance <= diagonal_distance:
        return up
    return upper_left


def write_rgba_png(
    path: Path,
    width: int,
    height: int,
    pixels: list[list[tuple[int, int, int, int]]],
) -> None:
    raw_rows: list[bytes] = []
    for row_pixels in pixels:
        raw_row = bytearray([0])
        for pixel in row_pixels:
            raw_row.extend(pixel)
        raw_rows.append(bytes(raw_row))

    png = bytearray(PNG_SIGNATURE)
    png.extend(
        build_png_chunk(
            b"IHDR",
            struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0),
        ),
    )
    png.extend(build_png_chunk(b"IDAT", zlib.compress(b"".join(raw_rows), 9)))
    png.extend(build_png_chunk(b"IEND", b""))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


def build_png_chunk(chunk_type: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + chunk_type
        + payload
        + struct.pack(">I", zlib.crc32(chunk_type + payload) & 0xFFFFFFFF)
    )


def color_distance_squared(
    pixel: tuple[int, int, int],
    background: tuple[int, int, int],
) -> int:
    return sum((pixel[channel] - background[channel]) ** 2 for channel in range(3))


def detect_large_components(
    pixels: list[list[tuple[int, int, int]]],
    background: tuple[int, int, int],
    component_threshold: int,
    large_component_area: int,
) -> list[tuple[int, int, int, int]]:
    height = len(pixels)
    width = len(pixels[0])
    threshold_sq = component_threshold * component_threshold
    mask = [
        [color_distance_squared(pixels[y][x], background) > threshold_sq for x in range(width)]
        for y in range(height)
    ]
    visited = [[False] * width for _ in range(height)]
    components: list[tuple[int, int, int, int]] = []

    for y in range(height):
        for x in range(width):
            if not mask[y][x] or visited[y][x]:
                continue

            queue = deque([(x, y)])
            visited[y][x] = True
            area = 0
            min_x = max_x = x
            min_y = max_y = y

            while queue:
                cx, cy = queue.popleft()
                area += 1
                min_x = min(min_x, cx)
                max_x = max(max_x, cx)
                min_y = min(min_y, cy)
                max_y = max(max_y, cy)

                for nx, ny in (
                    (cx + 1, cy),
                    (cx - 1, cy),
                    (cx, cy + 1),
                    (cx, cy - 1),
                ):
                    if (
                        0 <= nx < width
                        and 0 <= ny < height
                        and mask[ny][nx]
                        and not visited[ny][nx]
                    ):
                        visited[ny][nx] = True
                        queue.append((nx, ny))

            if area >= large_component_area:
                components.append((min_x, min_y, max_x, max_y))

    return sorted(components, key=lambda box: ((box[1] + box[3]) / 2, (box[0] + box[2]) / 2))


def group_components_by_row(
    components: list[tuple[int, int, int, int]],
    expected_row_counts: list[int],
    row_tolerance: int,
) -> list[list[tuple[int, int, int, int]]]:
    rows: list[list[tuple[int, int, int, int]]] = []
    centers: list[float] = []

    for box in components:
        center_y = (box[1] + box[3]) / 2
        if rows and abs(centers[-1] - center_y) < row_tolerance:
            rows[-1].append(box)
            centers[-1] = sum((row_box[1] + row_box[3]) / 2 for row_box in rows[-1]) / len(rows[-1])
        else:
            rows.append([box])
            centers.append(center_y)

    row_counts = [len(row) for row in rows]
    if row_counts != expected_row_counts:
        raise ValueError(
            f"Detected row counts {row_counts}, expected {expected_row_counts}. "
            "Tune thresholds/crop margins for this source sheet.",
        )

    return [sorted(row, key=lambda box: (box[0] + box[2]) / 2) for row in rows]


def extract_frame_pixels(
    pixels: list[list[tuple[int, int, int]]],
    background: tuple[int, int, int],
    box: tuple[int, int, int, int],
    crop_margin_x: int,
    crop_margin_top: int,
    crop_margin_bottom: int,
    alpha_zero: int,
    alpha_full: int,
) -> list[list[tuple[int, int, int, int]]]:
    source_height = len(pixels)
    source_width = len(pixels[0])
    min_x, min_y, max_x, max_y = box
    crop_left = max(0, min_x - crop_margin_x)
    crop_top = max(0, min_y - crop_margin_top)
    crop_right = min(source_width - 1, max_x + crop_margin_x)
    crop_bottom = min(source_height - 1, max_y + crop_margin_bottom)
    frame: list[list[tuple[int, int, int, int]]] = []

    for source_y in range(crop_top, crop_bottom + 1):
        frame_row: list[tuple[int, int, int, int]] = []
        for source_x in range(crop_left, crop_right + 1):
            red, green, blue = pixels[source_y][source_x]
            distance_sq = color_distance_squared((red, green, blue), background)

            if distance_sq <= alpha_zero * alpha_zero:
                frame_row.append((0, 0, 0, 0))
                continue

            if distance_sq >= alpha_full * alpha_full:
                alpha = 255
            else:
                distance = distance_sq**0.5
                alpha = round(
                    (distance - alpha_zero) * 255 / (alpha_full - alpha_zero),
                )

            if alpha < 255:
                inverse_alpha = 255 - alpha
                red = unblend_channel(red, background[0], alpha, inverse_alpha)
                green = unblend_channel(green, background[1], alpha, inverse_alpha)
                blue = unblend_channel(blue, background[2], alpha, inverse_alpha)

            frame_row.append((red, green, blue, alpha))
        frame.append(frame_row)

    return frame


def unblend_channel(
    source_channel: int,
    background_channel: int,
    alpha: int,
    inverse_alpha: int,
) -> int:
    return max(
        0,
        min(
            255,
            round((source_channel * 255 - background_channel * inverse_alpha) / alpha),
        ),
    )


def resize_frame(
    frame: list[list[tuple[int, int, int, int]]],
    scale: float,
) -> list[list[tuple[int, int, int, int]]]:
    source_height = len(frame)
    source_width = len(frame[0])
    target_width = max(1, round(source_width * scale))
    target_height = max(1, round(source_height * scale))
    resized_frame = [[(0, 0, 0, 0)] * target_width for _ in range(target_height)]

    for target_y in range(target_height):
        source_y = min(source_height - 1, int(target_y / scale))
        for target_x in range(target_width):
            source_x = min(source_width - 1, int(target_x / scale))
            resized_frame[target_y][target_x] = frame[source_y][source_x]

    return resized_frame


def build_sprite_strip(
    frames: list[list[list[tuple[int, int, int, int]]]],
    cell_width: int,
    cell_height: int,
    paste_bottom_margin: int,
) -> list[list[tuple[int, int, int, int]]]:
    max_frame_width = max(len(frame[0]) for frame in frames)
    max_frame_height = max(len(frame) for frame in frames)
    scale = min(
        (cell_width - 16) / max_frame_width,
        (cell_height - 10) / max_frame_height,
    )
    strip = [[(0, 0, 0, 0)] * (len(frames) * cell_width) for _ in range(cell_height)]

    for frame_index, frame in enumerate(frames):
        resized_frame = resize_frame(frame, scale)
        frame_height = len(resized_frame)
        frame_width = len(resized_frame[0])
        offset_x = frame_index * cell_width + (cell_width - frame_width) // 2
        offset_y = cell_height - paste_bottom_margin - frame_height

        for frame_y, frame_row in enumerate(resized_frame):
            for frame_x, pixel in enumerate(frame_row):
                strip[offset_y + frame_y][offset_x + frame_x] = pixel

    return strip


def parse_int_list(value: str, label: str) -> list[int]:
    values = [int(part) for part in value.split(",") if part]
    if len(values) != len(STATES) or any(item <= 0 for item in values):
        raise ValueError(f"--{label} must include {len(STATES)} positive integers")
    return values


def main() -> None:
    args = parse_args()
    row_frame_counts = parse_int_list(args.row_frame_counts, "row-frame-counts")
    frame_duration_ms = parse_int_list(args.frame_duration_ms, "frame-duration-ms")

    _, _, pixels = read_rgb_png(args.source_image)
    background = pixels[0][0]
    component_rows = group_components_by_row(
        detect_large_components(
            pixels=pixels,
            background=background,
            component_threshold=args.component_threshold,
            large_component_area=args.large_component_area,
        ),
        expected_row_counts=row_frame_counts,
        row_tolerance=args.row_tolerance,
    )
    frame_rows = [
        [
            extract_frame_pixels(
                pixels=pixels,
                background=background,
                box=frame_box,
                crop_margin_x=args.crop_margin_x,
                crop_margin_top=args.crop_margin_top,
                crop_margin_bottom=args.crop_margin_bottom,
                alpha_zero=args.alpha_zero,
                alpha_full=args.alpha_full,
            )
            for frame_box in component_row
        ]
        for component_row in component_rows
    ]

    states_dir = args.pack_dir / "states"
    states_dir.mkdir(parents=True, exist_ok=True)
    manifest_states: dict[str, dict[str, int | str]] = {}

    for state, frames, duration_ms in zip(STATES, frame_rows, frame_duration_ms):
        write_rgba_png(
            states_dir / f"{state}.png",
            args.cell_width * len(frames),
            args.cell_height,
            build_sprite_strip(frames, args.cell_width, args.cell_height, args.paste_bottom_margin),
        )
        manifest_states[state] = {
            "path": f"states/{state}.png",
            "frameCount": len(frames),
            "frameDurationMs": duration_ms,
        }

    write_rgba_png(
        args.pack_dir / "thumbnail.png",
        args.cell_width,
        args.cell_height,
        build_sprite_strip([frame_rows[0][0]], args.cell_width, args.cell_height, args.paste_bottom_margin),
    )
    manifest = {
        "schemaVersion": 1,
        "id": args.pack_id,
        "name": args.name,
        "revision": args.revision,
        "renderWidthPx": args.cell_width,
        "renderHeightPx": args.cell_height,
        "thumbnail": "thumbnail.png",
        "states": manifest_states,
    }
    args.pack_dir.mkdir(parents=True, exist_ok=True)
    (args.pack_dir / "manifest.json").write_text(
        f"{json.dumps(manifest, indent=2)}\n",
        encoding="utf-8",
    )
    print(json.dumps({"packId": args.pack_id, "packPath": str(args.pack_dir)}, indent=2))


if __name__ == "__main__":
    main()
