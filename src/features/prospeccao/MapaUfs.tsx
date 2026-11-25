import { useRef, type KeyboardEvent } from "react";
import malha from "../../assets/malha-ufs-ibge.json";
import { UNIDADES_FEDERATIVAS, type UnidadeFederativa } from "./unidadesFederativas";

export function MapaUfs({
  selecionada,
  desabilitado,
  selecionar,
}: {
  selecionada: UnidadeFederativa;
  desabilitado: boolean;
  selecionar: (sigla: UnidadeFederativa["sigla"]) => void;
}) {
  const svg = useRef<SVGSVGElement>(null);

  function navegar(evento: KeyboardEvent<SVGGElement>, indice: number) {
    if (desabilitado) return;
    let destino: UnidadeFederativa | undefined;
    switch (evento.key) {
      case "Enter":
      case " ":
        destino = UNIDADES_FEDERATIVAS[indice];
        break;
      case "ArrowUp":
      case "ArrowLeft":
        destino = UNIDADES_FEDERATIVAS[indice - 1] ?? UNIDADES_FEDERATIVAS[UNIDADES_FEDERATIVAS.length - 1];
        break;
      case "ArrowDown":
      case "ArrowRight":
        destino = UNIDADES_FEDERATIVAS[indice + 1] ?? UNIDADES_FEDERATIVAS[0];
        break;
      case "Home":
        destino = UNIDADES_FEDERATIVAS[0];
        break;
      case "End":
        destino = UNIDADES_FEDERATIVAS[UNIDADES_FEDERATIVAS.length - 1];
        break;
      default:
        return;
    }
    if (!destino) return;
    evento.preventDefault();
    selecionar(destino.sigla);
    svg.current?.querySelector<SVGGElement>(`[data-uf="${destino.sigla}"]`)?.focus();
  }

  return (
    <figure className="mapa-ufs">
      <svg
        ref={svg}
        viewBox={`0 0 ${malha.largura} ${malha.altura}`}
        role="group"
        aria-label="Mapa das unidades federativas do Brasil"
        aria-disabled={desabilitado}
      >
        {UNIDADES_FEDERATIVAS.map((unidade, indice) => {
          const estaSelecionada = unidade.sigla === selecionada.sigla;
          const rotulo = `${unidade.nome} (${unidade.sigla})`;
          return (
            <g
              key={unidade.sigla}
              role="button"
              className="mapa-uf"
              data-uf={unidade.sigla}
              aria-label={rotulo}
              aria-pressed={estaSelecionada}
              tabIndex={!desabilitado && estaSelecionada ? 0 : -1}
              onClick={() => {
                if (!desabilitado) selecionar(unidade.sigla);
              }}
              onKeyDown={(evento) => navegar(evento, indice)}
            >
              <title>{rotulo}</title>
              <path d={malha.contornos[unidade.codigo]} fillRule="evenodd" />
              {unidade.sigla === "DF" && (
                <circle cx={malha.df.x} cy={malha.df.y} r={5} />
              )}
            </g>
          );
        })}
      </svg>
      <figcaption>
        <strong>{selecionada.nome} · {selecionada.sigla}</strong>
        <a
          href="https://servicodados.ibge.gov.br/api/docs/malhas?versao=4"
          target="_blank"
          rel="noreferrer"
        >
          IBGE · Malhas v4
        </a>
      </figcaption>
    </figure>
  );
}
