import re
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Connection

from backend.api.crm_schemas import (
    AtividadeEdicao,
    AtividadeEntrada,
    ContatoEdicao,
    ContatoEntrada,
    EmpresaEdicao,
    EmpresaEntrada,
)
from backend.domain.crm import (
    ContextoLocal,
    ErroCrm,
    normalizarTelefone,
    normalizarTexto,
)
from backend.repositories import crm_repository as repositorio


def agoraUtc() -> str:
    return datetime.now(timezone.utc).isoformat()


def metadados(contexto: ContextoLocal) -> dict:
    instante = agoraUtc()
    return {
        "id": str(uuid4()),
        "organizationId": contexto.organizationId,
        "createdBy": contexto.actorId,
        "updatedBy": contexto.actorId,
        "createdAt": instante,
        "updatedAt": instante,
        "version": 1,
    }


def registrarEvento(
    conexao: Connection,
    empresaId: str,
    tipo: str,
    descricao: str,
    contexto: ContextoLocal,
) -> None:
    repositorio.inserir(
        conexao,
        "crm_evento",
        {
            "id": str(uuid4()),
            "empresaId": empresaId,
            "organizationId": contexto.organizationId,
            "tipo": tipo,
            "descricao": descricao,
            "autorId": contexto.actorId,
            "autorNome": contexto.nome,
            "createdAt": agoraUtc(),
        },
    )


def dadosEmpresa(entrada: EmpresaEntrada) -> dict:
    valores = entrada.model_dump(exclude={"telefone", "version"})
    return {
        **valores,
        "cnpj": entrada.cnpj or None,
        "nomeNormalizado": normalizarTexto(entrada.nome),
        "cidadeNormalizada": normalizarTexto(entrada.cidade),
    }


def conferirDuplicidade(
    conexao: Connection, valores: dict, contexto: ContextoLocal, empresaId: str = ""
) -> None:
    candidatas = repositorio.consultar(
        conexao,
        """SELECT id,nome,cidade,uf FROM crm_empresa
        WHERE organizationId=:org AND id<>:id AND
        ((:cnpj IS NOT NULL AND cnpj=:cnpj) OR (:urlMaps<>'' AND urlMaps=:urlMaps)
        OR (nomeNormalizado=:nomeNormalizado AND cidadeNormalizada=:cidadeNormalizada AND uf=:uf))""",
        {**valores, "org": contexto.organizationId, "id": empresaId},
    )
    if candidatas:
        raise ErroCrm(
            "Possível cadastro duplicado. Confira as empresas existentes antes de continuar.",
            "EMPRESA_DUPLICADA",
            409,
            candidatas,
        )


def adicionarContato(
    conexao: Connection,
    empresaId: str,
    entrada: ContatoEntrada,
    contexto: ContextoLocal,
) -> dict:
    valores = {
        **entrada.model_dump(),
        **metadados(contexto),
        "empresaId": empresaId,
        "nomeNormalizado": normalizarTexto(entrada.nome),
        "telefoneNormalizado": normalizarTelefone(entrada.telefone),
    }
    repositorio.inserir(conexao, "crm_contato", valores)
    registrarEvento(
        conexao, empresaId, "contato", f"Contato cadastrado: {entrada.nome}.", contexto
    )
    return valores


def adicionarEmpresa(
    conexao: Connection, entrada: EmpresaEntrada, contexto: ContextoLocal
) -> dict:
    valores = {**dadosEmpresa(entrada), **metadados(contexto), "arquivada": False}
    conferirDuplicidade(conexao, valores, contexto)
    repositorio.inserir(conexao, "crm_empresa", valores)
    registrarEvento(
        conexao,
        valores["id"],
        "cadastro",
        "Empresa cadastrada. Nenhuma abordagem registrada.",
        contexto,
    )
    repositorio.inserir(
        conexao,
        "crm_lead",
        {
            **metadados(contexto),
            "empresaId": valores["id"],
            "situacao": "novo",
            "motivo": "",
        },
    )
    if entrada.telefone:
        adicionarContato(
            conexao,
            valores["id"],
            ContatoEntrada(nome="Contato principal", telefone=entrada.telefone),
            contexto,
        )
    return valores


