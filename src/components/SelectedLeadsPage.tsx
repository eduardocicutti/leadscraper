import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, ExternalLink, MapPin, RefreshCw, Send, Trash2, Upload } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  api,
  type ImportSelectedLeadsResponse,
  type MessageTemplateResponse,
  type SelectedLead,
  type SelectedLeadFilters,
} from "../api";
import { useAppStore } from "../store";

const TEMPLATE_VARS = ["empresa", "segmento", "cidade", "estado", "prospectador"];

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

function invalidTemplateVars(template: string): string[] {
  const used = [...template.matchAll(/\{(\w+)\}/g)].map((match) => match[1]);
  return [...new Set(used.filter((name) => !TEMPLATE_VARS.includes(name)))];
}

const labelClass =
  "text-[10px] font-semibold text-[#4a5568] uppercase tracking-[0.08em]";
const inputClass =
  "h-8 bg-[#0b1220] border border-[#1e2d45] rounded-md px-3 text-[13px] text-[#e8edf5] font-['JetBrains_Mono'] placeholder:text-[#4a5568] focus:border-[#2563eb] focus:ring-0 outline-none transition-colors duration-100";
const headerClass =
  "sticky top-0 bg-[#0c1118] text-[10px] font-semibold text-[#4a5568] uppercase tracking-[0.1em] border-b border-[#1e2d45] px-3 py-2 text-left";
const cellClass =
  "text-[13px] text-[#8896ac] px-3 py-2.5 font-['JetBrains_Mono'] whitespace-nowrap";

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result || "");
      resolve(result.includes(",") ? result.split(",")[1] : result);
    };
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

