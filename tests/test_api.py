import base64
import io
import os
import sqlite3
import pytest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import parse_qs, unquote, urlparse

from fastapi.testclient import TestClient
from openpyxl import load_workbook

from backend.api.app import create_app
from backend.repositories import database
from backend.services.export_service import generate_xlsx


def make_client(tmp_path: str) -> TestClient:
    os.environ["DB_PATH"] = str(Path(tmp_path) / "test.db")
    return TestClient(create_app(), base_url="http://127.0.0.1")


def csv_payload(text: str, filename: str = "leads.csv") -> dict:
    return {
        "filename": filename,
        "content_base64": base64.b64encode(text.encode("utf-8")).decode("ascii"),
        "prospectador": "Eduardo",
    }


def whatsapp_text(link: str) -> str:
    parsed = urlparse(link)
    text = parse_qs(parsed.query).get("text", [""])[0]
    return unquote(text)


def test_diagnostics_reports_database_counts():
    with TemporaryDirectory() as tmp:
        with make_client(tmp) as client:
            response = client.get("/diagnostics")
            assert response.status_code == 200
            data = response.json()
            assert data["ok"] is True
            assert data["integrity_check"] == "ok"
            assert data["counts"]["selected_leads"] == 0
            assert data["db_path"].endswith("test.db")


@pytest.mark.parametrize("quantidade", [0, -1, 501, 1.5])
def test_rejeita_quantidade_invalida_sem_iniciar_extracao(quantidade):
    with TemporaryDirectory() as pasta:
        with make_client(pasta) as cliente:
            resposta = cliente.post("/scrape", json={
                "segmento": "clinicas", "cidade": "Sao Mateus", "estado": "ES",
                "max_results": quantidade, "prospectador": "Teste",
            })
            assert resposta.status_code == 422
            assert cliente.get("/history").json() == []


def test_spreadsheet_import_deduplicates_by_phone():
    with TemporaryDirectory() as tmp:
        with make_client(tmp) as client:
            content = """Nome da empresa;Telefone/WhatsApp;Cidade;UF;Ramo de atividade
Clínica Boa Vida;(11) 91234-5678;São Paulo;SP;Clínica
Clinica Boa Vida Ltda;11912345678;São Paulo;SP;Clínica
Padaria Sol;(11) 3333-4444;Campinas;SP;Padaria
"""
            response = client.post(
                "/selected-leads/import-spreadsheet",
                json=csv_payload(content),
            )
            assert response.status_code == 200
            data = response.json()
            assert data["imported_count"] == 2
            assert data["skipped_count"] == 1
            assert data["skipped"][0]["reason"] == "telefone"

            selected = client.get("/selected-leads").json()
            assert len(selected) == 2


def test_segment_template_refreshes_only_matching_segment_message():
    with TemporaryDirectory() as tmp:
        with make_client(tmp) as client:
            content = """Nome da empresa;Telefone/WhatsApp;Cidade;UF;Ramo de atividade
Clínica Boa Vida;(11) 91234-5678;São Paulo;SP;Clínica
Academia Norte;(11) 99888-7777;São Paulo;SP;Academia
"""
            client.post("/selected-leads/import-spreadsheet", json=csv_payload(content))

            response = client.put(
                "/selected-leads/segment-templates",
                json={
                    "segmento": "Clínica",
                    "template": "Mensagem clínica para {empresa} em {cidade}",
                },
            )
            assert response.status_code == 200

            selected = client.get("/selected-leads").json()
            by_name = {lead["nome"]: lead for lead in selected}
            clinic_text = whatsapp_text(by_name["Clínica Boa Vida"]["whatsapp_link"])
            academy_text = whatsapp_text(by_name["Academia Norte"]["whatsapp_link"])

            assert "Mensagem clínica" in clinic_text
            assert "Mensagem clínica" not in academy_text


def test_filtered_export_contains_only_matching_selected_leads():
    with TemporaryDirectory() as tmp:
        with make_client(tmp) as client:
            content = """Nome da empresa;Telefone/WhatsApp;Cidade;UF;Ramo de atividade
Clínica Boa Vida;(11) 91234-5678;São Paulo;SP;Clínica
Padaria Sol;(11) 3333-4444;Campinas;SP;Padaria
"""
            client.post("/selected-leads/import-spreadsheet", json=csv_payload(content))

            response = client.post(
                "/selected-leads/export",
                json={
                    "segmento": "Clínica",
                    "cidade": "",
                    "estado": "",
                    "temperatura": "",
                    "com_whatsapp": "",
                    "com_site": "",
                    "prospectador": "Eduardo",
                },
            )
            assert response.status_code == 200
            workbook_path = Path(tmp) / "export.xlsx"
            workbook_path.write_bytes(response.content)
            workbook = load_workbook(workbook_path)
            sheet = workbook.active

            company_names = [sheet.cell(row=row, column=3).value for row in range(2, sheet.max_row + 1)]
            assert "Clínica Boa Vida" in company_names
            assert "Padaria Sol" not in company_names


def test_backup_and_restore_round_trip_database():
    with TemporaryDirectory() as tmp:
        with make_client(tmp) as client:
            content = """Nome da empresa;Telefone/WhatsApp;Cidade;UF;Ramo de atividade
ClÃ­nica Boa Vida;(11) 91234-5678;SÃ£o Paulo;SP;ClÃ­nica
"""
            client.post("/selected-leads/import-spreadsheet", json=csv_payload(content))

            backup = client.get("/backup")
            assert backup.status_code == 200
            assert len(backup.content) > 0

            lead = client.get("/selected-leads").json()[0]
            delete_response = client.delete(f"/selected-leads/{lead['id']}")
            assert delete_response.status_code == 200
            assert client.get("/selected-leads").json() == []

            restore_response = client.post(
                "/restore",
                json={
                    "filename": "backup.db",
                    "content_base64": base64.b64encode(backup.content).decode("ascii"),
                },
            )
            assert restore_response.status_code == 200
            restored = client.get("/selected-leads").json()
            assert len(restored) == 1
            assert restored[0]["nome"] == "ClÃ­nica Boa Vida"


