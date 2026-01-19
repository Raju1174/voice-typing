@echo off
cd /d "%~dp0\.."

echo Building Voice Typing for Windows ...
pyinstaller ^
    --name "Voice Typing" ^
    --onedir ^
    --windowed ^
    --noconfirm ^
    --add-data "config.default.json;." ^
    --hidden-import "faster_whisper" ^
    --hidden-import "sounddevice" ^
    --hidden-import "pynput" ^
    --hidden-import "pystray" ^
    --hidden-import "pyperclip" ^
    src\voice_typing\__main__.py

echo Done — output in dist\
