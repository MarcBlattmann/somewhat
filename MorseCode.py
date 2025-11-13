#!/usr/bin/env python3
# morse_console_translator.py

from typing import Dict
import os, sys, subprocess, platform

# --- optional colors (for screen only) ---
try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init()
    USE_COLORS = True
except Exception:
    class _N: RESET_ALL = ""
    class _F: GREEN = ""; CYAN = ""
    Style = _N()
    Fore = _F()
    USE_COLORS = False

def cgreen(s: str) -> str:
    return f"{Fore.GREEN}{s}{Style.RESET_ALL}" if USE_COLORS else s

def ccyan(s: str) -> str:
    return f"{Fore.CYAN}{s}{Style.RESET_ALL}" if USE_COLORS else s

# --- clipboard backends (native only + pyperclip if installed) ---
_pyclip = None
try:
    import pyperclip  # type: ignore
    _pyclip = pyperclip
except Exception:
    pass

def _run_pipe(cmd, data: str) -> bool:
    try:
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        p.communicate(input=data.encode("utf-8"))
        return p.returncode == 0
    except Exception:
        return False

def copy_to_clipboard(text: str) -> bool:
    # Morse should be pure ASCII; sanitize just in case
    safe = "".join(ch for ch in text if ch in ".-/ \t")
    # 1) pyperclip if available (uses native APIs on each OS)
    if _pyclip:
        try:
            _pyclip.copy(safe)
            return True
        except Exception:
            pass
    # 2) OS-native CLIs
    system = platform.system().lower()
    if "windows" in system:
        # clip.exe expects CRLF or LF—either is fine; no BOM, no NULs
        return _run_pipe(["clip"], safe)
    if "darwin" in system:  # macOS
        return _run_pipe(["pbcopy"], safe)
    # Linux/BSD: try xclip, then xsel
    if _run_pipe(["xclip", "-selection", "clipboard"], safe):
        return True
    if _run_pipe(["xsel", "--clipboard", "--input"], safe):
        return True
    return False

# --- emoji mappings ---
EMOJI_TO_REFERENCE: Dict[str, str] = {
    "😀": "GRINNING_FACE",
    "😁": "BEAMING_FACE",
    "😂": "FACE_WITH_TEARS_OF_JOY",
    "😃": "GRINNING_FACE_WITH_BIG_EYES",
    "😄": "GRINNING_FACE_WITH_SMILING_EYES",
    "😅": "GRINNING_FACE_WITH_SWEAT",
    "😆": "GRINNING_SQUINTING_FACE",
    "😉": "WINKING_FACE",
    "😊": "SMILING_FACE_WITH_SMILING_EYES",
    "😍": "SMILING_FACE_WITH_HEART_EYES",
    "😘": "FACE_BLOWING_A_KISS",
    "😗": "KISSING_FACE",
    "😋": "FACE_SAVORING_FOOD",
    "😌": "RELIEVED_FACE",
    "😏": "SMIRKING_FACE",
    "😒": "UNAMUSED_FACE",
    "😔": "PENSIVE_FACE",
    "😪": "SLEEPY_FACE",
    "😓": "DOWNCAST_FACE_WITH_SWEAT",
    "😕": "CONFUSED_FACE",
    "😲": "ASTONISHED_FACE",
    "😞": "DISAPPOINTED_FACE",
    "😖": "CONFOUNDED_FACE",
    "😢": "CRYING_FACE",
    "😭": "LOUDLY_CRYING_FACE",
    "🤣": "ROLLING_ON_THE_FLOOR_LAUGHING",
    "😳": "FLUSHED_FACE",
    "😡": "POUTING_FACE",
    "😠": "ANGRY_FACE",
    "😤": "FACE_WITH_STEAM_FROM_NOSE",
    "😨": "FEARFUL_FACE",
    "😰": "ANXIOUS_FACE_WITH_SWEAT",
    "😧": "ANGUISHED_FACE",
    "😬": "GRIMACING_FACE",
    "😐": "NEUTRAL_FACE",
    "😑": "EXPRESSIONLESS_FACE",
    "😮": "FACE_WITH_OPEN_MOUTH",
    "❤️": "RED_HEART",
    "💔": "BROKEN_HEART",
    "💕": "TWO_HEARTS",
    "💖": "SPARKLING_HEART",
    "💗": "GROWING_HEART",
    "💘": "CUPID",
    "💚": "GREEN_HEART",
    "💙": "BLUE_HEART",
    "💜": "PURPLE_HEART",
    "💛": "YELLOW_HEART",
    "🎉": "PARTY_POPPER",
    "🎊": "CONFETTI_BALL",
    "🎈": "BALLOON",
    "🎁": "WRAPPED_GIFT",
    "⭐": "STAR",
    "✨": "SPARKLES",
    "🔥": "FIRE",
    "👍": "THUMBS_UP",
    "👎": "THUMBS_DOWN",
    "👋": "WAVING_HAND",
    "🙌": "RAISING_HANDS",
    "🤝": "HANDSHAKE",
    "🚀": "ROCKET",
    "🌟": "GLOWING_STAR",
    "☀️": "SUN",
    "🌙": "MOON",
    "⚡": "HIGH_VOLTAGE",
    "💧": "WATER_DROPLET",
}
REFERENCE_TO_EMOJI: Dict[str, str] = {v: k for k, v in EMOJI_TO_REFERENCE.items() if v != ""}

