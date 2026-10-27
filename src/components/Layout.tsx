import { useEffect, useRef, useState, type ReactNode } from "react";
import { History, Menu, Monitor, Search, X, Layers, ChevronRight } from "lucide-react";
import { NAVEGACAO, type Tela } from "../config/navegacao";
import { PRODUTO } from "../config/produto";
import { useAppStore } from "../store";
import { usePreferencias } from "../services/preferencias";
import { useConexaoLocal } from "../services/conexao";
import { APP_TITLE, APP_VERSION } from "../version";
import { getInitials } from "../utils/initials";
import { Botao } from "./ui/Botao";

export function Layout({ children, history }: { children: ReactNode; history: ReactNode }) {
  const tela = useAppStore((estado) => estado.activeView);
  const navegar = useAppStore((estado) => estado.setActiveView);
  const historicoAberto = useAppStore((estado) => estado.historyOpen);
  const alterarHistorico = useAppStore((estado) => estado.setHistoryOpen);
  const prospectador = useAppStore((estado) => estado.prospectador);
  const status = useAppStore((estado) => estado.status);
  const preferencias = usePreferencias();
  const conexao = useConexaoLocal();
  const [menuAberto, alterarMenu] = useState(false);
  const [busca, alterarBusca] = useState("");
  const campoBusca = useRef<HTMLInputElement>(null);
  const estaOnline = !conexao.isError && conexao.data?.ok && conexao.data.db_ready;
  const pagina = NAVEGACAO.find((item) => item.tela === tela);
  const titulo = tela === "agent" ? "Agente local" : pagina?.titulo;
  const descricao = tela === "agent" ? "Conexão e acompanhamento da execução local." : pagina?.descricao;
  const itensEncontrados = busca.trim() ? NAVEGACAO.filter((item) => item.titulo.toLocaleLowerCase("pt-BR").includes(busca.trim().toLocaleLowerCase("pt-BR"))) : [];

  useEffect(() => {
    document.title = APP_TITLE;
    document.documentElement.dataset.tema = preferencias.tema;
    document.documentElement.dataset.densidade = preferencias.densidade;
    document.documentElement.style.fontSize = `${16 * preferencias.escalaFonte / 100}px`;
  }, [preferencias.tema, preferencias.densidade, preferencias.escalaFonte]);

  useEffect(() => {
    const focarBusca = (evento: KeyboardEvent) => {
      if ((evento.ctrlKey || evento.metaKey) && evento.key.toLowerCase() === "k") {
        evento.preventDefault(); campoBusca.current?.focus();
      }
      if (evento.key === "Escape") { alterarMenu(false); alterarBusca(""); }
    };
    document.addEventListener("keydown", focarBusca);
    return () => document.removeEventListener("keydown", focarBusca);
  }, []);

  function abrirTela(destino: Tela) {
    navegar(destino); alterarMenu(false); alterarBusca("");
    document.getElementById("conteudo-principal")?.focus({ preventScroll: true });
    window.scrollTo({ top: 0 });
  }

  return <div className="aplicacao">
    <a className="pular-conteudo" href="#conteudo-principal">Pular para o conteúdo</a>
    {menuAberto && <button className="fundo-menu" aria-label="Fechar menu" onClick={() => alterarMenu(false)} />}
    <aside className={`sidebar ${menuAberto ? "sidebar--aberta" : ""}`} aria-label="Navegação principal">
      <div className="marca"><Layers size={33} aria-hidden="true" /><div><strong>{PRODUTO.organizacao}</strong><span>{PRODUTO.nome}</span></div>
        <button className="botao-icone fechar-menu" aria-label="Fechar menu" onClick={() => alterarMenu(false)}><X size={20} /></button>
      </div>
      <nav className="menu-principal">
        {[0, 1, 2].map((grupo) => <div className="grupo-menu" key={grupo}>
          {NAVEGACAO.filter((item) => item.grupo === grupo).map(({ tela: destino, titulo: rotulo, icone: Icone, fase }) =>
            <button key={destino} className={`item-menu ${tela === destino ? "item-menu--ativo" : ""}`}
              aria-current={tela === destino ? "page" : undefined} onClick={() => abrirTela(destino)} title={fase ? `${rotulo} · fase ${fase}` : rotulo}>
              <Icone size={19} aria-hidden="true" /><span>{rotulo}</span>
            </button>)}
        </div>)}
      </nav>
      <section className="cartao-agente" aria-label="Estado do backend local">
        <div className="linha-agente"><span className={`ponto-status ${estaOnline ? "ponto-status--online" : ""}`} /><div><strong>Agente local</strong><span>{conexao.isPending ? "Verificando…" : estaOnline ? "Backend conectado" : "Sem conexão"}</span></div><small>v{APP_VERSION}</small></div>
        <div className="estado-agente"><Monitor size={16} aria-hidden="true" />{status === "running" || status === "pending" ? "Extração em andamento" : "Execução neste computador"}</div>
        <Botao icone={Monitor} onClick={() => abrirTela("agent")}>Ver agente</Botao>
      </section>
    </aside>
    <div className="area-aplicacao">
      <header className="cabecalho">
        <button className="botao-icone abrir-menu" aria-label="Abrir menu" aria-expanded={menuAberto} onClick={() => alterarMenu(true)}><Menu size={22} /></button>
        <div className="busca-cabecalho"><Search size={18} aria-hidden="true" />
          <input ref={campoBusca} aria-label="Buscar menu" placeholder="Buscar um menu…" value={busca} onChange={(evento) => alterarBusca(evento.target.value)}
            onKeyDown={(evento) => { if (evento.key === "Enter" && itensEncontrados[0]) abrirTela(itensEncontrados[0].tela); }} />
          <kbd>Ctrl K</kbd>
          {busca.trim() && <div className="resultados-menu" aria-label="Menus encontrados">
            {itensEncontrados.length ? itensEncontrados.map((item) => <button key={item.tela} onClick={() => abrirTela(item.tela)}><item.icone size={18} />{item.titulo}<ChevronRight size={16} /></button>) : <p>Nenhum menu encontrado.</p>}
          </div>}
        </div>
        <div className="perfil-local"><span className="avatar">{getInitials(prospectador)}</span><div><strong>{prospectador}</strong><small>Operador local</small></div></div>
      </header>
      <main id="conteudo-principal" tabIndex={-1} className="conteudo">
        <div className="titulo-pagina"><div><h1>{titulo}</h1><p>{descricao}</p></div>
          {tela === "search" && <Botao icone={History} aria-expanded={historicoAberto} onClick={() => alterarHistorico(!historicoAberto)}>Histórico rápido</Botao>}
        </div>
        <div className="area-conteudo"><div className="pagina">{children}</div>
          {historicoAberto && tela === "search" && <div className="historico-rapido"><Botao icone={X} onClick={() => alterarHistorico(false)}>Fechar histórico</Botao>{history}</div>}
        </div>
      </main>
    </div>
  </div>;
}
