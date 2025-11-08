# Configuration Guide

## Environment Variables

SharinganPi uses environment variables for configuration. Create a `.env` file in the project root:

```bash
cp .env.example .env
```

### Available Variables

#### Frame Processing

**`SHARINGAN_FRAME_SIZE`**
- Format: `WIDTHxHEIGHT`, `WIDTH,HEIGHT`, or `WIDTH HEIGHT`
- Default: `240x240`
- Example: `SHARINGAN_FRAME_SIZE=240x240`

Controls the output frame dimensions. Must match your display resolution (240×240 for GC9A01).

**`SHARINGAN_RGB565`**
- Values: `true` or `false`
- Default: `true`
- Example: `SHARINGAN_RGB565=true`

When `true`, outputs binary RGB565 files for hardware. When `false`, outputs PNG files for inspection.

**`SHARINGAN_BYTEORDER`**
- Values: `little` or `big`
- Default: `little`
- Example: `SHARINGAN_BYTEORDER=little`

Byte order for RGB565 output. GC9A01 uses little-endian, so keep this as `little` unless you have a specific reason to change it.

**`SHARINGAN_DITHER`**
- Values: `true` or `false`
- Default: `false`
- Example: `SHARINGAN_DITHER=false`

Enable Floyd-Steinberg dithering during RGB565 conversion. Can improve color gradients but may add noise to smooth areas.

**`SHARINGAN_PREVIEW`**
- Values: `true` or `false`
- Default: `false`
- Example: `SHARINGAN_PREVIEW=true`

Generate PNG preview files alongside RGB565 output. Useful for debugging frame conversion.

## Command-Line Options

### GIF Conversion (`prepare_gif.py`)

```bash
python scripts/prepare_gif.py INPUT OUTPUT [OPTIONS]
```

**Arguments:**
- `INPUT` - Path to source GIF file
- `OUTPUT` - Directory for output frames

**Options:**
- `--size WIDTH HEIGHT` - Override frame size (default: 240 240)
- `--dither` - Enable dithering
- `--preview` - Generate PNG previews
- `--byteorder little|big` - Set byte order (default: little)
- `--png` - Output PNG instead of RGB565

**Examples:**

```bash
# Basic conversion
python scripts/prepare_gif.py gifs/left.gif build/left

# With dithering and previews
python scripts/prepare_gif.py gifs/left.gif build/left --dither --preview

# Custom size
python scripts/prepare_gif.py gifs/left.gif build/left --size 200 200
```

### Desktop Emulator (`run_emulator.py`)

```bash
python scripts/run_emulator.py LEFT RIGHT [OPTIONS]
```

**Arguments:**
- `LEFT` - Directory with left eye frames
- `RIGHT` - Directory with right eye frames

**Options:**
- `--loop` - Loop animation indefinitely
- `--diameter N` - Display diameter in pixels (default: 240)
- `--gap N` - Gap between windows in pixels (default: 20)
- `--swap` - Swap left/right positions

**Examples:**

```bash
# Basic preview
python scripts/run_emulator.py build/left build/right --loop

# Larger preview windows
python scripts/run_emulator.py build/left build/right --diameter 400 --gap 50

# Swap sides for testing
python scripts/run_emulator.py build/left build/right --swap
```

### Hardware Runner (`run_hardware.py`)

```bash
python scripts/run_hardware.py LEFT RIGHT [OPTIONS]
```

**Arguments:**
- `LEFT` - Directory with left eye frames
- `RIGHT` - Directory with right eye frames

**Options:**
- `--loop` - Loop animation indefinitely
- `--fps N` - Override frame rate
- `--left-spi BUS DEVICE` - Left display SPI (default: 0 0)
- `--right-spi BUS DEVICE` - Right display SPI (default: 0 1)
- `--left-dc PIN` - Left DC GPIO pin (default: 25)
- `--right-dc PIN` - Right DC GPIO pin (default: 23)
- `--left-rst PIN` - Left RST GPIO pin (default: 27)
- `--right-rst PIN` - Right RST GPIO pin (default: 22)
- `--left-bl PIN` - Left backlight GPIO pin (default: 24)
- `--right-bl PIN` - Right backlight GPIO pin (default: 18)

