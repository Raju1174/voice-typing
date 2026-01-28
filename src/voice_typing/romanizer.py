"""Devanagari / Urdu script to casual Roman Hindi (Hinglish) transliteration."""

from __future__ import annotations

import re

# ─── Hinglish word corrections ────────────────────────────────────────────────
# Maps common Whisper romanization mistakes to natural Hinglish spelling.
# Applied as whole-word replacements after romanization.
_HINGLISH_CORRECTIONS: dict[str, str] = {
    # Common loanwords Whisper writes in Devanagari instead of English
    'iskul': 'school', 'skul': 'school', 'iskool': 'school',
    'tichar': 'teacher', 'teechar': 'teacher',
    'ofis': 'office', 'ophis': 'office', 'aafis': 'office', 'daftar': 'office',
    'fon': 'phone', 'phon': 'phone',
    'kampyutar': 'computer', 'kampyootar': 'computer',
    'bais': 'bus',
    'plij': 'please', 'pleej': 'please',
    'sori': 'sorry',
    'thenk': 'thank', 'thaink': 'thank',
    'oke': 'okay', 'okei': 'okay',
    'mobaail': 'mobile', 'mobail': 'mobile',
    'daktar': 'doctor', 'doktar': 'doctor',
    'pulis': 'police', 'poolis': 'police',
    'tikat': 'ticket',
    'aspatal': 'hospital', 'asptaal': 'hospital',
    # Common Whisper mistakes for Hindi words
    'nahin': 'nahi',
    'kyonki': 'kyunki',
    'naheen': 'nahi',
}

# ─── Urdu (Arabic/Nastaliq) script → Roman ─────────────────────────────────────

_URDU_MAP = {
    # Consonants
    'ا': 'a', 'آ': 'aa', 'ب': 'b', 'پ': 'p', 'ت': 't', 'ٹ': 't',
    'ث': 's', 'ج': 'j', 'چ': 'ch', 'ح': 'h', 'خ': 'kh',
    'د': 'd', 'ڈ': 'd', 'ذ': 'z', 'ر': 'r', 'ڑ': 'r',
    'ز': 'z', 'ژ': 'zh', 'س': 's', 'ش': 'sh', 'ص': 's',
    'ض': 'z', 'ط': 't', 'ظ': 'z', 'ع': '', 'غ': 'gh',
    'ف': 'f', 'ق': 'q', 'ک': 'k', 'گ': 'g', 'ل': 'l',
    'م': 'm', 'ن': 'n', 'ں': 'n', 'و': 'o', 'ہ': 'h',
    'ھ': 'h', 'ء': '', 'ی': 'i', 'ے': 'e',
    # Vowel diacritics (harakat)
    '\u064E': 'a',   # fatha
    '\u064F': 'u',   # damma
    '\u0650': 'i',   # kasra
    '\u064B': 'an',  # tanween fatha
    '\u064C': 'un',  # tanween damma
    '\u064D': 'in',  # tanween kasra
    '\u0651': '',    # shadda (gemination, skip for casual)
    '\u0652': '',    # sukun
    # Common ligatures
    'لا': 'la',
}

# Characters that are Urdu joining forms / diacritics to skip
_URDU_SKIP = {'\u200C', '\u200D', '\u200E', '\u200F', '\uFEFF'}


def _romanize_urdu(text: str) -> str:
    """Transliterate Urdu (Arabic/Nastaliq) script to casual Roman."""
    result: list[str] = []
    i = 0
    while i < len(text):
        ch = text[i]

        # Two-char ligature check
        if i + 1 < len(text):
            pair = text[i:i+2]
            if pair in _URDU_MAP:
                result.append(_URDU_MAP[pair])
                i += 2
                continue

        if ch in _URDU_MAP:
            result.append(_URDU_MAP[ch])
        elif ch in _URDU_SKIP:
            pass  # skip zero-width joiners
        else:
            # Non-Urdu (space, punctuation, Latin, digits) pass through
            result.append(ch)
        i += 1

    return ''.join(result)


def _has_urdu(text: str) -> bool:
    """Check if text contains Urdu/Arabic script characters."""
    for ch in text:
        cp = ord(ch)
        # Arabic block: U+0600–U+06FF, Arabic Supplement: U+0750–U+077F
        if 0x0600 <= cp <= 0x06FF or 0x0750 <= cp <= 0x077F:
            return True
    return False


