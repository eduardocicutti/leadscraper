import { Botao } from "../../components/ui/Botao";

export function PaginacaoDetalhe({
  titulo,
  resumo,
  alterar,
  estaCarregando,
}: {
  titulo: string;
  resumo: { pagina: number; total: number; tamanho: number };
  alterar: (pagina: number) => void;
  estaCarregando: boolean;
}) {
  return (
    <nav className="crm-resumo" aria-label={`Paginação de ${titulo}`}>
      <small>
        {resumo.total} {resumo.total === 1 ? "registro" : "registros"} · página {resumo.pagina}
      </small>
      <div className="acoes">
        <Botao
          disabled={estaCarregando || resumo.pagina <= 1}
          onClick={() => alterar(resumo.pagina - 1)}
        >
          Anteriores ({titulo})
        </Botao>
        <Botao
          disabled={
            estaCarregando || resumo.pagina * resumo.tamanho >= resumo.total
          }
          onClick={() => alterar(resumo.pagina + 1)}
        >
          Próximos ({titulo})
        </Botao>
      </div>
    </nav>
  );
}
