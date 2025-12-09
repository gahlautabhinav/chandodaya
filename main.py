# main.py

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.api import analyze_text_to_dict
from src.ocr_bridge import analyze_file_to_dicts

app = FastAPI(title="Vedic & Classical Sanskrit Chandas API")

# CORS for Flutter frontend (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in production, restrict to your domain(s)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"status": "ok", "message": "Vedic Chandas API running"}


# ---------------- TEXT ENDPOINT ----------------

@app.post("/api/analyze/text")
async def analyze_text_endpoint(payload: Dict[str, Any]):
    """
    Analyze a single mantra/shloka given as Devanagari text.

    Request JSON:
    {
        "text": "अ॒ग्निमी॑ळे पु॒रोहि॑तं ..."
    }

    Response JSON:
    {
        "analysis": { ... see api.analyze_text_to_dict ... }
    }
    """
    text = payload.get("text")
    if not text or not isinstance(text, str) or not text.strip():
        raise HTTPException(status_code=400, detail="Missing or empty 'text' field")

    analysis = analyze_text_to_dict(text)
    return {"analysis": analysis}


# ---------------- FILE ENDPOINT ----------------

@app.post("/api/analyze/file")
async def analyze_file_endpoint(
    file: UploadFile = File(...),
    use_gemini: bool = Form(True),
):
    """
    Analyze one uploaded file (image/pdf/docx).

    Multipart form-data:
        file        : uploaded file
        use_gemini  : bool (default True)

    The OCR pipeline writes files to a temporary folder, then
    chandas analysis is run on each *_only_shloka.txt extracted.
    """
    # Save file to a temp location
    tmp_root = Path("/tmp")  # works on Render & local
    tmp_root.mkdir(parents=True, exist_ok=True)

    tmp_in = tmp_root / f"upload_{file.filename}"
    with tmp_in.open("wb") as f_out:
        shutil.copyfileobj(file.file, f_out)

    # Output directory for OCR text files
    out_dir = tmp_root / f"ocr_{tmp_in.stem}"
    try:
        results = analyze_file_to_dicts(
            input_path=str(tmp_in),
            out_dir=str(out_dir),
            use_gemini=use_gemini,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during OCR + analysis: {e}")

    return {
        "file": file.filename,
        "results": results,
    }
