# Lead Scraper

Aplicativo desktop para prospecção de leads no Google Maps. Busca estabelecimentos por segmento e localização, qualifica com score comercial e exporta planilha Excel.

---

## Stack

| Camada | Tecnologia |
|--------|------------|
| Interface | React 19, TypeScript, Vite, Tailwind CSS 4 |
| Desktop | Tauri 2 (WebView2 no Windows) |
| API | FastAPI + Uvicorn (`localhost:8000`) |
| Scraping | Playwright + Chromium (headless) |
| Banco | SQLite via SQLModel |
| Exportação | OpenPyXL (.xlsx) |

---

## Pré-requisitos

- **Node.js 18+** e npm
- **Python 3.10+**
- **Rust** (para builds Tauri) — [rustup.rs](https://rustup.rs)

---

## Instalação

### Dependências Python

```powershell
pip install fastapi uvicorn playwright openpyxl sqlmodel pyinstaller
python -m playwright install chromium
```

Ou use o script:

```powershell
.\install.bat
```

Para voltar ao Selenium legado: `$env:BROWSER_ENGINE="selenium"` antes de iniciar o backend.

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
.\build-sidecar.bat
npm run tauri build
```

O instalador `.exe` é gerado em `src-tauri/target/release/bundle/`.

`build-sidecar.bat` compila o backend com PyInstaller, baixa o Chromium do Playwright e copia tudo para `src-tauri/binaries/`. Detalhes em `src-tauri/binaries/README.md`.

---

## Como usar

1. Selecione o **prospectador** no formulário (as iniciais aparecem no avatar da sidebar).
2. Informe **segmento**, **cidade**, **estado** e **quantidade** de leads.
3. Clique em **Iniciar extração** e acompanhe o progresso na barra de status.
4. Ao concluir, revise a tabela, marque leads com **checkbox** e clique em **Salvar selecionados** para a Lista Preferencial.
5. Exporte a busca atual com **Exportar .xlsx**.

### Menu lateral

| Ícone | Tela | Função |
|-------|------|--------|
| Lupa | Prospecção | Nova extração e resultados |
| Estrela | Lista Preferencial | Leads salvos, mensagem base, envio via WhatsApp |
| Arquivo | Prospecções Passadas | Histórico completo: abrir, exportar, reler, excluir |
| Relógio | Histórico rápido | Painel lateral para reabrir buscas recentes |

### Lista Preferencial

- Salve leads de várias buscas sem duplicar (por URL do Maps, telefone ou nome + cidade).
- Edite a **mensagem base** com variáveis: `{empresa}`, `{segmento}`, `{cidade}`, `{estado}`, `{prospectador}`.
- Clique em **Atualizar links** para regenerar os links do WhatsApp.
- Opcionalmente, defina uma **mensagem customizada** por lead.
- Use **Enviar** para abrir o WhatsApp com a mensagem preenchida.

### Prospecções passadas

- Filtre buscas por segmento, cidade, estado e status.
- **Abrir** — reabre a busca como se tivesse acabado de extrair.
- **Exportar** — gera planilha `.xlsx` do histórico.
- **Reler** — reabre cada lead no Maps e atualiza telefone, site, nota, score etc.
- Selecione várias prospecções e use **Reler N** para releitura em lote (com dedupe).

---

## Planilha exportada

A exportação gera um `.xlsx` com três abas:

- **Página1** — leads com colunas de CRM (responsável, estágio, empresa, telefone formatado, ramo, porte, nota, score, temperatura, link WhatsApp, links).
- **Score** — legenda do sistema de pontuação.
- **Resumo** — totais da coleta (quentes, mornos, frios, WhatsApp, sites).

A coluna de telefone exporta apenas o número formatado: celular `(XX) XXXXX-XXXX`, fixo `(XX) XXXX-XXXX`. O link do WhatsApp fica em coluna separada.

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

**Temperatura:** Quente (≥ 70) · Morno (45–69) · Frio (&lt; 45)

---

## API local

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/scrape` | Inicia uma busca |
| `GET` | `/status/{job_id}` | Progresso e leads em tempo real |
| `GET` | `/download/{job_id}` | Download do Excel (job ativo) |
| `GET` | `/history` | Últimas 50 buscas |
| `GET` | `/history/{id}` | Detalhe de uma busca + leads |
| `POST` | `/history/{id}/refresh` | Releitura assíncrona dos leads salvos |
| `POST` | `/history/refresh-batch` | Releitura em lote (`history_ids`) |
| `DELETE` | `/history/{id}` | Exclui uma prospecção |
| `GET` | `/history/{id}/download` | Exporta planilha do histórico |
| `GET` | `/selected-leads` | Lista leads da Lista Preferencial |
| `POST` | `/selected-leads` | Salva leads selecionados |
| `PATCH` | `/selected-leads/{id}` | Edita notas, prospectador ou mensagem customizada |
| `DELETE` | `/selected-leads/{id}` | Remove da lista |
| `GET/PUT` | `/selected-leads/message-template` | Template global de mensagem |
| `POST` | `/selected-leads/refresh-links` | Atualiza links WhatsApp em lote |
| `POST` | `/selected-leads/{id}/refresh-message` | Atualiza link WhatsApp de um lead |
| `GET` | `/health` | Health check (usado pelo Tauri) |

---

## Estrutura do projeto

```
lead_scraper/
├── backend/             # API, domínio, repositórios e serviços
│   ├── api/             # FastAPI app e rotas
│   ├── adapters/        # Playwright (fallback: Selenium via BROWSER_ENGINE)
│   ├── domain/          # modelos, score, whatsapp
│   ├── ports/           # interfaces (BrowserPort)
│   ├── repositories/    # SQLite
│   ├── scrapers/        # Google Maps
│   └── services/        # orquestração, export, jobs, releitura
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

**Erro ao iniciar navegador**  
Rode `python -m playwright install chromium`. Se persistir, tente `$env:BROWSER_ENGINE="selenium"` como fallback.

**Nenhum lead encontrado**  
Tente outro segmento ou cidade. O Google Maps pode limitar acesso temporariamente — aguarde alguns minutos.

**Exportação indisponível**  
A busca precisa terminar com status `done` antes de exportar.

**Logs**  
O backend grava em `backend.log` ao lado do arquivo `banco.db`.
