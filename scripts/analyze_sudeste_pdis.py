#!/usr/bin/env python3
"""Build analysis artifacts for Southeast federal university PDIs.

Outputs:
- output/sudeste/iramuteq_corpus_sudeste.txt
- output/sudeste/cultura_resumo.csv
- output/sudeste/cultura_contextos.csv
- output/sudeste/analise_sudeste.md
"""

from __future__ import annotations

from collections import Counter
import csv
from pathlib import Path
import re
import sys

from prepare_iramuteq_corpus import (
    _clean_text,
    _doc_tag_from_filename,
    _filter_lines,
    _load_pdf_text,
)


ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "dados" / "pdi"
OUT_DIR = ROOT / "output" / "sudeste"
CORPUS_PATH = OUT_DIR / "iramuteq_corpus_sudeste.txt"
SUMMARY_PATH = OUT_DIR / "cultura_resumo.csv"
CONTEXTS_PATH = OUT_DIR / "cultura_contextos.csv"
REPORT_PATH = OUT_DIR / "analise_sudeste.md"

CULTURA_PATTERN = re.compile(r"\bcultur\w*\b", re.IGNORECASE)
TOKEN_PATTERN = re.compile(r"[a-záâãéêíóôõúç]+", re.IGNORECASE)

STOPWORDS = {
    "a", "ao", "aos", "as", "com", "como", "da", "das", "de", "do", "dos", "e",
    "em", "entre", "esta", "este", "foi", "na", "nas", "no", "nos", "o", "os",
    "ou", "para", "pela", "pelas", "pelo", "pelos", "por", "que", "se", "sem",
    "ser", "sua", "suas", "seu", "seus", "um", "uma", "universidade",
    "universidades", "federal", "federais", "pdi", "pd i", "institucional",
}

CATEGORY_RULES = {
    "artistica_patrimonial": {
        "arte", "artes", "artístico", "artística", "artísticas", "artísticos",
        "patrimônio", "patrimonio", "memória", "memoria", "museu", "museus",
        "acervo", "acervos", "extensão", "extensao",
    },
    "organizacional_gestao": {
        "organizacional", "gestão", "gestao", "clima", "governança", "governanca",
        "gestor", "gestores", "institucional", "planejamento",
    },
    "academica_formativa": {
        "formação", "formacao", "ensino", "pesquisa", "currículo", "curriculo",
        "formativo", "formativa", "discente", "docente",
    },
    "inovacao_empreendedorismo": {
        "inovação", "inovacao", "empreendedorismo", "inovador", "inovadora",
        "tecnologia", "tecnológico", "tecnologica",
    },
    "diversidade_inclusao": {
        "diversidade", "inclusão", "inclusao", "equidade", "acessibilidade",
        "direitos", "humanos", "identidade", "território", "territorio",
    },
}


def _iter_pdfs() -> list[Path]:
    pdfs = sorted(PDF_DIR.glob("*.pdf"))
    if not pdfs:
        raise RuntimeError(f"No PDFs found in {PDF_DIR}")
    return pdfs


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


def _split_contexts(text: str) -> list[str]:
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    parts = re.split(r"(?<=[\.\!\?;:])\s+", text)
    return [part.strip() for part in parts if part.strip()]


def _extract_neighbor_terms(context: str) -> list[str]:
    tokens = _tokenize(context)
    return [
        token for token in tokens
        if token not in STOPWORDS and not CULTURA_PATTERN.fullmatch(token)
    ]


def _classify_context(context: str) -> str:
    tokens = set(_tokenize(context))
    scores: list[tuple[int, str]] = []
    for label, keywords in CATEGORY_RULES.items():
        score = len(tokens & keywords)
        scores.append((score, label))

    best_score, best_label = max(scores)
    return best_label if best_score > 0 else "indefinido"


