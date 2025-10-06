import manual_mode
import pytest

from simple_mailer.manual.manual_config_adapter import (
    create_config,
    build_context,
    render_subject as adapter_render_subject,
    render_body as adapter_render_body,
    build_attachments as adapter_build_attachments,
    render_email,
    parse_extra_tags as adapter_parse_extra_tags,
    to_attachment_specs as adapter_to_attachment_specs,
    preview_attachment as adapter_preview_attachment,
    resolve_sender_name as adapter_resolve_sender_name,
)


@pytest.fixture(autouse=True)
def reset_attachment_root(tmp_path, monkeypatch):
    monkeypatch.setattr(manual_mode, "_ATTACHMENT_ROOT", tmp_path)


def test_build_context_and_render_match_manual(monkeypatch):
    monkeypatch.setattr(manual_mode, "_finalize_html_payload", lambda html, enable_random, seed: html)
    monkeypatch.setattr(manual_mode, "_random_suffix", lambda: "fixed")
    config = create_config(
        enabled=True,
        subject="Hi {{email}}",
        body="<p>Hello {{email}}</p>",
        body_is_html=True,
        tfn="",
        randomize_html=False,
    )

    context = build_context(config, "lead@example.com")
    manual_context = config.build_context("lead@example.com")
    assert context == manual_context

    subject = adapter_render_subject(config, context)
    assert subject == config.render_subject(manual_context)

    body, subtype = adapter_render_body(config, context)
    manual_body, manual_subtype = config.render_body(manual_context)
    assert body == manual_body
    assert subtype == manual_subtype


def test_render_email_collects_payload(tmp_path, monkeypatch):
    monkeypatch.setattr(manual_mode, "_ATTACHMENT_ROOT", tmp_path)
    monkeypatch.setattr(manual_mode, "_finalize_html_payload", lambda html, enable_random, seed: html)
    monkeypatch.setattr(manual_mode, "_random_suffix", lambda: "fixed")

    specs = adapter_to_attachment_specs(inline_html="<p>Inline {{email}}</p>")
    config = create_config(
        enabled=True,
        subject="Subject {{email}}",
        body="Body {{email}}",
        body_is_html=False,
        tfn="",
        attachments_enabled=True,
        attachments=specs,
        attachment_mode="original",
        sender_name="Manual",
        change_name_every_time=False,
    )

    result = render_email(config, "lead@example.com")

    manual_context = config.build_context("lead@example.com")
    manual_subject = config.render_subject(manual_context)
    manual_body = config.render_body(manual_context)
    manual_attachments = config.build_attachments(manual_context)
    manual_sender = config.resolve_sender_name()

    assert result["context"] == manual_context
    assert result["subject"] == manual_subject
    assert result["body"] == manual_body[0]
    assert result["body_subtype"] == manual_body[1]
    assert result["attachments"] == manual_attachments
    assert result["sender_name"] == manual_sender


def test_attachment_helpers_wrap_manual(monkeypatch, tmp_path):
    monkeypatch.setattr(manual_mode, "_ATTACHMENT_ROOT", tmp_path)
    rows = [["Tag", "Value"], ["Other", " "]]
    assert adapter_parse_extra_tags(rows) == manual_mode.parse_extra_tags(rows)

    specs = adapter_to_attachment_specs(inline_html="<p>Inline</p>", inline_name="inline.html")
    assert len(specs) == 1
    kind, payload = adapter_preview_attachment(specs[0])
    assert kind == "html"
    assert payload == "<p>Inline</p>"

    config = create_config(
        enabled=True,
        subject="",
        body="",
        body_is_html=False,
        tfn="",
        attachments_enabled=True,
        attachments=specs,
        attachment_mode="original",
        sender_name="Manual",
        change_name_every_time=False,
    )

    context = build_context(config, "lead@example.com")
    attachments = adapter_build_attachments(config, context)
    assert attachments

    assert adapter_resolve_sender_name(config, fallback_type="business") == "Manual"
