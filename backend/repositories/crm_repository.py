from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import Connection, text

from backend.domain.crm import ContextoLocal, ErroCrm
from backend.repositories import database


@contextmanager
def transacao(*, bloquearEscrita: bool = False) -> Iterator[Connection]:
    database.ensure_db_ready()
    with database.db_lock, database.engine.begin() as conexao:
        if bloquearEscrita:
            conexao.exec_driver_sql("BEGIN IMMEDIATE")
        yield conexao


def consultar(conexao: Connection, comando: str, parametros: dict) -> list[dict]:
    return [
        dict(linha) for linha in conexao.execute(text(comando), parametros).mappings()
    ]


def buscarEmpresa(conexao: Connection, empresaId: str, contexto: ContextoLocal) -> dict:
    empresas = consultar(
        conexao,
        "SELECT * FROM crm_empresa WHERE id=:id AND organizationId=:org",
        {"id": empresaId, "org": contexto.organizationId},
    )
    if not empresas:
        raise ErroCrm("Empresa não encontrada.", "NAO_ENCONTRADO", 404)
    return empresas[0]


def inserir(conexao: Connection, tabela: str, valores: dict) -> None:
    tabelasPermitidas = {
        "crm_empresa",
        "crm_contato",
        "crm_lead",
        "crm_atividade",
        "crm_evento",
        "crm_origem_selecionada",
        "crm_origem_historico",
    }
    if tabela not in tabelasPermitidas:
        raise ValueError("Tabela inválida.")
    campos = ",".join(valores)
    marcadores = ",".join(f":{campo}" for campo in valores)
    conexao.execute(
        text(f"INSERT INTO {tabela} ({campos}) VALUES ({marcadores})"), valores
    )


def atualizar(
    conexao: Connection,
    tabela: str,
    entidadeId: str,
    versao: int,
    valores: dict,
    contexto: ContextoLocal,
) -> None:
    if tabela not in {"crm_empresa", "crm_contato", "crm_atividade", "crm_lead"}:
        raise ValueError("Tabela inválida.")
    atribuicoes = ",".join(f"{campo}=:{campo}" for campo in valores)
    resultado = conexao.execute(
        text(
            f"UPDATE {tabela} SET {atribuicoes}, version=version+1 WHERE id=:entidadeId AND organizationId=:org AND version=:versao"
        ),
        {
            **valores,
            "entidadeId": entidadeId,
            "org": contexto.organizationId,
            "versao": versao,
        },
    )
    if resultado.rowcount != 1:
        raise ErroCrm(
            "O registro mudou ou não existe mais. Recarregue antes de editar.",
            "VERSAO_CONFLITANTE",
            409,
        )
