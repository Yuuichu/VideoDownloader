@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" video_downloader_qt.py
) else (
    echo [ERROR] .venv not found. Please run: python -m venv .venv
    pause
)
