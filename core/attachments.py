"""Attachment adapter bridging to legacy selection helpers."""
from __future__ import annotations

import glob
import os
import random
from typing import Any, Callable, Dict, Mapping, Optional

from content import IMAGE_ATTACHMENT_DIR as _DEFAULT_IMAGE_DIR
from content import PDF_ATTACHMENT_DIR as _DEFAULT_PDF_DIR

from . import invoice as invoice_adapter

PDF_ATTACHMENT_DIR = _DEFAULT_PDF_DIR
IMAGE_ATTACHMENT_DIR = _DEFAULT_IMAGE_DIR


def _choice(seq, *, seed: Optional[int] = None):
    if not seq:
        return None
    if seed is None:
        return random.choice(seq)
    rng = random.Random(seed)
    return rng.choice(seq)


def _normalize_path(path: os.PathLike[str] | str) -> str:
    return os.fspath(path)


def choose_static(include_pdfs: bool, include_images: bool, *, seed: Optional[int] = None) -> Dict[str, str]:
    attachments: Dict[str, str] = {}

    if include_pdfs:
        pdf_files = sorted(glob.glob(os.path.join(PDF_ATTACHMENT_DIR, "*.pdf")))
        chosen_pdf = _choice(pdf_files, seed=seed)
        if chosen_pdf:
            attachments[os.path.basename(chosen_pdf)] = _normalize_path(chosen_pdf)

    if include_images:
        jpg_files = glob.glob(os.path.join(IMAGE_ATTACHMENT_DIR, "*.jpg"))
        png_files = glob.glob(os.path.join(IMAGE_ATTACHMENT_DIR, "*.png"))
        image_files = sorted(jpg_files + png_files)
        chosen_image = _choice(image_files, seed=seed)
        if chosen_image:
            attachments[os.path.basename(chosen_image)] = _normalize_path(chosen_image)

    return attachments


def choose_from_folder(folder_path: os.PathLike[str] | str, *, seed: Optional[int] = None) -> Dict[str, str]:
    folder = os.path.abspath(os.path.expanduser(_normalize_path(folder_path)))
    if not os.path.exists(folder):
        raise RuntimeError(f"Attachment folder not found: {folder}")
    if not os.path.isdir(folder):
        raise RuntimeError(f"Attachment folder is not a directory: {folder}")

    try:
        entries = [entry.path for entry in os.scandir(folder) if entry.is_file()]
    except OSError as exc:  # pragma: no cover - propagate as runtime error
        raise RuntimeError(f"Failed to read attachment folder: {exc}") from exc

    if not entries:
        raise RuntimeError(f"No files available in attachment folder: {folder}")

    chosen = _choice(sorted(entries), seed=seed)
    if not chosen:
        raise RuntimeError(f"No files available in attachment folder: {folder}")

    return {os.path.basename(chosen): _normalize_path(chosen)}


def build(
    config: Mapping[str, Any],
    lead: str | Mapping[str, Any],
    invoice_factory: Optional[Callable[[], invoice_adapter.InvoiceGenerator]] = None,
    *,
    seed: Optional[int] = None,
) -> Dict[str, str]:
    mode = str(config.get("email_content_mode") or "attachment").strip().lower()

    if isinstance(lead, Mapping):
        lead_email = str(lead.get("email") or lead.get("Email") or lead)
    else:
        lead_email = str(lead)

    if mode == "attachment":
        folder_override = str(config.get("attachment_folder") or "").strip()
        if folder_override:
            return choose_from_folder(folder_override, seed=seed)

        fmt = str(config.get("attachment_format") or "pdf").strip().lower()
        include_pdfs = fmt == "pdf"
        include_images = fmt == "image"
        return choose_static(include_pdfs, include_images, seed=seed)

    invoice_format = str(config.get("invoice_format") or "pdf").strip().lower()
    support_number = str(config.get("support_number") or "")
    factory = invoice_factory or invoice_adapter.InvoiceGenerator
    generator = factory()
    invoice_path = generator.generate_for_recipient(lead_email, support_number, invoice_format)
    resolved_path = _normalize_path(invoice_path)
    return {os.path.basename(resolved_path): resolved_path}


__all__ = [
    "PDF_ATTACHMENT_DIR",
    "IMAGE_ATTACHMENT_DIR",
    "choose_static",
    "choose_from_folder",
    "build",
]
