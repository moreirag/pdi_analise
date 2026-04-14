#!/usr/bin/env python3
"""Build a preliminary IDIC for Southeast federal universities.

The script combines:
- discourse evidence from the PDI analysis outputs;
- organogram file availability;
- a manually enrichable institutional input table.

Outputs:
- data/idic_sudeste_input.csv
- output/sudeste/idic_sudeste.csv
- output/sudeste/idic_relatorio.md
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
import os
from pathlib import Path
import re
import sys

os.environ.setdefault("MPLBACKEND", "Agg")


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output" / "sudeste"
DATA_DIR = ROOT / "data"
ORGANOGRAM_DIR = ROOT / "dados" / "Organogramas Sudeste"
MPL_DIR = ROOT / ".matplotlib"

MPL_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_DIR))

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

SUMMARY_PATH = OUTPUT_DIR / "cultura_resumo.csv"
CONTEXTS_PATH = OUTPUT_DIR / "cultura_contextos.csv"
MANUAL_INPUT_PATH = DATA_DIR / "idic_sudeste_input.csv"
IDIC_OUTPUT_PATH = OUTPUT_DIR / "idic_sudeste.csv"
REPORT_PATH = OUTPUT_DIR / "idic_relatorio.md"
PDF_REPORT_PATH = OUTPUT_DIR / "idic_relatorio_visual.pdf"

LEVEL_SCORES = {
    "ausente": 0,
    "outro": 1,
    "setor": 1,
    "coordenadoria": 2,
    "coordenacao": 2,
    "gerencia": 2,
    "diretoria": 3,
    "secretaria": 3,
    "pro_reitoria": 4,
    "reitoria": 4,
}


@dataclass
class ManualRow:
    doc: str
    universidade: str
    sigla: str
    organograma_arquivo: str
    organograma_disponivel: str
    unidade_cultura_nivel: str
    unidade_cultura_nome: str
    vinculacao_superior: str
    produtores_culturais: str
    politica_cultural: str
    edital_fomento: str
    espacos_culturais: str
    observacoes: str


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _organogram_lookup() -> dict[str, str]:
    lookup: dict[str, str] = {}
    if not ORGANOGRAM_DIR.exists():
        return lookup
    for file_path in ORGANOGRAM_DIR.iterdir():
        if file_path.is_file():
            lookup[_normalize(file_path.stem)] = file_path.name
    return lookup


def _guess_organogram(doc: str, lookup: dict[str, str]) -> str:
    sigla = doc.replace("PDI_", "").replace("PIDE_", "")
    normalized_sigla = _normalize(sigla)
    for key, filename in lookup.items():
        if normalized_sigla in key:
            return filename
    return ""


def _build_manual_template(summary_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    organograms = _organogram_lookup()
    rows: list[dict[str, str]] = []
    for row in summary_rows:
        doc = row["doc"]
        sigla = doc.replace("PDI_", "").replace("PIDE_", "")
        organograma_arquivo = _guess_organogram(doc, organograms)
        rows.append(
            {
                "doc": doc,
                "universidade": sigla,
                "sigla": sigla,
                "organograma_arquivo": organograma_arquivo,
                "organograma_disponivel": "sim" if organograma_arquivo else "nao",
                "unidade_cultura_nivel": "",
                "unidade_cultura_nome": "",
                "vinculacao_superior": "",
                "produtores_culturais": "",
                "politica_cultural": "",
                "edital_fomento": "",
                "espacos_culturais": "",
                "observacoes": "",
            }
        )
    return rows


def _ensure_manual_input(summary_rows: list[dict[str, str]]) -> list[ManualRow]:
    fieldnames = [
        "doc",
        "universidade",
        "sigla",
        "organograma_arquivo",
        "organograma_disponivel",
        "unidade_cultura_nivel",
        "unidade_cultura_nome",
        "vinculacao_superior",
        "produtores_culturais",
        "politica_cultural",
        "edital_fomento",
        "espacos_culturais",
        "observacoes",
    ]

    if not MANUAL_INPUT_PATH.exists():
        template = _build_manual_template(summary_rows)
        _write_csv(MANUAL_INPUT_PATH, template, fieldnames)

    rows = _load_csv(MANUAL_INPUT_PATH)
    return [ManualRow(**row) for row in rows]


def _load_context_stats() -> dict[str, dict[str, object]]:
    rows = _load_csv(CONTEXTS_PATH)
    stats: dict[str, dict[str, object]] = {}
    for row in rows:
        doc = row["doc"]
        if doc not in stats:
            stats[doc] = {
                "contexts": 0,
                "categories": {},
                "strategic_hits": 0,
            }
        bucket = stats[doc]
        bucket["contexts"] = int(bucket["contexts"]) + 1
        categories = bucket["categories"]
        categories[row["categoria"]] = categories.get(row["categoria"], 0) + 1

        trecho = row["trecho"].lower()
        strategic_keywords = (
            "política", "politica", "gestão", "gestao", "governança", "governanca",
            "plano", "estratég", "estrateg", "orçamento", "orcamento", "diretriz",
            "meta", "indicador", "institucional",
        )
        if any(keyword in trecho for keyword in strategic_keywords):
            bucket["strategic_hits"] = int(bucket["strategic_hits"]) + 1
    return stats


def _quantile_score(values: list[float], value: float) -> int:
    ordered = sorted(values)
    if not ordered:
        return 0
    index = ordered.index(value)
    ratio = index / max(len(ordered) - 1, 1)
    if ratio >= 0.75:
        return 4
    if ratio >= 0.50:
        return 3
    if ratio >= 0.25:
        return 2
    if ratio > 0:
        return 1
    return 0


def _diversity_score(category_count: int) -> int:
    return min(max(category_count - 1, 0), 4)


def _strategic_score(strategy_share: float) -> int:
    if strategy_share >= 0.60:
        return 4
    if strategy_share >= 0.45:
        return 3
    if strategy_share >= 0.30:
        return 2
    if strategy_share >= 0.15:
        return 1
    return 0


def _level_score(level: str) -> int | None:
    value = level.strip().lower()
    if not value:
        return None
    return LEVEL_SCORES.get(value, LEVEL_SCORES["outro"])


def _numeric_score(raw: str, thresholds: tuple[int, int, int, int]) -> int | None:
    value = raw.strip()
    if not value:
        return None
    try:
        number = int(value)
    except ValueError:
        return None
    a, b, c, d = thresholds
    if number >= d:
        return 4
    if number >= c:
        return 3
    if number >= b:
        return 2
    if number >= a:
        return 1
    return 0


def _boolean_score(raw: str) -> int | None:
    value = raw.strip().lower()
    if not value:
        return None
    if value in {"sim", "s", "yes", "y", "1"}:
        return 1
    if value in {"nao", "não", "n", "no", "0"}:
        return 0
    return None


def _build_idic_rows(
    summary_rows: list[dict[str, str]],
    manual_rows: list[ManualRow],
    context_stats: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    manual_by_doc = {row.doc: row for row in manual_rows}
    density_values = [float(row["culture_per_1000"]) for row in summary_rows]
    count_values = [float(row["culture_count"]) for row in summary_rows]

    rows: list[dict[str, object]] = []
    for summary in summary_rows:
        doc = summary["doc"]
        manual = manual_by_doc.get(doc)
        stats = context_stats.get(doc, {"contexts": 0, "categories": {}, "strategic_hits": 0})
        categories = stats["categories"]
        non_indef = [name for name in categories if name != "indefinido" and categories[name] > 0]
        contexts = max(int(stats["contexts"]), 1)
        strategy_share = int(stats["strategic_hits"]) / contexts

        discourse_presence = round(
            (_quantile_score(density_values, float(summary["culture_per_1000"])) +
             _quantile_score(count_values, float(summary["culture_count"]))) / 2,
            2,
        )
        discourse_diversity = _diversity_score(len(non_indef))
        discourse_strategic = _strategic_score(strategy_share)

        organogram_presence = _boolean_score(manual.organograma_disponivel) if manual else None
        organogram_level = _level_score(manual.unidade_cultura_nivel) if manual else None
        staff_score = _numeric_score(manual.produtores_culturais, (1, 3, 6, 10)) if manual else None

        infra_items = 0
        infra_possible = 3
        infra_answers = 0
        for raw in (
            manual.politica_cultural if manual else "",
            manual.edital_fomento if manual else "",
            manual.espacos_culturais if manual else "",
        ):
            value = _boolean_score(raw)
            if value is not None:
                infra_answers += 1
                infra_items += value
        infra_score = (
            round((infra_items / infra_possible) * 4, 2)
            if manual and infra_answers > 0
            else None
        )

        scored_components: list[float] = [discourse_presence, discourse_diversity, discourse_strategic]
        component_labels = ["presenca_discursiva", "diversidade_discursiva", "orientacao_estrategica"]

        optional_components = [
            ("organograma_disponivel", organogram_presence * 4 if organogram_presence is not None else None),
            ("nivel_organizacional", organogram_level),
            ("quadro_produtores", staff_score),
            ("infraestrutura_normativa", infra_score),
        ]
        for label, value in optional_components:
            if value is not None:
                scored_components.append(float(value))
                component_labels.append(label)

        max_points = 4 * len(scored_components)
        total_points = sum(scored_components)
        idic = round((total_points / max_points) * 100, 2) if max_points else 0.0
        completeness = round((len(scored_components) / 7) * 100, 2)

        rows.append(
            {
                "doc": doc,
                "arquivo": summary["arquivo"],
                "culture_count": summary["culture_count"],
                "culture_per_1000": summary["culture_per_1000"],
                "presenca_discursiva": discourse_presence,
                "diversidade_discursiva": discourse_diversity,
                "orientacao_estrategica": discourse_strategic,
                "organograma_disponivel": organogram_presence * 4 if organogram_presence is not None else "",
                "nivel_organizacional": organogram_level if organogram_level is not None else "",
                "quadro_produtores": staff_score if staff_score is not None else "",
                "infraestrutura_normativa": infra_score if infra_score is not None else "",
                "componentes_utilizados": ", ".join(component_labels),
                "completude_percentual": completeness,
                "idic_parcial": idic,
                "perfil_discursivo": summary["top_category"],
                "termos_dominantes": summary["top_terms"],
                "unidade_cultura_nivel": manual.unidade_cultura_nivel if manual else "",
                "unidade_cultura_nome": manual.unidade_cultura_nome if manual else "",
                "vinculacao_superior": manual.vinculacao_superior if manual else "",
                "produtores_culturais": manual.produtores_culturais if manual else "",
                "politica_cultural": manual.politica_cultural if manual else "",
                "edital_fomento": manual.edital_fomento if manual else "",
                "espacos_culturais": manual.espacos_culturais if manual else "",
                "observacoes": manual.observacoes if manual else "",
            }
        )

    rows.sort(key=lambda row: float(row["idic_parcial"]), reverse=True)
    return rows


def _write_report(rows: list[dict[str, object]]) -> None:
    top_rows = rows[:10]
    incomplete = [row for row in rows if float(row["completude_percentual"]) < 100]
    average_idic = round(sum(float(row["idic_parcial"]) for row in rows) / max(len(rows), 1), 2)
    with_organogram = sum(1 for row in rows if str(row["organograma_disponivel"]) == "4")
    profile_counts: dict[str, int] = {}
    for row in rows:
        profile = str(row["perfil_discursivo"])
        profile_counts[profile] = profile_counts.get(profile, 0) + 1
    dominant_profile = max(profile_counts.items(), key=lambda item: item[1])[0] if profile_counts else "indefinido"

    top_discursive = max(rows, key=lambda row: float(row["presenca_discursiva"]))
    top_strategic = max(rows, key=lambda row: float(row["orientacao_estrategica"]))
    low_end = rows[-3:]

    lines = [
        "# IDIC preliminar do Sudeste",
        "",
        "Este relatorio combina indicadores discursivos extraidos dos PDIs com um quadro institucional preenchivel para organograma, estrutura e capacidade instalada da cultura.",
        "",
        f"- Universidades avaliadas: {len(rows)}",
        f"- Base manual: {MANUAL_INPUT_PATH}",
        f"- Casos com preenchimento incompleto: {len(incomplete)}",
        f"- Media atual do IDIC parcial: {average_idic}",
        f"- Casos com organograma identificado no repositorio: {with_organogram}",
        f"- Perfil discursivo mais frequente: {dominant_profile}",
        "",
        "## Ranking parcial",
        "",
        "| Documento | IDIC parcial | Completude (%) | Perfil discursivo |",
        "| --- | ---: | ---: | --- |",
    ]

    for row in top_rows:
        lines.append(
            f"| {row['doc']} | {row['idic_parcial']} | {row['completude_percentual']} | {row['perfil_discursivo']} |"
        )

    lines.extend(
        [
            "",
            "## Leitura interpretativa",
            "",
            f"- O ranking parcial e fortemente influenciado pela camada discursiva dos PDIs e pela mera disponibilidade de organograma, porque a base manual institucional ainda nao foi preenchida.",
            f"- {top_discursive['doc']} aparece com a maior presenca discursiva de cultura, o que sugere maior recorrencia e centralidade do tema no documento, mas isso ainda nao equivale automaticamente a maior institucionalizacao.",
            f"- {top_strategic['doc']} se destaca na orientacao estrategica, indicando que a cultura aparece associada com mais frequencia a politica, planejamento, gestao ou diretrizes institucionais.",
            f"- Os casos na faixa inferior atual ({', '.join(str(row['doc']) for row in low_end)}) devem ser lidos com cautela: o posicionamento pode mudar quando forem adicionados dados sobre estrutura, quadro de produtores e instrumentos de fomento.",
            "",
            "## Uso analitico",
            "",
            "- O `IDIC parcial` e util para triagem comparativa inicial e para selecionar casos de aprofundamento qualitativo.",
            "- O ranking deve ser confrontado com a tipologia analitica da pesquisa, e nao lido como medida definitiva de maturidade.",
            "- O campo `perfil_discursivo` ajuda a observar se a cultura aparece mais como patrimonio e arte, formacao, gestao, diversidade ou inovacao.",
            "",
            "## Como interpretar",
            "",
            "- `IDIC parcial` usa apenas os componentes atualmente disponiveis para cada universidade.",
            "- `Completude (%)` mostra quanto do modelo total foi efetivamente preenchido.",
            "- Para consolidar o indice, complete `unidade_cultura_nivel`, `produtores_culturais`, `politica_cultural`, `edital_fomento` e `espacos_culturais` na base manual.",
        ]
    )

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _render_wrapped_text(fig: plt.Figure, text: str, x: float = 0.08, y: float = 0.94) -> None:
    fig.text(x, y, text, va="top", ha="left", fontsize=12, wrap=True)


def _write_visual_report(rows: list[dict[str, object]]) -> None:
    labels = [str(row["doc"]).replace("PDI_", "").replace("PIDE_", "") for row in rows]
    idic_values = [float(row["idic_parcial"]) for row in rows]
    densities = [float(row["culture_per_1000"]) for row in rows]
    strategic = [float(row["orientacao_estrategica"]) for row in rows]
    diversity = [float(row["diversidade_discursiva"]) for row in rows]

    with PdfPages(PDF_REPORT_PATH) as pdf:
        fig = plt.figure(figsize=(11.69, 8.27))
        fig.suptitle("IDIC preliminar do Sudeste", fontsize=18, fontweight="bold", y=0.97)
        summary = (
            "Leitura geral:\n"
            f"- {len(rows)} universidades federais analisadas.\n"
            f"- O indice ainda e parcial e usa principalmente a dimensao discursiva dos PDIs.\n"
            f"- A base manual para estrutura institucional esta em {MANUAL_INPUT_PATH.name}."
        )
        _render_wrapped_text(fig, summary)
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(11.69, 8.27))
        top_n = min(12, len(rows))
        plot_labels = labels[:top_n][::-1]
        plot_values = idic_values[:top_n][::-1]
        colors = ["#2f5d50" if value >= 75 else "#7aa37a" if value >= 60 else "#c3a35b" for value in plot_values]
        ax.barh(plot_labels, plot_values, color=colors)
        ax.set_title("Ranking parcial do IDIC")
        ax.set_xlabel("IDIC parcial")
        ax.set_xlim(0, 100)
        for idx, value in enumerate(plot_values):
            ax.text(value + 1, idx, f"{value:.1f}", va="center", fontsize=9)
        ax.grid(axis="x", alpha=0.2)
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(11.69, 8.27))
        scatter = ax.scatter(densities, idic_values, c=strategic, cmap="viridis", s=90, alpha=0.9)
        for label, x, y in zip(labels, densities, idic_values):
            ax.annotate(label, (x, y), textcoords="offset points", xytext=(5, 4), fontsize=8)
        ax.set_title("Densidade discursiva x IDIC parcial")
        ax.set_xlabel("Ocorrencias de cultura por 1000 tokens")
        ax.set_ylabel("IDIC parcial")
        cbar = fig.colorbar(scatter, ax=ax)
        cbar.set_label("Orientacao estrategica")
        ax.grid(alpha=0.2)
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        fig, axes = plt.subplots(1, 2, figsize=(11.69, 8.27))
        top_n = min(8, len(rows))
        subset = rows[:top_n]
        subset_labels = [str(row["doc"]).replace("PDI_", "").replace("PIDE_", "") for row in subset]
        disc_presence = [float(row["presenca_discursiva"]) for row in subset]
        disc_diversity = [float(row["diversidade_discursiva"]) for row in subset]
        disc_strategy = [float(row["orientacao_estrategica"]) for row in subset]

        axes[0].bar(subset_labels, disc_presence, color="#406882", label="Presenca")
        axes[0].bar(subset_labels, disc_diversity, bottom=disc_presence, color="#6998ab", label="Diversidade")
        bottom = [a + b for a, b in zip(disc_presence, disc_diversity)]
        axes[0].bar(subset_labels, disc_strategy, bottom=bottom, color="#b1d0e0", label="Estrategica")
        axes[0].set_title("Componentes discursivos")
        axes[0].set_ylim(0, 12)
        axes[0].tick_params(axis="x", rotation=45)
        axes[0].legend(fontsize=8)

        organograma = [float(row["organograma_disponivel"]) if str(row["organograma_disponivel"]) else 0.0 for row in subset]
        completude = [float(row["completude_percentual"]) for row in subset]
        axes[1].bar(subset_labels, completude, color="#d9bf77", label="Completude (%)")
        axes[1].plot(subset_labels, [value * 25 for value in organograma], color="#8d4b32", marker="o", label="Organograma (escala)")
        axes[1].set_title("Completude e presenca de organograma")
        axes[1].set_ylim(0, 100)
        axes[1].tick_params(axis="x", rotation=45)
        axes[1].legend(fontsize=8)

        fig.suptitle("Detalhamento dos resultados parciais")
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)


def main() -> int:
    if not SUMMARY_PATH.exists() or not CONTEXTS_PATH.exists():
        print(
            "Missing discourse inputs. Run scripts/analyze_sudeste_pdis.py first.",
            file=sys.stderr,
        )
        return 1

    summary_rows = _load_csv(SUMMARY_PATH)
    manual_rows = _ensure_manual_input(summary_rows)
    context_stats = _load_context_stats()
    idic_rows = _build_idic_rows(summary_rows, manual_rows, context_stats)

    fieldnames = list(idic_rows[0].keys()) if idic_rows else []
    _write_csv(IDIC_OUTPUT_PATH, idic_rows, fieldnames)
    _write_report(idic_rows)
    _write_visual_report(idic_rows)

    print(f"Wrote manual input to: {MANUAL_INPUT_PATH}")
    print(f"Wrote IDIC output to: {IDIC_OUTPUT_PATH}")
    print(f"Wrote report to: {REPORT_PATH}")
    print(f"Wrote visual PDF to: {PDF_REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
