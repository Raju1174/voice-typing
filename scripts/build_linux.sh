#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "Building Voice Typing for Linux …"
pyinstaller \
    --name "voice-typing" \
    --onedir \
    --noconfirm \
    --add-data "config.default.json:." \
    --hidden-import "faster_whisper" \
    --hidden-import "sounddevice" \
    --hidden-import "pynput" \
    --hidden-import "pystray" \
    --hidden-import "pyperclip" \
    src/voice_typing/__main__.py

echo "Done — output in dist/"
