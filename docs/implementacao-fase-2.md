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

Organização local fixa no servidor. `X-Operador-Local` registra atribuição operacional e pode ser alterado pelo cliente: **não é autenticação nem autorização**. Não publicar este backend na internet. A interface continua com busca de menus no cabeçalho; a busca de dados fica nas telas do CRM neste incremento.

O detalhe da empresa ainda carrega o histórico vinculado sem paginação interna. Antes de volume maior, paginar contatos, atividades e eventos dentro do detalhe. As tabelas de qualificação e os contratos preliminares estão preparados, mas ainda não há fluxo de qualificação entregue.

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

1. Qualificação do lead, filtros de relacionamento, busca de dados no cabeçalho e paginação interna do detalhe.
2. Evoluir lembretes com filtros de vencimento e notificações, sem confundir data de retorno com instante de execução.
3. Serviço único de métricas por assessor e totais consolidados, conforme RF48–RF54, sem números fictícios.
4. Prosseguir com o mapa na fase 3 e projetos/oportunidades na fase 4. Autenticação, permissões e sincronização continuam nas fases previstas.

Não declarar a fase 2 inteira concluída, nem o visual final aprovado. Logo oficial e diferenças das telas legadas continuam registrados em `design-qa.md`.
