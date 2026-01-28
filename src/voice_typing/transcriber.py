"""Speech-to-text via lightning-whisper-mlx / mlx-whisper / faster-whisper.

Backend priority on macOS Apple Silicon:
  1. lightning-whisper-mlx — batched decoding + quantization, ~4x faster
  2. mlx-whisper — MLX GPU acceleration (covers models lightning doesn't support)
  3. faster-whisper — CPU fallback (also CUDA on Linux/Windows)
"""

from __future__ import annotations

import logging
import platform
import tempfile
import wave
from typing import Optional

import numpy as np

log = logging.getLogger(__name__)

# Models supported by lightning-whisper-mlx
_LIGHTNING_MODELS = {
    "tiny", "small", "distil-small.en", "base", "medium",
    "distil-medium.en", "large", "large-v2", "distil-large-v2",
    "large-v3", "distil-large-v3",
}

# MLX model repo mapping (mlx-whisper)
_MLX_REPOS = {
    "large-v3-turbo": "mlx-community/whisper-large-v3-turbo",
    "large-v3": "mlx-community/whisper-large-v3-mlx",
    "large-v2": "mlx-community/whisper-large-v2-mlx",
    "medium": "mlx-community/whisper-medium-mlx",
    "small": "mlx-community/whisper-small-mlx",
    "base": "mlx-community/whisper-base-mlx",
    "tiny": "mlx-community/whisper-tiny-mlx",
}


def _lightning_available() -> bool:
    """Check if lightning-whisper-mlx can be used."""
    if platform.system() != "Darwin":
        return False
    try:
        import lightning_whisper_mlx  # noqa: F401
        return True
    except ImportError:
        return False


def _mlx_available() -> bool:
    """Check if mlx-whisper can be used on this system."""
    if platform.system() != "Darwin":
        return False
    try:
        import mlx_whisper  # noqa: F401
        return True
    except ImportError:
        return False


