import { useAppStore } from "../store";

function formatarDuracao(duracaoMs: number) {
  const segundos = Math.floor(duracaoMs / 1000);
  return segundos >= 60
    ? `${Math.floor(segundos / 60)} min ${segundos % 60} s`
    : `${segundos} s`;
}

export function StatusBar() {
  const status = useAppStore((estado) => estado.status);
  const processadas = useAppStore((estado) => estado.progress);
  const encontradas = useAppStore((estado) => estado.total);
  const mensagem = useAppStore((estado) => estado.log);
  const medicao = useAppStore((estado) => estado.medicaoColeta);
  const concluiuComAvisos = useAppStore((estado) => estado.concluiuComAvisos);

  if (status === "idle") return null;

  let titulo = "Extração em andamento";
  if (status === "done") {
    titulo = concluiuComAvisos ? "Extração concluída com avisos" : "Extração concluída";
  } else if (status === "error") {
    titulo = "Falha na extração";
  }

  return (
    <section
      className="painel status-prospeccao"
      aria-label="Andamento da extração"
      data-situacao={status}
    >
      <div role="status">
        <h2>{titulo}</h2>
        {mensagem && <p>{mensagem}</p>}
      </div>
      {encontradas > 0 && (
        <progress
          aria-label="Estabelecimentos processados"
          max={encontradas}
          value={processadas}
        />
      )}
      {medicao && (
        <dl className="medicao-prospeccao">
          <div><dt>Coletados</dt><dd>{medicao.coletados}</dd></div>
          <div><dt>Processados</dt><dd>{medicao.processados}</dd></div>
          <div><dt>Falhas</dt><dd>{medicao.falhas}</dd></div>
          <div><dt>Tempo decorrido</dt><dd>{formatarDuracao(medicao.duracaoMs)}</dd></div>
        </dl>
      )}
    </section>
  );
}
