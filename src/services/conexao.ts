import { useQuery } from "@tanstack/react-query";
import { api } from "../api";

export function useConexaoLocal() {
  return useQuery({
    queryKey: ["health"],
    queryFn: () =>
      api
        .get<{ ok: boolean; db_ready: boolean }>("/health", { timeout: 4000 })
        .then((resposta) => resposta.data),
    refetchInterval: 15000,
    retry: false,
    staleTime: 5000,
  });
}
