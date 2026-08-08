#!/usr/bin/env python3
"""PDF Memory Vault — simple no-fuss version.
Converts memory/YYYY-MM-DD.md daily logs (plus MEMORY.md + LATEST.md) into
verbatim PDFs under memory/pdf-vault/. Incremental: skips files already done.
Unicode-safe (DejaVu fonts). Working files are NEVER touched."""

import os, re, sys, datetime
from pathlib import Path
from fpdf import FPDF
from fpdf.enums import XPos, YPos

DAY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")

WS = Path(os.path.expanduser("~/.openclaw/workspace"))
MEM = WS / "memory"
VAULT = MEM / "pdf-vault"
FONT_DIR = "/usr/share/fonts/TTF"
MONO = f"{FONT_DIR}/DejaVuSansMono.ttf"
MONO_B = f"{FONT_DIR}/DejaVuSansMono-Bold.ttf"
SANS = f"{FONT_DIR}/DejaVuSans.ttf"
SANS_B = f"{FONT_DIR}/DejaVuSans-Bold.ttf"

PAGE_W, PAGE_H = 210, 297  # A4 mm
MARGIN = 14
BODY = 8.2
CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def sanitize(text: str) -> str:
    return CTRL.sub("", text)


def make_pdf(src: Path, dest: Path, title: str, subtitle: str) -> int:
    raw = src.read_text(encoding="utf-8", errors="replace")
    raw = sanitize(raw)
    lines = raw.splitlines()

    pdf = FPDF(format="A4")
    pdf.set_margins(MARGIN, MARGIN, MARGIN)
    pdf.set_auto_page_break(True, margin=MARGIN)
    pdf.add_font("Mono", "", MONO)
    pdf.add_font("Mono", "B", MONO_B)
    pdf.add_font("Sans", "", SANS)
    pdf.add_font("Sans", "B", SANS_B)

    # Title page
    pdf.add_page()
    pdf.set_font("Sans", "B", 22)
    pdf.multi_cell(0, 11, title, align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)
    pdf.set_font("Sans", "", 11)
    pdf.set_text_color(110, 110, 110)
    pdf.multi_cell(0, 6, subtitle, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(6)
    pdf.set_font("Sans", "", 9)
    pdf.cell(0, 6, "Verbatim archive of the working memory log. Generated %s." % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    pdf.ln(6)
    pdf.cell(0, 6, "Source file untouched: %s" % src.name)

    # Body: verbatim lines
    pdf.add_page()
    pdf.set_font("Mono", "", BODY)
    for ln in lines:
        if ln.strip() == "":
            pdf.ln(2.4)
            continue
        # bold for headings (# ...)
        if ln.startswith("#"):
            pdf.set_font("Mono", "B", BODY + 0.8)
            pdf.set_text_color(20, 20, 120)
            pdf.multi_cell(0, 4.3, ln, align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Mono", "", BODY)
            pdf.set_text_color(0, 0, 0)
        else:
            pdf.multi_cell(0, 4.3, ln, align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.output(str(dest) + ".tmp")
    os.replace(str(dest) + ".tmp", str(dest))
    return pdf.page


def fmt_size(n: int) -> str:
    return f"{n/1024:.0f} KB" if n > 1024 else f"{n} B"


def main():
    VAULT.mkdir(parents=True, exist_ok=True)
    targets = sorted(f for f in MEM.glob("2026-*.md") if DAY_RE.match(f.name))
    extras = [(MEM / "LATEST.md", "LATEST.md - Rolling 30-exchange log")]
    all_pdfs = []
    made = skipped = 0
    total_pages = 0

    for f in targets:
        d = datetime.datetime.strptime(f.stem, "%Y-%m-%d")
        out_dir = VAULT / f"{d.year:04d}-{d.month:02d}"
        out_dir.mkdir(parents=True, exist_ok=True)
        dest = out_dir / f"{f.stem}.pdf"
        if dest.exists():
            skipped += 1
            all_pdfs.append(dest)
            continue
        title = f"Daily Log - {d.strftime('%A, %d %B %Y')}"
        subtitle = f"Source: memory/{f.name} | {fmt_size(f.stat().st_size)} of verbatim log"
        pages = make_pdf(f, dest, title, subtitle)
        all_pdfs.append(dest)
        made += 1
        total_pages += pages
        print(f"  + {dest.relative_to(WS)} ({pages}p)")

    for f, label in extras:
        if not f.exists():
            continue
        dest = VAULT / f"{f.stem}.pdf"
        if dest.exists():
            skipped += 1
            all_pdfs.append(dest)
            continue
        pages = make_pdf(f, dest, f.stem, f"{label} | {fmt_size(f.stat().st_size)}")
        all_pdfs.append(dest)
        made += 1
        total_pages += pages
        print(f"  + {dest.relative_to(WS)} ({pages}p)")

    # INDEX (grep-able guide seed)
    idx = VAULT / "INDEX.txt"
    lines = ["PDF MEMORY VAULT - INDEX", "Generated: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "",
             f"Daily logs archived: {len(targets)} | PDFs: {len(all_pdfs)} | New this run: {made} | Skipped: {skipped}", ""]
    for p in sorted(all_pdfs):
        rel = p.relative_to(VAULT)
        lines.append(f"{rel}  ({fmt_size(p.stat().st_size)})")
    idx.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nINDEX: {idx.relative_to(WS)}")
    print(f"Done: {made} new PDFs, {skipped} skipped, {total_pages} pages rendered this run.")


if __name__ == "__main__":
    main()
