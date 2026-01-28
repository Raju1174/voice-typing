"""Wispr Flow-style floating pill overlay for macOS using PyObjC.

Uses an NSPanel (always-on-top, click-through) to display a pill-shaped
recording/processing indicator at the bottom center of the screen.

Threading: pystray owns the main thread's NSApplication event loop.
All AppKit UI work is dispatched to the main thread via
performSelectorOnMainThread:withObject:waitUntilDone:.
"""

from __future__ import annotations

import logging
import math
import time

log = logging.getLogger(__name__)

try:
    import objc
    from AppKit import (
        NSApplication,
        NSBackingStoreBuffered,
        NSBezierPath,
        NSColor,
        NSFont,
        NSFontAttributeName,
        NSForegroundColorAttributeName,
        NSMakeRect,
        NSObject,
        NSPanel,
        NSScreen,
        NSString,
        NSTimer,
        NSView,
        NSWindowAbove,
    )
    from Foundation import NSMutableDictionary

    HAS_PYOBJC = True
except ImportError:
    HAS_PYOBJC = False


if HAS_PYOBJC:

    class PillView(NSView):
        """Custom NSView that draws the pill background, coloured dot, and label."""

        def initWithFrame_(self, frame):
            self = objc.super(PillView, self).initWithFrame_(frame)
            if self is None:
                return None
            self._dot_color = NSColor.redColor()
            self._label = "Recording..."
            self._pulse_alpha = 1.0
            return self

        def isFlipped(self):
            return True

        def setDotColor_label_(self, color, label):
            self._dot_color = color
            self._label = label
            self._pulse_alpha = 1.0
            self.setNeedsDisplay_(True)

        def setPulseAlpha_(self, alpha):
            self._pulse_alpha = alpha
            self.setNeedsDisplay_(True)

        def drawRect_(self, rect):
            bounds = self.bounds()
            w = bounds.size.width
            h = bounds.size.height
            radius = h / 2.0

            # --- Pill background ---
            bg = NSColor.colorWithCalibratedRed_green_blue_alpha_(
                0.1, 0.1, 0.1, 0.92
            )
            bg.setFill()
            path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
                bounds, radius, radius
            )
            path.fill()

            # --- Coloured dot with pulse alpha ---
            dot_size = 10.0
            dot_x = 14.0
            dot_y = (h - dot_size) / 2.0
            dot_color_with_alpha = self._dot_color.colorWithAlphaComponent_(
                self._pulse_alpha
            )
            dot_color_with_alpha.setFill()
            dot_rect = NSMakeRect(dot_x, dot_y, dot_size, dot_size)
            NSBezierPath.bezierPathWithOvalInRect_(dot_rect).fill()

            # --- Glow around dot when recording ---
            if self._pulse_alpha < 1.0 or self._label == "Recording...":
                glow_alpha = self._pulse_alpha * 0.3
                glow_color = self._dot_color.colorWithAlphaComponent_(glow_alpha)
                glow_color.setFill()
                glow_inset = -3.0
                glow_rect = NSMakeRect(
                    dot_x + glow_inset,
                    dot_y + glow_inset,
                    dot_size - 2 * glow_inset,
                    dot_size - 2 * glow_inset,
                )
                NSBezierPath.bezierPathWithOvalInRect_(glow_rect).fill()

            # --- Text label ---
            attrs = NSMutableDictionary.dictionary()
            attrs[NSFontAttributeName] = NSFont.systemFontOfSize_weight_(13.0, 0.3)
            attrs[NSForegroundColorAttributeName] = (
                NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 1.0, 1.0, 0.9)
            )
            ns_str = NSString.stringWithString_(self._label)
            text_size = ns_str.sizeWithAttributes_(attrs)
            text_x = dot_x + dot_size + 10.0
            text_y = (h - text_size.height) / 2.0
            ns_str.drawAtPoint_withAttributes_((text_x, text_y), attrs)

    class Dispatcher(NSObject):
        """Trampolines method calls to the main thread."""

        def initWithOverlay_(self, overlay):
            self = objc.super(Dispatcher, self).init()
            if self is None:
                return None
            self._overlay = overlay
            return self

        def doCreatePanel_(self, _arg):
            self._overlay._create_panel_on_main()

        def doShowRecording_(self, _arg):
            self._overlay._show_recording_on_main()

        def doShowProcessing_(self, _arg):
            self._overlay._show_processing_on_main()

        def doHide_(self, _arg):
            self._overlay._hide_on_main()

        def doDestroy_(self, _arg):
            self._overlay._destroy_on_main()

        def pulseTick_(self, timer):
            self._overlay._pulse_tick()


