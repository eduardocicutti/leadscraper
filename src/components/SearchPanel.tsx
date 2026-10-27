import { useState, type FormEvent } from "react";
import { Building2, MapPin, Layers, Play, UserRound, Database, Search } from "lucide-react";
import { api } from "../api";
import { useAppStore } from "../store";
import { Botao } from "./ui/Botao";

const PROSPECTADORES = ["Eduardo", "Murilo", "Sofia", "Ydian", "Gabriel"];
const ESTADOS = ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"];
const SEGMENTOS = ["Restaurantes", "Academias", "Salões de beleza", "Clínicas odontológicas", "Pet shops", "Supermercados"];

export function SearchPanel() {
  const status = useAppStore((estado) => estado.status);
  const iniciarJob = useAppStore((estado) => estado.setJob);
  const prospectador = useAppStore((estado) => estado.prospectador);
  const alterarProspectador = useAppStore((estado) => estado.setProspectador);
  const [segmento, alterarSegmento] = useState("");
  const [cidade, alterarCidade] = useState("");
  const [uf, alterarUf] = useState("ES");
  const [quantidade, alterarQuantidade] = useState("30");
  const [estaEnviando, alterarEnvio] = useState(false);
  const [erro, alterarErro] = useState("");
  const estaExecutando = estaEnviando || status === "running" || status === "pending";

  async function iniciarExtracao(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault(); alterarErro("");
    const total = Number(quantidade);
    if (!segmento.trim() || !cidade.trim() || !Number.isInteger(total) || total < 1 || total > 500) {
      alterarErro("Informe segmento, cidade e uma quantidade inteira de 1 a 500."); return;
    }
    const parametros = { segmento: segmento.trim(), cidade: cidade.trim(), estado: uf, prospectador };
    alterarEnvio(true);
    try {
      const resposta = await api.post<{ job_id: string }>("/scrape", { ...parametros, max_results: total });
      iniciarJob(resposta.data.job_id, parametros, total);
    } catch {
      alterarErro("Não foi possível iniciar. Verifique a conexão do backend na página Sobre e tente novamente. Seus campos foram mantidos.");
    } finally { alterarEnvio(false); }
  }

  return <form className="painel formulario-prospeccao" onSubmit={iniciarExtracao}>
    <div className="fonte-atual"><Search size={18} /><strong>Google Maps</strong><span className="selo">Fonte atual</span></div>
    <fieldset disabled={estaExecutando}>
      <legend><MapPin size={19} />Localização</legend>
      <div className="campos-localizacao"><label className="campo">Estado<select value={uf} onChange={(evento) => alterarUf(evento.target.value)}>{ESTADOS.map((estado) => <option key={estado}>{estado}</option>)}</select></label>
        <label className="campo">Cidade<input value={cidade} required placeholder="Ex.: São Mateus" onChange={(evento) => alterarCidade(evento.target.value)} /></label></div>
      <p className="ajuda-campo">O mapa interativo e o catálogo de municípios entram na fase 3.</p>
    </fieldset>
    <fieldset disabled={estaExecutando}><legend><Building2 size={19} />Segmento</legend>
      <label className="campo"><span className="sr-only">Segmento da busca</span><input required value={segmento} onChange={(evento) => alterarSegmento(evento.target.value)} placeholder="Buscar segmento…" /></label>
      <div className="chips" aria-label="Sugestões de segmentos">{SEGMENTOS.map((sugestao) => <button type="button" key={sugestao} aria-pressed={segmento === sugestao} onClick={() => alterarSegmento(sugestao)}>{sugestao}</button>)}</div>
    </fieldset>
    <fieldset disabled={estaExecutando}><legend><Layers size={19} />Quantidade</legend>
      <div className="presets" aria-label="Quantidade de leads">{[10, 30, 50, 100, 200].map((total) => <button type="button" key={total} aria-pressed={Number(quantidade) === total} onClick={() => alterarQuantidade(String(total))}>{total}</button>)}</div>
      <label className="campo">Quantidade personalizada<input type="number" min="1" max="500" step="1" required value={quantidade} onChange={(evento) => alterarQuantidade(evento.target.value)} /></label>
      <p className="ajuda-campo">Até 500 leads por busca. O total encontrado depende da região e do segmento.</p>
    </fieldset>
    <fieldset disabled={estaExecutando}><legend><UserRound size={19} />Responsável</legend>
      <label className="campo"><span className="sr-only">Prospectador</span><select value={prospectador} onChange={(evento) => alterarProspectador(evento.target.value)}>{PROSPECTADORES.map((nome) => <option key={nome}>{nome}</option>)}</select></label>
      <p className="ajuda-campo">Atribuição local. Contas e autenticação entram na fase 6.</p>
    </fieldset>
    <div className="resumo-fonte"><Database size={18} /><span>Extração e armazenamento neste computador</span></div>
    {erro && <p className="erro-formulario" role="alert">{erro}</p>}
    <Botao type="submit" variante="primario" icone={Play} carregando={estaExecutando} className="iniciar-extracao">{estaExecutando ? "Extração em andamento…" : "Iniciar extração"}</Botao>
  </form>;
}
