# sharinganPi

Display animated GIF eyes on dual round GC9A01 displays using a Raspberry Pi Zero 2 W.

Perfect for cosplay helmets, animatronics, or any project needing expressive circular displays.

## Quick Start

### Desktop Preview (No Hardware Required)

```bash
# Install
git clone https://github.com/antnsn/sharinganPi.git
cd sharinganPi
make install
source .venv/bin/activate

# Convert GIFs
python scripts/prepare_gif.py gifs/left.gif build/left --byteorder big --rgb565
python scripts/prepare_gif.py gifs/right.gif build/right --byteorder big --rgb565

# Preview in emulator
python scripts/run_emulator.py build/left build/right --loop
```

### Raspberry Pi Hardware

```bash
# Clone and install
git clone https://github.com/antnsn/sharinganPi.git
cd sharinganPi
make install
source .venv/bin/activate

# Enable SPI
sudo raspi-config  # Interface Options → SPI → Enable

# Convert GIFs (if not done on desktop)
python scripts/prepare_gif.py gifs/left.gif  build/left  --byteorder big --rgb565
python scripts/prepare_gif.py gifs/right.gif build/right --byteorder big --rgb565

# Run on displays
python scripts/run_hardware.py build/left build/right --loop
```

### Auto-Start on Boot (Cosplay Mode)

```bash
sudo cp sharingan.service /etc/systemd/system/
sudo systemctl enable sharingan.service
sudo systemctl start sharingan.service
```

Power on → Eyes animate automatically in ~20 seconds.

## Hardware Requirements

- Raspberry Pi Zero 2 W
- 2× Waveshare 1.28" Round LCD (GC9A01, 240×240)
- MicroSD card (8GB+)
- USB power supply or battery pack (5V, 2A)

## Documentation

- **[Wiring Guide](docs/WIRING.md)** - GPIO pinout and hardware connections
- **[Service Setup](docs/SERVICE.md)** - Auto-start configuration for cosplay/embedded use
- **[Configuration](docs/CONFIGURATION.md)** - Environment variables and customization options

## Features

✅ GIF to RGB565 conversion with letterboxing  
✅ Circular display emulator for desktop preview  
✅ Dual-display hardware driver with SPI  
✅ Systemd service for auto-start on boot  
✅ Configurable via environment variables  
✅ ~20 second boot time for instant cosplay use

## Project Status

- [x] GIF conversion pipeline
- [x] Desktop emulator
- [x] Hardware driver (GC9A01/SPI)
- [x] Wiring documentation
- [x] Auto-start service
- [ ] Interactive controls (buttons/sensors)
- [ ] Multiple animation sets

## License

See [LICENSE](LICENSE) for details.