def test_backup_gerado_inclui_alteracoes_do_wal_de_base_maior(tmp_path):
    with make_client(str(tmp_path)) as cliente:
        origem = tmp_path / "test.db"
        with closing(sqlite3.connect(origem)) as conexao:
            conteudo = "registro de teste\n" * 70000
            conexao.execute(
                "INSERT INTO appsetting (key,value,updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                ("teste_backup", conteudo),
            )
            conexao.commit()
            resposta = cliente.get("/backup")
            assert resposta.status_code == 200
            assert len(resposta.content) > 1024 * 1024
        arquivo = tmp_path / "copia.db"
        arquivo.write_bytes(resposta.content)
        with closing(sqlite3.connect(arquivo)) as copia:
            assert copia.execute(
                "SELECT value FROM appsetting WHERE key='teste_backup'"
            ).fetchone() == (conteudo,)


def test_api_local_reconhece_origem_do_desktop(tmp_path):
    with make_client(str(tmp_path)) as cliente:
        resposta = cliente.post(
            "/api/v1/crm/empresas",
            headers={"Origin": "https://tauri.localhost"},
            json={"nome": "Empresa de teste", "responsavel": "Ana"},
        )
        assert resposta.status_code == 201
        assert resposta.headers["access-control-allow-origin"] == "https://tauri.localhost"
        assert cliente.get("http://testserver/health").status_code == 400
        origemNaoPermitida = cliente.post(
            "/health", headers={"Origin": "https://example.com"}
        )
        assert origemNaoPermitida.status_code == 403
        assert origemNaoPermitida.json()["code"] == "ORIGEM_NAO_PERMITIDA"
        assert origemNaoPermitida.json()["correlationId"]


def test_restore_incompativel_preserva_banco_ativo(tmp_path):
    arquivo = tmp_path / "outro-app.db"
    with closing(sqlite3.connect(arquivo)) as conexao:
        conexao.execute("CREATE TABLE itens (id INTEGER PRIMARY KEY)")
    with make_client(str(tmp_path)) as cliente:
        assert cliente.post(
            "/api/v1/crm/empresas",
            json={"nome": "Empresa preservada", "responsavel": "Ana"},
        ).status_code == 201
        resposta = cliente.post(
            "/restore",
            json={"content_base64": base64.b64encode(arquivo.read_bytes()).decode("ascii")},
        )
        assert resposta.status_code == 400
        assert cliente.get("/api/v1/crm/empresas").json()["total"] == 1
    assert not list(tmp_path.glob("banco-before-restore-*"))
    assert not list(tmp_path.glob(".restore-*"))


def test_restore_com_migracao_marcada_e_coluna_crm_ausente(tmp_path):
    with make_client(str(tmp_path)) as cliente:
        assert cliente.post(
            "/api/v1/crm/empresas",
            json={"nome": "Empresa preservada", "responsavel": "Ana"},
        ).status_code == 201
        arquivo = tmp_path / "backup-incompleto.db"
        arquivo.write_bytes(cliente.get("/backup").content)
        with closing(sqlite3.connect(arquivo)) as conexao:
            conexao.execute("ALTER TABLE crm_atividade DROP COLUMN resultado")
        resposta = cliente.post(
            "/restore",
            json={"content_base64": base64.b64encode(arquivo.read_bytes()).decode("ascii")},
        )
        assert resposta.status_code == 400
        assert cliente.get("/api/v1/crm/empresas").json()["total"] == 1


def test_exportacao_excel_preserva_textos_e_tipos_das_celulas():
    arquivo = generate_xlsx(
        [{"nome": "= Em revisão", "score": 50}], "= Pesquisa interna", "São Mateus", "ES", "Ana"
    )
    planilha = load_workbook(io.BytesIO(arquivo))
    try:
        empresa = planilha["Página1"]["C2"]
        assert (empresa.value, empresa.data_type) == ("= Em revisão", "s")
        segmento = planilha["Resumo"]["B4"]
        assert (segmento.value, segmento.data_type) == ("= Pesquisa interna", "s")
        assert planilha["Página1"]["G2"].value is False
        assert planilha["Página1"]["O2"].value == 50
    finally:
        planilha.close()


def test_falha_na_ativacao_recarrega_banco_anterior(tmp_path, monkeypatch):
    with make_client(str(tmp_path)) as cliente:
        arquivo = cliente.get("/backup").content
        assert cliente.post(
            "/api/v1/crm/empresas",
            json={"nome": "Empresa depois do backup", "responsavel": "Ana"},
        ).status_code == 201
        iniciarBanco = database.init_db
        falhouAtivacao = False

        def simularFalhaDeAtivacao(caminho: str) -> None:
            nonlocal falhouAtivacao
            if not falhouAtivacao:
                falhouAtivacao = True
                raise OSError("Falha de ativação simulada.")
            iniciarBanco(caminho)

        monkeypatch.setattr(database, "init_db", simularFalhaDeAtivacao)
        resposta = cliente.post(
            "/restore",
            json={"content_base64": base64.b64encode(arquivo).decode("ascii")},
        )
        assert resposta.status_code == 500
        assert falhouAtivacao
        assert cliente.get("/api/v1/crm/empresas").json()["total"] == 1
    assert len(list(tmp_path.glob("banco-before-restore-*"))) == 1
