"""
Step 4 — Structure

Converts raw extracted content into a clean, structured JSON format.
Uses simple heuristics to identify headings, paragraphs, and tables.
No ML — pure rule-based structuring.
"""

import re
import logging
from datetime import datetime

log = logging.getLogger("rpa.structurer")


def _classify_line(line: str) -> str:
    """
    Heuristic to classify a line of text.

    Rules:
      - Short line (< 80 chars) + ALL CAPS                 → heading
      - Short line (< 80 chars) + ends with ':'            → heading
      - Short line (< 60 chars) + Title Case words          → heading
      - Everything else                                     → paragraph
    """
    line = line.strip()
    if not line:
        return "empty"

    if len(line) < 80 and line.isupper():
        return "heading"

    if len(line) < 80 and line.endswith(":"):
        return "heading"

    words = line.split()
    if len(words) <= 8 and sum(1 for w in words if w and w[0].isupper()) >= len(words) * 0.7:
        return "heading"

    return "paragraph"


def _structure_text(raw_text: str) -> list[dict]:
    """
    Split raw text into structured blocks of headings and paragraphs.
    Merges consecutive paragraph lines into a single paragraph block.
    """
    blocks = []
    current_paragraph_lines = []

    def flush_paragraph():
        if current_paragraph_lines:
            text = " ".join(current_paragraph_lines).strip()
            if text:
                blocks.append({"type": "paragraph", "text": text})
            current_paragraph_lines.clear()

    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            flush_paragraph()
            continue

        kind = _classify_line(line)

        if kind == "heading":
            flush_paragraph()
            blocks.append({"type": "heading", "text": line})
        else:
            current_paragraph_lines.append(line)

    flush_paragraph()
    return blocks


def _structure_table(raw_table: list) -> dict:
    """
    Convert a raw pdfplumber table (list of rows) into a clean dict.
    First row is treated as headers if it contains non-None values.
    """
    if not raw_table or not raw_table[0]:
        return {"type": "table", "headers": [], "rows": []}

    # Clean cells
    def clean(cell):
        if cell is None:
            return ""
        return str(cell).strip()

    cleaned = [[clean(cell) for cell in row] for row in raw_table]

    # Use first row as header
    headers = cleaned[0]
    rows = cleaned[1:]

    return {
        "type": "table",
        "headers": headers,
        "rows": rows,
        "row_count": len(rows),
        "col_count": len(headers),
    }


def structure(extracted: dict) -> dict:
    """
    Main structuring function.

    Takes raw extraction output and returns:
    {
      "metadata": {...},
      "processed_at": "...",
      "summary_stats": {...},
      "content": [
        {
          "page_number": 1,
          "blocks": [
            {"type": "heading", "text": "..."},
            {"type": "paragraph", "text": "..."},
            {"type": "table", "headers": [...], "rows": [...]},
            {"type": "image", "x0": ..., ...}
          ]
        },
        ...
      ]
    }
    """
    log.info("[STRUCTURE] Structuring extracted content...")

    structured_pages = []
    total_headings = 0
    total_paragraphs = 0
    total_tables = 0
    total_images = 0

    for page in extracted["pages"]:
        blocks = []

        # Structure text blocks
        text_blocks = _structure_text(page["raw_text"])
        blocks.extend(text_blocks)
        total_headings += sum(1 for b in text_blocks if b["type"] == "heading")
        total_paragraphs += sum(1 for b in text_blocks if b["type"] == "paragraph")

        # Structure tables
        for raw_table in page["raw_tables"]:
            table_block = _structure_table(raw_table)
            blocks.append(table_block)
            total_tables += 1

        # Add image location markers
        for img in page["images"]:
            blocks.append({"type": "image", **img})
            total_images += 1

        structured_pages.append({
            "page_number": page["page_number"],
            "blocks": blocks
        })

    result = {
        "metadata": extracted["metadata"],
        "processed_at": datetime.now().isoformat(),
        "summary_stats": {
            "total_pages": extracted["metadata"]["total_pages"],
            "total_headings": total_headings,
            "total_paragraphs": total_paragraphs,
            "total_tables": total_tables,
            "total_images": total_images,
        },
        "content": structured_pages
    }

    log.info(
        f"[STRUCTURE] Done — "
        f"headings: {total_headings}, "
        f"paragraphs: {total_paragraphs}, "
        f"tables: {total_tables}, "
        f"images: {total_images}"
    )
    return result
