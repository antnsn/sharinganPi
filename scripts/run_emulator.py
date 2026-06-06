#!/usr/bin/env python3
"""Run desktop emulator that displays left/right eye animations."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pygame

from sharingan.display import DualEmulator, EmulatorConfig
from sharingan.frames import prepare_frames

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


def main() -> int:
    args = parse_args()
    pygame.init()

    left_frames, left_size, left_byteorder = prepare_frames(args.left)
    right_frames, right_size, right_byteorder = prepare_frames(args.right)
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
            running = emulator.show_pair(
                right_payload, left_payload, right_size, left_size, duration_ms,
                right_byteorder, left_byteorder,
            )
        else:
            running = emulator.show_pair(
                left_payload, right_payload, left_size, right_size, duration_ms,
                left_byteorder, right_byteorder,
            )

        index += 1
        if not args.loop and index >= frame_count:
            break

    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
