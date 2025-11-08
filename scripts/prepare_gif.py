#!/usr/bin/env python3
"""Convert GIF animations into 240x240 frames and RGB565 payloads."""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from PIL import Image, ImageOps, ImageSequence
from dotenv import load_dotenv

try:  # Pillow < 9.1 transitional support
    RESAMPLING_FILTER = Image.Resampling.LANCZOS
except AttributeError:  # pragma: no cover - legacy fallback
    RESAMPLING_FILTER = Image.LANCZOS


@dataclass(frozen=True)
class FrameExport:
    filename: str
    duration_ms: int


def _parse_size_string(value: str) -> tuple[int, int]:
    tokens = value.replace("x", " ").replace(",", " ").split()
    if len(tokens) != 2:
        raise ValueError("Size must have two components")
    width, height = (int(token) for token in tokens)
    return width, height


def env_size(name: str, default: tuple[int, int]) -> tuple[int, int]:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return _parse_size_string(raw)
    except (ValueError, TypeError):
        return default


def env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def env_byteorder(name: str, default: str) -> str:
    raw = os.getenv(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"little", "big"}:
        return normalized
    return default


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resize GIF frames and emit RGB565 payloads plus timing metadata."
    )
    parser.add_argument("input_gif", type=Path, help="Path to the source GIF animation.")
    parser.add_argument("output_dir", type=Path, help="Directory to write processed frames.")
    parser.add_argument(
        "--size",
        type=int,
        nargs=2,
        default=None,
        metavar=("WIDTH", "HEIGHT"),
        help="Target frame size (default: 240 240).",
    )
    parser.add_argument(
        "--rgb565",
        dest="rgb565",
        action="store_true",
        default=None,
        help="Emit frames as little-endian RGB565 .bin files (default).",
    )
    parser.add_argument(
        "--png",
        dest="rgb565",
        action="store_false",
        help="Emit frames as PNG files instead of packed RGB565.",
    )
    parser.add_argument(
        "--byteorder",
        choices=("little", "big"),
        default=None,
        help="Endianness for RGB565 output (default: little).",
    )
    parser.add_argument(
        "--dither",
        action="store_true",
        default=None,
        help="Apply Floyd-Steinberg dithering before RGB565 packing.",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        default=None,
        help="Also save processed frames as PNG previews (helpful for quick inspection).",
    )
    return parser.parse_args()


def ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def iterate_frames(img: Image.Image) -> Iterator[Image.Image]:
    for frame in ImageSequence.Iterator(img):
        yield frame.copy()


def prepare_frame(frame: Image.Image, size: tuple[int, int], dither: bool) -> Image.Image:
    """Resize frame to fit within target size, adding black letterboxing if needed."""
    rgb_frame = frame.convert("RGB")
    
    # Calculate scaling to fit within target size while preserving aspect ratio
    frame_ratio = rgb_frame.width / rgb_frame.height
    target_ratio = size[0] / size[1]
    
    if frame_ratio > target_ratio:
        # Frame is wider - fit to width
        new_width = size[0]
        new_height = int(size[0] / frame_ratio)
    else:
        # Frame is taller - fit to height
        new_height = size[1]
        new_width = int(size[1] * frame_ratio)
    
    # Resize with high-quality resampling
    resized = rgb_frame.resize((new_width, new_height), RESAMPLING_FILTER)
    
    # Create black canvas and paste resized image centered
    canvas = Image.new("RGB", size, (0, 0, 0))
    offset_x = (size[0] - new_width) // 2
    offset_y = (size[1] - new_height) // 2
    canvas.paste(resized, (offset_x, offset_y))
    
    if dither:
        return canvas.convert("RGB", dither=Image.Dither.FLOYDSTEINBERG)
    return canvas


def rgb_to_rgb565_bytes(frame: Image.Image, byteorder: str) -> bytes:
    width, height = frame.size
    pixels = frame.load()
    buffer = bytearray(width * height * 2)
    idx = 0
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            value = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            if byteorder == "little":
                buffer[idx] = value & 0xFF
                buffer[idx + 1] = value >> 8
            else:
                buffer[idx] = value >> 8
                buffer[idx + 1] = value & 0xFF
            idx += 2
    return bytes(buffer)


def export_frame(
    processed: Image.Image,
    output_dir: Path,
    index: int,
    duration_ms: int,
    rgb565: bool,
    byteorder: str,
    preview: bool,
) -> FrameExport:
    stem = f"frame_{index:04d}"
    exports = []
    if rgb565:
        payload = rgb_to_rgb565_bytes(processed, byteorder)
        rgb_path = output_dir / f"{stem}.bin"
        rgb_path.write_bytes(payload)
        exports.append(FrameExport(rgb_path.name, duration_ms))
    else:
        png_path = output_dir / f"{stem}.png"
        processed.save(png_path, format="PNG")
        exports.append(FrameExport(png_path.name, duration_ms))

    if preview:
        preview_path = output_dir / f"{stem}_preview.png"
        processed.save(preview_path, format="PNG")
    return exports[0]


def build_metadata(
    source: Path,
    size: tuple[int, int],
    frames: list[FrameExport],
    loop: int,
) -> dict[str, object]:
    return {
        "source": str(source),
        "size": {"width": size[0], "height": size[1]},
        "frame_count": len(frames),
        "loop": loop,
        "frames": [frame.__dict__ for frame in frames],
    }


def main() -> None:
    load_dotenv()
    args = parse_args()

    size = tuple(args.size) if args.size else env_size("SHARINGAN_FRAME_SIZE", (240, 240))
    rgb565 = args.rgb565 if args.rgb565 is not None else env_bool("SHARINGAN_RGB565", True)
    byteorder = args.byteorder if args.byteorder is not None else env_byteorder("SHARINGAN_BYTEORDER", "little")
    dither = args.dither if args.dither is not None else env_bool("SHARINGAN_DITHER", False)
    preview = args.preview if args.preview is not None else env_bool("SHARINGAN_PREVIEW", False)

    ensure_output_dir(args.output_dir)

    with Image.open(args.input_gif) as img:
        loop = img.info.get("loop", 0)
        processed_frames: list[FrameExport] = []
        for index, frame in enumerate(iterate_frames(img)):
            duration_ms = int(frame.info.get("duration", 0)) or 100
            ready = prepare_frame(frame, size, dither)
            exported = export_frame(
                ready,
                args.output_dir,
                index,
                duration_ms,
                rgb565,
                byteorder,
                preview,
            )
            processed_frames.append(exported)

    metadata = build_metadata(args.input_gif, size, processed_frames, loop)
    metadata_path = args.output_dir / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2))

    print(
        f"Exported {len(processed_frames)} frames from {args.input_gif} to {args.output_dir} (loop={loop})."
    )


if __name__ == "__main__":
    main()
