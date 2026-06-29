import { FormEvent, useState } from "react";
import { Loader2, Play } from "lucide-react";
import { api } from "../api";
import { useAppStore } from "../store";

const prospectadores = ["Eduardo", "Murilo", "Sofia", "Ydian", "Gabriel"];
const estados = [
  "AC",
  "AL",
  "AP",
  "AM",
  "BA",
  "CE",
  "DF",
  "ES",
  "GO",
  "MA",
  "MT",
  "MS",
  "MG",
  "PA",
  "PB",
  "PR",
  "PE",
  "PI",
  "RJ",
  "RN",
  "RS",
  "RO",
  "RR",
  "SC",
  "SP",
  "SE",
  "TO",
];

export function SearchPanel() {
  const status = useAppStore((state) => state.status);
  const setJob = useAppStore((state) => state.setJob);
  const updateStatus = useAppStore((state) => state.updateStatus);
  const prospectador = useAppStore((state) => state.prospectador);
  const setProspectador = useAppStore((state) => state.setProspectador);
  const [segmento, setSegmento] = useState("");
  const [cidade, setCidade] = useState("");
  const [estado, setEstado] = useState("ES");
  const [maxResults, setMaxResults] = useState(30);

  const running = status === "running" || status === "pending";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const params = {
      segmento: segmento.trim(),
      cidade: cidade.trim(),
      estado,
      prospectador,
    };

    try {
      const response = await api.post<{ job_id: string }>("/scrape", {
        ...params,
        max_results: maxResults,
      });
      setJob(response.data.job_id, params, maxResults);
    } catch {
      updateStatus({
        status: "error",
        progress: 0,
        total: 0,
        log: "Falha na extração. Feche e abra o aplicativo novamente.",
        leads_count: 0,
        leads: [],
      });
    }
  }

  const labelClass =
    "text-[10px] font-semibold text-[#4a5568] uppercase tracking-[0.08em]";
  const inputClass =
    "h-8 bg-[#0b1220] border border-[#1e2d45] rounded-md px-3 text-[13px] text-[#e8edf5] font-['JetBrains_Mono'] placeholder:text-[#4a5568] focus:border-[#2563eb] focus:ring-0 outline-none transition-colors duration-100";

  return (
    <form
      onSubmit={handleSubmit}
      className="h-auto bg-[#0f1623] border-b border-[#1e2d45] px-6 py-3 flex items-end gap-3"
    >
      <label className="flex flex-col gap-1 w-36">
        <span className={labelClass}>Prospectador</span>
        <select
          value={prospectador}
          onChange={(event) => setProspectador(event.target.value)}
          className={inputClass}
        >
          {prospectadores.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-1 flex-1 min-w-48">
        <span className={labelClass}>Segmento</span>
        <input
          value={segmento}
          onChange={(event) => setSegmento(event.target.value)}
          placeholder="clínicas odontológicas, academias..."
          required
          className={inputClass}
        />
      </label>

      <label className="flex flex-col gap-1 w-44">
        <span className={labelClass}>Cidade</span>
        <input
          value={cidade}
          onChange={(event) => setCidade(event.target.value)}
          placeholder="São Mateus"
          required
          className={inputClass}
        />
      </label>

      <label className="flex flex-col gap-1 w-20">
        <span className={labelClass}>Estado</span>
        <select
          value={estado}
          onChange={(event) => setEstado(event.target.value)}
          required
          className={inputClass}
        >
          {estados.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-1 w-28">
        <span className={labelClass}>Quantidade</span>
        <input
          type="number"
          min={1}
          max={500}
          value={maxResults}
          onChange={(event) => setMaxResults(Number(event.target.value || 1))}
          required
          className={inputClass}
        />
      </label>

      <button
        type="submit"
        disabled={running}
        className="h-8 px-4 bg-[#2563eb] hover:bg-[#1d4ed8] disabled:bg-[#1d3a6e] disabled:text-[#8896ac] rounded-md text-[13px] font-semibold text-white flex items-center gap-2 transition-colors duration-100"
      >
        {running ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
        ) : (
          <Play className="w-3.5 h-3.5 fill-current" />
        )}
        {running ? "Extraindo..." : "Iniciar extração"}
      </button>
    </form>
  );
}
