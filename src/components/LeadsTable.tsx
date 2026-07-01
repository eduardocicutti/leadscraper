import { Download, ExternalLink, MapPin, Save } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { api } from "../api";
import type { Lead } from "../api";
import { leadKey, useAppStore } from "../store";

function tempBadge(classificacao: string) {
  if (classificacao.includes("Quente")) {
    return {
      label: "HOT",
      className:
        "bg-[rgba(239,68,68,0.08)] text-[#fca5a5] border-[rgba(239,68,68,0.2)]",
    };
  }
  if (classificacao.includes("Morno")) {
    return {
      label: "WARM",
      className:
        "bg-[rgba(234,179,8,0.08)] text-[#fcd34d] border-[rgba(234,179,8,0.2)]",
    };
  }
  return {
    label: "COLD",
    className:
      "bg-[rgba(59,130,246,0.08)] text-[#93c5fd] border-[rgba(59,130,246,0.2)]",
  };
}

function scoreClass(score: number) {
  if (score >= 70) return "text-[#fca5a5]";
  if (score >= 45) return "text-[#fcd34d]";
  return "text-[#8896ac]";
}

function LinkCell({
  href,
  label,
  children,
}: {
  href?: string | null;
  label: string;
  children: React.ReactNode;
}) {
  if (!href) {
    return <span className="text-[#1e2d45]">—</span>;
  }

  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      aria-label={label}
      className="inline-flex h-6 w-6 items-center justify-center text-[#4a5568] hover:text-[#8896ac] transition-colors duration-100"
    >
      {children}
    </a>
  );
}

