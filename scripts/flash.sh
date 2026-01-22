#!/bin/bash
cd "$(dirname "$0")"

UF2_FILE="build/monster_book.uf2"

# Find the Pico volume
PICO_VOL=$(ls -d /Volumes/RP2350 /Volumes/RPI-RP2 2>/dev/null | head -1)

if [ ! -f "$UF2_FILE" ]; then
    echo "Error: $UF2_FILE not found. Run ./build.sh first."
    exit 1
fi

if [ -z "$PICO_VOL" ]; then
    echo "Error: Pico not found. Hold BOOTSEL and plug in USB."
    exit 1
fi

echo "Copying to $PICO_VOL..."
cp "$UF2_FILE" "$PICO_VOL/"
echo "Done! Pico will reboot automatically."
