# Requisitos e plano de implementação da Plataforma Comercial

Versão 1.3 • 26/10/2026 • Prazo máximo 31/12/2026

## 1 Objetivo e decisões de planejamento

Este documento transforma o estudo de viabilidade em requisitos implementáveis, entregas, dependências, critérios de aceite e cronograma. A sequência prioriza CRM, mapa, interface, personalização, ícones e textos. Login, autenticação, permissões hierárquicas e operação distribuída entram na etapa final. O estudo original é referência de viabilidade; a ordem de execução deste plano substitui o roadmap anterior.

O produto usará provisoriamente o nome **Plataforma Comercial**. Será utilizado internamente pelo usuário e sua empresa, sem venda ou assinatura para terceiros. A implementação continuará aproveitando React, TypeScript, Vite, Zustand, React Query, FastAPI, SQLite, Tauri e Playwright. A migração para serviços compartilhados será incremental. Next.js e substituição do Playwright não são dependências para concluir a entrega de 2026.

A hospedagem web planejada passa a ser Cloudflare Pages, substituindo Vercel. Supabase Free será o ponto de partida para PostgreSQL, autenticação e arquivos; o scraping continuará no agente local. A meta é iniciar sem mensalidade, dentro das franquias dos serviços, sem assumir gratuidade ilimitada ou permanente. A operação compartilhada ainda depende das fases finais de autenticação e autorização.

As datas são metas de planejamento, não comprovação de capacidade contratada. Premissa: duas frentes técnicas com aproximadamente 30 horas produtivas por semana cada e validação funcional de Eduardo em até um dia útil. Isso corresponde a cerca de 480 horas de execução em oito semanas úteis equivalentes. O escopo estimado demanda 442 horas, com 38 horas de contingência. Com uma pessoa a 30 horas por semana, a capacidade seria aproximadamente metade; nesse cenário será necessário reduzir o escopo final ou aumentar a dedicação. A primeira revisão de capacidade ocorrerá em 30/10.

Não se pressupõe trabalho em feriados ou fins de semana. As datas finais de dezembro acomodam Natal, menor disponibilidade de usuários e preparação da entrega. O marco funcional é 23/12; os dias úteis restantes ficam para correções e recuperação. Não será permitido transferir silenciosamente uma pendência para depois de 31/12.

## 2 Cronograma de entregas

| Fase | Período | Entrega verificável | Esforço estimado |
|---|---|---|---:|
| 1 | 23/10 a 30/10 | Nova interface, identidade provisória, textos, ícones, preferências e contratos iniciais do CRM | 48 h |
| 2 | 03/11 a 13/11 | CRM local persistente com empresas, contatos, busca, histórico e atividades | 76 h |
| 3 | 16/11 a 20/11 | Mapa do Brasil, seleção de município e quantidade, fluxo de prospecção integrado | 40 h |
| 4 | 23/11 a 27/11 | Pipeline, projetos, indicadores básicos e assistente de planilhas | 52 h |
| 5 | 30/11 a 04/12 | Camada compartilhada preparada, migração ensaiada, preview Cloudflare Pages e protocolo do agente validado em ambiente de teste | 48 h |
| 6A | 07/12 a 11/12 | Login, autenticação, perfis, fotos e isolamento de dados | 48 h |
| 6B | 14/12 a 18/12 | Cargos, hierarquia, compartilhamento e agente conectado com recuperação | 82 h |
| 7 | 21/12 a 23/12 | Homologação integrada e versão candidata à produção | 32 h |
| Reserva | 28/12 a 31/12 | Correções, implantação controlada, restauração validada e entrega final | 16 h previstas + 38 h de contingência global |

As horas incluem desenvolvimento e verificação de cada bloco. São estimativas de trabalho, não duração corrida. As frentes são responsabilidades de planejamento e não atribuições a pessoas já confirmadas. A frente de produto cuida das telas, fluxos e integrações; a frente de dados cuida de persistência, migrações, backend e agente. A validação e a aprovação de escopo ficam com Eduardo.

## 3 Estratégia para adiar autenticação sem reconstruir o CRM

Nas fases 1 a 4, a entrega utilizável é local, com backend vinculado a 127.0.0.1 e banco existente preservado. O preview web mostra apenas dados fictícios. A publicação de dados comerciais compartilhados depende do aceite de autenticação e autorização nas fases 6A e 6B.

Desde a fase 1, toda operação comercial recebe um contexto interno com organizationId e actorId. Nesse período eles identificam a organização local e o operador local; não são tratados como identidade autenticada. Na fase 6, serão obtidos da sessão validada no servidor. Um valor enviado pelo navegador nunca definirá sozinho o escopo autorizado.

Os novos registros usam UUID, organizationId, createdBy, updatedBy, createdAt, updatedAt e version. Responsáveis são referências a registros internos de membros; nomes são apenas apresentação. Um mapa explícito liga membros locais a usuários autenticados durante a migração. Registros antigos sem responsável ficam em uma fila de atribuição, sem inventar autoria.

A interface acessa serviços de domínio e interfaces de repositório, não consultas SQLite espalhadas nos componentes. Os adaptadores local e remoto implementam os mesmos contratos. Testes de contrato verificam resultados, validação, paginação e erros equivalentes. A mudança para remoto ocorre por configuração única e desativa escrita local no CRM após o corte.

As políticas de acesso, entidades de concessão e casos de teste são especificados na fase 1. Sua execução real acontece na fase 6. Até lá, nenhuma tela de cargos será apresentada como proteção funcional.

## 4 Requisitos funcionais e critérios de aceite

Prioridade P0 significa indispensável para a entrega de 2026. P1 significa desejável com corte explícito se houver desvio. Cada requisito inclui fase, comportamento e evidência esperada.

### 4.1 Interface identidade e personalização

As oito imagens fornecidas em 22/10/2026 passam a ser referência visual principal. A especificação complementar está em [Direção visual da interface](direcao-visual-interface.md): menus completos, paleta escura com azul, ícones SVG, componentes, composição por tela e critérios de fidelidade. Aplicar na fase 1 e manter nas seguintes. Recursos extras representados nas imagens têm dependências e prioridades explícitas nesse documento.

