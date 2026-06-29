# Design System — Adapti Lead Scraper

## Identidade visual do produto

Este é um **app de operações internas** para membros de uma empresa júnior de tecnologia.
O público é técnico, usa a ferramenta diariamente, e o contexto é B2B/CRM.
A interface deve comunicar: precisão, controle, dados densos. Referências reais: **Linear**, **Raycast**, **Vercel Dashboard**, **Planetscale**.

**NÃO é:** um SaaS de marketing, um dashboard executivo, um produto consumer.

---

## ❌ Proibições absolutas (o que faz parecer IA)

```
- Cards com sombra (box-shadow, drop-shadow, shadow-lg/xl)
- rounded-2xl, rounded-3xl em qualquer elemento
- Gradientes em botões primários (use cor sólida)
- backdrop-blur em qualquer painel ou menu
- Emojis como ícones de navegação (usar lucide-react)
- Títulos de seção centralizados com linha decorativa embaixo
- Texto placeholder do tipo "Bem-vindo ao sistema"
- Animações em loop (pulse, bounce em ícones decorativos)
- Grid de "feature cards" com ícone + título + parágrafo
- Cor de destaque em múltiplos elementos ao mesmo tempo (1 cor quente por view)
- Bordas de progresso arredondadas com glow azul (clichê de AI)
- Badge "Beta" ou "New" em qualquer lugar
- Tabelas com linhas alternadas em cores pastel
```

---

## Tokens visuais

### Paleta (6 valores — não inventar outros)

```
--bg-base:     #0c1118   /* fundo da janela */
--bg-panel:    #0f1623   /* painéis internos */
--bg-input:    #0b1220   /* inputs, selects */
--border:      #1e2d45   /* todas as bordas */
--border-subtle: #162035 /* divisores internos */

--text-primary:   #e8edf5
--text-secondary: #8896ac
--text-muted:     #4a5568

--blue-action:  #2563eb   /* único botão CTA */
--blue-dim:     #1d3a6e   /* estado hover de itens de nav */
--blue-glow:    rgba(37,99,235,0.06)  /* radial de fundo */

/* Temperatura de leads — usar apenas nestas classes */
--hot:    #fca5a5  /* text */  --hot-bg:    rgba(239,68,68,0.08)
--warm:   #fcd34d  /* text */  --warm-bg:   rgba(234,179,8,0.08)
--cold:   #93c5fd  /* text */  --cold-bg:   rgba(59,130,246,0.08)
```

### Tipografia

```
Display (logo, títulos de view): "Geist Mono" — monospace técnico, sem serif
Body (labels, parágrafos):        system-ui, -apple-system, sans-serif
Data (tabela, métricas, código):  "JetBrains Mono", monospace
```

**Importar via CDN no index.html:**
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Geist+Mono:wght@400;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

**Scale de tipo (não usar outros tamanhos):**
```
10px / text-[10px]  → labels uppercase, cabeçalho de coluna
12px / text-xs      → metadata, timestamps, texto secundário
13px / text-[13px]  → body padrão, inputs
14px / text-sm      → itens de tabela principais
16px / text-base    → título de view ativo
20px / text-xl      → métricas numéricas grandes
```

### Espaçamento
Usar múltiplos de 4px. Nunca `p-5`, `p-7`, `gap-5`, `gap-7` — apenas `p-4`, `p-6`, `p-8`.

### Border-radius
```
rounded-sm (2px)  → badges de temperatura, tags
rounded-md (6px)  → inputs, botões, painéis
rounded-lg (8px)  → modal/overlay único
```

---

## Anatomia do layout (Split-Pane fixo)

```
┌──────┬────────────────────────────────┬──────────┐
│      │  HEADER (h-12, 48px)           │          │
│  S   ├────────────────────────────────┤          │
│  I   │  FILTER BAR (h-auto, p-4)      │  H       │
│  D   ├────────────────────────────────┤  I       │
│  E   │                                │  S       │
│  B   │  STATS ROW (6 métricas)        │  T       │
│  A   │                                │  Ó       │
│  R   ├────────────────────────────────┤  R       │
│      │                                │  I       │
│  w   │  LEADS TABLE (flex-1, scroll)  │  C       │
│  16  │                                │  O       │
│      │                                │          │
│      │                                │  w-72    │
└──────┴────────────────────────────────┴──────────┘
  64px         flex-1                      288px
```

- Todos os painéis separados por `border border-[#1e2d45]` — sem sombra, sem margin
- O painel de histórico começa colapsado, abre com o ícone History na sidebar
- Nenhuma área tem background branco ou cinza claro

---

