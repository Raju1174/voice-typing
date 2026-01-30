# VoxType

Hold a key, speak, text appears — offline voice typing powered by OpenAI Whisper.

Works on **macOS**, **Windows**, and **Linux**. All transcription runs locally on your machine. Your audio never leaves your device.

## Features

- **100% offline** — no cloud, no API keys, no data sent anywhere
- **GPU-accelerated** — Apple Silicon (MLX) on macOS, NVIDIA CUDA on Linux/Windows
- **Floating recording indicator** — Wispr Flow-style pill overlay on all platforms
- **Hindi romanization** — Devanagari → Roman script (Hinglish) with 1,800+ word dictionary
- **Voice Activity Detection** — trims silence automatically for faster, cleaner transcription
- **Multiple Whisper backends** — lightning-whisper-mlx, mlx-whisper, faster-whisper (CUDA/CPU)
- **Hold-to-talk** — configurable hotkey, clipboard paste or keystroke simulation

## Requirements

- Python 3.10+ (3.11–3.14 recommended)
- A working microphone

## Installation

```bash
git clone https://github.com/Raju1174/voice-typing.git
cd voice-typing
pip install -e .
```

### macOS (Apple Silicon GPU acceleration)

```bash
pip install -e ".[macos]"
```

Installs `mlx-whisper` and `lightning-whisper-mlx` for 3–5x faster transcription on M1/M2/M3/M4.

### NVIDIA GPU acceleration (Linux/Windows)

```bash
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

### Voice Activity Detection (recommended)

```bash
pip install -e ".[vad]"
```

Trims silence before sending audio to Whisper, reducing processing time.

## Usage

```bash
voxtype                  # Run with defaults
python3 -m voice_typing  # Alternative
```

**Hold the hotkey** to record your voice, **release** to transcribe and type the text at your cursor.

A floating pill indicator appears at the bottom of your screen:
- 🔴 **Red (pulsing)** — Recording
- 🟡 **Amber** — Processing
- Hidden when idle

### Command-line options

```
voxtype --model small              # Use a different Whisper model
voxtype --hotkey right_shift       # Change the hold-to-talk key
voxtype --language en              # Set language (default: auto-detect)
voxtype --typing-method simulate   # Type keys instead of pasting from clipboard
voxtype --romanize                 # Output Hindi in Roman script (Hinglish)
voxtype --quantization 4bit        # MLX 4-bit quantization (macOS)
voxtype --no-overlay               # Disable floating indicator
voxtype -v                         # Verbose logging
voxtype -vv                        # Debug logging
```

### Hindi Romanization

Use `--romanize` to get Hindi speech typed in Roman script instead of Devanagari:

```
Speak: "तुम क्या कर रही हो"
Without --romanize: तुम क्या कर रही हो
With --romanize:    tum kya kar rahi ho
```

```bash
voxtype --romanize                 # Auto-detect language, romanize Hindi
voxtype --romanize --language hi   # Force Hindi for best results
```

English speech passes through unchanged, so you can leave `--romanize` on and speak in either language.

To enable permanently, add to `~/.voxtype/config.json`:

```json
{ "romanize": true }
```

## Whisper Models

| Model | Size | Speed | Accuracy | Best For |
|-------|------|-------|----------|----------|
| tiny | 75 MB | Fastest | Lower | Quick tests, low-resource devices |
| base | 142 MB | Fast | Good | Daily use (recommended) |
| small | 466 MB | Medium | Better | Better accuracy, still fast on GPU |
| medium | 1.5 GB | Slow | Great | High accuracy, multilingual |
| large-v3 | 3 GB | Slowest | Best | Best accuracy, all languages |

The model downloads automatically on first run.

## Whisper Backends

VoxType auto-selects the fastest backend for your platform:

| Backend | Platform | Device | Speed |
|---------|----------|--------|-------|
| lightning-whisper-mlx | macOS (Apple Silicon) | GPU (MLX) | Fastest |
| mlx-whisper | macOS (Apple Silicon) | GPU (MLX) | Fast |
| faster-whisper (CUDA) | Linux / Windows | NVIDIA GPU | Fast |
| faster-whisper (CPU) | All platforms | CPU | Moderate |

## Configuration

Settings are stored at `~/.voxtype/config.json`. Create or edit this file to change defaults:

```json
{
  "hotkey": "right_shift",
  "whisper_model": "base",
  "language": null,
  "typing_method": "clipboard",
  "overlay_enabled": true,
  "vad_filter": true,
  "romanize": false,
  "quantization": null
}
```

All options can also be set via CLI flags (which override the config file).

### Available hotkeys

`right_ctrl` (default), `right_shift`, `left_shift`, `left_ctrl`, `right_alt`, `left_alt`, `right_cmd`, `left_cmd`, `caps_lock`, `f1`–`f20`

> **Note:** On macOS, `insert`, `pause`, `scroll_lock`, and `print_screen` are not available.

## Platform Setup

### macOS

Go to **System Settings > Privacy & Security** and enable your terminal app under:

1. **Accessibility** — for hotkey listening and text insertion
2. **Input Monitoring** — for keyboard event capture
3. **Microphone** — for audio recording

Restart your terminal after granting permissions.

### Windows

- Run your terminal as **Administrator** if hotkeys don't work in elevated apps
- Allow microphone access when Windows prompts

### Linux

```bash
sudo apt install portaudio19-dev xclip python3-tk   # Debian/Ubuntu
```

Requires **X11** display server. Wayland is not yet supported for global hotkeys.

## Setup Guide

See [VoxType_Setup_Guide.pdf](VoxType_Setup_Guide.pdf) for detailed installation instructions with screenshots, troubleshooting, and full configuration reference.

## License

MIT
