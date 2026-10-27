import {
  Monitor,
  Moon,
  RotateCcw,
  SlidersHorizontal,
  Sun,
  Type,
} from "lucide-react";
import { usePreferencias } from "../../services/preferencias";
import { Botao } from "../../components/ui/Botao";
import { Painel } from "../../components/ui/Painel";

export function Configuracoes() {
  const preferencias = usePreferencias();
  return (
    <div className="grade-configuracoes">
      <Painel titulo="Aparência" icone={Monitor}>
        <p className="texto-secundario">
          Escolha o tema que fica mais confortável para trabalhar.
        </p>
        <div
          className="opcoes-tema"
          role="group"
          aria-label="Tema da interface"
        >
          <Botao
            icone={Moon}
            aria-pressed={preferencias.tema === "escuro"}
            onClick={() => preferencias.alterarTema("escuro")}
          >
            Escuro
          </Botao>
          <Botao
            icone={Sun}
            aria-pressed={preferencias.tema === "claro"}
            onClick={() => preferencias.alterarTema("claro")}
          >
            Claro
          </Botao>
        </div>
      </Painel>
      <Painel titulo="Densidade" icone={SlidersHorizontal}>
        <label className="campo">
          Espaçamento das tabelas
          <select
            value={preferencias.densidade}
            onChange={(evento) =>
              preferencias.alterarDensidade(
                evento.target.value === "compacta" ? "compacta" : "confortavel",
              )
            }
          >
            <option value="confortavel">Confortável</option>
            <option value="compacta">Compacta</option>
          </select>
        </label>
        <p className="texto-secundario">
          A densidade compacta reduz o espaçamento, preservando a leitura.
        </p>
      </Painel>
      <Painel titulo="Tamanho do texto" icone={Type}>
        <label className="campo">
          Escala da interface: {preferencias.escalaFonte}%
          <input
            type="range"
            min="100"
            max="125"
            step="5"
            value={preferencias.escalaFonte}
            onChange={(evento) =>
              preferencias.alterarEscala(Number(evento.target.value))
            }
          />
        </label>
        <p className="texto-secundario">
          O texto e os controles acompanham a escala selecionada.
        </p>
      </Painel>
      <Painel titulo="Preferências deste navegador">
        <p className="texto-secundario">
          As alterações são salvas automaticamente neste dispositivo. Restaurar
          o padrão não remove leads, histórico ou arquivos.
        </p>
        <Botao icone={RotateCcw} onClick={preferencias.restaurar}>
          Restaurar aparência padrão
        </Botao>
      </Painel>
    </div>
  );
}
