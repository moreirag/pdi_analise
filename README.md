# pdi_analise

## IRaMuTeQ

Este projeto prepara o corpus para o IRaMuTeQ e orienta a gerar visualizações de
frequência e conectividade (análise de similitude).

## Analise dos PDIs do Sudeste

Ferramenta inicial para a etapa exploratoria da pesquisa sobre cultura nos PDIs
das universidades federais do Sudeste.

Saidas geradas em `output/sudeste/`:

- `iramuteq_corpus_sudeste.txt`: corpus consolidado para abrir no IRaMuTeQ.
- `cultura_resumo.csv`: resumo por universidade, com densidade de contextos de cultura.
- `cultura_contextos.csv`: trechos em que aparecem termos da familia `cultur*`.
- `analise_sudeste.md`: relatorio sintese para leitura rapida.

Execucao:

```
python3 scripts/analyze_sudeste_pdis.py
```

## IDIC do Sudeste

Ferramenta para construir uma versao preliminar do Indice de Densidade
Institucional da Cultura (IDIC), combinando:

- indicadores discursivos extraidos dos PDIs;
- disponibilidade de organograma no repositorio;
- uma base manual preenchivel com nivel organizacional da cultura, quadro de
  produtores culturais e evidencias institucionais.

Execucao:

```
python3 scripts/build_idic_sudeste.py
```

Arquivos gerados:

- `data/idic_sudeste_input.csv`: base manual para complementar o indice.
- `output/sudeste/idic_sudeste.csv`: ranking parcial do IDIC.
- `output/sudeste/idic_relatorio.md`: relatorio sintese.

### 1) Gerar o corpus

Dependência para extração de texto:

```
python -m pip install pypdf
```

Gerar o arquivo `output/iramuteq_corpus.txt`:

```
python scripts/prepare_iramuteq_corpus.py
```

### 2) Abrir no IRaMuTeQ

1. Abra o IRaMuTeQ.
2. `Corpora` -> `Nouveau corpus` e selecione `output/iramuteq_corpus.txt`.
3. Use:
   - `Statistiques` -> `Fréquences` ou `Nuage de mots` para frequência.
   - `Analyses` -> `Analyse de similitude` para conectividade.

O corpus inclui a variável `*doc=<nome_do_arquivo>` para facilitar filtros por instituição.
