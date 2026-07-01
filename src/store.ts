import { create } from "zustand";
import type { Lead, SearchRequest, StatusResponse } from "./api";

type Status = "idle" | "pending" | "running" | "done" | "error";
type View = "search" | "selected" | "history";

interface AppStore {
  activeView: View;
  jobId: string | null;
  refreshJobId: string | null;
  status: Status;
  progress: number;
  total: number;
  log: string;
  leads: Lead[];
  selectedLeadKeys: string[];
  searchParams: Omit<SearchRequest, "max_results"> | null;
  maxResults: number;
  prospectador: string;
  historyOpen: boolean;
  setActiveView: (view: View) => void;
  setJob: (jobId: string, params: AppStore["searchParams"], maxResults: number) => void;
  setRefreshJob: (jobId: string) => void;
  updateStatus: (data: StatusResponse) => void;
  openSavedLeads: (
    params: AppStore["searchParams"],
    leads: Lead[],
    historyId?: number,
  ) => void;
  toggleLeadSelection: (key: string) => void;
  clearLeadSelection: () => void;
  setProspectador: (prospectador: string) => void;
  setHistoryOpen: (open: boolean) => void;
  reset: () => void;
}

const initialState = {
  activeView: "search" as View,
  jobId: null,
  refreshJobId: null,
  status: "idle" as Status,
  progress: 0,
  total: 0,
  log: "",
  leads: [],
  selectedLeadKeys: [],
  searchParams: null,
  maxResults: 30,
  prospectador: "Eduardo",
  historyOpen: false,
};

export const leadKey = (lead: Lead) =>
  lead.url_maps || lead.telefone || `${lead.nome}-${lead.cidade}-${lead.estado}`;

export const useAppStore = create<AppStore>((set) => ({
  ...initialState,
  setActiveView: (activeView) => set({ activeView, historyOpen: false }),
  setJob: (jobId, params, maxResults) =>
    set({
      activeView: "search",
      jobId,
      refreshJobId: null,
      searchParams: params,
      maxResults,
      status: "pending",
      progress: 0,
      total: 0,
      log: "Extraindo...",
      leads: [],
      selectedLeadKeys: [],
    }),
  setRefreshJob: (refreshJobId) =>
    set({
      activeView: "search",
      refreshJobId,
      jobId: null,
      status: "pending",
      progress: 0,
      total: 0,
      log: "Iniciando releitura...",
      leads: [],
    }),
  updateStatus: (data) =>
    set({
      status: data.status,
      progress: data.progress,
      total: data.total,
      log: data.log,
      leads: data.leads,
    }),
  openSavedLeads: (params, leads, historyId) =>
    set({
      activeView: "search",
      jobId: historyId ? `history:${historyId}` : null,
      refreshJobId: null,
      searchParams: params,
      maxResults: leads.length,
      status: "done",
      progress: leads.length,
      total: leads.length,
      log: `Histórico reaberto com ${leads.length} leads.`,
      leads,
      selectedLeadKeys: [],
    }),
  toggleLeadSelection: (key) =>
    set((state) => ({
      selectedLeadKeys: state.selectedLeadKeys.includes(key)
        ? state.selectedLeadKeys.filter((item) => item !== key)
        : [...state.selectedLeadKeys, key],
    })),
  clearLeadSelection: () => set({ selectedLeadKeys: [] }),
  setProspectador: (prospectador) => set({ prospectador }),
  setHistoryOpen: (historyOpen) => set({ historyOpen, activeView: "search" }),
  reset: () => set(initialState),
}));
