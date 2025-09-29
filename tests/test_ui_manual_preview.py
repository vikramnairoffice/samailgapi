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


def test_manual_render_preview_requires_body_content():
    html_update = ui._manual_render_preview(
        preview_source='Body',
        manual_body='',
        manual_body_is_html=True,
        manual_inline_html='',
    )

    assert 'No Body HTML provided' in html_update['value']
    assert html_update['visible'] is True


def test_manual_render_preview_renders_body_html():
    html_update = ui._manual_render_preview(
        preview_source='Body',
        manual_body='<p>Hello</p>',
        manual_body_is_html=True,
        manual_inline_html='',
    )

    assert 'Body Preview' in html_update['value']
    assert '<p>Hello</p>' in html_update['value']


def test_manual_render_preview_requires_attachment_html():
    html_update = ui._manual_render_preview(
        preview_source='Attachment',
        manual_body='Ignored',
        manual_body_is_html=False,
        manual_inline_html='',
    )

    assert 'No Attachment HTML provided' in html_update['value']


def test_manual_render_preview_renders_inline_attachment():
    html_update = ui._manual_render_preview(
        preview_source='Attachment',
        manual_body='',
        manual_body_is_html=False,
        manual_inline_html='<div>Attachment</div>',
    )

    assert 'Attachment Preview' in html_update['value']
    assert '<div>Attachment</div>' in html_update['value']


def test_manual_preview_button_disabled_until_source_selected():
    demo = ui.gradio_ui()
    blocks = list(demo.blocks.values())
    preview_button = next(
        comp for comp in blocks
        if type(comp).__name__ == 'Button' and getattr(comp, 'value', None) == 'Preview'
    )
    assert preview_button.interactive is False


def test_manual_preview_mode_radio_has_no_default_selection():
    demo = ui.gradio_ui()
    blocks = list(demo.blocks.values())
    preview_radio = next(
        comp for comp in blocks
        if type(comp).__name__ == 'Radio'
        and getattr(comp, 'label', None) == 'Preview Source'
    )
    assert preview_radio.value is None
    labels = [choice[0] if isinstance(choice, tuple) else choice for choice in preview_radio.choices]
    assert labels == ['Body', 'Attachment']


def test_manual_toggle_attachments_only_adjusts_visibility():
    disabled_updates = ui._manual_toggle_attachments(False)
    enabled_updates = ui._manual_toggle_attachments(True)
    for update in (*disabled_updates, *enabled_updates):
        assert 'value' not in update
        assert 'choices' not in update
        assert set(update.keys()) <= {'visible', 'interactive', '__type__'}


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



def test_manual_tab_has_setup_and_preview_tabs():
    demo = ui.gradio_ui()
    blocks = list(demo.blocks.values())
    mode_tabs = next(
        comp for comp in blocks
        if type(comp).__name__ == 'Tabs' and getattr(comp, 'elem_id', None) == 'mode-tabs'
    )
    manual_tab = next(child for child in mode_tabs.children if child.label == 'Manual')
    nested_tabs = [
        comp for comp in blocks
        if type(comp).__name__ == 'Tabs' and _is_descendant(comp, manual_tab)
    ]
    assert any([child.label for child in tabs.children] == ['Setup', 'Preview'] for tabs in nested_tabs)


def test_manual_preview_controls_within_preview_tab():
    demo = ui.gradio_ui()
    blocks = list(demo.blocks.values())
    mode_tabs = next(
        comp for comp in blocks
        if type(comp).__name__ == 'Tabs' and getattr(comp, 'elem_id', None) == 'mode-tabs'
    )
    manual_tab = next(child for child in mode_tabs.children if child.label == 'Manual')
    preview_html = next(
        comp for comp in blocks
        if type(comp).__name__ == 'HTML'
        and getattr(comp, 'label', None) == 'Preview'
        and _is_descendant(comp, manual_tab)
    )
    labels = _collect_parent_labels(preview_html)
    assert 'Manual' in labels
    assert 'Preview' in labels


def test_manual_preview_mode_radio_within_preview_tab():
    demo = ui.gradio_ui()
    blocks = list(demo.blocks.values())
    mode_tabs = next(
        comp for comp in blocks
        if type(comp).__name__ == 'Tabs' and getattr(comp, 'elem_id', None) == 'mode-tabs'
    )
    manual_tab = next(child for child in mode_tabs.children if child.label == 'Manual')
    preview_radio = next(
        comp for comp in blocks
        if type(comp).__name__ == 'Radio'
        and getattr(comp, 'label', None) == 'Preview Source'
        and _is_descendant(comp, manual_tab)
    )
    labels = _collect_parent_labels(preview_radio)
    assert 'Manual' in labels
    assert 'Preview' in labels
