# Direção visual da Plataforma Comercial

Versão 1.0 • 22/10/2026

## Referência aprovada

As oito imagens fornecidas pelo usuário nesta conversa definem a linguagem visual principal da implementação. Reproduzir composição, menus, tratamento dos ícones, superfícies, botões e cores com alta fidelidade, adaptando a densidade para leitura e telas menores. As imagens 7 e 8 repetem a mesma composição de Projetos e Atividades e contam como uma referência de layout.

Este documento complementa o plano de requisitos. Não equivale à implementação das telas. Números, nomes, logos, estados e exemplos nas imagens são conteúdo demonstrativo; não comprovam integração ou dados reais.

## Estrutura comum

- Sidebar desktop de aproximadamente 220 a 240 px, com marca no topo, menu agrupado, divisórias discretas e painel do agente fixado na base quando houver altura disponível.
- Cabeçalho de aproximadamente 60 a 68 px: busca global à esquerda; notificações, avatar, nome e função à direita. Atalho Ctrl K abre a busca quando implementada.
- Conteúdo com margem de 24 a 32 px, título destacado, descrição curta e ação principal no canto superior direito.
- Cards de indicadores em linha, filtros em uma superfície independente e tabela com seleção, ordenação, ações e paginação.
- Painel contextual à direita para prévia de planilha, detalhes ou agenda, sem reduzir a tabela a colunas ilegíveis.
- Desktop largo segue as referências; telas menores reorganizam as colunas, recolhem a sidebar e usam rolagem interna de tabela ou cartões. Não encolher toda a página por escala.

## Menus e ícones SVG

Manter os rótulos e a ordem das referências. Utilizar Lucide já presente no projeto para os ícones de interface, exportados/renderizados como SVG, com traço e tamanhos consistentes.

| Grupo | Menu | Ícone sugerido |
|---|---|---|
| Operação | Prospecção | Search |
| Operação | Leads | ContactRound |
| Operação | Empresas | Building2 |
| Operação | Contatos | UsersRound |
| Operação | Oportunidades | Handshake |
| Operação | Atividades | CalendarDays |
| Operação | Projetos | FolderClosed |
| Gestão | Histórico | History |
| Gestão | Planilhas | Sheet |
| Gestão | Arquivos | File |
| Gestão | Equipe | Users |
| Sistema | Configurações | Settings |
| Sistema | Sobre | Info |
| Painel inferior | Agente local | Monitor |

A navegação permanece estável. Enquanto um módulo não existir, exibir sua disponibilidade e fase prevista de modo claro; não apresentar botões sem efeito como funcionalidades concluídas. Na fase de autorização, visibilidade e acesso seguem as permissões.

## Paleta e tipografia

Valores iniciais aproximados pela observação das referências. Validar a correspondência em comparação visual durante a implementação; não são cores extraídas de arquivo-fonte de design.

| Token | Valor inicial | Aplicação |
|---|---|---|
| background | #06111A | Fundo geral azul quase preto |
| sidebar | #07121C | Navegação lateral |
| surface | #0B1824 | Cards, campos e painéis |
| surfaceHover | #112435 | Hover e superfícies elevadas |
| border | #1B3448 | Contornos e divisórias discretos |
| primary | #0864FF | CTA, seleção e progresso |
| primaryHover | #287BFF | Hover dos botões principais |
| selected | #0B2C56 | Fundo do menu ativo |
| text | #F3F6FA | Texto principal |
| textSecondary | #AEC3DA | Descrições e informações secundárias |
| textMuted | #8097AE | Metadados |
| success | #00D889 | Sucesso e conexão confirmada |
| warning | #F5B91D | Aviso, pendência e atraso |
| danger | #FF4057 | Falha e ação destrutiva |
| purple | #A86BEB | Reuniões e categorias específicas |

Usar fonte sans-serif com boa leitura, preferencialmente Inter com licença incluída e hospedagem local, ou fonte de sistema equivalente. Texto principal 16 px; título 28 a 34 px; rótulos 14 px. Tabelas começam em 14 px na densidade confortável. Monoespaçada apenas para logs e dados técnicos. Espaçamentos em múltiplos de 4 px e raios de 6 a 10 px. Gradientes e sombras sutis, sem brilho excessivo.

## Componentes obrigatórios

- Botão primário azul com ícone à esquerda e texto; variantes secundária com contorno, discreta e destrutiva vermelha. Estados hover, foco, carregamento e desabilitado.
- Item ativo da sidebar com fundo azul escuro, borda/indicador azul à esquerda e texto claro.
- Cards com borda fina, indicador SVG em círculo tonal, valor principal e legenda. Tendência só aparece com cálculo real e período comparável.
- Inputs escuros com borda visível, rótulo acima, ícone opcional e erro abaixo. Seletores e datas seguem o mesmo padrão.
- Badges com ícone, texto e fundo tonal. Cor nunca é o único indicador de situação.
- Tabelas com cabeçalho discreto, hover de linha, checkbox acessível, alinhamento consistente, seleção e paginação. Seleção em massa mostra quantidade e ações disponíveis.
- Abas com ícone e sublinhado azul na opção ativa; controles de lista/quadro/calendário seguem a mesma linguagem.
- Avatares circulares com iniciais ou foto e agrupamento com contador. Indicador de presença exige informação real de sessão/heartbeat.
- Barras de progresso e anel do job com números equivalentes aos contadores reais.

