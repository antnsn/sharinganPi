# sharinganPi

A project to display GIF animations on dual round GC9A01 displays using a Raspberry Pi Zero 2 W.

## Features

- **GIF Conversion**: Convert animated GIFs to RGB565 frame buffers optimized for GC9A01 displays
- **Desktop Emulator**: Preview animations in circular windows before deploying to hardware
- **Dual Display Support**: Synchronize left and right eye animations
- **Configurable**: Environment-based configuration for frame size, color depth, and processing options

## Hardware

- **Controller**: Raspberry Pi Zero 2 W
- **Displays**: 2× Waveshare 1.28" round LCD modules (GC9A01 driver, 240×240 resolution)
- **Connection**: PH2.0 8-pin headers via SPI

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/sharinganPi.git
cd sharinganPi

# Set up virtual environment and install dependencies
make install

# Activate the virtual environment
source .venv/bin/activate
```

### 2. Prepare GIF Assets

Place your GIF files in the `gifs/` directory:
- `gifs/left.gif` - Animation for the left eye
- `gifs/right.gif` - Animation for the right eye

Convert GIFs to RGB565 frame buffers:

```bash
python scripts/prepare_gif.py gifs/left.gif build/left --preview
python scripts/prepare_gif.py gifs/right.gif build/right --preview
```

**Options:**
- `--size WIDTH HEIGHT` - Target frame size (default: 240 240)
- `--dither` - Apply Floyd-Steinberg dithering
- `--preview` - Generate PNG previews alongside RGB565 files
- `--byteorder little|big` - Endianness for RGB565 output

### 3. Test with Emulator

Preview animations on your desktop:

```bash
python scripts/run_emulator.py build/left build/right --loop
```

**Options:**
- `--loop` - Loop animation indefinitely
- `--diameter N` - Display diameter in pixels (default: 240)
- `--gap N` - Gap between windows (default: 20)
- `--swap` - Swap left/right positions

Press `Esc` or `Q` to exit.

## Configuration

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Available environment variables:

```bash
# Frame size (WIDTH×HEIGHT, WIDTH,HEIGHT, or WIDTH HEIGHT)
SHARINGAN_FRAME_SIZE=240x240

# Output format: true for RGB565 binary, false for PNG
SHARINGAN_RGB565=true

# Byte order for RGB565: little or big
SHARINGAN_BYTEORDER=little

# Enable Floyd-Steinberg dithering
SHARINGAN_DITHER=false

# Generate PNG previews
SHARINGAN_PREVIEW=false
```

## Project Structure

```
sharinganPi/
├── gifs/              # Source GIF animations
├── build/             # Generated frame data
│   ├── left/          # Left eye frames + metadata
│   └── right/         # Right eye frames + metadata
├── sharingan/         # Core Python package
│   └── display.py     # Display drivers and emulator
├── scripts/           # Utility scripts
│   ├── prepare_gif.py # GIF conversion tool
│   └── run_emulator.py # Desktop emulator
├── .env.example       # Configuration template
├── requirements.txt   # Python dependencies
└── pyproject.toml     # Package metadata
```

## Development

### Running Tests

```bash
# TODO: Add test suite
```

### Hardware Deployment

See [docs/WIRING.md](docs/WIRING.md) for complete wiring instructions.

**Quick test on Raspberry Pi:**

```bash
# Enable SPI first (if not already done)
sudo raspi-config
# Interface Options → SPI → Enable

# Run on hardware
python scripts/run_hardware.py build/left build/right --loop
```

**Hardware script options:**
- `--loop` - Loop animation indefinitely
- `--fps N` - Override frame rate
- `--left-spi BUS DEVICE` - Left display SPI (default: 0 0)
- `--right-spi BUS DEVICE` - Right display SPI (default: 0 1)
- `--left-dc PIN` - Left DC GPIO pin (default: 25)
- `--right-dc PIN` - Right DC GPIO pin (default: 23)

Press `Ctrl+C` to stop.

## Roadmap

- [x] GIF to RGB565 conversion
- [x] Desktop emulator with circular display preview
- [x] GC9A01 hardware driver (SPI communication)
- [x] Hardware wiring documentation
- [x] Dual-display synchronization on Pi
- [ ] Interactive controls (sensors/buttons)
- [ ] Configuration file for GIF sets and playback
- [ ] Hardware testing and optimization

## Resources

- [Waveshare 1.28" LCD Module Wiki](https://www.waveshare.com/wiki/1.28inch_LCD_Module)
- [GC9A01 Datasheet](https://www.waveshare.com/w/upload/5/5e/GC9A01A.pdf)

## License

See [LICENSE](LICENSE) for details.
