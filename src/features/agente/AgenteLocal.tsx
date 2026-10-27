import { Monitor, RefreshCw, Database, Activity } from "lucide-react";
import { useConexaoLocal } from "../../services/conexao";
import { useAppStore } from "../../store";
import { API_URL } from "../../config/produto";
import { Botao } from "../../components/ui/Botao";
import { Painel } from "../../components/ui/Painel";
import { StatusBar } from "../../components/StatusBar";

export function AgenteLocal() {
  const conexao = useConexaoLocal();
  const status = useAppStore((estado) => estado.status);
  const leads = useAppStore((estado) => estado.leads);
  const navegar = useAppStore((estado) => estado.setActiveView);
  return <div className="grade-configuracoes">
    <Painel titulo="Conexão local" icone={Monitor}><span className="selo">{conexao.isPending ? "Verificando" : conexao.isError ? "Sem conexão" : conexao.data?.db_ready ? "Backend conectado" : "Banco indisponível"}</span>
      <p className="caminho-tecnico">{API_URL}</p><p className="texto-secundario">O agente conectado ao CRM será entregue na fase 6. Esta tela acompanha o backend local atual.</p>
      <Botao icone={RefreshCw} carregando={conexao.isFetching} onClick={() => void conexao.refetch()}>Testar conexão</Botao>
    </Painel>
    <Painel titulo="Execução atual" icone={Activity}>{status === "idle" ? <p className="texto-secundario">Nenhuma extração acompanhada nesta sessão.</p> : <StatusBar />}
      <p>{leads.length} leads nos resultados da sessão</p><Botao onClick={() => navegar("search")}>Abrir prospecção</Botao>
    </Painel>
    <Painel titulo="Dados do dispositivo" icone={Database}><p className="texto-secundario">CPU, memória e heartbeat ainda não são medidos pelo backend atual.</p>
      <Botao onClick={() => navegar("about")}>Ver diagnóstico e backup</Botao>
    </Painel>
  </div>;
}
