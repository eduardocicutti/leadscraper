from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, FastAPI, Header, Query, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.api.crm_schemas import (
    AtividadeEdicao,
    AtividadeEntrada,
    ContatoEdicao,
    ContatoEntrada,
    ConversaoEntrada,
    EmpresaEdicao,
    EmpresaEntrada,
)
from backend.domain.crm import ContextoLocal, ErroCrm
from backend.services import crm_service as servico

rotas = APIRouter(prefix="/api/v1/crm", tags=["CRM local"])


def contextoLocal(
    operador: Annotated[
        str, Header(alias="X-Operador-Local", min_length=1, max_length=100)
    ] = "Operador local",
) -> ContextoLocal:
    if not operador.strip():
        raise ErroCrm("Informe o operador local.")
    return ContextoLocal(operador.strip())


Contexto = Annotated[ContextoLocal, Depends(contextoLocal)]
Pagina = Annotated[int, Query(ge=1)]
Tamanho = Annotated[int, Query(ge=1, le=100)]
Busca = Annotated[str, Query(max_length=200)]


@rotas.get("/empresas")
def listarEmpresas(
    contexto: Contexto,
    busca: Busca = "",
    pagina: Pagina = 1,
    tamanho: Tamanho = 25,
    arquivadas: bool = False,
):
    return servico.listarEmpresas(busca, pagina, tamanho, arquivadas, contexto)


@rotas.post("/empresas", status_code=201)
def criarEmpresa(entrada: EmpresaEntrada, contexto: Contexto):
    return servico.criarEmpresa(entrada, contexto)


@rotas.get("/empresas/{empresaId}")
def detalheEmpresa(empresaId: str, contexto: Contexto):
    return servico.detalheEmpresa(empresaId, contexto)


@rotas.put("/empresas/{empresaId}")
def editarEmpresa(empresaId: str, entrada: EmpresaEdicao, contexto: Contexto):
    return servico.editarEmpresa(empresaId, entrada, contexto)


@rotas.post("/empresas/{empresaId}/contatos", status_code=201)
def criarContato(empresaId: str, entrada: ContatoEntrada, contexto: Contexto):
    return servico.criarContato(empresaId, entrada, contexto)


@rotas.post("/empresas/{empresaId}/atividades", status_code=201)
def criarAtividade(empresaId: str, entrada: AtividadeEntrada, contexto: Contexto):
    return servico.salvarAtividade(empresaId, entrada, contexto)


@rotas.put("/empresas/{empresaId}/contatos/{contatoId}")
def editarContato(
    empresaId: str, contatoId: str, entrada: ContatoEdicao, contexto: Contexto
):
    return servico.editarContato(empresaId, contatoId, entrada, contexto)


@rotas.put("/empresas/{empresaId}/atividades/{atividadeId}")
def editarAtividade(
    empresaId: str, atividadeId: str, entrada: AtividadeEdicao, contexto: Contexto
):
    return servico.salvarAtividade(empresaId, entrada, contexto, atividadeId)


@rotas.get("/contatos")
def listarContatos(
    contexto: Contexto, busca: Busca = "", pagina: Pagina = 1, tamanho: Tamanho = 25
):
    return servico.listarRelacionados("contatos", busca, pagina, tamanho, contexto)


@rotas.post("/selecionados/{selectedId}/converter")
def converterSelecionado(
    selectedId: int, entrada: ConversaoEntrada, contexto: Contexto
):
    return servico.converterSelecionado(selectedId, entrada.empresaId, contexto)


@rotas.get("/atividades")
def listarAtividades(
    contexto: Contexto, busca: Busca = "", pagina: Pagina = 1, tamanho: Tamanho = 25
):
    return servico.listarRelacionados("atividades", busca, pagina, tamanho, contexto)


def configurarCrm(app: FastAPI) -> None:
    app.include_router(rotas)

    @app.exception_handler(ErroCrm)
    async def responderErro(_pedido: Request, erro: ErroCrm):
        return JSONResponse(
            status_code=erro.status,
            content={
                "code": erro.codigo,
                "message": erro.mensagem,
                "fieldErrors": [],
                "correlationId": str(uuid4()),
                "candidatas": erro.detalhes,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def responderValidacao(pedido: Request, erro: RequestValidationError):
        if not pedido.url.path.startswith("/api/v1/crm"):
            return await request_validation_exception_handler(pedido, erro)
        return JSONResponse(
            status_code=422,
            content={
                "code": "VALIDACAO",
                "message": "Confira os campos informados.",
                "fieldErrors": [
                    {
                        "field": ".".join(str(parte) for parte in item["loc"][1:]),
                        "message": item["msg"],
                    }
                    for item in erro.errors()
                ],
                "correlationId": str(uuid4()),
            },
        )
