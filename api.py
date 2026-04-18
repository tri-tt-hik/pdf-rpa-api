"""
api.py — Product-grade backend API

Wraps the existing RPA pipeline as HTTP endpoints.
Any RPA tool, frontend, or service can call this.

Run with:
    uvicorn api:app --host 0.0.0.0 --port 8000

Endpoints:
    POST /process       — Upload a PDF, get structured JSON back
    GET  /status/{job}  — Check processing status
    GET  /result/{job}  — Fetch stored result
    GET  /health        — Health check
"""

import os
import uuid
import json
import logging
import shutil
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from rpa.extractor  import extract
from rpa.structurer import structure
from rpa.storage    import store
from rpa.logger     import setup_logger

setup_logger()
log = logging.getLogger("api")

app = FastAPI(
    title="PDF Processing API",
    description="RPA-ready PDF extraction and structuring API",
    version="1.0.0"
)

# Allow Power Automate, browsers, and any RPA tool to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job tracker (replace with Redis in production)
jobs: dict = {}

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs("output_json", exist_ok=True)


# ── Background task ──────────────────────────────────────────

def process_pdf_task(job_id: str, filepath: str):
    """Runs the full pipeline in the background."""
    jobs[job_id]["status"] = "processing"
    log.info(f"[JOB {job_id}] Starting pipeline...")

    try:
        extracted   = extract(filepath)
        structured  = structure(extracted)
        output_path = store(structured)

        jobs[job_id]["status"]      = "done"
        jobs[job_id]["output_path"] = output_path
        jobs[job_id]["stats"]       = structured["summary_stats"]
        jobs[job_id]["completed_at"] = datetime.now().isoformat()

        log.info(f"[JOB {job_id}] ✅ Done → {output_path}")

    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"]  = str(e)
        log.error(f"[JOB {job_id}] ❌ Failed: {e}")

    finally:
        # Clean up uploaded temp file
        if os.path.exists(filepath):
            os.remove(filepath)


# ── Endpoints ────────────────────────────────────────────────

@app.get("/health")
def health():
    """Health check — RPA tools use this to verify the service is up."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.post("/process")
async def process_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload a PDF and start processing.
    Returns a job_id immediately — processing runs in the background.
    Poll /status/{job_id} to check progress.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    # Save uploaded file temporarily
    job_id   = str(uuid.uuid4())
    filepath = os.path.join(UPLOAD_DIR, f"{job_id}.pdf")

    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
    if file_size_mb > 50:
        os.remove(filepath)
        raise HTTPException(status_code=413, detail=f"File too large ({file_size_mb:.1f} MB). Max 50 MB.")

    # Register job
    jobs[job_id] = {
        "job_id":     job_id,
        "filename":   file.filename,
        "status":     "queued",
        "created_at": datetime.now().isoformat(),
    }

    # Run pipeline in background
    background_tasks.add_task(process_pdf_task, job_id, filepath)

    log.info(f"[JOB {job_id}] Queued: {file.filename}")
    return {"job_id": job_id, "status": "queued", "message": "Poll /status/{job_id} for updates."}


@app.get("/status/{job_id}")
def get_status(job_id: str):
    """
    Check job status.
    Returns: queued | processing | done | failed
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found.")
    return jobs[job_id]


@app.get("/result/{job_id}")
def get_result(job_id: str):
    """
    Fetch the full structured JSON result for a completed job.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found.")

    job = jobs[job_id]
    if job["status"] != "done":
        raise HTTPException(status_code=400, detail=f"Job status is '{job['status']}', not 'done'.")

    output_path = job.get("output_path")
    if not output_path or not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Output file not found.")

    with open(output_path, "r", encoding="utf-8") as f:
        result = json.load(f)

    return JSONResponse(content=result)
