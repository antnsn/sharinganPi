#!/usr/bin/env python3
"""Run Sharingan animations on hardware GC9A01 displays."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from threading import Thread

from sharingan.gc9a01 import GC9A01


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Sharingan on hardware displays")
    parser.add_argument(
        "left", type=Path, help="Directory containing left eye metadata.json and frames"
    )
    parser.add_argument(
        "right", type=Path, help="Directory containing right eye metadata.json and frames"
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Loop animation indefinitely (default: play once)",
    )
    parser.add_argument(
        "--left-spi",
        type=int,
        nargs=2,
        default=[0, 0],
        metavar=("BUS", "DEVICE"),
        help="Left display SPI bus and device (default: 0 0)",
    )
    parser.add_argument(
        "--right-spi",
        type=int,
        nargs=2,
        default=[0, 1],
        metavar=("BUS", "DEVICE"),
        help="Right display SPI bus and device (default: 0 1)",
    )
    parser.add_argument(
        "--left-dc",
        type=int,
        default=25,
        help="Left display DC GPIO pin (BCM, default: 25)",
    )
    parser.add_argument(
        "--right-dc",
        type=int,
        default=23,
        help="Right display DC GPIO pin (BCM, default: 23)",
    )
    parser.add_argument(
        "--left-rst",
        type=int,
        default=27,
        help="Left display RST GPIO pin (BCM, default: 27)",
    )
    parser.add_argument(
        "--right-rst",
        type=int,
        default=22,
        help="Right display RST GPIO pin (BCM, default: 22)",
    )
    parser.add_argument(
        "--left-bl",
        type=int,
        default=24,
        help="Left display backlight GPIO pin (BCM, default: 24)",
    )
    parser.add_argument(
        "--right-bl",
        type=int,
        default=18,
        help="Right display backlight GPIO pin (BCM, default: 18)",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=None,
        help="Override frame rate (frames per second)",
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

    # Load frame data
    left_frames, left_size = prepare_frames(args.left)
    right_frames, right_size = prepare_frames(args.right)
    frame_count = min(len(left_frames), len(right_frames))

    if frame_count == 0:
        print("No frames available. Did you run prepare_gif?", file=sys.stderr)
        return 1

    # Verify frame sizes match display resolution
    if left_size != (240, 240) or right_size != (240, 240):
        print(
            f"Warning: Frame sizes {left_size} and {right_size} may not match 240x240 displays",
            file=sys.stderr,
        )

    # Initialize displays
    print("Initializing displays...")
    try:
        left_display = GC9A01(
            spi_bus=args.left_spi[0],
            spi_device=args.left_spi[1],
            dc_pin=args.left_dc,
            rst_pin=args.left_rst,
            bl_pin=args.left_bl,
        )
        right_display = GC9A01(
            spi_bus=args.right_spi[0],
            spi_device=args.right_spi[1],
            dc_pin=args.right_dc,
            rst_pin=args.right_rst,
            bl_pin=args.right_bl,
        )
        print("Displays initialized successfully")
    except Exception as e:
        print(f"Failed to initialize displays: {e}", file=sys.stderr)
        return 1

    # Play animation
    try:
        index = 0
        running = True
        print(f"Playing {frame_count} frames... (Ctrl+C to stop)")

        while running:
            frame_start = time.perf_counter()
            
            left_payload, left_duration = left_frames[index % frame_count]
            right_payload, right_duration = right_frames[index % frame_count]

            # Display frames on both screens in parallel
            left_thread = Thread(target=left_display.display_frame, args=(left_payload,))
            right_thread = Thread(target=right_display.display_frame, args=(right_payload,))
            
            left_thread.start()
            right_thread.start()
            
            left_thread.join()
            right_thread.join()

            # Calculate delay accounting for frame processing time
            if args.fps:
                target_frame_time = 1.0 / args.fps
            else:
                target_frame_time = min(left_duration, right_duration) / 1000.0
            
            elapsed = time.perf_counter() - frame_start
            delay = max(0, target_frame_time - elapsed)
            if delay > 0:
                time.sleep(delay)

            index += 1
            if not args.loop and index >= frame_count:
                running = False

    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        print("Cleaning up...")
        left_display.cleanup()
        right_display.cleanup()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
