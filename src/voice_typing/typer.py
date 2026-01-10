"""Text insertion — clipboard-paste or key simulation."""

from __future__ import annotations

import logging
import time

import pyperclip
from pynput.keyboard import Controller, Key

from voice_typing.platform_utils import IS_MAC

log = logging.getLogger(__name__)

_kb = Controller()


def type_text(text: str, method: str = "clipboard") -> None:
    """Insert text into the currently focused application."""
    if not text:
        return
    if method == "clipboard":
        _paste(text)
    else:
        _simulate(text)


def _paste(text: str) -> None:
    """Copy text to clipboard, simulate paste, then restore original clipboard."""
    # Save original clipboard
    try:
        original = pyperclip.paste()
    except Exception:
        original = ""

    pyperclip.copy(text)
    time.sleep(0.05)  # small delay for clipboard to settle

    modifier = Key.cmd if IS_MAC else Key.ctrl
    _kb.press(modifier)
    _kb.press("v")
    _kb.release("v")
    _kb.release(modifier)

    # Give the target app time to process the paste
    time.sleep(0.1)

    # Restore original clipboard
    try:
        pyperclip.copy(original)
    except Exception:
        pass

    log.info("Typed %d chars via clipboard paste", len(text))


def _simulate(text: str) -> None:
    """Type text character by character using pynput."""
    for ch in text:
        _kb.type(ch)
        time.sleep(0.01)
    log.info("Typed %d chars via key simulation", len(text))
