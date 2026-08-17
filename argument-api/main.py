import threading
import uuid
from typing import List

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from job_store import get_job, init_job
from pipeline import AVAILABLE_MODELS, run_pipeline

app = FastAPI(title="Argument Miner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],#change with the real link (online version)
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/documents")
async def upload_document(file: UploadFile = File(...), models: List[str] = Form(...)):
    if not file.filename.lower().endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are accepted for now.")

    invalid = [m for m in models if m not in AVAILABLE_MODELS]
    if not models or invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid models: {invalid}. Available: {list(AVAILABLE_MODELS)}"
            if invalid else "Select at least one model.",
        )

    raw = await file.read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")

    if not text.strip():
        raise HTTPException(status_code=400, detail="The document is empty.")

    job_id = str(uuid.uuid4())
    init_job(job_id)
    #Thread for the LLMs
    thread = threading.Thread(target=run_pipeline, args=(job_id, text, models), daemon=True)
    thread.start()

    return {"job_id": job_id}


@app.get("/api/documents/{job_id}/status")
async def status(job_id: str):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job_id not found.")

    payload = {"status": job["status"]}
    if job.get("error"):
        payload["error"] = job["error"]
    return payload


@app.get("/api/documents/{job_id}/results")
async def results(job_id: str):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job_id not found.")
    if job["status"] == "error":
        raise HTTPException(status_code=500, detail=job.get("error", "Processing failed."))
    if job["status"] != "done":
        raise HTTPException(status_code=409, detail="The processing is not yet complete.")

    job_results = job.get("results")
    if job_results is None:
        raise HTTPException(status_code=500, detail="The job finished, but the result was not found in memory.")

    return job_results