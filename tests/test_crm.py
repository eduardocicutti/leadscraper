import base64
import sqlite3
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.domain.crm import normalizarTelefone, validarCnpj
from backend.repositories import database
from backend.repositories.migracoes import aplicarMigracoes
from backend.services import job_store, scrape_service


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "crm.db"))
    with TestClient(create_app(), base_url="http://127.0.0.1") as clienteLocal:
        yield clienteLocal


def cadastrar(cliente, **campos):
    resposta = cliente.post(
        "/api/v1/crm/empresas",
        json={
            "nome": "Clínica São Mateus",
            "cidade": "São Mateus",
            "uf": "ES",
            "responsavel": "Eduardo",
            **campos,
        },
        headers={"X-Operador-Local": "Eduardo"},
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def test_empresa_busca_contato_persistencia(cliente):
    empresa = cadastrar(cliente, telefone="(27) 99817-4086")
    for busca in (
        "clinica sao",
        "SÃO MATEUS",
        "27998174086",
        "+55 (27) 99817-4086",
        "99817",
    ):
        resposta = cliente.get("/api/v1/crm/empresas", params={"busca": busca}).json()
        assert resposta["total"] == 1
        assert resposta["itens"][0]["id"] == empresa["id"]
    detalhe = cliente.get(f"/api/v1/crm/empresas/{empresa['id']}").json()
    assert detalhe["contatos"][0]["telefoneNormalizado"] == "5527998174086"
    assert detalhe["atividades"] == []
    assert detalhe["eventos"][0]["autorNome"] == "Eduardo"


def test_duplicidade_versao_e_arquivo_preservam_historico(cliente):
    empresa = cadastrar(cliente)
    duplicada = cliente.post(
        "/api/v1/crm/empresas",
        json={
            "nome": "Clinica Sao Mateus",
            "cidade": "Sao Mateus",
            "uf": "ES",
            "responsavel": "Outro",
        },
    )
    assert duplicada.status_code == 409
    assert duplicada.json()["candidatas"][0]["id"] == empresa["id"]
    edicao = {
        campo: empresa[campo]
        for campo in (
            "nome",
            "segmento",
            "cidade",
            "uf",
            "site",
            "urlMaps",
            "responsavel",
            "version",
        )
    }
    edicao["arquivada"] = True
    caminho = f"/api/v1/crm/empresas/{empresa['id']}"
    assert cliente.put(caminho, json=edicao).status_code == 200
    assert cliente.put(caminho, json=edicao).status_code == 409
    assert cliente.get("/api/v1/crm/empresas").json()["total"] == 0
    assert cliente.get("/api/v1/crm/empresas?arquivadas=true").json()["total"] == 1
    assert len(cliente.get(caminho).json()["eventos"]) == 2


def test_lembrete_reagendamento_conclusao_e_autoria(cliente):
    empresa = cadastrar(cliente)
    caminho = f"/api/v1/crm/empresas/{empresa['id']}/atividades"
    entrada = {
        "titulo": "Retorno pós-venda",
        "tipo": "lembrete",
        "responsavel": "Ana",
        "prazoData": "2026-11-01",
    }
    resposta = cliente.post(
        caminho, json=entrada, headers={"X-Operador-Local": "Eduardo"}
    )
    assert resposta.status_code == 201
    atividade = resposta.json()
    edicao = {**entrada, "prazoData": "2026-11-10", "version": 1}
    retorno = cliente.put(f"{caminho}/{atividade['id']}", json=edicao)
    assert retorno.status_code == 200
    assert retorno.json()["situacao"] == "pendente"
    assert retorno.json()["concluidaEm"] is None
    assert retorno.json()["autorNome"] == "Eduardo"
    assert cliente.put(f"{caminho}/{atividade['id']}", json=edicao).status_code == 409
    assert (
        cliente.put(
            f"{caminho}/{atividade['id']}",
            json={**edicao, "version": 2, "situacao": "concluida"},
        ).status_code
        == 422
    )
    assert (
        cliente.put(
            f"{caminho}/{atividade['id']}",
            json={
                **edicao,
                "version": 2,
                "situacao": "concluida",
                "resultado": "Cliente confirmou o retorno",
            },
        ).status_code
        == 200
    )
    eventos = cliente.get(f"/api/v1/crm/empresas/{empresa['id']}").json()["eventos"]
    assert any("2026-11-01 → 2026-11-10" in evento["descricao"] for evento in eventos)
    assert cliente.get("/api/v1/crm/atividades").json()["total"] == 1


@pytest.mark.parametrize(
    "campos",
    [
        {"cnpj": "11.111.111/1111-11"},
        {"telefone": "12345"},
        {"uf": "XX"},
        {"organizationId": "outro"},
        {"site": "javascript:alert(1)"},
        {"confirmarTelefoneCompartilhado": "true"},
    ],
)
def test_validacao_estruturada(cliente, campos):
    resposta = cliente.post(
        "/api/v1/crm/empresas",
        json={"nome": "Empresa", "responsavel": "Eduardo", **campos},
    )
    assert resposta.status_code == 422
    assert resposta.json()["fieldErrors"]
    assert resposta.json()["correlationId"]
    assert cliente.get("/api/v1/crm/empresas").json()["total"] == 0


def test_crm_rejeita_data_numerica_e_inteiros_fora_dos_limites(cliente):
    empresa = cadastrar(cliente)
    resposta = cliente.post(
        f"/api/v1/crm/empresas/{empresa['id']}/atividades",
        json={"titulo": "Retorno", "responsavel": "Ana", "prazoData": 0},
    )
    assert resposta.status_code == 422
    assert resposta.json()["fieldErrors"][0]["field"] == "prazoData"
    assert cliente.get(
        "/api/v1/crm/atividades", params={"dataReferencia": "0"}
    ).status_code == 422
    assert cliente.get(
        "/api/v1/crm/empresas", params={"pagina": 2**63}
    ).status_code == 422
    assert cliente.post(
        f"/api/v1/crm/selecionados/{2**63}/converter", json={}
    ).status_code == 422
    assert cliente.put(
        f"/api/v1/crm/empresas/{empresa['id']}",
        json={"nome": empresa["nome"], "responsavel": "Ana", "version": 2**63},
    ).status_code == 422


def test_conversao_idempotente_e_vinculacao_explicita(cliente):
    conteudo = "Nome da empresa;Telefone/WhatsApp;Cidade;UF;Ramo de atividade\nClínica Teste;(27) 99817-4086;São Mateus;ES;Clínica\n"
    resposta = cliente.post(
        "/selected-leads/import-spreadsheet",
        json={
            "filename": "teste.csv",
            "content_base64": base64.b64encode(conteudo.encode()).decode(),
            "prospectador": "Eduardo",
        },
    )
    assert resposta.status_code == 200
    selecionado = cliente.get("/selected-leads").json()[0]
    caminho = f"/api/v1/crm/selecionados/{selecionado['id']}/converter"
    existente = cadastrar(cliente, telefone="27998174086")
    assert cliente.post(caminho, json={}).status_code == 409
    assert cliente.get("/api/v1/crm/empresas").json()["total"] == 1
    primeira = cliente.post(caminho, json={"empresaId": existente["id"]}).json()
    segunda = cliente.post(caminho, json={}).json()
    assert primeira["empresaId"] == segunda["empresaId"] == existente["id"]
    assert segunda["jaVinculado"] is True
    assert (
        cliente.get(f"/api/v1/crm/empresas/{existente['id']}").json()["atividades"]
        == []
    )


def test_conversao_nova_empresa(cliente):
    conteudo = "Nome da empresa;Telefone/WhatsApp;Cidade;UF;Ramo de atividade\nEmpresa Nova;(27) 99817-4086;São Mateus;ES;Clínica\n"
    cliente.post(
        "/selected-leads/import-spreadsheet",
        json={
            "filename": "teste.csv",
            "content_base64": base64.b64encode(conteudo.encode()).decode(),
            "prospectador": "Eduardo",
        },
    )
    selecionado = cliente.get("/selected-leads").json()[0]
    resposta = cliente.post(
        f"/api/v1/crm/selecionados/{selecionado['id']}/converter", json={}
    )
    assert resposta.status_code == 200, resposta.text
    detalhe = cliente.get(f"/api/v1/crm/empresas/{resposta.json()['empresaId']}").json()
    assert detalhe["nome"] == "Empresa Nova"
    assert len(detalhe["contatos"]) == 1


def test_nova_selecao_nao_reutiliza_id_com_origem_no_crm(cliente):
    [primeira] = database.add_selected_leads(
        [{"nome": "Loja anterior", "cidade": "São Mateus", "estado": "ES"}]
    )
    caminho = f"/api/v1/crm/selecionados/{primeira['id']}/converter"
    resposta = cliente.post(caminho, json={})
    assert resposta.status_code == 200, resposta.text
    empresaAnteriorId = resposta.json()["empresaId"]
    assert cliente.delete(f"/selected-leads/{primeira['id']}").status_code == 200
    assert cliente.post(caminho, json={}).status_code == 404

    importacao = database.import_selected_leads([{"nome": "Loja nova"}])
    [segunda] = importacao["imported"]
    assert segunda["id"] != primeira["id"]
    nova = cliente.post(f"/api/v1/crm/selecionados/{segunda['id']}/converter", json={})
    assert nova.status_code == 200, nova.text
    assert nova.json()["empresaId"] != empresaAnteriorId
    detalhe = cliente.get(f"/api/v1/crm/empresas/{empresaAnteriorId}").json()
    assert any(evento["tipo"] == "origem" for evento in detalhe["eventos"])


def test_conversao_historico_preserva_origem_e_e_idempotente(cliente):
    historicoId = database.save_search_history(
        "teste", "Clínica", "São Mateus", "ES", "Eduardo"
    )
    leadId = database.save_lead_incremental(
        historicoId,
        {
            "nome": "Clínica do Histórico",
            "telefone": "(27) 99817-4086",
            "url_maps": "https://example.com/locais/clinica",
        },
    )
    caminho = f"/api/v1/crm/historico/{historicoId}/leads/{leadId}/converter"
    assert cliente.post(
        f"/api/v1/crm/historico/{historicoId + 1}/leads/{leadId}/converter", json={}
    ).status_code == 404
    primeira = cliente.post(caminho, json={})
    assert primeira.status_code == 200, primeira.text
    empresaId = primeira.json()["empresaId"]
    assert primeira.json()["jaVinculado"] is False
    assert cliente.post(caminho, json={}).json() == {
        "empresaId": empresaId,
        "jaVinculado": True,
    }

    historico = cliente.get(f"/history/{historicoId}").json()
    assert historico["leads"][0]["id"] == leadId
    detalhe = cliente.get(f"/api/v1/crm/empresas/{empresaId}").json()
    assert detalhe["qualificacao"]["situacao"] == "novo"
    assert detalhe["contatos"][0]["telefone"] == "(27) 99817-4086"
    assert detalhe["atividades"] == []
    assert sum(evento["tipo"] == "origem" for evento in detalhe["eventos"]) == 1

    assert cliente.delete(f"/history/{historicoId}").status_code == 200
    historicoNovoId = database.save_search_history(
        "teste-2", "Loja", "São Mateus", "ES", "Eduardo"
    )
    leadNovoId = database.save_lead_incremental(
        historicoNovoId, {"nome": "Loja cadastrada depois"}
    )
    assert (historicoNovoId, leadNovoId) == (historicoId, leadId)
    nova = cliente.post(caminho, json={})
    assert nova.status_code == 200, nova.text
    assert nova.json()["empresaId"] != empresaId
    assert nova.json()["jaVinculado"] is False
    assert cliente.get(f"/api/v1/crm/empresas/{empresaId}").status_code == 200


def test_telefone_compartilhado_sugere_empresa_sem_mesclar(cliente):
    original = cadastrar(
        cliente, telefone="27998174086"
    )
    empresaComCnpj = cadastrar(
        cliente, nome="Fornecedor distinto", cnpj="04.252.011/0001-10"
    )
    entrada = {
        "nome": "Loja da Esquina",
        "responsavel": "Ana",
        "telefone": "+55 (27) 99817-4086",
    }
    resposta = cliente.post(
        "/api/v1/crm/empresas",
        json=entrada,
    )
    assert resposta.status_code == 409, resposta.text
    [candidata] = resposta.json()["candidatas"]
    assert candidata["id"] == original["id"]
    assert candidata["somenteTelefone"] is True
    entrada["confirmarTelefoneCompartilhado"] = True
    cnpjDuplicado = cliente.post(
        "/api/v1/crm/empresas", json={**entrada, "cnpj": "04.252.011/0001-10"}
    )
    assert cnpjDuplicado.status_code == 409
    assert cnpjDuplicado.json()["candidatas"][0]["id"] == empresaComCnpj["id"]
    assert cnpjDuplicado.json()["candidatas"][0]["somenteTelefone"] is False
    telefoneComCnpjDiferente = cliente.post(
        "/api/v1/crm/empresas", json={
            **entrada,
            "cnpj": "11.222.333/0001-81",
            "confirmarTelefoneCompartilhado": False,
        },
    )
    assert telefoneComCnpjDiferente.status_code == 409
    assert telefoneComCnpjDiferente.json()["candidatas"][0]["somenteTelefone"] is True
    assert cliente.post("/api/v1/crm/empresas", json=entrada).status_code == 201
    assert cliente.get(
        "/api/v1/crm/busca", params={"busca": "(27) 99817-4086"}
    ).json()["total"] == 2


def test_filtros_combinados_distinguem_abordagem_de_tarefa(cliente):
    feita = cadastrar(cliente, nome="Empresa abordada", responsavel="Ana Souza")
    pendente = cadastrar(cliente, nome="Empresa em análise", responsavel="Ana Souza")
    cadastrar(cliente, nome="Empresa de outro responsável", responsavel="Eduardo")

    for empresa, tipo, situacao in (
        (feita, "whatsapp", "concluida"),
        (pendente, "tarefa", "concluida"),
        (pendente, "whatsapp", "pendente"),
    ):
        resposta = cliente.post(
            f"/api/v1/crm/empresas/{empresa['id']}/atividades",
            json={
                "titulo": "Contato de teste",
                "tipo": tipo,
                "situacao": situacao,
                "responsavel": "Ana Souza",
                "resultado": "Confirmado" if situacao == "concluida" else "",
            },
        )
        assert resposta.status_code == 201, resposta.text

    for relacionamento, esperada in (("prospectada", feita), ("semAbordagem", pendente)):
        resposta = cliente.get(
            "/api/v1/crm/empresas",
            params={"relacionamento": relacionamento, "responsavel": "ana", "qualificacao": "novo"},
        )
        assert resposta.status_code == 200, resposta.text
        assert [empresa["id"] for empresa in resposta.json()["itens"]] == [esperada["id"]]

    atividades = cliente.get(
        "/api/v1/crm/atividades",
        params={"tipo": "whatsapp", "situacao": "concluida", "responsavel": "ana"},
    )
    assert atividades.status_code == 200, atividades.text
    assert [atividade["empresaId"] for atividade in atividades.json()["itens"]] == [feita["id"]]
    assert cliente.get("/api/v1/crm/empresas?busca=111234567890").status_code == 200


def test_resultado_da_coleta_traz_ids_dos_locais_persistidos(cliente, monkeypatch):
    urls = ["https://example.com/locais/a", "https://example.com/locais/b"]
    navegador = SimpleNamespace(launch=lambda: None, close=lambda: None)
    raspador = SimpleNamespace(
        collect_place_urls=lambda *_: urls,
        extract_lead=lambda url, *_: {
            "nome": f"Empresa {url[-1].upper()}",
            "url_maps": url,
            "telefone": "(27) 99817-4086",
            "score": 50,
        },
    )
    monkeypatch.setattr(scrape_service, "create_browser", lambda: navegador)
    monkeypatch.setattr(scrape_service, "GoogleMapsScraper", lambda *_: raspador)
    monkeypatch.setattr(job_store, "jobs", {})
    job_store.init_job("teste-coleta")

    scrape_service.scrape_worker("teste-coleta", "Clínica", "São Mateus", "ES", 2, "Ana")

    resultados = cliente.get("/status/teste-coleta").json()
    assert resultados["status"] == "done"
    assert len({lead["id"] for lead in resultados["leads"]}) == 2
    primeira = resultados["leads"][0]
    caminho = (
        f"/api/v1/crm/historico/{primeira['history_id']}/leads/{primeira['id']}/converter"
    )
    assert cliente.post(caminho, json={}).status_code == 200


def test_paginacao_e_contato_nao_expoem_outra_empresa(cliente):
    primeira = cadastrar(cliente)
    segunda = cadastrar(cliente, nome="Academia Norte")
    assert cliente.get("/api/v1/crm/empresas?tamanho=101").status_code == 422
    assert cliente.get("/api/v1/crm/empresas?pagina=0").status_code == 422
    assert (
        cliente.get("/api/v1/crm/empresas?tamanho=1").json()["itens"][0]["id"]
        == segunda["id"]
    )
    assert (
        cliente.post(
            "/api/v1/crm/empresas/inexistente/contatos", json={"nome": "Teste"}
        ).status_code
        == 404
    )
    assert (
        cliente.post(
            f"/api/v1/crm/empresas/{primeira['id']}/contatos",
            json={"nome": "João", "email": "joao@teste.com"},
        ).status_code
        == 201
    )
    assert cliente.get("/api/v1/crm/contatos?busca=joao").json()["total"] == 1


def test_migracao_preserva_legado_e_backup(tmp_path, monkeypatch):
    caminho = tmp_path / "antigo.db"
    with closing(sqlite3.connect(caminho)) as conexao:
        conexao.execute("CREATE TABLE registro_legado (valor TEXT)")
        conexao.execute("INSERT INTO registro_legado VALUES ('preservado')")
        conexao.commit()
    monkeypatch.setenv("DB_PATH", str(caminho))
    with TestClient(create_app(), base_url="http://127.0.0.1") as clienteLocal:
        empresa = cadastrar(clienteLocal)
    backups = list(tmp_path.glob("banco-before-crm-001-*.db"))
    assert len(backups) == 1
    with closing(sqlite3.connect(backups[0])) as conexao:
        assert (
            conexao.execute("SELECT valor FROM registro_legado").fetchone()[0]
            == "preservado"
        )
        assert not conexao.execute(
            "SELECT 1 FROM sqlite_master WHERE name='crm_empresa'"
        ).fetchone()
    with TestClient(create_app(), base_url="http://127.0.0.1") as clienteLocal:
        assert (
            clienteLocal.get(f"/api/v1/crm/empresas/{empresa['id']}").status_code == 200
        )
    assert len(list(tmp_path.glob("banco-before-crm-001-*.db"))) == 1


def test_migracao_002_faz_backup_da_base_com_crm_anterior(tmp_path, monkeypatch):
    caminho = tmp_path / "crm-v1.db"
    versaoAnterior = (
        Path(__file__).resolve().parents[1] / "backend/migrations/001_crm_local.sql"
    )
    with closing(sqlite3.connect(caminho)) as conexao:
        conexao.executescript(versaoAnterior.read_text(encoding="utf-8"))
        conexao.execute(
            "CREATE TABLE crm_migration (versao INTEGER PRIMARY KEY, aplicadaEm TEXT NOT NULL)"
        )
        conexao.execute("INSERT INTO crm_migration VALUES (1, '2026-10-26')")
        conexao.commit()

    monkeypatch.setenv("DB_PATH", str(caminho))
    with TestClient(create_app(), base_url="http://127.0.0.1") as clienteLocal:
        assert cadastrar(clienteLocal)["nome"] == "Clínica São Mateus"

    [backup] = tmp_path.glob("banco-before-crm-002-*.db")
    with closing(sqlite3.connect(backup)) as conexao:
        assert conexao.execute("SELECT versao FROM crm_migration").fetchall() == [(1,)]
        assert conexao.execute("SELECT * FROM crm_empresa").fetchall() == []
    with closing(sqlite3.connect(caminho)) as conexao:
        assert conexao.execute("SELECT versao FROM crm_migration ORDER BY versao").fetchall() == [
            (1,), (2,)
        ]


def test_normalizacao_ddd55_e_cnpj():
    assert normalizarTelefone("(55) 99999-1234") == "5555999991234"
    assert normalizarTelefone("+55 55 99999-1234") == "5555999991234"
    assert validarCnpj("04.252.011/0001-10") == "04252011000110"


def test_edicao_contato_busca_telefone_e_versao(cliente):
    empresa = cadastrar(cliente)
    caminho = f"/api/v1/crm/empresas/{empresa['id']}/contatos"
    contato = cliente.post(
        caminho, json={"nome": "João", "telefone": "27999990000"}
    ).json()
    edicao = {
        "nome": "João Silva",
        "telefone": "+55 (27) 98888-0000",
        "version": contato["version"],
    }
    assert cliente.put(f"{caminho}/{contato['id']}", json=edicao).status_code == 200
    assert cliente.put(f"{caminho}/{contato['id']}", json=edicao).status_code == 409
    assert cliente.get("/api/v1/crm/contatos?busca=27988880000").json()["total"] == 1
    assert cliente.get("/api/v1/crm/contatos?busca=27999990000").json()["total"] == 0


def test_qualificacao_validacao_conflito_e_historico(cliente):
    empresa = cadastrar(cliente)
    caminho = f"/api/v1/crm/empresas/{empresa['id']}"
    assert cliente.get(caminho).json()["qualificacao"]["situacao"] == "novo"
    assert (
        cliente.put(
            f"{caminho}/qualificacao",
            json={"situacao": "desqualificado", "motivo": "   ", "version": 1},
        ).status_code
        == 422
    )
    assert (
        cliente.put(
            f"{caminho}/qualificacao", json={"situacao": "convertido", "version": 1}
        ).status_code
        == 422
    )
    entrada = {"situacao": "qualificado", "motivo": "Perfil compatível", "version": 1}
    resposta = cliente.put(f"{caminho}/qualificacao", json=entrada)
    assert resposta.status_code == 200
    assert resposta.json()["version"] == 2
    assert cliente.put(f"{caminho}/qualificacao", json=entrada).status_code == 409
    entrada["version"] = 2
    assert cliente.put(f"{caminho}/qualificacao", json=entrada).json()["version"] == 2
    detalhe = cliente.get(caminho).json()
    assert (
        len(
            [
                evento
                for evento in detalhe["eventos"]
                if evento["tipo"] == "qualificacao"
            ]
        )
        == 1
    )
    assert detalhe["atividades"] == []
    assert (
        cliente.put(
            "/api/v1/crm/empresas/inexistente/qualificacao", json=entrada
        ).status_code
        == 404
    )


def test_filtros_atividades_limites_data_e_situacao(cliente):
    empresa = cadastrar(cliente)
    caminho = f"/api/v1/crm/empresas/{empresa['id']}/atividades"
    for titulo, prazo, situacao in [
        ("Vencido", "2026-11-05", "pendente"),
        ("Hoje", "2026-11-06", "pendente"),
        ("Futuro", "2026-11-07", "pendente"),
        ("Sem data", None, "pendente"),
        ("Concluído", "2026-11-05", "concluida"),
        ("Cancelado", "2026-11-05", "cancelada"),
    ]:
        assert (
            cliente.post(
                caminho,
                json={
                    "titulo": titulo,
                    "prazoData": prazo,
                    "situacao": situacao,
                    "resultado": "Registrado",
                    "responsavel": "Eduardo",
                    "tipo": "lembrete",
                },
            ).status_code
            == 201
        )
    for prazo, esperado in [
        ("vencidos", "Vencido"),
        ("hoje", "Hoje"),
        ("proximos", "Futuro"),
        ("semData", "Sem data"),
    ]:
        resposta = cliente.get(
            "/api/v1/crm/atividades",
            params={"prazo": prazo, "dataReferencia": "2026-11-06"},
        ).json()
        assert resposta["total"] == 1
        assert resposta["itens"][0]["titulo"] == esperado
    assert cliente.get("/api/v1/crm/atividades?situacao=concluida").json()["total"] == 1
    assert cliente.get("/api/v1/crm/atividades?prazo=vencidos").status_code == 400
    assert cliente.get("/api/v1/crm/atividades?prazo=invalido").status_code == 422
    assert (
        cliente.get("/api/v1/crm/atividades?dataReferencia=2026-02-30").status_code
        == 422
    )
    assert (
        cliente.get(
            "/api/v1/crm/atividades?prazo=vencidos&situacao=concluida&dataReferencia=2026-11-06"
        ).json()["total"]
        == 0
    )


def test_busca_global_cnpj_contato_arquivados_e_ultima_interacao(cliente):
    empresa = cadastrar(cliente, cnpj="04.252.011/0001-10", telefone="27999990000")
    caminho = f"/api/v1/crm/empresas/{empresa['id']}"
    for busca in ("04252011000110", "04.252.011/0001-10", "clinica sao", "27999990000"):
        resultado = cliente.get("/api/v1/crm/busca", params={"busca": busca}).json()
        assert resultado["total"] == 1
        assert resultado["itens"][0]["ultimoContatoEm"] is None
        assert resultado["itens"][0]["qualificacaoSituacao"] == "novo"
    cliente.post(
        f"{caminho}/atividades",
        json={
            "titulo": "Tarefa interna",
            "tipo": "tarefa",
            "situacao": "concluida",
            "resultado": "Organizado",
            "responsavel": "Eduardo",
        },
    )
    assert (
        cliente.get("/api/v1/crm/busca?busca=clinica").json()["itens"][0][
            "ultimoContatoEm"
        ]
        is None
    )
    atividade = cliente.post(
        f"{caminho}/atividades",
        json={
            "titulo": "Ligação realizada",
            "tipo": "ligacao",
            "situacao": "concluida",
            "resultado": "Cliente pediu retorno",
            "responsavel": "Eduardo",
        },
    ).json()
    assert (
        cliente.get("/api/v1/crm/busca?busca=clinica").json()["itens"][0][
            "ultimoContatoEm"
        ]
        == atividade["concluidaEm"]
    )
    cliente.put(
        caminho,
        json={
            "nome": empresa["nome"],
            "cidade": empresa["cidade"],
            "uf": empresa["uf"],
            "cnpj": empresa["cnpj"],
            "responsavel": "Eduardo",
            "version": 1,
            "arquivada": True,
        },
    )
    assert (
        cliente.get("/api/v1/crm/busca?busca=clinica").json()["itens"][0]["arquivada"]
        == 1
    )
    assert cliente.get("/api/v1/crm/empresas?busca=clinica").json()["total"] == 0
    assert cliente.get("/api/v1/crm/busca?busca=a").status_code == 422


def test_paginacao_independente_detalhe(cliente):
    empresa = cadastrar(cliente)
    caminho = f"/api/v1/crm/empresas/{empresa['id']}"
    for indice in range(26):
        cliente.post(f"{caminho}/contatos", json={"nome": f"Contato {indice}"})
    primeira = cliente.get(caminho).json()
    segunda = cliente.get(
        caminho, params={"paginaContatos": 2, "paginaEventos": 2}
    ).json()
    assert len(primeira["contatos"]) == len(primeira["eventos"]) == 25
    assert len(segunda["contatos"]) == 1
    assert segunda["paginacao"]["contatos"]["total"] == 26
    assert segunda["paginacao"]["eventos"]["total"] == 27
    assert (
        len({contato["id"] for contato in primeira["contatos"] + segunda["contatos"]})
        == 26
    )
    assert cliente.get(caminho, params={"paginaAtividades": 0}).status_code == 422
    assert (
        cliente.get("/api/v1/crm/empresas/inexistente?paginaEventos=2").status_code
        == 404
    )


def test_migracao_invalida_reverte_estrutura(tmp_path, monkeypatch):
    caminho = tmp_path / "falha.db"
    monkeypatch.setattr(
        "pathlib.Path.read_text",
        lambda *argumentos, **opcoes: "CREATE TABLE teste_parcial (id INTEGER); INVALID SQL;",
    )
    with pytest.raises(sqlite3.OperationalError):
        aplicarMigracoes(caminho)
    with closing(sqlite3.connect(caminho)) as conexao:
        assert (
            conexao.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            == []
        )
