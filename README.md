# Voice Typing

Hold a key, speak, text appears — offline voice typing powered by OpenAI Whisper.

Works on macOS, Windows, and Linux. All transcription runs locally on your machine.

## Requirements

- Python 3.10 or higher
- A working microphone

## Installation

```bash
cd voice_typing
pip install .
```

## Usage

### Run with the installed command

```bash
voice-typing
```

### Or run directly without installing

```bash
pip install .
python3 -m voice_typing
```

**Hold the hotkey** to record your voice, **release** to transcribe and type the text at your cursor.

### Command-line options

```
voice-typing --hotkey right_shift       # Change the hold-to-talk key
voice-typing --model small              # Use a different Whisper model
voice-typing --language en              # Set language (default: auto-detect)
voice-typing --typing-method simulate   # Type keys instead of pasting from clipboard
voice-typing --romanize                 # Output Hindi in Roman script (Hinglish)
voice-typing -v                         # Verbose/debug logging
```

### Hindi Romanization

Use `--romanize` to get Hindi speech typed in Roman script instead of Devanagari:

```
Speak: "तुम क्या कर रही हो"
Without --romanize: तुम क्या कर रही हो
With --romanize:    tum kya kar rahi ho
```

```bash
voice-typing --romanize                 # Auto-detect language, romanize Hindi
voice-typing --romanize --language hi   # Force Hindi for best results
```

English speech passes through unchanged, so you can leave `--romanize` on and speak in either language.

To enable permanently, add to `~/.voice_typing/config.json`:

```json
{ "romanize": true }
```

### Available Whisper models

| Model    | Size   | Speed   | Accuracy |
|----------|--------|---------|----------|
| tiny     | 75 MB  | Fastest | Lower    |
| base     | 142 MB | Fast    | Good     |
| small    | 466 MB | Medium  | Better   |
| medium   | 1.5 GB | Slow    | Great    |
| large-v3 | 3 GB   | Slowest | Best     |

The model downloads automatically on first run.

## Configuration

Settings are stored at `~/.voice_typing/config.json`. Create or edit this file to change defaults:

```json
{
  "hotkey": "right_shift",
  "whisper_model": "base",
  "language": null,
  "typing_method": "clipboard"
}
```

### Available hotkeys

`right_shift`, `left_shift`, `right_ctrl`, `left_ctrl`, `right_alt`, `left_alt`, `right_cmd`, `left_cmd`, `caps_lock`, `f1`-`f20`

## macOS Setup

macOS requires extra permissions. Go to **System Settings > Privacy & Security** and enable your terminal app under:

1. **Accessibility**
2. **Input Monitoring**

Restart your terminal after granting permissions.

## License

MIT
