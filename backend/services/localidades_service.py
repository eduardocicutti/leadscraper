import json
import os
from dataclasses import asdict, dataclass
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import urlopen

from backend.domain.crm import normalizarTexto


FONTE_MUNICIPIOS = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios?view=nivelado"
ARQUIVO_EMBUTIDO = Path(__file__).resolve().parents[1] / "data" / "municipios-ibge.json"
UF_POR_CODIGO = {
    11: "RO", 12: "AC", 13: "AM", 14: "RR", 15: "PA", 16: "AP", 17: "TO",
    21: "MA", 22: "PI", 23: "CE", 24: "RN", 25: "PB", 26: "PE", 27: "AL", 28: "SE", 29: "BA",
    31: "MG", 32: "ES", 33: "RJ", 35: "SP",
    41: "PR", 42: "SC", 43: "RS", 50: "MS", 51: "MT", 52: "GO", 53: "DF",
}
UFS = frozenset(UF_POR_CODIGO.values())
LIMITE_RESPOSTA_BYTES = 8 * 1024 * 1024
MINIMO_MUNICIPIOS = 5500


@dataclass(frozen=True)
class Municipio:
    codigo: int
    nome: str
    uf: str


@dataclass(frozen=True)
class CatalogoMunicipios:
    municipios: tuple[Municipio, ...]
    versao: str

    def filtrar(self, uf: str, busca: str) -> list[Municipio]:
        termo = normalizarTexto(busca)
        return [
            municipio
            for municipio in self.municipios
            if municipio.uf == uf and termo in normalizarTexto(municipio.nome)
        ]

    def localizar(self, codigo: int) -> Municipio | None:
        return next(
            (municipio for municipio in self.municipios if municipio.codigo == codigo),
            None,
        )


def montarCatalogo(registros: object) -> CatalogoMunicipios:
    if not isinstance(registros, list) or len(registros) < MINIMO_MUNICIPIOS:
        raise ValueError("Catálogo municipal incompleto.")
    municipios = []
    codigos: set[int] = set()
    unidadesFederativas: set[str] = set()
    for registro in registros:
        if not isinstance(registro, dict):
            raise ValueError("Registro de município inválido.")
        codigo = registro.get("codigo")
        nome = registro.get("nome")
        uf = registro.get("uf")
        if (
            type(codigo) is not int
            or not 1_000_000 <= codigo <= 9_999_999
            or codigo in codigos
            or not isinstance(nome, str)
            or not nome.strip()
            or "\ufffd" in nome
            or not isinstance(uf, str)
            or UF_POR_CODIGO.get(codigo // 100_000) != uf
        ):
            raise ValueError("Registro de município inválido ou repetido.")
        codigos.add(codigo)
        unidadesFederativas.add(uf)
        municipios.append(Municipio(codigo, nome.strip(), uf))
    if unidadesFederativas != UFS:
        raise ValueError("O catálogo não contém todas as unidades federativas.")
    municipios.sort(key=lambda municipio: (normalizarTexto(municipio.nome), municipio.codigo))
    itens = [asdict(municipio) for municipio in municipios]
    versao = sha256(json.dumps(itens, ensure_ascii=False).encode("utf-8")).hexdigest()
    return CatalogoMunicipios(tuple(municipios), f"ibge-{versao}")


def serializarCatalogo(catalogo: CatalogoMunicipios) -> str:
    itens = [
        json.dumps(asdict(municipio), ensure_ascii=False, separators=(",", ":"))
        for municipio in catalogo.municipios
    ]
    return "[\n" + ",\n".join(itens) + "\n]\n"


def caminhoCache() -> Path:
    banco = Path(os.getenv("DB_PATH", "banco.db")).expanduser().resolve()
    return banco.with_suffix(".municipios-ibge.json")


@lru_cache(maxsize=1)
def carregarCatalogoEmbutido() -> CatalogoMunicipios:
    return montarCatalogo(json.loads(ARQUIVO_EMBUTIDO.read_bytes()))


@lru_cache(maxsize=4)
def carregarCache(caminho: Path, _horarioModificacao: int) -> CatalogoMunicipios:
    return montarCatalogo(json.loads(caminho.read_bytes()))


def obterCatalogo() -> CatalogoMunicipios:
    caminho = caminhoCache()
    try:
        return carregarCache(caminho, caminho.stat().st_mtime_ns)
    except (OSError, ValueError):
        return carregarCatalogoEmbutido()


def interpretarCatalogoIbge(conteudo: bytes) -> CatalogoMunicipios:
    registros = json.loads(conteudo)
    if not isinstance(registros, list) or any(not isinstance(item, dict) for item in registros):
        raise ValueError("Formato do catálogo do IBGE inválido.")
    return montarCatalogo([
        {"codigo": item.get("municipio-id"), "nome": item.get("municipio-nome"), "uf": item.get("UF-sigla")}
        for item in registros
    ])


def atualizarCatalogo() -> CatalogoMunicipios:
    with urlopen(FONTE_MUNICIPIOS, timeout=10) as resposta:
        conteudo = resposta.read(LIMITE_RESPOSTA_BYTES + 1)
    if len(conteudo) > LIMITE_RESPOSTA_BYTES:
        raise ValueError("Catálogo do IBGE acima do limite de tamanho esperado.")
    catalogo = interpretarCatalogoIbge(conteudo)
    caminho = caminhoCache()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=caminho.parent, delete=False) as temporario:
        arquivo = Path(temporario.name)
    try:
        arquivo.write_text(serializarCatalogo(catalogo), encoding="utf-8")
        arquivo.replace(caminho)
    finally:
        arquivo.unlink(missing_ok=True)
    return catalogo