**Examples:**

```bash
# Basic hardware run
python scripts/run_hardware.py build/left build/right --loop

# Custom frame rate
python scripts/run_hardware.py build/left build/right --loop --fps 30

# Custom GPIO pins
python scripts/run_hardware.py build/left build/right \
  --left-dc 25 --right-dc 23 \
  --left-rst 27 --right-rst 22
```

## Display Settings

### Rotation

The GC9A01 driver supports 0°, 90°, 180°, and 270° rotation. Modify in `sharingan/gc9a01.py`:

```python
left_display = GC9A01(
    spi_bus=0,
    spi_device=0,
    dc_pin=25,
    rotation=0  # Change to 90, 180, or 270
)
```

### SPI Speed

Default: 60 MHz. Reduce if you experience display artifacts:

```python
# In sharingan/gc9a01.py, __init__ method
self.spi.max_speed_hz = 30000000  # 30 MHz
```

### Backlight Control

Control backlight programmatically:

```python
display.set_backlight(True)   # On
display.set_backlight(False)  # Off
```

Or via GPIO directly (BCM pin 24 for left, 18 for right):

```bash
# Turn on
gpio -g write 24 1

# Turn off
gpio -g write 24 0
```

## Performance Tuning

### Frame Rate

GIF frame timing is preserved by default. Override with `--fps`:

```bash
# Force 30 FPS
python scripts/run_hardware.py build/left build/right --fps 30
```

### Memory Usage

Each 240×240 RGB565 frame is 115,200 bytes. With 224 frames (your current GIFs):
- Total memory: ~25 MB per eye
- Pi Zero 2 W has 512 MB RAM - plenty of headroom

### Boot Time Optimization

See [SERVICE.md](SERVICE.md) for boot time reduction techniques.

## Troubleshooting

### Colors Look Wrong

- Check byte order: GC9A01 uses little-endian
- Try enabling dithering: `--dither`
- Verify source GIF color depth

### Animation Too Fast/Slow

- Check GIF frame timing in metadata.json
- Override with `--fps` flag
- Verify SPI speed isn't too slow

### Frames Look Stretched/Cropped

- Verify source GIF dimensions
- Check `--size` parameter matches 240×240
- Review letterboxing in preview mode

### Display Artifacts

- Reduce SPI speed from 60 MHz to 30 MHz
- Check wiring connections
- Ensure proper grounding

## Advanced Configuration

### Custom Color Profiles

Modify RGB565 conversion in `scripts/prepare_gif.py`:

```python
# Adjust color channel bit depths
r = (value >> 11) & 0x1F  # 5 bits red
g = (value >> 5) & 0x3F   # 6 bits green
b = value & 0x1F          # 5 bits blue
```

### Multiple Animation Sets

Organize animations by theme:

```
animations/
├── normal/
│   ├── left/
│   └── right/
├── activated/
│   ├── left/
│   └── right/
└── mangekyou/
    ├── left/
    └── right/
```

Switch via symlinks or service modification (see [SERVICE.md](SERVICE.md)).

## Configuration Files

### `.env` Template

```bash
# Frame conversion settings
SHARINGAN_FRAME_SIZE=240x240
SHARINGAN_RGB565=true
SHARINGAN_BYTEORDER=little
SHARINGAN_DITHER=false
SHARINGAN_PREVIEW=false
```

### Service Configuration

Edit `/etc/systemd/system/sharingan.service` to customize service behavior. See [SERVICE.md](SERVICE.md) for details.

## References

- [Pillow Documentation](https://pillow.readthedocs.io/)
- [GC9A01 Datasheet](https://www.waveshare.com/w/upload/5/5e/GC9A01A.pdf)
- [RGB565 Format](https://en.wikipedia.org/wiki/High_color)
