const FORMATADOR_INSTANTE = new Intl.DateTimeFormat("pt-BR", {
  timeZone: "America/Sao_Paulo",
  dateStyle: "short",
  timeStyle: "medium",
});

export function formatarInstanteCrm(valor: string | null | undefined): string {
  const instante = valor ? Date.parse(valor) : NaN;
  return Number.isFinite(instante)
    ? FORMATADOR_INSTANTE.format(instante)
    : "Não registrado";
}

export function formatarDataCivil(valor: string | null): string {
  if (!valor || !/^\d{4}-\d{2}-\d{2}$/.test(valor)) return "Sem data";
  const dataEmUtc = new Date(`${valor}T00:00:00Z`);
  if (!Number.isFinite(dataEmUtc.getTime()) || dataEmUtc.toISOString().slice(0, 10) !== valor)
    return "Sem data";
  return valor.split("-").reverse().join("/");
}
