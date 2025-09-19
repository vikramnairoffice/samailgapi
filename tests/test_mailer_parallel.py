import threading
from typing import Any, Dict, List

import pytest

import mailer


class _FakeInvoiceGen:
    def generate_for_recipient(self, lead_email: str, support_number: str, fmt: str) -> str:
        return "dummy.pdf"


def _build_accounts(count: int) -> List[Dict[str, Any]]:
    return [
        {
            "email": f"user{idx}@example.com",
            "creds": object(),
            "path": f"token{idx}.json",
        }
        for idx in range(count)
    ]


@pytest.fixture(autouse=True)
def _patch_invoice(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mailer, "InvoiceGenerator", lambda: _FakeInvoiceGen())


def test_run_campaign_emits_one_event_per_lead(monkeypatch: pytest.MonkeyPatch) -> None:
    accounts = _build_accounts(2)
    leads = ["lead1@example.com", "lead2@example.com", "lead3@example.com", "lead4@example.com"]
    recorded: List[Dict[str, Any]] = []

    def fake_sender(account: Dict[str, Any], lead: str, config: Dict[str, Any], invoice_gen: Any):
        recorded.append({"account": account["email"], "lead": lead})
        return True, "ok"

    monkeypatch.setattr(mailer, "send_single_email", fake_sender)
    monkeypatch.setattr(mailer.time, "sleep", lambda _: None)

    config = {
        "content_template": "own_proven",
        "email_content_mode": "attachment",
        "attachment_format": "pdf",
        "attachment_folder": "",
        "invoice_format": "pdf",
        "support_number": "",
        "sender_name_type": "business",
    }

    events = list(
        mailer.run_campaign(accounts, "manual", leads, 2, config, send_delay_seconds=0.0)
    )

    assert len(events) == len(leads)
    assert {event["lead"] for event in events} == set(leads)
    assert len(recorded) == len(leads)


def test_run_campaign_uses_distinct_worker_threads(monkeypatch: pytest.MonkeyPatch) -> None:
    accounts = _build_accounts(3)
    leads = [f"lead{i}@example.com" for i in range(6)]
    thread_names: List[str] = []

    def fake_sender(account: Dict[str, Any], lead: str, config: Dict[str, Any], invoice_gen: Any):
        thread_names.append(threading.current_thread().name)
        return True, "ok"

    monkeypatch.setattr(mailer, "send_single_email", fake_sender)
    monkeypatch.setattr(mailer.time, "sleep", lambda _: None)

    config = {
        "content_template": "own_proven",
        "email_content_mode": "attachment",
        "attachment_format": "pdf",
        "attachment_folder": "",
        "invoice_format": "pdf",
        "support_number": "",
        "sender_name_type": "business",
    }

    list(mailer.run_campaign(accounts, "manual", leads, 2, config, send_delay_seconds=0.0))

    assert len(set(thread_names)) >= 3

def test_distribute_leads_even_split_without_cap() -> None:
    leads = [f"lead{i}@example.com" for i in range(5)]
    assignments = mailer.distribute_leads(leads, 2, leads_per_account=1)
    assert [len(chunk) for chunk in assignments] == [3, 2]
    assert sorted(sum(assignments, [])) == sorted(leads)

def test_distribute_leads_handles_more_accounts_than_leads() -> None:
    leads = ["a@example.com", "b@example.com"]
    assignments = mailer.distribute_leads(leads, 3, leads_per_account=10)
    assert [len(chunk) for chunk in assignments] == [1, 1, 0]