# ─── Devanagari → Roman ─────────────────────────────────────────────────────────

# Consonants → Roman (inherent 'a' handled by algorithm)
_CONSONANTS = {
    'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'ng',
    'च': 'ch', 'छ': 'ch', 'ज': 'j', 'झ': 'jh', 'ञ': 'n',
    'ट': 't', 'ठ': 'th', 'ड': 'd', 'ढ': 'dh', 'ण': 'n',
    'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
    'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm',
    'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'w',
    'श': 'sh', 'ष': 'sh', 'स': 's', 'ह': 'h',
}

# Nukta variants (consonant + ़) for Urdu-origin sounds
_NUKTA_CONSONANTS = {
    'क': 'q', 'ख': 'kh', 'ग': 'gh', 'ज': 'z',
    'ड': 'd', 'ढ': 'dh', 'फ': 'f',
}

# Independent vowels (long vowels doubled where natural in Hinglish)
_VOWELS = {
    'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'i',
    'उ': 'u', 'ऊ': 'oo', 'ऋ': 'ri', 'ॠ': 'ri',
    'ऌ': 'li', 'ॡ': 'li',
    'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au',
    'ऑ': 'o',  # Short O (English loanwords: ऑफिस → office)
}

# Vowel signs (matras) — replace the inherent 'a'
# Casual Hinglish: ा→aa, ू→oo; ी→i (people write "shaadi" not "shaadee")
_MATRAS = {
    'ा': 'aa', 'ि': 'i', 'ी': 'i',
    'ु': 'u', 'ू': 'oo', 'ृ': 'ri', 'ॄ': 'ri',
    'ॢ': 'li', 'ॣ': 'li',
    'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au',
}

_HALANT = '्'       # U+094D virama
_NUKTA = '़'        # U+093C
_ANUSVARA = 'ं'     # U+0902
_VISARGA = 'ः'      # U+0903
_CHANDRABINDU = 'ँ'  # U+0901

# Labial consonants — anusvara before these becomes 'm' instead of 'n'
_LABIALS = {'प', 'फ', 'ब', 'भ', 'म'}

_DIGITS = {
    '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
    '५': '5', '६': '6', '७': '7', '८': '8', '९': '9',
}

# Devanagari punctuation → Latin equivalents
_PUNCTUATION = {
    '।': '.',   # danda → period
    '॥': '.',   # double danda → period
    '॰': '.',   # abbreviation sign
}


def _tokenize_devanagari(text: str) -> list[list[tuple[str, str]]]:
    """Parse Devanagari text into words, each word as a list of (type, roman) tokens.

    Token types: 'C' = consonant (has inherent 'a'), 'V' = vowel/matra,
    'H' = halant, 'N' = nasal/modifier, 'O' = other (space, punct, latin).
    """
    words: list[list[tuple[str, str]]] = []
    current_word: list[tuple[str, str]] = []
    i = 0

    while i < len(text):
        ch = text[i]
        next_ch = text[i + 1] if i + 1 < len(text) else ''

        if ch in _CONSONANTS:
            # Check for nukta variant
            if next_ch == _NUKTA and ch in _NUKTA_CONSONANTS:
                current_word.append(('C', _NUKTA_CONSONANTS[ch]))
                i += 2
            else:
                current_word.append(('C', _CONSONANTS[ch]))
                i += 1

        elif ch == _HALANT:
            current_word.append(('H', ''))
            i += 1

        elif ch in _MATRAS:
            current_word.append(('V', _MATRAS[ch]))
            i += 1

        elif ch in _VOWELS:
            current_word.append(('V', _VOWELS[ch]))
            i += 1

        elif ch == _ANUSVARA:
            # Contextual: 'm' before labial consonants, 'n' otherwise
            nasal = 'n'
            for j in range(i + 1, len(text)):
                nch = text[j]
                if nch in _CONSONANTS:
                    if nch in _LABIALS:
                        nasal = 'm'
                    break
                if nch == _NUKTA or nch in _MATRAS:
                    continue
                break
            current_word.append(('N', nasal))
            i += 1

        elif ch == _VISARGA:
            current_word.append(('N', 'h'))
            i += 1

        elif ch == _CHANDRABINDU:
            current_word.append(('N', 'n'))
            i += 1

        elif ch == _NUKTA:
            i += 1  # stray nukta

        elif ch in _DIGITS:
            current_word.append(('O', _DIGITS[ch]))
            i += 1

        elif ch in _PUNCTUATION:
            # Word boundary
            if current_word:
                words.append(current_word)
                current_word = []
            words.append([('O', _PUNCTUATION[ch])])
            i += 1

        else:
            # Space, Latin, other — word boundary
            if current_word:
                words.append(current_word)
                current_word = []
            words.append([('O', ch)])
            i += 1

    if current_word:
        words.append(current_word)
    return words


