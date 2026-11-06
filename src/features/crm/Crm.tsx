import { useEffect, useState, type FormEvent } from "react";
import { QualificacaoLead } from "./QualificacaoLead";
import { PaginacaoDetalhe } from "./PaginacaoDetalhe";
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
  mensagemErroCrm,
  salvarCrm,
  type Atividade,
  type AtividadeEntrada,
  type Contato,
  type DetalheEmpresa,
  type Empresa,
  type EmpresaEntrada,
  type PaginaCrm,
} from "../../services/crm";

type Modo = "empresas" | "contatos" | "atividades";

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
  const [salvando, definirSalvando] = useState(false);
  async function salvar(evento: FormEvent) {
    evento.preventDefault();
    definirErro("");
    definirSalvando(true);
    try {
      const resultado = await salvarCrm<Empresa>(
        empresa ? `empresas/${empresa.id}` : "empresas",
        empresa
          ? {
              ...valores,
              version: empresa.version,
              arquivada: empresa.arquivada,
            }
          : valores,
        Boolean(empresa),
      );
      concluir(resultado.id);
    } catch (falha) {
      definirErro(mensagemErroCrm(falha));
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
      <form onSubmit={(evento) => void salvar(evento)}>
        <div className="crm-campos">
          {(
            [
              ["nome", "Nome da empresa"],
              ["cnpj", "CNPJ (opcional)"],
              ["segmento", "Segmento"],
              ["cidade", "Cidade"],
              ["uf", "UF"],
              ["site", "Site (https://…)"],
              ["responsavel", "Responsável"],
            ] as const
          ).map(([nome, titulo]) => (
            <Campo
              key={nome}
              titulo={titulo}
              nome={nome}
              valor={valores[nome] || ""}
              alterar={(valor) => alterarValores({ ...valores, [nome]: valor })}
              obrigatorio={nome === "nome" || nome === "responsavel"}
              limite={nome === "uf" ? 2 : 200}
            />
          ))}
          {!empresa && (
            <Campo
              titulo="Telefone principal"
              nome="telefone"
              tipo="tel"
              valor={valores.telefone}
              alterar={(telefone) => alterarValores({ ...valores, telefone })}
            />
          )}
        </div>
        {erro && (
          <p className="aviso" role="alert">
            {erro}
          </p>
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
            {[
              "lembrete",
              "tarefa",
              "ligacao",
              "whatsapp",
              "email",
              "reuniao",
            ].map((tipo) => (
              <option key={tipo} value={tipo}>
                {
                  {
                    lembrete: "Lembrete",
                    tarefa: "Tarefa",
                    ligacao: "Ligação",
                    whatsapp: "WhatsApp",
                    email: "E-mail",
                    reuniao: "Reunião",
                  }[tipo]
                }
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
      consultarCrm<DetalheEmpresa>(`empresas/${empresaId}`, {
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
                  {empresa.site && (
                    <a href={empresa.site} target="_blank" rel="noreferrer">
                      Visitar site
                    </a>
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
                          {item.tipo} · {item.situacao} ·{" "}
                          {item.prazoData
                            ? item.prazoData.split("-").reverse().join("/")
                            : "Sem data"}
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
                      {new Date(evento.createdAt).toLocaleString("pt-BR")}
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
    ],
    queryFn: () =>
      consultarCrm<PaginaCrm<Empresa | Contato | Atividade>>(modo, {
        busca: termo,
        pagina,
        arquivadas,
        ...(modo === "atividades" ? { situacao, prazo, dataReferencia } : {}),
      }),
    enabled: !empresaId,
  });
  if (empresaId)
    return (
      <Detalhes
        key={empresaId}
        empresaId={empresaId}
        voltar={() => definirEmpresaId(null)}
      />
    );
  if (criando)
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
          <span className="selo">CRM local · uso interno</span>
          <p>
            {modo === "empresas"
              ? "Cadastre empresas, consulte contatos e acompanhe o relacionamento."
              : modo === "contatos"
                ? "Pessoas e canais de contato vinculados às empresas."
                : "Retornos e lembretes de pós-venda. Abra a empresa para registrar ou reagendar."}
          </p>
        </div>
        <Botao
          variante="primario"
          icone={Plus}
          onClick={() => definirCriando(true)}
        >
          Nova empresa
        </Botao>
      </div>
      <section className="painel crm-formulario">
        <div className="crm-filtros">
          <label className="campo">
            <span>
              <Search size={16} aria-hidden="true" />{" "}
              {modo === "empresas"
                ? "Buscar por empresa, contato, cidade ou telefone"
                : "Buscar por nome ou empresa"}
            </span>
            <input
              type="search"
              value={busca}
              onChange={(evento) => definirBusca(evento.target.value)}
              placeholder="Digite para buscar…"
              maxLength={200}
            />
          </label>
          {modo === "empresas" && (
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
          )}
          {modo === "atividades" && (
            <>
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
                  <option value="pendente">Pendentes</option>
                  <option value="concluida">Concluídas</option>
                  <option value="cancelada">Canceladas</option>
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
                Filtros de prazo consideram apenas pendentes. Referência:{" "}
                {dataReferencia.split("-").reverse().join("/")} (São Paulo).
              </p>
            </>
          )}
        </div>
      </section>
      <section className="painel crm-formulario">
        <h2>
          <Icone size={22} aria-hidden="true" /> {titulo}{" "}
          <span className="selo">{consulta.data?.total ?? "—"} registros</span>
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
                    <th>{modo === "atividades" ? "Atividade" : "Nome"}</th>
                    <th>{modo === "empresas" ? "Cidade / UF" : "Empresa"}</th>
                    <th>
                      {modo === "empresas"
                        ? "Responsável"
                        : modo === "contatos"
                          ? "Telefone / e-mail"
                          : "Prazo / situação"}
                    </th>
                    <th>Ação</th>
                  </tr>
                </thead>
                <tbody>
                  {consulta.data?.itens.map((item) => (
                    <tr key={item.id}>
                      <td>
                        <strong>
                          {"titulo" in item ? item.titulo : item.nome}
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
                          : "telefone" in item
                            ? [item.telefone, item.email]
                                .filter(Boolean)
                                .join(" · ") || "—"
                            : `${item.prazoData?.split("-").reverse().join("/") || "Sem data"} · ${item.situacao}`}
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
                {termo
                  ? "Nenhum registro encontrado. Tente outro nome ou telefone."
                  : "Nenhum registro ainda. Comece pelo cadastro de uma empresa."}
              </p>
            )}
            <div className="crm-resumo">
              <span>
                Página {pagina} · {consulta.data?.total ?? 0} registros
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
      </section>
    </div>
  );
}
