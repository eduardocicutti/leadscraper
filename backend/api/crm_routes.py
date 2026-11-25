from typing import Annotated
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, FastAPI, Header, Path, Query, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.api.crm_schemas import (
    AtividadeEdicao,
    AtividadeEntrada,
    ContatoEdicao,
    ContatoEntrada,
    ConversaoEntrada,
    DataIso,
    EmpresaEdicao,
    EmpresaEntrada,
    QualificacaoEntrada,
)
from backend.domain.crm import MAXIMO_INTEIRO_SQLITE, ContextoLocal, ErroCrm
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
MAXIMO_TAMANHO_PAGINA = 100
Pagina = Annotated[
    int, Query(ge=1, le=MAXIMO_INTEIRO_SQLITE // MAXIMO_TAMANHO_PAGINA + 1)
]
Tamanho = Annotated[int, Query(ge=1, le=MAXIMO_TAMANHO_PAGINA)]
IdLegado = Annotated[int, Path(ge=1, le=MAXIMO_INTEIRO_SQLITE)]
Busca = Annotated[str, Query(max_length=200)]
Responsavel = Annotated[str, Query(max_length=100)]


@rotas.get("/empresas")
def listarEmpresas(
    contexto: Contexto,
    busca: Busca = "",
    pagina: Pagina = 1,
    tamanho: Tamanho = 25,
    arquivadas: bool = False,
    qualificacao: Literal["", "novo", "analise", "qualificado", "desqualificado"] = "",
    responsavel: Responsavel = "",
    relacionamento: Literal["", "prospectada", "semAbordagem"] = "",
):
    return servico.listarEmpresas(
        busca, pagina, tamanho, arquivadas, contexto, qualificacao, responsavel, relacionamento
    )


@rotas.get("/busca")
def buscarCrm(
    contexto: Contexto,
    busca: Annotated[str, Query(min_length=2, max_length=200)],
    pagina: Pagina = 1,
    tamanho: Tamanho = 25,
):
    return servico.listarEmpresas(busca, pagina, tamanho, None, contexto)


@rotas.post("/empresas", status_code=201)
def criarEmpresa(entrada: EmpresaEntrada, contexto: Contexto):
    return servico.criarEmpresa(entrada, contexto)


@rotas.get("/empresas/{empresaId}")
def detalheEmpresa(
    empresaId: str,
    contexto: Contexto,
    paginaContatos: Pagina = 1,
    paginaAtividades: Pagina = 1,
    paginaEventos: Pagina = 1,
):
    return servico.detalheEmpresa(
        empresaId, contexto, paginaContatos, paginaAtividades, paginaEventos
    )


@rotas.put("/empresas/{empresaId}")
def editarEmpresa(empresaId: str, entrada: EmpresaEdicao, contexto: Contexto):
    return servico.editarEmpresa(empresaId, entrada, contexto)


@rotas.put("/empresas/{empresaId}/qualificacao")
def qualificarEmpresa(empresaId: str, entrada: QualificacaoEntrada, contexto: Contexto):
    return servico.qualificarEmpresa(empresaId, entrada, contexto)


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
    selectedId: IdLegado, entrada: ConversaoEntrada, contexto: Contexto
):
    return servico.converterSelecionado(
        selectedId, entrada.empresaId, contexto, entrada.confirmarTelefoneCompartilhado
    )


@rotas.post("/historico/{historicoId}/leads/{leadId}/converter")
def converterLeadHistorico(
    historicoId: IdLegado,
    leadId: IdLegado,
    entrada: ConversaoEntrada,
    contexto: Contexto,
):
    return servico.converterLeadHistorico(
        historicoId, leadId, entrada.empresaId, contexto, entrada.confirmarTelefoneCompartilhado
    )


@rotas.get("/atividades")
def listarAtividades(
    contexto: Contexto,
    busca: Busca = "",
    pagina: Pagina = 1,
    tamanho: Tamanho = 25,
    situacao: Literal["", "pendente", "concluida", "cancelada"] = "",
    prazo: Literal["", "vencidos", "hoje", "proximos", "semData"] = "",
    dataReferencia: DataIso | None = None,
    tipo: Literal["", "ligacao", "whatsapp", "email", "reuniao", "tarefa", "lembrete"] = "",
    responsavel: Responsavel = "",
):
    return servico.listarRelacionados(
        "atividades", busca, pagina, tamanho, contexto, situacao, prazo, dataReferencia,
        tipo, responsavel,
    )


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
        if not pedido.url.path.startswith("/api/v1/"):
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
