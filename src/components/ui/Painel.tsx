import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";

export function Painel({ titulo, icone: Icone, children, className = "" }: {
  titulo?: string; icone?: LucideIcon; children: ReactNode; className?: string;
}) {
  return <section className={`painel ${className}`}>
    {titulo && <h2 className="painel-titulo">{Icone && <Icone size={21} aria-hidden="true" />}{titulo}</h2>}
    {children}
  </section>;
}
