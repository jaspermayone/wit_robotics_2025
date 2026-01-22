# Windows build script for robotics project

# Navigate to script directory
Set-Location $PSScriptRoot

# Setup tools directory
$toolsDir = "$env:USERPROFILE\robotics-tools"
$picoSdkPath = "$toolsDir\pico-sdk"

# Check environment
if (-not $env:PICO_SDK_PATH) {
    Write-Host "PICO_SDK_PATH not set. Checking if Pico SDK is installed locally..."
    
    if (-not (Test-Path $picoSdkPath)) {
        $downloadSdk = Read-Host "Pico SDK not found. Would you like to download it now? (y/n)"
        if ($downloadSdk -eq 'y') {
            # Create tools directory if it doesn't exist
            if (-not (Test-Path $toolsDir)) {
                New-Item -ItemType Directory -Force -Path $toolsDir | Out-Null
            }
            
            # Clone Pico SDK
            Write-Host "Downloading Raspberry Pi Pico SDK..."
            git clone --recursive https://github.com/raspberrypi/pico-sdk.git $picoSdkPath
            
            # Set environment variable for current session
            $env:PICO_SDK_PATH = $picoSdkPath
            
            # Set permanent environment variable
            [Environment]::SetEnvironmentVariable("PICO_SDK_PATH", $picoSdkPath, "User")
            Write-Host "Pico SDK downloaded and PICO_SDK_PATH set to $picoSdkPath"
        } else {
            Write-Error "PICO_SDK_PATH not set and download declined. Cannot continue."
            exit 1
        }
    } else {
        # SDK exists locally but environment variable not set
        $env:PICO_SDK_PATH = $picoSdkPath
        [Environment]::SetEnvironmentVariable("PICO_SDK_PATH", $picoSdkPath, "User")
        Write-Host "Found existing Pico SDK. Set PICO_SDK_PATH to $picoSdkPath"
    }
}

# Calculate number of jobs for parallel build
$totalCores = (Get-CimInstance -ClassName Win32_ComputerSystem).NumberOfLogicalProcessors
$jobs = if ($totalCores -gt 2) { $totalCores - 2 } else { 1 }

# Clean and create build directory
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
}
New-Item -ItemType Directory -Path "build" | Out-Null
Set-Location "build"

# Use Ninja if available, otherwise use standard CMake
if (Get-Command "ninja" -ErrorAction SilentlyContinue) {
    Write-Host "Building with Ninja..."
    cmake -G Ninja ..
    ninja -j $jobs
} else {
    Write-Host "Building with CMake..."
    cmake -G "MinGW Makefiles" ..
    cmake --build . -j $jobs
}

Write-Host "Build complete! UF2 file is in the build directory."
Set-Location $PSScriptRoot