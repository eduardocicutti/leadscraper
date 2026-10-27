# Revisão visual do primeiro incremento

Data: 26/10/2026

## Alvo e evidências

Referências: oito imagens fornecidas na conversa, com destaque para a tela Sobre em `C:/Users/eduar/AppData/Local/Temp/codex-clipboard-f1c11cbf-5fab-4ccf-844e-71150a2d850a.png` e Prospecção em `C:/Users/eduar/AppData/Local/Temp/codex-clipboard-6653d7ab-a1c8-4f19-baa3-92b72f3f1b4c.png`.

Implementação: navegador interno em http://127.0.0.1:1420. Captura Sobre: `docs/qa/fase-1/sobre-desktop.png` (evidência local ignorada pelo Git). Referência Sobre 1536 × 1024; viewport solicitado 1536 × 1024; captura implementada com largura útil reduzida pela barra de rolagem. Comparação feita com as duas imagens no mesmo retorno visual. Não atribuir divergência de 15 px da barra à grade CSS. Teste adicional em 360 × 800, sem referência móvel fornecida.

## Histórico de ajustes

- Campo de segmento aparecia comprimido por legend flutuante: removido float; segunda captura confirma campo completo.
- Troca de página deslocava cabeçalho para fora da tela por foco automático: aplicado foco sem rolagem e retorno ao topo; captura posterior mostra cabeçalho.
- Sobre concentrava diagnóstico e caminho no card de banco: separadas seções Banco e Diagnóstico, alinhando a estrutura com a referência.
- Sidebar móvel fora da tela continuava acessível: visibility controlada; snapshot posterior confirma ausência do menu fechado na árvore acessível.

## Superfícies avaliadas

- Tipografia: sans-serif de sistema, hierarquia de título e texto secundário legíveis. Fonte exata da referência não fornecida.
- Layout: sidebar, cabeçalho, grid de cards e CTAs implementados; ainda há diferença de densidade vertical em Sobre e nas telas legadas.
- Cores: tokens escuros e azul de destaque aplicados; tema claro verificado separadamente com persistência.
- Assets: SVG Lucide de interface. Layers é identificação provisória, não reprodução do logo oficial Adapti; ativo oficial continua pendente.
- Conteúdo: dados reais do diagnóstico substituem exemplos. Menus futuros mostram fase e indisponibilidade. Sem números fictícios ou indicadores de produtividade simulados.

## Pendências de fidelidade

- P1: logo oficial da referência ainda não disponível em vetor. Não declarar marca fiel.
- P2: ajustar densidade dos cards Sobre e modernizar componentes legados de histórico/lista para a mesma escala.
- P2: primeira tela não contém o mapa regional da referência; mapa e catálogo de municípios pertencem à fase 3 e não foram simulados neste incremento.

## Verificações funcionais

Navegação, busca de menu com Enter, tema claro/escuro, densidade persistente após recarga, restauração da aparência, menu móvel e indicação de módulo futuro exercitados. Seleção de Academias e preset 50 atualizaram os campos correspondentes sem iniciar coleta. Consulta aos logs do navegador não retornou erros nesse percurso. Largura do documento não excedeu o viewport em 360 e 768 px. Build não substitui aprovação visual final.

Este relatório registra um primeiro incremento, não a aceitação da interface final das referências. Não bloquear testes e versionamento do incremento por chamar a interface final de concluída.

final result: blocked
