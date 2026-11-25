import { useEffect, useRef, useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Building2, Database, Layers, MapPin, Play, Search, UserRound } from "lucide-react";
import { MapaUfs } from "../features/prospeccao/MapaUfs";
import { SeletorMunicipio } from "../features/prospeccao/SeletorMunicipio";
import { UNIDADES_FEDERATIVAS, type UnidadeFederativa } from "../features/prospeccao/unidadesFederativas";
import {
  atualizarCatalogo,
  consultarMunicipios,
  criarProspeccao,
  type Municipio,
  type ParametrosProspeccao,
} from "../services/prospeccao";
import { useAppStore } from "../store";
import { Botao } from "./ui/Botao";

const PROSPECTADORES = ["Eduardo", "Murilo", "Sofia", "Ydian", "Gabriel"];
const SEGMENTOS = [
  "Restaurantes", "Academias", "Salões de beleza", "Clínicas odontológicas",
  "Pet shops", "Supermercados",
];
const QUANTIDADES_RAPIDAS = [25, 50, 100, 200];
const QUANTIDADE_MINIMA = 1;
const QUANTIDADE_MAXIMA = 500;
const LISTA_UFS: readonly UnidadeFederativa[] = UNIDADES_FEDERATIVAS;
const UF_INICIAL = LISTA_UFS.find((item) => item.sigla === "ES") ?? UNIDADES_FEDERATIVAS[0];
const CHAVE_CATALOGO = ["prospeccao", "municipios"] as const;

interface RevisaoProspeccao {
  parametros: ParametrosProspeccao;
  cidade: string;
}

