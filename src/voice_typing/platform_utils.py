"""OS detection, permission checks, platform helpers."""

from __future__ import annotations

import logging
import platform
import subprocess
import sys

log = logging.getLogger(__name__)

PLATFORM = platform.system().lower()  # "darwin", "windows", "linux"
IS_MAC = PLATFORM == "darwin"
IS_WIN = PLATFORM == "windows"
IS_LINUX = PLATFORM == "linux"


def paste_keys() -> tuple[str, str]:
    """Return (modifier, key) for the paste shortcut on this OS."""
    if IS_MAC:
        return ("cmd", "v")
    return ("ctrl", "v")


def resolve_whisper_device(preference: str) -> str:
    """Resolve 'auto' to 'cuda' or 'cpu'."""
    if preference != "auto":
        return preference
    if IS_MAC:
        return "cpu"  # No CUDA on macOS
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass
    return "cpu"


def check_permissions() -> None:
    """Log warnings about missing OS-level permissions."""
    if IS_MAC:
        log.info(
            "macOS detected — make sure Accessibility and Input Monitoring "
            "are enabled for this app in System Settings > Privacy & Security."
        )
    elif IS_LINUX:
        # Check if X11 is available
        display = subprocess.run(
            ["xdpyinfo"], capture_output=True, timeout=5
        )
        if display.returncode != 0:
            log.warning(
                "X11 display not detected. Global hotkeys and clipboard "
                "paste require an X11 session."
            )
        # Check for xclip/xsel
        has_clip = (
            subprocess.run(["which", "xclip"], capture_output=True).returncode == 0
            or subprocess.run(["which", "xsel"], capture_output=True).returncode == 0
        )
        if not has_clip:
            log.warning(
                "Neither xclip nor xsel found. Install one for clipboard paste: "
                "sudo apt install xclip"
            )
