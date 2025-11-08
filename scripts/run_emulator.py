#!/usr/bin/env python3
"""Run desktop emulator that displays left/right eye animations."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, Iterator

import pygame

from sharingan.display import DualEmulator, EmulatorConfig

DEFAULT_DIAMETER = 240


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Sharingan dual-eye emulator")
    parser.add_argument(
        "left", type=Path, help="Directory containing left eye metadata.json and frames"
    )
    parser.add_argument(
        "right", type=Path, help="Directory containing right eye metadata.json and frames"
    )
    parser.add_argument(
        "--diameter",
        type=int,
        default=DEFAULT_DIAMETER,
        help="Display diameter in pixels (default: 240)",
    )
    parser.add_argument(
        "--gap",
        type=int,
        default=20,
        help="Gap in pixels between the left and right windows (default: 20)",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Loop animation indefinitely (default: play once)",
    )
    parser.add_argument(
        "--swap",
        action="store_true",
        help="Swap left/right windows (useful for testing mirroring)",
    )
    return parser.parse_args()


def load_metadata(directory: Path) -> dict:
    metadata_path = directory / "metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"Missing metadata.json in {directory}")
    return json.loads(metadata_path.read_text())


def load_frame(directory: Path, filename: str) -> bytes:
    path = directory / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing frame {filename} in {directory}")
    return path.read_bytes()


def prepare_frames(directory: Path) -> tuple[list[tuple[bytes, int]], tuple[int, int]]:
    metadata = load_metadata(directory)
    size = (metadata["size"]["width"], metadata["size"]["height"])
    frames: list[tuple[bytes, int]] = []
    for frame in metadata.get("frames", []):
        payload = load_frame(directory, frame["filename"])
        frames.append((payload, frame["duration_ms"]))
    return frames, size


def main() -> int:
    args = parse_args()
    pygame.init()

    left_frames, left_size = prepare_frames(args.left)
    right_frames, right_size = prepare_frames(args.right)
    frame_count = min(len(left_frames), len(right_frames))
    if frame_count == 0:
        print("No frames available. Did you run prepare_gif?", file=sys.stderr)
        return 1

    config = EmulatorConfig(
        diameter=args.diameter,
        gap=args.gap,
        position=(100, 100),
    )
    emulator = DualEmulator(config)

    running = True
    index = 0
    while running:
        left_payload, left_duration = left_frames[index % frame_count]
        right_payload, right_duration = right_frames[index % frame_count]
        duration_ms = min(left_duration, right_duration)
        
        if args.swap:
            running = emulator.show_pair(right_payload, left_payload, right_size, left_size, duration_ms)
        else:
            running = emulator.show_pair(left_payload, right_payload, left_size, right_size, duration_ms)
        
        index += 1
        if not args.loop and index >= frame_count:
            break

    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