| ID | Fase e prioridade | Requisito e aceite |
|---|---|---|
| RF01 | 1 P0 | Aplicar tokens de tipografia, cores, espaçamento, bordas e foco. Texto principal de 16 px, rótulos legíveis e botões principais com área de 44 px. Todas as telas atuais usam componentes comuns. |
| RF02 | 1 P0 | Navegação com texto e ícones consistentes de uma única biblioteca. Prospecção, Empresas, Atividades, Oportunidades, Projetos, Histórico e Configurações são localizáveis; módulos pendentes exibem estado indisponível identificado. |
| RF03 | 1 P0 | Reescrever instruções, erros, confirmações e estados vazios em português direto. Erro informa ação possível; entradas são preservadas após falha; status operacional reflete checagem real do backend. |
| RF04 | 1 P0 | Aplicar nome provisório por configuração central. Preservar identificador técnico e diretório de dados do desktop até haver migração própria. Alterar nome exibido não cria banco vazio nem rompe atualização. |
| RF05 | 1 P0 | Preferências de tema claro/escuro, densidade confortável/compacta e escala de fonte. Persistem ao reiniciar, possuem padrão e opção restaurar; preferências locais serão associadas ao perfil na fase 6. |
| RF06 | 1 a 4 P0 | Layout utilizável em 360, 768 e 1366 px. Tabela usa rolagem interna ou visão em cartões; página não exige rolagem horizontal. Todas as ações principais funcionam por teclado. |
| RF07 | 4 P1 | Preferências de colunas, ordenação, filtros salvos e página inicial. Restaurar padrões não apaga registros comerciais. |

### 4.2 CRM e acompanhamento comercial

| ID | Fase e prioridade | Requisito e aceite |
|---|---|---|
| RF08 | 2 P0 | Cadastrar, consultar, editar e arquivar empresa. Nome é obrigatório; CNPJ é opcional e validado quando informado. Segmento, cidade, UF, site, origem e responsável são persistidos. Arquivamento preserva vínculos. |
| RF09 | 2 P0 | Manter vários contatos por empresa com nome, cargo, telefones e e-mails. Guardar telefone original e normalizado; pesquisar com ou sem formatação retorna o mesmo contato. |
| RF10 | 2 P0 | Busca global por nome, telefone e CNPJ. Desconsiderar acentos no nome e pontuação no telefone. Mostrar empresa, último contato, responsável e situação comercial. Persistência confirmada após fechar e reabrir o aplicativo. |
| RF11 | 2 P0 | Histórico de prospecção por empresa com data, canal, responsável e resultado. “Já prospectado” exige uma interação registrada; apenas coletar no Maps não confirma abordagem. |
| RF12 | 2 P0 | Registrar atividade de ligação, mensagem, e-mail, reunião ou tarefa, com prazo, responsável e situação. Abrir WhatsApp não marca mensagem como enviada; usuário registra resultado manualmente. |
| RF13 | 2 P0 | Antes de criar empresa, procurar duplicidade por CNPJ, telefone, URL de origem ou nome mais município. Mostrar candidatos; nunca mesclar automaticamente registros por semelhança de nome. |
| RF14 | 2 P0 | Converter resultado de coleta ou lista preferencial em empresa/contato/lead sem perder origem. Repetir a conversão não cria novas cópias. Histórico original continua consultável. |
| RF15 | 2 P0 | Qualificação do lead: novo, em análise, qualificado, convertido ou desqualificado. Desqualificação exige motivo; conversão cria ou vincula oportunidade em operação única. |
| RF16 | 4 P0 | Pipeline em quadro e lista com contato, diagnóstico, proposta, negociação, ganho e perdido. Mudança persiste; ganho/perda exige data e perda exige motivo. Valor é opcional até proposta. |
| RF17 | 4 P0 | Projeto de entrega vinculado à oportunidade ganha ou projeto comercial de prospecção independente, identificado por tipoProjeto. Ambos possuem escopo, responsável, prazo, situação e marcos. Projeto comercial agrupa buscas, empresas e tarefas; criar entrega duas vezes para a mesma conversão exige confirmação explícita. |
| RF18 | 4 P0 | Linha do tempo reúne atividades, alterações de etapa e vínculos com projetos. Dashboard apresenta total por etapa, tarefas vencidas e oportunidades ganhas/perdidas no período com filtros e definição de cada indicador. |
| RF19 | 4 P1 | Mesclagem assistida com escolha de valores e registro dos IDs de origem. Sem aceite desta função, manter bloqueio de duplicidade e revisão manual; não remover dados para cumprir prazo. |

### 4.3 Mapa e prospecção

| ID | Fase e prioridade | Requisito e aceite |
|---|---|---|
| RF20 | 3 P0 | Mapa vetorial das 26 UFs e DF com foco, nome, sigla e seleção. Lista equivalente funciona por teclado e em celular; mapa e lista permanecem sincronizados. |
| RF21 | 3 P0 | Município vinculado à UF por código oficial, com busca textual e cache de catálogo. Trocar UF limpa município incompatível; falha de atualização preserva catálogo válido anterior. |
| RF22 | 3 P0 | Quantidade por presets 25/50/100/200, campo numérico e controle visual sincronizados. Limite inicial de 1 a 500 validado no cliente e servidor; quantidade pedida não é promessa de quantidade disponível. |
| RF23 | 3 P0 | Revisar localização, segmento e quantidade antes da execução. Exibir coletados, processados, falhas e tempo decorrido; estimativa de término só aparece quando houver amostra medida suficiente. |
| RF24 | 3 e 6B P0 | Em local, continuar o scraper atual e persistência incremental. Em remoto, acompanhar job fora da página inicial. Falha parcial preserva resultados e distingue concluído com avisos de falha total. |
| RF25 | 5 P1 | Piloto OSM em amostra fixa de três municípios e três segmentos; comparar cobertura, telefone/site preenchidos, duplicidades e latência com a fonte atual. Ausência de site no OSM significa desconhecido, sem bônus automático de score. |
| RF26 | 5 P1 | Benchmark Scrapling contra Playwright com a mesma amostra e versão fixada. Substituição só se melhorar métrica definida sem regressão de dados/instalação; manter Playwright se não aprovado em 04/12. |

