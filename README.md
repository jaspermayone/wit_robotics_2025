# Monster Book of Monsters

Pico 2 W battlebot with Bluetooth controller support and WiFi dashboard.

## Cross-Platform Setup

This project supports Windows, macOS, and Linux users:

### Windows Users

Follow instructions in [WINDOWS.md](WINDOWS.md)

- Use `scripts/setup.bat` or `scripts/setup-windows.ps1` to install dependencies
- Use `scripts/build.bat` or `scripts/build.ps1` to build the project
- Use `scripts/flash.bat` or `scripts/flash.ps1` to flash your Pico

### macOS Users

- Use `scripts/build.sh` to build the project
- Use `scripts/flash.sh` to flash your Pico
- Use `scripts/secrets.sh` to manage secrets

### Linux Users

Follow instructions in [LINUX.md](LINUX.md)

- Use `scripts/setup-linux.sh` to install dependencies
- Use `scripts/build-linux.sh` to build the project
- Use `scripts/flash-linux.sh` to flash your Pico
- Use `scripts/secrets-linux.sh` to manage secrets

## Pinout

```
                        Pico 2 W
                    ┌───────────────┐
            GP0  ←──┤ 1          40 ├── VBUS
            GP1  ←──┤ 2          39 ├── VSYS
            GND  ───┤ 3          38 ├── GND
            GP2  ←──┤ 4          37 ├── 3V3_EN
            GP3  ←──┤ 5          36 ├── 3V3
            GP4  ←──┤ 6          35 ├── ADC_VREF
            GP5  ───┤ 7          34 ├── GP28
            GND  ───┤ 8          33 ├── GND
            GP6  ───┤ 9          32 ├── GP27
            GP7  ───┤ 10         31 ├── GP26  ←── Battery ADC
            GP8  ───┤ 11         30 ├── RUN
            GP9  ───┤ 12         29 ├── GP22
            GND  ───┤ 13         28 ├── GND
            GP10 ───┤ 14         27 ├── GP21
            GP11 ───┤ 15         26 ├── GP20
            GP12 ───┤ 16         25 ├── GP19
            GP13 ───┤ 17         24 ├── GP18
            GND  ───┤ 18         23 ├── GND
            GP14 ───┤ 19         22 ├── GP17
            GP15 ───┤ 20         21 ├── GP16
                    └───────────────┘
```

### Motor Connections

| Pin  | Function          | Wire To                    |
|------|-------------------|----------------------------|
| GP0  | Left Front Motor  | ESC signal (white/yellow)  |
| GP1  | Right Front Motor | ESC signal (white/yellow)  |
| GP2  | Left Back Motor   | ESC signal (white/yellow)  |
| GP3  | Right Back Motor  | ESC signal (white/yellow)  |
| GP4  | Weapon Motor      | ESC signal (white/yellow)  |
| GP26 | Battery Voltage   | Voltage divider output     |
| GND  | Common Ground     | All ESC grounds            |

### ESC Wiring

Each ESC has 3 wires:
- **Signal** (white/yellow) → Connect to GPIO pin
- **Ground** (black/brown) → Connect to Pico GND
- **Power** (red) → Leave disconnected (or power Pico from ONE ESC's BEC)

### Power

- ESCs powered directly from battery (3S LiPo)
- Pico powered via USB or from one ESC's BEC (5V to VSYS)

## Connecting Your Pico

To put your Pico in bootloader mode (needed for flashing):

1. Hold the BOOTSEL button
2. Connect USB while holding the button
3. Release the button after connecting

The flash scripts will automatically detect and flash your Pico.