## Aplicação por tela

| Referência | Tela | Composição a reproduzir | Entrega funcional |
|---|---|---|---|
| 1 | Prospecção | Formulário à esquerda; mapa à direita; resumo e últimas buscas abaixo; presets de quantidade e botão largo | Base visual na fase 1; mapa/fluxo na 3 |
| 2 | Histórico | Quatro indicadores, faixa de filtros e tabela com origem, status, duração e responsável | Adequação inicial na fase 1; dados novos conforme domínio |
| 3 | Sobre | Marca, versão, diagnóstico, banco, tecnologias, backup e atualização em cards | Fase 1 com recursos já existentes |
| 4 | Agente local | Cards de execução, recursos e conta; abas; job; logs e últimos resultados | Estrutura prevista desde fase 1; integração real na 6B |
| 5 | Planilhas | Indicadores, pesquisa, tabela e prévia/detalhes à direita | Fase 4 |
| 6 | Equipe | Indicadores, abas, árvore de organização à esquerda e membros à direita | Fases 6A/6B |
| 7 e 8 | Projetos | Indicadores, filtros, alternância de visualização, equipe e progresso por linha | Lista e progresso na fase 4; calendário avançado opcional |
| 7 e 8 | Atividades | Lista central com tipos e badges; agenda lateral; filtros | Cadastro/lista na fase 2; agenda resumida na 4 |

Leads, Empresas, Contatos, Oportunidades, Arquivos e Configurações não possuem tela própria completa nas imagens. Devem reutilizar o mesmo shell e componentes. Não inventar outra identidade visual para esses módulos.

## SVG marca e imagens

Todos os ícones de navegação e ações, ilustrações simples, estados vazios e o mapa seletor do Brasil devem usar SVG. Não embutir a screenshot inteira em SVG nem chamar um PNG encapsulado de vetor. Fotografias, avatares e imagens de satélite permanecem raster quando apropriado.

O logo Adapti deve usar o arquivo vetorial oficial quando disponível. As screenshots não fornecem o SVG original, sua geometria ou a fonte exata. Até obter o ativo, identificar qualquer reconstrução como provisória e não alterar o arquivo de marca existente. Armazenar vetores em diretório de assets com nome descritivo e origem/licença registrada; SVG importado deve ser sanitizado, sem scripts e recursos externos.

Logotipos de provedores devem vir de assets autorizados e manter atribuição/condições aplicáveis. Não substituir ícones por emojis: dentes, pastas coloridas, categorias e marcas precisam de vetores consistentes com o desenho das referências.

## Mapa e funcionalidades adicionais mostradas

A referência de Prospecção amplia o mapa inicialmente planejado: mostra mapa regional, satélite, clusters, área de busca, zoom e minimapa do Brasil. O seletor de UF continua P0 na fase 3. Mapa regional e clusters são evolução P1 nessa fase; satélite e busca por área dependem de provedor, atribuição, condições e orçamento verificados. Não utilizar tiles do Google extraídos da página como infraestrutura do CRM. O mapa de seleção é independente do mecanismo de scraping.

CPU, memória, consumo do navegador, último heartbeat e estado do agente só serão mostrados com medição. Enquanto indisponíveis, usar “Indisponível” ou “Sem conexão”, nunca valores fixos. Dashboard não deve mostrar crescimento percentual sem histórico comparável.

“Ver no Drive”, armazenamento em nuvem, notificações, organograma e calendário completo presentes nas imagens são referências de produto, não integrações já contratadas. Manter o aspecto visual; ativar ações quando houver implementação real. Integração Drive e central de notificações ficam P1 e passam por estimativa antes de entrar no compromisso de 2026.

Projetos nas imagens incluem campanhas de prospecção anteriores à venda. O modelo deve distinguir projeto comercial de prospecção e projeto de entrega após venda por campo tipoProjeto. Projeto de prospecção pode existir sem oportunidade ganha e agrupar buscas, empresas e tarefas; projeto de entrega mantém o vínculo comercial previsto. Não forçar campanhas de prospecção a simular vendas concluídas.

## Critérios de fidelidade visual

1. Comparar screenshot da implementação com a referência correspondente em viewport equivalente, especialmente 1672 × 941 e 1536 × 1024.
2. Verificar sidebar, cabeçalho, espaçamento, proporções dos painéis, cor ativa, contornos, ícones, hierarquia de texto e densidade das tabelas.
3. Aceitar conteúdo distinto quando necessário para dados reais, estado vazio, permissões e fase disponível, mantendo composição.
4. Validar em 1366, 768 e 360 px, zoom 200%, teclado e foco. Legibilidade prevalece sobre comprimir dados para caber na screenshot.
5. Registrar screenshot por tela entregue e pendências visuais. Tela só será considerada integrada quando ações e estados tiverem comportamento real.

## Prioridade e nomenclatura

As referências passam a reger a fase 1 e as telas seguintes, mantendo o cronograma funcional. O tema escuro é o padrão aprovado; tema claro conserva a mesma estrutura. Nas imagens, “Adapti” é marca organizacional e “Lead Scraper” é rótulo do produto antigo: aplicar “Plataforma Comercial” conforme decisão anterior, com identidade configurável e logo oficial quando disponível.
