"""
Pipeline Orchestrator

Ties all RPA steps together in sequence:
  1. Trigger   (in trigger.py)
  2. Validate  (in trigger.py)
  3. Extract   → extractor.py
  4. Structure → structurer.py
  5. Store     → storage.py
  6. Log       → logger.py  (runs throughout)
  7. Notify    → notifier.py

Called by trigger.py after validation passes.
"""

import os
import shutil
import logging

from PDF_RPA_CLOUD.rpa.extractor  import extract
from PDF_RPA_CLOUD.rpa.structurer import structure
from PDF_RPA_CLOUD.rpa.storage    import store
from PDF_RPA_CLOUD.rpa.notifier   import notify_success, notify_failure

log = logging.getLogger("rpa.pipeline")


def _move_file(src: str, dest_folder: str):
    """Move a processed/failed file to the appropriate archive folder."""
    os.makedirs(dest_folder, exist_ok=True)
    dest = os.path.join(dest_folder, os.path.basename(src))
    shutil.move(src, dest)
    log.info(f"[PIPELINE] Moved '{os.path.basename(src)}' → {dest_folder}/")


def run_pipeline(filepath: str):
    """
    Run the full RPA pipeline for a single PDF file.
    On success → file moved to processed/
    On failure → file moved to failed/
    """
    filename = os.path.basename(filepath)
    log.info(f"[PIPELINE] ── Starting pipeline for: {filename} ──")

    try:
        # Step 3: Extract
        extracted = extract(filepath)

        # Step 4: Structure
        structured = structure(extracted)

        # Step 5: Store
        output_path = store(structured)

        # Step 7: Notify success
        notify_success(filename, structured["summary_stats"], output_path)

        # Archive the original PDF
        _move_file(filepath, "processed")

        log.info(f"[PIPELINE] ── ✅ Completed: {filename} ──\n")

    except Exception as e:
        log.exception(f"[PIPELINE] ── ❌ Failed: {filename} — {e} ──\n")
        notify_failure(filename, str(e))
        _move_file(filepath, "failed")