## Assinatura visual (elemento único deste produto)

**Barra de extração com dados em tempo real no estilo terminal.**

Quando o scraper está rodando, a `StatusBar` deve parecer um log de terminal, não uma barra de progresso de SaaS:

```
┌─────────────────────────────────────────────────────────┐
│  ▶ EXTRAINDO                            14 / 30   46%   │
│  ─────────────────────────────────────────────────────  │
│  > Abrindo Google Maps: Clínicas · São Mateus ES        │
│  > Extraindo 14/30: Clínica Odonto Center              │
│  > Score calculado: 🔥 82 pts                           │
└─────────────────────────────────────────────────────────┘
```

Implementação:
- Fundo `#080d14`, borda `border-[#1e2d45]`, fonte `JetBrains Mono`
- Texto do log em `text-[#8896ac]`, prefixo `>` em `text-[#2563eb]`
- Barra de progresso: `height: 2px`, `background: #2563eb` — sem rounded, sem glow
- Contador `14 / 30` em `Geist Mono font-bold text-white`
- **Sem spinner animado** — usar um cursor piscando `|` via CSS `animate-[blink_1s_step-end_infinite]`

---

## Componentes — regras visuais específicas

### Sidebar (64px)
```
bg-[#0c1118] border-r border-[#1e2d45]

Ícone ATIVO:
  bg-[#1d3a6e] text-[#60a5fa]  ← sem border extra, sem rounded-xl

Ícone INATIVO:
  text-[#4a5568] hover:text-[#8896ac] hover:bg-[#0f1623]

Placeholder logo:
  w-8 h-8 bg-[#0f1623] border border-[#1e2d45] rounded-md
  font-["Geist_Mono"] text-xs font-bold text-[#2563eb] tracking-widest
  texto: "AJ" (não "AD")
```

### Filter Bar
```
Não usar section com grid solto — usar uma barra compacta de altura fixa:
  h-auto bg-[#0f1623] border-b border-[#1e2d45] px-6 py-3
  flex items-end gap-3 (não grid)

Label dos campos:
  text-[10px] font-semibold text-[#4a5568] uppercase tracking-[0.08em]
  (sem dois-pontos)

Input/Select:
  h-8 bg-[#0b1220] border border-[#1e2d45] rounded-md px-3
  text-[13px] text-[#e8edf5] font-["JetBrains_Mono"]
  focus:border-[#2563eb] focus:ring-0 outline-none

Botão "Iniciar Extração":
  h-8 px-4 bg-[#2563eb] hover:bg-[#1d4ed8] rounded-md
  text-[13px] font-semibold text-white
  ícone Play w-3.5 h-3.5 fill-current (não stroke)
  NUNCA: gradiente, sombra, rounded-lg+
```

### Tabela de leads

**Cabeçalho das colunas:**
```
sticky top-0 bg-[#0c1118]
text-[10px] font-semibold text-[#4a5568] uppercase tracking-[0.1em]
border-b border-[#1e2d45] px-3 py-2
```

**Linha de dado:**
```
border-b border-[#162035]   ← border-subtle, não border padrão
hover:bg-[#0f1623] transition-colors duration-100
text-[13px] text-[#8896ac] px-3 py-2.5

Nome da empresa: text-[#e8edf5] font-medium (não bold)
```

**Badge de temperatura:**
```
/* Quente */   bg-[rgba(239,68,68,0.08)] text-[#fca5a5] border border-[rgba(239,68,68,0.2)]
/* Morno */    bg-[rgba(234,179,8,0.08)] text-[#fcd34d] border border-[rgba(234,179,8,0.2)]
/* Frio */     bg-[rgba(59,130,246,0.08)] text-[#93c5fd] border border-[rgba(59,130,246,0.2)]
px-1.5 py-0.5 rounded-sm text-[10px] font-mono font-medium
Texto: "HOT" / "WARM" / "COLD" (não emojis na tabela)
```

**Célula de score:**
```
font-["JetBrains_Mono"] font-medium
>= 70: text-[#fca5a5]
45-69: text-[#fcd34d]
< 45:  text-[#8896ac]
```

**Botão WhatsApp na célula:**
```
h-6 px-2 bg-transparent border border-[#1e2d45] rounded-sm
text-[11px] text-[#4a5568] hover:border-[#25d366] hover:text-[#25d366]
transition-colors duration-100
texto: "WA ↗"  (não "Enviar", não ícone de telefone)
```

