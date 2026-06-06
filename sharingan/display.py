"""Display interfaces and round-window emulator for sharinganPi."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable, Iterator, Tuple

import numpy as np
import pygame

__all__ = ["EmulatorConfig", "DualEmulator", "pump_events", "should_exit"]


def rgb565_to_surface(
    payload: bytes, width: int, height: int, byteorder: str = "little"
) -> pygame.Surface:
    """Convert packed RGB565 bytes into a Pygame surface (vectorized)."""

    dtype = "<u2" if byteorder == "little" else ">u2"
    value = np.frombuffer(payload, dtype=dtype).reshape((height, width)).astype(np.uint32)

    r = (value >> 11) & 0x1F
    g = (value >> 5) & 0x3F
    b = value & 0x1F
    # Expand 5/6-bit channels back to full 8-bit range.
    r = ((r << 3) | (r >> 2)).astype(np.uint8)
    g = ((g << 2) | (g >> 4)).astype(np.uint8)
    b = ((b << 3) | (b >> 2)).astype(np.uint8)

    rgb = np.dstack((r, g, b))  # (height, width, 3), row-major
    return pygame.image.frombuffer(rgb.tobytes(), (width, height), "RGB")


def build_circle_alpha(diameter: int) -> pygame.Surface:
    """Create a circular alpha stencil: opaque white inside, transparent outside.

    Blitting this onto an eye surface with ``BLEND_RGBA_MULT`` keeps the eye's
    colors inside the circle while zeroing alpha outside it.
    """
    radius = diameter // 2
    circle = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
    circle.fill((255, 255, 255, 0))
    pygame.draw.circle(circle, (255, 255, 255, 255), (radius, radius), radius)
    return circle


@dataclass(frozen=True)
class EmulatorConfig:
    """Window sizing and layout options for the emulator."""

    diameter: int = 240
    gap: int = 20
    position: Tuple[int, int] = (100, 100)
    background_color: Tuple[int, int, int] = (50, 50, 50)
    window_title: str = "Sharingan Emulator"


def pump_events() -> Iterator[pygame.event.Event]:
    """Yield pending Pygame events."""

    for event in pygame.event.get():
        yield event


def should_exit(events: Iterable[pygame.event.Event]) -> bool:
    """Return True when any exit-triggering event is observed."""

    for event in events:
        if event.type == pygame.QUIT:
            return True
        if event.type == pygame.KEYDOWN and event.key in {pygame.K_ESCAPE, pygame.K_q}:
            return True
    return False


class DualEmulator:
    """Render two circular eye windows inside a single borderless Pygame window."""

    def __init__(self, config: EmulatorConfig) -> None:
        self.config = config
        os.environ.setdefault("SDL_VIDEO_CENTERED", "0")
        os.environ["SDL_VIDEO_WINDOW_POS"] = f"{config.position[0]},{config.position[1]}"
        os.environ["SDL_VIDEO_WINDOW_ALPHA"] = "1"

        total_width = config.diameter * 2 + config.gap
        self.window = pygame.display.set_mode((total_width, config.diameter), pygame.NOFRAME)
        if self.window is None:
            raise RuntimeError("Failed to create Pygame window")
        pygame.display.set_caption(config.window_title)
        
        # Enable per-pixel alpha for transparency
        self.window.set_alpha(None)

        self.circle_alpha = build_circle_alpha(config.diameter)

    def _render_eye(
        self, payload: bytes, size: Tuple[int, int], byteorder: str
    ) -> pygame.Surface:
        diameter = self.config.diameter
        surface = rgb565_to_surface(payload, *size, byteorder)
        if surface.get_size() != (diameter, diameter):
            surface = pygame.transform.smoothscale(surface, (diameter, diameter))

        # Stencil to a circle: keep colors inside, zero alpha outside so the
        # window background shows through the corners.
        surface = surface.convert_alpha()
        surface.blit(self.circle_alpha, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        return surface

    def show_pair(
        self,
        left_payload: bytes,
        right_payload: bytes,
        left_size: Tuple[int, int],
        right_size: Tuple[int, int],
        duration_ms: int,
        left_byteorder: str = "little",
        right_byteorder: str = "little",
    ) -> bool:
        start = pygame.time.get_ticks()

        events = list(pump_events())
        if should_exit(events):
            return False

        # Fill with background color to show non-circular areas
        self.window.fill(self.config.background_color)

        left_surface = self._render_eye(left_payload, left_size, left_byteorder)
        right_surface = self._render_eye(right_payload, right_size, right_byteorder)
        self.window.blit(left_surface, (0, 0))
        self.window.blit(right_surface, (self.config.diameter + self.config.gap, 0))
        pygame.display.flip()

        # Subtract render time so playback tracks the authored frame durations.
        elapsed = pygame.time.get_ticks() - start
        pygame.time.wait(max(duration_ms - elapsed, 0))
        return True
