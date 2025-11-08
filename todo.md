# Development TODOs

## Hardware decisions
- Confirmed controller: Raspberry Pi Zero 2 W
- Document PH2.0 8-pin wiring map between module header and Pi GPIO (power, SPI lines, backlight).
- Verify display/backlight power rails (3.3 V vs 5 V) and SPI level compatibility.
- Confirm display wiring scheme (shared SPI vs. dual SPI) and backlight control.

## Asset preparation
- Select/create GIF animations for each eye.
- Convert/resize to 240×240 RGB565-friendly frames; verify frame timing metadata.

## Playback implementation
- Integrate GIF decoder (e.g., AnimatedGIF for ESP32 or Pillow/SDL on Pi).
- Stream frames line-by-line to each GC9A01 display; ensure non-blocking timing.
- Add configuration for dual-display synchronization (shared clock or independent).
- Evaluate Waveshare sample drivers (lgpio-based C/Python) to reuse or port initialization sequence.

## Emulation layer
- Abstract display driver calls behind an interface.
- Implement desktop mock (SDL/Python/Qt) that renders frames in windows for rapid iteration.
- Add build target or script to run animation logic against the emulator.

## Testing & optimization
- Profile SPI throughput and frame rate; tune SPI clock/DMA or rendering loop.
- Validate memory usage (frame buffers, GIF decoder workspace).
- Regression-test blink/animation timing on hardware and emulator.

## Deployment polish
- Create configuration file for selecting GIF sets and playback speed.
- Document wiring, build instructions, and emulation workflow in README.
- Optionally add user hooks (sensors/buttons) for interactive control.
- Archive Waveshare datasheets, pinout diagrams, and demo code in repo resources.

## References
- [Waveshare 1.28" LCD Module Wiki](https://www.waveshare.com/wiki/1.28inch_LCD_Module)