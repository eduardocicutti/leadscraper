import axios from "axios";

export interface Lead {
  id?: number | null;
  history_id?: number | null;
  source_history_id?: number | null;
  source_lead_id?: number | null;
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

export interface SelectedLead extends Lead {
  id: number;
  segmento: string;
  notes: string;
  custom_message: string;
  last_message_updated_at: string | null;
  selected_at: string;
  updated_at: string;
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

export interface HistoryDetail extends HistoryRecord {
  leads: Lead[];
}

export interface MessageTemplateResponse {
  template: string;
  segmento?: string;
  leads?: SelectedLead[];
}

export interface SelectedLeadFilters {
  segmento: string;
  cidade: string;
  estado: string;
  temperatura: string;
  com_whatsapp: string;
  com_site: string;
  prospectador: string;
}

export interface ImportSelectedLeadsResponse {
  imported_count: number;
  skipped_count: number;
  rows_read: number;
  columns_detected: string[];
  imported: SelectedLead[];
  skipped: Array<{
    row: number;
    reason: string;
    nome: string;
    existing_id?: number;
    existing_nome?: string;
  }>;
}

export interface DiagnosticsResponse {
  ok: boolean;
  db_ready: boolean;
  db_path: string;
  db_exists: boolean;
  db_size_bytes: number;
  wal_size_bytes: number;
  journal_mode: string;
  synchronous: number | string;
  integrity_check: string;
  db_path_source: string;
  counts: {
    history: number;
    leads: number;
    selected_leads: number;
    settings: number;
  };
}

export const api = axios.create({ baseURL: "http://127.0.0.1:8000" });
