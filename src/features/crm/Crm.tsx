import { useEffect, useState, type FormEvent } from "react";
import { QualificacaoLead } from "./QualificacaoLead";
import { PaginacaoDetalhe } from "./PaginacaoDetalhe";
import { QuadroAtividades, SITUACOES_ATIVIDADE } from "./QuadroAtividades";
import { formatarDataCivil, formatarInstanteCrm } from "./formatarDatasCrm";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Building2,
  CalendarDays,
  Plus,
  Search,
  UsersRound,
} from "lucide-react";
import { Botao } from "../../components/ui/Botao";
import { useAppStore } from "../../store";
import {
  consultarCrm,
  ehAtividade,
  ehContato,
  ehDetalheEmpresa,
  ehEmpresa,
  empresasCandidatas,
  mensagemErroCrm,
  rotuloEmpresaCandidata,
  salvarCrm,
  validarPaginaCrm,
  type Atividade,
  type AtividadeEntrada,
  type Contato,
  type Empresa,
  type EmpresaCandidata,
  type EmpresaEntrada,
} from "../../services/crm";
import { urlHttp } from "../../utils/urlHttp";

type Modo = "empresas" | "contatos" | "atividades";

const TIPOS_ATIVIDADE: Record<Atividade["tipo"], string> = {
  lembrete: "Lembrete",
  tarefa: "Tarefa",
  ligacao: "Ligação",
  whatsapp: "WhatsApp",
  email: "E-mail",
  reuniao: "Reunião",
};

const ROTULOS_SITUACAO: Record<Atividade["situacao"], string> = {
  pendente: "Pendente",
  concluida: "Concluída",
  cancelada: "Cancelada",
};

function Campo({
  titulo,
  nome,
  valor,
  alterar,
  obrigatorio = false,
  tipo = "text",
  limite = 200,
}: {
  titulo: string;
  nome: string;
  valor: string;
  alterar: (valor: string) => void;
  obrigatorio?: boolean;
  tipo?: string;
  limite?: number;
}) {
  return (
    <label className="campo">
      <span>{titulo}</span>
      <input
        name={nome}
        type={tipo}
        value={valor}
        onChange={(evento) => alterar(evento.target.value)}
        required={obrigatorio}
        maxLength={limite}
      />
    </label>
  );
}

