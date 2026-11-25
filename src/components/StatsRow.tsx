import { useAppStore } from "../store";

export function StatsRow() {
  const leads = useAppStore((state) => state.leads);
  const status = useAppStore((state) => state.status);

  if (status !== "done") {
    return null;
  }

  const stats = [
    { label: "Total", value: leads.length },
    {
      label: "Quentes",
      value: leads.filter((lead) => lead.classificacao.includes("Quente")).length,
    },
    {
      label: "Mornos",
      value: leads.filter((lead) => lead.classificacao.includes("Morno")).length,
    },
    {
      label: "Frios",
      value: leads.filter((lead) => lead.classificacao.includes("Frio")).length,
    },
    {
      label: "Com WhatsApp",
      value: leads.filter((lead) => lead.is_whatsapp).length,
    },
    {
      label: "Com Site",
      value: leads.filter((lead) => lead.site).length,
    },
  ];

  return (
    <dl className="painel medicao-prospeccao" aria-label="Resumo dos resultados">
      {stats.map((indicador) => (
        <div key={indicador.label}>
          <dt>{indicador.label}</dt>
          <dd>{indicador.value}</dd>
        </div>
      ))}
    </dl>
  );
}
