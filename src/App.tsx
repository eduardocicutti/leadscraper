import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
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

const queryClient = new QueryClient();

function Workspace() {
  const jobId = useAppStore((state) => state.jobId);
  const refreshJobId = useAppStore((state) => state.refreshJobId);
  const status = useAppStore((state) => state.status);
  const activeView = useAppStore((state) => state.activeView);
  const updateStatus = useAppStore((state) => state.updateStatus);

  const isPolling = status === "pending" || status === "running";

  const { data: scrapeData } = useQuery({
    queryKey: ["status", jobId],
    queryFn: () =>
      api.get<StatusResponse>(`/status/${jobId}`).then((response) => response.data),
    enabled: Boolean(jobId) && !jobId?.startsWith("history:") && isPolling,
    refetchInterval: 1500,
  });

  const { data: refreshData } = useQuery({
    queryKey: ["status", refreshJobId],
    queryFn: () =>
      api.get<StatusResponse>(`/status/${refreshJobId}`).then((response) => response.data),
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
      {activeView === "selected" ? (
        <SelectedLeadsPage />
      ) : activeView === "history" ? (
        <PastProspectionsPage />
      ) : (
        <>
          <SearchPanel />
          <div className="flex-1 min-h-0 p-6 flex flex-col gap-6 overflow-hidden">
            <StatusBar />
            <StatsRow />
            <LeadsTable />
          </div>
        </>
      )}
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