function FormularioEmpresa({
  empresa,
  concluir,
  cancelar,
}: {
  empresa?: Empresa;
  concluir: (id: string) => void;
  cancelar: () => void;
}) {
  const operador = useAppStore((estado) => estado.prospectador);
  const abrirEmpresa = useAppStore((estado) => estado.abrirEmpresa);
  const [valores, alterarValores] = useState<EmpresaEntrada>({
    nome: empresa?.nome || "",
    cnpj: empresa?.cnpj || "",
    segmento: empresa?.segmento || "",
    cidade: empresa?.cidade || "",
    uf: empresa?.uf || "",
    site: empresa?.site || "",
    urlMaps: empresa?.urlMaps || "",
    responsavel: empresa?.responsavel || operador || "Operador local",
    telefone: "",
  });
  const [erro, definirErro] = useState("");
  const [candidatas, definirCandidatas] = useState<EmpresaCandidata[]>([]);
  const [salvando, definirSalvando] = useState(false);
  const podeCadastrarSeparadamente =
    !empresa &&
    candidatas.length > 0 &&
    candidatas.every((candidata) => candidata.somenteTelefone);
  async function salvar(confirmarTelefoneCompartilhado = false) {
    definirErro("");
    definirCandidatas([]);
    definirSalvando(true);
    try {
      const resultado = await salvarCrm(
        empresa ? `empresas/${empresa.id}` : "empresas",
        ehEmpresa,
        empresa
          ? {
              ...valores,
              version: empresa.version,
              arquivada: Boolean(empresa.arquivada),
            }
          : confirmarTelefoneCompartilhado
            ? { ...valores, confirmarTelefoneCompartilhado }
            : valores,
        Boolean(empresa),
      );
      concluir(resultado.id);
    } catch (falha) {
      definirErro(mensagemErroCrm(falha));
      definirCandidatas(empresasCandidatas(falha));
    } finally {
      definirSalvando(false);
    }
  }
  return (
    <section className="painel crm-formulario">
      <h2>{empresa ? "Editar empresa" : "Nova empresa"}</h2>
      <p>
        O cadastro não registra uma abordagem. Telefones ficam vinculados aos
        contatos.
      </p>
      <form
        onSubmit={(evento) => {
          evento.preventDefault();
          void salvar();
        }}
        onChange={() => {
          if (candidatas.length > 0) {
            definirCandidatas([]);
            definirErro("");
          }
        }}
      >
        <fieldset className="crm-campos min-w-0" disabled={salvando}>
          {(
            [
              ["nome", "Nome da empresa", 200],
              ["cnpj", "CNPJ (opcional)", 30],
              ["segmento", "Segmento", 120],
              ["cidade", "Cidade", 120],
              ["uf", "UF", 2],
              ["site", "Site (https://…)", 1000],
              ["urlMaps", "URL de origem (Google Maps)", 2000],
              ["responsavel", "Responsável", 100],
            ] as const
          ).map(([nome, titulo, limite]) => (
            <Campo
              key={nome}
              titulo={titulo}
              nome={nome}
              valor={valores[nome] || ""}
              alterar={(valor) => alterarValores({ ...valores, [nome]: valor })}
              obrigatorio={nome === "nome" || nome === "responsavel"}
              limite={limite}
            />
          ))}
          {!empresa && (
            <Campo
              titulo="Telefone principal"
              nome="telefone"
              tipo="tel"
              limite={40}
              valor={valores.telefone}
              alterar={(telefone) => alterarValores({ ...valores, telefone })}
            />
          )}
        </fieldset>
        {erro && (
          <p className="aviso" role="alert">
            {erro}
          </p>
        )}
        {candidatas.length > 0 && (
          <div className="acoes">
            {candidatas.map((candidata) => (
              <Botao
                key={candidata.id}
                disabled={salvando}
                onClick={() => {
                  cancelar();
                  abrirEmpresa(candidata.id);
                }}
              >
                Abrir {rotuloEmpresaCandidata(candidata)}
              </Botao>
            ))}
            {podeCadastrarSeparadamente && (
              <Botao carregando={salvando} onClick={() => void salvar(true)}>
                Cadastrar empresa separadamente
              </Botao>
            )}
          </div>
        )}
        <div className="acoes">
          <Botao type="submit" variante="primario" carregando={salvando}>
            Salvar empresa
          </Botao>
          <Botao onClick={cancelar}>Cancelar</Botao>
        </div>
      </form>
    </section>
  );
}

function FormularioContato({
  empresaId,
  concluir,
  contato,
  cancelar,
}: {
  empresaId: string;
  concluir: () => void;
  contato?: Contato;
  cancelar?: () => void;
}) {
  const [valores, alterarValores] = useState({
    nome: contato?.nome || "",
    telefone: contato?.telefone || "",
    email: contato?.email || "",
    cargo: contato?.cargo || "",
  });
  const [erro, definirErro] = useState("");
  const [salvando, definirSalvando] = useState(false);
  async function salvar(evento: FormEvent) {
    evento.preventDefault();
    definirErro("");
    definirSalvando(true);
    try {
      await salvarCrm(
        `empresas/${empresaId}/contatos${contato ? `/${contato.id}` : ""}`,
        ehContato,
        contato ? { ...valores, version: contato.version } : valores,
        Boolean(contato),
      );
      alterarValores({ nome: "", telefone: "", email: "", cargo: "" });
      concluir();
    } catch (falha) {
      definirErro(mensagemErroCrm(falha));
    } finally {
      definirSalvando(false);
    }
  }
  return (
    <form onSubmit={(evento) => void salvar(evento)}>
      <h3>{contato ? "Editar contato" : "Adicionar contato"}</h3>
      <div className="crm-campos">
        {(
          [
            ["nome", "Nome do contato"],
            ["telefone", "Telefone com DDD"],
            ["email", "E-mail"],
            ["cargo", "Cargo"],
          ] as const
        ).map(([nome, titulo]) => (
          <Campo
            key={nome}
            nome={nome}
            titulo={titulo}
            valor={valores[nome]}
            obrigatorio={nome === "nome"}
            tipo={
              nome === "email" ? "email" : nome === "telefone" ? "tel" : "text"
            }
            alterar={(valor) => alterarValores({ ...valores, [nome]: valor })}
          />
        ))}
      </div>
      {erro && (
        <p role="alert" className="aviso">
          {erro}
        </p>
      )}
      <Botao type="submit" icone={Plus} carregando={salvando}>
        Salvar contato
      </Botao>
      {cancelar && <Botao onClick={cancelar}>Cancelar edição</Botao>}
    </form>
  );
}

