#!/bin/bash
# Linux flash script for robotics project
set -e
cd "$(dirname "$0")"

UF2_FILE="build/monster_book.uf2"

# Check if UF2 file exists
if [ ! -f "$UF2_FILE" ]; then
    echo "Error: $UF2_FILE not found. Run ./build-linux.sh first."
    exit 1
fi

# Find mounted Pico volume - typical Linux mount points
PICO_PATHS=(
    "/media/$USER/RPI-RP2"
    "/media/$USER/RP2350"
    "/run/media/$USER/RPI-RP2"
    "/run/media/$USER/RP2350"
)

PICO_VOL=""
for path in "${PICO_PATHS[@]}"; do
    if [ -d "$path" ]; then
        PICO_VOL="$path"
        break
    fi
done

# If not found in common locations, try to find by listing all mounts
if [ -z "$PICO_VOL" ]; then
    # Look for any mount point containing RP2 or RP2350 in name
    PICO_VOL=$(mount | grep -E 'RP2|RP2350' | awk '{print $3}' | head -1)
fi

if [ -z "$PICO_VOL" ]; then
    echo "Error: Pico not found. Hold BOOTSEL and plug in USB."
    echo "Common mount points checked:"
    printf "  %s\n" "${PICO_PATHS[@]}"
    exit 1
fi

echo "Copying to $PICO_VOL..."
cp "$UF2_FILE" "$PICO_VOL/"
echo "Done! Pico will reboot automatically."