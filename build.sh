#!/bin/bash
cd "$(dirname "$0")"
export PICO_SDK_PATH="$HOME/dev/pico-sdk"
export PATH="$HOME/toolchains/gcc-arm-none-eabi-10.3-2021.10/bin:$PATH"
rm -rf build
mkdir build
cd build
cmake ..
make -j4
