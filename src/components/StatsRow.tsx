import { useAppStore } from "../store";

export function StatsRow() {
  const leads = useAppStore((state) => state.leads);
  const status = useAppStore((state) => state.status);

  if (status !== "done") {
    return null;
  }

  const stats = [
    { label: "Total", value: leads.length, className: "text-[#e8edf5]" },
    {
      label: "Quentes",
      value: leads.filter((lead) => lead.classificacao.includes("Quente")).length,
      className: "text-[#fca5a5]",
    },
    {
      label: "Mornos",
      value: leads.filter((lead) => lead.classificacao.includes("Morno")).length,
      className: "text-[#fcd34d]",
    },
    {
      label: "Frios",
      value: leads.filter((lead) => lead.classificacao.includes("Frio")).length,
      className: "text-[#8896ac]",
    },
    {
      label: "Com WhatsApp",
      value: leads.filter((lead) => lead.is_whatsapp).length,
      className: "text-[#e8edf5]",
    },
    {
      label: "Com Site",
      value: leads.filter((lead) => lead.site).length,
      className: "text-[#e8edf5]",
    },
  ];

  return (
    <div className="flex items-center gap-0 border border-[#1e2d45] rounded-md overflow-hidden">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className="flex-1 px-4 py-3 border-r border-[#1e2d45] last:border-r-0 bg-[#0f1623]"
        >
          <div className={`text-xl font-['Geist_Mono'] font-bold ${stat.className}`}>
            {stat.value}
          </div>
          <div className="text-[10px] text-[#4a5568] uppercase tracking-[0.08em] mt-0.5">
            {stat.label}
          </div>
        </div>
      ))}
    </div>
  );
}
