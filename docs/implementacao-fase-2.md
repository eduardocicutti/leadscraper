# CRM local — primeiro incremento da fase 2

Data: 26/10/2026. Uso pessoal e interno da empresa; não é um produto SaaS comercial.

## Implementado

- Empresas: cadastro, edição, responsável, CNPJ opcional validado, localização, segmento, site, arquivamento e restauração sem exclusão.
- Contatos: cadastro e edição vinculados à empresa, telefone original e normalizado, cargo e e-mail.
- Busca de empresas por nome, cidade, nome do contato ou telefone; busca de contatos por nome, empresa ou telefone. Acentos e formatação do telefone não impedem a consulta.
- Listas de empresas, contatos e atividades com paginação padrão de 25, máximo de 100 e ordenação estável.
- Atividades: ligação, WhatsApp, e-mail, reunião, tarefa e lembrete; responsável, descrição, data de retorno, situação e resultado.
- Reagendamento preserva a atividade e registra datas anterior/nova na linha do tempo. Conclusão exige resultado; editar uma atividade já concluída preserva o instante original da conclusão.
- Linha do tempo por empresa com autor operacional e instante UTC. Datas de retorno são datas sem horário.
- Botão de inclusão na lista de leads: cria empresa/contato ou exige confirmação para vincular a cadastro existente identificado como possível duplicado. Não sobrescreve a empresa existente. Repetir a inclusão não duplica o cadastro.
- Controle de versão nas edições de empresa, contato e atividade. Alteração com versão antiga retorna conflito, sem sobrescrever dados.
- Migração SQLite numerada, transacional, com backup anterior e checksum registrado no log quando já existe banco. A conexão da migração é fechada explicitamente, inclusive em caso de erro.

Cadastrar empresa, importar lead, exportar planilha ou abrir WhatsApp não comprova abordagem. Apenas uma atividade explicitamente registrada informa o relacionamento.

## Contratos

Rotas novas em `/api/v1/crm`:

| Método | Caminho | Uso |
|---|---|---|
| GET / POST | `/empresas` | Listar / cadastrar |
| GET / PUT | `/empresas/{empresaId}` | Detalhar / editar e arquivar |
| POST | `/empresas/{empresaId}/contatos` | Cadastrar contato |
| PUT | `/empresas/{empresaId}/contatos/{contatoId}` | Editar contato |
| POST | `/empresas/{empresaId}/atividades` | Cadastrar atividade |
| PUT | `/empresas/{empresaId}/atividades/{atividadeId}` | Editar ou reagendar |
| GET | `/contatos` e `/atividades` | Listas paginadas |
| POST | `/selecionados/{selectedId}/converter` | Inclusão idempotente; `empresaId` opcional para vinculação explícita |

Listagem: `busca`, `pagina` e `tamanho`; empresas também aceitam `arquivadas`. Edições exigem `version`. Erros de negócio/validação retornam `code`, `message`, `fieldErrors` e `correlationId`; duplicidades incluem `candidatas`.

Organização local fixa no servidor. `X-Operador-Local` registra atribuição operacional e pode ser alterado pelo cliente: **não é autenticação nem autorização**. Não publicar este backend na internet. A busca do cabeçalho consulta menus e dados do CRM local.

O detalhe da empresa possui paginação independente de contatos, atividades e eventos, com limite de 25 registros por coleção em cada consulta.

### Terceiro incremento: busca global e paginação do detalhe

- Cabeçalho busca empresas por nome sem acentos, telefone com/sem pontuação e CNPJ completo com/sem máscara, além de continuar localizando menus. A busca por nome do contato retorna a empresa correspondente.
- Resultados identificam arquivadas, responsável, qualificação e último contato concluído por ligação, WhatsApp, e-mail ou reunião. Tarefa interna, lembrete, coleta e atividade pendente não preenchem último contato. Sem interação concluída aparece “Não registrado”.
- Selecionar resultado abre diretamente o cadastro, inclusive quando outra empresa já estava aberta. Enter abre o primeiro menu encontrado ou, na ausência de menu, o primeiro resultado estável do CRM. Escape ou saída do foco fecha os resultados. Consulta começa após dois caracteres e espera 300 ms de digitação; erro permite tentar novamente.
- `GET /api/v1/crm/busca` aceita `busca`, `pagina`, `tamanho` (padrão 25, máximo 100), inclui ativos e arquivados e mantém a organização local definida no servidor. A lista normal de empresas continua separando ativos de arquivados.
- `GET /api/v1/crm/empresas/{empresaId}` aceita `paginaContatos`, `paginaAtividades`, `paginaEventos`, todos a partir de 1. Arrays existentes são preservados no contrato, agora limitados a 25 itens. `paginacao` informa total, página e tamanho de cada coleção. Escritas e banco existente não foram alterados estruturalmente.
- 28 testes passaram. Novos cenários verificam busca por CNPJ, último contato real versus tarefa interna, arquivamento e páginas sem sobreposição em 26 contatos. TypeScript e build web verificados; dados privados não foram usados como massa de teste.
- Busca por telefone e abertura direta verificadas no navegador sobre o banco de prévia. Evidências locais em `docs/qa/fase-2-busca/`. A aprovação final de fidelidade visual segue pendente em `design-qa.md`.

