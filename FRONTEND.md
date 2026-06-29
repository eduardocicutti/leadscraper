# Interface React — Adapti Lead Scraper

## Regras estéticas (aplicar em TODOS os componentes)
- **Proibido:** cards brancos/cinzas flutuantes, emojis como ícones de nav, `rounded-2xl`/`3xl`, `backdrop-blur` em menus
- **Obrigatório:** ícones via `lucide-react`, `rounded-md` ou `rounded-lg`, painéis sólidos separados por `border-slate-800`
- Paleta base: fundo `#0f172a`, painel interno `#090d16`, borda `border-slate-800/60`, texto primário `slate-100`
- Fonte: `font-mono` para dados de tabela, `font-sans` para UI

---

## Estrutura de arquivos

```
src/
├── App.tsx                  # Provider raiz (QueryClient + Zustand)
├── store.ts                 # Zustand store
├── api.ts                   # Axios — baseURL http://localhost:8000
├── components/
│   ├── Layout.tsx           # Shell do app (sidebar + main)
│   ├── SearchPanel.tsx      # Formulário de busca + botão iniciar
│   ├── StatusBar.tsx        # Barra de progresso em tempo real
│   ├── LeadsTable.tsx       # Tabela de resultados
│   ├── HistoryPanel.tsx     # Painel de histórico (sidebar direita)
│   └── StatsRow.tsx         # Contadores de 🔥/🟡/❄️/total
```

---

## Layout raiz — `Layout.tsx`

Estrutura de colunas fixas inspirada em VS Code / Linear:

```tsx
<div className="min-h-screen w-full bg-[#0f172a] text-slate-100 font-sans">
  {/* Glow de fundo */}
  <div className="fixed inset-0 z-0 pointer-events-none"
    style={{ backgroundImage: "radial-gradient(circle 800px at 50% 50%, rgba(59,130,246,0.08), transparent)" }} />

  <div className="relative z-10 flex h-screen w-full">
    {/* Sidebar 64px */}
    <aside className="w-16 h-full bg-[#090d16]/80 border-r border-slate-800/60 flex flex-col items-center py-6 justify-between">
      {/* Placeholder logo: div 36x36 bg-blue-600/20 border border-blue-500/30 rounded-lg texto "AD" */}
      {/* Nav: ícones Search (ativo) e History (lucide-react), sem texto */}
      {/* Rodapé: ícone Settings */}
    </aside>

    {/* Conteúdo principal */}
    <main className="flex-1 h-full flex flex-col bg-transparent">
      {/* Header 56px com título + badge Online + assinatura "BY ADAPTI JE" */}
      <header className="h-14 border-b border-slate-800/60 px-6 flex items-center justify-between bg-[#090d16]/30">
        {/* PLACEHOLDER LOGO: espaço reservado com comentário para substituir por <img src="./assets/logo.svg" /> */}
      </header>
      {/* Área de trabalho com overflow-y-auto */}
      <div className="flex-1 p-6 flex flex-col gap-6 overflow-y-auto">
        {children}
      </div>
    </main>
  </div>
</div>
```

---

## Componentes

### `SearchPanel.tsx`
Campos em grid 3 colunas + linha separada para prospectador:

| Campo | Tipo | Placeholder |
|---|---|---|
| `prospectador` | `<select>` | Eduardo / Murilo / Sofia / Ydian / Gabriel |
| `segmento` | `<input>` | Ex: Clínicas odontológicas, Academias |
| `cidade` | `<input>` | Ex: São Mateus |
| `estado` | `<input>` | Ex: ES |
| `max_results` | `<select>` | 10 / 20 / 30 / 50 |

Ao submeter: `POST /scrape` → armazena `job_id` no Zustand store → ativa polling.

Botão "Iniciar Extração":
- Estado idle: ícone `Play` (lucide) + texto
- Estado running: ícone `Loader2 animate-spin` + "Extraindo..."
- Desabilitado enquanto `status === "running"`

Estilo dos inputs:
```tsx
className="w-full h-9 bg-[#0b1322] border border-slate-700/60 rounded-md px-3 text-sm 
           text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500/60 transition-colors"
```

---

### `StatusBar.tsx`
Visível apenas quando `status !== "idle"`. Lê do Zustand.

```tsx
<div className="bg-[#090d16]/40 border border-slate-800/60 rounded-lg p-4">
  <div className="flex justify-between text-xs text-slate-400 mb-2">
    <span>{log}</span>
    <span>{progress}/{total}</span>
  </div>
  <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
    <div className="h-full bg-blue-500 transition-all duration-500 rounded-full"
         style={{ width: `${(progress/total)*100}%` }} />
  </div>
</div>
```

---

### `StatsRow.tsx`
6 métricas em grid após conclusão:

| Stat | Valor calculado de `leads[]` |
|---|---|
| Total | `leads.length` |
| 🔥 Quentes | `filter(l => l.classificacao.includes("Quente")).length` |
| 🟡 Mornos | `filter(l => l.classificacao.includes("Morno")).length` |
| ❄️ Frios | `filter(l => l.classificacao.includes("Frio")).length` |
| Com WhatsApp | `filter(l => l.is_whatsapp).length` |
| Com Site | `filter(l => l.site).length` |

