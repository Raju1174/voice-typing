"""Devanagari to casual Roman Hindi (Hinglish) transliteration."""

from __future__ import annotations

# Consonants → Roman (inherent 'a' handled by algorithm)
_CONSONANTS = {
    'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'ng',
    'च': 'ch', 'छ': 'chh', 'ज': 'j', 'झ': 'jh', 'ञ': 'n',
    'ट': 't', 'ठ': 'th', 'ड': 'd', 'ढ': 'dh', 'ण': 'n',
    'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
    'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm',
    'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v',
    'श': 'sh', 'ष': 'sh', 'स': 's', 'ह': 'h',
}

# Nukta variants (consonant + ़) for Urdu-origin sounds
_NUKTA_CONSONANTS = {
    'क': 'q', 'ख': 'kh', 'ग': 'gh', 'ज': 'z',
    'ड': 'r', 'ढ': 'rh', 'फ': 'f',
}

# Independent vowels
_VOWELS = {
    'अ': 'a', 'आ': 'a', 'इ': 'i', 'ई': 'i',
    'उ': 'u', 'ऊ': 'u', 'ऋ': 'ri', 'ॠ': 'ri',
    'ऌ': 'li', 'ॡ': 'li',
    'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au',
}

# Vowel signs (matras) — replace the inherent 'a'
_MATRAS = {
    'ा': 'a', 'ि': 'i', 'ी': 'i',
    'ु': 'u', 'ू': 'u', 'ृ': 'ri', 'ॄ': 'ri',
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


def romanize(text: str) -> str:
    """Transliterate Devanagari text to casual Roman Hindi.

    Non-Devanagari characters (Latin, punctuation, spaces) pass through unchanged.
    Word-final inherent 'a' is dropped (Hindi schwa deletion).
    """
    result: list[str] = []
    i = 0
    pending_a = False  # consonant's inherent 'a' not yet resolved

    while i < len(text):
        ch = text[i]
        next_ch = text[i + 1] if i + 1 < len(text) else ''

        if ch in _CONSONANTS:
            # Flush pending inherent 'a' from previous consonant
            if pending_a:
                result.append('a')

            # Check for nukta variant
            if next_ch == _NUKTA and ch in _NUKTA_CONSONANTS:
                result.append(_NUKTA_CONSONANTS[ch])
                i += 2
            else:
                result.append(_CONSONANTS[ch])
                i += 1
            pending_a = True

        elif ch == _HALANT:
            # Virama — suppress inherent 'a'
            pending_a = False
            i += 1

        elif ch in _MATRAS:
            # Vowel sign replaces inherent 'a'
            pending_a = False
            result.append(_MATRAS[ch])
            i += 1

        elif ch in _VOWELS:
            if pending_a:
                result.append('a')
                pending_a = False
            result.append(_VOWELS[ch])
            i += 1

        elif ch == _ANUSVARA:
            if pending_a:
                result.append('a')
                pending_a = False
            # Contextual: 'm' before labial consonants, 'n' otherwise
            nasal = 'n'
            for j in range(i + 1, len(text)):
                nch = text[j]
                if nch in _CONSONANTS:
                    if nch in _LABIALS:
                        nasal = 'm'
                    break
                if nch == _NUKTA or nch in _MATRAS:
                    continue  # skip modifiers
                break
            result.append(nasal)
            i += 1

        elif ch == _VISARGA:
            if pending_a:
                result.append('a')
                pending_a = False
            result.append('h')
            i += 1

        elif ch == _CHANDRABINDU:
            if pending_a:
                result.append('a')
                pending_a = False
            result.append('n')
            i += 1

        elif ch == _NUKTA:
            # Stray nukta without preceding consonant — skip
            i += 1

        elif ch in _DIGITS:
            if pending_a:
                result.append('a')
                pending_a = False
            result.append(_DIGITS[ch])
            i += 1

        else:
            # Non-Devanagari (space, punctuation, Latin text, etc.)
            # Word boundary — drop inherent 'a' (Hindi schwa deletion)
            pending_a = False
            result.append(ch)
            i += 1

    # End of text — drop final inherent 'a' (word-final schwa deletion)
    return ''.join(result)