### Segundo incremento: qualificação e filtros de retorno

- Qualificação disponível no detalhe: novo, em análise, qualificado e desqualificado. Desqualificar exige motivo; atualização mantém autor, instante, histórico e controle de versão. Salvar os mesmos valores com versão atual não cria evento nem incrementa versão.
- `PUT /empresas/{empresaId}/qualificacao`: recebe `situacao`, `motivo` e `version`. O detalhe passa a incluir `qualificacao`. O estado convertido não está disponível: depende da operação atômica com oportunidade na fase 4. RF15 permanece parcialmente entregue.
- `GET /atividades`: aceita `situacao` (`pendente`, `concluida`, `cancelada`), `prazo` (`vencidos`, `hoje`, `proximos`, `semData`) e `dataReferencia` em ISO. Os filtros são combinados com busca e paginação. Prazo restringe a atividades pendentes; concluídas/canceladas nunca reaparecem como vencidas.
- `dataReferencia` é obrigatória quando há filtro de prazo, evitando usar implicitamente a data UTC do servidor. A interface calcula a data em America/Sao_Paulo; “Futuros” considera qualquer data posterior, não uma janela arbitrária de sete dias. O corte por prazo é por dia, ainda sem horário de lembrete.
- 26 testes passaram, além de TypeScript e build Vite. Novos testes cobrem motivo obrigatório, conflito de versão, repetição sem evento extra, limites entre vencido/hoje/futuro, ausência de data e combinações de filtros.
- Qualificação e filtro de vencidos exercitados no navegador com dados fictícios do mesmo banco isolado. Capturas em `docs/qa/fase-2-qualificacao/`; verificadas larguras 360 e 768 px. Não houve alteração estrutural do banco neste incremento.

## Prévia isolada

- Interface: `http://127.0.0.1:1420/`.
- Backend de validação: `http://127.0.0.1:8010`, com `DB_PATH=F:\leadscraper\build\runtime\crm-preview.db`.
- `.env` local ignorado pelo Git aponta `VITE_API_URL` para a porta 8010. Não trocar silenciosamente para o banco instalado na porta 8000.
- Dados de demonstração são fictícios. O banco instalado em AppData não foi usado para testes de escrita.
- Para reiniciar: definir o mesmo `DB_PATH` e executar `.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8010`; iniciar o frontend com `npm run dev`.
- O backend instalado anterior não contém as novas rotas. Abrir apenas a interface nova com o sidecar antigo resulta em indisponibilidade do CRM, não em migração concluída.
- O instalador deve carregar `backend/migrations/*.sql`; o spec foi ajustado. Não foi gerado instalador neste incremento.

## Verificação

- 24 testes passaram: legado, cadastro, busca, duplicidade, validação, controle de versão, contatos, lembretes, conversão, persistência após reabertura, preservação do legado, backup e rollback da migração.
- TypeScript e build Vite passaram.
- Teste no navegador: cadastro fictício, busca por telefone, edição de contato, criação e reagendamento de lembrete, retorno à lista e persistência após recarga/reinício do backend.
- Detalhe inspecionado em 1536, 768 e 360 px. Sem transbordamento horizontal do documento nas duas larguras menores; tabelas usam rolagem própria.
- Evidências locais em `docs/qa/fase-2/`, ignoradas pelo Git.
- Build Tauri tentado, bloqueado porque `cargo` não está disponível no ambiente. Empacotamento nativo e instalador seguem sem validação.
- Pytest emite um aviso de depreciação do TestClient/HTTPX; não houve falha de teste por esse aviso.

## Próximos incrementos

1. Completar filtros de relacionamento e revisão dos critérios de aceite da fase 2; conversão em oportunidade segue dependente da fase 4.
2. Evoluir lembretes com horário e notificações, sem confundir data de retorno com instante de execução.
3. Serviço único de métricas por assessor e totais consolidados, conforme RF48–RF54, sem números fictícios.
4. Prosseguir com o mapa na fase 3 e projetos/oportunidades na fase 4. Autenticação, permissões e sincronização continuam nas fases previstas.

Não declarar a fase 2 inteira concluída, nem o visual final aprovado. Logo oficial e diferenças das telas legadas continuam registrados em `design-qa.md`.
