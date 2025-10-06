import pytest

from simple_mailer.content import render_tagged_content


def test_render_tagged_content_replaces_curly_tag():
    result = render_tagged_content("Hello {{CONTENT}}", {"content": "World"})
    assert result == "Hello World"


def test_render_tagged_content_supports_legacy_hash_syntax():
    result = render_tagged_content("Hello #CONTENT#", {"content": "World"})
    assert result == "Hello World"
