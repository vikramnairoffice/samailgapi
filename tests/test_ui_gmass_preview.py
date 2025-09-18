import itertools

import pytest
import ui_token_helpers as helpers


def test_build_gmass_preview_returns_urls(monkeypatch):
    captured = {}

    def fake_load_token_files(token_files):
        captured['token_files'] = token_files
        return (
            [
                {'email': 'niao78@gmail.com'},
                {'email': 'first.last+tag@example.com'},
            ],
            [],
        )

    monkeypatch.setattr(helpers, 'load_token_files', fake_load_token_files)

    status, table = helpers.build_gmass_preview('gmass', ['niao78.json'])

    assert captured['token_files'] == ['niao78.json']
    assert status == 'Completed! Check 2 GMass URLs.'
    assert table == [
        ['niao78@gmail.com', 'https://www.gmass.co/inbox?q=niao78'],
        ['first.last+tag@example.com', 'https://www.gmass.co/inbox?q=first.last%2Btag'],
    ]


def test_build_gmass_preview_handles_no_accounts(monkeypatch):
    monkeypatch.setattr(helpers, 'load_token_files', lambda files: ([], []))

    status, table = helpers.build_gmass_preview('gmass', ['missing.json'])

    assert status == 'No Gmail accounts available for GMass preview.'
    assert table == []


def test_build_gmass_preview_non_gmass_mode(monkeypatch):
    # load_token_files should not be called when mode is not GMass
    called = {'value': False}

    def fake_loader(token_files):
        called['value'] = True
        return ([], [])

    monkeypatch.setattr(helpers, 'load_token_files', fake_loader)

    status, table = helpers.build_gmass_preview('leads', ['file.json'])

    assert called['value'] is False
    assert status == ''
    assert table == []


def test_gmass_rows_to_markdown_generates_links():
    rows = [
        ['niao78@gmail.com', 'https://www.gmass.co/inbox?q=niao78'],
        ['first.last+tag@example.com', 'https://www.gmass.co/inbox?q=first.last%2Btag'],
    ]
    markdown = helpers.gmass_rows_to_markdown(rows)
    assert markdown == (
        '- [niao78@gmail.com](https://www.gmass.co/inbox?q=niao78)\n'
        '- [first.last+tag@example.com](https://www.gmass.co/inbox?q=first.last%2Btag)'
    )



def test_start_campaign_appends_gmass_preview(monkeypatch):
    preview_status = 'Completed! Check 1 GMass URLs.'
    preview_rows = [['niao78@gmail.com', 'https://www.gmass.co/inbox?q=niao78']]

    monkeypatch.setattr(helpers, 'build_gmass_preview', lambda mode, tokens: (preview_status, preview_rows))

    def fake_campaign_events(**kwargs):
        yield {
            'kind': 'progress',
            'account': 'niao78@gmail.com',
            'lead': 'lead@example.com',
            'success': True,
            'message': 'ok',
            'successes': 1,
            'total': 1,
        }
        yield {
            'kind': 'done',
            'message': 'Completed sends.'
        }

    monkeypatch.setattr(helpers, 'gmass_rows_to_markdown', lambda rows: '- [niao78@gmail.com](https://www.gmass.co/inbox?q=niao78)')
    monkeypatch.setattr(helpers, 'campaign_events', fake_campaign_events)

    generator = helpers.start_campaign(
        token_files=['niao78.json'],
        leads_file=None,
        leads_per_account=1,
        send_delay_seconds=0.0,
        mode='gmass',
        email_content_mode='Attachment',
        attachment_folder='',
        invoice_format='pdf',
        support_number='',
        advance_header=False,
        force_header=False,
        sender_name_type='default',
        content_template='own_proven',
    )

    outputs = list(itertools.islice(generator, 3))

    assert len(outputs[0]) == 5
    assert outputs[0][-2] == preview_status
    assert outputs[0][-1] == '- [niao78@gmail.com](https://www.gmass.co/inbox?q=niao78)'
    assert outputs[-1][-2] == preview_status
    assert outputs[-1][-1] == '- [niao78@gmail.com](https://www.gmass.co/inbox?q=niao78)'


def test_start_campaign_leads_mode_has_empty_preview(monkeypatch):
    monkeypatch.setattr(helpers, 'build_gmass_preview', lambda mode, tokens: ('unexpected', [['x']]))
    monkeypatch.setattr(helpers, 'gmass_rows_to_markdown', lambda rows: 'should-not-appear')

    def fake_campaign_events(**kwargs):
        yield {'kind': 'done', 'message': 'Finished.'}

    monkeypatch.setattr(helpers, 'campaign_events', fake_campaign_events)

    generator = helpers.start_campaign(
        token_files=['niao78.json'],
        leads_file=None,
        leads_per_account=1,
        send_delay_seconds=0.0,
        mode='leads',
        email_content_mode='Attachment',
        attachment_folder='',
        invoice_format='pdf',
        support_number='',
        advance_header=False,
        force_header=False,
        sender_name_type='default',
        content_template='own_proven',
    )

    outputs = list(generator)

    assert outputs[0][-2] == ''
    assert outputs[0][-1] == ''
