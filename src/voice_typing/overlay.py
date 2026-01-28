"""Floating pill recording indicator overlay (tkinter) for Windows & Linux.

Displays a Wispr Flow-style pill at the bottom center of the screen showing
recording/processing state. Matches the macOS NSPanel overlay design.
"""

from __future__ import annotations

import logging
import math
import threading
import time
from typing import Optional

log = logging.getLogger(__name__)

# ── Design constants ─────────────────────────────────────────────────
PILL_W = 180
PILL_H = 36
PILL_RADIUS = 18          # half of height for full rounded ends
BOTTOM_OFFSET = 60        # px from bottom of screen
BG_COLOR = "#1a1a1a"
DOT_RADIUS = 5
DOT_X = 19                # center x of dot
RED = "#F44336"
AMBER = "#FFC107"
TEXT_COLOR = "#e6e6e6"
FONT = ("Segoe UI", 11)   # Segoe UI on Windows, falls back to default on Linux


class Overlay:
    """Floating pill overlay — bottom center of screen."""

    def __init__(self) -> None:
        self._root = None
        self._canvas = None
        self._dot_id: Optional[int] = None
        self._glow_id: Optional[int] = None
        self._text_id: Optional[int] = None
        self._thread: Optional[threading.Thread] = None
        self._ready = threading.Event()
        self._pulse_running = False
        self._pulse_thread: Optional[threading.Thread] = None

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

            # Make window click-through on Windows
            try:
                # Windows: WS_EX_LAYERED | WS_EX_TRANSPARENT
                self._root.attributes("-transparentcolor", BG_COLOR)
            except tk.TclError:
                pass  # Linux doesn't support -transparentcolor

            # Position at bottom center
            screen_w = self._root.winfo_screenwidth()
            screen_h = self._root.winfo_screenheight()
            x = (screen_w - PILL_W) // 2
            y = screen_h - PILL_H - BOTTOM_OFFSET
            self._root.geometry(f"{PILL_W}x{PILL_H}+{x}+{y}")

            # Use a frame with dark background as the pill
            # On Windows, -transparentcolor makes BG_COLOR transparent,
            # so we use a slightly different shade for the actual pill
            pill_bg = "#1b1b1b"

            self._canvas = tk.Canvas(
                self._root, width=PILL_W, height=PILL_H,
                bg=BG_COLOR, highlightthickness=0, bd=0,
            )
            self._canvas.pack()

            # Draw pill shape (rounded rectangle)
            self._pill_bg = self._draw_rounded_rect(
                1, 1, PILL_W - 1, PILL_H - 1,
                radius=PILL_RADIUS, fill=pill_bg, outline=""
            )

            # Glow behind dot (drawn first so it's behind)
            dot_cy = PILL_H // 2
            self._glow_id = self._canvas.create_oval(
                DOT_X - DOT_RADIUS - 3, dot_cy - DOT_RADIUS - 3,
                DOT_X + DOT_RADIUS + 3, dot_cy + DOT_RADIUS + 3,
                fill="", outline=""
            )

            # Coloured dot
            self._dot_id = self._canvas.create_oval(
                DOT_X - DOT_RADIUS, dot_cy - DOT_RADIUS,
                DOT_X + DOT_RADIUS, dot_cy + DOT_RADIUS,
                fill=RED, outline=""
            )

            # Text label
            self._text_id = self._canvas.create_text(
                DOT_X + DOT_RADIUS + 12, dot_cy,
                text="Recording...", fill=TEXT_COLOR,
                font=FONT, anchor="w"
            )

            # Start hidden
            self._root.withdraw()
            self._ready.set()
            log.info("Overlay started (tkinter pill)")
            self._root.mainloop()
        except Exception as exc:
            log.warning("Overlay failed to start (%s), continuing without it", exc)
            self._root = None
            self._canvas = None
            self._ready.set()

    def _draw_rounded_rect(self, x1, y1, x2, y2, radius=10, **kwargs):
        """Draw a rounded rectangle on the canvas."""
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
        ]
        return self._canvas.create_polygon(points, smooth=True, **kwargs)

    # ── Public API ───────────────────────────────────────────────────

    def show_recording(self) -> None:
        if self._root is None:
            return
        self._root.after(0, lambda: self._show_state(RED, "Recording..."))
        self._start_pulse()

    def show_processing(self) -> None:
        if self._root is None:
            return
        self._stop_pulse()
        self._root.after(0, lambda: self._show_state(AMBER, "Processing..."))

    def hide(self) -> None:
        if self._root is None:
            return
        self._stop_pulse()
        try:
            self._root.after(0, self._root.withdraw)
        except Exception:
            pass

    def stop(self) -> None:
        self._stop_pulse()
        if self._root is not None:
            try:
                self._root.after(0, self._root.destroy)
            except Exception:
                pass

    # ── Internal ─────────────────────────────────────────────────────

    def _show_state(self, dot_color: str, label: str) -> None:
        """Update dot color and label, then show the window."""
        try:
            if self._canvas is None:
                return
            self._canvas.itemconfig(self._dot_id, fill=dot_color)
            self._canvas.itemconfig(self._text_id, text=label)
            self._root.deiconify()
            self._root.lift()
        except Exception:
            pass

    def _start_pulse(self) -> None:
        self._pulse_running = True
        self._pulse_thread = threading.Thread(target=self._pulse_loop, daemon=True)
        self._pulse_thread.start()

    def _stop_pulse(self) -> None:
        self._pulse_running = False

    def _pulse_loop(self) -> None:
        """Animate the dot glow with a sine wave pulse."""
        start = time.monotonic()
        while self._pulse_running and self._root is not None:
            elapsed = time.monotonic() - start
            # Sine wave between 0.3 and 1.0
            alpha = 0.65 + 0.35 * math.sin(elapsed * 3.0)
            # Map alpha to a hex color for the glow
            r = int(244 * alpha * 0.3)
            g = int(67 * alpha * 0.3)
            b = int(54 * alpha * 0.3)
            glow_color = f"#{r:02x}{g:02x}{b:02x}"
            try:
                self._root.after(0, lambda c=glow_color: (
                    self._canvas.itemconfig(self._glow_id, fill=c) if self._canvas else None
                ))
            except Exception:
                break
            time.sleep(1.0 / 30)  # ~30 FPS