def _build_document_record(pdf: Path) -> dict[str, object]:
    raw_text = _load_pdf_text(pdf)
    clean_text = _filter_lines(_clean_text(raw_text))
    tag = _doc_tag_from_filename(pdf)
    contexts = _split_contexts(clean_text)

    culture_contexts = [
        context for context in contexts if CULTURA_PATTERN.search(context)
    ]
    culture_terms = Counter()
    classified_contexts = Counter()
    context_rows: list[dict[str, object]] = []

    for index, context in enumerate(culture_contexts, start=1):
        neighbor_terms = _extract_neighbor_terms(context)
        culture_terms.update(neighbor_terms)
        category = _classify_context(context)
        classified_contexts.update([category])
        context_rows.append(
            {
                "doc": tag,
                "arquivo": pdf.name,
                "contexto_id": index,
                "categoria": category,
                "trecho": context,
                "termos_vizinhos": ", ".join(term for term, _ in Counter(neighbor_terms).most_common(8)),
            }
        )

    tokens = _tokenize(clean_text)
    return {
        "doc": tag,
        "arquivo": pdf.name,
        "texto": clean_text,
        "token_count": len(tokens),
        "culture_count": len(culture_contexts),
        "culture_per_1000": round((len(culture_contexts) / max(len(tokens), 1)) * 1000, 2),
        "top_terms": ", ".join(term for term, _ in culture_terms.most_common(15)),
        "top_category": classified_contexts.most_common(1)[0][0] if classified_contexts else "indefinido",
        "context_rows": context_rows,
    }


def _write_corpus(records: list[dict[str, object]]) -> None:
    lines: list[str] = []
    for record in records:
        lines.append(f"**** *doc={record['doc']}")
        lines.append(str(record["texto"]))
    CORPUS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_summary(records: list[dict[str, object]]) -> None:
    with SUMMARY_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "doc",
                "arquivo",
                "token_count",
                "culture_count",
                "culture_per_1000",
                "top_category",
                "top_terms",
            ],
        )
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "doc": record["doc"],
                    "arquivo": record["arquivo"],
                    "token_count": record["token_count"],
                    "culture_count": record["culture_count"],
                    "culture_per_1000": record["culture_per_1000"],
                    "top_category": record["top_category"],
                    "top_terms": record["top_terms"],
                }
            )


def _write_contexts(records: list[dict[str, object]]) -> None:
    with CONTEXTS_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "doc",
                "arquivo",
                "contexto_id",
                "categoria",
                "trecho",
                "termos_vizinhos",
            ],
        )
        writer.writeheader()
        for record in records:
            for row in record["context_rows"]:
                writer.writerow(row)


def _write_report(records: list[dict[str, object]]) -> None:
    total_contexts = sum(int(record["culture_count"]) for record in records)
    ranked = sorted(records, key=lambda item: int(item["culture_count"]), reverse=True)

    lines = [
        "# Analise inicial dos PDIs do Sudeste",
        "",
        f"- Universidades analisadas: {len(records)}",
        f"- Contextos com ocorrencias de termos da familia 'cultur*': {total_contexts}",
        "",
        "## Resumo por documento",
        "",
        "| Documento | Contextos com cultura | Ocorrencias por 1000 tokens | Categoria predominante |",
        "| --- | ---: | ---: | --- |",
    ]

    for record in ranked:
        lines.append(
            f"| {record['doc']} | {record['culture_count']} | {record['culture_per_1000']} | {record['top_category']} |"
        )

    lines.extend(
        [
            "",
            "## Observacoes",
            "",
            "- Cada PDI foi tratado como unidade documental para o corpus do IRaMuTeQ.",
            "- Os contextos foram segmentados por frases para localizar os usos de 'cultura' e variantes.",
            "- A categoria do contexto e heuristica e serve como apoio exploratorio, nao como classificacao final da pesquisa.",
        ]
    )

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    try:
        records = [_build_document_record(pdf) for pdf in _iter_pdfs()]
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    _write_corpus(records)
    _write_summary(records)
    _write_contexts(records)
    _write_report(records)

    print(f"Wrote corpus to: {CORPUS_PATH}")
    print(f"Wrote summary to: {SUMMARY_PATH}")
    print(f"Wrote contexts to: {CONTEXTS_PATH}")
    print(f"Wrote report to: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
