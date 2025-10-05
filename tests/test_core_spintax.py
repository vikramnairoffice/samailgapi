import random

import pytest

from core import spintax


def test_render_tags_uses_context_values():
    result = spintax.render_tags("Hello {{CONTENT}}", {"content": "World"})
    assert result == "Hello World"


def test_render_tags_leaves_unknown_tokens():
    text = "Hello {{UNKNOWN}}"
    assert spintax.render_tags(text, {}) == text


def test_expand_spintax_accepts_injected_rng():
    seed = 42
    expected_choice = random.Random(seed).choice(["left", "right"])
    rng = random.Random(seed)
    result = spintax.expand_spintax("{left|right}", rng)
    assert result == expected_choice


def test_expand_renders_tags_then_spintax():
    seed = 7
    context = {"content": "Friend"}
    expected_branch = random.Random(seed).choice(["x", "y"])
    rng = random.Random(seed)
    result = spintax.expand("Hello {{CONTENT}} {x|y}", context, rng)
    assert result == f"Hello Friend {expected_branch}"