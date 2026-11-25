from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ConfigDict, Field

from backend.api.schemas import QuantidadeColeta
from backend.core.logging import logger
from backend.domain.crm import ErroCrm
from backend.services import localidades_service as localidades
from backend.services.scrape_service import iniciarColeta


rotas = APIRouter(prefix="/api/v1", tags=["Prospecção local"])


class ProspeccaoEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    segmento: str = Field(min_length=1, max_length=120)
    estado: str = Field(min_length=2, max_length=2)
    municipioCodigo: int = Field(strict=True, ge=1_000_000, le=9_999_999)
    max_results: QuantidadeColeta
    prospectador: str = Field(default="", max_length=100)


def metadadosCatalogo(catalogo: localidades.CatalogoMunicipios) -> dict[str, str]:
    return {"versao": catalogo.versao, "fonte": localidades.FONTE_MUNICIPIOS}


@rotas.get("/localidades/municipios")
def listarMunicipios(
    uf: Annotated[str, Query(min_length=2, max_length=2)],
    busca: Annotated[str, Query(max_length=120)] = "",
):
    uf = uf.upper()
    if uf not in localidades.UFS:
        raise RequestValidationError([
            {"loc": ("query", "uf"), "msg": "Informe uma UF brasileira válida."}
        ])
    catalogo = localidades.obterCatalogo()
    return {**metadadosCatalogo(catalogo), "itens": catalogo.filtrar(uf, busca)}


@rotas.post("/localidades/atualizar")
def atualizarMunicipios():
    try:
        return metadadosCatalogo(localidades.atualizarCatalogo())
    except (OSError, ValueError):
        logger.warning("Falha na atualização do catálogo de municípios", exc_info=True)
        raise ErroCrm(
            "Não foi possível atualizar o catálogo. A última versão válida foi mantida.",
            "CATALOGO_INDISPONIVEL",
            503,
        ) from None


@rotas.post("/prospeccoes")
def iniciarProspeccao(entrada: ProspeccaoEntrada) -> dict[str, str]:
    estado = entrada.estado.upper()
    if estado not in localidades.UFS:
        raise RequestValidationError([
            {"loc": ("body", "estado"), "msg": "Informe uma UF brasileira válida."}
        ])
    municipio = localidades.obterCatalogo().localizar(entrada.municipioCodigo)
    if municipio is None or municipio.uf != estado:
        raise RequestValidationError([
            {
                "loc": ("body", "municipioCodigo"),
                "msg": "Selecione um município válido da UF informada.",
            }
        ])
    jobId = iniciarColeta(
        entrada.segmento, municipio.nome, estado, entrada.max_results,
        entrada.prospectador, municipioCodigo=municipio.codigo,
    )
    return {"job_id": jobId}
