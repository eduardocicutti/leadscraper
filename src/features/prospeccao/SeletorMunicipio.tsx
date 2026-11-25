import { useId, useState, type KeyboardEvent } from "react";
import type { Municipio } from "../../services/prospeccao";

const LIMITE_SUGESTOES = 40;

function normalizarBusca(valor: string): string {
  return valor
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .trim()
    .toLocaleLowerCase("pt-BR");
}

export function SeletorMunicipio({
  municipios,
  selecionado,
  desabilitado,
  selecionar,
}: {
  municipios: Municipio[];
  selecionado: Municipio | null;
  desabilitado: boolean;
  selecionar: (municipio: Municipio | null) => void;
}) {
  const listaId = useId();
  const campoId = useId();
  const [busca, definirBusca] = useState("");
  const [estaAberto, definirAbertura] = useState(false);
  const [indiceAtivo, definirIndiceAtivo] = useState(-1);
  const termo = selecionado ? "" : normalizarBusca(busca);
  const resultados = municipios.filter(
    (municipio) =>
      normalizarBusca(municipio.nome).includes(termo) ||
      String(municipio.codigo).startsWith(termo),
  );
  const opcoes = resultados.slice(0, LIMITE_SUGESTOES);
  const codigoAtivo = opcoes[indiceAtivo]?.codigo;
  const mostraOpcoes = estaAberto && !desabilitado;

  function fecharOpcoes() {
    definirAbertura(false);
    definirIndiceAtivo(-1);
  }

  function selecionarMunicipio(municipio: Municipio) {
    selecionar(municipio);
    definirBusca(municipio.nome);
    fecharOpcoes();
  }

  function navegar(evento: KeyboardEvent<HTMLInputElement>) {
    if (evento.key === "Escape" && mostraOpcoes) {
      evento.stopPropagation();
      fecharOpcoes();
      return;
    }
    if (evento.key === "ArrowDown" || evento.key === "ArrowUp") {
      evento.preventDefault();
      definirAbertura(true);
      const direcao = evento.key === "ArrowDown" ? 1 : -1;
      const proximoIndice = Math.max(0, Math.min(opcoes.length - 1, indiceAtivo + direcao));
      definirIndiceAtivo(proximoIndice);
      const codigo = opcoes[proximoIndice]?.codigo;
      if (codigo) {
        requestAnimationFrame(() =>
          document.getElementById(`${listaId}-${codigo}`)?.scrollIntoView({ block: "nearest" }),
        );
      }
      return;
    }
    if (evento.key === "Enter" && mostraOpcoes) {
      evento.preventDefault();
      const municipio = opcoes[indiceAtivo] ?? (opcoes.length === 1 ? opcoes[0] : undefined);
      if (municipio) selecionarMunicipio(municipio);
    }
  }

  return (
    <div className="seletor-municipio">
      <label className="campo" htmlFor={campoId}>
        Município
        <input
          id={campoId}
          role="combobox"
          aria-label="Buscar município"
          aria-autocomplete="list"
          aria-haspopup="listbox"
          aria-expanded={mostraOpcoes}
          aria-controls={mostraOpcoes ? listaId : undefined}
          aria-activedescendant={
            mostraOpcoes && codigoAtivo ? `${listaId}-${codigoAtivo}` : undefined
          }
          type="text"
          autoComplete="off"
          placeholder="Nome ou código IBGE"
          disabled={desabilitado}
          value={selecionado?.nome ?? busca}
          onFocus={() => definirAbertura(true)}
          onClick={() => definirAbertura(true)}
          onBlur={fecharOpcoes}
          onChange={(evento) => {
            selecionar(null);
            definirBusca(evento.target.value);
            definirAbertura(true);
            definirIndiceAtivo(-1);
          }}
          onKeyDown={navegar}
        />
      </label>
      {mostraOpcoes && (
        <div className="opcoes-municipio">
          <ul id={listaId} role="listbox" aria-label="Municípios">
            {opcoes.map((municipio, indice) => (
              <li
                id={`${listaId}-${municipio.codigo}`}
                key={municipio.codigo}
                role="option"
                aria-selected={indice === indiceAtivo || (indiceAtivo < 0 && selecionado?.codigo === municipio.codigo)}
                onMouseDown={(evento) => evento.preventDefault()}
                onClick={() => selecionarMunicipio(municipio)}
              >
                <span>{municipio.nome}</span>
                <small>{municipio.codigo}</small>
              </li>
            ))}
          </ul>
          {opcoes.length === 0 && <p role="status">Nenhum município encontrado.</p>}
          {resultados.length > LIMITE_SUGESTOES && (
            <p>Digite parte do nome para filtrar os {resultados.length} municípios.</p>
          )}
        </div>
      )}
    </div>
  );
}
