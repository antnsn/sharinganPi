# Hardware Wiring Guide

## Components

- **Raspberry Pi Zero 2 W**
- **2× Waveshare 1.28" Round LCD Module** (GC9A01 driver)
- **PH2.0 8-pin cables** (included with displays)

## Display Pinout (PH2.0 8-pin Header)

Each Waveshare 1.28" LCD module has the following pinout:

| Pin | Signal | Description |
|-----|--------|-------------|
| 1   | VCC    | Power (3.3V) |
| 2   | GND    | Ground |
| 3   | DIN    | SPI MOSI (Data In) |
| 4   | CLK    | SPI SCLK (Clock) |
| 5   | CS     | SPI Chip Select |
| 6   | DC     | Data/Command Select |
| 7   | RST    | Reset (optional) |
| 8   | BL     | Backlight Control (optional) |

## Raspberry Pi GPIO Pinout (BCM Numbering)

### Left Eye Display

| Display Pin | Signal | Pi GPIO (BCM) | Physical Pin |
|-------------|--------|---------------|--------------|
| VCC         | 3.3V   | 3.3V          | Pin 1 or 17  |
| GND         | GND    | GND           | Pin 6, 9, 14, 20, 25, 30, 34, 39 |
| DIN         | MOSI   | GPIO 10       | Pin 19       |
| CLK         | SCLK   | GPIO 11       | Pin 23       |
| CS          | CE0    | GPIO 8        | Pin 24       |
| DC          | GPIO   | GPIO 25       | Pin 22       |
| RST         | GPIO   | GPIO 27       | Pin 13       |
| BL          | GPIO   | GPIO 24       | Pin 18       |

### Right Eye Display

| Display Pin | Signal | Pi GPIO (BCM) | Physical Pin |
|-------------|--------|---------------|--------------|
| VCC         | 3.3V   | 3.3V          | Pin 1 or 17  |
| GND         | GND    | GND           | Pin 6, 9, 14, 20, 25, 30, 34, 39 |
| DIN         | MOSI   | GPIO 10       | Pin 19       |
| CLK         | SCLK   | GPIO 11       | Pin 23       |
| CS          | CE1    | GPIO 7        | Pin 26       |
| DC          | GPIO   | GPIO 23       | Pin 16       |
| RST         | GPIO   | GPIO 22       | Pin 15       |
| BL          | GPIO   | GPIO 18       | Pin 12       |

## Wiring Notes

### Shared SPI Bus

Both displays share the same SPI bus (MOSI and SCLK), which allows efficient communication:
- **MOSI (GPIO 10)** - Shared data line
- **SCLK (GPIO 11)** - Shared clock line

### Individual Control Signals

Each display has independent control signals:
- **CS (Chip Select)** - Selects which display receives data (CE0 for left, CE1 for right)
- **DC (Data/Command)** - Separate GPIO for each display
- **RST (Reset)** - Separate GPIO for each display (optional but recommended)
- **BL (Backlight)** - Separate GPIO for each display (optional)

### Power Considerations

- Both displays run on **3.3V** (NOT 5V!)
- Total current draw: ~200mA with backlight on (both displays)
- Pi Zero 2 W can supply sufficient current via 3.3V pins
- Use multiple GND connections for better grounding

## Enable SPI on Raspberry Pi

Before using the displays, enable SPI:

```bash
sudo raspi-config
# Navigate to: Interface Options → SPI → Enable
```

Or edit `/boot/config.txt`:

```bash
dtparam=spi=on
```

Reboot after enabling SPI.

## Verify SPI Devices

Check that SPI devices are available:

```bash
ls -l /dev/spidev*
```

You should see:
```
/dev/spidev0.0  # Left display (CE0)
/dev/spidev0.1  # Right display (CE1)
```

## Connection Diagram

```
Raspberry Pi Zero 2 W
┌─────────────────────────────────┐
│                                 │
│  3.3V ──┬─────────────────────┐ │
│         │                     │ │
│  GND ───┼──┬──────────────┐   │ │
│         │  │              │   │ │
│  MOSI ──┼──┼──┬───────┐   │   │ │
│  SCLK ──┼──┼──┼──┬────│───│───│─┤
│         │  │  │  │    │   │   │ │
│  CE0 ───┼──│──│──│────│───│───│─┤ Left Eye
│  GPIO25─┼──│──│──│────│───│───│─┤
│  GPIO27─┼──│──│──│────│───│───│─┤
│  GPIO24─┼──│──│──│────│───│───│─┤
│         │  │  │  │    │   │   │ │
│  CE1 ───┼──│──│──│────│───│───│─┤ Right Eye
│  GPIO23─┼──│──│──│────│───│───│─┤
│  GPIO22─┼──│──│──│────│───│───│─┤
│  GPIO18─┼──│──│──│────│───│───│─┤
│         │  │  │  │    │   │   │ │
└─────────┴──┴──┴──┴────┴───┴───┴─┘
          │  │  │  │    │   │   │
          VCC│  │  │    │   │   │
          GND│  │  │    │   │   │
          MOSI │  │    │   │   │
          SCLK │  │    │   │   │
             CS  DC   RST BL  │
                              │
          (Same for right eye)
```

## Testing

Test individual displays:

```python
from sharingan.gc9a01 import GC9A01

# Test left display
left = GC9A01(spi_bus=0, spi_device=0, dc_pin=25, rst_pin=27, bl_pin=24)
left.clear((255, 0, 0))  # Red
left.cleanup()

# Test right display
right = GC9A01(spi_bus=0, spi_device=1, dc_pin=23, rst_pin=22, bl_pin=18)
right.clear((0, 0, 255))  # Blue
right.cleanup()
```

## Troubleshooting

### Display not responding
- Check SPI is enabled: `lsmod | grep spi`
- Verify wiring connections
- Ensure 3.3V power (NOT 5V)
- Check CS pin matches SPI device number

### Incorrect colors or garbage
- Verify MOSI/SCLK connections
- Check SPI speed (try reducing from 60MHz to 30MHz)
- Ensure proper grounding

### Backlight not working
- Check BL pin connection
- Verify GPIO pin is set HIGH
- Some modules have hardware backlight control

## References

- [Waveshare 1.28" LCD Module Wiki](https://www.waveshare.com/wiki/1.28inch_LCD_Module)
- [GC9A01 Datasheet](https://www.waveshare.com/w/upload/5/5e/GC9A01A.pdf)
- [Raspberry Pi GPIO Pinout](https://pinout.xyz/)
