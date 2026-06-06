"""Shared loading of prepared frame directories (metadata.json + payloads)."""

from __future__ import annotations

import json
from pathlib import Path

__all__ = ["load_metadata", "load_frame", "prepare_frames"]


def load_metadata(directory: Path) -> dict:
    """Read and parse a frame directory's metadata.json."""
    metadata_path = directory / "metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"Missing metadata.json in {directory}")
    return json.loads(metadata_path.read_text())


def load_frame(directory: Path, filename: str) -> bytes:
    """Read a single frame payload from a directory."""
    path = directory / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing frame {filename} in {directory}")
    return path.read_bytes()


def prepare_frames(
    directory: Path,
) -> tuple[list[tuple[bytes, int]], tuple[int, int], str]:
    """Load all frames for an eye.

    Returns a list of ``(payload, duration_ms)`` tuples, the frame size, and the
    RGB565 byte order recorded in metadata (defaults to ``"little"`` for frames
    produced before byte order was persisted).
    """
    metadata = load_metadata(directory)
    size = (metadata["size"]["width"], metadata["size"]["height"])
    byteorder = metadata.get("byteorder", "little")
    frames: list[tuple[bytes, int]] = []
    for frame in metadata.get("frames", []):
        payload = load_frame(directory, frame["filename"])
        frames.append((payload, frame["duration_ms"]))
    return frames, size, byteorder
