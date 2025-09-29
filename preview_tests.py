"""Sanity checks for manual preview rendering."""

from ui import (
    _manual_render_preview,
    _manual_toggle_attachments,
)


HTML_SAMPLE = """<!DOCTYPE html><html><head><title>Test</title></head><body><h1>Hello</h1><p>World</p></body></html>"""


def assert_body_preview_renders():
    update = _manual_render_preview(
        preview_source='Body',
        manual_body=HTML_SAMPLE,
        manual_body_is_html=True,
        manual_inline_html='',
    )

    assert "<h1>Hello</h1>" in update["value"], "Body HTML should appear in preview"
    assert update["visible"] is True, "Preview area should be shown"


def assert_body_preview_requires_content():
    update = _manual_render_preview(
        preview_source='Body',
        manual_body="",
        manual_body_is_html=True,
        manual_inline_html='',
    )

    assert "No Body HTML provided" in update["value"]


def assert_attachment_preview_requires_content():
    update = _manual_render_preview(
        preview_source='Attachment',
        manual_body="",
        manual_body_is_html=False,
        manual_inline_html='',
    )

    assert "No Attachment HTML provided" in update["value"]


def assert_toggle_attachments_keeps_state():
    for enabled in (True, False):
        updates = _manual_toggle_attachments(enabled)
        for update in updates:
            assert 'value' not in update and 'choices' not in update
            assert set(update.keys()) <= {"visible", "interactive", "__type__"}


if __name__ == "__main__":
    assert_body_preview_renders()
    assert_body_preview_requires_content()
    assert_attachment_preview_requires_content()
    assert_toggle_attachments_keeps_state()
    print("Preview sanity checks passed.")
