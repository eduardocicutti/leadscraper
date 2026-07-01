import type { ReactNode } from "react";
import { useState } from "react";
import { Archive, History, Search, Settings, Star, X } from "lucide-react";
import { useAppStore } from "../store";
import { getInitials } from "../utils/initials";

interface LayoutProps {
  children: ReactNode;
  history: ReactNode;
}

export function Layout({ children, history }: LayoutProps) {
  const activeView = useAppStore((state) => state.activeView);
  const setActiveView = useAppStore((state) => state.setActiveView);
  const historyOpen = useAppStore((state) => state.historyOpen);
  const setHistoryOpen = useAppStore((state) => state.setHistoryOpen);
  const prospectador = useAppStore((state) => state.prospectador);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const avatarInitials = getInitials(prospectador);

  const navItem =
    "w-8 h-8 rounded-md flex items-center justify-center transition-colors duration-100";

  const headerTitle =
    activeView === "selected"
      ? "LISTA PREFERENCIAL"
      : activeView === "history"
        ? "PROSPECÇÕES PASSADAS"
        : "PROSPECÇÃO";

  return (
    <div className="min-h-screen w-full bg-[#0c1118] text-[#e8edf5] font-sans">
      <div
        className="fixed inset-0 z-0 pointer-events-none"
        style={{
          backgroundImage:
            "radial-gradient(circle 800px at 50% 50%, rgba(37,99,235,0.06), transparent)",
        }}
      />

      <div className="relative z-10 flex h-screen w-full">
        <aside className="w-16 h-full bg-[#0c1118] border-r border-[#1e2d45] flex flex-col items-center py-6 justify-between">
          <div className="flex flex-col items-center gap-6">
            <div
              title={prospectador}
              aria-label={`Prospectador: ${prospectador}`}
              className="w-8 h-8 bg-[#0f1623] border border-[#1e2d45] rounded-md flex items-center justify-center font-['Geist_Mono'] text-xs font-bold text-[#2563eb] tracking-widest"
            >
              {avatarInitials}
            </div>

            <nav className="flex flex-col gap-2">
              <button
                type="button"
                aria-label="Busca"
                onClick={() => setActiveView("search")}
                className={`${navItem} ${
                  activeView === "search" && !historyOpen
                    ? "bg-[#1d3a6e] text-[#60a5fa]"
                    : "text-[#4a5568] hover:text-[#8896ac] hover:bg-[#0f1623]"
                }`}
              >
                <Search className="w-4 h-4" />
              </button>
              <button
                type="button"
                aria-label="Lista Preferencial"
                onClick={() => setActiveView("selected")}
                className={`${navItem} ${
                  activeView === "selected"
                    ? "bg-[#1d3a6e] text-[#60a5fa]"
                    : "text-[#4a5568] hover:text-[#8896ac] hover:bg-[#0f1623]"
                }`}
              >
                <Star className="w-4 h-4" />
              </button>
              <button
                type="button"
                aria-label="Prospecções passadas"
                onClick={() => setActiveView("history")}
                className={`${navItem} ${
                  activeView === "history"
                    ? "bg-[#1d3a6e] text-[#60a5fa]"
                    : "text-[#4a5568] hover:text-[#8896ac] hover:bg-[#0f1623]"
                }`}
              >
                <Archive className="w-4 h-4" />
              </button>
              <button
                type="button"
                aria-label="Histórico rápido"
                onClick={() => setHistoryOpen(!historyOpen)}
                className={`${navItem} ${
                  historyOpen
                    ? "bg-[#1d3a6e] text-[#60a5fa]"
                    : "text-[#4a5568] hover:text-[#8896ac] hover:bg-[#0f1623]"
                }`}
              >
                <History className="w-4 h-4" />
              </button>
            </nav>
          </div>

          <button
            type="button"
            aria-label="Configurações"
            onClick={() => setSettingsOpen(true)}
            className={`${navItem} text-[#4a5568] hover:text-[#8896ac] hover:bg-[#0f1623]`}
          >
            <Settings className="w-4 h-4" />
          </button>
        </aside>

        <main className="flex-1 h-full flex flex-col bg-transparent min-w-0">
          <header className="h-12 bg-[#0c1118] border-b border-[#1e2d45] px-6 flex items-center justify-between">
            <div className="text-[13px] font-['Geist_Mono'] font-semibold text-[#8896ac] uppercase tracking-[0.12em]">
              {headerTitle}
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-[11px] text-[#4a5568] font-['JetBrains_Mono']">
                  operacional
                </span>
              </div>
            </div>
          </header>

          <div className="flex-1 flex min-h-0">
            <div className="flex-1 flex flex-col min-w-0">{children}</div>
            {historyOpen && activeView === "search" ? history : null}
          </div>
        </main>
      </div>

      {settingsOpen ? (
        <div className="fixed inset-0 z-20 flex items-center justify-center bg-[#0c1118]/80">
          <section className="w-[420px] rounded-lg border border-[#1e2d45] bg-[#0f1623]">
            <div className="h-10 px-4 border-b border-[#162035] flex items-center justify-between">
              <span className="text-[11px] font-semibold text-[#4a5568] uppercase tracking-[0.1em]">
                Sobre
              </span>
              <button
                type="button"
                aria-label="Fechar configurações"
                onClick={() => setSettingsOpen(false)}
                className="w-8 h-8 rounded-md flex items-center justify-center text-[#4a5568] hover:text-[#8896ac] hover:bg-[#0c1118] transition-colors duration-100"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <div className="text-base font-['Geist_Mono'] font-semibold text-[#e8edf5] uppercase tracking-[0.08em]">
                  Lead Scraper
                </div>
                <div className="mt-1 text-[12px] text-[#4a5568] font-['JetBrains_Mono']">
                  Desenvolvido por Eduardo
                </div>
              </div>

              <p className="text-[13px] leading-6 text-[#8896ac]">
                O objetivo do aplicativo é automatizar a prospecção de leads no
                Google Maps, qualificar empresas com score comercial e exportar
                uma planilha pronta para prospecção comercial.
              </p>

              <div className="border border-[#1e2d45] rounded-md bg-[#0c1118] px-4 py-3">
                <div className="text-[10px] text-[#4a5568] uppercase tracking-[0.08em]">
                  Backend local
                </div>
                <div className="mt-1 text-[12px] text-[#8896ac] font-['JetBrains_Mono']">
                  FastAPI em http://localhost:8000
                </div>
              </div>
            </div>
          </section>
        </div>
      ) : null}
    </div>
  );
}