export function SearchPanel() {
  const status = useAppStore((estado) => estado.status);
  const iniciarJob = useAppStore((estado) => estado.setJob);
  const prospectador = useAppStore((estado) => estado.prospectador);
  const alterarProspectador = useAppStore((estado) => estado.setProspectador);
  const [segmento, alterarSegmento] = useState("");
  const [unidade, alterarUnidade] = useState<UnidadeFederativa>(UF_INICIAL);
  const uf = unidade.sigla;
  const [municipio, alterarMunicipio] = useState<Municipio | null>(null);
  const [quantidade, alterarQuantidade] = useState("25");
  const [revisao, alterarRevisao] = useState<RevisaoProspeccao | null>(null);
  const [erro, alterarErro] = useState("");
  const tituloRevisao = useRef<HTMLHeadingElement>(null);
  const botaoRevisar = useRef<HTMLButtonElement>(null);
  const enviando = useRef(false);
  const cliente = useQueryClient();
  const catalogo = useQuery({
    queryKey: [...CHAVE_CATALOGO, uf],
    queryFn: ({ signal }) => consultarMunicipios(uf, signal),
    staleTime: Infinity,
    retry: false,
  });
  const atualizacao = useMutation({
    mutationFn: atualizarCatalogo,
    onSuccess: () => cliente.invalidateQueries({ queryKey: CHAVE_CATALOGO }),
  });
  const extracao = useMutation({
    mutationFn: criarProspeccao,
  });
  const estaExecutando = extracao.isPending || status === "running" || status === "pending";
  const estaEditavel = !estaExecutando && revisao === null;
  const total = Number(quantidade);
  const quantidadeValida = Number.isInteger(total) && total >= QUANTIDADE_MINIMA && total <= QUANTIDADE_MAXIMA;
  const versaoCatalogo = catalogo.data?.versao;

  useEffect(() => {
    if (revisao) tituloRevisao.current?.focus();
  }, [revisao]);

  function selecionarUf(sigla: string) {
    const escolhida = LISTA_UFS.find((item) => item.sigla === sigla);
    if (!escolhida || escolhida.sigla === uf) return;
    alterarUnidade(escolhida);
    alterarMunicipio(null);
    alterarErro("");
  }

  function revisarExtracao(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    if (!estaEditavel) return;
    alterarErro("");
    const segmentoLimpo = segmento.trim();
    if (!segmentoLimpo) {
      alterarErro("Informe o segmento da busca.");
      return;
    }
    const municipioAtual = catalogo.data?.itens.find((item) => item.codigo === municipio?.codigo);
    if (!municipioAtual) {
      alterarErro("Escolha um município nas sugestões da UF selecionada.");
      return;
    }
    if (!quantidadeValida) {
      alterarErro("Informe uma quantidade inteira de 1 a 500.");
      return;
    }
    alterarRevisao({
      cidade: municipioAtual.nome,
      parametros: {
        segmento: segmentoLimpo,
        estado: uf,
        municipioCodigo: municipioAtual.codigo,
        max_results: total,
        prospectador,
      },
    });
  }

  function voltarEdicao() {
    alterarRevisao(null);
    alterarErro("");
    requestAnimationFrame(() => botaoRevisar.current?.focus());
  }

  async function confirmarExtracao() {
    if (!revisao || estaExecutando || enviando.current) return;
    enviando.current = true;
    alterarErro("");
    try {
      const { parametros, cidade } = revisao;
      const jobId = await extracao.mutateAsync(parametros);
      iniciarJob(jobId, {
        segmento: parametros.segmento,
        cidade,
        estado: parametros.estado,
        prospectador: parametros.prospectador,
        municipioCodigo: parametros.municipioCodigo,
      }, parametros.max_results);
      alterarRevisao(null);
    } catch {
      alterarErro("Não foi possível iniciar a extração. Confira a conexão e tente novamente. A seleção foi mantida.");
    } finally {
      enviando.current = false;
    }
  }

  return (
    <form className="painel formulario-prospeccao" onSubmit={revisarExtracao}>
      <div className="fonte-atual">
        <Search size={18} aria-hidden="true" />
        <strong>Google Maps</strong>
        <span className="selo">Fonte atual</span>
      </div>
      <fieldset disabled={!estaEditavel}>
        <legend>
          <MapPin size={19} aria-hidden="true" />
          Localização
        </legend>
        <label className="campo">
          Estado
          <select
            value={uf}
            onChange={(evento) => selecionarUf(evento.target.value)}
          >
            {LISTA_UFS.map((item) => (
              <option key={item.sigla} value={item.sigla}>
                {item.nome} ({item.sigla})
              </option>
            ))}
          </select>
        </label>
        <SeletorMunicipio
          key={uf}
          municipios={catalogo.data?.itens ?? []}
          selecionado={municipio}
          desabilitado={!estaEditavel || !catalogo.data?.itens.length}
          selecionar={alterarMunicipio}
        />
        {catalogo.isPending && <p className="ajuda-campo" role="status">Carregando municípios…</p>}
        {catalogo.isError && (
          <div className="ajuda-campo" role="alert">
            {catalogo.data ? "Não foi possível atualizar a lista. O catálogo anterior continua disponível." : "Catálogo indisponível. Verifique a conexão com o agente local."}{" "}
            <Botao variante="discreto" onClick={() => void catalogo.refetch()}>
              Consultar novamente
            </Botao>
          </div>
        )}
        {catalogo.data?.itens.length === 0 && !catalogo.isError && (
          <p className="ajuda-campo" role="status">Nenhum município disponível nesta UF.</p>
        )}
        <div className="catalogo-municipios">
          {versaoCatalogo && (
            <span title={versaoCatalogo}>Catálogo IBGE · {versaoCatalogo.replace(/^ibge-/, "").slice(0, 8)}</span>
          )}
          <Botao
            variante="discreto"
            carregando={atualizacao.isPending}
            onClick={() => atualizacao.mutate()}
          >
            Atualizar catálogo
          </Botao>
        </div>
        {atualizacao.isError && (
          <p className="ajuda-campo" role="alert">
            Falha ao atualizar. A última versão válida do catálogo foi preservada.
          </p>
        )}
        {atualizacao.isSuccess && !catalogo.isError && (
          <p className="ajuda-campo" role="status">Atualização do catálogo concluída.</p>
        )}
      </fieldset>
      <MapaUfs selecionada={unidade} desabilitado={!estaEditavel} selecionar={selecionarUf} />
      <fieldset disabled={!estaEditavel}>
        <legend>
          <Building2 size={19} aria-hidden="true" />
          Segmento
        </legend>
        <label className="campo">
          <span className="sr-only">Segmento da busca</span>
          <input
            required
            value={segmento}
            maxLength={120}
            onChange={(evento) => alterarSegmento(evento.target.value)}
            placeholder="Buscar segmento…"
          />
        </label>
        <div className="chips" aria-label="Sugestões de segmentos">
          {SEGMENTOS.map((sugestao) => (
            <button
              type="button"
              key={sugestao}
              aria-pressed={segmento === sugestao}
              onClick={() => alterarSegmento(sugestao)}
            >
              {sugestao}
            </button>
          ))}
        </div>
      </fieldset>
      <fieldset disabled={!estaEditavel}>
        <legend>
          <Layers size={19} aria-hidden="true" />
          Quantidade
        </legend>
        <div className="presets" aria-label="Quantidade de leads">
          {QUANTIDADES_RAPIDAS.map((valor) => (
            <button
              type="button"
              key={valor}
              aria-pressed={total === valor}
              onClick={() => alterarQuantidade(String(valor))}
            >
              {valor}
            </button>
          ))}
        </div>
        <label className="campo">
          Quantidade personalizada
          <input
            type="number"
            min={QUANTIDADE_MINIMA}
            max={QUANTIDADE_MAXIMA}
            step="1"
            required
            value={quantidade}
            onChange={(evento) => alterarQuantidade(evento.target.value)}
          />
        </label>
        <div className="quantidade-prospeccao">
          <input
            type="range"
            min={QUANTIDADE_MINIMA}
            max={QUANTIDADE_MAXIMA}
            step="1"
            aria-label="Ajustar quantidade"
            value={quantidadeValida ? total : QUANTIDADE_MINIMA}
            onChange={(evento) => alterarQuantidade(evento.target.value)}
          />
          <span>{QUANTIDADE_MINIMA}</span>
          <span>{QUANTIDADE_MAXIMA}</span>
        </div>
        <p className="ajuda-campo">O total encontrado depende da região e do segmento.</p>
      </fieldset>
      <fieldset disabled={!estaEditavel}>
        <legend>
          <UserRound size={19} aria-hidden="true" />
          Responsável
        </legend>
        <label className="campo">
          <span className="sr-only">Prospectador</span>
          <select
            value={prospectador}
            onChange={(evento) => alterarProspectador(evento.target.value)}
          >
            {PROSPECTADORES.map((nome) => (
              <option key={nome}>{nome}</option>
            ))}
          </select>
        </label>
        <p className="ajuda-campo">Atribuição local.</p>
      </fieldset>
      <div className="resumo-fonte">
        <Database size={18} aria-hidden="true" />
        <span>Extração e armazenamento neste computador</span>
      </div>
      {erro && <p className="erro-formulario" role="alert">{erro}</p>}
      {revisao ? (
        <section className="revisao-prospeccao" aria-labelledby="titulo-revisao-prospeccao">
          <h2 ref={tituloRevisao} tabIndex={-1} id="titulo-revisao-prospeccao">Revisão da extração</h2>
          <dl>
            <div><dt>Localização</dt><dd>{revisao.cidade} · {revisao.parametros.estado}</dd></div>
            <div><dt>Segmento</dt><dd>{revisao.parametros.segmento}</dd></div>
            <div><dt>Quantidade solicitada</dt><dd>{revisao.parametros.max_results}</dd></div>
          </dl>
          <div className="acoes">
            <Botao disabled={estaExecutando} onClick={voltarEdicao}>Voltar e editar</Botao>
            <Botao
              variante="primario"
              icone={Play}
              carregando={estaExecutando}
              onClick={() => void confirmarExtracao()}
            >
              Iniciar extração
            </Botao>
          </div>
        </section>
      ) : (
        <Botao
          type="submit"
          variante="primario"
          icone={Play}
          carregando={estaExecutando}
          className="iniciar-extracao"
        >
          {estaExecutando ? "Extração em andamento…" : "Revisar extração"}
        </Botao>
      )}
    </form>
  );
}
