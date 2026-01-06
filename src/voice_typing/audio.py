"""Microphone recording via sounddevice."""

from __future__ import annotations

import logging
import threading
from typing import Optional

import numpy as np
import sounddevice as sd

log = logging.getLogger(__name__)


class AudioRecorder:
    """Records audio from the default mic into a float32 numpy buffer."""

    def __init__(self, sample_rate: int = 16000, channels: int = 1) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self._chunks: list[np.ndarray] = []
        self._stream: Optional[sd.InputStream] = None
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start recording from the default microphone."""
        with self._lock:
            self._chunks = []
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="float32",
                callback=self._callback,
            )
            self._stream.start()
            log.info("Recording started")

    def stop(self) -> np.ndarray:
        """Stop recording and return the audio as a 1-D float32 array."""
        with self._lock:
            if self._stream is not None:
                self._stream.stop()
                self._stream.close()
                self._stream = None
            log.info("Recording stopped")
            if not self._chunks:
                return np.array([], dtype=np.float32)
            audio = np.concatenate(self._chunks, axis=0)
            # Flatten to 1-D (mono)
            if audio.ndim > 1:
                audio = audio[:, 0]
            duration = len(audio) / self.sample_rate
            log.info("Captured %.2fs of audio", duration)
            return audio

    def _callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: object,
        status: sd.CallbackFlags,
    ) -> None:
        if status:
            log.warning("Audio callback status: %s", status)
        self._chunks.append(indata.copy())
