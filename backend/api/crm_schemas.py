import re
from datetime import date
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StrictBool,
    field_validator,
    model_validator,
)

from backend.domain.crm import MAXIMO_INTEIRO_SQLITE, normalizarTelefone, validarCnpj


def validarDataIso(valor: object) -> str | date:
    if type(valor) is date:
        return valor
    if isinstance(valor, str) and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", valor):
        return valor
    raise ValueError("Informe a data no formato AAAA-MM-DD.")


DataIso = Annotated[date, BeforeValidator(validarDataIso)]
VersaoEditavel = Annotated[int, Field(ge=1, le=MAXIMO_INTEIRO_SQLITE - 1, strict=True)]


class EntradaCrm(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class EmpresaEntrada(EntradaCrm):
    nome: str = Field(min_length=2, max_length=200)
    cnpj: str = Field(default="", max_length=30)
    segmento: str = Field(default="", max_length=120)
    cidade: str = Field(default="", max_length=120)
    uf: str = ""
    site: str = Field(default="", max_length=1000)
    telefone: str = Field(default="", max_length=40)
    confirmarTelefoneCompartilhado: StrictBool = False
    urlMaps: str = Field(default="", max_length=2000)
    responsavel: str = Field(min_length=1, max_length=100)

    @field_validator("cnpj")
    @classmethod
    def conferirCnpj(cls, valor: str) -> str:
        return validarCnpj(valor) or ""

    @field_validator("telefone")
    @classmethod
    def conferirTelefone(cls, valor: str) -> str:
        normalizarTelefone(valor)
        return valor

    @field_validator("uf")
    @classmethod
    def conferirUf(cls, valor: str) -> str:
        valor = valor.upper()
        if (
            valor
            and valor
            not in "AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split()
        ):
            raise ValueError("UF inválida.")
        return valor

    @field_validator("site", "urlMaps")
    @classmethod
    def conferirUrl(cls, valor: str) -> str:
        if valor and not re.match(
            r"^https?://[^\s/]+(?:/[^\s]*)?$", valor, re.IGNORECASE
        ):
            raise ValueError(
                "Informe endereço completo começando por https:// ou http://."
            )
        return valor


class EmpresaEdicao(EmpresaEntrada):
    version: VersaoEditavel
    arquivada: StrictBool = False


class ContatoEntrada(EntradaCrm):
    nome: str = Field(min_length=1, max_length=150)
    cargo: str = Field(default="", max_length=120)
    telefone: str = Field(default="", max_length=40)
    email: str = Field(default="", max_length=200)

    @field_validator("telefone")
    @classmethod
    def conferirTelefone(cls, valor: str) -> str:
        normalizarTelefone(valor)
        return valor

    @field_validator("email")
    @classmethod
    def conferirEmail(cls, valor: str) -> str:
        if valor and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", valor):
            raise ValueError("E-mail inválido.")
        return valor


class ContatoEdicao(ContatoEntrada):
    version: VersaoEditavel


class AtividadeEntrada(EntradaCrm):
    titulo: str = Field(min_length=2, max_length=200)
    tipo: Literal["ligacao", "whatsapp", "email", "reuniao", "tarefa", "lembrete"] = (
        "tarefa"
    )
    situacao: Literal["pendente", "concluida", "cancelada"] = "pendente"
    descricao: str = Field(default="", max_length=4000)
    resultado: str = Field(default="", max_length=2000)
    responsavel: str = Field(min_length=1, max_length=100)
    prazoData: DataIso | None = None

    @model_validator(mode="after")
    def conferirResultado(self):
        if self.situacao == "concluida" and not self.resultado:
            raise ValueError("Informe o resultado da atividade concluída.")
        return self


class AtividadeEdicao(AtividadeEntrada):
    version: VersaoEditavel


class QualificacaoEntrada(EntradaCrm):
    situacao: Literal["novo", "analise", "qualificado", "desqualificado"]
    motivo: str = Field(default="", max_length=1000)
    version: VersaoEditavel

    @model_validator(mode="after")
    def conferirMotivo(self):
        if self.situacao == "desqualificado" and not self.motivo:
            raise ValueError("Informe o motivo da desqualificação.")
        return self


class ConversaoEntrada(EntradaCrm):
    empresaId: str | None = Field(default=None, min_length=1, max_length=64)
    confirmarTelefoneCompartilhado: StrictBool = False