### 4.4 Planilhas e configurações

| ID | Fase e prioridade | Requisito e aceite |
|---|---|---|
| RF27 | 4 P0 | Assistente XLSX/CSV/TSV com escolha de aba quando aplicável, mapeamento, prévia e simulação. Nome ou telefone identifica linha candidata; validar campos antes de gravar e reportar número da linha original. |
| RF28 | 4 P0 | Importar em lotes identificados, informando inseridos, atualizados, duplicados e rejeitados. Política inicial: ignorar duplicado e não sobrescrever valor existente sem escolha do usuário. Repetir lote confirmado não duplica dados. |
| RF29 | 4 P0 | Exportar visão filtrada em XLSX e CSV com template versionado. Proteger conteúdo iniciado por operadores de fórmula, preservar telefones como texto e respeitar autorização na etapa remota. |
| RF30 | 4 P0 | Templates globais e por segmento com variáveis conhecidas, prévia e erro em variável inválida. Mensagem individual tem precedência sobre segmento e global. |
| RF31 | 4 e 6 P0 | Separar configuração pessoal, da equipe, da organização e do agente. Na fase local, apenas pessoal/local é editável; configuração organizacional passa a exigir permissão em 6B. |

### 4.5 Login perfis e transparência

| ID | Fase e prioridade | Requisito e aceite |
|---|---|---|
| RF32 | 6A P0 | Login com e-mail e senha, recuperação, logout, expiração e renovação de sessão. Cadastro inicial por convite; não permitir autoatribuição de organização ou cargo. Convite expirado pode ser reemitido. |
| RF33 | 6A P0 | Perfil com nome, foto e preferências. Upload JPG/PNG/WebP até 2 MB com validação real do arquivo e redimensionamento; usuário não altera próprio cargo. Perfil desativado perde acesso e dispositivos. |
| RF34 | 6B P0 | Cargos: Assessor Comercial, Assessor Marketing, Gerente Comercial, Gerente Marketing, Diretor Comercial/Marketing e Presidente. Escopo combina organização, equipe, gestão, responsável e concessão específica. |
| RF35 | 6B P0 | Diretor e presidente concedem leitura/comentário/edição de oportunidade ou projeto a membro da organização, com expiração opcional e revogação. Concessão não libera campos sensíveis sem permissão separada. |
| RF36 | 6B P0 | Auditoria de alteração de cargo, concessão, exportação, arquivamento, mesclagem e mudanças comerciais. Eventos não podem ser alterados por usuários comuns e não armazenam tokens ou senhas. |

### 4.6 Hospedagem e agente conectado

| ID | Fase e prioridade | Requisito e aceite |
|---|---|---|
| RF37 | 5 e 7 P0 | Preview Cloudflare Pages por PR com dados fictícios; produção só após aceite de acesso. URL web usa configuração remota e não depende de localhost do computador de outro usuário. |
| RF38 | 6B P0 | Agente Windows baixável, com versão, diagnóstico, pareamento e revogação. Segredo por dispositivo fica protegido no sistema operacional; distribuição não inclui service role. |
| RF39 | 6B P0 | Claim atômico de job com lease e fencingToken crescentes. Dois agentes concorrentes produzem uma única tentativa aceita pelo servidor; execução física repetida ainda pode ocorrer após falha. |
| RF40 | 6B P0 | Heartbeat, progresso e resultados em lotes idempotentes; outbox local reenvia após reconexão e remove apenas lote confirmado. Escrita de lease vencido é rejeitada. |
| RF41 | 6B P0 | Cancelamento cooperativo entre unidades de trabalho e encerramento do navegador. Interface distingue cancelamento solicitado de confirmado; retomar cria nova tentativa sem sobrescrever silenciosamente a anterior. |
| RF42 | 7 P0 | Release do agente com updater assinado, checksum e versão mínima de protocolo. Atualização preserva outbox e dados; incompatibilidade impede novos jobs e orienta atualização. |

## 5 Regras do domínio e modelo de dados

Empresa é a entidade principal. Lead registra qualificação; oportunidade registra negociação; projeto registra entrega. A temperatura calculada não substitui etapa comercial. Nenhuma atividade será criada automaticamente como abordagem só porque houve extração, exportação ou abertura de link.

| Entidade | Conteúdo mínimo e relações |
|---|---|
| organization e member | Organização local inicial; membro com nome, equipe e futuro authUserId. Cargo e gestão são definidos no servidor na fase 6. |
| company | UUID, nome original/normalizado, CNPJ opcional, município, UF, segmento, site, origem, arquivadoEm e responsável. |
| contact e contactChannel | Pessoa e vários telefones/e-mails; telefone original, normalizado e situação de confirmação. |
| lead | Empresa, responsável, estado de qualificação, motivo e vínculo de conversão. |
| opportunity | Empresa, etapa, valor opcional, responsável, próxima ação e datas de ganho/perda. |
| project e milestone | Oportunidade, escopo, responsável, estado, prazo e marcos. |
| activity | Empresa e vínculos opcionais com contato/oportunidade/projeto; tipo, resultado, prazo e situação. |
| prospectionRun e result | Parâmetros, fonte, horários, valores coletados, origem por campo e vínculo com empresa canônica. |
| importBatch e importRow | Versão do template, hash, estado de confirmação, resultado por linha e vínculo criado. |
| preference e messageTemplate | Escopo, chave, versão e valor; mensagem individual prevalece. |
| device e jobAttempt | Organização, membro, revogação, versão, lease, token de execução e última conexão. |
| resourceGrant e auditEvent | Recurso, destinatário, ações, campos sensíveis, validade; ator, ação, resultado e data. |

Telefone não é único globalmente: filiais e empresas podem compartilhar números. CNPJ preenchido é único por organização, salvo tratamento explícito de cadastro legado inválido. Sugestão por nome usa similaridade, mas exige revisão. O UUID da empresa é a referência dos relacionamentos; renomear empresa não rompe vínculos.