Cada stat:
```tsx
<div className="bg-[#090d16]/40 border border-slate-800/60 rounded-lg p-4 text-center">
  <div className="text-2xl font-bold text-slate-100">{value}</div>
  <div className="text-[10px] text-slate-500 uppercase tracking-wider mt-1">{label}</div>
</div>
```

---

### `LeadsTable.tsx`
Tabela com `overflow-x-auto`. Colunas visíveis:

| # | Coluna | Campo | Largura |
|---|---|---|---|
| 1 | Temp. | `classificacao` (badge colorido) | 80px |
| 2 | Score | `score` | 60px |
| 3 | Empresa | `nome` (bold) | 220px |
| 4 | Categoria | `categoria` | 150px |
| 5 | Porte | `porte` | 120px |
| 6 | Telefone | `telefone` + ícone WhatsApp se `is_whatsapp` | 140px |
| 7 | Nota ⭐ | `nota` | 60px |
| 8 | Aval. | `avaliacoes` | 70px |
| 9 | Site | ícone `ExternalLink` se `site` existe | 60px |
| 10 | Maps | ícone `MapPin` link para `url_maps` | 60px |
| 11 | WA | botão "Enviar" se `is_whatsapp` (abre `whatsapp_link`) | 80px |

Badge de temperatura:
```tsx
// 🔥 Quente → bg-red-500/10 text-red-400 border border-red-500/20
// 🟡 Morno  → bg-yellow-500/10 text-yellow-400 border border-yellow-500/20
// ❄️ Frio   → bg-blue-500/10 text-blue-400 border border-blue-500/20
className="px-2 py-0.5 text-[10px] font-medium rounded-md border"
```

Cabeçalho da tabela:
```tsx
<thead>
  <tr className="border-b border-slate-800/60">
    <th className="px-3 py-3 text-left text-[10px] font-semibold text-slate-500 uppercase tracking-wider bg-[#090d16]/60">
```

Estado vazio (antes de buscar):
```tsx
<div className="flex-1 flex items-center justify-center text-slate-600 text-sm font-mono">
  Aguardando início da prospecção...
</div>
```

Botão exportar (só aparece quando `status === "done"`):
```tsx
<button onClick={handleDownload}
  className="h-8 px-3 bg-slate-800 hover:bg-slate-700 border border-slate-700 
             text-slate-200 text-xs font-medium rounded-md flex items-center gap-1.5">
  <Download className="w-3.5 h-3.5"/> Exportar .xlsx
</button>
```
`handleDownload`: `GET /download/{job_id}?segmento=...` → `URL.createObjectURL(blob)` → clique programático em `<a>`.

---

### `HistoryPanel.tsx`
Painel lateral direito (320px) separado por `border-l border-slate-800/60`.
Exibe resultado de `GET /history`. Cada item é um row clicável que recarrega os leads daquela busca.

```tsx
<div className="w-80 h-full bg-[#090d16]/60 border-l border-slate-800/60 flex flex-col">
  <div className="p-4 border-b border-slate-800/60">
    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Histórico</span>
  </div>
  <div className="flex-1 overflow-y-auto">
    {history.map(item => (
      <div className="px-4 py-3 border-b border-slate-800/30 hover:bg-slate-800/20 cursor-pointer">
        <div className="text-xs font-medium text-slate-300">{item.keyword} · {item.city}</div>
        <div className="text-[10px] text-slate-500 mt-0.5">{item.leads_found} leads · {formataData(item.created_at)}</div>
      </div>
    ))}
  </div>
</div>
```

---

## Zustand store — `store.ts`

```typescript
interface AppStore {
  jobId: string | null
  status: "idle" | "pending" | "running" | "done" | "error"
  progress: number
  total: number
  log: string
  leads: Lead[]
  searchParams: { segmento: string; cidade: string; estado: string; prospectador: string } | null
  setJob: (jobId: string, params: AppStore["searchParams"]) => void
  updateStatus: (data: StatusResponse) => void
  reset: () => void
}
```

---

## Polling com TanStack Query

```typescript
// Em SearchPanel.tsx ou componente pai
const { data } = useQuery({
  queryKey: ["status", jobId],
  queryFn: () => api.get(`/status/${jobId}`).then(r => r.data),
  enabled: !!jobId && status !== "done" && status !== "error",
  refetchInterval: 1500,
})

useEffect(() => {
  if (data) updateStatus(data)
}, [data])
```

---

## api.ts

```typescript
import axios from "axios"
export const api = axios.create({ baseURL: "http://localhost:8000" })
```

---

## Notas de implementação
- O app React substitui completamente o `index.html` existente. Tauri serve o bundle Vite.
- O FastAPI continua na porta 8000 como sidecar. O frontend nunca chama APIs externas.
- Ao exportar `.xlsx`, usar `window.__TAURI__.dialog.save()` para abrir o diálogo nativo de "Salvar como" com filtro `.xlsx`.
- `HistoryPanel` aparece na view "Histórico" (ícone History na sidebar). View padrão é "Busca" (ícone Search).
