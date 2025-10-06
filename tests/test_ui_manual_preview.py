import types

import pytest

from simple_mailer import ui_token_helpers as helpers

from simple_mailer.orchestrator import email_manual


class DummyFile(types.SimpleNamespace):
    def __iter__(self):
        return iter(())


@pytest.fixture
def tmp_html_file(tmp_path):
    path = tmp_path / 'sample.html'
    path.write_text('<div>Attachment Preview</div>', encoding='utf-8')
    return path


def test_manual_preview_snapshot_with_html_body(tmp_html_file):
    choices, default, html_map, meta = helpers.manual_preview_snapshot(
        manual_body='<p>Hello {{email}}</p>',
        manual_body_is_html=True,
        manual_body_image_enabled=False,
        manual_randomize_html=False,
        manual_tfn='',
        manual_extra_tags=[],
        manual_attachment_enabled=False,
        manual_attachment_mode='original',
        manual_attachment_files=[],
        manual_inline_html='',
        manual_inline_name='',
        selected_attachment_name=None,
    )

    assert choices == ['Body']
    assert default == 'Body'
    assert meta['body_available'] is True
    assert meta['attachment_available'] is False
    body_html = html_map['Body']
    assert 'Hello' in body_html
    assert 'Body Preview' in body_html


def test_manual_preview_snapshot_with_attachment_only(tmp_html_file):
    dummy = DummyFile(name=str(tmp_html_file), orig_name='sample.html')
    choices, default, html_map, meta = helpers.manual_preview_snapshot(
        manual_body='',
        manual_body_is_html=False,
        manual_body_image_enabled=False,
        manual_randomize_html=False,
        manual_tfn='',
        manual_extra_tags=[],
        manual_attachment_enabled=True,
        manual_attachment_mode='original',
        manual_attachment_files=[dummy],
        manual_inline_html='',
        manual_inline_name='',
        selected_attachment_name='sample.html',
    )

    assert choices == ['Body', 'Attachment']
    assert default == 'Attachment'
    assert meta['body_available'] is False
    assert meta['attachment_available'] is True
    attachment_html = html_map['Attachment']
    assert 'Attachment Preview' in attachment_html
    assert 'sample.html' in attachment_html
    assert 'No body content available' in html_map['Body']


def test_build_preview_state_returns_inline_attachment(tmp_html_file):
    dummy = DummyFile(name=str(tmp_html_file), orig_name='sample.html')
    state = email_manual.build_preview_state(
        subject='Subject',
        body='',
        body_is_html=False,
        body_image_enabled=False,
        randomize_html=False,
        tfn='',
        extra_tags=[],
        attachment_enabled=True,
        attachment_mode='original',
        attachment_files=[dummy],
        inline_html='<div>Inline</div>',
        inline_name='inline.html',
        sender_name='',
        change_name=False,
        sender_type='business',
        selected_attachment_name='inline.html',
    )

    assert 'Attachment' in state.choices
    assert state.meta['attachment_available'] is True
    assert state.html_map['Attachment'].startswith('<div')


def test_build_preview_state_defaults_to_body_choice():
    state = email_manual.build_preview_state(
        subject='',
        body='<p>Body</p>',
        body_is_html=True,
        body_image_enabled=False,
        randomize_html=False,
        tfn='',
        extra_tags=[],
        attachment_enabled=False,
        attachment_mode='original',
        attachment_files=[],
        inline_html='',
        inline_name='',
        sender_name='',
        change_name=False,
        sender_type='business',
        selected_attachment_name=None,
    )

    assert state.default == 'Body'
    assert 'Body Preview' in state.html_map['Body']

