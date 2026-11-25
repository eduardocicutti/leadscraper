from collections.abc import Callable
from datetime import datetime
from threading import Thread
from time import monotonic


jobs: dict[str, dict] = {}


def init_job(
    job_id: str,
    *,
    municipioCodigo: int | None = None,
    quantidadeSolicitada: int | None = None,
) -> None:
    jobs[job_id] = {
        "status": "pending",
        "progress": 0,
        "total": 0,
        "leads": [],
        "log": "Iniciando...",
        "iniciadoEm": monotonic(),
        "municipioCodigo": municipioCodigo,
        "quantidadeSolicitada": quantidadeSolicitada,
    }


def iniciarJob(
    tarefa: Callable[..., None],
    *argumentos: object,
    municipioCodigo: int | None = None,
    quantidadeSolicitada: int | None = None,
) -> str:
    jobId = datetime.now().strftime("%Y%m%d%H%M%S%f")
    init_job(
        jobId, municipioCodigo=municipioCodigo, quantidadeSolicitada=quantidadeSolicitada
    )
    Thread(target=tarefa, args=(jobId, *argumentos), daemon=True).start()
    return jobId


def get_job(job_id: str) -> dict | None:
    return jobs.get(job_id)


def respostaJob(job: dict, somenteProgresso: bool) -> dict:
    estado = job.copy()
    status = estado["status"]
    processados = estado.get("progress", 0)
    resultados = estado.get("leads", [])
    resposta = {
        "status": status,
        "progress": processados,
        "total": estado.get("total", 0),
        "log": estado.get("log", ""),
        "leads_count": len(resultados),
        "leads": [] if somenteProgresso and status in {"pending", "running"} else resultados,
    }
    if estado.get("quantidadeSolicitada") is not None:
        falhasExtracao = estado.get("falhasExtracao", 0)
        falhasPersistencia = estado.get("falhasPersistencia", 0)
        fim = estado.get("terminouEm", monotonic())
        resposta.update(
            processados=processados,
            coletados=estado.get("coletados", 0),
            extraidos=len(resultados),
            falhas=falhasExtracao + falhasPersistencia,
            falhasExtracao=falhasExtracao,
            falhasPersistencia=falhasPersistencia,
            duracaoMs=max(0, int((fim - estado["iniciadoEm"]) * 1000)),
            municipioCodigo=estado.get("municipioCodigo"),
            quantidadeSolicitada=estado["quantidadeSolicitada"],
            runId=estado.get("runId"),
            source="google_maps",
            concluidoComAvisos=estado.get("concluidoComAvisos", False),
        )
    return resposta
