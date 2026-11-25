import json
from threading import Event
from time import monotonic, sleep

import pytest
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.services import localidades_service, scrape_service


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "prospeccao.db"))
    with TestClient(create_app(), base_url="http://127.0.0.1") as aplicacao:
        yield aplicacao


def test_catalogo_busca_por_uf_e_preserva_cache_quando_atualizacao_falha(cliente, monkeypatch):
    dados = cliente.get("/api/v1/localidades/municipios", params={"uf": "es", "busca": "Sao Mateus"}).json()
    assert dados["itens"] == [{"codigo": 3204906, "nome": "São Mateus", "uf": "ES"}]
    assert dados["versao"].startswith("ibge-")
    assert cliente.get("/api/v1/localidades/municipios", params={"uf": "ZZ"}).status_code == 422

    registros = [
        {"municipio-id": municipio.codigo, "municipio-nome": municipio.nome, "UF-sigla": municipio.uf}
        for municipio in localidades_service.carregarCatalogoEmbutido().municipios
    ]

    class RespostaIbge:
        def __enter__(self):
            return self

        def __exit__(self, *argumentos):
            pass

        def read(self, limite):
            return json.dumps(registros).encode("utf-8")[:limite]

    monkeypatch.setattr(localidades_service, "urlopen", lambda *argumentos, **opcoes: RespostaIbge())
    assert cliente.post("/api/v1/localidades/atualizar").status_code == 200
    cache = localidades_service.caminhoCache()
    anterior = cache.read_bytes()
    registros.pop()
    registros.append(registros[0])
    resposta = cliente.post("/api/v1/localidades/atualizar")
    assert resposta.status_code == 503
    assert resposta.json()["code"] == "CATALOGO_INDISPONIVEL"
    assert cache.read_bytes() == anterior


@pytest.mark.parametrize("alteracao", [
    {"estado": "SP"}, {"municipioCodigo": "3204906"}, {"municipioCodigo": 3200000},
    {"max_results": 0}, {"max_results": 501}, {"max_results": 1.5},
])
def test_prospeccao_recusa_selecao_invalida_antes_da_coleta(cliente, alteracao):
    campos = {"segmento": "Clínicas", "estado": "ES", "municipioCodigo": 3204906, "max_results": 25}
    resposta = cliente.post("/api/v1/prospeccoes", json={**campos, **alteracao})
    assert resposta.status_code == 422
    assert resposta.json()["fieldErrors"]
    assert cliente.get("/history").json() == []


def test_coleta_parcial_preserva_origem_conversao_e_poll_leve(cliente, monkeypatch):
    entrouNaSegunda = Event()
    prosseguir = Event()
    parametrosRecebidos = []

    class Navegador:
        def launch(self):
            pass

        def close(self):
            pass

    class Scraper:
        def __init__(self, navegador, jobId):
            pass

        def collect_place_urls(self, segmento, cidade, estado, quantidade):
            parametrosRecebidos.append((segmento, cidade, estado, quantidade))
            return ["https://example.invalid/primeira", "https://example.invalid/segunda"]

        def extract_lead(self, url, segmento, cidade, estado, prospectador):
            if url.endswith("segunda"):
                entrouNaSegunda.set()
                prosseguir.wait(5)
                raise RuntimeError("Falha controlada da segunda extração")
            return {
                "nome": "Clínica de Teste", "url_maps": url,
                "telefone": "27999001234", "score": 20,
            }

    monkeypatch.setattr(scrape_service, "create_browser", Navegador)
    monkeypatch.setattr(scrape_service, "GoogleMapsScraper", Scraper)
    resposta = cliente.post("/api/v1/prospeccoes", json={
        "segmento": "Clínicas", "estado": "es", "municipioCodigo": 3204906, "max_results": 2,
    })
    assert resposta.status_code == 200
    caminho = f"/status/{resposta.json()['job_id']}"
    try:
        assert entrouNaSegunda.wait(5)
        progresso = cliente.get(caminho, params={"somenteProgresso": True}).json()
        assert progresso["status"] == "running"
        assert progresso["leads"] == []
        assert progresso["processados"] == progresso["coletados"] == 1
        assert cliente.get(caminho).json()["leads_count"] == 1
        assert len(cliente.get(caminho).json()["leads"]) == 1
    finally:
        prosseguir.set()

    limite = monotonic() + 5
    while monotonic() < limite:
        final = cliente.get(caminho, params={"somenteProgresso": True}).json()
        if final["status"] in {"done", "error"}:
            break
        sleep(0.02)
    assert final["status"] == "done" and final["concluidoComAvisos"] is True
    assert final["processados"] == 2 and final["coletados"] == final["falhas"] == 1
    assert final["falhasExtracao"] == 1 and final["falhasPersistencia"] == 0
    assert final["municipioCodigo"] == 3204906
    assert parametrosRecebidos == [("Clínicas", "São Mateus", "ES", 2)]
    lead = final["leads"][0]
    assert lead["runId"] == lead["history_id"] == final["runId"]
    historico = cliente.get(f"/history/{lead['history_id']}").json()
    assert historico["status"] == "done_with_warnings"
    assert historico["leads"][0]["source"] == "google_maps"
    assert historico["leads"][0]["runId"] == lead["runId"]
    converter = f"/api/v1/crm/historico/{lead['history_id']}/leads/{lead['id']}/converter"
    primeiro = cliente.post(converter, json={})
    segundo = cliente.post(converter, json={})
    assert primeiro.status_code == segundo.status_code == 200
    assert primeiro.json()["empresaId"] == segundo.json()["empresaId"]
    assert segundo.json()["jaVinculado"] is True
