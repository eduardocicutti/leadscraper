# Implementação da fase 1

Primeiro incremento • 26/10/2026

## Implementado

- Navegação com todos os menus das referências, busca de menus e atalho Ctrl K.
- Layout com sidebar, cabeçalho, identificação do operador local e estado real do backend.
- Tokens de tema escuro/claro, densidade e escala de texto com persistência neste navegador.
- Componentes Botao e Painel; diretórios por funcionalidade e configuração central do nome/API.
- Formulário de extração com segmentos sugeridos, presets, validação de quantidade e erro sem limpar entradas.
- Página Sobre com diagnóstico, backup, restauração e atualização Tauri.
- Página do agente com informações realmente disponíveis no backend atual.
- Acesso às importações e exportações existentes pelo menu Planilhas.
- Módulos futuros identificados como em preparação, sem cadastros ou dados simulados.
- CI de tipos/build e regressão da API; dependências Python diretas fixadas e ambiente virtual local.
- Validação de 1 a 500 leads no servidor, incluindo rejeição de quantidades fracionárias.

## Execução

Frontend: `npm ci`, depois `npm run dev`. Backend: Python 3.12 com `.venv`, `python -m pip install -r requirements.txt -r requirements-dev.txt` e `python main.py`. Usar o ambiente virtual para os comandos Python.

Copiar `.env.example` para `.env` se necessário. `VITE_API_URL` configura o destino da API; não colocar segredos em variáveis públicas. URLs diferentes também exigem CORS compatível no backend.

Na máquina desta implementação, npm foi executado pelo pacote npm 10 obtido via pnpm do runtime disponível. Foram usados o mesmo package-lock.json e o comando npm ci. Nenhuma mudança de gerenciador ou lockfile foi feita.

## Verificações e limitações

Nove casos de teste da API passaram com bancos temporários: cinco regressões existentes e quatro quantidades inválidas. A instalação inicialmente trouxe SQLModel 0.0.48, que exigiu timezone e quebrou o modelo legado de datas; SQLModel 0.0.27 e SQLAlchemy 2.0.44 foram fixados e a regressão passou, sem migração destrutiva das datas existentes. Há aviso de depreciação do TestClient/httpx na versão instalada do Starlette.

Typescript e build Vite passaram. Interface inspecionada no navegador interno, com alteração de tema/densidade, persistência após recarga, navegação e revisão responsiva. Evidências locais ficam em docs/qa e não entram no Git.

O backend instalado existente foi apenas consultado para diagnóstico. Testes de gravação usam bancos temporários. Não foi iniciada coleta real nem restaurado banco do usuário. Build do instalador Windows e fluxo de atualização nativa ainda precisam de validação em ambiente Tauri com Rust e sidecar.

## Próximos incrementos

Completar contratos e contexto do CRM, refinar fidelidade visual das telas legadas e controles de erro, preparar cadastro persistente de empresas/contatos. Mapa é fase 3, CRM é fase 2 e autenticação é fase 6. O ícone Layers é identificação provisória da aplicação: o SVG oficial da Adapti continua pendente. Não declarar correspondência exata de marca ou interface final.
