"""GC9A01 round LCD driver for Raspberry Pi via SPI."""

from __future__ import annotations

import time
from typing import Optional

try:
    import spidev
    import RPi.GPIO as GPIO
    HAS_HARDWARE = True
except ImportError:
    HAS_HARDWARE = False
    spidev = None
    GPIO = None


# GC9A01 Commands
CMD_SLPOUT = 0x11  # Sleep Out
CMD_DISPON = 0x29  # Display ON
CMD_CASET = 0x2A   # Column Address Set
CMD_RASET = 0x2B   # Row Address Set
CMD_RAMWR = 0x2C   # Memory Write
CMD_MADCTL = 0x36  # Memory Data Access Control
CMD_COLMOD = 0x3A  # Interface Pixel Format
CMD_INVON = 0x21   # Display Inversion ON


class GC9A01:
    """Driver for GC9A01 240x240 round LCD display."""

    def __init__(
        self,
        spi_bus: int = 0,
        spi_device: int = 0,
        dc_pin: int = 25,
        rst_pin: Optional[int] = 27,
        bl_pin: Optional[int] = 24,
        width: int = 240,
        height: int = 240,
        rotation: int = 0,
    ):
        """
        Initialize GC9A01 display.

        Args:
            spi_bus: SPI bus number (0 or 1)
            spi_device: SPI device/CS number (0 or 1)
            dc_pin: Data/Command GPIO pin (BCM numbering)
            rst_pin: Reset GPIO pin (optional)
            bl_pin: Backlight GPIO pin (optional)
            width: Display width in pixels
            height: Display height in pixels
            rotation: Display rotation (0, 90, 180, 270)
        """
        if not HAS_HARDWARE:
            raise RuntimeError(
                "Hardware libraries not available. Install spidev and RPi.GPIO on Raspberry Pi."
            )

        self.width = width
        self.height = height
        self.rotation = rotation
        self.dc_pin = dc_pin
        self.rst_pin = rst_pin
        self.bl_pin = bl_pin

        # Initialize GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.dc_pin, GPIO.OUT)

        if self.rst_pin is not None:
            GPIO.setup(self.rst_pin, GPIO.OUT)
            GPIO.output(self.rst_pin, GPIO.HIGH)

        if self.bl_pin is not None:
            GPIO.setup(self.bl_pin, GPIO.OUT)
            GPIO.output(self.bl_pin, GPIO.HIGH)

        # Initialize SPI
        self.spi = spidev.SpiDev()
        self.spi.open(spi_bus, spi_device)
        self.spi.max_speed_hz = 60000000  # 60 MHz
        self.spi.mode = 0

        # Initialize display
        self._init_display()

    def _write_command(self, cmd: int) -> None:
        """Send command byte to display."""
        GPIO.output(self.dc_pin, GPIO.LOW)
        self.spi.writebytes([cmd])

    def _write_data(self, data: bytes | list[int]) -> None:
        """Send data bytes to display."""
        GPIO.output(self.dc_pin, GPIO.HIGH)
        if isinstance(data, bytes):
            self.spi.writebytes(list(data))
        else:
            self.spi.writebytes(data)

    def _reset(self) -> None:
        """Hardware reset the display."""
        if self.rst_pin is None:
            return
        GPIO.output(self.rst_pin, GPIO.HIGH)
        time.sleep(0.01)
        GPIO.output(self.rst_pin, GPIO.LOW)
        time.sleep(0.01)
        GPIO.output(self.rst_pin, GPIO.HIGH)
        time.sleep(0.12)

    def _init_display(self) -> None:
        """Initialize GC9A01 display with configuration sequence."""
        self._reset()

        def cmd(command: int, data: list[int] | None = None) -> None:
            self._write_command(command)
            if data is not None:
                self._write_data(data)

        cmd(0xEF)
        cmd(0xEB, [0x14])

        cmd(0xFE)
        cmd(0xEF)

        cmd(0xEB, [0x14])

        cmd(0x84, [0x40])
        cmd(0x85, [0xFF])
        cmd(0x86, [0xFF])
        cmd(0x87, [0xFF])

        cmd(0x88, [0x0A])
        cmd(0x89, [0x21])
        cmd(0x8A, [0x00])
        cmd(0x8B, [0x80])
        cmd(0x8C, [0x01])
        cmd(0x8D, [0x01])
        cmd(0x8E, [0xFF])
        cmd(0x8F, [0xFF])

        cmd(0xB6, [0x00, 0x20])

        # Interface Pixel Format: 16-bit RGB565
        cmd(CMD_COLMOD, [0x05])

        cmd(0x90, [0x08, 0x08, 0x08, 0x08])

        cmd(0xBD, [0x06])
        cmd(0xBC, [0x00])

        cmd(0xFF, [0x60, 0x01, 0x04])

        cmd(0xC3, [0x13])
        cmd(0xC4, [0x13])

        cmd(0xC9, [0x22])
        cmd(0xBE, [0x11])

        cmd(0xE1, [0x10, 0x0E])

        cmd(0xDF, [0x21, 0x0C, 0x02])

        cmd(0xF0, [0x45, 0x09, 0x08, 0x08, 0x26, 0x2A])
        cmd(0xF1, [0x43, 0x70, 0x72, 0x36, 0x37, 0x6F])
        cmd(0xF2, [0x45, 0x09, 0x08, 0x08, 0x26, 0x2A])
        cmd(0xF3, [0x43, 0x70, 0x72, 0x36, 0x37, 0x6F])

        cmd(0xED, [0x1B, 0x0B])

        cmd(0xAE, [0x77])
        cmd(0xCD, [0x63])

        cmd(0x70, [0x07, 0x07, 0x04, 0x0E, 0x0F, 0x09, 0x07, 0x08, 0x03])

        cmd(0xE8, [0x34])

        cmd(
            0x62,
            [
                0x18,
                0x0D,
                0x71,
                0xED,
                0x70,
                0x70,
                0x18,
                0x0F,
                0x71,
                0xEF,
                0x70,
                0x70,
            ],
        )

        cmd(
            0x63,
            [
                0x18,
                0x11,
                0x71,
                0xF1,
                0x70,
                0x70,
                0x18,
                0x13,
                0x71,
                0xF3,
                0x70,
                0x70,
            ],
        )

        cmd(0x64, [0x28, 0x29, 0xF1, 0x01, 0xF1, 0x00, 0x07])

        cmd(
            0x66,
            [
                0x3C,
                0x00,
                0xCD,
                0x67,
                0x45,
                0x45,
                0x10,
                0x00,
                0x00,
                0x00,
            ],
        )

        cmd(
            0x67,
            [
                0x00,
                0x3C,
                0x00,
                0x00,
                0x00,
                0x01,
                0x54,
                0x10,
                0x32,
                0x98,
            ],
        )

        cmd(0x74, [0x10, 0x85, 0x80, 0x00, 0x00, 0x4E, 0x00])

        cmd(0x98, [0x3E, 0x07])

        # Tearing effect line + display inversion ON (matches CircuitPython GC9A01A)
        cmd(0x35)
        cmd(CMD_INVON)

        # Sleep out & display ON
        self._write_command(CMD_SLPOUT)
        time.sleep(0.12)
        self._write_command(CMD_DISPON)
        time.sleep(0.02)

        # Memory Data Access Control (BGR color order, no mirroring)
        self._write_command(CMD_MADCTL)
        self._write_data([0x08])

    def set_window(self, x0: int, y0: int, x1: int, y1: int) -> None:
        """Set the pixel address window for writing."""
        # Column Address Set
        self._write_command(CMD_CASET)
        self._write_data([x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF])

        # Row Address Set
        self._write_command(CMD_RASET)
        self._write_data([y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF])

        # Memory Write
        self._write_command(CMD_RAMWR)

    def display_frame(self, frame_data: bytes) -> None:
        """
        Display a full frame of RGB565 data.

        Args:
            frame_data: RGB565 pixel data (width * height * 2 bytes)
        """
        expected_size = self.width * self.height * 2
        if len(frame_data) != expected_size:
            raise ValueError(
                f"Frame data size mismatch: expected {expected_size}, got {len(frame_data)}"
            )

        # Set window to full screen
        self.set_window(0, 0, self.width - 1, self.height - 1)

        # Write frame data in chunks for better performance
        chunk_size = 4096
        for i in range(0, len(frame_data), chunk_size):
            chunk = frame_data[i : i + chunk_size]
            self._write_data(chunk)

    def clear(self, color: tuple[int, int, int] = (0, 0, 0)) -> None:
        """Clear display to a solid color."""
        r, g, b = color
        # Convert RGB888 to RGB565
        rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        pixel_bytes = bytes([rgb565 >> 8, rgb565 & 0xFF])
        frame_data = pixel_bytes * (self.width * self.height)
        self.display_frame(frame_data)

    def set_backlight(self, state: bool) -> None:
        """Control backlight on/off."""
        if self.bl_pin is not None:
            GPIO.output(self.bl_pin, GPIO.HIGH if state else GPIO.LOW)

    def cleanup(self) -> None:
        """Clean up GPIO and SPI resources."""
        if self.bl_pin is not None:
            GPIO.output(self.bl_pin, GPIO.LOW)
        self.spi.close()
        GPIO.cleanup()