class MacOverlay:
    """Wispr Flow-style floating pill overlay.

    Public API matches the existing Overlay class:
        start(), show_recording(), show_processing(), hide(), stop()
    """

    # Pill dimensions
    WIDTH = 180
    HEIGHT = 36

    def __init__(self) -> None:
        self._panel = None
        self._pill_view = None
        self._dispatcher = None
        self._pulse_timer = None
        self._pulse_start: float = 0.0
        self._is_recording = False

    def start(self) -> None:
        """Create the panel (dispatched to main thread)."""
        if not HAS_PYOBJC:
            log.warning("PyObjC not available, macOS overlay disabled")
            return
        self._dispatcher = Dispatcher.alloc().initWithOverlay_(self)
        self._dispatcher.performSelectorOnMainThread_withObject_waitUntilDone_(
            "doCreatePanel:", None, False
        )
        log.info("macOS overlay started")

    def show_recording(self) -> None:
        if self._dispatcher is None:
            return
        self._dispatcher.performSelectorOnMainThread_withObject_waitUntilDone_(
            "doShowRecording:", None, False
        )

    def show_processing(self) -> None:
        if self._dispatcher is None:
            return
        self._dispatcher.performSelectorOnMainThread_withObject_waitUntilDone_(
            "doShowProcessing:", None, False
        )

    def hide(self) -> None:
        if self._dispatcher is None:
            return
        self._dispatcher.performSelectorOnMainThread_withObject_waitUntilDone_(
            "doHide:", None, False
        )

    def stop(self) -> None:
        if self._dispatcher is None:
            return
        self._dispatcher.performSelectorOnMainThread_withObject_waitUntilDone_(
            "doDestroy:", None, False
        )

    # ── Main-thread implementations ──────────────────────────────────

    def _create_panel_on_main(self) -> None:
        screen = NSScreen.mainScreen()
        if screen is None:
            log.warning("No main screen found, overlay disabled")
            return

        screen_frame = screen.frame()
        visible = screen.visibleFrame()

        x = (screen_frame.size.width - self.WIDTH) / 2.0
        y = visible.origin.y + 60  # 60px from bottom of visible area

        panel_rect = NSMakeRect(x, y, self.WIDTH, self.HEIGHT)

        # NSPanel: floating, non-activating, utility style
        style_mask = 0  # borderless
        self._panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            panel_rect, style_mask, NSBackingStoreBuffered, False
        )
        self._panel.setLevel_(NSWindowAbove + 100)  # Always on top
        self._panel.setOpaque_(False)
        self._panel.setBackgroundColor_(NSColor.clearColor())
        self._panel.setHasShadow_(True)
        self._panel.setIgnoresMouseEvents_(True)  # Click-through
        self._panel.setCollectionBehavior_(
            (1 << 0) | (1 << 4)  # canJoinAllSpaces | fullScreenAuxiliary
        )

        # Create pill view
        content_rect = NSMakeRect(0, 0, self.WIDTH, self.HEIGHT)
        self._pill_view = PillView.alloc().initWithFrame_(content_rect)
        self._panel.setContentView_(self._pill_view)

        # Start hidden
        self._panel.orderOut_(None)

    def _show_recording_on_main(self) -> None:
        if self._panel is None:
            return
        self._is_recording = True
        red = NSColor.colorWithCalibratedRed_green_blue_alpha_(
            0.957, 0.263, 0.212, 1.0
        )
        self._pill_view.setDotColor_label_(red, "Recording...")
        self._panel.orderFront_(None)
        self._start_pulse()

    def _show_processing_on_main(self) -> None:
        if self._panel is None:
            return
        self._is_recording = False
        self._stop_pulse()
        amber = NSColor.colorWithCalibratedRed_green_blue_alpha_(
            1.0, 0.757, 0.027, 1.0
        )
        self._pill_view.setDotColor_label_(amber, "Processing...")
        self._panel.orderFront_(None)

    def _hide_on_main(self) -> None:
        if self._panel is None:
            return
        self._is_recording = False
        self._stop_pulse()
        self._panel.orderOut_(None)

    def _destroy_on_main(self) -> None:
        self._stop_pulse()
        if self._panel is not None:
            self._panel.orderOut_(None)
            self._panel.close()
            self._panel = None
        self._pill_view = None

    # ── Pulse animation ──────────────────────────────────────────────

    def _start_pulse(self) -> None:
        self._stop_pulse()
        self._pulse_start = time.monotonic()
        self._pulse_timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            1.0 / 30.0,  # ~30 FPS
            self._dispatcher,
            "pulseTick:",
            None,
            True,
        )

    def _stop_pulse(self) -> None:
        if self._pulse_timer is not None:
            self._pulse_timer.invalidate()
            self._pulse_timer = None

    def _pulse_tick(self) -> None:
        if self._pill_view is None or not self._is_recording:
            return
        elapsed = time.monotonic() - self._pulse_start
        # Smooth sine wave pulse between 0.35 and 1.0
        alpha = 0.675 + 0.325 * math.sin(elapsed * 3.0)
        self._pill_view.setPulseAlpha_(alpha)
