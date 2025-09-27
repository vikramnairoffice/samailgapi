import re

from html_randomizer import randomize_html


def _extract_colors(html: str):
    return set(re.findall(r"#[0-9a-fA-F]{6}", html))


def test_randomization_disabled_returns_input():
    html = "<html><body><p style='color:#112233'>Hello</p></body></html>"
    assert randomize_html(html, enabled=False) == html


def test_randomization_modifies_existing_colors_but_keeps_count():
    html = "<html><body><div style=\"background:#336699;color:#ffffff\">Hi</div></body></html>"
    randomized = randomize_html(html, enabled=True, seed=7)
    assert randomized != html
    colors_before = _extract_colors(html)
    colors_after = _extract_colors(randomized)
    assert colors_before != colors_after
    assert len(colors_before) == len(colors_after)


def test_randomization_seed_deterministic():
    html = "<html><body><p style='color:#112233'>Hello</p></body></html>"
    first = randomize_html(html, enabled=True, seed=42)
    second = randomize_html(html, enabled=True, seed=42)
    assert first == second
    assert '#112233' not in first