def _apply_schwa_deletion(tokens: list[tuple[str, str]]) -> str:
    """Convert a tokenized Devanagari word to Roman with Hindi schwa deletion.

    Rules:
    - Word-final consonant: always drop schwa
    - First consonant sound in a word: keep schwa (no word-initial clusters)
    - Internal consonant followed by another consonant: drop schwa, UNLESS
      dropping would create a 3+ consonant cluster
    """
    if not tokens:
        return ''

    # Build elements: each consonant gets a potential schwa
    elements: list[tuple[str, str, bool]] = []  # (type, roman, has_schwa)

    for tok_type, tok_roman in tokens:
        if tok_type == 'C':
            elements.append(('C', tok_roman, True))  # consonant with pending schwa
        elif tok_type == 'H':
            # Halant: suppress schwa of previous consonant
            if elements and elements[-1][0] == 'C':
                elements[-1] = ('C', elements[-1][1], False)
        elif tok_type == 'V':
            # Vowel/matra: replaces schwa of previous consonant
            if elements and elements[-1][0] == 'C' and elements[-1][2]:
                elements[-1] = ('C', elements[-1][1], False)
            elements.append(('V', tok_roman, False))
        else:
            elements.append((tok_type, tok_roman, False))

    # Find consonants with pending schwas
    schwa_indices = [i for i, (t, _, has) in enumerate(elements) if t == 'C' and has]

    if not schwa_indices:
        return ''.join(r for _, r, _ in elements)

    # Find index of first phonetic element (first C or V in the word)
    first_sound_idx = next(
        (i for i, (t, _, _) in enumerate(elements) if t in ('C', 'V')), -1
    )

    for idx in schwa_indices:
        # Rule 1: Word-final — always drop
        remaining = [e for e in elements[idx+1:] if e[0] in ('C', 'V', 'N')]
        if not remaining:
            elements[idx] = ('C', elements[idx][1], False)
            continue

        # Rule 2: First consonant sound in the word — keep schwa
        if idx == first_sound_idx:
            continue

        # Rule 3: Check if next element is a consonant
        next_idx = None
        for j in range(idx + 1, len(elements)):
            if elements[j][0] in ('C', 'V', 'N'):
                next_idx = j
                break

        if next_idx is None or elements[next_idx][0] != 'C':
            continue  # next is vowel or nasal, keep schwa

        # Next is a consonant — check if deleting would create a 3+ phoneme cluster
        # Count consecutive consonant elements (phonemes) on each side
        left_count = 0
        for j in range(idx - 1, -1, -1):
            if elements[j][0] == 'C' and not elements[j][2]:
                left_count += 1
            else:
                break

        right_count = 0
        for j in range(next_idx + 1, len(elements)):
            if elements[j][0] == 'C' and not elements[j][2]:
                right_count += 1
            else:
                break

        # Total phonemes in cluster if we delete schwa
        total = left_count + 1 + 1 + right_count
        if total >= 3:
            continue  # would create a 3+ consonant cluster, keep schwa

        # Word-final cluster protection: don't create consonant clusters
        # at word end — "salamt" is unreadable, keep as "salamat"
        has_vowel_after = False
        for j in range(next_idx + 1, len(elements)):
            if elements[j][0] == 'V':
                has_vowel_after = True
                break
            if elements[j][0] in ('C', 'N'):
                break
        if not has_vowel_after:
            continue  # next consonant has no vowel after it, keep schwa

        # Safe to delete schwa
        elements[idx] = ('C', elements[idx][1], False)

    # Build final string
    result: list[str] = []
    for t, r, has_schwa in elements:
        result.append(r)
        if has_schwa:
            result.append('a')
    return ''.join(result)


