import os
import random
from pathlib import Path

import pytest

from core import attachments
from core import invoice as invoice_adapter


def _write_sample(directory: Path, name: str) -> Path:
    path = directory / name
    path.write_bytes(b"sample")
    return path


def test_choose_static_respects_seed(tmp_path, monkeypatch):
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    _write_sample(pdf_dir, "alpha.pdf")
    _write_sample(pdf_dir, "beta.pdf")

    image_dir = tmp_path / "images"
    image_dir.mkdir()
    _write_sample(image_dir, "one.png")
    _write_sample(image_dir, "two.jpg")

    monkeypatch.setattr(attachments, "PDF_ATTACHMENT_DIR", str(pdf_dir))
    monkeypatch.setattr(attachments, "IMAGE_ATTACHMENT_DIR", str(image_dir))

    selection = attachments.choose_static(include_pdfs=True, include_images=True, seed=11)
    assert selection == attachments.choose_static(True, True, seed=11)

    rng = random.Random(11)
    expected_pdf = rng.choice(sorted(str(path) for path in pdf_dir.glob("*.pdf")))
    expected_image = rng.choice(
        sorted(
            str(path)
            for path in list(image_dir.glob("*.jpg")) + list(image_dir.glob("*.png"))
        )
    )

    assert selection == {
        os.path.basename(expected_pdf): expected_pdf,
        os.path.basename(expected_image): expected_image,
    }


def test_choose_from_folder_errors_for_missing_directory(tmp_path):
    with pytest.raises(RuntimeError) as exc:
        attachments.choose_from_folder(tmp_path / "missing")
    assert "not found" in str(exc.value)


def test_choose_from_folder_returns_random_file(tmp_path):
    folder = tmp_path / "attachments"
    folder.mkdir()
    first = _write_sample(folder, "first.bin")
    second = _write_sample(folder, "second.bin")

    chosen = attachments.choose_from_folder(folder, seed=3)
    assert chosen in ({first.name: str(first)}, {second.name: str(second)})

    assert attachments.choose_from_folder(folder, seed=3) == chosen


def test_build_uses_folder_override_without_invoice(tmp_path):
    folder = tmp_path / "docs"
    folder.mkdir()
    sample = _write_sample(folder, "doc.txt")

    config = {
        "email_content_mode": "Attachment",
        "attachment_folder": str(folder),
        "attachment_format": "pdf",
    }

    def fail_factory():  # pragma: no cover - ensure invoice factory is unused
        raise AssertionError("Invoice factory should not be invoked")

    result = attachments.build(config, "lead@example.com", invoice_factory=fail_factory)
    assert result == {sample.name: str(sample)}


def test_build_generates_invoice_for_invoice_mode(tmp_path):
    generated = tmp_path / "invoice.pdf"
    generated.write_bytes(b"invoice")

    calls = []

    class DummyInvoice:
        def generate_for_recipient(self, email, support_number, fmt):
            calls.append((email, support_number, fmt))
            return str(generated)

    def factory():
        return DummyInvoice()

    config = {
        "email_content_mode": "invoice",
        "invoice_format": "heif",
        "support_number": "555-0100",
    }

    result = attachments.build(config, "lead@example.com", invoice_factory=factory)
    assert result == {generated.name: str(generated)}
    assert calls == [("lead@example.com", "555-0100", "heif")]


def test_invoice_adapter_wraps_legacy(monkeypatch):
    instantiated = []

    class StubLegacy:
        def __init__(self):
            instantiated.append(self)
            self.saved = []

        def generate_for_recipient(self, email, phone_numbers, fmt):
            self.saved.append((email, phone_numbers, fmt))
            return "path/to/invoice"

    monkeypatch.setattr(invoice_adapter, "_LEGACY_GENERATOR", StubLegacy)

    generator = invoice_adapter.InvoiceGenerator()
    path = generator.generate_for_recipient("lead@example.com", "123", "png")

    assert path == "path/to/invoice"
    assert instantiated and instantiated[0].saved == [("lead@example.com", "123", "png")]
