import axios from "axios";
import { api } from "../api";
import { useAppStore } from "../store";

export interface Empresa {
  id: string;
  nome: string;
  cnpj: string | null;
  segmento: string;
  cidade: string;
  uf: string;
  site: string;
  urlMaps: string;
  responsavel: string;
  arquivada: boolean | 0 | 1;
  version: number;
  qualificacaoSituacao?: Qualificacao["situacao"] | null;
  ultimoContatoEm?: string | null;
}

export interface EmpresaCandidata {
  id: string;
  nome: string;
  cidade: string;
  uf: string;
  somenteTelefone: boolean;
}

export interface Contato {
  id: string;
  empresaId: string;
  empresaNome?: string;
  nome: string;
  telefone: string;
  email: string;
  cargo: string;
  version: number;
}

export interface Atividade {
  id: string;
  empresaId: string;
  empresaNome?: string;
  titulo: string;
  tipo: "ligacao" | "whatsapp" | "email" | "reuniao" | "tarefa" | "lembrete";
  situacao: "pendente" | "concluida" | "cancelada";
  descricao: string;
  resultado: string;
  responsavel: string;
  prazoData: string | null;
  version: number;
}

export interface DetalheEmpresa extends Empresa {
  paginacao: Record<
    "contatos" | "atividades" | "eventos",
    { pagina: number; total: number; tamanho: number }
  >;
  qualificacao: Qualificacao | null;
  contatos: Contato[];
  atividades: Atividade[];
  eventos: {
    id: string;
    descricao: string;
    autorNome: string;
    createdAt: string;
  }[];
}

export interface Qualificacao {
  id: string;
  situacao: "novo" | "analise" | "qualificado" | "desqualificado";
  motivo: string;
  version: number;
}

export interface PaginaCrm<T> {
  itens: T[];
  total: number;
  pagina: number;
  tamanho: number;
}
export type EmpresaEntrada = Pick<
  Empresa,
  "nome" | "cnpj" | "segmento" | "cidade" | "uf" | "site" | "urlMaps" | "responsavel"
> & {
  telefone: string;
};
export type AtividadeEntrada = Omit<
  Atividade,
  "id" | "empresaId" | "empresaNome" | "version"
>;

type Validador<T> = (valor: unknown) => valor is T;

function ehRegistro(valor: unknown): valor is Record<string, unknown> {
  return typeof valor === "object" && valor !== null && !Array.isArray(valor);
}

function temTextos(registro: Record<string, unknown>, campos: string[]): boolean {
  return campos.every((campo) => typeof registro[campo] === "string");
}

function ehInteiro(valor: unknown, minimo: number): valor is number {
  return typeof valor === "number" && Number.isSafeInteger(valor) && valor >= minimo;
}

function ehIdCrm(valor: unknown): valor is string {
  return typeof valor === "string" &&
    /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(valor);
}

function ehSituacaoQualificacao(valor: unknown): valor is Qualificacao["situacao"] {
  return valor === "novo" || valor === "analise" ||
    valor === "qualificado" || valor === "desqualificado";
}

export function ehEmpresa(valor: unknown): valor is Empresa {
  return ehRegistro(valor) &&
    ehIdCrm(valor.id) &&
    ehInteiro(valor.version, 1) &&
    temTextos(valor, ["nome", "segmento", "cidade", "uf", "site", "urlMaps", "responsavel"]) &&
    (valor.cnpj === null || typeof valor.cnpj === "string") &&
    (typeof valor.arquivada === "boolean" || valor.arquivada === 0 || valor.arquivada === 1) &&
    (valor.qualificacaoSituacao == null || ehSituacaoQualificacao(valor.qualificacaoSituacao)) &&
    (valor.ultimoContatoEm == null || typeof valor.ultimoContatoEm === "string");
}

function ehRegistroVinculado(valor: unknown): valor is Record<string, unknown> {
  return ehRegistro(valor) && ehIdCrm(valor.id) && ehIdCrm(valor.empresaId) &&
    ehInteiro(valor.version, 1) &&
    (valor.empresaNome === undefined || typeof valor.empresaNome === "string");
}

export function ehContato(valor: unknown): valor is Contato {
  return ehRegistroVinculado(valor) && temTextos(valor, ["nome", "telefone", "email", "cargo"]);
}

export function ehAtividade(valor: unknown): valor is Atividade {
  return ehRegistroVinculado(valor) &&
    temTextos(valor, ["titulo", "descricao", "resultado", "responsavel"]) &&
    (valor.prazoData === null ||
      (typeof valor.prazoData === "string" && /^\d{4}-\d{2}-\d{2}$/.test(valor.prazoData))) &&
    (valor.tipo === "ligacao" || valor.tipo === "whatsapp" || valor.tipo === "email" ||
      valor.tipo === "reuniao" || valor.tipo === "tarefa" || valor.tipo === "lembrete") &&
    (valor.situacao === "pendente" || valor.situacao === "concluida" || valor.situacao === "cancelada");
}

export function ehQualificacao(valor: unknown): valor is Qualificacao {
  return ehRegistro(valor) && ehIdCrm(valor.id) && ehInteiro(valor.version, 1) &&
    ehSituacaoQualificacao(valor.situacao) && typeof valor.motivo === "string";
}

