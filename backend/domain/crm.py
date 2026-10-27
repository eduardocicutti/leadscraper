import re
import unicodedata
from dataclasses import dataclass
from uuid import UUID, uuid5


ORGANIZACAO_LOCAL = "00000000-0000-4000-8000-000000000001"


@dataclass(frozen=True)
class ContextoLocal:
    nome: str
    organizationId: str = ORGANIZACAO_LOCAL

    @property
    def actorId(self) -> str:
        return str(uuid5(UUID(self.organizationId), normalizarTexto(self.nome)))


class ErroCrm(Exception):
    def __init__(
        self,
        mensagem: str,
        codigo: str = "INVALIDO",
        status: int = 400,
        detalhes: list | None = None,
    ):
        self.mensagem = mensagem
        self.codigo = codigo
        self.status = status
        self.detalhes = detalhes or []


def normalizarTexto(valor: str) -> str:
    texto = unicodedata.normalize("NFKD", valor.casefold())
    return " ".join(
        "".join(
            letra if letra.isalnum() else " "
            for letra in texto
            if not unicodedata.combining(letra)
        ).split()
    )


def normalizarTelefone(valor: str) -> str:
    numeros = re.sub(r"\D", "", valor)
    if not numeros:
        if valor.strip():
            raise ValueError("Informe um telefone válido com DDD.")
        return ""
    if len(numeros) in (10, 11):
        return "55" + numeros
    if len(numeros) in (12, 13) and numeros.startswith("55"):
        return numeros
    raise ValueError("Informe telefone brasileiro com DDD, ou código 55 e DDD.")


def validarCnpj(valor: str) -> str | None:
    numeros = re.sub(r"\D", "", valor)
    if not numeros:
        if valor.strip():
            raise ValueError("CNPJ inválido.")
        return None
    if len(numeros) != 14 or len(set(numeros)) == 1:
        raise ValueError("CNPJ inválido.")
    for tamanho in (12, 13):
        pesos = list(range(tamanho - 7, 1, -1)) + list(range(9, 1, -1))
        resto = (
            sum(int(numero) * peso for numero, peso in zip(numeros[:tamanho], pesos))
            % 11
        )
        if int(numeros[tamanho]) != (0 if resto < 2 else 11 - resto):
            raise ValueError("Dígitos verificadores do CNPJ inválidos.")
    return numeros