Antes da migração remota, registrar tabela de correspondência entre IDs inteiros antigos e UUIDs. Cada execução de migração possui ID, contagens por entidade, rejeições e checksum do backup. Não transformar automaticamente cada lead histórico em empresa ativa: importar primeiro como resultado de origem e criar vínculos revisados.

## 6 Mapa de implementação no repositório

| Área atual | Mudança planejada | Fase |
|---|---|---|
| src/styles.css e componentes | Tokens, componentes compartilhados, escala e responsividade | 1 |
| src/components/Layout.tsx | Navegação, nome configurável, diagnóstico real e preferências | 1 |
| src/api.ts | Separar tipos, configuração de transporte e contratos por domínio | 1 a 5 |
| src/store.ts | Manter estado visual; entidades persistentes via camada de consulta e serviços | 1 a 2 |
| backend/domain/models.py | Introduzir empresas, contatos, atividades, oportunidades, projetos e vínculos | 2 e 4 |
| backend/repositories/database.py | Extrair repositórios por módulo e migrações numeradas; manter compatibilidade antiga | 2 a 5 |
| backend/api/app.py | Rotas modulares de CRM com validação e paginação | 2 a 4 |
| SearchPanel.tsx e componentes novos | Mapa UF, município, quantidade e revisão | 3 |
| SelectedLeadsPage.tsx | Preservar lista e adicionar conversão para CRM e origem | 2 a 4 |
| import_service.py e export_service.py | Prévia, lotes, erros por linha e templates versionados | 4 |
| job_store.py e scrape_service.py | Separar execução da comunicação; migrar memória para estado durável e tentativas | 5 a 6B |
| src-tauri e runtime Python | Pareamento, credenciais, outbox, atualização e diagnóstico | 6B e 7 |
| supabase/migrations e tests novos | Modelo remoto, funções atômicas, índices e políticas | 5 a 6B |
| .github/workflows | CI em PR, previews, testes de políticas, release e produção | 1 a 7 |

Não mover todo o repositório para monorepo no começo. Criar módulos progressivamente em src/features, src/components/ui, src/services e backend/api/routes. A organização apps/web e apps/agent só será adotada se necessária para os builds independentes, sem transformar a reorganização em bloqueio de entrega.

## 7 Contratos preparados antes das integrações finais

Na fase 1 definir DTOs, enums, erros e contexto. Na fase 2 implementar operações locais. Na fase 5 reproduzir contratos no adaptador remoto. Na fase 6 aplicar identidade validada e políticas reais.

Contratos mínimos: listCompanies com paginação e filtros; getCompany com linha do tempo; createCompany; updateCompany com version; createActivity; convertLead; changeOpportunityStage; createProject; previewImport; confirmImport; exportFiltered; createJob; claimJob; heartbeat; uploadBatch; requestCancel; completeAttempt.

API local pode preservar rotas antigas para compatibilidade. Novos contratos usam /api/v1. Toda listagem tem tamanho padrão 25, máximo 100 e ordenação estável. Erros usam code, message, fieldErrors e correlationId. Escrita concorrente com version antiga retorna conflito, em vez de perder a edição anterior. Operações repetíveis recebem idempotencyKey com escopo da organização.

Claim, renovação, upload e finalização de jobs são operações de servidor. O agente não escreve livremente nas tabelas. Identidade do dispositivo, organização e lease são verificados em toda operação. Realtime serve para atualizar a interface; consulta periódica oferece recuperação quando um evento não chega.

## 8 Plano detalhado por fase

### Fase 1 até 30 de outubro

1. Inventariar telas e estados atuais; congelar glossário, navegação e contratos de entidades.
2. Implementar componentes de botão, campo, modal, tabela, aviso, estado vazio e ícone com rótulo.
3. Aplicar tipografia, responsividade, textos, nome provisório e preferências persistentes.
4. Definir contexto local, UUID, repository interfaces, matriz de acesso e migrações versionadas.
5. Adicionar CI de lint, tipos, build e regressão existente.

Aceite: telas atuais utilizáveis, preferências persistentes, extração e exportação atuais preservadas. Próxima fase recebe cadastro de empresa e contratos sem depender da identidade visual antiga.

### Fase 2 até 13 de novembro

1. Criar migrações aditivas com backup anterior e correspondência de IDs.
2. Implementar empresa, contato, qualificação, atividade e linha do tempo.
3. Adicionar busca global e detecção assistida de duplicidades.
4. Integrar histórico e Lista Preferencial ao CRM com conversão idempotente.
5. Ensaiar migração com banco de teste representativo e preservar consultas antigas.

Aceite: cadastrar empresa, pesquisar telefone formatado, registrar abordagem, reiniciar app e recuperar todos os vínculos. Preparação seguinte: oportunidades apontam para empresa e atividades já aceitam vínculo comercial opcional.

### Fase 3 até 20 de novembro

1. Integrar mapa vetorial e catálogo de municípios com versão e atribuição.
2. Sincronizar UF/município e controles de quantidade.
3. Criar resumo antes da extração e tratamento de resultados parciais.
4. Integrar conversão de resultados com deduplicação do CRM.

Aceite: seleção por mapa e lista produz parâmetros equivalentes; quantidade inválida é recusada no servidor. Preparação seguinte: source e runId já fazem parte dos resultados, permitindo novas fontes sem alterar cadastros.

### Fase 4 até 27 de novembro

1. Implementar oportunidades em lista/quadro, transições e criação de projeto.
2. Implementar projetos, marcos, tarefas e indicadores básicos com filtros.
3. Criar prévia de planilha, mapeamento, confirmação em lote e relatório.
4. Concluir templates, exportação e configurações por escopo.

Aceite: percurso completo de empresa até oportunidade ganha e projeto, com histórico persistente; importação repetida sem duplicar lote. Preparação seguinte: anexos possuem metadados e interface de armazenamento; serviço remoto pode substituir armazenamento local.

### Fase 5 até 4 de dezembro

1. Criar schema PostgreSQL de homologação, migrações e índices equivalentes ao domínio local.
2. Ensaiar importação do banco local e comparar contagens, vínculos e campos.
3. Publicar preview com dados fictícios, usando configuração e adaptadores separados.
4. Implementar simulador do protocolo do agente e testar claim concorrente, lease vencido e reenvio.
5. Executar pilotos OSM/Scrapling se houver capacidade; registrar decisão de manter fonte atual quando não houver benefício medido.