export function LeadsTable() {
  const queryClient = useQueryClient();
  const leads = useAppStore((state) => state.leads);
  const status = useAppStore((state) => state.status);
  const jobId = useAppStore((state) => state.jobId);
  const searchParams = useAppStore((state) => state.searchParams);
  const selectedLeadKeys = useAppStore((state) => state.selectedLeadKeys);
  const toggleLeadSelection = useAppStore((state) => state.toggleLeadSelection);
  const clearLeadSelection = useAppStore((state) => state.clearLeadSelection);

  const selectedLeads = leads.filter((lead) => selectedLeadKeys.includes(leadKey(lead)));

  async function handleDownload() {
    if (!jobId || !searchParams) return;

    if (jobId.startsWith("history:")) {
      const historyId = jobId.replace("history:", "");
      const response = await api.get(`/history/${historyId}/download`, {
        responseType: "blob",
      });
      const url = URL.createObjectURL(response.data);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `leads_${searchParams.segmento}_${searchParams.cidade}.xlsx`;
      anchor.click();
      URL.revokeObjectURL(url);
      return;
    }

    const query = new URLSearchParams(searchParams).toString();
    const response = await api.get(`/download/${jobId}?${query}`, {
      responseType: "blob",
    });
    const url = URL.createObjectURL(response.data);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `leads_${searchParams.segmento}_${searchParams.cidade}.xlsx`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  async function handleSaveSelected() {
    if (selectedLeads.length === 0) return;
    await api.post("/selected-leads", { leads: selectedLeads });
    clearLeadSelection();
    await queryClient.invalidateQueries({ queryKey: ["selected-leads"] });
  }

  const headerClass =
    "sticky top-0 bg-[#0c1118] text-[10px] font-semibold text-[#4a5568] uppercase tracking-[0.1em] border-b border-[#1e2d45] px-3 py-2 text-left";
  const cellClass =
    "text-[13px] text-[#8896ac] px-3 py-2.5 font-['JetBrains_Mono'] whitespace-nowrap";

  return (
    <div className="flex-1 min-h-0 border border-[#1e2d45] rounded-md overflow-hidden bg-[#0c1118] flex flex-col">
      <div className="h-10 px-4 border-b border-[#1e2d45] flex items-center justify-between">
        <span className="text-[11px] font-semibold text-[#4a5568] uppercase tracking-[0.1em]">
          Resultados
        </span>
        <div className="flex items-center gap-2">
          {selectedLeads.length > 0 ? (
            <button
              type="button"
              onClick={handleSaveSelected}
              className="h-8 px-3 bg-[#0f1623] hover:bg-[#162035] border border-[#1e2d45] text-[#e8edf5] text-xs font-medium rounded-md flex items-center gap-1.5 transition-colors duration-100"
            >
              <Save className="w-3.5 h-3.5" /> Salvar {selectedLeads.length}
            </button>
          ) : null}
          {status === "done" && jobId ? (
            <button
              type="button"
              onClick={handleDownload}
              className="h-8 px-3 bg-[#0f1623] hover:bg-[#162035] border border-[#1e2d45] text-[#e8edf5] text-xs font-medium rounded-md flex items-center gap-1.5 transition-colors duration-100"
            >
              <Download className="w-3.5 h-3.5" /> Exportar .xlsx
            </button>
          ) : null}
        </div>
      </div>

      {leads.length === 0 ? (
        <div className="flex-1 p-4 text-[12px] font-['JetBrains_Mono'] text-[#1e2d45]">
          // nenhuma extração iniciada
        </div>
      ) : (
        <div className="flex-1 overflow-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <th className={`${headerClass} w-12`}>Sel.</th>
                <th className={`${headerClass} w-20`}>Temp.</th>
                <th className={`${headerClass} w-16`}>Score</th>
                <th className={`${headerClass} w-[220px]`}>Empresa</th>
                <th className={`${headerClass} w-[150px]`}>Categoria</th>
                <th className={`${headerClass} w-[120px]`}>Porte</th>
                <th className={`${headerClass} w-[140px]`}>Telefone</th>
                <th className={`${headerClass} w-16`}>Nota</th>
                <th className={`${headerClass} w-[70px]`}>Aval.</th>
                <th className={`${headerClass} w-16`}>Site</th>
                <th className={`${headerClass} w-16`}>Maps</th>
                <th className={`${headerClass} w-20`}>WA</th>
              </tr>
            </thead>
            <tbody>
              {leads.map((lead: Lead, index) => {
                const badge = tempBadge(lead.classificacao);
                const key = leadKey(lead);
                const checked = selectedLeadKeys.includes(key);
                return (
                  <tr
                    key={`${lead.nome}-${lead.url_maps}-${index}`}
                    className="border-b border-[#162035] hover:bg-[#0f1623] transition-colors duration-100"
                  >
                    <td className={cellClass}>
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => toggleLeadSelection(key)}
                        aria-label="Selecionar lead"
                        className="h-4 w-4 accent-[#2563eb]"
                      />
                    </td>
                    <td className={cellClass}>
                      <span
                        className={`px-1.5 py-0.5 rounded-sm text-[10px] font-mono font-medium border ${badge.className}`}
                      >
                        {badge.label}
                      </span>
                    </td>
                    <td className={`${cellClass} ${scoreClass(lead.score)} font-medium`}>
                      {lead.score}
                    </td>
                    <td className={`${cellClass} text-[#e8edf5] font-medium`}>
                      {lead.nome}
                    </td>
                    <td className={cellClass}>{lead.categoria}</td>
                    <td className={cellClass}>{lead.porte}</td>
                    <td className={cellClass}>
                      {lead.telefone || <span className="text-[#1e2d45]">—</span>}
                    </td>
                    <td className={cellClass}>{lead.nota ?? "—"}</td>
                    <td className={cellClass}>{lead.avaliacoes ?? 0}</td>
                    <td className={cellClass}>
                      <LinkCell href={lead.site} label="Abrir site">
                        <ExternalLink className="w-3.5 h-3.5" />
                      </LinkCell>
                    </td>
                    <td className={cellClass}>
                      <LinkCell href={lead.url_maps} label="Abrir Maps">
                        <MapPin className="w-3.5 h-3.5" />
                      </LinkCell>
                    </td>
                    <td className={cellClass}>
                      {lead.is_whatsapp && lead.whatsapp_link ? (
                        <a
                          href={lead.whatsapp_link}
                          target="_blank"
                          rel="noreferrer"
                          className="h-6 px-2 bg-transparent border border-[#1e2d45] rounded-sm text-[11px] text-[#4a5568] hover:border-[#25d366] hover:text-[#25d366] transition-colors duration-100 inline-flex items-center"
                        >
                          WA ↗
                        </a>
                      ) : (
                        <span className="text-[#1e2d45]">—</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}