# Create a numeric index for emojis to use in morse encoding

# --- mappings ---
TEXT_TO_MORSE: Dict[str, str] = {
    "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".", "F": "..-.",
    "G": "--.", "H": "....", "I": "..", "J": ".---", "K": "-.-", "L": ".-..",
    "M": "--", "N": "-.", "O": "---", "P": ".--.", "Q": "--.-", "R": ".-.",
    "S": "...", "T": "-", "U": "..-", "V": "...-", "W": ".--", "X": "-..-",
    "Y": "-.--", "Z": "--..",
    "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-",
    "5": ".....", "6": "-....", "7": "--...", "8": "---..", "9": "----.",
    ".": ".-.-.-", ",": "--..--", "?": "..--..", "'": ".----.", "!": "-.-.--",
    "/": "-..-.", "(": "-.--.", ")": "-.--.-", "&": ".-...", ":": "---...",
    ";": "-.-.-.", "=": "-...-", "+": ".-.-.", "-": "-....-", "_": "..--.-",
    '"': ".-..-.", "$": "...-..-", "@": ".--.-."
}
MORSE_TO_TEXT: Dict[str, str] = {v: k for k, v in TEXT_TO_MORSE.items()}

def is_morse_line(s: str) -> bool:
    allowed = set(".-/ \t")
    s = s.strip()
    return s != "" and all(ch in allowed for ch in s) and any(ch in ".-" for ch in s)

def text_to_morse(s: str) -> str:
    out_words = []
    for word in s.strip().split():
        codes = []
        i = 0
        while i < len(word):
            ch = word[i]
            # Check if this is an emoji
            if ch in EMOJI_TO_REFERENCE:
                emoji_ref = EMOJI_TO_REFERENCE[ch]
                # Convert reference text to morse
                for ref_ch in emoji_ref:
                    morse_code = TEXT_TO_MORSE.get(ref_ch.upper())
                    if morse_code:
                        codes.append(morse_code)
                i += 1
            else:
                code = TEXT_TO_MORSE.get(ch.upper())
                codes.append(code if code else f"[{ch}]")
                i += 1
        out_words.append(" ".join(codes))
    return " / ".join(out_words)

def morse_to_text(s: str) -> str:
    words = []
    for raw_word in s.strip().split("/"):
        raw_word = raw_word.strip()
        if not raw_word:
            continue
        
        # First, decode all morse to text
        tokens = raw_word.split()
        decoded_chars = []
        for token in tokens:
            char = MORSE_TO_TEXT.get(token, "")
            if char:
                decoded_chars.append(char)
        
        decoded_text = "".join(decoded_chars)
        
        # Now check if parts of this text match emoji references and convert them back
        result = []
        i = 0
        while i < len(decoded_text):
            found_emoji = False
            # Try to match emoji references from longest to shortest
            for emoji_ref in sorted(REFERENCE_TO_EMOJI.keys(), key=len, reverse=True):
                if decoded_text[i:i+len(emoji_ref)] == emoji_ref:
                    emoji = REFERENCE_TO_EMOJI[emoji_ref]
                    result.append(emoji)
                    i += len(emoji_ref)
                    found_emoji = True
                    break
            
            if not found_emoji:
                result.append(decoded_text[i])
                i += 1
        
        words.append("".join(result))
    return " ".join(words)

def main():
    print(cgreen("Hello"))
    print(cgreen("Morse Code Output is copied to clipboard automatically!"))
    try:
        while True:
            line = input()
            if not line.strip():
                print("")
                continue
            if is_morse_line(line):
                print(ccyan(morse_to_text(line)))
            else:
                morse = text_to_morse(line)
                print(ccyan(morse))
                # auto-copy (silent)
                copy_to_clipboard(morse)
    except (EOFError, KeyboardInterrupt):
        pass

if __name__ == "__main__":
    main()
