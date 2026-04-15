#!/usr/bin/env python3
"""Autofill conservative IDIC institutional fields from PDI and organogram texts."""

from __future__ import annotations

import csv
from pathlib import Path
import re
import sys

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "idic_sudeste_input.csv"
PDF_DIR = ROOT / "dados" / "pdi"
ORGANOGRAM_DIR = ROOT / "dados" / "Organogramas Sudeste"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _extract_pdf_text(path: Path) -> str:
    if not path.exists() or path.suffix.lower() != ".pdf":
        return ""
    try:
        reader = PdfReader(str(path))
    except Exception:
        return ""
    parts: list[str] = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return re.sub(r"\s+", " ", " ".join(parts)).strip()


def _append_note(row: dict[str, str], message: str) -> None:
    current = row.get("observacoes", "").strip()
    if message in current:
        return
    row["observacoes"] = f"{current} | {message}".strip(" |")


def _fill_if_blank(row: dict[str, str], field: str, value: str, note: str) -> None:
    if not value or row.get(field, "").strip():
        return
    row[field] = value
    _append_note(row, note)


def _search_original(text: str, pattern: str) -> str:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group(1).strip() if match else ""


def _infer_unit_name(texts: list[tuple[str, str]]) -> tuple[str, str, str]:
    patterns = [
        (r"(Pr[oó][ -]?Reitoria de [A-Za-zÀ-ÿ() /-]{0,60}?Cultura)", "pro_reitoria"),
        (r"(Pr[oó][ -]?Reitoria de [A-Za-zÀ-ÿ() /-]{0,60}?Extens[aã]o e Cultura)", "pro_reitoria"),
        (r"(Diretoria de [A-Za-zÀ-ÿ() /-]{0,60}?Cultura)", "diretoria"),
        (r"(Coordenadori[aá] de [A-Za-zÀ-ÿ() /-]{0,60}?Cultura)", "coordenadoria"),
        (r"(Coordena[cç][aã]o de [A-Za-zÀ-ÿ() /-]{0,60}?Cultura)", "coordenacao"),
        (r"(Secretaria de [A-Za-zÀ-ÿ() /-]{0,60}?Cultura)", "secretaria"),
    ]
    for source, text in texts:
        for pattern, level in patterns:
            value = _search_original(text, pattern)
            if value:
                return value, level, source
    return "", "", ""


def _apply_overrides(row: dict[str, str]) -> None:
    overrides = {
        "PDI_UFABC": {
            "unidade_cultura_nivel": "",
            "unidade_cultura_nome": "",
            "vinculacao_superior": "",
        },
        "PDI_UFES": {
            "unidade_cultura_nivel": "",
            "unidade_cultura_nome": "",
            "vinculacao_superior": "",
        },
        "PDI_UFJF": {
            "unidade_cultura_nivel": "pro_reitoria",
            "unidade_cultura_nome": "Pró-Reitoria de Cultura",
            "vinculacao_superior": "Reitoria",
        },
        "PDI_UFMG": {
            "unidade_cultura_nivel": "pro_reitoria",
            "unidade_cultura_nome": "Pró-Reitoria de Cultura",
            "vinculacao_superior": "Reitoria",
        },
        "PDI_UFOP": {
            "unidade_cultura_nivel": "",
            "unidade_cultura_nome": "",
            "vinculacao_superior": "",
        },
        "PDI_UFRRJ": {
            "unidade_cultura_nivel": "setor",
            "unidade_cultura_nome": "Centro de Arte e Cultura",
            "vinculacao_superior": "Pro-Reitoria de Extensao",
        },
        "PIDE_UFU": {
            "unidade_cultura_nivel": "pro_reitoria",
            "unidade_cultura_nome": "Pró-Reitoria de Extensão e Cultura",
            "vinculacao_superior": "Reitoria",
        },
    }
    data = overrides.get(row["doc"])
    if not data:
        return
    for key, value in data.items():
        row[key] = value
    _append_note(row, "ajuste conservador aplicado na inferencia automatica")


def _contains_any(texts: list[str], patterns: list[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for text in texts for pattern in patterns)


def _infer_vinculacao(unit_name: str) -> str:
    lowered = unit_name.lower()
    if not unit_name:
        return ""
    if "pró" in lowered or "pro" in lowered:
        return "Reitoria"
    if "diretoria" in lowered or "coorden" in lowered or "secretaria" in lowered:
        if "extensão" in lowered or "extensao" in lowered:
            return "Pro-Reitoria de Extensao"
    return ""


def _resolve_pdi_path(row: dict[str, str]) -> Path:
    doc = row["doc"]
    if doc.startswith("PDI_"):
        filename = f"PDI {doc.removeprefix('PDI_')}.pdf"
    elif doc.startswith("PIDE_"):
        filename = f"PIDE {doc.removeprefix('PIDE_')}.pdf"
    else:
        filename = f"{doc}.pdf"
    return PDF_DIR / filename


def _resolve_organogram_path(row: dict[str, str]) -> Path:
    return ORGANOGRAM_DIR / row["organograma_arquivo"]


def _autofill_row(row: dict[str, str]) -> dict[str, str]:
    pdi_text = _extract_pdf_text(_resolve_pdi_path(row))
    organogram_text = _extract_pdf_text(_resolve_organogram_path(row))
    texts = [("pdi", pdi_text), ("organograma", organogram_text)]
    non_empty_texts = [text for _, text in texts if text]

    unit_name, level, source = _infer_unit_name(texts)
    _fill_if_blank(row, "unidade_cultura_nome", unit_name, f"unidade inferida a partir do {source}")
    _fill_if_blank(row, "unidade_cultura_nivel", level, f"nivel inferido a partir do {source}")

    if not row.get("vinculacao_superior", "").strip():
        vinculacao = _infer_vinculacao(row.get("unidade_cultura_nome", ""))
        _fill_if_blank(row, "vinculacao_superior", vinculacao, "vinculacao inferida a partir do nome da unidade")

    if _contains_any(non_empty_texts, [r"pol[ií]tica de cultura", r"pol[ií]tica cultural"]):
        _fill_if_blank(row, "politica_cultural", "sim", "politica cultural identificada no texto")

    if _contains_any(non_empty_texts, [r"editais?[^\.]{0,80}cultura", r"pibiart", r"fomento[^\.]{0,80}cultura"]):
        _fill_if_blank(row, "edital_fomento", "sim", "indicio de edital ou fomento cultural identificado")

    if _contains_any(non_empty_texts, [r"espa[çc]os? culturais?", r"equipamentos?[^\.]{0,60}cultur", r"museu", r"teatro", r"galeria", r"arquivo central", r"biblioteca central"]):
        _fill_if_blank(row, "espacos_culturais", "sim", "indicio de espacos ou equipamentos culturais identificado")

    if _contains_any(non_empty_texts, [r"produtores? culturais?"]):
        _append_note(row, "ha mencao a produtores culturais no corpus; revisar quantitativo manualmente")

    _apply_overrides(row)
    return row


def main() -> int:
    if not DATA_PATH.exists():
        print("Missing data/idic_sudeste_input.csv. Run build_idic_sudeste.py first.", file=sys.stderr)
        return 1

    rows = _read_csv(DATA_PATH)
    fieldnames = list(rows[0].keys()) if rows else []
    updated = [_autofill_row(dict(row)) for row in rows]
    _write_csv(DATA_PATH, updated, fieldnames)
    print(f"Updated manual input: {DATA_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
