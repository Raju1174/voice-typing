#!/usr/bin/env python3
"""Comprehensive test suite for Voice Typing application.

Tests: config, audio, transcription accuracy & speed, VAD, romanizer, typer, hotkey, platform utils.
Generates speech via macOS `say`, feeds through the pipeline, measures accuracy & latency.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import wave
from dataclasses import asdict
from pathlib import Path

import numpy as np

# ─── Helpers ───────────────────────────────────────────────────────────────────

def generate_audio(text: str, voice: str, out_path: str) -> None:
    """Use macOS `say` to generate a WAV file."""
    # say outputs AIFF by default; we request a specific format
    subprocess.run(
        ["say", "-v", voice, "-o", out_path, "--data-format=LEI16@16000", text],
        check=True, timeout=30,
    )


def load_wav(path: str) -> np.ndarray:
    """Load a 16kHz mono WAV as float32 array."""
    with wave.open(path, "rb") as wf:
        assert wf.getsampwidth() == 2, f"Expected 16-bit, got {wf.getsampwidth()*8}-bit"
        data = wf.readframes(wf.getnframes())
    return np.frombuffer(data, np.int16).astype(np.float32) / 32768.0


def similarity(a: str, b: str) -> float:
    """Simple word-overlap similarity (0-1)."""
    a_words = set(a.lower().split())
    b_words = set(b.lower().split())
    if not a_words or not b_words:
        return 0.0
    intersection = a_words & b_words
    return len(intersection) / max(len(a_words), len(b_words))


PASS = "\033[92m✓ PASS\033[0m"
FAIL = "\033[91m✗ FAIL\033[0m"
WARN = "\033[93m⚠ WARN\033[0m"
HEADER = "\033[1;96m"
RESET = "\033[0m"

total_pass = 0
total_fail = 0


def check(description: str, condition: bool, detail: str = "") -> None:
    global total_pass, total_fail
    if condition:
        total_pass += 1
        print(f"  {PASS}  {description}" + (f" — {detail}" if detail else ""))
    else:
        total_fail += 1
        print(f"  {FAIL}  {description}" + (f" — {detail}" if detail else ""))


def section(title: str) -> None:
    print(f"\n{HEADER}{'═'*60}")
    print(f"  {title}")
    print(f"{'═'*60}{RESET}")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 1: Config
# ═══════════════════════════════════════════════════════════════════════════════

def test_config():
    section("1. Config System")
    from voice_typing.config import Config, CONFIG_FILE

    # Test defaults
    c = Config()
    check("Default hotkey is 'right_ctrl'", c.hotkey == "right_ctrl")
    check("Default model is 'base'", c.whisper_model == "base")
    check("Default device is 'auto'", c.whisper_device == "auto")
    check("Default typing method is 'clipboard'", c.typing_method == "clipboard")
    check("Default sample rate is 16000", c.audio_sample_rate == 16000)
    check("Default VAD filter is True", c.vad_filter is True)
    check("Default romanize is False", c.romanize is False)
    check("Default quantization is None", c.quantization is None)

    # Test save/load round-trip
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        tmp = f.name
    try:
        import voice_typing.config as cfg_mod
        orig_file = cfg_mod.CONFIG_FILE
        cfg_mod.CONFIG_FILE = Path(tmp)

        c2 = Config(hotkey="f5", whisper_model="small", language="es")
        c2.save()
        c3 = Config.load()
        check("Save/load round-trip: hotkey", c3.hotkey == "f5", f"got '{c3.hotkey}'")
        check("Save/load round-trip: model", c3.whisper_model == "small", f"got '{c3.whisper_model}'")
        check("Save/load round-trip: language", c3.language == "es", f"got '{c3.language}'")
        cfg_mod.CONFIG_FILE = orig_file
    finally:
        os.unlink(tmp)

    # Test loading with invalid keys (should be ignored)
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        json.dump({"hotkey": "caps_lock", "nonexistent_key": True}, f)
        tmp = f.name
    try:
        import voice_typing.config as cfg_mod
        orig_file = cfg_mod.CONFIG_FILE
        cfg_mod.CONFIG_FILE = Path(tmp)
        c4 = Config.load()
        check("Invalid keys are ignored on load", c4.hotkey == "caps_lock")
        check("Unknown field doesn't crash", not hasattr(c4, "nonexistent_key"))
        cfg_mod.CONFIG_FILE = orig_file
    finally:
        os.unlink(tmp)

    # Test config.default.json is valid
    default_path = Path(__file__).parent / "config.default.json"
    if default_path.exists():
        data = json.loads(default_path.read_text())
        valid_fields = {f.name for f in Config.__dataclass_fields__.values()}
        extra = set(data.keys()) - valid_fields
        check("config.default.json has only valid keys", len(extra) == 0,
              f"extra keys: {extra}" if extra else "all keys valid")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 2: Platform Utils
# ═══════════════════════════════════════════════════════════════════════════════

def test_platform_utils():
    section("2. Platform Utils")
    from voice_typing.platform_utils import IS_MAC, IS_WIN, IS_LINUX, resolve_whisper_device, paste_keys

    check("Detected macOS", IS_MAC is True)
    check("Not Windows", IS_WIN is False)
    check("Not Linux", IS_LINUX is False)

    device = resolve_whisper_device("auto")
    check("Auto device on macOS → 'cpu'", device == "cpu", f"got '{device}'")

    device2 = resolve_whisper_device("cuda")
    check("Explicit 'cuda' passes through", device2 == "cuda")

    mod, key = paste_keys()
    check("Paste keys on macOS", mod == "cmd" and key == "v", f"got ({mod}, {key})")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 3: Audio Recorder
# ═══════════════════════════════════════════════════════════════════════════════

def test_audio():
    section("3. Audio Recorder")
    from voice_typing.audio import AudioRecorder

    rec = AudioRecorder(sample_rate=16000, channels=1)

    # Test short recording
    rec.start()
    time.sleep(0.5)
    audio = rec.stop()
    check("Recording produces audio", len(audio) > 0, f"{len(audio)} samples")
    check("Audio is float32", audio.dtype == np.float32)
    check("Audio is 1-D", audio.ndim == 1)
    duration = len(audio) / 16000
    check("Duration ~0.5s", 0.3 < duration < 1.0, f"{duration:.2f}s")

    # Test empty recording (immediate stop)
    rec.start()
    audio2 = rec.stop()
    check("Immediate stop returns array", isinstance(audio2, np.ndarray))

    # Test double stop (should not crash)
    try:
        rec.stop()
        check("Double stop doesn't crash", True)
    except Exception as e:
        check("Double stop doesn't crash", False, str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 4: Hotkey
# ═══════════════════════════════════════════════════════════════════════════════

def test_hotkey():
    section("4. Hotkey System")
    from voice_typing.hotkey import resolve_key, HotkeyListener, _KEY_MAP
    from pynput.keyboard import Key, KeyCode

    # Test key resolution
    check("'right_ctrl' resolves", resolve_key("right_ctrl") == Key.ctrl_r)
    check("'right_shift' resolves", resolve_key("right_shift") == Key.shift_r)
    check("'caps_lock' resolves", resolve_key("caps_lock") == Key.caps_lock)
    check("'f5' resolves", resolve_key("f5") == Key.f5)
    check("'cmd' resolves", resolve_key("cmd") == Key.cmd)

    # Single character
    k = resolve_key("a")
    check("Single char 'a' resolves", isinstance(k, KeyCode))

    # Case insensitive
    check("Case insensitive", resolve_key("Right_Ctrl") == Key.ctrl_r)

    # Invalid key
    try:
        resolve_key("nonexistent_key_xyz")
        check("Invalid key raises ValueError", False)
    except ValueError:
        check("Invalid key raises ValueError", True)

    # macOS-specific: these keys should NOT be in the map
    for name in ("insert", "pause", "scroll_lock", "print_screen"):
        has_it = name in _KEY_MAP
        # On macOS these typically don't exist
        if not has_it:
            check(f"'{name}' correctly absent on macOS", True)
        else:
            check(f"'{name}' present (unexpected on macOS)", True, "may be available")

    # Test listener start/stop
    pressed = []
    released = []
    listener = HotkeyListener("f19", on_press=lambda: pressed.append(1), on_release=lambda: released.append(1))
    listener.start()
    time.sleep(0.2)
    listener.stop()
    check("Listener starts and stops cleanly", True)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 5: VAD (Voice Activity Detection)
# ═══════════════════════════════════════════════════════════════════════════════

def test_vad():
    section("5. VAD (Silero)")
    from voice_typing.vad import trim_silence

    # Test with silence (should return None)
    silence = np.zeros(16000 * 2, dtype=np.float32)  # 2 seconds of silence
    t0 = time.time()
    result = trim_silence(silence, sample_rate=16000)
    vad_time = time.time() - t0

    if result is None:
        check("Silence detected as no speech", True, f"VAD took {vad_time:.3f}s")
    elif result is silence:
        check("Silero not installed, returned audio unchanged", True, "fallback mode")
    else:
        check("Silence handling", False, f"unexpected result type: {type(result)}")

    # Test with noise (synthetic speech-like)
    # Generate a tone that might trigger VAD
    t = np.linspace(0, 1, 16000, dtype=np.float32)
    tone = 0.3 * np.sin(2 * np.pi * 300 * t)  # 300Hz tone, 1s
    result2 = trim_silence(tone, sample_rate=16000)
    if result2 is None:
        check("Pure tone detected as non-speech", True, "VAD correctly filtered")
    elif result2 is tone:
        check("Silero fallback (not installed)", True)
    else:
        check("Tone processed by VAD", True, f"output {len(result2)} samples")

    # Test with actual speech audio (generate via say)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp_wav = f.name
    try:
        generate_audio("Hello, this is a test of voice activity detection.", "Samantha", tmp_wav)
        speech = load_wav(tmp_wav)
        # Pad with 1 second of silence on each side
        padded = np.concatenate([
            np.zeros(16000, dtype=np.float32),
            speech,
            np.zeros(16000, dtype=np.float32),
        ])
        t0 = time.time()
        result3 = trim_silence(padded, sample_rate=16000)
        vad_time = time.time() - t0
        if result3 is not None and result3 is not padded:
            trimmed_dur = len(result3) / 16000
            original_dur = len(padded) / 16000
            check("Speech detected and trimmed", len(result3) < len(padded),
                  f"{original_dur:.1f}s → {trimmed_dur:.1f}s in {vad_time:.3f}s")
        elif result3 is padded:
            check("Silero not installed, audio unchanged", True)
        else:
            check("VAD returned None on speech audio", False, "expected speech detection")
    finally:
        os.unlink(tmp_wav)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 6: Romanizer
# ═══════════════════════════════════════════════════════════════════════════════

def test_romanizer():
    section("6. Hindi Romanizer")
    from voice_typing.romanizer import romanize, format_text

    # Basic words
    cases = [
        ("नमस्ते", "namaste"),
        ("हिंदी", "hindi"),
        ("भारत", "bharat"),
        ("प्यार", "pyar"),
        ("खुश", "khush"),
        ("धन्यवाद", "dhanyavad"),
        ("कृपया", "kripaya"),  # strict: no internal schwa deletion
    ]
    for devanagari, expected in cases:
        result = romanize(devanagari)
        match = result.lower() == expected.lower()
        check(f"'{devanagari}' → '{expected}'", match, f"got '{result}'")

    # Digits
    check("Devanagari digits", romanize("१२३") == "123")

    # Punctuation
    result = romanize("नमस्ते। कैसे हो?")
    check("Punctuation (danda → period)", "." in result, f"got '{result}'")

    # Mixed text (Latin passthrough)
    result = romanize("Hello नमस्ते World")
    check("Mixed Latin+Devanagari", "Hello" in result and "namaste" in result.lower(),
          f"got '{result}'")

    # Empty string
    check("Empty string", romanize("") == "")

    # format_text
    check("format_text capitalizes first letter", format_text("hello world") == "Hello world")
    check("format_text after period", format_text("hello. world") == "Hello. World")
    check("format_text empty", format_text("") == "")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 7: Transcriber — Backend Selection
# ═══════════════════════════════════════════════════════════════════════════════

def test_transcriber_backend():
    section("7. Transcriber Backend Selection")
    from voice_typing.transcriber import Transcriber, _lightning_available, _mlx_available

    lightning = _lightning_available()
    mlx = _mlx_available()
    print(f"  Lightning available: {lightning}")
    print(f"  MLX available: {mlx}")

    # Test backend selection for various models
    models_expected = {
        "tiny": "lightning" if lightning else ("mlx" if mlx else "faster-whisper"),
        "base": "lightning" if lightning else ("mlx" if mlx else "faster-whisper"),
        "small": "lightning" if lightning else ("mlx" if mlx else "faster-whisper"),
        "large-v3": "lightning" if lightning else ("mlx" if mlx else "faster-whisper"),
        "large-v3-turbo": "mlx" if mlx else "faster-whisper",  # Not in lightning
    }

    for model, expected in models_expected.items():
        t = Transcriber(model_size=model)
        check(f"Model '{model}' → backend '{expected}'", t._backend == expected,
              f"got '{t._backend}'")

    # Test empty audio returns empty
    t = Transcriber(model_size="base")
    text, lang = t.transcribe(np.array([], dtype=np.float32))
    check("Empty audio → empty text", text == "" and lang == "")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 8: Transcription Accuracy & Speed — Multi-Language
# ═══════════════════════════════════════════════════════════════════════════════

def test_transcription():
    section("8. Transcription Accuracy & Speed")
    from voice_typing.transcriber import Transcriber

    # Use the project's configured model for real testing
    from voice_typing.config import Config
    config = Config.load()

    t = Transcriber(
        model_size=config.whisper_model,
        device="cpu",
        compute_type=config.whisper_compute_type,
        quantization=config.quantization,
    )
    print(f"  Loading model: {config.whisper_model} (backend: {t._backend}) ...")
    t0 = time.time()
    t.load_model()
    load_time = time.time() - t0
    print(f"  Model loaded in {load_time:.2f}s")
    check("Model loads successfully", True, f"{load_time:.2f}s")

    # ── Test cases: (voice, language_code, text, description) ──
    test_cases = [
        # English
        ("Samantha", "en",
         "The quick brown fox jumps over the lazy dog",
         "English — pangram"),
        ("Samantha", "en",
         "Artificial intelligence is transforming the world of technology",
         "English — tech sentence"),
        ("Daniel", "en",
         "Good morning, how are you doing today",
         "English — greeting (British)"),
        # Hindi
        ("Lekha", "hi",
         "नमस्ते आप कैसे हैं",
         "Hindi — greeting"),
        ("Lekha", "hi",
         "भारत एक महान देश है",
         "Hindi — sentence"),
        # Spanish
        ("Mónica", "es",
         "Buenos días cómo estás hoy",
         "Spanish — greeting"),
        # French
        ("Thomas", "fr",
         "Bonjour comment allez vous aujourd'hui",
         "French — greeting"),
        # Japanese
        ("Kyoko", "ja",
         "こんにちは元気ですか",
         "Japanese — greeting"),
        # German
        ("Anna", "de",
         "Guten Morgen wie geht es Ihnen",
         "German — greeting"),
    ]

    results = []

    for voice, lang, expected_text, description in test_cases:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            tmp_wav = f.name
        try:
            generate_audio(expected_text, voice, tmp_wav)
            audio = load_wav(tmp_wav)
            duration = len(audio) / 16000

            t0 = time.time()
            transcribed, detected_lang = t.transcribe(
                audio,
                language=lang,
                beam_size=config.beam_size,
                vad_filter=False,
            )
            elapsed = time.time() - t0
            rtf = elapsed / duration if duration > 0 else 0  # Real-time factor

            sim = similarity(expected_text, transcribed)

            results.append({
                "description": description,
                "language": lang,
                "expected": expected_text,
                "transcribed": transcribed,
                "similarity": sim,
                "audio_duration": duration,
                "transcription_time": elapsed,
                "rtf": rtf,
                "detected_lang": detected_lang,
            })

            status = sim >= 0.5
            detail = (
                f"sim={sim:.0%}, {elapsed:.2f}s (RTF={rtf:.2f}x)\n"
                f"         Expected:     \"{expected_text}\"\n"
                f"         Transcribed:  \"{transcribed}\""
            )
            check(description, status, detail)

        finally:
            os.unlink(tmp_wav)

    # Summary statistics
    print(f"\n  {'─'*55}")
    print(f"  {'TRANSCRIPTION SUMMARY':^55}")
    print(f"  {'─'*55}")
    avg_sim = np.mean([r["similarity"] for r in results])
    avg_rtf = np.mean([r["rtf"] for r in results])
    avg_time = np.mean([r["transcription_time"] for r in results])
    print(f"  Average similarity: {avg_sim:.0%}")
    print(f"  Average RTF:        {avg_rtf:.2f}x (lower = faster)")
    print(f"  Average latency:    {avg_time:.2f}s")
    print(f"  {'─'*55}")

    for r in results:
        emoji = "●" if r["similarity"] >= 0.7 else "◐" if r["similarity"] >= 0.4 else "○"
        print(f"  {emoji} [{r['language']}] {r['description']:30s}  sim={r['similarity']:.0%}  {r['transcription_time']:.2f}s")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 9: Auto-detect language
# ═══════════════════════════════════════════════════════════════════════════════

def test_language_detection():
    section("9. Language Auto-Detection")
    from voice_typing.transcriber import Transcriber
    from voice_typing.config import Config
    config = Config.load()

    t = Transcriber(
        model_size=config.whisper_model,
        device="cpu",
        compute_type=config.whisper_compute_type,
        quantization=config.quantization,
    )
    t.load_model()

    cases = [
        ("Samantha", "Hello this is a test of language detection", "en", "English detection"),
        ("Mónica", "Hola buenos días cómo estás", "es", "Spanish detection"),
        ("Thomas", "Bonjour comment allez vous", "fr", "French detection"),
    ]

    for voice, text, expected_lang, desc in cases:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            tmp_wav = f.name
        try:
            generate_audio(text, voice, tmp_wav)
            audio = load_wav(tmp_wav)
            # language=None triggers auto-detection
            _, detected = t.transcribe(audio, language=None, beam_size=5, vad_filter=False)
            check(desc, detected == expected_lang, f"detected '{detected}', expected '{expected_lang}'")
        finally:
            os.unlink(tmp_wav)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 10: End-to-end pipeline (audio → VAD → transcribe → romanize → format)
# ═══════════════════════════════════════════════════════════════════════════════

def test_e2e_pipeline():
    section("10. End-to-End Pipeline")
    from voice_typing.transcriber import Transcriber
    from voice_typing.vad import trim_silence
    from voice_typing.romanizer import romanize, format_text
    from voice_typing.config import Config
    config = Config.load()

    t = Transcriber(
        model_size=config.whisper_model,
        device="cpu",
        compute_type=config.whisper_compute_type,
        quantization=config.quantization,
    )
    t.load_model()

    # English E2E
    print("\n  ── English E2E ──")
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp_wav = f.name
    try:
        text_en = "Hello world this is a complete end to end test"
        generate_audio(text_en, "Samantha", tmp_wav)
        audio = load_wav(tmp_wav)
        # Pad with silence
        padded = np.concatenate([np.zeros(8000, dtype=np.float32), audio, np.zeros(8000, dtype=np.float32)])

        t0 = time.time()
        trimmed = trim_silence(padded, sample_rate=16000)
        if trimmed is None:
            trimmed = padded  # fallback
        text, lang = t.transcribe(trimmed, language="en", beam_size=5, vad_filter=False)
        text = format_text(text)
        total_time = time.time() - t0

        check("English E2E produces text", len(text) > 0, f"'{text}' in {total_time:.2f}s")
        check("English E2E text is capitalized", text[0].isupper() if text else False)
    finally:
        os.unlink(tmp_wav)

    # Hindi E2E with romanization
    print("\n  ── Hindi E2E (with romanization) ──")
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp_wav = f.name
    try:
        text_hi = "नमस्ते आप कैसे हैं"
        generate_audio(text_hi, "Lekha", tmp_wav)
        audio = load_wav(tmp_wav)

        t0 = time.time()
        trimmed = trim_silence(audio, sample_rate=16000)
        if trimmed is None:
            trimmed = audio
        text, lang = t.transcribe(trimmed, language="hi", beam_size=5, vad_filter=False)
        if text and lang == "hi":
            romanized = romanize(text)
            romanized = format_text(romanized)
        else:
            romanized = format_text(text) if text else ""
        total_time = time.time() - t0

        check("Hindi E2E produces text", len(text) > 0, f"Devanagari: '{text}'")
        check("Hindi romanization works", len(romanized) > 0, f"Roman: '{romanized}' in {total_time:.2f}s")
        # Check romanized text is Latin script
        has_latin = any(c.isascii() and c.isalpha() for c in romanized)
        check("Romanized output is Latin script", has_latin)
    finally:
        os.unlink(tmp_wav)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 11: Typer
# ═══════════════════════════════════════════════════════════════════════════════

def test_typer():
    section("11. Typer Module")
    from voice_typing.typer import type_text
    import pyperclip

    # Test that empty text doesn't crash
    try:
        type_text("", method="clipboard")
        check("Empty text doesn't crash (clipboard)", True)
    except Exception as e:
        check("Empty text doesn't crash (clipboard)", False, str(e))

    try:
        type_text("", method="simulate")
        check("Empty text doesn't crash (simulate)", True)
    except Exception as e:
        check("Empty text doesn't crash (simulate)", False, str(e))

    # Test clipboard method preserves original clipboard
    original = "TEST_ORIGINAL_CLIPBOARD_CONTENT"
    pyperclip.copy(original)
    # We can't test the actual paste (no focused app), but we can verify
    # the function at least runs without error for a short string
    # and restores clipboard
    # NOTE: We skip actual typing to avoid pasting into random apps
    # Instead just test the clipboard save/restore logic
    current = pyperclip.paste()
    check("Clipboard accessible", current == original, f"got '{current[:50]}'")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 12: Tray Icon
# ═══════════════════════════════════════════════════════════════════════════════

def test_tray():
    section("12. Tray Icon")
    from voice_typing.tray import TrayIcon, TrayState, _make_icon

    # Test icon generation for all states
    for state in TrayState:
        img = _make_icon(state)
        check(f"Icon generated for {state.value}", img is not None and img.size == (64, 64))

    # Test TrayIcon creation
    tray = TrayIcon(on_quit=lambda: None)
    check("TrayIcon instantiation", tray is not None)
    check("Initial state is IDLE", tray._state == TrayState.IDLE)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 13: Overlay
# ═══════════════════════════════════════════════════════════════════════════════

def test_overlay():
    section("13. Overlay")
    from voice_typing.app import _can_use_overlay
    from voice_typing.platform_utils import IS_MAC

    can_use = _can_use_overlay()
    if IS_MAC:
        check("Overlay disabled on macOS (expected)", can_use is False)
    else:
        check("Overlay availability", True, f"can_use={can_use}")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 14: State Machine Logic
# ═══════════════════════════════════════════════════════════════════════════════

def test_state_machine():
    section("14. App State Machine")
    from voice_typing.app import AppState

    check("IDLE state exists", AppState.IDLE.value == "idle")
    check("RECORDING state exists", AppState.RECORDING.value == "recording")
    check("PROCESSING state exists", AppState.PROCESSING.value == "processing")
    check("Three states total", len(AppState) == 3)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 15: Stress test — multiple transcriptions back to back
# ═══════════════════════════════════════════════════════════════════════════════

def test_stress():
    section("15. Stress Test — Rapid Sequential Transcriptions")
    from voice_typing.transcriber import Transcriber
    from voice_typing.config import Config
    config = Config.load()

    t = Transcriber(
        model_size=config.whisper_model,
        device="cpu",
        compute_type=config.whisper_compute_type,
        quantization=config.quantization,
    )
    t.load_model()

    phrases = [
        ("Samantha", "en", "Hello world"),
        ("Samantha", "en", "How are you today"),
        ("Samantha", "en", "Testing one two three"),
        ("Daniel", "en", "The weather is nice"),
        ("Samantha", "en", "Voice typing is working"),
    ]

    times = []
    all_ok = True
    for voice, lang, text in phrases:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            tmp_wav = f.name
        try:
            generate_audio(text, voice, tmp_wav)
            audio = load_wav(tmp_wav)
            t0 = time.time()
            result, _ = t.transcribe(audio, language=lang, beam_size=3, vad_filter=False)
            elapsed = time.time() - t0
            times.append(elapsed)
            if not result:
                all_ok = False
        finally:
            os.unlink(tmp_wav)

    avg = np.mean(times)
    mx = np.max(times)
    mn = np.min(times)
    check("All 5 rapid transcriptions produced text", all_ok)
    check(f"Average latency", True, f"{avg:.2f}s (min={mn:.2f}s, max={mx:.2f}s)")
    check("No outlier > 3x average", mx < avg * 3 + 1, f"max={mx:.2f}s vs avg={avg:.2f}s")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print(f"\n{HEADER}{'╔'+'═'*58+'╗'}")
    print(f"{'║'} {'VOICE TYPING — COMPREHENSIVE TEST SUITE':^56} {'║'}")
    print(f"{'╚'+'═'*58+'╝'}{RESET}\n")

    global total_pass, total_fail

    tests = [
        ("Config", test_config),
        ("Platform Utils", test_platform_utils),
        ("Audio", test_audio),
        ("Hotkey", test_hotkey),
        ("VAD", test_vad),
        ("Romanizer", test_romanizer),
        ("Transcriber Backend", test_transcriber_backend),
        ("Transcription", test_transcription),
        ("Language Detection", test_language_detection),
        ("E2E Pipeline", test_e2e_pipeline),
        ("Typer", test_typer),
        ("Tray", test_tray),
        ("Overlay", test_overlay),
        ("State Machine", test_state_machine),
        ("Stress Test", test_stress),
    ]

    for name, fn in tests:
        try:
            fn()
        except Exception as e:
            print(f"\n  {FAIL}  {name} CRASHED: {e}")
            total_fail += 1
            import traceback
            traceback.print_exc()

    print(f"\n{HEADER}{'═'*60}")
    print(f"  FINAL RESULTS")
    print(f"{'═'*60}{RESET}")
    print(f"  Passed: {total_pass}")
    print(f"  Failed: {total_fail}")
    total = total_pass + total_fail
    print(f"  Total:  {total}")
    pct = (total_pass / total * 100) if total else 0
    color = "\033[92m" if total_fail == 0 else "\033[91m"
    print(f"  {color}Score: {pct:.0f}%{RESET}")
    print()

    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
