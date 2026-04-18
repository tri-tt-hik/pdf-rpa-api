"""
Step 1 — Trigger
Step 2 — Validate

Watchdog event handler: fires when a new PDF lands in input_pdfs/.
Validates the file before passing it to the pipeline.
"""

import os
import logging
from watchdog.events import FileSystemEventHandler
from PDF_RPA_CLOUD.rpa.pipeline import run_pipeline

log = logging.getLogger("rpa.trigger")

MAX_FILE_SIZE_MB = 50
PROCESSED_LOG = "logs/processed_files.txt"


def _already_processed(filepath: str) -> bool:
    """Check if this file was processed before (by filename)."""
    filename = os.path.basename(filepath)
    if not os.path.exists(PROCESSED_LOG):
        return False
    with open(PROCESSED_LOG, "r") as f:
        return filename in f.read().splitlines()


def _mark_processed(filepath: str):
    """Record filename in processed log."""
    filename = os.path.basename(filepath)
    with open(PROCESSED_LOG, "a") as f:
        f.write(filename + "\n")


def validate(filepath: str) -> tuple[bool, str]:
    """
    Step 2 — Validate.
    Returns (True, "") if valid, or (False, reason) if not.
    """
    # Check extension
    if not filepath.lower().endswith(".pdf"):
        return False, "Not a PDF file"

    # Check file exists and is readable
    if not os.path.isfile(filepath):
        return False, "File not found"

    # Check file size
    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        return False, f"File too large ({size_mb:.1f} MB > {MAX_FILE_SIZE_MB} MB)"

    # Check for duplicate
    if _already_processed(filepath):
        return False, "Already processed"

    return True, ""


class PDFEventHandler(FileSystemEventHandler):
    """Watchdog handler — triggers on new file creation."""

    def on_created(self, event):
        if event.is_directory:
            return

        filepath = event.src_path
        filename = os.path.basename(filepath)

        log.info(f"[TRIGGER] New file detected: {filename}")

        # Small delay to ensure file is fully written to disk
        import time
        time.sleep(1)

        # Step 2: Validate
        valid, reason = validate(filepath)
        if not valid:
            log.warning(f"[VALIDATE] Skipping '{filename}': {reason}")
            return

        log.info(f"[VALIDATE] '{filename}' passed validation. Starting pipeline...")
        _mark_processed(filepath)

        # Hand off to pipeline
        run_pipeline(filepath)
