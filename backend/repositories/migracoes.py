import hashlib
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from backend.core.logging import logger


MIGRACOES = ("001_crm_local.sql", "002_crm_origem_historico.sql")


def lerMigracao(arquivo: str) -> str:
    pasta = Path(__file__).resolve().parents[1] / "migrations"
    return (pasta / arquivo).read_text(encoding="utf-8")


def aplicarMigracoes(caminhoBanco: Path) -> None:
    existiaBanco = caminhoBanco.exists() and caminhoBanco.stat().st_size > 0
    with closing(sqlite3.connect(caminhoBanco)) as conexao:
        possuiControle = conexao.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='crm_migration'"
        ).fetchone()
        aplicadas = (
            {versao for (versao,) in conexao.execute("SELECT versao FROM crm_migration")}
            if possuiControle
            else set()
        )
        pendentes = [
            (versao, arquivo)
            for versao, arquivo in enumerate(MIGRACOES, start=1)
            if versao not in aplicadas
        ]
        if not pendentes:
            return
        if existiaBanco:
            nomeBackup = f"banco-before-crm-{pendentes[0][0]:03d}-{uuid4().hex}.db"
            caminhoBackup = caminhoBanco.parent / nomeBackup
            with closing(sqlite3.connect(caminhoBackup)) as destino:
                conexao.backup(destino)
            checksum = hashlib.sha256(caminhoBackup.read_bytes()).hexdigest()
            logger.info("Backup anterior ao CRM: %s SHA256=%s", nomeBackup, checksum)
        script = "\n".join(lerMigracao(arquivo) for _, arquivo in pendentes)
        conexao.execute("PRAGMA foreign_keys=ON")
        try:
            conexao.executescript(
                "BEGIN IMMEDIATE;"
                "CREATE TABLE IF NOT EXISTS crm_migration (versao INTEGER PRIMARY KEY, aplicadaEm TEXT NOT NULL);"
                + script
            )
            instante = datetime.now(timezone.utc).isoformat()
            conexao.executemany(
                "INSERT INTO crm_migration(versao, aplicadaEm) VALUES (?, ?)",
                [(versao, instante) for versao, _ in pendentes],
            )
            conexao.commit()
        except Exception:
            conexao.rollback()
            raise
