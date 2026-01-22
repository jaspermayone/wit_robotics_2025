@echo off
REM Batch file wrapper for PowerShell script
PowerShell -ExecutionPolicy Bypass -File "%~dp0build.ps1"