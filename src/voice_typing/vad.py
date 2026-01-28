"""Silero VAD — trim silence from audio before transcription."""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np

log = logging.getLogger(__name__)

_vad_model = None


def _load_vad():
    """Lazy-load the Silero VAD model (singleton)."""
    global _vad_model
    if _vad_model is not None:
        return _vad_model

    from silero_vad import load_silero_vad
    _vad_model = load_silero_vad()
    log.info("Silero VAD model loaded")
    return _vad_model


def trim_silence(
    audio: np.ndarray,
    sample_rate: int = 16000,
    pad_ms: int = 300,
) -> Optional[np.ndarray]:
    """Trim leading/trailing silence using Silero VAD.

    Returns the trimmed audio, or None if no speech is detected.
    If silero-vad is not installed, returns the audio unchanged.
    """
    try:
        from silero_vad import get_speech_timestamps
    except ImportError:
        log.debug("silero-vad not installed, skipping VAD")
        return audio

    try:
        import torch
        model = _load_vad()
    except Exception:
        log.warning("Failed to load Silero VAD, skipping", exc_info=True)
        return audio

    audio_tensor = torch.from_numpy(audio).float()

    timestamps = get_speech_timestamps(audio_tensor, model, sampling_rate=sample_rate)

    if not timestamps:
        log.info("VAD: no speech detected")
        return None

    # Trim to [first_start - pad, last_end + pad], keeping internal pauses intact
    pad_samples = int(sample_rate * pad_ms / 1000)
    start = max(0, timestamps[0]["start"] - pad_samples)
    end = min(len(audio), timestamps[-1]["end"] + pad_samples)

    trimmed = audio[start:end]
    trimmed_duration = len(trimmed) / sample_rate
    original_duration = len(audio) / sample_rate
    log.info(
        "VAD: trimmed %.1fs → %.1fs (removed %.1fs silence)",
        original_duration, trimmed_duration, original_duration - trimmed_duration,
    )
    return trimmed
