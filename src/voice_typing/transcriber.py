"""Speech-to-text via faster-whisper."""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
from faster_whisper import WhisperModel

log = logging.getLogger(__name__)


class Transcriber:
    """Loads a faster-whisper model and transcribes audio arrays to text."""

    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
    ) -> None:
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model: Optional[WhisperModel] = None

    def load_model(self) -> None:
        """Download (if needed) and load the Whisper model."""
        log.info(
            "Loading Whisper model '%s' on %s (%s) …",
            self.model_size, self.device, self.compute_type,
        )
        self._model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type,
        )
        log.info("Model loaded. Ready.")

    def transcribe(
        self,
        audio: np.ndarray,
        language: Optional[str] = None,
        beam_size: int = 5,
        vad_filter: bool = True,
    ) -> str:
        """Transcribe a float32 audio array and return the text."""
        if self._model is None:
            raise RuntimeError("Model not loaded — call load_model() first")

        if len(audio) == 0:
            log.warning("Empty audio, nothing to transcribe")
            return ""

        segments, info = self._model.transcribe(
            audio,
            language=language,
            beam_size=beam_size,
            vad_filter=vad_filter,
        )

        text = " ".join(seg.text.strip() for seg in segments)
        detected = info.language if language is None else language
        log.info("Transcribed [%s, %.0f%% prob]: %s", detected, info.language_probability * 100, text)
        return text
