# Running as a System Service

For cosplay or embedded use, you can run Sharingan as a systemd service that starts automatically on boot.

## Installation

### 1. Clone and Install on Raspberry Pi

```bash
cd /home/pi
git clone https://github.com/antnsn/sharinganPi.git
cd sharinganPi
make install
```

### 2. Prepare Your Animations

```bash
source .venv/bin/activate
python scripts/prepare_gif.py gifs/left.gif build/left
python scripts/prepare_gif.py gifs/right.gif build/right
```

### 3. Test Manually First

```bash
python scripts/run_hardware.py build/left build/right --loop
```

Press `Ctrl+C` to stop. If it works, proceed to service setup.

### 4. Install the Service

```bash
# Copy service file to systemd
sudo cp sharingan.service /etc/systemd/system/

# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable sharingan.service

# Start the service now
sudo systemctl start sharingan.service
```

## Service Management

### Check Status

```bash
sudo systemctl status sharingan.service
```

### View Logs

```bash
# Recent logs
sudo journalctl -u sharingan.service -n 50

# Follow logs in real-time
sudo journalctl -u sharingan.service -f

# Logs since last boot
sudo journalctl -u sharingan.service -b
```

### Control the Service

```bash
# Start
sudo systemctl start sharingan.service

# Stop
sudo systemctl stop sharingan.service

# Restart
sudo systemctl restart sharingan.service

# Disable auto-start on boot
sudo systemctl disable sharingan.service

# Re-enable auto-start
sudo systemctl enable sharingan.service
```

## Customization

Edit the service file to customize behavior:

```bash
sudo nano /etc/systemd/system/sharingan.service
```

### Common Customizations

**Change animation paths:**

```ini
ExecStart=/home/pi/sharinganPi/.venv/bin/python /home/pi/sharinganPi/scripts/run_hardware.py /path/to/left /path/to/right --loop
```

**Add frame rate control:**

```ini
ExecStart=/home/pi/sharinganPi/.venv/bin/python /home/pi/sharinganPi/scripts/run_hardware.py /home/pi/sharinganPi/build/left /home/pi/sharinganPi/build/right --loop --fps 30
```

**Change GPIO pins:**

```ini
ExecStart=/home/pi/sharinganPi/.venv/bin/python /home/pi/sharinganPi/scripts/run_hardware.py /home/pi/sharinganPi/build/left /home/pi/sharinganPi/build/right --loop --left-dc 25 --right-dc 23
```

After editing, reload and restart:

```bash
sudo systemctl daemon-reload
sudo systemctl restart sharingan.service
```

## Power Management

### Auto-start on Power Up

The service is configured to start automatically when the Pi boots. Simply power on the Pi and the eyes will start animating.

### Graceful Shutdown

To safely power down:

```bash
sudo shutdown -h now
```

Or use a physical button (requires additional GPIO setup).

### Quick Power Cycle

For cosplay use, you can simply:

1. Power on the Pi (via battery pack or USB)
2. Wait ~30 seconds for boot
3. Eyes start animating automatically
4. Power off when done (service stops gracefully)

## Troubleshooting

### Service won't start

Check logs:

```bash
sudo journalctl -u sharingan.service -n 100
```

Common issues:

- **SPI not enabled**: Run `sudo raspi-config` → Interface Options → SPI
- **Wrong paths**: Verify paths in service file match your installation
- **Permissions**: Ensure `pi` user owns the files
- **Missing frames**: Check `build/left` and `build/right` exist

### Service starts but displays don't work

```bash
# Check if service is running
sudo systemctl status sharingan.service

# View real-time logs
sudo journalctl -u sharingan.service -f

# Test manually
sudo systemctl stop sharingan.service
cd /home/pi/sharinganPi
source .venv/bin/activate
python scripts/run_hardware.py build/left build/right --loop
```

### Update animations without rebooting

```bash
# Stop service
sudo systemctl stop sharingan.service

# Update frames
source .venv/bin/activate
python scripts/prepare_gif.py gifs/new_left.gif build/left
python scripts/prepare_gif.py gifs/new_right.gif build/right

# Restart service
sudo systemctl start sharingan.service
```

## Boot Time Optimization

To reduce boot time for cosplay use:

### 1. Disable Unnecessary Services

```bash
# Disable WiFi if not needed
sudo systemctl disable wpa_supplicant.service

# Disable Bluetooth if not needed
sudo systemctl disable bluetooth.service

# Disable GUI (if using Lite version, already disabled)
sudo systemctl set-default multi-user.target
```

### 2. Enable Fast Boot

Edit `/boot/config.txt`:

```bash
sudo nano /boot/config.txt
```

Add:

```
# Fast boot
boot_delay=0
disable_splash=1
```

### 3. Optimize Service Start

Edit service file to start earlier:

```ini
[Unit]
Description=Sharingan Eye Display Service
After=local-fs.target
DefaultDependencies=no
```

Expected boot time: **15-25 seconds** from power-on to animation start.

## Battery Power Considerations

For portable cosplay use:

- **Recommended**: USB battery pack (5V, 2A minimum)
- **Runtime**: ~4-6 hours with 10,000mAh battery
- **Power consumption**: ~500mA average (both displays + Pi)
- **Low battery**: Service will stop when Pi shuts down (no data corruption)

### Power Button (Optional)

Add a shutdown button to GPIO 3 (Pin 5):

- Pressing button triggers safe shutdown
- No need to SSH or remove power unsafely

See [Raspberry Pi documentation](https://www.raspberrypi.com/documentation/computers/configuration.html#gpio-shutdown) for setup.

## Advanced: Multiple Animation Sets

Create a script to switch between different animations:

```bash
#!/bin/bash
# switch_animation.sh

ANIM=$1
sudo systemctl stop sharingan.service
cp -r /home/pi/sharinganPi/animations/$ANIM/left/* /home/pi/sharinganPi/build/left/
cp -r /home/pi/sharinganPi/animations/$ANIM/right/* /home/pi/sharinganPi/build/right/
sudo systemctl start sharingan.service
```

Usage:

```bash
./switch_animation.sh normal
./switch_animation.sh activated
./switch_animation.sh mangekyou
```

## Resources

- [systemd Service Documentation](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [Raspberry Pi Auto-start Guide](https://www.raspberrypi.com/documentation/computers/using_linux.html#the-systemd-daemon)
