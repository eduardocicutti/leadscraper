# Camada de Dados — SQLModel + SQLite

## Contexto
O `main.py` já existe com FastAPI funcionando. A tarefa é **adicionar** persistência SQLModel sem modificar nenhuma rota existente. Apenas:
1. Inserir os imports e modelos no topo do arquivo
2. Chamar `init_db()` no startup do FastAPI
3. Inserir registros nos pontos corretos dentro de `scrape_worker()`

---

## Schema

### Tabela `SearchHistory`
| Campo | Tipo | Obs |
|---|---|---|
| `id` | `int` PK autoincrement | |
| `keyword` | `str` | campo `segmento` do ScrapeRequest |
| `city` | `str` | campo `cidade` do ScrapeRequest |
| `state` | `str` | campo `estado` do ScrapeRequest |
| `status` | `str` | `"running"` → `"done"` / `"error"` |
| `leads_found` | `int` default 0 | atualizar ao final do scraper |
| `prospectador` | `str` | nome do membro da JE |
| `created_at` | `datetime` | `default=datetime.now` |

### Tabela `Lead`
| Campo | Tipo | Obs |
|---|---|---|
| `id` | `int` PK autoincrement | |
| `search_history_id` | `int` FK → `SearchHistory.id` cascade delete | |
| `company_name` | `str` | |
| `phone` | `str \| None` | |
| `is_whatsapp` | `bool` default False | |
| `whatsapp_link` | `str \| None` | |
| `website` | `str \| None` | |
| `address` | `str \| None` | |
| `rating` | `float \| None` | nota Google |
| `review_count` | `int \| None` | número de avaliações |
| `category` | `str \| None` | |
| `porte` | `str \| None` | |
| `score` | `int` default 0 | 0–100 |
| `classificacao` | `str \| None` | 🔥/🟡/❄️ |
| `maps_url` | `str \| None` | |

> **Regra:** `cascade="all, delete-orphan"` na relação `SearchHistory → leads`.

---

## Código a gerar

### Prompt para o Codex

```
Você é desenvolvedor Python sênior. Tenho um arquivo `main.py` com FastAPI já funcionando.
Preciso adicionar persistência SQLModel/SQLite SEM modificar nenhuma rota ou função existente.

Gere APENAS o bloco de código para inserir no início do main.py (após os imports existentes):

1. Imports: `from sqlmodel import Field, SQLModel, create_engine, Session, Relationship`
2. Variável global: `engine = None`
3. Modelo `SearchHistory(SQLModel, table=True)` com os campos do schema acima.
4. Modelo `Lead(SQLModel, table=True)` com os campos do schema acima, incluindo FK para SearchHistory com cascade delete.
5. Função `init_db(db_path: str)` que:
   - Recebe o caminho absoluto do .db (passado pelo Tauri via env var `DB_PATH`)
   - Atribui o engine global com `create_engine(f"sqlite:///{db_path}")`
   - Chama `SQLModel.metadata.create_all(engine)`
6. Evento FastAPI `@app.on_event("startup")` que chama `init_db(os.getenv("DB_PATH", "banco.db"))`
7. Função helper `save_search_history(job_id, segmento, cidade, estado, prospectador) -> int` que:
   - Cria um registro SearchHistory com status="running"
   - Retorna o ID gerado
8. Função helper `save_leads_batch(history_id: int, leads: list[dict])` que:
   - Recebe a lista de leads do dict `jobs[job_id]["leads"]`
   - Persiste todos na tabela Lead vinculados ao history_id
   - Atualiza SearchHistory.leads_found e SearchHistory.status="done"

Também mostre os dois pontos exatos no `scrape_worker()` onde inserir as chamadas:
- Logo após `jobs[job_id]["status"] = "running"` → chamar `save_search_history()`
- Logo antes de `driver.quit()` no bloco finally → chamar `save_leads_batch()`

Use type hints completos. Não use `Optional` — use `X | None`. Python 3.12.
```

---

## Rota nova: `GET /history`

Adicionar ao `main.py` após as rotas existentes:

```python
@app.get("/history")
async def get_history():
    with Session(engine) as session:
        records = session.exec(
            select(SearchHistory).order_by(SearchHistory.created_at.desc()).limit(50)
        ).all()
        return [r.model_dump() for r in records]
```

---

## Caminho do banco via Tauri

O Tauri passa o caminho do banco por variável de ambiente antes de iniciar o sidecar:

```rust
// src-tauri/src/main.rs
std::env::set_var("DB_PATH", app.path().app_data_dir()?.join("banco.db"));
```

Isso garante que o banco fique em `%APPDATA%/adapti-scraper/banco.db` no Windows.
