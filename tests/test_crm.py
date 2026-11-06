import base64
import sqlite3
from contextlib import closing

import pytest
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.domain.crm import normalizarTelefone, validarCnpj
from backend.repositories.migracoes import aplicarMigracoes


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "crm.db"))
    with TestClient(create_app()) as clienteLocal:
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
    with TestClient(create_app()) as clienteLocal:
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
    with TestClient(create_app()) as clienteLocal:
        assert (
            clienteLocal.get(f"/api/v1/crm/empresas/{empresa['id']}").status_code == 200
        )
    assert len(list(tmp_path.glob("banco-before-crm-001-*.db"))) == 1


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
