"""Central orchestrator — wires all components together with a state machine."""

from __future__ import annotations

import logging
import threading
from enum import Enum

from voice_typing.config import Config
from voice_typing.audio import AudioRecorder
from voice_typing.transcriber import Transcriber
from voice_typing.typer import type_text
from voice_typing.hotkey import HotkeyListener
from voice_typing.tray import TrayIcon, TrayState
from voice_typing.overlay import Overlay
from voice_typing.platform_utils import check_permissions, resolve_whisper_device

log = logging.getLogger(__name__)


def _can_use_overlay() -> bool:
    """Check if the tkinter overlay can work.

    On macOS, tkinter requires the main thread, but pystray already occupies it,
    so the overlay cannot be used alongside the tray icon.
    """
    from voice_typing.platform_utils import IS_MAC
    if IS_MAC:
        log.info("Overlay disabled on macOS (tkinter requires main thread, used by tray)")
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
        )
        self.hotkey = HotkeyListener(
            key_name=config.hotkey,
            on_press=self._on_hotkey_press,
            on_release=self._on_hotkey_release,
        )
        self.tray = TrayIcon(on_quit=self.quit)
        self.overlay: Overlay | None = None
        if config.overlay_enabled and _can_use_overlay():
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
        log.info("Voice Typing is running. Hold '%s' to record.", self.config.hotkey)

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
            text = self.transcriber.transcribe(
                audio,
                language=self.config.language,
                beam_size=self.config.beam_size,
                vad_filter=self.config.vad_filter,
            )
            if text:
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
