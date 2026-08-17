import threading

JOBS: dict = {}
JOBS_LOCK = threading.Lock()


def init_job(job_id: str) -> None:
    with JOBS_LOCK:
        JOBS[job_id] = {"status": "queued", "error": None}


def set_status(job_id: str, status: str, error: str | None = None) -> None:
    with JOBS_LOCK:
        if job_id not in JOBS:
            JOBS[job_id] = {}
        JOBS[job_id]["status"] = status
        if error:
            JOBS[job_id]["error"] = error


def set_results(job_id: str, results: dict) -> None:
    with JOBS_LOCK:
        if job_id not in JOBS:
            JOBS[job_id] = {}
        JOBS[job_id]["results"] = results


def get_job(job_id: str) -> dict | None:
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        return dict(job) if job is not None else None