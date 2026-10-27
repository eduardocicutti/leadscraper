# Guia de desenvolvimento

## Escopo e referências

Estas regras se aplicam a todo o repositório. Leia os arquivos envolvidos antes de alterar código e preserve mudanças locais existentes. Instruções explícitas do usuário prevalecem sobre este guia. Um AGENTS.md em subdiretório pode detalhar regras específicas daquele módulo.

- Requisitos, fases e critérios de aceite: `docs/requisitos-e-plano-implementacao-2026.md`.
- Interface e referências aprovadas: `docs/direcao-visual-interface.md`.
- Execução atual: `README.md`.
- Distribuição atual: `docs/release.md` e `.github/workflows/release.yml`.

O estudo de viabilidade é histórico. Para decisões posteriores, seguir o plano de requisitos mais recente. Não tratar funcionalidades planejadas como implementadas. Não iniciar fases diferentes apenas porque aparecem na documentação.

## Escrita e nomes

- Escrever variáveis, funções e propriedades próprias novas em **camelCase**, com nomes claros em português e sem acentos: `empresaSelecionada`, `telefoneNormalizado`, `quantidadeSolicitada` e `calcularMediaProspeccao`.
- Usar **PascalCase** em componentes React, classes e tipos: `TabelaEmpresas`, `ResumoProspeccao`.
- Usar `UPPER_SNAKE_CASE` em constantes de módulo realmente fixas. Não transformar todo valor local em constante global.
- Booleanos devem indicar condição: `estaCarregando`, `temTelefone`, `podeEditar`.
- Coleções usam plural; elementos individuais usam singular. Datas e unidades devem aparecer no nome quando houver ambiguidade: `duracaoMs`, `prazoEmUtc`.
- Não usar nomes como `data`, `temp`, `obj`, `aux` ou `handle` sem contexto. Índices curtos são aceitáveis em laços pequenos.
- Abreviações devem ser reconhecíveis: `id`, `uf`, `url`, `api`, `crm`, `cnpj`. Não encurtar palavras só para diminuir linhas.
- Preservar grafia de APIs, bibliotecas, métodos especiais, traits Rust, contratos públicos, campos persistidos e interfaces existentes. `useEffect`, `created_at`, `__init__` e rotas legadas não devem ser renomeados por estética.
- No Python, camelCase vale para funções e variáveis próprias novas quando não houver contrato externo. Manter exceções exigidas pela linguagem e bibliotecas. No Rust, preservar convenções necessárias aos traits e APIs e o padrão dos módulos existentes.
- Não fazer renomeação em massa do legado. Converter nomes somente dentro de mudança justificada e verificando consumidores.
- Arquivos React usam PascalCase quando representam componente. Outros arquivos seguem o padrão do módulo; evitar múltiplas convenções no mesmo diretório.

## Comentários e documentação

- Código claro deve funcionar sem comentários explicativos linha a linha.
- Adicionar comentário apenas para motivo não evidente, restrição externa, compatibilidade ou decisão de negócio incomum.
- Comentários devem ser curtos, objetivos, em português e preferencialmente em minúsculas: `// mantem id legado na migracao`.
- Não adicionar comentários que apenas repitam o código, seções decorativas, emojis, diálogos, propaganda ou referências a geração por IA.
- Não remover avisos de licença, atribuições, diretivas de ferramentas ou comentários necessários à operação.
- Não silenciar erro de lint ou tipos sem justificativa local específica. Não acumular TODO sem tarefa e escopo identificáveis.
- Documentar contratos, decisões arquiteturais, instalação e operação em schemas e `docs/`, sem transformar cada função interna em um texto longo.

## Organização e implementação