function FormularioAtividade({
  empresaId,
  atividade,
  concluir,
  cancelar,
}: {
  empresaId: string;
  atividade?: Atividade;
  concluir: () => void;
  cancelar: () => void;
}) {
  const operador = useAppStore((estado) => estado.prospectador);
  const [valores, alterarValores] = useState<AtividadeEntrada>({
    titulo: atividade?.titulo || "",
    tipo: atividade?.tipo || "lembrete",
    situacao: atividade?.situacao || "pendente",
    descricao: atividade?.descricao || "",
    resultado: atividade?.resultado || "",
    responsavel: atividade?.responsavel || operador || "Operador local",
    prazoData: atividade?.prazoData || null,
  });
  const [erro, definirErro] = useState("");
  const [salvando, definirSalvando] = useState(false);
  async function salvar(evento: FormEvent) {
    evento.preventDefault();
    definirErro("");
    definirSalvando(true);
    try {
      await salvarCrm(
        `empresas/${empresaId}/atividades${atividade ? `/${atividade.id}` : ""}`,
        ehAtividade,
        atividade ? { ...valores, version: atividade.version } : valores,
        Boolean(atividade),
      );
      concluir();
    } catch (falha) {
      definirErro(mensagemErroCrm(falha));
    } finally {
      definirSalvando(false);
    }
  }
  return (
    <form onSubmit={(evento) => void salvar(evento)} className="crm-formulario">
      <h3>{atividade ? "Editar atividade" : "Nova atividade / lembrete"}</h3>
      <div className="crm-campos">
        <Campo
          titulo="Título da atividade"
          nome="titulo"
          valor={valores.titulo}
          obrigatorio
          alterar={(titulo) => alterarValores({ ...valores, titulo })}
        />
        <Campo
          titulo="Responsável pela atividade"
          nome="responsavel"
          valor={valores.responsavel}
          obrigatorio
          alterar={(responsavel) => alterarValores({ ...valores, responsavel })}
        />
        <label className="campo">
          <span>Tipo</span>
          <select
            value={valores.tipo}
            onChange={(evento) =>
              alterarValores({
                ...valores,
                tipo: evento.target.value as Atividade["tipo"],
              })
            }
          >
            {Object.entries(TIPOS_ATIVIDADE).map(([tipo, rotulo]) => (
              <option key={tipo} value={tipo}>
                {rotulo}
              </option>
            ))}
          </select>
        </label>
        <Campo
          titulo="Data de retorno"
          nome="prazoData"
          tipo="date"
          valor={valores.prazoData || ""}
          alterar={(prazoData) =>
            alterarValores({ ...valores, prazoData: prazoData || null })
          }
        />
        <label className="campo">
          <span>Situação</span>
          <select
            value={valores.situacao}
            onChange={(evento) =>
              alterarValores({
                ...valores,
                situacao: evento.target.value as Atividade["situacao"],
              })
            }
          >
            <option value="pendente">Pendente</option>
            <option value="concluida">Concluída</option>
            <option value="cancelada">Cancelada</option>
          </select>
        </label>
        <Campo
          titulo="Resultado (obrigatório ao concluir)"
          nome="resultado"
          valor={valores.resultado}
          obrigatorio={valores.situacao === "concluida"}
          alterar={(resultado) => alterarValores({ ...valores, resultado })}
          limite={2000}
        />
        <label className="campo">
          <span>Descrição</span>
          <textarea
            value={valores.descricao}
            maxLength={4000}
            onChange={(evento) =>
              alterarValores({ ...valores, descricao: evento.target.value })
            }
          />
        </label>
      </div>
      <p>
        Reagendar mantém a atividade pendente e registra a mudança na linha do
        tempo. Sem notificações automáticas nesta etapa.
      </p>
      {erro && (
        <p role="alert" className="aviso">
          {erro}
        </p>
      )}
      <div className="acoes">
        <Botao type="submit" variante="primario" carregando={salvando}>
          Salvar atividade
        </Botao>
        <Botao onClick={cancelar}>Cancelar</Botao>
      </div>
    </form>
  );
}

