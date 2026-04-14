# IDIC preliminar do Sudeste

Este relatorio combina indicadores discursivos extraidos dos PDIs com um quadro institucional preenchivel para organograma, estrutura e capacidade instalada da cultura.

- Universidades avaliadas: 17
- Base manual: /Users/gladstonmoreira/Documents/New project/pdi_analise/data/idic_sudeste_input.csv
- Casos com preenchimento incompleto: 17
- Media atual do IDIC parcial: 68.57
- Casos com organograma identificado no repositorio: 14
- Perfil discursivo mais frequente: indefinido

## Ranking parcial

| Documento | IDIC parcial | Completude (%) | Perfil discursivo |
| --- | ---: | ---: | --- |
| PDI_UFMG | 84.38 | 57.14 | indefinido |
| PDI_UFTM | 84.38 | 57.14 | indefinido |
| PDI_UFJF | 81.25 | 57.14 | indefinido |
| PDI_UFRRJ | 81.25 | 57.14 | artistica_patrimonial |
| PDI_UFSCAR | 81.25 | 57.14 | artistica_patrimonial |
| PDI_UFV | 78.12 | 57.14 | artistica_patrimonial |
| PDI_Unirio | 75.0 | 57.14 | inovacao_empreendedorismo |
| PDI_UFLA | 71.88 | 57.14 | indefinido |
| PDI_Unifesp | 68.75 | 57.14 | indefinido |
| PDI_UFF | 62.5 | 57.14 | indefinido |

## Leitura interpretativa

- O ranking parcial e fortemente influenciado pela camada discursiva dos PDIs e pela mera disponibilidade de organograma, porque a base manual institucional ainda nao foi preenchida.
- PDI_UFJF aparece com a maior presenca discursiva de cultura, o que sugere maior recorrencia e centralidade do tema no documento, mas isso ainda nao equivale automaticamente a maior institucionalizacao.
- PDI_UFRRJ se destaca na orientacao estrategica, indicando que a cultura aparece associada com mais frequencia a politica, planejamento, gestao ou diretrizes institucionais.
- Os casos na faixa inferior atual (PDI_Unifal, PIDE_UFU, PDI_UFOP) devem ser lidos com cautela: o posicionamento pode mudar quando forem adicionados dados sobre estrutura, quadro de produtores e instrumentos de fomento.

## Uso analitico

- O `IDIC parcial` e util para triagem comparativa inicial e para selecionar casos de aprofundamento qualitativo.
- O ranking deve ser confrontado com a tipologia analitica da pesquisa, e nao lido como medida definitiva de maturidade.
- O campo `perfil_discursivo` ajuda a observar se a cultura aparece mais como patrimonio e arte, formacao, gestao, diversidade ou inovacao.

## Como interpretar

- `IDIC parcial` usa apenas os componentes atualmente disponiveis para cada universidade.
- `Completude (%)` mostra quanto do modelo total foi efetivamente preenchido.
- Para consolidar o indice, complete `unidade_cultura_nivel`, `produtores_culturais`, `politica_cultural`, `edital_fomento` e `espacos_culturais` na base manual.
