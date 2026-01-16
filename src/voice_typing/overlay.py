"""Optional small recording indicator overlay (tkinter)."""

from __future__ import annotations

import logging
import threading
from typing import Optional

log = logging.getLogger(__name__)


class Overlay:
    """A small coloured dot in the corner of the screen to indicate recording state."""

    def __init__(self) -> None:
        self._root: Optional[object] = None
        self._canvas: Optional[object] = None
        self._dot: Optional[int] = None
        self._thread: Optional[threading.Thread] = None
        self._ready = threading.Event()

    def start(self) -> None:
        """Launch the overlay in a background thread."""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._ready.wait(timeout=5)

    def _run(self) -> None:
        try:
            import tkinter as tk
        except ImportError:
            log.warning("tkinter not available, overlay disabled")
            self._ready.set()
            return

        try:
            self._root = tk.Tk()
            self._root.title("")
            self._root.overrideredirect(True)
            self._root.attributes("-topmost", True)
            try:
                self._root.attributes("-transparentcolor", "black")
            except tk.TclError:
                pass  # not supported on all platforms

            dot_size = 20
            padding = 10
            # Position in top-right corner
            screen_w = self._root.winfo_screenwidth()
            x = screen_w - dot_size - padding - 40
            y = padding + 10
            self._root.geometry(f"{dot_size}x{dot_size}+{x}+{y}")

            self._canvas = tk.Canvas(
                self._root, width=dot_size, height=dot_size,
                bg="black", highlightthickness=0,
            )
            self._canvas.pack()
            self._dot = self._canvas.create_oval(
                2, 2, dot_size - 2, dot_size - 2, fill="black", outline="",
            )
            self._ready.set()
            log.info("Overlay started")
            self._root.mainloop()
        except Exception as exc:
            log.warning("Overlay failed to start (%s), continuing without it", exc)
            self._root = None
            self._canvas = None
            self._dot = None
            self._ready.set()

    def show_recording(self) -> None:
        self._update_colour("#F44336")  # red

    def show_processing(self) -> None:
        self._update_colour("#FFC107")  # amber

    def hide(self) -> None:
        self._update_colour("black")  # invisible against transparent bg

    def _update_colour(self, colour: str) -> None:
        if self._root is None or self._canvas is None or self._dot is None:
            return
        try:
            self._root.after(0, lambda: self._canvas.itemconfig(self._dot, fill=colour))
        except Exception:
            pass

    def stop(self) -> None:
        if self._root is not None:
            try:
                self._root.after(0, self._root.destroy)
            except Exception:
                pass
