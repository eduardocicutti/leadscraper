import { create } from "zustand";
import type { Lead, SearchRequest, StatusResponse } from "./api";

type Status = "idle" | "pending" | "running" | "done" | "error";

interface AppStore {
  jobId: string | null;
  status: Status;
  progress: number;
  total: number;
  log: string;
  leads: Lead[];
  searchParams: Omit<SearchRequest, "max_results"> | null;
  maxResults: number;
  prospectador: string;
  historyOpen: boolean;
  setJob: (jobId: string, params: AppStore["searchParams"], maxResults: number) => void;
  updateStatus: (data: StatusResponse) => void;
  setProspectador: (prospectador: string) => void;
  setHistoryOpen: (open: boolean) => void;
  reset: () => void;
}

const initialState = {
  jobId: null,
  status: "idle" as Status,
  progress: 0,
  total: 0,
  log: "",
  leads: [],
  searchParams: null,
  maxResults: 30,
  prospectador: "Eduardo",
  historyOpen: false,
};

export const useAppStore = create<AppStore>((set) => ({
  ...initialState,
  setJob: (jobId, params, maxResults) =>
    set({
      jobId,
      searchParams: params,
      maxResults,
      status: "pending",
      progress: 0,
      total: 0,
      log: "Extraindo...",
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
  setProspectador: (prospectador) => set({ prospectador }),
  setHistoryOpen: (historyOpen) => set({ historyOpen }),
  reset: () => set(initialState),
}));