### Stats Row (6 métricas)
```
Não usar "cards" — usar uma barra inline horizontal:
  flex items-center gap-0 border border-[#1e2d45] rounded-md overflow-hidden

Cada métrica:
  flex-1 px-4 py-3 border-r border-[#1e2d45] last:border-r-0
  bg-[#0f1623]

Número:  text-xl font-["Geist_Mono"] font-bold text-[#e8edf5]
Label:   text-[10px] text-[#4a5568] uppercase tracking-[0.08em] mt-0.5

Quentes: número em text-[#fca5a5]
Mornos:  número em text-[#fcd34d]
```

### Painel de Histórico (w-72)
```
bg-[#0c1118] border-l border-[#1e2d45]

Header:
  h-10 px-4 border-b border-[#162035] flex items-center
  text-[11px] font-semibold text-[#4a5568] uppercase tracking-[0.1em]

Item de histórico:
  px-4 py-3 border-b border-[#162035] cursor-pointer
  hover:bg-[#0f1623] transition-colors duration-100

  Linha 1: text-[13px] text-[#8896ac] font-medium  → "Clínicas · São Mateus"
  Linha 2: text-[11px] text-[#4a5568] font-mono    → "30 leads · há 2h"

  Item ativo (busca atual):
    border-l-2 border-l-[#2563eb] bg-[#0f1623]
    Linha 1: text-[#e8edf5]
```

### Empty state (antes de buscar)
```
NÃO usar: ícone grande centralizado + título + subtítulo

Usar texto inline na área da tabela:
  text-[12px] font-["JetBrains_Mono"] text-[#1e2d45]
  alinhado à esquerda no topo da área, como um comentário de código:
  "// nenhuma extração iniciada"
```

### Header (h-12)
```
bg-[#0c1118] border-b border-[#1e2d45] px-6
flex items-center justify-between

Esquerda:
  text-[13px] font-["Geist_Mono"] font-semibold text-[#8896ac] uppercase tracking-[0.12em]
  texto: "PROSPECÇÃO · ADAPTI JE"

Direita:
  Badge de status: dot verde pulsante + texto "operacional"
  dot: w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse
  texto: text-[11px] text-[#4a5568] font-mono

  PLACEHOLDER para logo:
  /* TODO: substituir pela logo Adapti */
  /* <img src="./assets/logo-adapti.svg" className="h-4 opacity-70" /> */
```

---

## Micro-interações permitidas

```
✅ transition-colors duration-100  → hover em linhas de tabela e itens de nav
✅ transition-all duration-500     → largura da barra de progresso
✅ cursor piscando na StatusBar    → @keyframes blink { 50% { opacity: 0 } }
✅ opacity-0 → opacity-100 em leads novos aparecendo na tabela (duration-200)

❌ Animate-bounce, animate-ping em qualquer elemento decorativo
❌ Framer Motion ou qualquer lib de animação externa
❌ Transições de página / route transitions
❌ Skeleton loaders (usar o empty state de texto simples)
```

---

## Copy (textos da interface)

Regra: **verbos imperativos, sem marketing, sem "bem-vindo".**

```
Botão CTA:       "Iniciar extração"  (não "Buscar Leads", não "Prospectar Agora")
Status rodando:  "Extraindo..."      (não "Aguarde, estamos buscando...")
Status concluído:"Extração concluída — 28 leads"
Erro:            "Falha na extração. Verifique se o Edge está instalado."
Exportar:        "Exportar .xlsx"    (não "Baixar Planilha", não "Download")
Histórico vazio: "Nenhuma extração registrada"
Tabela vazia:    "// nenhuma extração iniciada"
Campo segmento:  placeholder "clínicas odontológicas, academias..."  (minúsculo, sem Ex:)
Campo cidade:    placeholder "São Mateus"
Campo estado:    placeholder "ES"
```

---

## Checklist antes de entregar ao Codex

O Codex deve verificar cada item antes de gerar o código final:

- [ ] Nenhum `box-shadow` ou `shadow-*` em qualquer elemento
- [ ] Nenhum `rounded-2xl` ou maior
- [ ] Botão CTA usa `bg-[#2563eb]` sólido — sem gradiente
- [ ] Tabela usa `border-[#162035]` nas linhas (border-subtle), não a border padrão
- [ ] Badges de temperatura usam texto "HOT/WARM/COLD" em `font-mono`, não emojis
- [ ] StatusBar parece terminal, não progress bar de SaaS
- [ ] Stats Row é uma barra horizontal contínua, não 6 cards separados
- [ ] Empty state usa texto `font-mono` comentário de código, não ícone + parágrafo
- [ ] Fontes Geist Mono e JetBrains Mono importadas e aplicadas nos roles corretos
- [ ] Paleta usa apenas os 6 valores base definidos neste documento
