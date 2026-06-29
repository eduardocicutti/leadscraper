# Lead Scraper Desktop — Adapti JE

## Contexto e objetivo
Transformar o `main.py` existente (FastAPI + Selenium + OpenPyXL já funcionais) em um app desktop local empacotado com Tauri 2. Nenhum membro da JE precisa de terminal — apenas clica no `.exe`.

---

## O que já existe (NÃO reescrever)
O arquivo `main.py` contém lógica de produção completa. Preserve integralmente:
- Rotas FastAPI: `POST /scrape`, `GET /status/{job_id}`, `GET /download/{job_id}`, `GET /`
- `scrape_worker()` — Selenium com Edge headless, extração de 15+ campos por lead
- `score_lead_adapti()` — sistema de score 0–100 com 5 dimensões
- `classify_porte()` — classificação de porte por heurística + keywords
- `build_whatsapp_link()` — geração de link wa.me com mensagem pré-escrita
- `generate_xlsx()` — planilha com 21 colunas, 3 abas, data validations, cores por temperatura
- Modelo `ScrapeRequest`: `segmento`, `cidade`, `estado`, `max_results`, `prospectador`

---

## Stack tecnológica

### Frontend (Interface)
- Tauri 2.x
- Vite 6 + TypeScript 5
- React 19
- Tailwind CSS 4
- TanStack Query 5 (polling de status)
- Zustand 5 (estado global)
- Axios 1 (chamadas ao FastAPI local)
- lucide-react (iconografia — proibido emojis como ícones de nav)

### Backend (já pronto — só empacotar)
- Python 3.12
- FastAPI + Uvicorn (servidor local oculto na porta 8000)
- Selenium 4 + webdriver-manager 4 (Edge headless)
- OpenPyXL 3 (geração de XLSX)
- PyInstaller 6 (compilar `main.py` → sidecar `.exe`)

### Persistência (novo — adicionar ao main.py)
- SQLite 3 via SQLModel
- Ver `BANCO_DE_DADOS.md` para schema completo

---

## Cronograma (5 dias)

**Dia 1 — Persistência**
- Adicionar SQLModel ao `main.py` existente sem quebrar nenhuma rota
- Salvar cada `scrape_worker` em `SearchHistory` + cada lead em `Lead`
- Criar rota `GET /history` retornando lista de buscas anteriores

**Dia 2 — Tauri + Sidecar**
- `tauri init` com React + Vite
- Configurar lifecycle: ao abrir o app, disparar o binário `scraper-sidecar` (PyInstaller)
- Configurar `tauri.conf.json` com `sidecar` apontando para o executável gerado

**Dia 3 — Interface React**
- Substituir o `index.html` atual pela interface React descrita em `FRONTEND.md`
- Implementar polling `GET /status/{job_id}` a cada 1.5s com TanStack Query

**Dia 4 — Histórico + Exportação**
- Tela de histórico lendo `GET /history`
- Botão de exportação chamando `GET /download/{job_id}` e salvando via Tauri dialog

**Dia 5 — Build e validação**
- `pyinstaller main.py --onefile --name scraper-sidecar`
- `tauri build` gerando `.exe` instalável
- Testar em máquina limpa (sem Python instalado)

---

## Contratos de API (Frontend ↔ Backend)

```typescript
// POST /scrape
body: { segmento: string; cidade: string; estado: string; max_results: number; prospectador: string }
response: { job_id: string }

// GET /status/{job_id}
response: {
  status: "pending" | "running" | "done" | "error"
  progress: number     // leads extraídos até agora
  total: number        // total de URLs encontradas
  log: string          // mensagem atual para exibir
  leads_count: number
  leads: Lead[]
}

// GET /download/{job_id}?segmento=&cidade=&estado=&prospectador=
response: application/vnd.openxmlformats (.xlsx)

// GET /history  (novo — Dia 1)
response: SearchHistory[]
```

```typescript
interface Lead {
  nome: string; categoria: string; nota: number | null
  avaliacoes: number | null; endereco: string; telefone: string
  is_whatsapp: boolean; whatsapp_link: string; site: string
  url_maps: string; porte: string; classificacao: string; score: number
  cidade: string; estado: string; prospectador: string
}
```
