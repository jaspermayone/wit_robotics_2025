# Linux Setup for Robotics Project

This guide will help Linux users set up and use this robotics project.

## Quick Setup

1. **Make Scripts Executable**
   ```bash
   chmod +x scripts/setup-linux.sh scripts/build-linux.sh scripts/flash-linux.sh scripts/secrets-linux.sh
   ```

2. **Run Setup Script**
   ```bash
   ./scripts/setup-linux.sh
   ```

3. **Apply Environment Variables**
   ```bash
   source ~/.bashrc
   ```

The setup script will:
- Install required packages using your distribution's package manager
- Download the ARM GCC toolchain
- Clone the Raspberry Pi Pico SDK
- Configure environment variables in your .bashrc

## Building the Project

```bash
./scripts/build-linux.sh
```

This will:
- Check if the Pico SDK is installed, download it if needed
- Configure and build the project
- Create the UF2 file in the `build` folder

## Flashing to Pico

1. Put your Pico in bootloader mode:
   - Hold the BOOTSEL button while plugging in USB
   - Release after connecting

2. Flash the firmware:
   ```bash
   ./scripts/flash-linux.sh
   ```

The script will copy the UF2 file to your Pico, which will automatically reboot with the new firmware.

## Managing Secrets

```bash
./scripts/secrets-linux.sh encrypt  # Encrypt secrets.h
./scripts/secrets-linux.sh decrypt  # Decrypt secrets.h.age
```

## Troubleshooting

- **Permission Issues**: Make sure scripts are executable with `chmod +x script.sh`
- **Build Errors**: Ensure all required packages are installed
- **ARM GCC Not Found**: Check that the PATH includes the ARM toolchain
- **Pico Not Detected**: 
  - Ensure you're holding the BOOTSEL button while connecting USB
  - The script checks common mount points, but if your distribution mounts it elsewhere, you may need to modify flash-linux.sh

## Manual Setup (if scripts don't work)

If the automated scripts don't work, you can manually:

1. Install required packages:
   ```bash
   # Ubuntu/Debian
   sudo apt install git build-essential cmake ninja-build python3
   
   # Fedora
   sudo dnf install git gcc gcc-c++ cmake ninja-build python3
   
   # Arch
   sudo pacman -S git base-devel cmake ninja python
   ```

2. Download ARM GCC toolchain from [developer.arm.com](https://developer.arm.com/downloads/-/gnu-rm)

3. Clone Pico SDK:
   ```bash
   git clone --recursive https://github.com/raspberrypi/pico-sdk.git
   ```

4. Set environment variables:
   ```bash
   export PICO_SDK_PATH=/path/to/pico-sdk
   export PATH=$PATH:/path/to/arm-gcc/bin
   ```