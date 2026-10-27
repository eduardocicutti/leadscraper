import type { ButtonHTMLAttributes } from "react";
import { LoaderCircle, type LucideIcon } from "lucide-react";

interface Propriedades extends ButtonHTMLAttributes<HTMLButtonElement> {
  variante?: "primario" | "secundario" | "discreto";
  icone?: LucideIcon;
  carregando?: boolean;
}

export function Botao({
  variante = "secundario",
  icone: Icone,
  carregando,
  children,
  className = "",
  disabled,
  ...propriedades
}: Propriedades) {
  return (
    <button
      type="button"
      {...propriedades}
      disabled={disabled || carregando}
      className={`botao botao--${variante} ${className}`}
      aria-busy={carregando || undefined}
    >
      {carregando ? (
        <LoaderCircle size={18} className="animate-spin" aria-hidden="true" />
      ) : Icone ? (
        <Icone size={18} aria-hidden="true" />
      ) : null}
      {children}
    </button>
  );
}
