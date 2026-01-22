# Windows Setup for Robotics Project

This guide will help Windows users set up and use this robotics project.

## Quick Setup

**Run Setup Script**
   - Right-click on Windows Start menu and select "Windows PowerShell (Admin)"
   - Navigate to the project folder: `cd path\to\project`
   - Run: `Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process`
   - Run: `.\scripts\setup-windows.ps1`
   - Restart your terminal after setup completes

## Building the Project

- Open PowerShell in the project directory
- Run: `.\scripts\build.ps1`

This will:
- Check if the Pico SDK is installed, download it if needed
- Configure and build the project
- Create the UF2 file in the `build` folder

## Flashing to Pico

1. Put your Pico in bootloader mode:
   - Hold the BOOTSEL button while plugging in USB
   - Release after connecting

2. Flash the firmware:
   - Run: `.\scripts\flash.ps1`

The script will copy the UF2 file to your Pico, which will automatically reboot with the new firmware.

## Troubleshooting

- **"Not Digitally Signed" Error**: Run `Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process` before running scripts
- **Build Errors**: Check that all build tools are properly installed via the setup script
- **Pico Not Detected**: Ensure you're holding the BOOTSEL button while connecting USB
- **Missing Tools**: Run the setup script again to install any missing components

## Manual Setup (if scripts don't work)

If the automated scripts don't work, you can manually:

1. Install ARM GCC toolchain from [developer.arm.com](https://developer.arm.com/downloads/-/gnu-rm)
2. Clone Pico SDK: `git clone --recursive https://github.com/raspberrypi/pico-sdk.git`
3. Install CMake from [cmake.org](https://cmake.org/download/)
4. Set environment variables:
   - `PICO_SDK_PATH` to point to your Pico SDK location
   - Add ARM GCC bin directory to PATH