function Detalhes({
  empresaId,
  voltar,
}: {
  empresaId: string;
  voltar: () => void;
}) {
  const cliente = useQueryClient();
  const [paginaContatos, definirPaginaContatos] = useState(1);
  const [paginaAtividades, definirPaginaAtividades] = useState(1);
  const [paginaEventos, definirPaginaEventos] = useState(1);
  const consulta = useQuery({
    queryKey: [
      "crm",
      "empresa",
      empresaId,
      paginaContatos,
      paginaAtividades,
      paginaEventos,
    ],
    queryFn: () =>
      consultarCrm(`empresas/${empresaId}`, ehDetalheEmpresa, {
        paginaContatos,
        paginaAtividades,
        paginaEventos,
      }),
    placeholderData: (anterior) => anterior,
  });
  const [editando, definirEditando] = useState(false);
  const [contatoEditando, definirContatoEditando] = useState<
    Contato | undefined
  >();
  const [atividade, definirAtividade] = useState<Atividade | "nova" | null>(
    null,
  );
  const [erro, definirErro] = useState("");
  const [arquivando, definirArquivando] = useState(false);
  const empresa = consulta.data;
  const site = urlHttp(empresa?.site);
  const urlMaps = urlHttp(empresa?.urlMaps);
  function atualizar() {
    void cliente.invalidateQueries({ queryKey: ["crm"] });
  }
  async function arquivar() {
    if (!empresa) return;
    definirArquivando(true);
    definirErro("");
    try {
      const {
        id,
        version,
        nome,
        cnpj,
        segmento,
        cidade,
        uf,
        site,
        urlMaps,
        responsavel,
      } = empresa;
      await salvarCrm(
        `empresas/${id}`,
        ehEmpresa,
        {
          version,
          nome,
          cnpj: cnpj || "",
          segmento,
          cidade,
          uf,
          site,
          urlMaps,
          responsavel,
          arquivada: !empresa.arquivada,
        },
        true,
      );
      atualizar();
    } catch (falha) {
      definirErro(mensagemErroCrm(falha));
    } finally {
      definirArquivando(false);
    }
  }
  return (
    <div className="crm-espaco">
      <Botao icone={ArrowLeft} onClick={voltar}>
        Voltar à lista
      </Botao>
      {consulta.isPending ? (
        <p role="status">Carregando empresa…</p>
      ) : consulta.isError ? (
        <div role="alert" className="aviso">
          {mensagemErroCrm(consulta.error)}
          <Botao onClick={() => void consulta.refetch()}>
            Tentar novamente
          </Botao>
        </div>
      ) : (
        empresa && (
          <>
            {editando ? (
              <FormularioEmpresa
                empresa={empresa}
                concluir={() => {
                  definirEditando(false);
                  atualizar();
                }}
                cancelar={() => definirEditando(false)}
              />
            ) : (
              <section className="painel crm-resumo">
                <div>
                  <span className="selo">
                    {empresa.arquivada ? "Arquivada" : "Cadastro ativo"}
                  </span>
                  <h2>{empresa.nome}</h2>
                  <p>
                    {[empresa.segmento, empresa.cidade, empresa.uf]
                      .filter(Boolean)
                      .join(" · ") || "Localização não informada"}
                  </p>
                  <p>
                    Responsável: {empresa.responsavel} · CNPJ:{" "}
                    {empresa.cnpj || "não informado"}
                  </p>
                  {site && (
                    <a href={site} target="_blank" rel="noreferrer">
                      Visitar site
                    </a>
                  )}
                  {urlMaps && (
                    <p>
                      <a href={urlMaps} target="_blank" rel="noreferrer">
                        Abrir origem no Maps
                      </a>
                    </p>
                  )}
                </div>
                <div className="acoes">
                  <Botao
                    onClick={() => {
                      definirEditando(false);
                      definirAtividade(null);
                      definirContatoEditando(undefined);
                      void consulta.refetch();
                    }}
                  >
                    Recarregar cadastro
                  </Botao>
                  <Botao onClick={() => definirEditando(true)}>
                    Editar cadastro
                  </Botao>
                  <Botao
                    carregando={arquivando}
                    onClick={() => void arquivar()}
                  >
                    {empresa.arquivada
                      ? "Restaurar cadastro"
                      : "Arquivar cadastro"}
                  </Botao>
                </div>
              </section>
            )}
            {erro && (
              <p role="alert" className="aviso">
                {erro}
              </p>
            )}
            {empresa.qualificacao && (
              <QualificacaoLead
                key={`${empresa.id}:${empresa.qualificacao.version}`}
                empresaId={empresaId}
                qualificacao={empresa.qualificacao}
                atualizar={atualizar}
              />
            )}
            <div className="crm-colunas">
              <section className="painel crm-formulario">
                <h2>
                  <UsersRound size={21} aria-hidden="true" /> Contatos
                </h2>
                {empresa.contatos.length ? (
                  <ul className="crm-registros">
                    {empresa.contatos.map((contato) => (
                      <li key={contato.id}>
                        <strong>{contato.nome}</strong>
                        <span>{contato.cargo}</span>
                        <span>{contato.telefone || "Sem telefone"}</span>
                        <span>{contato.email}</span>
                        <Botao onClick={() => definirContatoEditando(contato)}>
                          Editar contato
                        </Botao>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p>Nenhum contato cadastrado.</p>
                )}
                <PaginacaoDetalhe
                  titulo="contatos"
                  resumo={empresa.paginacao.contatos}
                  alterar={definirPaginaContatos}
                  estaCarregando={consulta.isFetching}
                />
                <FormularioContato
                  key={contatoEditando?.id || "novo"}
                  empresaId={empresaId}
                  contato={contatoEditando}
                  concluir={() => {
                    definirContatoEditando(undefined);
                    atualizar();
                  }}
                  cancelar={
                    contatoEditando
                      ? () => definirContatoEditando(undefined)
                      : undefined
                  }
                />
              </section>
              <section className="painel crm-formulario">
                <div className="crm-resumo">
                  <h2>
                    <CalendarDays size={21} aria-hidden="true" /> Atividades e
                    retornos
                  </h2>
                  <Botao icone={Plus} onClick={() => definirAtividade("nova")}>
                    Nova atividade
                  </Botao>
                </div>
                {atividade ? (
                  <FormularioAtividade
                    key={atividade === "nova" ? "nova" : atividade.id}
                    empresaId={empresaId}
                    atividade={atividade === "nova" ? undefined : atividade}
                    concluir={() => {
                      definirAtividade(null);
                      atualizar();
                    }}
                    cancelar={() => definirAtividade(null)}
                  />
                ) : (
                  <ul className="crm-registros">
                    {empresa.atividades.map((item) => (
                      <li key={item.id}>
                        <strong>{item.titulo}</strong>
                        <span>
                          {TIPOS_ATIVIDADE[item.tipo]} · {ROTULOS_SITUACAO[item.situacao]} ·{" "}
                          {formatarDataCivil(item.prazoData)}
                        </span>
                        <span>{item.resultado}</span>
                        <Botao onClick={() => definirAtividade(item)}>
                          Editar atividade
                        </Botao>
                      </li>
                    ))}
                    {!empresa.atividades.length && (
                      <li>
                        Nenhuma atividade registrada. Uma coleta não comprova
                        abordagem.
                      </li>
                    )}
                  </ul>
                )}
                <PaginacaoDetalhe
                  titulo="atividades"
                  resumo={empresa.paginacao.atividades}
                  alterar={definirPaginaAtividades}
                  estaCarregando={consulta.isFetching}
                />
              </section>
            </div>
            <section className="painel crm-formulario">
              <h2>Linha do tempo</h2>
              <ol className="crm-registros">
                {empresa.eventos.map((evento) => (
                  <li key={evento.id}>
                    <strong>{evento.descricao}</strong>
                    <span>
                      {evento.autorNome} ·{" "}
                      {formatarInstanteCrm(evento.createdAt)}
                    </span>
                  </li>
                ))}
              </ol>
              <PaginacaoDetalhe
                titulo="eventos"
                resumo={empresa.paginacao.eventos}
                alterar={definirPaginaEventos}
                estaCarregando={consulta.isFetching}
              />
            </section>
          </>
        )
      )}
    </div>
  );
}

export function Crm({ modo }: { modo: Modo }) {
  const [busca, definirBusca] = useState("");
  const [termo, definirTermo] = useState("");
  const [pagina, definirPagina] = useState(1);
  const [arquivadas, definirArquivadas] = useState(false);
  const [situacao, definirSituacao] = useState("");
  const [prazo, definirPrazo] = useState("");
  const [qualificacao, definirQualificacao] = useState("");
  const [responsavel, definirResponsavel] = useState("");
  const [relacionamento, definirRelacionamento] = useState("");
  const [tipo, definirTipo] = useState("");
  const temFiltro = Boolean(
    termo ||
      arquivadas ||
      situacao ||
      prazo ||
      qualificacao ||
      responsavel.trim() ||
      relacionamento ||
      tipo,
  );
  const dataReferencia = new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/Sao_Paulo",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());
  const [criando, definirCriando] = useState(false);
  const empresaId = useAppStore((estado) => estado.empresaSelecionadaId);
  const definirEmpresaId = useAppStore(
    (estado) => estado.definirEmpresaSelecionada,
  );
  const cliente = useQueryClient();
  useEffect(() => {
    const temporizador = window.setTimeout(() => {
      definirTermo(busca);
      definirPagina(1);
    }, 300);
    return () => window.clearTimeout(temporizador);
  }, [busca]);
  const consulta = useQuery({
    queryKey: [
      "crm",
      modo,
      termo,
      pagina,
      arquivadas,
      situacao,
      prazo,
      dataReferencia,
      qualificacao,
      responsavel,
      relacionamento,
      tipo,
    ],
    queryFn: () =>
      consultarCrm(
        modo,
        validarPaginaCrm<Empresa | Contato>(modo === "empresas" ? ehEmpresa : ehContato),
        {
          busca: termo,
          pagina,
          ...(modo === "empresas"
            ? { arquivadas, qualificacao, relacionamento, responsavel }
            : {}),
        },
      ),
    enabled: !empresaId && modo !== "atividades",
  });
  if (empresaId)
    return (
      <Detalhes
        key={empresaId}
        empresaId={empresaId}
        voltar={() => definirEmpresaId(null)}
      />
    );
  if (criando && modo === "empresas")
    return (
      <FormularioEmpresa
        cancelar={() => definirCriando(false)}
        concluir={(id) => {
          definirCriando(false);
          definirEmpresaId(id);
          void cliente.invalidateQueries({ queryKey: ["crm"] });
        }}
      />
    );
  const titulo =
    modo === "empresas"
      ? "Empresas"
      : modo === "contatos"
        ? "Contatos"
        : "Atividades";
  const Icone =
    modo === "empresas"
      ? Building2
      : modo === "contatos"
        ? UsersRound
        : CalendarDays;
  return (
    <div className="crm-espaco">
      <div className="crm-resumo">
        <div>
          <p>
            {modo === "empresas"
              ? "Cadastre empresas, consulte contatos e acompanhe o relacionamento."
              : modo === "contatos"
                ? "Pessoas e canais de contato vinculados às empresas."
                : "Abra o cadastro da empresa para registrar ou editar uma atividade."}
          </p>
        </div>
        {modo === "empresas" && (
          <Botao
            variante="primario"
            icone={Plus}
            onClick={() => definirCriando(true)}
          >
            Nova empresa
          </Botao>
        )}
      </div>
      <section className="painel crm-formulario">
        <div className="crm-filtros">
          <label className="campo">
            <span>
              <Search size={16} aria-hidden="true" />{" "}
              {modo === "empresas"
                ? "Buscar por empresa, contato, cidade ou telefone"
                : modo === "contatos"
                  ? "Buscar por contato, empresa ou telefone"
                  : "Buscar por título da atividade ou empresa"}
            </span>
            <input
              type="search"
              value={busca}
              onChange={(evento) => definirBusca(evento.target.value)}
              placeholder="Digite para buscar…"
              maxLength={200}
            />
          </label>
          {modo !== "contatos" && (
            <Campo
              titulo="Filtrar responsável"
              nome="responsavel"
              valor={responsavel}
              limite={100}
              alterar={(valor) => {
                definirResponsavel(valor);
                definirPagina(1);
              }}
            />
          )}
          {modo === "empresas" && (
            <>
              <label className="campo">
                <span>Cadastros</span>
                <select
                  value={String(arquivadas)}
                  onChange={(evento) => {
                    definirArquivadas(evento.target.value === "true");
                    definirPagina(1);
                  }}
                >
                  <option value="false">Ativos</option>
                  <option value="true">Arquivados</option>
                </select>
              </label>
              <label className="campo">
                <span>Filtrar qualificação</span>
                <select
                  value={qualificacao}
                  onChange={(evento) => {
                    definirQualificacao(evento.target.value);
                    definirPagina(1);
                  }}
                >
                  <option value="">Todas</option>
                  <option value="novo">Novo</option>
                  <option value="analise">Em análise</option>
                  <option value="qualificado">Qualificado</option>
                  <option value="desqualificado">Desqualificado</option>
                </select>
              </label>
              <label className="campo">
                <span>Filtrar relacionamento</span>
                <select
                  value={relacionamento}
                  onChange={(evento) => {
                    definirRelacionamento(evento.target.value);
                    definirPagina(1);
                  }}
                >
                  <option value="">Todos</option>
                  <option value="prospectada">Já prospectadas</option>
                  <option value="semAbordagem">Sem abordagem</option>
                </select>
              </label>
            </>
          )}
          {modo === "atividades" && (
            <>
              <label className="campo">
                <span>Filtrar tipo de atividade</span>
                <select
                  value={tipo}
                  onChange={(evento) => {
                    definirTipo(evento.target.value);
                    definirPagina(1);
                  }}
                >
                  <option value="">Todos os tipos</option>
                  {Object.entries(TIPOS_ATIVIDADE).map(([valor, rotulo]) => (
                    <option key={valor} value={valor}>
                      {rotulo}
                    </option>
                  ))}
                </select>
              </label>
              <label className="campo">
                <span>Filtrar situação</span>
                <select
                  value={situacao}
                  onChange={(evento) => {
                    definirSituacao(evento.target.value);
                    definirPagina(1);
                  }}
                >
                  <option value="">Todas</option>
                  {SITUACOES_ATIVIDADE.map(({ valor, titulo }) => (
                    <option key={valor} value={valor}>{titulo}</option>
                  ))}
                </select>
              </label>
              <label className="campo">
                <span>Filtrar prazo</span>
                <select
                  value={prazo}
                  onChange={(evento) => {
                    definirPrazo(evento.target.value);
                    definirPagina(1);
                  }}
                >
                  <option value="">Todos os prazos</option>
                  <option value="vencidos">Vencidos</option>
                  <option value="hoje">Hoje</option>
                  <option value="proximos">Futuros</option>
                  <option value="semData">Sem data</option>
                </select>
              </label>
              <p>
                Filtros de prazo se aplicam às atividades pendentes. Hoje é{" "}
                {formatarDataCivil(dataReferencia)} no horário de São Paulo.
              </p>
            </>
          )}
        </div>
      </section>
      {modo === "atividades" ? (
        <QuadroAtividades
          filtros={{ busca: termo, prazo, dataReferencia, tipo, responsavel }}
          situacao={situacao}
          abrirEmpresa={definirEmpresaId}
        />
      ) : <section className="painel crm-formulario">
        <h2>
          <Icone size={22} aria-hidden="true" /> {titulo}{" "}
          {consulta.data && <span className="selo">{consulta.data.total}</span>}
        </h2>
        {consulta.isPending ? (
          <p role="status">Carregando registros…</p>
        ) : consulta.isError ? (
          <div role="alert" className="aviso">
            {mensagemErroCrm(consulta.error)}
            <Botao onClick={() => void consulta.refetch()}>
              Tentar novamente
            </Botao>
          </div>
        ) : (
          <>
            <div className="crm-tabela">
              <table>
                <caption className="sr-only">
                  Lista de {titulo.toLowerCase()}
                </caption>
                <thead>
                  <tr>
                    <th>Nome</th>
                    <th>{modo === "empresas" ? "Cidade / UF" : "Empresa"}</th>
                    <th>
                      {modo === "empresas" ? "Responsável" : "Telefone / e-mail"}
                    </th>
                    <th>Ação</th>
                  </tr>
                </thead>
                <tbody>
                  {consulta.data?.itens.map((item) => (
                    <tr key={item.id}>
                      <td>
                        <strong>
                          {item.nome}
                        </strong>
                        {"segmento" in item && <small>{item.segmento}</small>}
                      </td>
                      <td>
                        {"cidade" in item
                          ? [item.cidade, item.uf]
                              .filter(Boolean)
                              .join(" / ") || "—"
                          : item.empresaNome}
                      </td>
                      <td>
                        {"cidade" in item
                          ? item.responsavel
                          : [item.telefone, item.email]
                              .filter(Boolean)
                              .join(" · ") || "—"}
                      </td>
                      <td>
                        <Botao
                          onClick={() =>
                            definirEmpresaId(
                              "empresaId" in item ? item.empresaId : item.id,
                            )
                          }
                        >
                          Abrir empresa
                        </Botao>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {consulta.data?.total === 0 && (
              <p className="crm-vazio">
                {temFiltro
                  ? "Nenhum registro encontrado com os filtros selecionados."
                  : modo === "contatos"
                    ? "Nenhum contato cadastrado. Abra uma empresa para adicionar um contato."
                    : "Nenhuma empresa cadastrada."}
              </p>
            )}
            <div className="crm-resumo">
              <span>
                Página {pagina} de {Math.max(1, Math.ceil((consulta.data?.total ?? 0) / (consulta.data?.tamanho ?? 25)))}
              </span>
              <div className="acoes">
                <Botao
                  disabled={pagina <= 1}
                  onClick={() => definirPagina(pagina - 1)}
                >
                  Anterior
                </Botao>
                <Botao
                  disabled={pagina * 25 >= (consulta.data?.total ?? 0)}
                  onClick={() => definirPagina(pagina + 1)}
                >
                  Próxima
                </Botao>
              </div>
            </div>
          </>
        )}
      </section>}
    </div>
  );
}
