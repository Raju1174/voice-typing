"""Entry point: python -m voice_typing"""

from __future__ import annotations

import argparse
import logging
import sys

from voice_typing.config import Config
from voice_typing.app import VoiceTypingApp


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="voxtype",
        description="VoxType — Hold a key, speak, text appears. Offline voice typing.",
    )
    parser.add_argument(
        "--model", default=None,
        help="Whisper model size (tiny/base/small/medium/large-v3/large-v3-turbo/distil-large-v3)",
    )
    parser.add_argument(
        "--hotkey", default=None,
        help="Hold-to-talk key (e.g. right_ctrl, f5, caps_lock)",
    )
    parser.add_argument(
        "--language", default=None,
        help="Language code (e.g. en, es, ja) or omit for auto-detect",
    )
    parser.add_argument(
        "--typing-method", choices=["clipboard", "simulate"], default=None,
        help="How to insert text (default: clipboard)",
    )
    parser.add_argument(
        "--no-overlay", action="store_true",
        help="Disable the recording indicator overlay",
    )
    parser.add_argument(
        "--quantization", choices=["4bit", "8bit"], default=None,
        help="Quantization for lightning-whisper-mlx (4bit or 8bit)",
    )
    parser.add_argument(
        "--romanize", action="store_true",
        help="Transliterate Hindi (Devanagari) output to Roman script (Hinglish)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    config = Config.load()

    # CLI overrides
    if args.model:
        config.whisper_model = args.model
    if args.hotkey:
        config.hotkey = args.hotkey
    if args.language:
        config.language = args.language
    if args.typing_method:
        config.typing_method = args.typing_method
    if args.no_overlay:
        config.overlay_enabled = False
    if args.quantization:
        config.quantization = args.quantization
    if args.romanize:
        config.romanize = True

    app = VoiceTypingApp(config)
    try:
        app.run()
    except KeyboardInterrupt:
        app.quit()
        sys.exit(0)


if __name__ == "__main__":
    main()
