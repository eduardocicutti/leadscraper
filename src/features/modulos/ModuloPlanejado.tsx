import { ArrowLeft, Construction } from "lucide-react";
import { NAVEGACAO } from "../../config/navegacao";
import { useAppStore } from "../../store";
import { Botao } from "../../components/ui/Botao";

export function ModuloPlanejado() {
  const tela = useAppStore((estado) => estado.activeView);
  const navegar = useAppStore((estado) => estado.setActiveView);
  const modulo = NAVEGACAO.find((item) => item.tela === tela);
  return (
    <section className="modulo-planejado painel">
      <Construction size={40} className="icone-destaque" aria-hidden="true" />
      <span className="selo">Fase {modulo?.fase}</span>
      <h2>{modulo?.titulo} em preparação</h2>
      <p>
        {modulo?.descricao} Este módulo será entregue na fase indicada no plano
        de implementação.
      </p>
      <Botao icone={ArrowLeft} onClick={() => navegar("search")}>
        Voltar à prospecção
      </Botao>
    </section>
  );
}
