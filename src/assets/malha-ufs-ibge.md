# Malha vetorial das unidades federativas

Os 27 contornos de `malha-ufs-ibge.json` foram gerados a partir da [API de Malhas do IBGE, v4](https://servicodados.ibge.gov.br/api/docs/malhas?versao=4), com geometria GeoJSON de qualidade mínima e recorte interno por UF.

- [Requisição utilizada](https://servicodados.ibge.gov.br/api/v4/malhas/paises/BR?formato=application%2Fvnd.geo%2Bjson&qualidade=minima&intrarregiao=UF), consultada em 24/11/2026.
- SHA-256 do GeoJSON original: `79ba7a1be8cde8397a22384c7d5a1fb75789980a5fd9f9fac8de744122e0f14a`.
- Fonte e autoria dos dados geográficos: IBGE. Conferir também os [termos do portal](https://www.ibge.gov.br/acesso-informacao/acoes-e-programas/politica-de-privacidade.html). A atribuição é exibida no mapa.
- Conversão para caminhos SVG pelo código IBGE de cada UF. Usa projeção equiretangular, longitude corrigida pelo paralelo de 15° sul, e coordenadas arredondadas a 0,1 unidade do quadro. Mantém anéis separados dos polígonos e usa um marcador sobre o DF para facilitar a seleção.
- O ativo local contém somente dimensões, coordenadas e caminhos. Sem arquivos SVG de terceiros, scripts, serviços externos em tempo de execução ou tiles.
