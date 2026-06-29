# Lead Scraper

Aplicativo desktop para prospecção de leads no Google Maps. Busca estabelecimentos por segmento e localização, qualifica com score comercial e exporta planilha Excel.

---

## Stack

| Camada | Tecnologia |
|--------|------------|
| Interface | React 19, TypeScript, Vite, Tailwind CSS 4 |
| Desktop | Tauri 2 (WebView2 no Windows) |
| API | FastAPI + Uvicorn (`localhost:8000`) |
| Scraping | Selenium 4 + Microsoft Edge (headless) |
| Banco | SQLite via SQLModel |
| Exportação | OpenPyXL (.xlsx) |

---

## Pré-requisitos

- **Node.js 18+** e npm
- **Python 3.10+**
- **Rust** (para builds Tauri) — [rustup.rs](https://rustup.rs)
- **Microsoft Edge** (já incluso no Windows 10/11)

---

## Instalação

### Dependências Python

```powershell
pip install fastapi uvicorn selenium webdriver-manager openpyxl sqlmodel
```

Ou use o script:

```powershell
.\install.bat
```

### Dependências Node

```powershell
npm install
```

---

## Como rodar

### Modo desenvolvimento (recomendado)

Em um terminal, inicie o backend:

```powershell
python main.py
```

Em outro terminal, inicie o app desktop:

```powershell
npm run tauri dev
```

O frontend carrega em `http://127.0.0.1:1420` e comunica com a API em `http://127.0.0.1:8000`.

### Apenas backend (sem Tauri)

```powershell
python -m uvicorn main:app --port 8000
```

> O arquivo `roda.bat` abre o navegador em `:8000`, mas a interface React exige o Vite ou o build em `dist/`. Prefira `npm run tauri dev` ou `npm run dev` + backend separado.

### Build de produção

```powershell
npm run build
npm run tauri build
```

O instalador `.exe` é gerado em `src-tauri/target/release/bundle/`.

O sidecar Python precisa ser compilado com PyInstaller antes do build Tauri — veja `src-tauri/binaries/README.md`.

---

## Como usar

1. Selecione o **prospectador** no formulário (as iniciais aparecem no avatar da sidebar).
2. Informe **segmento**, **cidade**, **estado** e **quantidade** de leads.
3. Clique em **Iniciar extração** e acompanhe o progresso na barra de status.
4. Ao concluir, revise a tabela e clique em **Exportar .xlsx**.

O histórico de buscas fica no painel lateral (ícone de relógio).

---

## Planilha exportada

A exportação gera um `.xlsx` com três abas:

- **Página1** — leads com colunas de CRM (responsável, estágio, empresa, telefone, ramo, porte, nota, score, temperatura, links).
- **Score** — legenda do sistema de pontuação.
- **Resumo** — totais da coleta (quentes, mornos, frios, WhatsApp, sites).

---

## Sistema de score (0–100)

| Dimensão | Critério | Pontos |
|----------|----------|--------|
| Presença digital | Sem site | 25 |
| Presença digital | Com site | 5 |
| Avaliações Google | ≥ 100 / 50–99 / 10–49 / 1–9 | até 20 |
| Nota Google | ≥ 4.5 / 4.0–4.4 / 3.5–3.9 | até 15 |
| Fit de segmento | Segmento com alto potencial digital | 20 |
| Contato | Tem telefone | 10 |
| Porte | Grande / Média / Pequena / Micro / MEI | até 15 |

**Temperatura:** 🔥 Quente (≥ 70) · 🟡 Morno (45–69) · ❄️ Frio (&lt; 45)

---

## API local

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/scrape` | Inicia uma busca |
| `GET` | `/status/{job_id}` | Progresso e leads em tempo real |
| `GET` | `/download/{job_id}` | Download do Excel |
| `GET` | `/history` | Últimas 50 buscas |
| `GET` | `/health` | Health check (usado pelo Tauri) |

---

## Estrutura do projeto

```
lead_scraper/
├── backend/             # API, domínio, repositórios e serviços
│   ├── api/             # FastAPI app e rotas
│   ├── domain/          # modelos, score, whatsapp
│   ├── repositories/    # SQLite
│   └── services/        # scraping, export, jobs
├── src/                 # Frontend React
├── src-tauri/           # Shell Tauri + sidecar
├── main.py              # Entry point do backend
├── install.bat          # Instala deps Python
├── scraper-sidecar.spec # PyInstaller
└── package.json
```

---

## Problemas comuns

**Backend não responde**  
Confirme que `python main.py` está rodando e que a porta 8000 está livre.

**Erro ao iniciar Edge**  
Atualize o Microsoft Edge ou verifique se o `webdriver-manager` consegue baixar o driver.

**Nenhum lead encontrado**  
Tente outro segmento ou cidade. O Google Maps pode limitar acesso temporariamente — aguarde alguns minutos.

**Exportação indisponível**  
A busca precisa terminar com status `done` antes de exportar.

**Logs**  
O backend grava em `backend.log` ao lado do arquivo `banco.db`.
