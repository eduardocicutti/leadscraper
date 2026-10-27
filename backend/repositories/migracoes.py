import hashlib
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from backend.core.logging import logger


def aplicarMigracoes(caminhoBanco: Path) -> None:
    existiaBanco = caminhoBanco.exists() and caminhoBanco.stat().st_size > 0
    with closing(sqlite3.connect(caminhoBanco)) as conexao:
        possuiControle = conexao.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='crm_migration'"
        ).fetchone()
        if (
            possuiControle
            and conexao.execute("SELECT 1 FROM crm_migration WHERE versao=1").fetchone()
        ):
            return
        if existiaBanco:
            nomeBackup = f"banco-before-crm-001-{uuid4().hex}.db"
            caminhoBackup = caminhoBanco.parent / nomeBackup
            with closing(sqlite3.connect(caminhoBackup)) as destino:
                conexao.backup(destino)
            checksum = hashlib.sha256(caminhoBackup.read_bytes()).hexdigest()
            logger.info("Backup anterior ao CRM: %s SHA256=%s", nomeBackup, checksum)
        script = (
            Path(__file__).resolve().parents[1] / "migrations" / "001_crm_local.sql"
        ).read_text(encoding="utf-8")
        conexao.execute("PRAGMA foreign_keys=ON")
        try:
            conexao.executescript(
                "BEGIN IMMEDIATE;"
                "CREATE TABLE IF NOT EXISTS crm_migration (versao INTEGER PRIMARY KEY, aplicadaEm TEXT NOT NULL);"
                + script
            )
            conexao.execute(
                "INSERT INTO crm_migration(versao, aplicadaEm) VALUES (1, ?)",
                (datetime.now(timezone.utc).isoformat(),),
            )
            conexao.commit()
        except Exception:
            conexao.rollback()
            raise
