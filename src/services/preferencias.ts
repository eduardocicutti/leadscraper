import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

interface Preferencias {
  tema: "escuro" | "claro";
  densidade: "confortavel" | "compacta";
  escalaFonte: number;
  alterarTema: (tema: Preferencias["tema"]) => void;
  alterarDensidade: (densidade: Preferencias["densidade"]) => void;
  alterarEscala: (escala: number) => void;
  restaurar: () => void;
}

const PADRAO = { tema: "escuro" as const, densidade: "confortavel" as const, escalaFonte: 100 };

export const usePreferencias = create<Preferencias>()(persist((set) => ({
  ...PADRAO,
  alterarTema: (tema) => set({ tema }),
  alterarDensidade: (densidade) => set({ densidade }),
  alterarEscala: (escalaFonte) => set({ escalaFonte: Math.min(125, Math.max(100, escalaFonte)) }),
  restaurar: () => set(PADRAO),
}), {
  name: "plataforma-comercial-preferencias",
  version: 1,
  storage: createJSONStorage(() => localStorage),
  partialize: ({ tema, densidade, escalaFonte }) => ({ tema, densidade, escalaFonte }),
  merge: (persistido, atual) => {
    const salvo = persistido as Partial<Preferencias> | undefined;
    return { ...atual,
      tema: salvo?.tema === "claro" ? "claro" : "escuro",
      densidade: salvo?.densidade === "compacta" ? "compacta" : "confortavel",
      escalaFonte: typeof salvo?.escalaFonte === "number" && Number.isFinite(salvo.escalaFonte)
        ? Math.min(125, Math.max(100, salvo.escalaFonte)) : 100,
    };
  },
}));
