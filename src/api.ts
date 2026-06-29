import axios from "axios";

export interface Lead {
  nome: string;
  categoria: string;
  nota: number | null;
  avaliacoes: number | null;
  endereco: string | null;
  telefone: string | null;
  is_whatsapp: boolean;
  whatsapp_link: string;
  site: string | null;
  url_maps: string;
  porte: string;
  classificacao: string;
  score: number;
  cidade: string;
  estado: string;
  prospectador: string;
}

export interface SearchRequest {
  segmento: string;
  cidade: string;
  estado: string;
  max_results: number;
  prospectador: string;
}

export interface StatusResponse {
  status: "pending" | "running" | "done" | "error";
  progress: number;
  total: number;
  log: string;
  leads_count: number;
  leads: Lead[];
}

export interface HistoryRecord {
  id: number;
  keyword: string;
  city: string;
  state: string;
  status: "running" | "done" | "error";
  leads_found: number;
  prospectador: string;
  created_at: string;
}

export const api = axios.create({ baseURL: "http://127.0.0.1:8000" });
