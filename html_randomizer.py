import random
import re
from typing import Dict, Optional

_HEX_COLOR_PATTERN = re.compile(r"#(?P<hex>[0-9a-fA-F]{6})(?![0-9a-fA-F])")
_RGB_PATTERN = re.compile(r"(?P<prefix>rgb|rgba)\((?P<body>[^)]+)\)", re.IGNORECASE)
_FONT_PATTERN = re.compile(r"(font-family\s*:\s*)([^;{}]+)", re.IGNORECASE)


def _jitter_channel(value: int, rng: random.Random) -> int:
    delta = rng.randint(-40, 40)
    if delta == 0:
        delta = 1 if value < 255 else -1
    return max(0, min(255, value + delta))


def _mutate_hex(hex_digits: str, rng: random.Random) -> str:
    r = int(hex_digits[0:2], 16)
    g = int(hex_digits[2:4], 16)
    b = int(hex_digits[4:6], 16)
    new_r = _jitter_channel(r, rng)
    new_g = _jitter_channel(g, rng)
    new_b = _jitter_channel(b, rng)
    if (new_r, new_g, new_b) == (r, g, b):
        new_r = (r + 64) % 256
        new_g = (g + 96) % 256
        new_b = (b + 128) % 256
    return f"#{new_r:02X}{new_g:02X}{new_b:02X}"


def _mutate_rgb(prefix: str, body: str, rng: random.Random) -> str:
    parts = [segment.strip() for segment in body.split(',')]
    if len(parts) < 3:
        return f"{prefix}({body})"
    channels = parts[:3]
    remainder = parts[3:]
    mutated_channels = []
    for part in channels:
        try:
            value = float(part.rstrip('%'))
        except ValueError:
            mutated_channels.append(part)
            continue
        channel = int(max(0, min(255, value)))
        mutated_channels.append(str(_jitter_channel(channel, rng)))
    mutated = mutated_channels + remainder
    return f"{prefix.lower()}({', '.join(mutated)})"


def _rotate_fonts(value: str, rng: random.Random) -> str:
    families = [chunk.strip() for chunk in value.split(',') if chunk.strip()]
    if len(families) <= 1:
        return value
    offset = rng.randint(1, len(families) - 1)
    rotated = families[offset:] + families[:offset]
    return ', '.join(rotated)


def randomize_html(html: str, *, enabled: bool, seed: Optional[int] = None) -> str:
    if not enabled:
        return html
    if not html or not html.strip():
        return html

    rng = random.Random(seed)
    output = html

    hex_map: Dict[str, str] = {}
    hex_used = set()

    def replace_hex(match: re.Match[str]) -> str:
        original = match.group(0)
        key = original.lower()
        if key not in hex_map:
            hex_digits = match.group('hex')
            candidate = _mutate_hex(hex_digits, rng)
            attempts = 0
            while candidate.lower() in hex_used and attempts < 8:
                candidate = _mutate_hex(hex_digits, rng)
                attempts += 1
            hex_used.add(candidate.lower())
            hex_map[key] = candidate
        return hex_map[key]

    output = _HEX_COLOR_PATTERN.sub(replace_hex, output)

    rgb_map: Dict[str, str] = {}
    rgb_used = set()

    def replace_rgb(match: re.Match[str]) -> str:
        original = match.group(0)
        key = original.lower()
        if key not in rgb_map:
            prefix = match.group('prefix') or 'rgb'
            body = match.group('body')
            candidate = _mutate_rgb(prefix, body, rng)
            attempts = 0
            while candidate.lower() in rgb_used and attempts < 8:
                candidate = _mutate_rgb(prefix, body, rng)
                attempts += 1
            rgb_used.add(candidate.lower())
            rgb_map[key] = candidate
        return rgb_map[key]

    output = _RGB_PATTERN.sub(replace_rgb, output)

    font_map: Dict[str, str] = {}

    def replace_font(match: re.Match[str]) -> str:
        prefix = match.group(1)
        value = match.group(2)
        key = value.lower()
        if key not in font_map:
            font_map[key] = _rotate_fonts(value, rng)
        return f"{prefix}{font_map[key]}"

    output = _FONT_PATTERN.sub(replace_font, output)

    return output