- Fazer mudanças pequenas e relacionadas ao pedido. Não reformatar ou reorganizar arquivos sem necessidade.
- Reutilizar a stack e as dependências existentes antes de adicionar bibliotecas. Não migrar para Next.js, outro gerenciador ou outro scraper sem necessidade e decisão explícita.
- Separar interface, casos de uso, domínio, acesso a dados e integrações externas.
- Componentes React não executam SQL, regras de autorização ou cálculos comerciais duplicados.
- Manter regras de negócio em serviços testáveis; repositórios cuidam de persistência e adaptadores cuidam de transporte/provedores.
- Frontend: componentes reutilizáveis em `src/components/ui`, funcionalidades em `src/features` e serviços em `src/services`, conforme os módulos forem criados.
- Backend: separar rotas, schemas, serviços, domínio, repositórios e adaptadores. Evitar expandir indefinidamente `app.py` e `database.py`.
- Não introduzir abstração genérica sem uso concreto. Preferir funções curtas e coesas, retornos explícitos e fluxo legível.
- Não substituir implementações por mocks, listas fixas ou respostas de sucesso para esconder integração incompleta.

## Tipos validação e erros

- TypeScript deve manter modo estrito. Evitar `any`, coerções encadeadas e `!` sem garantia comprovável; validar `unknown` na entrada.
- Python novo deve declarar tipos nas interfaces de serviço e contratos relevantes. Usar schemas existentes para validação.
- Validar entrada no servidor, mesmo quando já validada na interface. Erros de campo devem apontar o campo e preservar formulário preenchido.
- Tratar falhas na camada que pode resolvê-las. Não usar `catch` vazio ou capturar qualquer exceção retornando sucesso.
- Erros novos de API seguem `code`, `message`, `fieldErrors` e `correlationId`. Não expor stack trace ou segredo ao usuário.
- Novas rotas usam `/api/v1` sem quebrar rotas atuais. Paginação padrão 25, máximo 100 e ordenação estável.
- Transporte e URLs dependem de configuração por ambiente. Nunca embutir chave privilegiada em código ou variável pública `VITE_*`.

## Dados e regras comerciais

- Preservar bancos, arquivos e histórico. Migração estrutural exige backup, migrations numeradas e verificação em cópia.
- Não editar migration já aplicada em ambiente compartilhado. Criar uma nova migration.
- Novas entidades usam UUID e contexto de organização/autoria conforme o plano. Responsável e autor histórico são conceitos diferentes.
- Antes da autenticação, o membro local é atribuição operacional, não identidade autenticada. Não fingir que há proteção por cargo.
- Empresa é cadastro central. Lead representa qualificação, oportunidade representa negociação e projeto representa prospecção ou entrega, com tipo explícito.
- Abrir WhatsApp, coletar empresa ou exportar planilha não comprova abordagem ou envio de mensagem.
- Telefone original e normalizado são preservados. Não impor unicidade global de telefone; não mesclar empresas automaticamente por nome parecido.
- Leituras e escritas locais/remotas seguem contratos equivalentes. Após corte remoto, manter uma fonte de escrita do CRM; SQLite do agente é outbox/cache, não réplica editável completa.
- Usar transações para conversão e operações que precisam ser atômicas. Reenvios devem ser idempotentes; edição concorrente exige controle de versão.
- Guardar instantes em UTC, exibir no fuso da organização e separar datas sem horário. Reagendamento mantém histórico e não conclui lembrete.
- Fórmulas de médias ficam em serviço único. Consolidar pelos totais e denominadores, sem média simples de médias; sem amostra significa “Sem dados”. Cargo restringe o conjunto consultável, não muda fórmula.

## Interface e SVG

- Seguir as referências aprovadas: sidebar com rótulos e ícones, cabeçalho com busca, superfícies escuras, azul principal, cards, filtros, tabelas e painéis contextuais.
- Centralizar cores, tipografia e espaçamentos em tokens. Não espalhar valores divergentes para o mesmo componente.
- Usar Lucide para ícones de interface em SVG. Não usar emoji como substituto de ícone ou screenshot encapsulada em SVG.
- Logo oficial deve vir de ativo existente ou fornecido. Reconstrução provisória não deve ser apresentada como arquivo oficial.
- Fotos e satélite podem ser raster. Assets vetoriais externos precisam de origem/licença, sanitização e ausência de scripts externos.
- Texto principal de referência: 16 px; rótulos 14 px; ações principais com área de 44 px. Preservar teclado, foco e rótulos acessíveis.
- Validar desktop e larguras de 768 e 360 px. Não reduzir toda a tela por zoom para fazê-la caber.
- Oferecer carregamento, vazio, erro, sucesso e falha parcial. Indicadores, presença, CPU, memória e percentuais exigem dados medidos; indisponibilidade não vira valor fictício.
- Tema escuro é padrão. Tema claro mantém estrutura e componentes.

