import types

import ui


def _is_descendant(component, ancestor):
    parent = getattr(component, 'parent', None)
    while parent is not None:
        if parent is ancestor:
            return True
        parent = getattr(parent, 'parent', None)
    return False


def test_top_level_pages_follow_new_flow():
    demo = ui.gradio_ui()
    page_tabs = next(
        comp for comp in demo.blocks.values()
        if type(comp).__name__ == 'Tabs' and getattr(comp, 'elem_id', None) == 'page-tabs'
    )
    labels = [tab.label for tab in page_tabs.children]
    assert labels == ['Setup', 'Sending Modes', 'Multi Mode']


def test_setup_tab_contains_upload_controls_only():
    demo = ui.gradio_ui()
    blocks = list(demo.blocks.values())
    setup_tab = next(comp for comp in blocks if type(comp).__name__ == 'Tab' and comp.label == 'Setup')
    token_files = next(
        comp for comp in blocks
        if type(comp).__name__ == 'Files' and getattr(comp, 'label', '') == 'Credential Files'
    )
    leads_file = next(
        comp for comp in blocks
        if type(comp).__name__ == 'File' and getattr(comp, 'label', '') == 'Leads File (one email per line)'
    )
    delay_control = next(
        comp for comp in blocks
        if type(comp).__name__ == 'Number' and getattr(comp, 'label', '') == 'Delay Between Emails (seconds)'
    )
    assert _is_descendant(token_files, setup_tab)
    assert _is_descendant(leads_file, setup_tab)
    assert not _is_descendant(delay_control, setup_tab)


def test_sending_modes_tab_has_automatic_and_manual_without_nested_preview():
    demo = ui.gradio_ui()
    blocks = list(demo.blocks.values())
    mode_tabs = next(
        comp for comp in blocks
        if type(comp).__name__ == 'Tabs' and getattr(comp, 'elem_id', None) == 'mode-tabs'
    )
    labels = [tab.label for tab in mode_tabs.children]
    assert labels == ['Automatic', 'Manual']
    automatic_tab = next(tab for tab in mode_tabs.children if tab.label == 'Automatic')
    nested_tabs = [
        comp for comp in blocks
        if type(comp).__name__ == 'Tabs' and _is_descendant(comp, automatic_tab)
    ]
    assert nested_tabs == []


def test_manual_multi_accounts_from_tokens_prefers_orig_name():
    files = [
        types.SimpleNamespace(name='C:/tmp/alpha.json', orig_name='alpha.json'),
        types.SimpleNamespace(name='C:/tmp/beta.json', orig_name=None),
        types.SimpleNamespace(name='C:/tmp/sub/gamma.TXT', orig_name='gamma_special.txt'),
    ]
    assert ui._manual_multi_accounts_from_tokens(files) == ['alpha', 'beta', 'gamma_special']


def test_manual_multi_store_and_retrieve_config():
    initial_state = {}
    updated_state = ui._manual_multi_store_current(
        initial_state,
        'alpha',
        manual_subject='Hello',
        manual_body='Body',
        manual_body_is_html=True,
        manual_body_image_enabled=False,
        manual_randomize_html=True,
        manual_tfn='123',
        manual_extra_tags=['tag1'],
        manual_attachment_enabled=True,
        manual_attachment_mode='pdf',
        manual_attachment_files=[types.SimpleNamespace(name='file.pdf', orig_name='file.pdf')],
        manual_inline_html='inline.html',
        manual_inline_name='Inline',
        manual_sender_name='Sender',
        manual_change_name=False,
        manual_sender_type='Custom',
    )
    assert 'alpha' in updated_state
    stored = ui._manual_multi_get_config(updated_state, 'alpha')
    assert stored['manual_subject'] == 'Hello'
    assert stored['manual_randomize_html'] is True
    assert stored['manual_attachment_mode'] == 'pdf'


def test_manual_multi_default_config_provides_baseline():
    default = ui._manual_multi_default_config()
    assert default['manual_subject'] == ''
    assert default['manual_attachment_enabled'] is False
    assert default['manual_change_name'] is True