def criarEmpresa(entrada: EmpresaEntrada, contexto: ContextoLocal) -> dict:
    with repositorio.transacao() as conexao:
        return adicionarEmpresa(conexao, entrada, contexto)


def editarEmpresa(
    empresaId: str, entrada: EmpresaEdicao, contexto: ContextoLocal
) -> dict:
    if entrada.telefone:
        raise ErroCrm("Edite telefones pelo cadastro de contatos.")
    with repositorio.transacao() as conexao:
        repositorio.buscarEmpresa(conexao, empresaId, contexto)
        valores = dadosEmpresa(entrada)
        conferirDuplicidade(conexao, valores, contexto, empresaId)
        repositorio.atualizar(
            conexao,
            "crm_empresa",
            empresaId,
            entrada.version,
            {**valores, "updatedBy": contexto.actorId, "updatedAt": agoraUtc()},
            contexto,
        )
        registrarEvento(
            conexao,
            empresaId,
            "edicao",
            "Cadastro atualizado" + (" e arquivado." if entrada.arquivada else "."),
            contexto,
        )
        return repositorio.buscarEmpresa(conexao, empresaId, contexto)


def listarEmpresas(
    busca: str, pagina: int, tamanho: int, arquivadas: bool, contexto: ContextoLocal
) -> dict:
    termo = normalizarTexto(busca)
    digitos = re.sub(r"\D", "", busca)
    if digitos and len(digitos) in (10, 11, 12, 13):
        digitos = normalizarTelefone(busca)
    parametros = {
        "org": contexto.organizationId,
        "busca": f"%{termo}%",
        "telefone": f"%{digitos}%",
        "temTelefone": bool(digitos),
        "arquivadas": arquivadas,
        "limite": tamanho,
        "inicio": (pagina - 1) * tamanho,
    }
    filtro = """e.organizationId=:org AND e.arquivada=:arquivadas AND
        (e.nomeNormalizado LIKE :busca OR e.cidadeNormalizada LIKE :busca OR
        EXISTS (SELECT 1 FROM crm_contato c WHERE c.empresaId=e.id AND c.organizationId=:org
        AND (c.nomeNormalizado LIKE :busca OR (:temTelefone AND c.telefoneNormalizado LIKE :telefone))))"""
    with repositorio.transacao() as conexao:
        total = repositorio.consultar(
            conexao,
            f"SELECT count(*) AS total FROM crm_empresa e WHERE {filtro}",
            parametros,
        )[0]["total"]
        itens = repositorio.consultar(
            conexao,
            f"SELECT e.* FROM crm_empresa e WHERE {filtro} ORDER BY e.nomeNormalizado,e.id LIMIT :limite OFFSET :inicio",
            parametros,
        )
        return {"itens": itens, "total": total, "pagina": pagina, "tamanho": tamanho}


def detalheEmpresa(empresaId: str, contexto: ContextoLocal) -> dict:
    with repositorio.transacao() as conexao:
        empresa = repositorio.buscarEmpresa(conexao, empresaId, contexto)
        parametros = {"id": empresaId, "org": contexto.organizationId}
        for chave, tabela in (
            ("contatos", "crm_contato"),
            ("atividades", "crm_atividade"),
            ("eventos", "crm_evento"),
        ):
            empresa[chave] = repositorio.consultar(
                conexao,
                f"SELECT * FROM {tabela} WHERE empresaId=:id AND organizationId=:org ORDER BY createdAt DESC,id DESC",
                parametros,
            )
        return empresa


def criarContato(
    empresaId: str, entrada: ContatoEntrada, contexto: ContextoLocal
) -> dict:
    with repositorio.transacao() as conexao:
        repositorio.buscarEmpresa(conexao, empresaId, contexto)
        return adicionarContato(conexao, empresaId, entrada, contexto)


