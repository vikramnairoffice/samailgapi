import sys
import time
from pathlib import Path
from typing import Dict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from invoice import InvoiceGenerator, REMOTE_LOGO_CACHE_DIR, REMOTE_LOGO_URLS

RECIPIENT = "remote.logo.test@example.com"
PHONE_NUMBERS = "800-555-0100\n800-555-0199"


def clear_cache() -> None:
    if REMOTE_LOGO_CACHE_DIR.exists():
        for item in REMOTE_LOGO_CACHE_DIR.iterdir():
            if item.is_file():
                item.unlink(missing_ok=True)


def timed_invoice_generation(generator: InvoiceGenerator, fmt: str) -> Dict[str, float | str]:
    start = time.perf_counter()
    path = generator.generate_for_recipient(RECIPIENT, PHONE_NUMBERS, output_format=fmt)
    elapsed = time.perf_counter() - start
    print(f"Generated {fmt.upper()} invoice in {elapsed:.2f}s: {path}")
    return {"format": fmt, "path": path, "elapsed": elapsed}


def generate_invoices():
    print(f"Testing remote logos from {len(REMOTE_LOGO_URLS)} URLs")
    clear_cache()

    generator = InvoiceGenerator()

    total_start = time.perf_counter()
    pdf_info = timed_invoice_generation(generator, "pdf")
    png_info = timed_invoice_generation(generator, "png")
    heif_info = timed_invoice_generation(generator, "heif")
    total_elapsed = time.perf_counter() - total_start

    print("--- Timing summary (seconds) ---")
    print(f"pdf: {pdf_info['elapsed']:.2f}")
    print(f"png: {png_info['elapsed']:.2f}")
    print(f"heif: {heif_info['elapsed']:.2f}")
    print(f"total: {total_elapsed:.2f}")

    return {
        "pdf": pdf_info["path"],
        "png": png_info["path"],
        "heif": heif_info["path"],
        "timings": {
            "pdf": pdf_info["elapsed"],
            "png": png_info["elapsed"],
            "heif": heif_info["elapsed"],
            "total": total_elapsed,
        },
    }


if __name__ == "__main__":
    generate_invoices()
