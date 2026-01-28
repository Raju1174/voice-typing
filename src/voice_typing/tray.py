"""System tray icon with state changes (idle / recording / processing)."""

from __future__ import annotations

import logging
from enum import Enum
from typing import Callable, Optional

from PIL import Image, ImageDraw
import pystray

log = logging.getLogger(__name__)

ICON_SIZE = 64


class TrayState(Enum):
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"


# State -> colour
_COLOURS: dict[TrayState, str] = {
    TrayState.IDLE: "#4CAF50",       # green
    TrayState.RECORDING: "#F44336",  # red
    TrayState.PROCESSING: "#FFC107", # amber
}


def _make_icon(state: TrayState) -> Image.Image:
    """Generate a simple circle icon for the given state."""
    img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = 4
    draw.ellipse(
        [margin, margin, ICON_SIZE - margin, ICON_SIZE - margin],
        fill=_COLOURS[state],
    )
    return img


class TrayIcon:
    """Manages a system tray icon that reflects app state."""

    def __init__(self, on_quit: Callable[[], None]) -> None:
        self._on_quit = on_quit
        self._state = TrayState.IDLE
        self._icon: Optional[pystray.Icon] = None

    def set_state(self, state: TrayState) -> None:
        self._state = state
        if self._icon is not None:
            self._icon.icon = _make_icon(state)
            self._icon.title = f"VoxType — {state.value}"

    def run(self, setup_callback: Callable[["TrayIcon"], None]) -> None:
        """Create and run the tray icon. Blocks on the main thread (required by macOS)."""
        menu = pystray.Menu(
            pystray.MenuItem("VoxType", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", lambda: self._on_quit()),
        )
        self._icon = pystray.Icon(
            name="voxtype",
            icon=_make_icon(self._state),
            title="VoxType — idle",
            menu=menu,
        )

        def on_setup(icon: pystray.Icon) -> None:
            icon.visible = True
            setup_callback(self)

        self._icon.run(setup=on_setup)

    def stop(self) -> None:
        if self._icon is not None:
            self._icon.stop()