def editarContato(
    empresaId: str, contatoId: str, entrada: ContatoEdicao, contexto: ContextoLocal
) -> dict:
    with repositorio.transacao() as conexao:
        repositorio.buscarEmpresa(conexao, empresaId, contexto)
        parametros = {
            "id": contatoId,
            "empresaId": empresaId,
            "org": contexto.organizationId,
        }
        existentes = repositorio.consultar(
            conexao,
            "SELECT * FROM crm_contato WHERE id=:id AND empresaId=:empresaId AND organizationId=:org",
            parametros,
        )
        if not existentes:
            raise ErroCrm("Contato não encontrado.", "NAO_ENCONTRADO", 404)
        valores = {
            **entrada.model_dump(exclude={"version"}),
            "nomeNormalizado": normalizarTexto(entrada.nome),
            "telefoneNormalizado": normalizarTelefone(entrada.telefone),
            "updatedBy": contexto.actorId,
            "updatedAt": agoraUtc(),
        }
        repositorio.atualizar(
            conexao, "crm_contato", contatoId, entrada.version, valores, contexto
        )
        registrarEvento(
            conexao,
            empresaId,
            "contato",
            f"Contato atualizado: {existentes[0]['nome']} → {entrada.nome}.",
            contexto,
        )
        return repositorio.consultar(
            conexao,
            "SELECT * FROM crm_contato WHERE id=:id AND organizationId=:org",
            parametros,
        )[0]


def salvarAtividade(
    empresaId: str,
    entrada: AtividadeEntrada,
    contexto: ContextoLocal,
    atividadeId: str | None = None,
) -> dict:
    with repositorio.transacao() as conexao:
        repositorio.buscarEmpresa(conexao, empresaId, contexto)
        valores = entrada.model_dump(mode="json", exclude={"version"})
        valores["concluidaEm"] = agoraUtc() if entrada.situacao == "concluida" else None
        if atividadeId:
            anteriores = repositorio.consultar(
                conexao,
                "SELECT * FROM crm_atividade WHERE id=:id AND empresaId=:empresaId AND organizationId=:org",
                {
                    "id": atividadeId,
                    "empresaId": empresaId,
                    "org": contexto.organizationId,
                },
            )
            if not anteriores:
                raise ErroCrm("Atividade não encontrada.", "NAO_ENCONTRADO", 404)
            anterior = anteriores[0]
            if anterior["situacao"] == "concluida" and entrada.situacao == "concluida":
                valores["concluidaEm"] = anterior["concluidaEm"]
            if not isinstance(entrada, AtividadeEdicao):
                raise ErroCrm("Informe a versão da atividade.")
            repositorio.atualizar(
                conexao,
                "crm_atividade",
                atividadeId,
                entrada.version,
                {**valores, "updatedBy": contexto.actorId, "updatedAt": agoraUtc()},
                contexto,
            )
            descricao = f"Atividade atualizada: {entrada.titulo}. Situação: {anterior['situacao']} → {entrada.situacao}. Prazo: {anterior['prazoData'] or 'sem data'} → {valores['prazoData'] or 'sem data'}."
        else:
            valores = {
                **valores,
                **metadados(contexto),
                "empresaId": empresaId,
                "autorNome": contexto.nome,
            }
            atividadeId = valores["id"]
            repositorio.inserir(conexao, "crm_atividade", valores)
            descricao = (
                f"Atividade criada: {entrada.titulo}. Situação: {entrada.situacao}."
            )
        registrarEvento(conexao, empresaId, "atividade", descricao, contexto)
        return repositorio.consultar(
            conexao,
            "SELECT * FROM crm_atividade WHERE id=:id AND organizationId=:org",
            {"id": atividadeId, "org": contexto.organizationId},
        )[0]


