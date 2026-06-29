import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { api, type StatusResponse } from "./api";
import { HistoryPanel } from "./components/HistoryPanel";
import { Layout } from "./components/Layout";
import { LeadsTable } from "./components/LeadsTable";
import { SearchPanel } from "./components/SearchPanel";
import { StatsRow } from "./components/StatsRow";
import { StatusBar } from "./components/StatusBar";
import { useAppStore } from "./store";

const queryClient = new QueryClient();

function Workspace() {
  const jobId = useAppStore((state) => state.jobId);
  const status = useAppStore((state) => state.status);
  const updateStatus = useAppStore((state) => state.updateStatus);

  const { data } = useQuery({
    queryKey: ["status", jobId],
    queryFn: () =>
      api.get<StatusResponse>(`/status/${jobId}`).then((response) => response.data),
    enabled: Boolean(jobId) && status !== "done" && status !== "error",
    refetchInterval: 1500,
  });

  useEffect(() => {
    if (data) {
      updateStatus(data);
    }
  }, [data, updateStatus]);

  return (
    <Layout history={<HistoryPanel />}>
      <SearchPanel />
      <div className="flex-1 min-h-0 p-6 flex flex-col gap-6 overflow-hidden">
        <StatusBar />
        <StatsRow />
        <LeadsTable />
      </div>
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