Aceite: contratos locais/remotos equivalentes em teste e migração reproduzível. Não habilitar dados comerciais via API anônima para compensar ausência de login.

### Fases 6A e 6B até 18 de dezembro

1. Integrar Auth, convites, recuperação, sessão, perfil e foto.
2. Vincular membros legados; implantar políticas por organização e testes de negação.
3. Implementar matriz de cargos, gestão e concessões por registro e por campo sensível.
4. Parear agente real, proteger credenciais e ativar protocolo com lease, fencing e outbox.
5. Testar desconexão, reinício, revogação, disputa entre agentes e cancelamento.

Aceite: dois usuários de escopos diferentes não acessam registros indevidos, inclusive chamando API diretamente. Job real completa com uma interrupção de rede e reconcilia dados sem duplicar. Preparação final: instalador candidato, scripts de migração e roteiro de reversão versionados.

### Fase 7 e reserva até 31 de dezembro

1. Homologar percurso ponta a ponta por perfil com dados controlados.
2. Validar instalação limpa e atualização do agente no Windows.
3. Congelar funcionalidades em 18/12; gerar versão candidata em 23/12.
4. Fazer backup, aplicar migração e verificar dados antes de abrir operação compartilhada.
5. Entregar release, notas, guia de operação, limitações conhecidas e evidências até 31/12.

Aceite final: nenhum defeito crítico de acesso ou perda de dados; fluxos P0 aprovados; restauração ensaiada. Se falhar critério de segurança ou integridade, a versão local continua disponível e a publicação remota fica bloqueada, com desvio registrado na entrega final.

## 9 Matriz de acesso a implementar no final

| Cargo | Escopo padrão | Ações comerciais | Concessões |
|---|---|---|---|
| Assessor Comercial | Próprios registros e compartilhados | Cadastrar e atualizar atividades/leads/oportunidades atribuídas | Não concede acesso |
| Assessor Marketing | Registros de marketing e compartilhados | Atualizar atividades atribuídas e consultar informações autorizadas | Não concede acesso |
| Gerente Comercial | Equipe comercial subordinada | Distribuir responsáveis, acompanhar e editar trabalho da equipe | Solicita compartilhamento entre áreas |
| Gerente Marketing | Equipe de marketing subordinada | Acompanhar e editar trabalho de marketing autorizado | Solicita compartilhamento entre áreas |
| Diretor Comercial/Marketing | Equipes das áreas sob sua gestão | Acompanhar, editar e administrar escopo dessas áreas | Concede e revoga acesso explícito |
| Presidente | Organização | Acompanhamento e administração organizacional | Concede e revoga acesso organizacional |

Valores de proposta, margem, condições contratuais e anexos restritos são classificados separadamente. Acesso ao resumo de andamento não implica acesso a esses campos. Os testes devem verificar também buscas, contagens, exportações e arquivos para evitar exposição indireta. Gerente não recebe automaticamente acesso à outra área. Mudanças na hierarquia não reescrevem autoria histórica.

## 10 Requisitos não funcionais e verificação

| ID | Meta | Verificação |
|---|---|---|
| RNF01 | Persistência consistente e migração reversível por backup | Cadastro/alteração/reinício; migração em cópia; comparação de contagens e restauração |
| RNF02 | Busca local p95 até 500 ms em 10 mil empresas na máquina de referência | Medir amostra repetível, excluir tempo de digitação e registrar hardware |
| RNF03 | Busca remota p95 até 2 s com 10 mil empresas e cinco sessões simultâneas | Medir em homologação e registrar região/rede; meta de aplicação, não SLA de provedor |
| RNF04 | Navegação responsiva e por teclado | Percursos de busca, cadastro e mapa em 360/768/1366 px, zoom 200% e foco visível |
| RNF05 | Nenhuma chave privilegiada distribuída | Inspeção dos bundles web/agente e variáveis dos ambientes |
| RNF06 | Autorização aplicada em banco/serviço | Matriz positiva e negativa por cargo, organização, concessão e arquivo |
| RNF07 | Jobs toleram repetição e falha de rede | Concorrência de dois agentes, lease vencido, replay e queda antes/depois da confirmação |
| RNF08 | Logs úteis sem segredos | Eventos com correlationId e amostragem para dados confidenciais |
| RNF09 | Instalação e atualização preservam dados | Máquina Windows limpa, atualização sobre versão anterior, outbox pendente |
| RNF10 | Backup recuperável | Meta operacional inicial RPO 24 h e RTO 4 h, dependentes de rotina configurada e ensaio; não presumir backup automático do plano do provedor |

Heartbeat inicial a cada 15 s, indicação offline após 60 s e lease de 120 s são parâmetros de piloto. Validar antes de produção, manter configuráveis e usar relógio do servidor. Timeout não comprova que o agente parou; fencing impede aceitar gravações antigas.

## 11 Padrões de implementação e entrega

Seguir camelCase para nomes próprios de variáveis e funções novas, em português claro e sem acentos, conforme preferência do projeto; PascalCase para componentes e tipos. APIs e interfaces de terceiros mantêm a grafia exigida. Não renomear símbolos legados em massa para adequação estética. Exemplo de vocabulário: empresaSelecionada, telefoneNormalizado, quantidadeSolicitada, prazoConcessao e resultadoImportacao.

Comentários são dispensados por padrão. Quando necessários para explicar restrição ou motivo, serão curtos, objetivos e no vocabulário do projeto, como “mantem id legado na migracao”. Abreviações apenas reconhecíveis como id, uf, api, crm e url. Documentação de contratos fica em schemas e documentos próprios.

Branches curtas seguem codex/feat-crm-empresas, codex/fix-busca-telefone ou codex/docs-requisitos. main protegida, PR com mudança, evidência e efeito sobre dados; commits Conventional Commits com descrição concreta. Versionar web e agente separadamente quando passarem a ter ciclos independentes. Usar SemVer e tags web-vX.Y.Z e agent-vX.Y.Z; corrigir release por nova versão, sem reutilizar tag.

