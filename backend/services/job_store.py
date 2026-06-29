jobs: dict = {}


def init_job(job_id: str) -> None:
    jobs[job_id] = {
        "status": "pending",
        "progress": 0,
        "total": 0,
        "leads": [],
        "log": "Iniciando...",
    }


def get_job(job_id: str) -> dict | None:
    return jobs.get(job_id)