class Transcriber:
    """Loads a Whisper model and transcribes audio arrays to text.

    Selects the fastest available backend:
      lightning-whisper-mlx > mlx-whisper > faster-whisper
    """

    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
        quantization: Optional[str] = None,
    ) -> None:
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.quantization = quantization
        self._model = None
        self._mlx_repo: Optional[str] = None
        self._backend = self._select_backend()

    def _select_backend(self) -> str:
        """Choose the best available backend for the requested model."""
        # 1. lightning-whisper-mlx
        if _lightning_available() and self.model_size in _LIGHTNING_MODELS:
            return "lightning"

        # 2. mlx-whisper
        if _mlx_available() and self.model_size in _MLX_REPOS:
            return "mlx"

        # 3. faster-whisper (always available)
        return "faster-whisper"

    def load_model(self) -> None:
        """Download (if needed) and load the Whisper model."""
        if self._backend == "lightning":
            self._load_lightning()
        elif self._backend == "mlx":
            self._load_mlx()
        else:
            self._load_faster_whisper()

    @staticmethod
    def _patch_lightning() -> None:
        """Patch lightning-whisper-mlx for compatibility.

        1. MLX >= 0.30: QuantizedLinear.quantize_module → nn.quantize
        2. Replace ffmpeg-based load_audio with stdlib wave reader
        """
        try:
            import mlx.nn as nn
            if not hasattr(nn.QuantizedLinear, "quantize_module"):
                nn.QuantizedLinear.quantize_module = staticmethod(nn.quantize)
                log.debug("Patched QuantizedLinear.quantize_module → nn.quantize")
        except ImportError:
            pass

        try:
            import lightning_whisper_mlx.audio as _la
            import mlx.core as mx

            def _load_audio_wav(file_path: str) -> "mx.array":
                """Read WAV without ffmpeg, return as mx.array.

                Our temp files are already 16kHz mono int16. Returning mx.array
                ensures log_mel_spectrogram's isinstance(audio, mx.array) check
                passes, avoiding the ndarray→mx.pad crash.
                """
                with wave.open(file_path, "rb") as wf:
                    data = wf.readframes(wf.getnframes())
                arr = np.frombuffer(data, np.int16).flatten().astype(np.float32) / 32768.0
                return mx.array(arr)

            _la.load_audio = _load_audio_wav
            log.debug("Patched lightning load_audio to use stdlib wave (no ffmpeg)")
        except ImportError:
            pass

    def _load_lightning(self) -> None:
        """Load model via lightning-whisper-mlx (eager load)."""
        self._patch_lightning()
        from lightning_whisper_mlx import LightningWhisperMLX

        quant = self.quantization  # None, "4bit", or "8bit"
        log.info(
            "Using Lightning Whisper MLX — model '%s', batch_size=12, quant=%s",
            self.model_size, quant or "None (fp16)",
        )
        self._model = LightningWhisperMLX(
            model=self.model_size,
            batch_size=12,
            quant=quant,
        )
        log.info("Lightning model loaded. Ready.")

    def _load_mlx(self) -> None:
        """Set up mlx-whisper (lazy load on first transcribe)."""
        self._mlx_repo = _MLX_REPOS[self.model_size]
        log.info(
            "Using MLX Whisper — model '%s' (%s)",
            self.model_size, self._mlx_repo,
        )

    def _load_faster_whisper(self) -> None:
        """Load model via faster-whisper."""
        from faster_whisper import WhisperModel

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
        initial_prompt: Optional[str] = None,
    ) -> tuple[str, str]:
        """Transcribe a float32 audio array and return (text, detected_language)."""
        if len(audio) == 0:
            log.warning("Empty audio, nothing to transcribe")
            return "", ""

        if self._backend == "lightning":
            return self._transcribe_lightning(audio, language, initial_prompt)
        elif self._backend == "mlx":
            return self._transcribe_mlx(audio, language, initial_prompt)
        return self._transcribe_faster_whisper(
            audio, language, beam_size, vad_filter, initial_prompt,
        )

    def _transcribe_lightning(
        self,
        audio: np.ndarray,
        language: Optional[str],
        initial_prompt: Optional[str] = None,
    ) -> tuple[str, str]:
        """Transcribe using lightning-whisper-mlx.

        Lightning only accepts file paths, so we write audio to a temp WAV file.
        We call transcribe_audio directly to pass initial_prompt (the
        LightningWhisperMLX wrapper doesn't expose it).
        """
        if self._model is None:
            raise RuntimeError("Model not loaded — call load_model() first")

        from lightning_whisper_mlx.transcribe import transcribe_audio

        # Convert float32 [-1, 1] to int16 for WAV
        audio_int16 = (audio * 32767).astype(np.int16)

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
                with wave.open(tmp, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)  # 16-bit
                    wf.setframerate(16000)
                    wf.writeframes(audio_int16.tobytes())

            result = transcribe_audio(
                tmp_path,
                path_or_hf_repo=f"./mlx_models/{self.model_size}",
                language=language,
                batch_size=12,
                initial_prompt=initial_prompt,
            )
            text = result.get("text", "").strip()
            detected = result.get("language", language or "")
            log.info("Transcribed (Lightning) [%s]: %s", detected, text)
            return text, detected
        finally:
            if tmp_path is not None:
                import os
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

    def _transcribe_mlx(
        self,
        audio: np.ndarray,
        language: Optional[str],
        initial_prompt: Optional[str],
    ) -> tuple[str, str]:
        """Transcribe using mlx-whisper (Apple Silicon GPU)."""
        import mlx_whisper

        kwargs: dict = {"path_or_hf_repo": self._mlx_repo}
        if language is not None:
            kwargs["language"] = language
        if initial_prompt is not None:
            kwargs["initial_prompt"] = initial_prompt

        result = mlx_whisper.transcribe(audio, **kwargs)
        text = result.get("text", "").strip()
        detected = result.get("language", language or "")
        log.info("Transcribed (MLX) [%s]: %s", detected, text)
        return text, detected

    def _transcribe_faster_whisper(
        self,
        audio: np.ndarray,
        language: Optional[str],
        beam_size: int,
        vad_filter: bool,
        initial_prompt: Optional[str],
    ) -> tuple[str, str]:
        """Transcribe using faster-whisper (CPU)."""
        if self._model is None:
            raise RuntimeError("Model not loaded — call load_model() first")

        segments, info = self._model.transcribe(
            audio,
            language=language,
            beam_size=beam_size,
            vad_filter=vad_filter,
            initial_prompt=initial_prompt,
        )

        text = " ".join(seg.text.strip() for seg in segments)
        detected = info.language if language is None else language
        log.info("Transcribed [%s, %.0f%% prob]: %s", detected, info.language_probability * 100, text)
        return text, detected