CI desde a fase 1: lint, tipos, build e regressão da API. Acrescentar testes do domínio nas fases 2/4, contratos na 5, RLS e integração do agente na 6 e smoke de instalação na 7. Preview nunca aponta para produção. Segredos de release ficam apenas em ambiente autorizado; dependências Python possuem versões fixadas e frontend usa lockfile. Migrations numeradas são revisadas, não editadas após aplicação compartilhada.

## 12 Dependências caminho crítico e gestão de desvios

O caminho crítico é: contratos e IDs → CRM persistente → vínculos de oportunidade/projeto → modelo remoto e migração → autenticação/isolamento → cargos e agente → homologação. Mapa e personalização podem avançar sem aguardar login, mas dependem do formulário e componentes comuns.

| Marco | Evidência | Ação se houver atraso |
|---|---|---|
| 30/10 | Interface e contratos aprovados; capacidade real medida | Reestimar horas; retirar filtros salvos antes de comprimir testes |
| 13/11 | CRM persistente e busca aprovados | Congelar campos acessórios; manter cadastro, contato, histórico e busca |
| 27/11 | Pipeline/projetos e planilhas operacionais | Cortar mesclagem avançada e dashboards adicionais |
| 04/12 | Migração e protocolo demonstrados | Encerrar pilotos OSM/Scrapling; manter Playwright e fonte atual |
| 11/12 | Login e isolamento aprovados | Concentrar execução em segurança; não abrir banco anonimamente |
| 18/12 | Cargos e agente completos | Congelar escopo; classificar P0 pendentes e concentrar reserva neles |
| 23/12 | Versão candidata aprovada | Apenas correções e operação até 31/12 |

Revisão semanal confronta requisitos aceitos, horas restantes, dependências e defeitos. Novo pedido entra no backlog com efeito explícito no prazo. Não substituir critério de aceite por “tela pronta”. A entrega exige persistência, integração e evidência verificável.

São cortes P1 predefinidos: filtros pessoais avançados, mesclagem assistida, piloto produtivo OSM, substituição por Scrapling e indicadores além dos básicos. Campanhas completas de marketing, integração automática de WhatsApp/e-mail, inteligência artificial, aplicativo móvel nativo, relatórios personalizados e Scrum de projetos não integram o compromisso de 2026.

## 13 Roteiro de migração e operação

1. Preservar banco e artefatos existentes; criar backup com checksum antes de cada migração estrutural.
2. Aplicar migrations locais aditivas e validar leitura das funções atuais nas fases 2/4.
3. Ensaiar remoto na fase 5 com dados sintéticos ou cópia controlada; produzir relatório de vínculos e rejeições.
4. Na fase 6, cadastrar organização, convidar usuários e mapear membros antigos. Não migrar senhas locais, pois não existem no sistema atual.
5. No corte, pausar novas escritas, gerar backup final, migrar e validar total de empresas, contatos, oportunidades, projetos e atividades.
6. Ativar uma única fonte de escrita do CRM. SQLite do agente fica reservado à outbox e cache; não executar sincronização bidirecional genérica de todo o CRM.
7. Se o aceite falhar antes de liberar escrita remota, restaurar versão local e backup. Se já houver dados remotos novos, exportar e reconciliar antes de reverter; backup antigo isoladamente perderia essas alterações.

## 14 Evidências e pacote final

Cada fase deve entregar release ou build identificável, demonstração do fluxo, lista de requisitos aceitos e pendentes e notas de migração. O pacote final contém aplicação web publicada, instalador do agente, migrations, backup/restore documentados, matriz de acesso validada, guia de uso e operação e limitações conhecidas.

Este documento é a especificação inicial de implementação. A avaliação de 30/10 deve confirmar capacidade e ajustar apenas escopo opcional ou recursos, preservando a ordem solicitada e a data limite de 31/12/2026.

## 15 Hospedagem gratuita e capacidade do Supabase

### 15.1 Serviços e limites de partida

| Componente | Solução inicial | Limites e condições relevantes |
|---|---|---|
| Frontend React e Vite | Cloudflare Pages Free | 500 builds por mês, um build simultâneo e limite de 25 MiB por arquivo estático. Usar endereço pages.dev inicialmente; domínio próprio é opcional e pode gerar custo. |
| Banco compartilhado | Supabase Free | 500 MB de banco por projeto. Índices, histórico, atividades, auditoria e jobs também consomem espaço. |
| Fotos e arquivos | Supabase Storage Free | 1 GB de armazenamento. Não confundir com os 500 MB do banco. |
| Tráfego | Supabase Free | 5 GB de egress incluído e franquia separada de cached egress; não tratar a soma como 10 GB livremente intercambiáveis. Medir cada categoria no painel. |
| Disponibilidade | Supabase Free | Projeto pode ser pausado após período de baixa atividade de sete dias. Não prometer funcionamento contínuo como se houvesse SLA contratado. |
| Backup | Rotina própria | Backups automáticos não estão incluídos no Free. Configurar exportação protegida, retenção e restauração testada. |
| Scraping | Agente local | Computador ligado e conectado para receber e executar trabalhos. Sem servidor de Chromium contratado; há consumo local de recursos e internet. |

Os números refletem as fontes consultadas em 22/10/2026 e precisam ser conferidos novamente na configuração das contas e antes da produção. O plano não prevê ativar recursos pagos automaticamente. Necessidade de pagamento será apresentada com consumo medido e alternativa de redução ou migração.

### 15.2 Estimativa de crescimento

Hipótese preliminar: 5 a 10 KB por empresa única, incluindo contatos, índices e um histórico curto. Essa faixa não foi medida no sistema novo e não representa reserva garantida nem limite de registros do Supabase.

| Empresas únicas | Espaço estimado da hipótese |
|---|---:|
| 5 mil | 25 a 50 MB |
| 20 mil | 100 a 200 MB |
| 50 mil | 250 a 500 MB |

Somar separadamente usuários, oportunidades, projetos, atividades adicionais, resultados de pesquisas, jobs e auditoria. Cinquenta mil empresas já podem pressionar o Free. Empresas repetidas em novas buscas não devem gerar novo cadastro canônico, mas seus eventos e resultados de origem ainda aumentam o banco.

