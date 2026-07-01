import { useQuery } from "@tanstack/react-query";
import { api, type HistoryDetail, type HistoryRecord } from "../api";
import { useAppStore } from "../store";

function formatRelative(value: string) {
  const date = new Date(value);
  const diff = Date.now() - date.getTime();
  const minutes = Math.max(0, Math.floor(diff / 60000));

  if (minutes < 1) return "agora";
  if (minutes < 60) return `há ${minutes}min`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `há ${hours}h`;

  const days = Math.floor(hours / 24);
  return `há ${days}d`;
}

export function HistoryPanel() {
  const currentParams = useAppStore((state) => state.searchParams);
  const openSavedLeads = useAppStore((state) => state.openSavedLeads);
  const { data = [] } = useQuery({
    queryKey: ["history"],
    queryFn: () => api.get<HistoryRecord[]>("/history").then((response) => response.data),
    refetchInterval: 5000,
  });

  async function handleOpen(item: HistoryRecord) {
    const response = await api.get<HistoryDetail>(`/history/${item.id}`);
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

  return (
    <div className="w-72 h-full bg-[#0c1118] border-l border-[#1e2d45] flex flex-col">
      <div className="h-10 px-4 border-b border-[#162035] flex items-center">
        <span className="text-[11px] font-semibold text-[#4a5568] uppercase tracking-[0.1em]">
          Histórico
        </span>
      </div>
      <div className="flex-1 overflow-y-auto">
        {data.length === 0 ? (
          <div className="px-4 py-3 text-[11px] text-[#4a5568] font-['JetBrains_Mono']">
            Nenhuma extração registrada
          </div>
        ) : (
          data.map((item) => {
            const active =
              currentParams?.segmento === item.keyword &&
              currentParams?.cidade === item.city &&
              currentParams?.estado === item.state;

            return (
              <button
                type="button"
                key={item.id}
                onClick={() => handleOpen(item)}
                className={`w-full text-left px-4 py-3 border-b border-[#162035] cursor-pointer hover:bg-[#0f1623] transition-colors duration-100 ${
                  active ? "border-l-2 border-l-[#2563eb] bg-[#0f1623]" : ""
                }`}
              >
                <div
                  className={`text-[13px] font-medium ${
                    active ? "text-[#e8edf5]" : "text-[#8896ac]"
                  }`}
                >
                  {item.keyword} · {item.city}
                </div>
                <div className="text-[11px] text-[#4a5568] font-['JetBrains_Mono'] mt-0.5">
                  {item.leads_found} leads · {formatRelative(item.created_at)}
                </div>
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}