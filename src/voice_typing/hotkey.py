"""Global hold-to-talk hotkey listener."""

from __future__ import annotations

import logging
from typing import Callable, Optional

from pynput.keyboard import Key, KeyCode, Listener

log = logging.getLogger(__name__)

def _build_key_map() -> dict[str, Key | KeyCode]:
    """Build key map, skipping keys not available on this platform."""
    km: dict[str, Key | KeyCode] = {}
    # Modifier keys — always available
    km["right_ctrl"] = Key.ctrl_r
    km["left_ctrl"] = Key.ctrl_l
    km["ctrl"] = Key.ctrl
    km["right_shift"] = Key.shift_r
    km["left_shift"] = Key.shift_l
    km["shift"] = Key.shift
    km["right_alt"] = Key.alt_r
    km["left_alt"] = Key.alt_l
    km["alt"] = Key.alt
    km["right_cmd"] = Key.cmd_r
    km["left_cmd"] = Key.cmd_l
    km["cmd"] = Key.cmd
    km["caps_lock"] = Key.caps_lock
    # Function keys
    for i in range(1, 21):
        try:
            km[f"f{i}"] = Key[f"f{i}"]
        except (KeyError, AttributeError):
            pass
    # Special keys — not all exist on every OS
    for name in ("insert", "pause", "scroll_lock", "print_screen"):
        try:
            km[name] = getattr(Key, name)
        except AttributeError:
            pass
    return km


_KEY_MAP = _build_key_map()


def resolve_key(name: str) -> Key | KeyCode:
    """Convert a config key name to a pynput key."""
    name_lower = name.lower().strip()
    if name_lower in _KEY_MAP:
        return _KEY_MAP[name_lower]
    # Single character key
    if len(name) == 1:
        return KeyCode.from_char(name)
    raise ValueError(f"Unknown hotkey name: {name!r}")


class HotkeyListener:
    """Listens for a hold-to-talk key. Calls on_press / on_release."""

    def __init__(
        self,
        key_name: str,
        on_press: Callable[[], None],
        on_release: Callable[[], None],
    ) -> None:
        self._target_key = resolve_key(key_name)
        self._on_press = on_press
        self._on_release = on_release
        self._pressed = False
        self._listener: Optional[Listener] = None
        log.info("Hotkey set to: %s -> %s", key_name, self._target_key)

    def start(self) -> None:
        """Start the global keyboard listener (daemon thread)."""
        self._listener = Listener(
            on_press=self._handle_press,
            on_release=self._handle_release,
        )
        self._listener.daemon = True
        self._listener.start()
        log.info("Hotkey listener started")

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    def _matches(self, key: Key | KeyCode) -> bool:
        return key == self._target_key

    def _handle_press(self, key: Key | KeyCode | None) -> None:
        if key is not None and self._matches(key) and not self._pressed:
            self._pressed = True
            self._on_press()

    def _handle_release(self, key: Key | KeyCode | None) -> None:
        if key is not None and self._matches(key) and self._pressed:
            self._pressed = False
            self._on_release()
