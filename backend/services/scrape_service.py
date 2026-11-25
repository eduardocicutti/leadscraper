from time import monotonic

from backend.adapters.browser_factory import create_browser
from backend.core.logging import logger
from backend.repositories.database import (
    save_lead_incremental,
    save_search_history,
    update_search_history_status,
)
from backend.scrapers.google_maps import GoogleMapsScraper
from backend.services import job_store


def iniciarColeta(
    segmento: str,
    cidade: str,
    estado: str,
    quantidade: int,
    prospectador: str,
    *,
    municipioCodigo: int | None = None,
) -> str:
    return job_store.iniciarJob(
        scrape_worker, segmento, cidade, estado, quantidade, prospectador,
        municipioCodigo=municipioCodigo, quantidadeSolicitada=quantidade,
    )


def scrape_worker(
    job_id: str,
    segmento: str,
    cidade: str,
    estado: str,
    max_results: int,
    prospectador: str,
) -> None:
    logger.info("Iniciando coleta job=%s", job_id)
    job = job_store.jobs[job_id]
    navegador = None
    historicoId = None
    resultados: list[dict] = []
    coletados = 0
    falhasExtracao = 0
    falhasPersistencia = 0
    mensagemFalha = ""
    job.update(status="running", log="Iniciando navegador...")

    try:
        historicoId = save_search_history(job_id, segmento, cidade, estado, prospectador)
        job["runId"] = historicoId
        navegador = create_browser()
        navegador.launch()
        scraper = GoogleMapsScraper(navegador, job_id)
        job["log"] = "Carregando estabelecimentos..."
        urls = list(dict.fromkeys(
            scraper.collect_place_urls(segmento, cidade, estado, max_results)
        ))[:max_results]
        job["total"] = len(urls)

        for indice, url in enumerate(urls, start=1):
            try:
                lead = scraper.extract_lead(url, segmento, cidade, estado, prospectador)
            except Exception:
                falhasExtracao += 1
                logger.exception("Falha ao extrair estabelecimento %s de %s", indice, job_id)
            else:
                lead["source"] = "google_maps"
                lead["runId"] = historicoId
                try:
                    leadId = save_lead_incremental(historicoId, lead)
                    if leadId is None:
                        falhasPersistencia += 1
                    else:
                        lead["id"] = leadId
                        lead["history_id"] = historicoId
                        coletados += 1
                except Exception:
                    falhasPersistencia += 1
                    logger.exception("Falha ao gravar estabelecimento %s de %s", indice, job_id)
                resultados.append(lead)
            job.update(
                progress=indice,
                coletados=coletados,
                falhasExtracao=falhasExtracao,
                falhasPersistencia=falhasPersistencia,
                leads=sorted(resultados, key=lambda item: item["score"], reverse=True),
                log=f"Processando estabelecimentos: {indice} de {len(urls)}.",
            )
    except Exception:
        logger.exception("Falha na coleta job=%s", job_id)
        mensagemFalha = "A coleta foi interrompida."
    finally:
        if navegador is not None:
            try:
                navegador.close()
            except Exception:
                logger.warning("Falha ao encerrar navegador job=%s", job_id, exc_info=True)

    concluiuComAvisos = bool(resultados and (mensagemFalha or falhasExtracao or falhasPersistencia))
    situacaoHistorico = "done" if coletados else "error"
    if coletados and concluiuComAvisos:
        situacaoHistorico = "done_with_warnings"
    if historicoId is not None:
        try:
            update_search_history_status(historicoId, situacaoHistorico, coletados)
        except Exception:
            logger.exception("Falha ao finalizar o histórico da coleta job=%s", job_id)
            concluiuComAvisos = bool(resultados)
            mensagemFalha = "Não foi possível atualizar a situação no histórico."

    if resultados:
        mensagem = (
            f"Coleta concluída com avisos. {coletados} de {len(resultados)} resultados salvos."
            if concluiuComAvisos
            else f"Coleta concluída. {coletados} resultados salvos."
        )
    elif mensagemFalha:
        mensagem = mensagemFalha
    elif job["total"]:
        mensagem = "Não foi possível extrair nenhum dos estabelecimentos encontrados."
    else:
        mensagem = "Nenhum estabelecimento encontrado para a localização e o segmento."
    job.update(
        status="done" if resultados else "error",
        terminouEm=monotonic(),
        coletados=coletados,
        falhasExtracao=falhasExtracao,
        falhasPersistencia=falhasPersistencia,
        concluidoComAvisos=concluiuComAvisos,
        log=mensagem,
    )
