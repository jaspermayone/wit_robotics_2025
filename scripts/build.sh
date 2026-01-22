#!/bin/bash
cd "$(dirname "$0")"
export PICO_SDK_PATH="$HOME/dev/pico-sdk"
export PATH="$HOME/toolchains/gcc-arm-none-eabi-10.3-2021.10/bin:$PATH"

# Use most cores (leave 2 for system responsiveness)
TOTAL_CORES=$(sysctl -n hw.ncpu)
JOBS=$((TOTAL_CORES > 2 ? TOTAL_CORES - 2 : 1))

rm -rf build
mkdir build
cd build

# Use Ninja if available (faster than Make), otherwise Make
if command -v ninja &> /dev/null; then
    cmake -G Ninja ..
    ninja -j$JOBS
else
    cmake ..
    make -j$JOBS
fi
