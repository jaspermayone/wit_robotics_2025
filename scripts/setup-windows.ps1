# Windows setup script for robotics project
# Run in PowerShell with admin privileges

# Create tools directory
$toolsDir = "$env:USERPROFILE\robotics-tools"
New-Item -ItemType Directory -Force -Path $toolsDir | Out-Null

# Function to download and extract files
function Download-Extract {
    param (
        [string]$url,
        [string]$destination,
        [string]$name
    )
    
    Write-Host "Downloading $name..."
    $tempFile = "$env:TEMP\$(Split-Path -Leaf $url)"
    Invoke-WebRequest -Uri $url -OutFile $tempFile
    
    Write-Host "Extracting $name..."
    Expand-Archive -Path $tempFile -DestinationPath $destination -Force
    Remove-Item $tempFile
}

# Install Chocolatey if not installed
if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Chocolatey package manager..."
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
    refreshenv
}

# Install required tools
Write-Host "Installing required tools (CMake and Ninja)..."
choco install -y cmake ninja

# Download and extract ARM GCC toolchain
$armToolchainUrl = "https://developer.arm.com/-/media/Files/downloads/gnu-rm/10.3-2021.10/gcc-arm-none-eabi-10.3-2021.10-win32.zip"
Download-Extract -url $armToolchainUrl -destination $toolsDir -name "ARM GCC Toolchain"

# Clone Pico SDK if not present
$picoSdkPath = "$toolsDir\pico-sdk"
if (-not (Test-Path $picoSdkPath)) {
    Write-Host "Cloning Raspberry Pi Pico SDK..."
    git clone --recursive https://github.com/raspberrypi/pico-sdk.git $picoSdkPath
} else {
    Write-Host "Updating Pico SDK..."
    Set-Location $picoSdkPath
    git pull
    git submodule update --init --recursive
    Set-Location -
}

# Add environment variables
[Environment]::SetEnvironmentVariable("PICO_SDK_PATH", $picoSdkPath, "User")
[Environment]::SetEnvironmentVariable("PATH", "$env:PATH;$toolsDir\gcc-arm-none-eabi-10.3-2021.10\bin", "User")

Write-Host "Setup complete! Environment variables have been set."
Write-Host "Please restart your terminal for changes to take effect."