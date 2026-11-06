import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { NAVEGACAO, type Tela } from "../../config/navegacao";
import { useAppStore } from "../../store";
import {
  consultarCrm,
  mensagemErroCrm,
  type Empresa,
  type PaginaCrm,
} from "../../services/crm";

export function BuscaGlobal({ navegar }: { navegar: (tela: Tela) => void }) {
  const [busca, definirBusca] = useState("");
  const [termo, definirTermo] = useState("");
  const [pagina, definirPagina] = useState(1);
  const campo = useRef<HTMLInputElement>(null);
  const abrirEmpresa = useAppStore((estado) => estado.abrirEmpresa);
  const menus = busca.trim()
    ? NAVEGACAO.filter((item) =>
        item.titulo
          .toLocaleLowerCase("pt-BR")
          .includes(busca.trim().toLocaleLowerCase("pt-BR")),
      )
    : [];
  useEffect(() => {
    const temporizador = window.setTimeout(() => {
      definirTermo(busca.trim());
      definirPagina(1);
    }, 300);
    return () => window.clearTimeout(temporizador);
  }, [busca]);
  useEffect(() => {
    function atalhos(evento: KeyboardEvent) {
      if (
        (evento.ctrlKey || evento.metaKey) &&
        evento.key.toLowerCase() === "k"
      ) {
        evento.preventDefault();
        campo.current?.focus();
      }
      if (evento.key === "Escape") definirBusca("");
    }
    document.addEventListener("keydown", atalhos);
    return () => document.removeEventListener("keydown", atalhos);
  }, []);
  const consulta = useQuery({
    queryKey: ["crm", "busca-global", termo, pagina],
    queryFn: () =>
      consultarCrm<PaginaCrm<Empresa>>("busca", { busca: termo, pagina }),
    enabled: termo.length >= 2 && busca.trim() === termo,
    retry: false,
  });
  function selecionarEmpresa(id: string) {
    definirBusca("");
    abrirEmpresa(id);
    document
      .getElementById("conteudo-principal")
      ?.focus({ preventScroll: true });
    window.scrollTo({ top: 0 });
  }
  const estaAtualizando = busca.trim() !== termo || consulta.isFetching;
  return (
    <div
      className="busca-cabecalho"
      onBlur={(evento) => {
        if (!evento.currentTarget.contains(evento.relatedTarget))
          definirBusca("");
      }}
    >
      <Search size={18} aria-hidden="true" />
      <input
        ref={campo}
        aria-label="Buscar no CRM e nos menus"
        placeholder="Buscar empresa, telefone, CNPJ ou menu…"
        value={busca}
        onChange={(evento) => definirBusca(evento.target.value)}
        onKeyDown={(evento) => {
          if (evento.key === "Enter") {
            if (menus[0]) {
              definirBusca("");
              navegar(menus[0].tela);
            } else if (!estaAtualizando && consulta.data?.itens[0])
              selecionarEmpresa(consulta.data.itens[0].id);
          }
        }}
      />
      <kbd>Ctrl K</kbd>
      {busca.trim() && (
        <div
          className="resultados-menu busca-global"
          aria-label="Resultados da busca"
        >
          <h2>Menus</h2>
          {menus.map((item) => (
            <button
              key={item.tela}
              onClick={() => {
                definirBusca("");
                navegar(item.tela);
              }}
            >
              <item.icone size={18} aria-hidden="true" />
              {item.titulo}
            </button>
          ))}
          {!menus.length && <p>Nenhum menu encontrado.</p>}
          <h2>Empresas e contatos</h2>
          {busca.trim().length < 2 ? (
            <p>Digite pelo menos 2 caracteres.</p>
          ) : estaAtualizando ? (
            <p role="status">Buscando…</p>
          ) : consulta.isError ? (
            <p role="alert">
              {mensagemErroCrm(consulta.error)}{" "}
              <button onClick={() => void consulta.refetch()}>
                Tentar novamente
              </button>
            </p>
          ) : (
            <>
              {consulta.data?.itens.map((empresa) => (
                <button
                  key={empresa.id}
                  onClick={() => selecionarEmpresa(empresa.id)}
                >
                  <span>
                    <strong>
                      {empresa.nome}
                      {empresa.arquivada ? " · Arquivada" : ""}
                    </strong>
                    <small>
                      {empresa.responsavel} ·{" "}
                      {empresa.qualificacaoSituacao || "Sem qualificação"}
                    </small>
                    <small>
                      Último contato:{" "}
                      {empresa.ultimoContatoEm
                        ? new Date(empresa.ultimoContatoEm).toLocaleString(
                            "pt-BR",
                            { timeZone: "America/Sao_Paulo" },
                          )
                        : "Não registrado"}
                    </small>
                  </span>
                </button>
              ))}
              {consulta.data?.total === 0 && <p>Nenhum cadastro encontrado.</p>}
              {consulta.data && consulta.data.total > 25 && (
                <div className="acoes">
                  <button
                    disabled={pagina === 1}
                    onClick={() => definirPagina(pagina - 1)}
                  >
                    Anterior
                  </button>
                  <span>Página {pagina}</span>
                  <button
                    disabled={pagina * 25 >= consulta.data.total}
                    onClick={() => definirPagina(pagina + 1)}
                  >
                    Próxima
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
