# Prospecção local — fase 3

O fluxo seleciona a UF pelo mapa ou pela lista, consulta os municípios pelo catálogo do IBGE e apresenta a revisão da localização, do segmento e da quantidade antes de iniciar a coleta. A execução continua no agente local e os resultados persistidos podem ser vinculados ao CRM.

## Contratos

| Método e rota | Uso |
|---|---|
| `GET /api/v1/localidades/municipios` | Consulta municípios por `uf` e termo opcional `busca`. Retorna itens com `codigo`, `nome` e `uf`, além de versão e fonte do catálogo. |
| `POST /api/v1/localidades/atualizar` | Atualiza o catálogo local a partir do IBGE. Uma falha mantém disponível a última cópia válida. |
| `POST /api/v1/prospeccoes` | Inicia a coleta com `segmento`, `estado`, `municipioCodigo`, `max_results` e `prospectador`. O servidor resolve o município pelo código e valida a UF e a quantidade inteira de 1 a 500. |
| `GET /status/{job_id}` | Mantém o contrato de acompanhamento e informa os contadores medidos. Com `somenteProgresso=true`, os resultados só são enviados quando a coleta chega ao estado terminal. |

O catálogo inicial acompanha o sidecar em `backend/data/municipios-ibge.json`. A atualização grava uma cópia validada no diretório do banco local. A rota `POST /scrape` continua disponível aos clientes legados.

O campo `coletados` conta os resultados gravados. `extraidos` conta os detalhes disponíveis, inclusive os que ficaram só na sessão devido a uma falha de gravação. A API também informa processados, falhas de extração, falhas de persistência e duração. Resultados gravados incluem o identificador do histórico e podem ser convertidos no CRM. A origem `source` e o `runId` identificam a fonte e a prospecção persistida.

## Origem dos dados

- Municípios e códigos oficiais: [API de Localidades do IBGE](https://servicodados.ibge.gov.br/api/docs/localidades).
- Malha das UFs: [API de Malhas do IBGE](https://servicodados.ibge.gov.br/api/docs/malhas?versao=4). A [origem do ativo vetorial](../src/assets/malha-ufs-ibge.md) registra a consulta, o checksum e as transformações.

O catálogo inicial contém 5.571 localidades com códigos únicos, cobrindo as 27 UFs. A atualização foi validada contra a API do IBGE em cache temporário. O executável local gerado com o PyInstaller foi iniciado com banco temporário e retornou Campinas/SP, código IBGE 3509502, a partir do catálogo embutido. A compilação do instalador Tauri continua pendente.

## Verificação

A suíte completa passou com 50 testes e o build web compilou. A homologação no Edge usou banco fictício e coleta simulada. Validou mapa e lista, teclado, cache, revisão da busca, falha parcial e total, conversão e deduplicação no CRM e recuperação após reiniciar o backend. As evidências estão em `build/homologacao-fase3-zz5_11_7/matriz-homologacao.md`, com capturas em 1536, 1366, 768 e 360 px.