function ehEvento(valor: unknown): valor is DetalheEmpresa["eventos"][number] {
  return ehRegistro(valor) && ehIdCrm(valor.id) &&
    temTextos(valor, ["descricao", "autorNome", "createdAt"]);
}

function ehResumoPaginacao(valor: unknown): boolean {
  return ehRegistro(valor) && ehInteiro(valor.pagina, 1) && ehInteiro(valor.total, 0) &&
    ehInteiro(valor.tamanho, 1) && valor.tamanho <= 100;
}

function ehColecao<T>(valor: unknown, validarItem: Validador<T>): valor is T[] {
  return Array.isArray(valor) && valor.every(validarItem);
}

export function validarPaginaCrm<T>(validarItem: Validador<T>): Validador<PaginaCrm<T>> {
  return (valor): valor is PaginaCrm<T> =>
    ehRegistro(valor) && ehResumoPaginacao(valor) && ehColecao(valor.itens, validarItem);
}

export function ehDetalheEmpresa(valor: unknown): valor is DetalheEmpresa {
  if (!ehRegistro(valor) || !ehEmpresa(valor)) return false;
  const paginacao = valor.paginacao;
  return ehRegistro(paginacao) &&
    ehResumoPaginacao(paginacao.contatos) &&
    ehResumoPaginacao(paginacao.atividades) &&
    ehResumoPaginacao(paginacao.eventos) &&
    (valor.qualificacao === null || ehQualificacao(valor.qualificacao)) &&
    ehColecao(valor.contatos, ehContato) &&
    ehColecao(valor.atividades, ehAtividade) &&
    ehColecao(valor.eventos, ehEvento);
}

export function ehConversao(valor: unknown): valor is { empresaId: string; jaVinculado: boolean } {
  return ehRegistro(valor) && ehIdCrm(valor.empresaId) && typeof valor.jaVinculado === "boolean";
}

class RespostaInvalidaCrm extends Error {
  constructor() {
    super("O agente local retornou dados inválidos. Verifique se ele está atualizado.");
  }
}

function validarResposta<T>(valor: unknown, validar: Validador<T>): T {
  if (!validar(valor)) throw new RespostaInvalidaCrm();
  return valor;
}

function cabecalhos() {
  return {
    "X-Operador-Local":
      useAppStore.getState().prospectador.trim() || "Operador local",
  };
}

export async function consultarCrm<T>(
  caminho: string,
  validar: Validador<T>,
  parametros?: Record<string, string | number | boolean>,
): Promise<T> {
  const resposta = await api.get<unknown>(`/api/v1/crm/${caminho}`, {
    params: parametros,
    headers: cabecalhos(),
  });
  return validarResposta(resposta.data, validar);
}

export async function salvarCrm<T>(
  caminho: string,
  validar: Validador<T>,
  valores: unknown,
  editar = false,
): Promise<T> {
  const resposta = await api.request<unknown>({
    method: editar ? "PUT" : "POST",
    url: `/api/v1/crm/${caminho}`,
    data: valores,
    headers: cabecalhos(),
  });
  return validarResposta(resposta.data, validar);
}

export function mensagemErroCrm(erro: unknown): string {
  if (erro instanceof RespostaInvalidaCrm) return erro.message;
  if (!axios.isAxiosError(erro)) return "Não foi possível concluir a operação.";
  const resposta: unknown = erro.response?.data;
  if (!ehRegistro(resposta))
    return "Não foi possível acessar o CRM. Verifique o agente local atualizado.";
  const detalhes = Array.isArray(resposta.fieldErrors)
    ? resposta.fieldErrors.flatMap((item: unknown) => {
        if (!ehRegistro(item)) return [];
        const campo = typeof item.field === "string" && item.field ? item.field : "Dados";
        return typeof item.message === "string"
          ? [`${campo}: ${item.message}`]
          : [];
      })
    : [];
  return [
    typeof resposta.message === "string"
      ? resposta.message
      : "Não foi possível concluir a operação.",
    ...detalhes,
  ].join(" ");
}

export function empresasCandidatas(erro: unknown): EmpresaCandidata[] {
  if (!axios.isAxiosError(erro) || erro.response?.status !== 409) return [];
  const resposta: unknown = erro.response.data;
  if (
    !ehRegistro(resposta) ||
    !Array.isArray(resposta.candidatas)
  )
    return [];

  return resposta.candidatas.flatMap((item: unknown) => {
    if (
      !ehRegistro(item) ||
      !ehIdCrm(item.id) ||
      typeof item.nome !== "string"
    )
      return [];
    return [
      {
        id: item.id,
        nome: item.nome,
        cidade: typeof item.cidade === "string" ? item.cidade : "",
        uf: typeof item.uf === "string" ? item.uf : "",
        somenteTelefone: item.somenteTelefone === true,
      },
    ];
  });
}

export function rotuloEmpresaCandidata(empresa: EmpresaCandidata): string {
  const local = [empresa.cidade, empresa.uf].filter(Boolean).join(" / ");
  return local ? `${empresa.nome} (${local})` : empresa.nome;
}
