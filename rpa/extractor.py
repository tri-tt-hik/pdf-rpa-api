"""
Step 3 — Extract

Extracts text, tables, and metadata from a PDF using pdfplumber.
No ML models — pure library-based extraction.
"""

import logging
import pdfplumber

log = logging.getLogger("rpa.extractor")


def extract(filepath: str) -> dict:
    """
    Extract all content from a PDF.

    Returns a dict with:
      - metadata : file info
      - pages    : list of per-page raw content
    """
    log.info(f"[EXTRACT] Opening: {filepath}")

    result = {
        "metadata": {},
        "pages": []
    }

    with pdfplumber.open(filepath) as pdf:
        # Metadata
        result["metadata"] = {
            "filename": filepath.split("/")[-1],
            "total_pages": len(pdf.pages),
            "pdf_info": pdf.metadata or {}
        }
        log.info(f"[EXTRACT] Total pages: {len(pdf.pages)}")

        for i, page in enumerate(pdf.pages):
            page_num = i + 1
            log.info(f"[EXTRACT] Processing page {page_num}/{len(pdf.pages)}")

            # Extract plain text
            raw_text = page.extract_text() or ""

            # Extract tables (each table is a list of rows; each row is a list of cells)
            raw_tables = page.extract_tables() or []

            # Extract images (bounding boxes only — no model decoding)
            images = [
                {
                    "x0": round(img["x0"], 2),
                    "y0": round(img["y0"], 2),
                    "x1": round(img["x1"], 2),
                    "y1": round(img["y1"], 2),
                    "width": round(img["width"], 2),
                    "height": round(img["height"], 2),
                }
                for img in (page.images or [])
            ]

            result["pages"].append({
                "page_number": page_num,
                "raw_text": raw_text,
                "raw_tables": raw_tables,
                "images": images,
            })

    total_tables = sum(len(p["raw_tables"]) for p in result["pages"])
    total_images = sum(len(p["images"]) for p in result["pages"])
    log.info(f"[EXTRACT] Done — tables: {total_tables}, images: {total_images}")

    return result
