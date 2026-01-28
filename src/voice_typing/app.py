"""Central orchestrator — wires all components together with a state machine."""

from __future__ import annotations

import logging
import threading
from enum import Enum

from voice_typing.config import Config
from voice_typing.audio import AudioRecorder
from voice_typing.transcriber import Transcriber
from voice_typing.typer import type_text
from voice_typing.romanizer import romanize, format_text
from voice_typing.hotkey import HotkeyListener
from voice_typing.tray import TrayIcon, TrayState
from voice_typing.overlay import Overlay
from voice_typing.platform_utils import check_permissions, resolve_whisper_device

log = logging.getLogger(__name__)


def _can_use_overlay() -> bool:
    """Check if an overlay can work on this platform.

    On macOS, we use a PyObjC NSPanel overlay instead of tkinter (which would
    conflict with pystray for the main thread). On other platforms, tkinter is used.
    """
    from voice_typing.platform_utils import IS_MAC
    if IS_MAC:
        try:
            from voice_typing.overlay_macos import HAS_PYOBJC
            if HAS_PYOBJC:
                return True
            log.warning("PyObjC not available, macOS overlay disabled")
            return False
        except ImportError:
            log.warning("overlay_macos module not found, overlay disabled")
            return False
    try:
        import tkinter  # noqa: F401
        return True
    except ImportError:
        log.warning("tkinter not available, overlay disabled")
        return False


class AppState(Enum):
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"


class VoiceTypingApp:
    """Main application controller."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self._state = AppState.IDLE
        self._lock = threading.Lock()

        device = resolve_whisper_device(config.whisper_device)

        self.recorder = AudioRecorder(
            sample_rate=config.audio_sample_rate,
            channels=config.audio_channels,
        )
        self.transcriber = Transcriber(
            model_size=config.whisper_model,
            device=device,
            compute_type=config.whisper_compute_type,
            quantization=config.quantization,
        )
        self.hotkey = HotkeyListener(
            key_name=config.hotkey,
            on_press=self._on_hotkey_press,
            on_release=self._on_hotkey_release,
        )
        self.tray = TrayIcon(on_quit=self.quit)
        self.overlay: Overlay | None = None
        if config.overlay_enabled and _can_use_overlay():
            from voice_typing.platform_utils import IS_MAC
            if IS_MAC:
                from voice_typing.overlay_macos import MacOverlay
                self.overlay = MacOverlay()
            else:
                self.overlay = Overlay()

    def run(self) -> None:
        """Start the app. Blocks on the tray icon loop (main thread)."""
        check_permissions()

        # Load model before starting the tray (so we're ready as soon as UI is up)
        self.transcriber.load_model()

        # The tray.run() will call _on_tray_ready once the icon is visible
        self.tray.run(setup_callback=self._on_tray_ready)

    def _on_tray_ready(self, tray: TrayIcon) -> None:
        """Called from tray setup, runs in a background thread."""
        self.hotkey.start()
        if self.overlay is not None:
            self.overlay.start()
        log.info("VoxType is running. Hold '%s' to record.", self.config.hotkey)

    def _on_hotkey_press(self) -> None:
        with self._lock:
            if self._state != AppState.IDLE:
                return
            self._state = AppState.RECORDING

        self.tray.set_state(TrayState.RECORDING)
        if self.overlay:
            self.overlay.show_recording()
        self.recorder.start()

    def _on_hotkey_release(self) -> None:
        with self._lock:
            if self._state != AppState.RECORDING:
                return
            self._state = AppState.PROCESSING

        self.tray.set_state(TrayState.PROCESSING)
        if self.overlay:
            self.overlay.show_processing()
        audio = self.recorder.stop()

        # Transcribe + type in a background thread so we don't block hotkey listener
        threading.Thread(target=self._process, args=(audio,), daemon=True).start()

    def _process(self, audio) -> None:
        try:
            from voice_typing.vad import trim_silence
            trimmed = trim_silence(audio, sample_rate=self.config.audio_sample_rate)
            if trimmed is None:
                log.info("No speech detected, skipping transcription")
                return  # finally block still resets state to IDLE
            # If VAD trimmed successfully, disable faster-whisper's internal VAD
            # to avoid double processing. If trim_silence returned audio unchanged
            # (silero not installed), keep the config's vad_filter as fallback.
            silero_active = trimmed is not audio
            text, detected_lang = self.transcriber.transcribe(
                trimmed,
                language=self.config.language,
                beam_size=self.config.beam_size,
                vad_filter=False if silero_active else self.config.vad_filter,
                initial_prompt=self.config.initial_prompt,
            )
            # When romanize is on and Whisper detected Urdu instead of Hindi,
            # re-transcribe with language="hi" forced so we get Devanagari
            # (which has explicit vowels) instead of Urdu script (which drops
            # short vowels and can't be romanized accurately).
            if (text and self.config.romanize and detected_lang == "ur"
                    and self.config.language is None):
                log.info("Detected Urdu, re-transcribing as Hindi for romanization")
                text, detected_lang = self.transcriber.transcribe(
                    trimmed,
                    language="hi",
                    beam_size=self.config.beam_size,
                    vad_filter=False if silero_active else self.config.vad_filter,
                    initial_prompt=self.config.initial_prompt,
                )
            if text and self.config.romanize and detected_lang in ("hi", "ur"):
                text = romanize(text)
            if text:
                text = format_text(text)
                type_text(text, method=self.config.typing_method)
        except Exception:
            log.exception("Transcription/typing failed")
        finally:
            with self._lock:
                self._state = AppState.IDLE
            self.tray.set_state(TrayState.IDLE)
            if self.overlay:
                self.overlay.hide()

    def quit(self) -> None:
        log.info("Shutting down …")
        self.hotkey.stop()
        if self.overlay:
            self.overlay.stop()
        self.tray.stop()
