import { Download, Upload } from "lucide-react";
import { useAppStore } from "../../store";
import { Botao } from "../../components/ui/Botao";
import { Painel } from "../../components/ui/Painel";

export function Planilhas() {
  const navegar = useAppStore((estado) => estado.setActiveView);
  return <Painel titulo="Importação e exportação">
    <p className="texto-secundario">Importe uma planilha XLSX, CSV ou TSV pela lista de leads. Exporte a lista filtrada ou uma prospecção salva no histórico.</p>
    <div className="acoes">
      <Botao icone={Upload} onClick={() => navegar("selected")}>Importar pela lista de leads</Botao>
      <Botao icone={Download} onClick={() => navegar("history")}>Exportar pelo histórico</Botao>
    </div>
    <p className="texto-secundario">O assistente com prévia e mapeamento de colunas será entregue na fase 4.</p>
  </Painel>;
}
