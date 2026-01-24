"""Configuration loading with defaults."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

CONFIG_DIR = Path.home() / ".voice_typing"
CONFIG_FILE = CONFIG_DIR / "config.json"


@dataclass
class Config:
    hotkey: str = "right_ctrl"
    whisper_model: str = "base"
    whisper_device: str = "auto"
    whisper_compute_type: str = "int8"
    language: Optional[str] = None
    typing_method: str = "clipboard"  # "clipboard" or "simulate"
    audio_sample_rate: int = 16000
    audio_channels: int = 1
    vad_filter: bool = True
    beam_size: int = 5
    overlay_enabled: bool = True
    romanize: bool = False

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(asdict(self), indent=2))
        log.info("Config saved to %s", CONFIG_FILE)

    @classmethod
    def load(cls) -> Config:
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text())
                # Only use keys that are valid fields
                valid = {f.name for f in cls.__dataclass_fields__.values()}
                filtered = {k: v for k, v in data.items() if k in valid}
                cfg = cls(**filtered)
                log.info("Config loaded from %s", CONFIG_FILE)
                return cfg
            except Exception as exc:
                log.warning("Failed to load config (%s), using defaults", exc)
        else:
            log.info("No config file found, using defaults")
        return cls()
