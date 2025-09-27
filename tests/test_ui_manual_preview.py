import types

import pytest

import ui
import ui_token_helpers as helpers


class DummyFile(types.SimpleNamespace):
    def __iter__(self):
        return iter(())


@pytest.fixture

def tmp_html_file(tmp_path):
    path = tmp_path / 'sample.html'
    path.write_text('<div>Attachment Preview</div>', encoding='utf-8')
    return path


def test_manual_preview_snapshot_with_html_body(tmp_html_file):
    choices, default, html_map = helpers.manual_preview_snapshot(
        manual_body='<p>Hello {{email}}</p>',
        manual_body_is_html=True,
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

    assert 'Body' in choices
    assert default == 'Body'
    body_html = html_map['Body']
    assert 'Hello' in body_html
    assert 'Body Preview' in body_html

def test_manual_preview_snapshot_with_attachment_only(tmp_html_file):
    dummy = DummyFile(name=str(tmp_html_file), orig_name='sample.html')
    choices, default, html_map = helpers.manual_preview_snapshot(
        manual_body='Plain content',
        manual_body_is_html=False,
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

    assert 'Attachment' in choices
    assert default in choices
    attachment_html = html_map['Attachment']
    assert 'Attachment Preview' in attachment_html
    assert 'sample.html' in attachment_html

def test_manual_update_preview_body_only_selects_valid_choice():
    mode_update, refresh_update, html_update, html_map = ui._manual_update_preview(
        manual_body='<p>Hello</p>',
        manual_body_is_html=True,
        manual_randomize_html=False,
        manual_tfn='',
        manual_extra_tags=[],
        manual_attachment_enabled=False,
        manual_attachment_mode='original',
        manual_attachment_files=[],
        manual_inline_html='',
        manual_inline_name='',
        selected_attachment=None,
        current_mode='Attachment',
    )

    assert mode_update['choices'] == ['Body']
    assert mode_update['value'] == 'Body'
    assert refresh_update['visible'] is True
    assert 'Body' in html_map
    assert '<div' in html_update['value']

def test_manual_update_preview_with_selected_attachment(tmp_html_file):
    dummy = DummyFile(name=str(tmp_html_file), orig_name='sample.html')
    mode_update, refresh_update, html_update, html_map = ui._manual_update_preview(
        manual_body='',
        manual_body_is_html=False,
        manual_randomize_html=False,
        manual_tfn='',
        manual_extra_tags=[],
        manual_attachment_enabled=True,
        manual_attachment_mode='original',
        manual_attachment_files=[dummy],
        manual_inline_html='',
        manual_inline_name='',
        selected_attachment='sample.html',
        current_mode='Body',
    )

    assert 'Attachment' in mode_update['choices']
    assert mode_update['value'] == 'Attachment'
    assert refresh_update['visible'] is True
    assert 'Attachment' in html_map
    assert 'sample.html' in html_map['Attachment']
    assert '<div' in html_update['value']



def _is_descendant(component, ancestor):
    parent = getattr(component, 'parent', None)
    while parent is not None:
        if parent is ancestor:
            return True
        parent = getattr(parent, 'parent', None)
    return False


def _collect_parent_labels(component):
    labels = []
    parent = getattr(component, 'parent', None)
    while parent is not None:
        labels.append(getattr(parent, 'label', None))
        parent = getattr(parent, 'parent', None)
    return labels


def test_manual_mode_has_setup_and_preview_tabs():
    demo = ui.gradio_ui()
    blocks = list(demo.blocks.values())
    manual_tab = next(comp for comp in blocks if type(comp).__name__ == 'Tab' and comp.label == 'Manual Mode')
    nested_tabs = [
        comp for comp in blocks
        if type(comp).__name__ == 'Tabs' and _is_descendant(comp, manual_tab)
    ]
    assert any([child.label for child in tabs.children] == ['Setup', 'Preview'] for tabs in nested_tabs)


def test_manual_preview_controls_within_preview_tab():
    demo = ui.gradio_ui()
    blocks = list(demo.blocks.values())
    manual_tab = next(comp for comp in blocks if type(comp).__name__ == 'Tab' and comp.label == 'Manual Mode')
    preview_html = next(
        comp for comp in blocks
        if type(comp).__name__ == 'HTML'
        and getattr(comp, 'label', None) == 'Preview'
        and _is_descendant(comp, manual_tab)
    )
    labels = _collect_parent_labels(preview_html)
    assert 'Manual Mode' in labels
    assert 'Preview' in labels


def test_manual_preview_mode_radio_within_preview_tab():
    demo = ui.gradio_ui()
    blocks = list(demo.blocks.values())
    manual_tab = next(comp for comp in blocks if type(comp).__name__ == 'Tab' and comp.label == 'Manual Mode')
    preview_radio = next(
        comp for comp in blocks
        if type(comp).__name__ == 'Radio'
        and getattr(comp, 'label', None) == 'Preview Source'
        and _is_descendant(comp, manual_tab)
    )
    labels = _collect_parent_labels(preview_radio)
    assert 'Manual Mode' in labels
    assert 'Preview' in labels
