#!/bin/bash
# Linux build script for robotics project
set -e
cd "$(dirname "$0")"

# Setup tools directory
TOOLS_DIR="$HOME/robotics-tools"
PICO_SDK_DIR="$TOOLS_DIR/pico-sdk"

# Check environment
if [ -z "$PICO_SDK_PATH" ]; then
    echo "PICO_SDK_PATH not set. Checking if Pico SDK is installed locally..."
    
    if [ ! -d "$PICO_SDK_DIR" ]; then
        read -p "Pico SDK not found. Would you like to download it now? (y/n) " DOWNLOAD_SDK
        if [ "$DOWNLOAD_SDK" = "y" ]; then
            # Create tools directory if it doesn't exist
            mkdir -p "$TOOLS_DIR"
            
            # Clone Pico SDK
            echo "Downloading Raspberry Pi Pico SDK..."
            git clone --recursive https://github.com/raspberrypi/pico-sdk.git "$PICO_SDK_DIR"
            
            # Set environment variable for current session
            export PICO_SDK_PATH="$PICO_SDK_DIR"
            echo "Pico SDK downloaded and PICO_SDK_PATH set to $PICO_SDK_PATH"
        else
            echo "Error: PICO_SDK_PATH not set and download declined. Cannot continue."
            exit 1
        fi
    else
        # SDK exists locally but environment variable not set
        export PICO_SDK_PATH="$PICO_SDK_DIR"
        echo "Found existing Pico SDK. Set PICO_SDK_PATH to $PICO_SDK_PATH"
    fi
fi

# Use ARM GCC from tools directory if it exists
ARM_GCC_DIR="$TOOLS_DIR/gcc-arm-none-eabi-10.3-2021.10"
if [ -d "$ARM_GCC_DIR" ]; then
    export PATH="$ARM_GCC_DIR/bin:$PATH"
fi

# Use most cores (leave 2 for system responsiveness)
if command -v nproc &> /dev/null; then
    # Linux-specific way to get CPU count
    TOTAL_CORES=$(nproc)
else
    # Fallback
    TOTAL_CORES=4
fi
JOBS=$((TOTAL_CORES > 2 ? TOTAL_CORES - 2 : 1))

rm -rf build
mkdir build
cd build

# Use Ninja if available (faster than Make), otherwise Make
if command -v ninja &> /dev/null; then
    echo "Building with Ninja..."
    cmake -G Ninja ..
    ninja -j$JOBS
else
    echo "Building with Make..."
    cmake ..
    make -j$JOBS
fi

echo "Build complete! UF2 file is in the build directory."