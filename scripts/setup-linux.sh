#!/bin/bash
# Linux setup script for robotics project
set -e

# Create tools directory
TOOLS_DIR="$HOME/robotics-tools"
mkdir -p "$TOOLS_DIR"

# Detect distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO="$ID"
else
    DISTRO="unknown"
fi

echo "Detected Linux distribution: $DISTRO"

# Install required packages based on distribution
install_packages() {
    case "$DISTRO" in
        ubuntu|debian|pop|linuxmint)
            sudo apt update
            sudo apt install -y git build-essential cmake ninja-build python3 python3-pip
            ;;
        fedora)
            sudo dnf install -y git gcc gcc-c++ cmake ninja-build python3 python3-pip
            ;;
        arch|manjaro)
            sudo pacman -Syu --noconfirm git base-devel cmake ninja python python-pip
            ;;
        *)
            echo "Unsupported distribution. Please install these packages manually:"
            echo "git, build tools (gcc/g++), cmake, ninja, python3, pip"
            ;;
    esac
}

# Download and extract ARM GCC toolchain
download_arm_gcc() {
    ARM_GCC_DIR="$TOOLS_DIR/gcc-arm-none-eabi-10.3-2021.10"
    
    if [ -d "$ARM_GCC_DIR" ]; then
        echo "ARM GCC toolchain already installed."
        return
    fi
    
    echo "Downloading ARM GCC toolchain..."
    cd "$TOOLS_DIR"
    
    # Architecture detection
    ARCH=$(uname -m)
    if [ "$ARCH" = "x86_64" ]; then
        ARM_URL="https://developer.arm.com/-/media/Files/downloads/gnu-rm/10.3-2021.10/gcc-arm-none-eabi-10.3-2021.10-x86_64-linux.tar.bz2"
    elif [ "$ARCH" = "aarch64" ]; then
        ARM_URL="https://developer.arm.com/-/media/Files/downloads/gnu-rm/10.3-2021.10/gcc-arm-none-eabi-10.3-2021.10-aarch64-linux.tar.bz2"
    else
        echo "Architecture $ARCH not supported for prebuilt toolchain."
        echo "Please download and install the appropriate ARM GCC toolchain manually."
        return
    fi
    
    wget "$ARM_URL" -O arm-gcc.tar.bz2 || curl -L "$ARM_URL" -o arm-gcc.tar.bz2
    tar xf arm-gcc.tar.bz2
    rm arm-gcc.tar.bz2
    
    echo "ARM GCC toolchain installed to $ARM_GCC_DIR"
}

# Clone Pico SDK if not present
setup_pico_sdk() {
    PICO_SDK_DIR="$TOOLS_DIR/pico-sdk"
    
    if [ ! -d "$PICO_SDK_DIR" ]; then
        echo "Cloning Raspberry Pi Pico SDK..."
        git clone --recursive https://github.com/raspberrypi/pico-sdk.git "$PICO_SDK_DIR"
    else
        echo "Updating Pico SDK..."
        cd "$PICO_SDK_DIR"
        git pull
        git submodule update --init --recursive
    fi
    
    # Set up environment variables in bashrc if not already there
    if ! grep -q "PICO_SDK_PATH" "$HOME/.bashrc"; then
        echo "" >> "$HOME/.bashrc"
        echo "# Raspberry Pi Pico SDK" >> "$HOME/.bashrc"
        echo "export PICO_SDK_PATH=\"$PICO_SDK_DIR\"" >> "$HOME/.bashrc"
        echo "export PATH=\"\$PATH:$TOOLS_DIR/gcc-arm-none-eabi-10.3-2021.10/bin\"" >> "$HOME/.bashrc"
    fi
    
    # Set for current session
    export PICO_SDK_PATH="$PICO_SDK_DIR"
    export PATH="$PATH:$TOOLS_DIR/gcc-arm-none-eabi-10.3-2021.10/bin"
    
    echo "Pico SDK configured at $PICO_SDK_DIR"
}

# Main installation process
echo "Starting robotics project setup for Linux..."

# Install system packages
install_packages

# Download and install ARM GCC toolchain
download_arm_gcc

# Setup Pico SDK
setup_pico_sdk

echo ""
echo "Setup complete! Environment variables have been added to your ~/.bashrc"
echo "Please run 'source ~/.bashrc' or restart your terminal for changes to take effect."