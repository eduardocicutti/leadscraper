import {
  QueryClient,
  QueryClientProvider,
  useQuery,
} from "@tanstack/react-query";
import { useEffect } from "react";
import { api, type StatusResponse } from "./api";
import { HistoryPanel } from "./components/HistoryPanel";
import { Layout } from "./components/Layout";
import { LeadsTable } from "./components/LeadsTable";
import { PastProspectionsPage } from "./components/PastProspectionsPage";
import { SearchPanel } from "./components/SearchPanel";
import { SelectedLeadsPage } from "./components/SelectedLeadsPage";
import { StatsRow } from "./components/StatsRow";
import { StatusBar } from "./components/StatusBar";
import { useAppStore } from "./store";
import { Configuracoes } from "./features/configuracoes/Configuracoes";
import { Sobre } from "./features/sobre/Sobre";
import { AgenteLocal } from "./features/agente/AgenteLocal";
import { ModuloPlanejado } from "./features/modulos/ModuloPlanejado";
import { NAVEGACAO } from "./config/navegacao";
import { Botao } from "./components/ui/Botao";
import { Planilhas } from "./features/planilhas/Planilhas";
import { Crm } from "./features/crm/Crm";

const queryClient = new QueryClient();

function ConteudoPagina() {
  const tela = useAppStore((estado) => estado.activeView);
  if (NAVEGACAO.find((item) => item.tela === tela)?.fase)
    return <ModuloPlanejado />;
  switch (tela) {
    case "companies":
      return <Crm key="empresas" modo="empresas" />;
    case "contacts":
      return <Crm key="contatos" modo="contatos" />;
    case "activities":
      return <Crm key="atividades" modo="atividades" />;
    case "settings":
      return <Configuracoes />;
    case "about":
      return <Sobre />;
    case "agent":
      return <AgenteLocal />;
    case "spreadsheets":
      return <Planilhas />;
    case "selected":
      return <SelectedLeadsPage />;
    case "history":
      return <PastProspectionsPage />;
    default:
      return (
        <div className="prospeccao-layout">
          <SearchPanel />
          <div className="resultados-prospeccao legado">
            <StatusBar />
            <StatsRow />
            <LeadsTable />
          </div>
        </div>
      );
  }
}

function Workspace() {
  const jobId = useAppStore((state) => state.jobId);
  const refreshJobId = useAppStore((state) => state.refreshJobId);
  const status = useAppStore((state) => state.status);
  const navegar = useAppStore((estado) => estado.setActiveView);
  const updateStatus = useAppStore((state) => state.updateStatus);

  const isPolling = status === "pending" || status === "running";

  const {
    data: scrapeData,
    isError: erroExtracao,
    refetch: consultarExtracao,
  } = useQuery({
    queryKey: ["status", jobId],
    queryFn: ({ signal }) =>
      api
        .get<StatusResponse>(`/status/${jobId}`, {
          params: { somenteProgresso: true },
          signal,
        })
        .then((response) => response.data),
    enabled: Boolean(jobId) && !jobId?.startsWith("history:") && isPolling,
    refetchInterval: 1500,
  });

  const {
    data: refreshData,
    isError: erroReleitura,
    refetch: consultarReleitura,
  } = useQuery({
    queryKey: ["status", refreshJobId],
    queryFn: () =>
      api
        .get<StatusResponse>(`/status/${refreshJobId}`)
        .then((response) => response.data),
    enabled: Boolean(refreshJobId) && isPolling,
    refetchInterval: 1500,
  });

  useEffect(() => {
    if (scrapeData) {
      updateStatus(scrapeData);
    }
  }, [scrapeData, updateStatus]);

  useEffect(() => {
    if (refreshData) {
      updateStatus(refreshData);
    }
  }, [refreshData, updateStatus]);

  return (
    <Layout history={<HistoryPanel />}>
      {(erroExtracao || erroReleitura) && isPolling && (
        <div className="aviso" role="alert">
          Não foi possível acompanhar a execução. Os resultados já salvos
          continuam no histórico.
          <Botao
            onClick={() =>
              void (refreshJobId ? consultarReleitura() : consultarExtracao())
            }
          >
            Consultar novamente
          </Botao>
          <Botao onClick={() => navegar("history")}>Abrir histórico</Botao>
        </div>
      )}
      <ConteudoPagina />
    </Layout>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Workspace />
    </QueryClientProvider>
  );
}
