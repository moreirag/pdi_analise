# MDMC-MOP (Python + pymoo)

Versao Python dos algoritmos do repositorio [MDMC-MOP](https://github.com/moreirag/MDMC-MOP), portados para a biblioteca `pymoo`.

## Algoritmos incluidos

- `ROINSGA2`: NSGA-II com penalizacao de regiao de interesse (ROI) no espaco de objetivos.
- `ROIDWUMOEA`: ROI + selecao por uniformidade ponderada por dominancia no espaco de decisao.

## Estrutura

- `/Users/gladstonmoreira/Documents/New project/mdmc_mop_py/algorithms.py`: implementacao dos algoritmos e operadores customizados.
- `/Users/gladstonmoreira/Documents/New project/scripts/run_experiment.py`: script CLI para executar experimentos.

## Instalacao

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Exemplo de execucao

Equivalente ao `run_test.m` (WFG9, M=2, D=5, 1e5 avaliacoes):

```bash
PYTHONPATH=. python scripts/run_experiment.py \
  --algorithm roidwu \
  --problem wfg9 \
  --pop-size 100 \
  --n-obj 2 \
  --n-var 5 \
  --n-evals 100000 \
  --seed 1
```

Executar a variante ROI-NSGA-II:

```bash
PYTHONPATH=. python scripts/run_experiment.py \
  --algorithm roinsga2 \
  --problem dtlz2 \
  --pop-size 100 \
  --n-obj 2 \
  --n-var 7 \
  --n-evals 100000 \
  --seed 1
```

## Saida

Os resultados sao salvos em `.npz` na pasta `results/` com:

- `X`: variaveis de decisao
- `F`: valores de objetivos

## Observacoes

- Os metodos mantem a logica central da implementacao MATLAB original.
- Pequenas diferencas numericas podem ocorrer devido a detalhes de operadores e ordenacao do `pymoo`.

## Plot das solucoes no espaco de objetivos

Depois de gerar resultados `.npz`, use:

```bash
PYTHONPATH=. python scripts/plot_objectives.py \
  results/roidwu_wfg9_M2_D5_seed1.npz \
  --title "ROIDWU - WFG9" \
  --output results/roidwu_wfg9_plot.png
```

Comparando duas execucoes/algoritmos no mesmo grafico:

```bash
PYTHONPATH=. python scripts/plot_objectives.py \
  results/roidwu_wfg9_M2_D5_seed1.npz \
  results/roinsga2_dtlz2_M2_D7_seed1.npz \
  --title "Comparacao"
```
