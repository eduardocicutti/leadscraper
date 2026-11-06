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
  arquivada: boolean;
  version: number;
  qualificacaoSituacao?: string;
  ultimoContatoEm?: string | null;
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
export type EmpresaEntrada = Omit<Empresa, "id" | "version" | "arquivada"> & {
  telefone: string;
};
export type AtividadeEntrada = Omit<
  Atividade,
  "id" | "empresaId" | "empresaNome" | "version"
>;

function cabecalhos() {
  return {
    "X-Operador-Local":
      useAppStore.getState().prospectador.trim() || "Operador local",
  };
}

export async function consultarCrm<T>(
  caminho: string,
  parametros?: Record<string, string | number | boolean>,
): Promise<T> {
  const resposta = await api.get<T>(`/api/v1/crm/${caminho}`, {
    params: parametros,
    headers: cabecalhos(),
  });
  return resposta.data;
}

export async function salvarCrm<T>(
  caminho: string,
  valores: unknown,
  editar = false,
): Promise<T> {
  const resposta = await api.request<T>({
    method: editar ? "PUT" : "POST",
    url: `/api/v1/crm/${caminho}`,
    data: valores,
    headers: cabecalhos(),
  });
  return resposta.data;
}

export function mensagemErroCrm(erro: unknown): string {
  if (!axios.isAxiosError(erro)) return "Não foi possível concluir a operação.";
  const resposta: unknown = erro.response?.data;
  if (typeof resposta !== "object" || resposta === null)
    return "Não foi possível acessar o CRM. Verifique o agente local atualizado.";
  const campos = resposta as Record<string, unknown>;
  const detalhes = Array.isArray(campos.fieldErrors)
    ? campos.fieldErrors.flatMap((item: unknown) => {
        if (typeof item !== "object" || item === null) return [];
        const campo = item as Record<string, unknown>;
        return typeof campo.message === "string"
          ? [`${String(campo.field || "Dados")}: ${campo.message}`]
          : [];
      })
    : [];
  return [
    typeof campos.message === "string"
      ? campos.message
      : "Não foi possível concluir a operação.",
    ...detalhes,
  ].join(" ");
}
