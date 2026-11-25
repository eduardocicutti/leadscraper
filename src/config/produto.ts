export const PRODUTO = {
  nome: "Plataforma Comercial",
  organizacao: "Adapti",
  repositorio: "https://github.com/eduardocicutti/leadscraper",
};

const ambiente = (
  import.meta as ImportMeta & {
    env: Record<string, string | undefined>;
  }
).env;

export const API_URL = ambiente.VITE_API_URL || "http://127.0.0.1:8000";