def listarRelacionados(
    tipo: str, busca: str, pagina: int, tamanho: int, contexto: ContextoLocal
) -> dict:
    tabela = "crm_contato" if tipo == "contatos" else "crm_atividade"
    campo = "r.nomeNormalizado" if tipo == "contatos" else "r.titulo"
    parametros = {
        "org": contexto.organizationId,
        "busca": f"%{normalizarTexto(busca) if tipo == 'contatos' else busca}%",
        "limite": tamanho,
        "inicio": (pagina - 1) * tamanho,
    }
    filtroTelefone = ""
    if tipo == "contatos":
        digitos = re.sub(r"\D", "", busca)
        if len(digitos) in (10, 11, 12, 13):
            digitos = normalizarTelefone(busca)
        parametros.update({"telefone": f"%{digitos}%", "temTelefone": bool(digitos)})
        filtroTelefone = " OR (:temTelefone AND r.telefoneNormalizado LIKE :telefone)"
    filtro = f"r.organizationId=:org AND e.organizationId=:org AND ({campo} LIKE :busca OR e.nomeNormalizado LIKE :busca{filtroTelefone})"
    with repositorio.transacao() as conexao:
        origem = (
            f"FROM {tabela} r JOIN crm_empresa e ON e.id=r.empresaId WHERE {filtro}"
        )
        total = repositorio.consultar(
            conexao, f"SELECT count(*) AS total {origem}", parametros
        )[0]["total"]
        itens = repositorio.consultar(
            conexao,
            f"SELECT r.*,e.nome AS empresaNome {origem} ORDER BY r.createdAt DESC,r.id DESC LIMIT :limite OFFSET :inicio",
            parametros,
        )
        return {"itens": itens, "total": total, "pagina": pagina, "tamanho": tamanho}


def converterSelecionado(
    selectedId: int, empresaId: str | None, contexto: ContextoLocal
) -> dict:
    with repositorio.transacao() as conexao:
        parametros = {"id": selectedId, "org": contexto.organizationId}
        origens = repositorio.consultar(
            conexao,
            "SELECT empresaId FROM crm_origem_selecionada WHERE selectedId=:id AND organizationId=:org",
            parametros,
        )
        if origens:
            return {"empresaId": origens[0]["empresaId"], "jaVinculado": True}
        selecionados = repositorio.consultar(
            conexao, "SELECT * FROM selectedlead WHERE id=:id", parametros
        )
        if not selecionados:
            raise ErroCrm("Lead selecionado não encontrado.", "NAO_ENCONTRADO", 404)
        selecionado = selecionados[0]
        if empresaId:
            repositorio.buscarEmpresa(conexao, empresaId, contexto)
        else:
            telefone = selecionado["phone"] or ""
            if telefone:
                try:
                    normalizado = normalizarTelefone(telefone)
                except ValueError as erro:
                    raise ErroCrm(
                        "Corrija o telefone do lead antes de adicioná-lo ao CRM."
                    ) from erro
                candidatas = repositorio.consultar(
                    conexao,
                    "SELECT DISTINCT e.id,e.nome,e.cidade,e.uf FROM crm_empresa e JOIN crm_contato c ON c.empresaId=e.id WHERE e.organizationId=:org AND c.organizationId=:org AND c.telefoneNormalizado=:telefone",
                    {"org": contexto.organizationId, "telefone": normalizado},
                )
                if candidatas:
                    raise ErroCrm(
                        "Telefone já cadastrado. Confirme a vinculação a uma empresa existente.",
                        "EMPRESA_DUPLICADA",
                        409,
                        candidatas,
                    )
            try:
                entrada = EmpresaEntrada(
                    nome=selecionado["company_name"],
                    telefone=telefone,
                    segmento=selecionado["segmento"] or selecionado["category"] or "",
                    cidade=selecionado["city"] or "",
                    uf=selecionado["state"] or "",
                    site=selecionado["website"] or "",
                    urlMaps=selecionado["maps_url"] or "",
                    responsavel=selecionado["prospectador"] or contexto.nome,
                )
            except ValueError as erro:
                raise ErroCrm(
                    "O lead contém dados inválidos. Corrija o cadastro ou vincule a uma empresa existente."
                ) from erro
            empresaId = adicionarEmpresa(conexao, entrada, contexto)["id"]
        repositorio.inserir(
            conexao,
            "crm_origem_selecionada",
            {
                "selectedId": selectedId,
                "empresaId": empresaId,
                "organizationId": contexto.organizationId,
                "nomeOriginal": selecionado["company_name"],
                "createdBy": contexto.actorId,
                "createdAt": agoraUtc(),
            },
        )
        registrarEvento(
            conexao,
            empresaId,
            "origem",
            f"Lead selecionado #{selectedId} vinculado ao CRM, sem registrar abordagem.",
            contexto,
        )
        return {"empresaId": empresaId, "jaVinculado": False}