## Segurança e infraestrutura

- Hospedagem web planejada: Cloudflare Pages. Serviços compartilhados: Supabase. Chromium roda no agente local.
- Produção com dados comerciais só após autenticação e autorização verificadas. Previews iniciais usam dados fictícios.
- Escopo autorizado vem da sessão validada, nunca apenas de `organizationId` recebido do navegador.
- Aplicar autorização nos serviços/banco e arquivos, inclusive consultas agregadas e exportações. Esconder botão não é proteção.
- Não colocar service role, senha, token ou chave de assinatura no frontend, agente, commit, log ou screenshot.
- Credenciais de dispositivo ficam protegidas no sistema operacional e podem ser revogadas.
- Jobs distribuídos precisam de claim atômico, lease, fencing, heartbeat e lotes idempotentes. Não prometer execução física exatamente uma vez.
- Atualizações de progresso enviam contadores e mudanças, sem retransmitir toda a lista de leads.
- Retenção elimina apenas dados temporários classificados e confirmados, não histórico comercial nem outbox pendente.

## Verificação

- Executar verificações proporcionais à mudança e reportar exatamente o que passou ou não pôde ser executado.
- Frontend: `npm ci` para instalação pelo lockfile e `npm run build` para tipos/build. Não alterar lockfile por edição manual.
- Backend: usar ambiente virtual do projeto e `python -m pytest`. Testar com banco temporário, nunca com banco real do usuário.
- Desktop: verificar build Tauri quando alterar shell, capabilities, empacotamento ou recursos nativos. Build depende do sidecar e ferramentas Windows.
- Rodar lint se configurado; não afirmar que passou uma verificação inexistente.
- Testar regras novas com casos de borda reais: duplicidade, falha parcial, divisão por zero, data/fuso, permissões, replay ou concorrência conforme o módulo.
- Não escrever testes que só repitam a implementação ou exijam dados privados, scraping real ou rede para toda execução de CI.
- UI requer inspeção visual e teste das ações, não apenas compilação. Comparar com referências em viewport equivalente quando disponíveis.
- Falta de ferramenta não comprova código correto. Registrar limitação e não declarar entrega validada integralmente.

## Git CI e releases

- O usuário autorizou o agente a cuidar de commits, atualização do repositório e releases dentro do trabalho solicitado.
- Antes de editar/commitar, verificar branch, status e diff. Nunca incluir arquivos alheios ao escopo, segredos, banco ou artefatos temporários com `git add .` indiscriminado.
- Usar branches curtas `codex/feat-...`, `codex/fix-...` e `codex/docs-...`. Não enviar diretamente à `main`; preferir PR e CI aprovado.
- Commits seguem Conventional Commits e descrição objetiva: `feat: adiciona busca por telefone no crm` ou `docs: define regras de desenvolvimento`.
- Não fazer force push, apagar alterações ou reescrever histórico compartilhado sem pedido explícito.
- CI deve validar os comandos realmente configurados. Previews não acessam produção; workflows de PR externo não recebem secrets de release.
- Fixar dependências e preservar lockfiles. Adição de dependência deve ter motivo e impacto no build/instalador avaliados.
- Versões seguem SemVer. Não aumentar versão por toda alteração documental nem gerar release por commit.
- Atualmente o workflow usa tags `v*`. Não criar `web-v*` ou `agent-v*` supondo automação pronta; atualizar e validar workflows/updater primeiro, conforme a separação planejada.
- Preservar a chave de atualização existente. Não gerar chave substituta sem estratégia para usuários instalados.
- Release exige verificações, notas, artefatos esperados e checksum. Confirmar publicação remota; arquivo local ou workflow iniciado não é release entregue.

## Comunicação de entrega

Informar o que mudou, arquivos relevantes, verificações executadas e pendências concretas. Distinguir implementação local, commit, push, PR, deploy e release: concluir um desses passos não implica concluir os demais. Atualizar a documentação quando mudar contrato, configuração ou regra de negócio.
