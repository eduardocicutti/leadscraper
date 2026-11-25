import { useRef, useState, type ChangeEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { check } from "@tauri-apps/plugin-updater";
import { relaunch } from "@tauri-apps/plugin-process";
import {
  Code2,
  Database,
  Download,
  ExternalLink,
  HardDrive,
  RefreshCw,
  Upload,
} from "lucide-react";
import {
  api,
  type BackupRestoreResponse,
  type DiagnosticsResponse,
} from "../../api";
import { API_URL, PRODUTO } from "../../config/produto";
import { APP_VERSION } from "../../version";
import { useAppStore } from "../../store";
import { useConexaoLocal } from "../../services/conexao";
import { Painel } from "../../components/ui/Painel";
import { Botao } from "../../components/ui/Botao";
import { LogoAdapti } from "../../components/ui/LogoAdapti";

export function Sobre() {
  const cache = useQueryClient();
  const arquivoBackup = useRef<HTMLInputElement>(null);
  const [mensagem, alterarMensagem] = useState("");
  const status = useAppStore((estado) => estado.status);
  const resetar = useAppStore((estado) => estado.reset);
  const estaExecutando = status === "pending" || status === "running";
  const conexao = useConexaoLocal();
  const diagnostico = useQuery({
    queryKey: ["diagnostics"],
    queryFn: () =>
      api
        .get<DiagnosticsResponse>("/diagnostics")
        .then((resposta) => resposta.data),
    retry: false,
  });
  const backup = useMutation({
    mutationFn: () => api.get<Blob>("/backup", { responseType: "blob" }),
    onSuccess: (resposta) => {
      const url = URL.createObjectURL(resposta.data);
      const link = document.createElement("a");
      link.href = url;
      link.download = `plataforma-comercial-backup-${new Date().toISOString().slice(0, 10)}.db`;
      link.click();
      URL.revokeObjectURL(url);
      alterarMensagem("Backup baixado. Guarde o arquivo em um local seguro.");
    },
    onError: () =>
      alterarMensagem(
        "Não foi possível baixar o backup. Verifique a conexão com o backend.",
      ),
  });
  const restauracao = useMutation({
    mutationFn: async (arquivo: File) => {
      const conteudo = await new Promise<string>((resolver, rejeitar) => {
        const leitor = new FileReader();
        leitor.onload = () => resolver(String(leitor.result).split(",")[1]);
        leitor.onerror = () => rejeitar(leitor.error);
        leitor.readAsDataURL(arquivo);
      });
      return api.post<BackupRestoreResponse>("/restore", {
        filename: arquivo.name,
        content_base64: conteudo,
      });
    },
    onSuccess: () => {
      resetar();
      cache.clear();
      alterarMensagem("Backup restaurado. Os dados serão recarregados.");
    },
    onError: () =>
      alterarMensagem(
        "Não foi possível restaurar. Confira se o arquivo é um backup válido do aplicativo.",
      ),
  });
  const atualizacao = useMutation({
    mutationFn: async () => {
      if (
        !(window as Window & { __TAURI_INTERNALS__?: unknown })
          .__TAURI_INTERNALS__
      )
        return "A atualização automática está disponível no aplicativo instalado.";
      const novaVersao = await check();
      if (!novaVersao) return "Você está na versão mais recente.";
      alterarMensagem(`Baixando versão ${novaVersao.version}…`);
      await novaVersao.downloadAndInstall();
      await relaunch();
      return "Atualização instalada.";
    },
    onSuccess: alterarMensagem,
    onError: () =>
      alterarMensagem(
        "Não foi possível verificar atualizações. Tente novamente mais tarde.",
      ),
  });
  function escolherBackup(evento: ChangeEvent<HTMLInputElement>) {
    const arquivo = evento.target.files?.[0];
    evento.target.value = "";
    if (
      arquivo &&
      window.confirm(
        "Restaurar substituirá os dados atuais. O backend criará uma cópia de segurança antes da troca. Continuar?",
      )
    )
      restauracao.mutate(arquivo);
  }
  return (
    <div className="grade-sobre">
      <Painel className="apresentacao-produto">
        <LogoAdapti />
        <div>
          <div className="linha-titulo">
            <h2>{PRODUTO.nome}</h2>
            <span className="selo">v{APP_VERSION}</span>
          </div>
          <p className="texto-secundario">
            Desenvolvido por Eduardo · {PRODUTO.organizacao}
          </p>
          <p>
            Prospecção local, qualificação de empresas e organização do
            relacionamento comercial.
          </p>
        </div>
        <a
          className="botao"
          href={PRODUTO.repositorio}
          target="_blank"
          rel="noreferrer"
        >
          <ExternalLink size={18} />
          Ver repositório
        </a>
      </Painel>
      <Painel titulo="Backend local" icone={HardDrive}>
        <span className="selo">
          {conexao.isPending
            ? "Verificando"
            : conexao.isError
              ? "Sem conexão"
              : conexao.data?.db_ready
                ? "Conectado"
                : "Banco indisponível"}
        </span>
        <p className="caminho-tecnico">{API_URL}</p>
        <p className="texto-secundario">
          Executa as extrações e mantém os dados neste computador.
        </p>
        <Botao
          icone={RefreshCw}
          carregando={conexao.isFetching}
          onClick={() => void conexao.refetch()}
        >
          Testar conexão
        </Botao>
      </Painel>
      <Painel titulo="Banco de dados" icone={Database}>
        <p className="caminho-tecnico">
          {diagnostico.data?.db_path ||
            "Caminho disponível após carregar o diagnóstico."}
        </p>
        <p className="texto-secundario">
          Leads, mensagens e histórico ficam no SQLite local. A identidade
          técnica do aplicativo e o diretório original foram preservados.
        </p>
      </Painel>
      <Painel titulo="Diagnóstico do sistema" icone={Database}>
        {diagnostico.isPending ? (
          <p>Carregando diagnóstico…</p>
        ) : diagnostico.isError ? (
          <p role="alert">
            Diagnóstico indisponível. Inicie o backend e tente novamente.
          </p>
        ) : (
          <>
            <dl className="lista-diagnostico">
              <div>
                <dt>Prospecções</dt>
                <dd>{diagnostico.data.counts.history}</dd>
              </div>
              <div>
                <dt>Leads coletados</dt>
                <dd>{diagnostico.data.counts.leads}</dd>
              </div>
              <div>
                <dt>Lista preferencial</dt>
                <dd>{diagnostico.data.counts.selected_leads}</dd>
              </div>
              <div>
                <dt>Integridade</dt>
                <dd>{diagnostico.data.integrity_check}</dd>
              </div>
            </dl>
            <p className="caminho-tecnico">{diagnostico.data.db_path}</p>
          </>
        )}
        <Botao
          icone={RefreshCw}
          carregando={diagnostico.isFetching}
          onClick={() => void diagnostico.refetch()}
        >
          Atualizar diagnóstico
        </Botao>
      </Painel>
      <Painel titulo="Tecnologias utilizadas" icone={Code2}>
        <dl className="lista-diagnostico">
          <div>
            <dt>Interface</dt>
            <dd>React + Vite</dd>
          </div>
          <div>
            <dt>Backend</dt>
            <dd>FastAPI + Python</dd>
          </div>
          <div>
            <dt>Extração</dt>
            <dd>Playwright + Chromium</dd>
          </div>
          <div>
            <dt>Persistência atual</dt>
            <dd>SQLite local</dd>
          </div>
        </dl>
      </Painel>
      <Painel titulo="Backup" icone={Download}>
        <p className="texto-secundario">
          Salve uma cópia dos leads, mensagens e histórico. Termine a extração
          antes de restaurar.
        </p>
        <div className="acoes">
          <Botao
            variante="primario"
            icone={Download}
            carregando={backup.isPending}
            onClick={() => backup.mutate()}
          >
            Baixar backup
          </Botao>
          <Botao
            icone={Upload}
            disabled={estaExecutando || restauracao.isPending}
            onClick={() => arquivoBackup.current?.click()}
          >
            Restaurar backup
          </Botao>
        </div>
        <input
          ref={arquivoBackup}
          type="file"
          hidden
          accept=".db,.sqlite,.sqlite3"
          onChange={escolherBackup}
        />
      </Painel>
      <Painel titulo="Atualizações" icone={RefreshCw}>
        <p className="texto-secundario">
          Confira se há uma nova versão para o aplicativo instalado.
        </p>
        <Botao
          icone={RefreshCw}
          carregando={atualizacao.isPending}
          onClick={() => atualizacao.mutate()}
        >
          Verificar atualização
        </Botao>
      </Painel>
      {mensagem && (
        <p className="aviso" role="status">
          {mensagem}
        </p>
      )}
    </div>
  );
}
