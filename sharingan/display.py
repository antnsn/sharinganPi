"""Display interfaces and round-window emulator for sharinganPi."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable, Iterator, Tuple

import pygame

__all__ = ["EmulatorConfig", "DualEmulator", "pump_events", "should_exit"]


def rgb565_to_surface(payload: bytes, width: int, height: int) -> pygame.Surface:
    """Convert packed RGB565 bytes into a Pygame surface."""

    surface = pygame.Surface((width, height))
    pixels = pygame.PixelArray(surface)
    idx = 0
    for y in range(height):
        for x in range(width):
            lo = payload[idx]
            hi = payload[idx + 1]
            idx += 2
            value = (hi << 8) | lo
            r = (value >> 11) & 0x1F
            g = (value >> 5) & 0x3F
            b = value & 0x1F
            r = (r << 3) | (r >> 2)
            g = (g << 2) | (g >> 4)
            b = (b << 3) | (b >> 2)
            pixels[x][y] = (r << 16) | (g << 8) | b
    del pixels
    return surface


def build_round_mask(diameter: int) -> pygame.Surface:
    """Create a circular stencil - black outside circle, white inside."""
    radius = diameter // 2
    mask = pygame.Surface((diameter, diameter))
    mask.fill((0, 0, 0))  # Black background
    pygame.draw.circle(mask, (255, 255, 255), (radius, radius), radius)
    mask.set_colorkey((0, 0, 0))  # Make black transparent
    return mask


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

        self.mask = build_round_mask(config.diameter)

    def _render_eye(self, payload: bytes, size: Tuple[int, int]) -> pygame.Surface:
        surface = rgb565_to_surface(payload, *size)
        if surface.get_size() != (self.config.diameter, self.config.diameter):
            surface = pygame.transform.smoothscale(surface, (self.config.diameter, self.config.diameter))
        
        # Create output with background
        output = pygame.Surface((self.config.diameter, self.config.diameter))
        output.fill(self.config.background_color)
        
        # Blit the surface and apply circular mask efficiently
        output.blit(surface, (0, 0))
        output.blit(self.mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        
        return output

    def show_pair(
        self,
        left_payload: bytes,
        right_payload: bytes,
        left_size: Tuple[int, int],
        right_size: Tuple[int, int],
        duration_ms: int,
    ) -> bool:
        events = list(pump_events())
        if should_exit(events):
            return False

        # Fill with background color to show non-circular areas
        self.window.fill(self.config.background_color)
        
        left_surface = self._render_eye(left_payload, left_size)
        right_surface = self._render_eye(right_payload, right_size)
        self.window.blit(left_surface, (0, 0))
        self.window.blit(right_surface, (self.config.diameter + self.config.gap, 0))
        pygame.display.flip()

        pygame.time.wait(max(duration_ms, 16))
        return True