Para projeção mensal, medir: usuários prospectando × buscas diárias por usuário × resultados por busca × dias de uso × proporção de empresas novas. Esse cálculo estima novas empresas; acrescentar o crescimento dos eventos por empresa e dos jobs. Quantidade de usuários e volume diário ainda não foram informados, portanto não é possível afirmar quantos meses a franquia durará.

### 15.3 Requisitos adicionais de capacidade

| ID | Fase e prioridade | Requisito e aceite |
|---|---|---|
| RF43 | 5 a 7 P0 | Medir banco, índices, arquivos, egress e mensagens Realtime separadamente. Registrar base inicial e projeção no relatório semanal do piloto. |
| RF44 | 5 a 6B P0 | Progresso remoto transmite status, contadores e alterações, sem reenviar a lista completa de leads a cada consulta. Resultados usam lotes idempotentes e leitura paginada. Teste mede bytes transferidos por job. |
| RF45 | 5 a 7 P0 | Definir expiração configurável para cache e detalhes temporários dos jobs. Limpeza só alcança dados classificados como temporários, após confirmação de recebimento; nunca apaga silenciosamente contatos, atividades ou histórico comercial. |
| RF46 | 6A a 7 P0 | Foto de perfil recebida com limite de 2 MB é reduzida antes do armazenamento. Anexos têm limite por arquivo e orçamento organizacional configurados; recusa apresenta motivo e alternativa. |
| RF47 | 7 P0 | Alertar ao atingir 60%, 75% e 90% de cada franquia acompanhada. Em 75%, revisar projeção; em 90%, limitar operações opcionais de alto consumo. Manter exportação e recuperação disponíveis sempre que a infraestrutura permitir. |
| RNF11 | 5 a 7 | Pilotar dados representativos, medir tamanho médio por entidade e tráfego por job e substituir a hipótese de 5 a 10 KB por medição documentada. Aceite: relatório com amostra, duração, volume, índices e projeção mensal. |

Política inicial proposta para validação na fase 5: cache de busca por sete dias; logs detalhados de jobs concluídos por 30 dias; resumo do job e origem comercial preservados segundo a retenção organizacional. Outbox não confirmada nunca é removida por essa rotina. Falhas pendentes de análise e jobs em execução ficam fora da limpeza automática. A política definitiva será registrada antes de habilitar a rotina.

### 15.4 Decisão de continuidade

Começar no Supabase Free é adequado para um piloto, condicionado às medições. Não é compromisso de que toda a operação futura caberá nele. Se a projeção alcançar 75% do banco em até 60 dias, revisar duplicação, retenção e índices antes de expandir a coleta. Se o egress se aproximar do limite, revisar frequência de consulta, payloads e assinaturas antes de aumentar o volume.

Se os dados comerciais necessários ultrapassarem a capacidade mesmo após otimização, apresentar duas opções: plano maior no Supabase ou migração do PostgreSQL para infraestrutura compatível. Preservar migrations, contratos e exportações para permitir a mudança. Não remover histórico necessário apenas para permanecer gratuito.

### 15.5 Efeito sobre o cronograma e operação

As datas até 31/12/2026 permanecem. A fase 1 já separa configuração de hospedagem e transporte; a fase 5 configura Cloudflare Pages, mede dados e tráfego e define retenção; a fase 6 implementa progresso incremental; a fase 7 valida alertas, backup e projeção. O esforço adicional será absorvido pela preparação de infraestrutura e contingência existentes e revisado no primeiro marco; não representa capacidade extra comprovada.

O agente responsável pelo desenvolvimento também executará commits, branches, atualização do repositório, PRs, versionamento e releases, conforme autorização do usuário. Alterações verificadas entram em commits rastreáveis; releases agrupam entregas aprovadas e não são criadas a cada commit. Autenticação de contas e instalação com privilégio administrativo podem exigir interação do usuário.

## 16 Indicadores por assessor e lembretes de pós venda

### 16.1 Indicadores de prospecção independentes do perfil

O sistema deve permitir consultar dados médios da prospecção por assessor e no consolidado. O cálculo pertence a um serviço de domínio único, independente da tela, do usuário conectado e do cargo. Perfil e permissões determinam quais registros podem ser consultados; não alteram a fórmula. Dois usuários com acesso ao mesmo conjunto de dados e aos mesmos filtros devem obter o mesmo resultado. O consolidado representa somente o escopo autorizado e deve identificá-lo claramente.

“Dados médios” foi solicitado sem definição exata das grandezas. O conjunto abaixo é uma proposta inicial de métricas, a ser validada no marco funcional; não representa metas de desempenho aprovadas. Distinguir resultados extraídos por execução de empresas únicas e de abordagens comerciais efetivamente registradas.

| Indicador proposto | Fórmula e base |
|---|---|
| Resultados médios por busca | Total de resultados persistidos em buscas concluídas do período ÷ quantidade dessas buscas. Duplicidade entre buscas não é contada como nova empresa. |
| Empresas novas por busca | Empresas canônicas criadas pela primeira conversão de resultados dessas buscas ÷ quantidade dessas buscas. Reprocessamento não gera nova criação. |
| Tempo médio de extração | Soma das durações medidas das buscas concluídas ÷ quantidade de buscas com duração disponível. Tempo desconhecido não é zero. |
| Abordagens médias por dia ativo | Interações de prospecção registradas pelo assessor ÷ dias distintos com essas interações, no fuso da organização. Exibir denominador e informar que dias sem atividade não integram essa média. |
| Contatos com retorno | Empresas com retorno registrado ÷ empresas distintas abordadas na mesma coorte. Definir janela de acompanhamento antes de habilitar a taxa. |

Filtros mínimos: período, assessor, equipe, segmento, UF, município e fonte. Oferecer agrupamento por assessor e visão consolidada com os mesmos filtros. Média geral é calculada a partir dos totais e denominadores, nunca pela média simples das médias dos assessores. Divisão por zero retorna “Sem dados”. Exibir tamanho da amostra, unidade, período e exclusões. Falhas e cancelamentos aparecem em contadores separados, sem entrar silenciosamente na média das buscas concluídas.

