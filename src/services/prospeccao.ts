import { api } from "../api";
import { idLegadoValido } from "../utils/idLegadoValido";

export interface Municipio {
  codigo: number;
  nome: string;
  uf: string;
}

interface CatalogoMunicipios {
  itens: Municipio[];
  versao: string;
}

export interface ParametrosProspeccao {
  segmento: string;
  estado: string;
  municipioCodigo: number;
  max_results: number;
  prospectador: string;
}

function ehRegistro(valor: unknown): valor is Record<string, unknown> {
  return typeof valor === "object" && valor !== null && !Array.isArray(valor);
}

function municipioDaUf(valor: unknown, uf: string): valor is Municipio {
  return (
    ehRegistro(valor) &&
    idLegadoValido(valor.codigo) &&
    String(valor.codigo).length === 7 &&
    typeof valor.nome === "string" &&
    valor.nome.trim().length > 0 &&
    valor.uf === uf
  );
}

export async function consultarMunicipios(
  uf: string,
  signal?: AbortSignal,
): Promise<CatalogoMunicipios> {
  const { data: resposta } = await api.get<unknown>("/api/v1/localidades/municipios", {
    params: { uf },
    signal,
  });
  if (!ehRegistro(resposta) || typeof resposta.versao !== "string") {
    throw new Error("Catálogo de municípios inválido.");
  }
  const itens: unknown = resposta.itens;
  if (!Array.isArray(itens) || !itens.every((item) => municipioDaUf(item, uf))) {
    throw new Error("Catálogo de municípios inválido.");
  }
  return { itens, versao: resposta.versao };
}

export async function atualizarCatalogo(): Promise<void> {
  await api.post("/api/v1/localidades/atualizar");
}

export async function criarProspeccao(parametros: ParametrosProspeccao): Promise<string> {
  const { data: resposta } = await api.post<unknown>("/api/v1/prospeccoes", parametros);
  if (!ehRegistro(resposta) || typeof resposta.job_id !== "string" || !/^\d+$/.test(resposta.job_id)) {
    throw new Error("Identificador da prospecção inválido.");
  }
  return resposta.job_id;
}
