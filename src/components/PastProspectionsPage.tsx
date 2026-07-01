import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, RefreshCw, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";
import { api, type HistoryRecord } from "../api";
import { useAppStore } from "../store";

const labelClass =
  "text-[10px] font-semibold text-[#4a5568] uppercase tracking-[0.08em]";
const inputClass =
  "h-8 bg-[#0b1220] border border-[#1e2d45] rounded-md px-3 text-[13px] text-[#e8edf5] font-['JetBrains_Mono'] placeholder:text-[#4a5568] focus:border-[#2563eb] focus:ring-0 outline-none transition-colors duration-100";
const headerClass =
  "sticky top-0 bg-[#0c1118] text-[10px] font-semibold text-[#4a5568] uppercase tracking-[0.1em] border-b border-[#1e2d45] px-3 py-2 text-left";
const cellClass =
  "text-[13px] text-[#8896ac] px-3 py-2.5 font-['JetBrains_Mono'] whitespace-nowrap";

function formatDate(value: string) {
  return new Date(value).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function PastProspectionsPage() {
  const queryClient = useQueryClient();
  const openSavedLeads = useAppStore((state) => state.openSavedLeads);
  const setRefreshJob = useAppStore((state) => state.setRefreshJob);

  const [segmento, setSegmento] = useState("");
  const [cidade, setCidade] = useState("");
  const [estado, setEstado] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  const { data = [], isLoading } = useQuery({
    queryKey: ["history"],
    queryFn: () => api.get<HistoryRecord[]>("/history").then((r) => r.data),
    refetchInterval: 5000,
  });

  const filtered = useMemo(() => {
    return data.filter((item) => {
      if (segmento && !item.keyword.toLowerCase().includes(segmento.toLowerCase())) {
        return false;
      }
      if (cidade && !item.city.toLowerCase().includes(cidade.toLowerCase())) {
        return false;
      }
      if (estado && item.state !== estado) {
        return false;
      }
      if (statusFilter && item.status !== statusFilter) {
        return false;
      }
      return true;
    });
  }, [data, segmento, cidade, estado, statusFilter]);

  const estados = useMemo(
    () => [...new Set(data.map((item) => item.state).filter(Boolean))].sort(),
    [data],
  );

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/history/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["history"] });
      setSelectedIds([]);
    },
  });

  async function handleOpen(item: HistoryRecord) {
    const response = await api.get(`/history/${item.id}`);
    openSavedLeads(
      {
        segmento: response.data.keyword,
        cidade: response.data.city,
        estado: response.data.state,
        prospectador: response.data.prospectador,
      },
      response.data.leads,
      item.id,
    );
  }

  async function handleDownload(item: HistoryRecord) {
    const response = await api.get(`/history/${item.id}/download`, {
      responseType: "blob",
    });
    const url = URL.createObjectURL(response.data);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `leads_${item.keyword}_${item.city}.xlsx`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  async function handleRefresh(item: HistoryRecord) {
    const response = await api.post<{ job_id: string }>(`/history/${item.id}/refresh`);
    setRefreshJob(response.data.job_id);
  }

  async function handleBatchRefresh() {
    if (selectedIds.length === 0) return;
    const response = await api.post<{ job_id: string }>("/history/refresh-batch", {
      history_ids: selectedIds,
    });
    setRefreshJob(response.data.job_id);
  }

  function toggleSelect(id: number) {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id],
    );
  }

  return (
    <div className="flex-1 min-h-0 p-6 flex flex-col gap-4 overflow-hidden">
      <section className="border border-[#1e2d45] rounded-md bg-[#0f1623] px-4 py-3 flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-1 w-40">
          <span className={labelClass}>Segmento</span>
          <input
            value={segmento}
            onChange={(e) => setSegmento(e.target.value)}
            placeholder="Filtrar..."
            className={inputClass}
          />
        </label>
        <label className="flex flex-col gap-1 w-36">
          <span className={labelClass}>Cidade</span>
          <input
            value={cidade}
            onChange={(e) => setCidade(e.target.value)}
            placeholder="Filtrar..."
            className={inputClass}
          />
        </label>
        <label className="flex flex-col gap-1 w-24">
          <span className={labelClass}>Estado</span>
          <select
            value={estado}
            onChange={(e) => setEstado(e.target.value)}
            className={inputClass}
          >
            <option value="">Todos</option>
            {estados.map((uf) => (
              <option key={uf} value={uf}>
                {uf}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 w-28">
          <span className={labelClass}>Status</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className={inputClass}
          >
            <option value="">Todos</option>
            <option value="done">Concluído</option>
            <option value="running">Em andamento</option>
            <option value="error">Erro</option>
          </select>
        </label>
        <div className="ml-auto flex items-center gap-2 pb-0.5">
          <span className="text-[11px] text-[#4a5568] font-['JetBrains_Mono']">
            {filtered.length} buscas
          </span>
          {selectedIds.length > 0 ? (
            <button
              type="button"
              onClick={handleBatchRefresh}
              className="h-8 px-3 bg-[#2563eb] hover:bg-[#1d4ed8] rounded-md text-xs font-medium text-white flex items-center gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Reler {selectedIds.length}
            </button>
          ) : null}
        </div>
      </section>

      <div className="flex-1 min-h-0 border border-[#1e2d45] rounded-md overflow-hidden bg-[#0c1118] flex flex-col">
        <div className="h-10 px-4 border-b border-[#1e2d45] flex items-center">
          <span className="text-[11px] font-semibold text-[#4a5568] uppercase tracking-[0.1em]">
            Prospecções Passadas
          </span>
        </div>

        {isLoading ? (
          <div className="flex-1 p-4 text-[12px] font-['JetBrains_Mono'] text-[#4a5568]">
            // carregando...
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex-1 p-4 text-[12px] font-['JetBrains_Mono'] text-[#1e2d45]">
            // nenhuma prospecção registrada
          </div>
        ) : (
          <div className="flex-1 overflow-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <th className={`${headerClass} w-12`}>Sel.</th>
                  <th className={`${headerClass} w-[180px]`}>Segmento</th>
                  <th className={`${headerClass} w-[120px]`}>Cidade</th>
                  <th className={`${headerClass} w-14`}>UF</th>
                  <th className={`${headerClass} w-20`}>Leads</th>
                  <th className={`${headerClass} w-24`}>Status</th>
                  <th className={`${headerClass} w-[140px]`}>Data</th>
                  <th className={`${headerClass} w-[200px]`}>Ações</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((item) => {
                  const checked = selectedIds.includes(item.id);
                  return (
                    <tr
                      key={item.id}
                      className="border-b border-[#162035] hover:bg-[#0f1623] transition-colors duration-100"
                    >
                      <td className={cellClass}>
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={() => toggleSelect(item.id)}
                          className="h-4 w-4 accent-[#2563eb]"
                        />
                      </td>
                      <td className={`${cellClass} text-[#e8edf5] font-medium`}>
                        {item.keyword}
                      </td>
                      <td className={cellClass}>{item.city}</td>
                      <td className={cellClass}>{item.state}</td>
                      <td className={cellClass}>{item.leads_found}</td>
                      <td className={cellClass}>{item.status}</td>
                      <td className={cellClass}>{formatDate(item.created_at)}</td>
                      <td className={cellClass}>
                        <div className="flex items-center gap-1">
                          <button
                            type="button"
                            onClick={() => handleOpen(item)}
                            className="h-7 px-2 border border-[#1e2d45] rounded-sm text-[11px] hover:border-[#2563eb] hover:text-[#60a5fa]"
                          >
                            Abrir
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDownload(item)}
                            className="h-7 w-7 border border-[#1e2d45] rounded-sm flex items-center justify-center hover:text-[#8896ac]"
                            aria-label="Exportar"
                          >
                            <Download className="w-3.5 h-3.5" />
                          </button>
                          <button
                            type="button"
                            onClick={() => handleRefresh(item)}
                            className="h-7 w-7 border border-[#1e2d45] rounded-sm flex items-center justify-center hover:text-[#8896ac]"
                            aria-label="Reler leads"
                          >
                            <RefreshCw className="w-3.5 h-3.5" />
                          </button>
                          <button
                            type="button"
                            onClick={() => deleteMutation.mutate(item.id)}
                            className="h-7 w-7 border border-[#1e2d45] rounded-sm flex items-center justify-center hover:text-[#fca5a5]"
                            aria-label="Excluir"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