def _hinglish_simplify(word: str) -> str:
    """Simplify long vowels for casual Hinglish writing conventions.

    Rules:
    - Word-final 'aa' → 'a' (करना → karna, not karnaa)
    - 'aa' before 2+ consonant chars → 'a' (चाहता → chahta, not chaahta)
    - 'aao' → 'ao', 'aau' → 'au', 'aae' → 'ae' (खाओ → khao)
    - Word-final 'oo' → 'o' is NOT simplified (हूँ → hoon stays)
    """
    # Simplify 'aa' before consonant clusters (2+ non-vowel chars)
    # चाहता: "chaahtaa" → "chahta" (aa before ht)
    word = re.sub(r'aa([^aeiou]{2,})', r'a\1', word)

    # Simplify 'aa' before consonant + 'a' (reduces internal doubles)
    # सलामत: "salaamat" → "salamat", क़ायम: "qaayam" → "qayam"
    # But preserves शादी: "shaadi" (aa before d+i, not d+a)
    word = re.sub(r'aa([^aeiou]+a)', r'a\1', word)

    # Simplify 'aa' before another vowel (except 'a' itself)
    # खाओ: "khaao" → "khao"
    word = re.sub(r'aa([eiou])', r'a\1', word)

    # Simplify word-final 'aa' → 'a'
    if word.endswith('aa'):
        word = word[:-1]

    # Nasalized 'e': में → "mein" not "men", दें → "dein" not "den"
    word = re.sub(r'en$', 'ein', word)

    return word


def _dict_lookup(text: str) -> str | None:
    """Look up a Devanagari word in the Hinglish dictionary.

    Strips punctuation for lookup and reattaches it after.
    Returns None if not found.
    """
    from voice_typing.hinglish_dict import HINGLISH_DICT

    stripped = text.strip('।॥,.!?;:')
    prefix = text[:len(text) - len(text.lstrip('।॥,.!?;:'))]
    suffix = text[len(stripped) + len(prefix):]

    result = HINGLISH_DICT.get(stripped)
    if result is not None:
        return prefix + result + suffix
    return None


def romanize(text: str) -> str:
    """Transliterate Devanagari or Urdu script to casual Roman Hindi.

    Priority: dictionary lookup > algorithmic romanization.
    Detects which script is present and applies the appropriate transliteration.
    Non-target characters (Latin, punctuation, spaces) pass through unchanged.
    """
    if _has_urdu(text):
        return _romanize_urdu(text)

    # Split on spaces to enable per-word dictionary lookup
    raw_words = text.split(' ')
    output_parts: list[str] = []

    for raw_word in raw_words:
        # Try dictionary first
        dict_result = _dict_lookup(raw_word)
        if dict_result is not None:
            output_parts.append(dict_result)
            continue

        # Fall back to algorithmic romanization
        tokens = _tokenize_devanagari(raw_word)
        word_parts: list[str] = []
        for w in tokens:
            raw = _apply_schwa_deletion(w)
            if len(w) == 1 and w[0][0] == 'O':
                word_parts.append(raw)
            else:
                word_parts.append(_hinglish_simplify(raw))
        output_parts.append(''.join(word_parts))

    result = ' '.join(output_parts)

    # Apply whole-word corrections for common Whisper mistakes
    return _apply_corrections(result)


def _apply_corrections(text: str) -> str:
    """Apply whole-word Hinglish corrections to fix common Whisper mistakes."""
    words = text.split(' ')
    for i, w in enumerate(words):
        # Strip punctuation for lookup, reattach after
        stripped = w.strip('.,!?;:')
        suffix = w[len(stripped):]
        key = stripped.lower()
        if key in _HINGLISH_CORRECTIONS:
            replacement = _HINGLISH_CORRECTIONS[key]
            # Preserve original capitalization
            if stripped and stripped[0].isupper():
                replacement = replacement[0].upper() + replacement[1:]
            words[i] = replacement + suffix
    return ' '.join(words)


def format_text(text: str) -> str:
    """Capitalize first letter of each sentence and clean up spacing."""
    if not text:
        return text

    # Clean up extra spaces around punctuation
    text = text.strip()

    result: list[str] = []
    cap_next = True  # capitalize the next letter

    for ch in text:
        if cap_next and ch.isalpha():
            result.append(ch.upper())
            cap_next = False
        else:
            result.append(ch)
            if ch in '.?!':
                cap_next = True

    return ''.join(result)