export function SelectedLeadsPage() {
  const queryClient = useQueryClient();
  const prospectador = useAppStore((state) => state.prospectador);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [segmento, setSegmento] = useState("");
  const [cidade, setCidade] = useState("");
  const [estado, setEstado] = useState("");
  const [temperatura, setTemperatura] = useState("");
  const [comWhatsapp, setComWhatsapp] = useState("");
  const [comSite, setComSite] = useState("");
  const [templateSegmento, setTemplateSegmento] = useState("");
  const [template, setTemplate] = useState("");
  const [templateDirty, setTemplateDirty] = useState(false);
  const [editingNotes, setEditingNotes] = useState<Record<number, string>>({});
  const [editingMessages, setEditingMessages] = useState<Record<number, string>>({});
  const [importSummary, setImportSummary] = useState("");

  const { data: leads = [], isLoading } = useQuery({
    queryKey: ["selected-leads"],
    queryFn: () => api.get<SelectedLead[]>("/selected-leads").then((r) => r.data),
  });

  const templateQuery = useQuery({
    queryKey: ["message-template", templateSegmento],
    queryFn: () =>
      api
        .get<{ template: string }>("/selected-leads/message-template", {
          params: templateSegmento ? { segmento: templateSegmento } : {},
        })
        .then((r) => r.data.template),
  });

  useEffect(() => {
    if (templateQuery.data && !templateDirty) {
      setTemplate(templateQuery.data);
    }
  }, [templateQuery.data, templateDirty]);

  const displayTemplate = template;

  const invalidVars = useMemo(
    () => invalidTemplateVars(displayTemplate || ""),
    [displayTemplate],
  );

  const filtered = useMemo(() => {
    return leads.filter((lead) => {
      if (segmento && !(lead.segmento || lead.categoria).toLowerCase().includes(segmento.toLowerCase())) {
        return false;
      }
      if (cidade && !lead.cidade.toLowerCase().includes(cidade.toLowerCase())) {
        return false;
      }
      if (estado && lead.estado !== estado) {
        return false;
      }
      if (temperatura === "quente" && !lead.classificacao.includes("Quente")) {
        return false;
      }
      if (temperatura === "morno" && !lead.classificacao.includes("Morno")) {
        return false;
      }
      if (temperatura === "frio" && !lead.classificacao.includes("Frio")) {
        return false;
      }
      if (comWhatsapp === "sim" && !lead.is_whatsapp) {
        return false;
      }
      if (comWhatsapp === "nao" && lead.is_whatsapp) {
        return false;
      }
      if (comSite === "sim" && !lead.site) {
        return false;
      }
      if (comSite === "nao" && lead.site) {
        return false;
      }
      return true;
    });
  }, [leads, segmento, cidade, estado, temperatura, comWhatsapp, comSite]);

  const estados = useMemo(
    () => [...new Set(leads.map((l) => l.estado).filter(Boolean))].sort(),
    [leads],
  );

  const segmentos = useMemo(
    () => [...new Set(leads.map((l) => l.segmento || l.categoria).filter(Boolean))].sort(),
    [leads],
  );

  const activeFilters: SelectedLeadFilters = {
    segmento,
    cidade,
    estado,
    temperatura,
    com_whatsapp: comWhatsapp,
    com_site: comSite,
    prospectador,
  };

  const refreshMutation = useMutation({
    mutationFn: () =>
      api
        .post<MessageTemplateResponse>("/selected-leads/refresh-links", {
          template: displayTemplate,
          segmento: templateSegmento || undefined,
        })
        .then((r) => r.data),
    onSuccess: (data) => {
      setTemplate(data.template);
      setTemplateDirty(false);
      queryClient.setQueryData(["message-template", templateSegmento], data.template);
      queryClient.setQueryData(["selected-leads"], data.leads);
    },
  });

  const exportMutation = useMutation({
    mutationFn: () =>
      api.post("/selected-leads/export", activeFilters, { responseType: "blob" }),
    onSuccess: (response) => {
      const url = URL.createObjectURL(response.data);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "lista_preferencial_filtrada.xlsx";
      anchor.click();
      URL.revokeObjectURL(url);
    },
  });

  const saveLeadMutation = useMutation({
    mutationFn: ({
      id,
      notes,
      custom_message,
    }: {
      id: number;
      notes?: string;
      custom_message?: string;
    }) =>
      api
        .patch<SelectedLead>(`/selected-leads/${id}`, { notes, custom_message })
        .then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["selected-leads"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/selected-leads/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["selected-leads"] });
    },
  });

  const importMutation = useMutation({
    mutationFn: async (file: File) => {
      const content_base64 = await fileToBase64(file);
      return api
        .post<ImportSelectedLeadsResponse>("/selected-leads/import-spreadsheet", {
          filename: file.name,
          content_base64,
          prospectador,
        })
        .then((r) => r.data);
    },
    onSuccess: (data) => {
      setImportSummary(
        `Importados: ${data.imported_count}. Repetidos/ignorados: ${data.skipped_count}. Linhas lidas: ${data.rows_read}.`,
      );
      queryClient.invalidateQueries({ queryKey: ["selected-leads"] });
    },
    onError: () => {
      setImportSummary("Falha ao importar planilha.");
    },
  });

  function handleTemplateChange(value: string) {
    setTemplate(value);
    setTemplateDirty(true);
  }

  function getNotes(lead: SelectedLead) {
    return editingNotes[lead.id] ?? lead.notes;
  }

  function getCustomMessage(lead: SelectedLead) {
    return editingMessages[lead.id] ?? lead.custom_message ?? "";
  }

  function handleNotesBlur(lead: SelectedLead) {
    const notes = getNotes(lead);
    if (notes !== lead.notes) {
      saveLeadMutation.mutate({ id: lead.id, notes });
    }
    setEditingNotes((prev) => {
      const next = { ...prev };
      delete next[lead.id];
      return next;
    });
  }

  function handleMessageBlur(lead: SelectedLead) {
    const custom_message = getCustomMessage(lead);
    if (custom_message !== (lead.custom_message ?? "")) {
      saveLeadMutation.mutate({ id: lead.id, custom_message });
    }
    setEditingMessages((prev) => {
      const next = { ...prev };
      delete next[lead.id];
      return next;
    });
  }

  function handleImportChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setImportSummary("");
    importMutation.mutate(file);
    event.target.value = "";
  }

  return (
    <div className="flex-1 min-h-0 p-6 flex flex-col gap-4 overflow-hidden">
      <section className="border border-[#1e2d45] rounded-md bg-[#0f1623] p-4 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-semibold text-[#4a5568] uppercase tracking-[0.1em]">
            Mensagem base
          </span>
          <div className="flex items-center gap-2">
            <select
              value={templateSegmento}
              onChange={(e) => {
                setTemplateSegmento(e.target.value);
                setTemplateDirty(false);
              }}
              className="h-8 bg-[#0b1220] border border-[#1e2d45] rounded-md px-2 text-xs text-[#e8edf5] outline-none"
            >
              <option value="">Template global</option>
              {segmentos.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx,.xlsm,.xltx,.xltm,.csv,.tsv"
              onChange={handleImportChange}
              className="hidden"
            />
            <button
              type="button"
              disabled={importMutation.isPending}
              onClick={() => fileInputRef.current?.click()}
              className="h-8 px-3 bg-[#0f1623] hover:bg-[#162035] disabled:bg-[#0b1220] border border-[#1e2d45] text-[#e8edf5] rounded-md text-xs font-medium flex items-center gap-1.5 transition-colors duration-100"
            >
              <Upload className="w-3.5 h-3.5" />
              {importMutation.isPending ? "Importando" : "Importar planilha"}
            </button>
            <button
              type="button"
              disabled={refreshMutation.isPending || invalidVars.length > 0}
              onClick={() => refreshMutation.mutate()}
              className="h-8 px-3 bg-[#2563eb] hover:bg-[#1d4ed8] disabled:bg-[#1d3a6e] disabled:text-[#8896ac] rounded-md text-xs font-medium text-white flex items-center gap-1.5 transition-colors duration-100"
            >
              <RefreshCw
                className={`w-3.5 h-3.5 ${refreshMutation.isPending ? "animate-spin" : ""}`}
              />
              Atualizar links
            </button>
          </div>
        </div>
        <textarea
          value={displayTemplate}
          onChange={(event) => handleTemplateChange(event.target.value)}
          rows={5}
          className="w-full bg-[#0b1220] border border-[#1e2d45] rounded-md px-3 py-2 text-[13px] text-[#e8edf5] font-['JetBrains_Mono'] placeholder:text-[#4a5568] focus:border-[#2563eb] focus:ring-0 outline-none transition-colors duration-100 resize-y"
        />
        <div className="text-[11px] text-[#4a5568] font-['JetBrains_Mono']">
          Variáveis:{" "}
          {TEMPLATE_VARS.map((v) => (
            <code key={v} className="text-[#8896ac] mr-2">{`{${v}}`}</code>
          ))}
        </div>
        {invalidVars.length > 0 ? (
          <div className="text-[11px] text-[#fca5a5] font-['JetBrains_Mono']">
            Variáveis inválidas: {invalidVars.map((v) => `{${v}}`).join(", ")}
          </div>
        ) : null}
        <div className="text-[11px] text-[#4a5568] font-['JetBrains_Mono']">
          Prospectador atual: {prospectador}
          {templateSegmento ? ` | Template do segmento: ${templateSegmento}` : " | Template global"}
        </div>
        {importSummary ? (
          <div className="text-[11px] text-[#60a5fa] font-['JetBrains_Mono']">
            {importSummary}
          </div>
        ) : null}
      </section>

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
          <span className={labelClass}>Temperatura</span>
          <select
            value={temperatura}
            onChange={(e) => setTemperatura(e.target.value)}
            className={inputClass}
          >
            <option value="">Todas</option>
            <option value="quente">Quente</option>
            <option value="morno">Morno</option>
            <option value="frio">Frio</option>
          </select>
        </label>
        <label className="flex flex-col gap-1 w-28">
          <span className={labelClass}>WhatsApp</span>
          <select
            value={comWhatsapp}
            onChange={(e) => setComWhatsapp(e.target.value)}
            className={inputClass}
          >
            <option value="">Todos</option>
            <option value="sim">Com WA</option>
            <option value="nao">Sem WA</option>
          </select>
        </label>
        <label className="flex flex-col gap-1 w-28">
          <span className={labelClass}>Site</span>
          <select
            value={comSite}
            onChange={(e) => setComSite(e.target.value)}
            className={inputClass}
          >
            <option value="">Todos</option>
            <option value="sim">Com site</option>
            <option value="nao">Sem site</option>
          </select>
        </label>
        <div className="ml-auto text-[11px] text-[#4a5568] font-['JetBrains_Mono'] pb-1">
          {filtered.length} de {leads.length} leads
        </div>
        <button
          type="button"
          disabled={exportMutation.isPending}
          onClick={() => exportMutation.mutate()}
          className="h-8 px-3 bg-[#0f1623] hover:bg-[#162035] disabled:bg-[#0b1220] border border-[#1e2d45] text-[#e8edf5] rounded-md text-xs font-medium flex items-center gap-1.5"
        >
          <Download className="w-3.5 h-3.5" />
          {exportMutation.isPending ? "Exportando" : "Exportar filtro"}
        </button>
      </section>

      <div className="flex-1 min-h-0 border border-[#1e2d45] rounded-md overflow-hidden bg-[#0c1118] flex flex-col">
        <div className="h-10 px-4 border-b border-[#1e2d45] flex items-center">
          <span className="text-[11px] font-semibold text-[#4a5568] uppercase tracking-[0.1em]">
            Lista Preferencial
          </span>
        </div>

        {isLoading ? (
          <div className="flex-1 p-4 text-[12px] font-['JetBrains_Mono'] text-[#4a5568]">
            // carregando...
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex-1 p-4 text-[12px] font-['JetBrains_Mono'] text-[#1e2d45]">
            // nenhum lead selecionado
          </div>
        ) : (
          <div className="flex-1 overflow-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <th className={`${headerClass} w-20`}>Temp.</th>
                  <th className={`${headerClass} w-[200px]`}>Empresa</th>
                  <th className={`${headerClass} w-[130px]`}>Categoria</th>
                  <th className={`${headerClass} w-[100px]`}>Cidade</th>
                  <th className={`${headerClass} w-14`}>UF</th>
                  <th className={`${headerClass} w-[130px]`}>Telefone</th>
                  <th className={`${headerClass} w-[180px]`}>Notas</th>
                  <th className={`${headerClass} w-[180px]`}>Msg. custom.</th>
                  <th className={`${headerClass} w-16`}>Site</th>
                  <th className={`${headerClass} w-16`}>Maps</th>
                  <th className={`${headerClass} w-28`}>Ações</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((lead) => {
                  const badge = tempBadge(lead.classificacao);
                  return (
                    <tr
                      key={lead.id}
                      className="border-b border-[#162035] hover:bg-[#0f1623] transition-colors duration-100"
                    >
                      <td className={cellClass}>
                        <span
                          className={`px-1.5 py-0.5 rounded-sm text-[10px] font-mono font-medium border ${badge.className}`}
                        >
                          {badge.label}
                        </span>
                      </td>
                      <td className={`${cellClass} text-[#e8edf5] font-medium`}>
                        {lead.nome}
                      </td>
                      <td className={cellClass}>{lead.categoria}</td>
                      <td className={cellClass}>{lead.cidade}</td>
                      <td className={cellClass}>{lead.estado}</td>
                      <td className={cellClass}>
                        {lead.telefone || <span className="text-[#1e2d45]">—</span>}
                      </td>
                      <td className={cellClass}>
                        <input
                          value={getNotes(lead)}
                          onChange={(e) =>
                            setEditingNotes((prev) => ({
                              ...prev,
                              [lead.id]: e.target.value,
                            }))
                          }
                          onBlur={() => handleNotesBlur(lead)}
                          placeholder="..."
                          className="w-full h-7 bg-[#0b1220] border border-[#1e2d45] rounded px-2 text-[12px] text-[#8896ac] focus:border-[#2563eb] outline-none"
                        />
                      </td>
                      <td className={cellClass}>
                        <input
                          value={getCustomMessage(lead)}
                          onChange={(e) =>
                            setEditingMessages((prev) => ({
                              ...prev,
                              [lead.id]: e.target.value,
                            }))
                          }
                          onBlur={() => handleMessageBlur(lead)}
                          placeholder="Usa template global"
                          className="w-full h-7 bg-[#0b1220] border border-[#1e2d45] rounded px-2 text-[12px] text-[#8896ac] focus:border-[#2563eb] outline-none"
                        />
                      </td>
                      <td className={cellClass}>
                        {lead.site ? (
                          <a
                            href={lead.site}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex h-6 w-6 items-center justify-center text-[#4a5568] hover:text-[#8896ac]"
                          >
                            <ExternalLink className="w-3.5 h-3.5" />
                          </a>
                        ) : (
                          <span className="text-[#1e2d45]">—</span>
                        )}
                      </td>
                      <td className={cellClass}>
                        {lead.url_maps ? (
                          <a
                            href={lead.url_maps}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex h-6 w-6 items-center justify-center text-[#4a5568] hover:text-[#8896ac]"
                          >
                            <MapPin className="w-3.5 h-3.5" />
                          </a>
                        ) : (
                          <span className="text-[#1e2d45]">—</span>
                        )}
                      </td>
                      <td className={cellClass}>
                        <div className="flex items-center gap-1">
                          {lead.is_whatsapp && lead.whatsapp_link ? (
                            <a
                              href={lead.whatsapp_link}
                              target="_blank"
                              rel="noreferrer"
                              className="h-7 px-2 bg-transparent border border-[#1e2d45] rounded-sm text-[11px] text-[#25d366] hover:border-[#25d366] transition-colors duration-100 inline-flex items-center gap-1"
                            >
                              <Send className="w-3 h-3" /> Enviar
                            </a>
                          ) : (
                            <span className="h-7 px-2 border border-[#1e2d45] rounded-sm text-[11px] text-[#4a5568] inline-flex items-center">
                              Sem WhatsApp
                            </span>
                          )}
                          <button
                            type="button"
                            aria-label="Remover lead"
                            onClick={() => deleteMutation.mutate(lead.id)}
                            className="h-7 w-7 rounded-sm border border-[#1e2d45] text-[#4a5568] hover:text-[#fca5a5] hover:border-[rgba(239,68,68,0.3)] flex items-center justify-center transition-colors duration-100"
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
