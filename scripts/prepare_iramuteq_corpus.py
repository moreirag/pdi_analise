#!/usr/bin/env python3
"""Prepare IRaMuTeQ corpus from PDI PDFs.

Outputs a single UTF-8 text file in IRaMuTeQ format:
**** *doc=UFABC
<text>
**** *doc=UFES
<text>
"""

from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "dados" / "pdi"
OUT_PATH = ROOT / "output" / "iramuteq_corpus.txt"


def _load_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception as exc:  # pragma: no cover - dependency is optional
        raise RuntimeError(
            "Missing dependency: pypdf. Install with: python -m pip install pypdf"
        ) from exc

    reader = PdfReader(str(path))
    parts: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        parts.append(text)
    return "\n".join(parts)


def _clean_text(text: str) -> str:
    text = text.replace("\u00a0", " ").replace("\u202f", " ")
    text = text.replace("\r", "\n")
    # Join hyphenated line breaks: "exem-\nplo" -> "exemplo"
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    # Normalize whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    # Remove stray separators that might break IRaMuTeQ parsing
    text = text.replace("****", "")
    return text.strip()


def _filter_lines(text: str) -> str:
    lines = [ln.strip() for ln in text.split("\n")]
    cleaned: list[str] = []

    # Heuristics to drop covers/credits and administrative lists
    drop_patterns = [
        r"^PLANO DE$",
        r"^DESENVOLVIMENTO$",
        r"^INSTITUCIONAL\b",
        r"^UNIVERSIDADE FEDERAL",
        r"^REITOR",
        r"^VICE[- ]REITOR",
        r"^PR[ÓO]-REITOR",
        r"^PR[ÓO]-REITORA",
        r"^DIRETOR",
        r"^DIRETORA",
        r"^COMISS[AÃ]O",
        r"^PORTARIA",
        r"^EIXO TEM[AÁ]TICO",
        r"^SUBCOMISS",
        r"^ILUSTRA",
        r"^CAMPUS",
        r"^PROF",
        r"^PROFESSOR",
        r"^PROFESSORA",
        r"^SUM[ÁA]RIO",
        r"^RESUMO EXECUTIVO",
    ]
    drop_re = re.compile("|".join(drop_patterns), re.IGNORECASE)

    for ln in lines:
        ln = ln.lstrip("\ufeff\u200e\u200f")
        if not ln:
            cleaned.append("")
            continue
        if drop_re.search(ln):
            continue
        if "portaria" in ln.lower():
            continue
        if "ilustra" in ln.lower():
            continue
        if re.match(r"^[IVXLCDM]+\s*-", ln):
            continue
        if re.search(r"\.{5,}", ln):
            continue
        # Drop TOC-style merged headings like "INTRODUÇÃO 15INTRODUÇÃO 15"
        if re.search(r"[A-Za-zÁÉÍÓÚÂÊÔÃÕÇ]{3,}\s*\d+\s*[A-Za-zÁÉÍÓÚÂÊÔÃÕÇ]{3,}\s*\d+", ln):
            continue
        if re.fullmatch(r"[A-ZÁÂÃÉÊÍÓÔÕÚÇ]{2,10}", ln):
            continue
        # Drop lines that are mostly numbers/symbols (years, bullets)
        if re.fullmatch(r"[\d\s\-–—•·\.\/\u2022\u00b7\uF0DF\uF09F]+", ln):
            continue
        if re.sub(r"[\d\s\-–—•·\.\/\u2022\u00b7\uF0DF\uF09F]+", "", ln) == "":
            continue
        # Drop lines that look like name lists (many capitalized words)
        words = re.findall(r"\b\w+\b", ln)
        cap_words = sum(1 for w in words if w[:1].isupper() and len(w) > 2)
        lower_words = sum(1 for w in words if w[:1].islower())
        if words and all(w[:1].isupper() for w in words) and len(words) >= 2:
            continue
        if cap_words >= 2 and lower_words <= 2 and len(words) <= 10:
            continue
        if cap_words >= 4 and len(words) >= 6:
            continue
        cleaned.append(ln)

    # Collapse multiple empty lines
    text = "\n".join(cleaned)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Normalize tokens for analysis (post-filter)
    text = text.lower()
    text = re.sub(r"\b\d+\b", " ", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def _doc_tag_from_filename(path: Path) -> str:
    name = path.stem
    # Standardize doc tag to ASCII-ish token for IRaMuTeQ variables
    tag = re.sub(r"\s+", "_", name)
    tag = re.sub(r"[^A-Za-z0-9_]+", "", tag)
    return tag or "DOC"


def build_corpus() -> list[str]:
    pdfs = sorted(PDF_DIR.glob("*.pdf"))
    if not pdfs:
        raise RuntimeError(f"No PDFs found in {PDF_DIR}")

    corpus_lines: list[str] = []
    for pdf in pdfs:
        raw_text = _load_pdf_text(pdf)
        text = _filter_lines(_clean_text(raw_text))
        if not text:
            continue
        tag = _doc_tag_from_filename(pdf)
        corpus_lines.append(f"**** *doc={tag}")
        corpus_lines.append(text)
    return corpus_lines


def main() -> int:
    corpus_lines = build_corpus()
    if not corpus_lines:
        print("No text extracted from PDFs.", file=sys.stderr)
        return 1

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("\n".join(corpus_lines) + "\n", encoding="utf-8")
    print(f"Wrote corpus to: {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