Atribuir extração ao solicitante registrado na criação da busca e interação ao autor registrado no evento. Mudança posterior do responsável da empresa não transfere produtividade histórica. Antes da autenticação, usar o membro local selecionado e indicar que a atribuição não é identidade autenticada. Registros antigos sem autoria conhecida ficam como “Não atribuído”.

### 16.2 Lembretes datas e acompanhamento após venda

Lembretes devem apoiar retornos ao cliente, acompanhamento de entrega e revisão após a venda. São registros persistentes vinculados a empresa e, quando aplicável, contato, oportunidade ou projeto. O primeiro escopo é interno ao aplicativo: lista de próximos/vencidos e aviso ao abrir. Não pressupor envio de e-mail, WhatsApp ou notificação do sistema operacional com o app fechado.

| ID | Fase e prioridade | Requisito e aceite |
|---|---|---|
| RF48 | 2 e 4 P0 | Registrar autor, solicitante, fonte e datas necessárias aos indicadores desde o CRM inicial; entregar agrupamento por assessor e consolidado na fase 4, com exportação respeitando filtros. |
| RF49 | 4 e 6B P0 | Usar um único serviço de cálculo para telas e relatórios. Aceite: totais e denominadores reconciliam com registros de origem; consolidado ponderado difere corretamente de média simples; acesso é filtrado antes da agregação. |
| RF50 | 2 e 4 P0 | Criar lembrete de pós-venda com título, responsável, vínculo, data/hora e situação. Lista exibe próximos, vencidos, concluídos e cancelados; reiniciar o app preserva os lembretes. |
| RF51 | 2 e 4 P0 | Reagendar, concluir ou cancelar lembrete. Reagendamento registra data anterior, nova data, autor e motivo opcional; concluir registra horário e resultado. Repetir confirmação não duplica evento. |
| RF52 | 4 P0 | Ao registrar venda ganha ou marco de entrega, oferecer criação de lembrete de retorno com data escolhida. Não impor prazo arbitrário nem criar duplicatas ao reabrir a tela; cancelamento da sugestão não impede concluir a venda. |
| RF53 | 4 e 6B P0 | Avisos internos apresentam contagem de vencidos e próximos, link para o cliente e ação de reagendar. Após login/permissões, apenas destinatários autorizados acessam texto e vínculo. Abrir aviso não conclui tarefa. |
| RF54 | 4 P0 | Alterar prazo de projeto ou marco identifica lembretes vinculados e oferece manter datas ou deslocar pelo mesmo intervalo. Mostrar alterações antes de confirmar; lembrete concluído/cancelado não é movido. |

Datas de negócio usam o fuso America/Sao_Paulo como padrão configurável; instantes são armazenados em UTC. Compromissos com apenas data usam campo de data separado, sem conversão artificial para meia-noite UTC. Atraso deriva da data limite e situação, sem substituir situação persistente por “atrasado”. Manter prazo original, prazo vigente e histórico de alterações quando aplicável.

Modelo adicional: reminder com id, organizationId, responsável, vínculos, titulo, dataLimite ou instanteLimite, fuso, situacao, concluidoEm e version; reminderEvent com alteração, ator e valores anterior/novo. Notificação interna referencia o lembrete e possui controle de leitura independente. Auditar mudanças de datas e evitar dupla gravação por reenvio.

### 16.3 Fases esforço e verificação

Fase 2: autoria, datas, lembretes simples e persistência. Fase 4: indicadores, consolidado, avisos e reagendamento de marcos. Fase 6B: aplicar permissões e destinatários reais. Fase 7: homologar datas e cálculos no cenário integrado. Login e integrações complexas permanecem no final, e a data limite continua 31/12/2026.

Estimativa adicional preliminar: 20 horas, distribuídas entre modelo/persistência (5 h), indicadores (6 h), interface e datas de lembretes (6 h) e verificação (3 h). Proposta de consumo de 20 das 38 horas de contingência originais, deixando 18 horas antes de considerar outros desvios. Confirmar saldo real no próximo marco; nenhum consumo de capacidade já foi demonstrado por implementação. E-mail, WhatsApp automático e lembretes recorrentes avançados ficam fora deste incremento.

Verificar: comparação entre média ponderada e média simples com assessores de volumes diferentes; período vazio; autoria desconhecida; mudança de responsável; acesso negado a agregados; lembrete em virada de dia; alteração concorrente; reagendamento após troca de prazo; abertura do app com compromisso vencido; prevenção de aviso duplicado. A taxa de retorno só entra na entrega após definição da janela e do evento que caracteriza retorno.

## 17 Referências de planejamento

- Estudo de viabilidade local: estudo-viabilidade-plataforma-comercial.docx, versão 1.0.
- Mapeamento do repositório desta conversa: frontend React/Vite, backend FastAPI, SQLite, Tauri e Playwright.
- Este plano define novos requisitos e metas. Não declara funcionalidades planejadas como já implementadas nem confirma quotas ou preços dos provedores.
- [Cloudflare Pages limites](https://developers.cloudflare.com/pages/platform/limits/) — franquias de build e arquivos da hospedagem.
- [Supabase planos](https://supabase.com/pricing) — banco, arquivos, egress e condições do Free.
- [Supabase pausa de projetos](https://supabase.com/docs/guides/platform/free-project-pausing) — pausa por baixa atividade.

## 18 Histórico de revisão

- 1.0 — cronograma e requisitos iniciais com término em 31/12/2026.
- 1.1 — uso interno explicitado; Cloudflare Pages substitui Vercel; Supabase Free como ponto de partida, estimativas de crescimento, RF43 a RF47, RNF11, retenção, medição, alertas e responsabilidade por Git e releases.
- 1.2 — referências visuais aprovadas incorporadas em documento próprio; menus e SVG especificados; mapa regional/satélite e integrações extras classificados; projeto de prospecção distinguido de projeto de entrega.
- 1.3 — indicadores por assessor e consolidado com cálculo independente do perfil, RF48 a RF54, lembretes de pós-venda, atualização de datas, autoria histórica, fases e esforço adicional estimado.
