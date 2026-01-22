# Windows flash script for robotics project

# Navigate to script directory
Set-Location $PSScriptRoot

$uf2File = "build\monster_book.uf2"

# Check if UF2 file exists
if (-not (Test-Path $uf2File)) {
    Write-Error "Error: $uf2File not found. Run .\build.ps1 first."
    exit 1
}

# Find Pico volume (RPI-RP2 or similar)
$picoDrives = Get-WmiObject Win32_LogicalDisk | Where-Object { 
    $_.VolumeName -match 'RPI-RP2' -or $_.VolumeName -match 'RP2350'
}

if (-not $picoDrives) {
    Write-Error "Error: Pico not found. Hold BOOTSEL button and plug in USB."
    exit 1
}

# Use the first matching drive
$picoDrive = $picoDrives[0].DeviceID

Write-Host "Copying to $picoDrive..."
Copy-Item $uf2File "$picoDrive\"
Write-Host "Done! Pico will reboot automatically."