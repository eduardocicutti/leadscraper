import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Botao } from "../../components/ui/Botao";
import {
  consultarCrm,
  ehAtividade,
  mensagemErroCrm,
  validarPaginaCrm,
  type Atividade,
} from "../../services/crm";
import { formatarDataCivil } from "./formatarDatasCrm";

export const SITUACOES_ATIVIDADE = [
  { valor: "pendente", titulo: "Pendentes" },
  { valor: "concluida", titulo: "Concluídas" },
  { valor: "cancelada", titulo: "Canceladas" },
] as const;

type FiltrosAtividades = {
  busca: string;
  prazo: string;
  dataReferencia: string;
  tipo: string;
  responsavel: string;
};

function ColunaAtividades({
  coluna,
  filtros,
  abrirEmpresa,
}: {
  coluna: (typeof SITUACOES_ATIVIDADE)[number];
  filtros: FiltrosAtividades;
  abrirEmpresa: (id: string) => void;
}) {
  const [pagina, definirPagina] = useState(1);
  const consulta = useQuery({
    queryKey: ["crm", "atividades", "quadro", coluna.valor, filtros, pagina],
    queryFn: () =>
      consultarCrm("atividades", validarPaginaCrm(ehAtividade), {
        ...filtros,
        situacao: coluna.valor,
        pagina,
      }),
  });
  const resultado = consulta.data;
  return (
    <section className="painel coluna-atividades" aria-label={coluna.titulo}>
      <h3>{coluna.titulo} {resultado && <span className="selo">{resultado.total}</span>}</h3>
      {consulta.isPending && <p role="status">Carregando atividades…</p>}
      {consulta.isError && (
        <div className="aviso" role="alert">
          {mensagemErroCrm(consulta.error)}
          <Botao onClick={() => void consulta.refetch()}>Tentar novamente</Botao>
        </div>
      )}
      {resultado?.total === 0 && <p>Nenhuma atividade nesta coluna.</p>}
      {resultado && resultado.total > 0 && (
        <>
          <ul className="cartoes-atividades">
            {resultado.itens.map((atividade: Atividade) => (
              <li key={atividade.id}>
                <strong>{atividade.titulo}</strong>
                <span>{atividade.empresaNome}</span>
                <span>{atividade.responsavel} · {formatarDataCivil(atividade.prazoData)}</span>
                <Botao onClick={() => abrirEmpresa(atividade.empresaId)}>
                  Ver na empresa
                </Botao>
              </li>
            ))}
          </ul>
          {resultado.total > resultado.tamanho && (
            <nav className="acoes" aria-label={`Paginação de atividades ${coluna.titulo.toLowerCase()}`}>
              <Botao disabled={pagina === 1} onClick={() => definirPagina(pagina - 1)}>
                Anterior
              </Botao>
              <Botao
                disabled={pagina * resultado.tamanho >= resultado.total}
                onClick={() => definirPagina(pagina + 1)}
              >
                Próxima
              </Botao>
            </nav>
          )}
        </>
      )}
    </section>
  );
}

export function QuadroAtividades({
  filtros,
  situacao,
  abrirEmpresa,
}: {
  filtros: FiltrosAtividades;
  situacao: string;
  abrirEmpresa: (id: string) => void;
}) {
  const colunas = SITUACOES_ATIVIDADE.filter(
    (coluna) => (!situacao || coluna.valor === situacao) &&
      (!filtros.prazo || coluna.valor === "pendente"),
  );
  return (
    <div className="quadro-atividades" aria-label="Quadro de atividades">
      {colunas.map((coluna) => (
        <ColunaAtividades
          key={`${coluna.valor}:${JSON.stringify(filtros)}`}
          coluna={coluna}
          filtros={filtros}
          abrirEmpresa={abrirEmpresa}
        />
      ))}
      {colunas.length === 0 && <p>Nenhuma atividade com os filtros selecionados.</p>}
    </div>
  );
}
