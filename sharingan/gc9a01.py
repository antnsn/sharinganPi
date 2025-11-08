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

        # Sleep out
        self._write_command(CMD_SLPOUT)
        time.sleep(0.12)

        # Interface Pixel Format: 16-bit RGB565
        self._write_command(CMD_COLMOD)
        self._write_data([0x05])

        # Memory Data Access Control (rotation)
        self._write_command(CMD_MADCTL)
        rotation_values = {0: 0x00, 90: 0x60, 180: 0xC0, 270: 0xA0}
        self._write_data([rotation_values.get(self.rotation, 0x00)])

        # Display Inversion ON (common for GC9A01)
        self._write_command(CMD_INVON)

        # Display ON
        self._write_command(CMD_DISPON)
        time.sleep(0.01)

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
