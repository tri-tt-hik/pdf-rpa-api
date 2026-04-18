# ── Base image ───────────────────────────────────────────────
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# ── System dependencies ───────────────────────────────────────
# pdfplumber needs these for PDF rendering
RUN apt-get update && apt-get install -y \
    libpoppler-cpp-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ───────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── App source ────────────────────────────────────────────────
COPY rpa/ ./rpa/
COPY api.py .

# ── Create runtime folders ────────────────────────────────────
RUN mkdir -p uploads output_json logs

# ── Expose port ───────────────────────────────────────────────
EXPOSE 8000

# ── Start command ─────────────────────────────────────────────
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
