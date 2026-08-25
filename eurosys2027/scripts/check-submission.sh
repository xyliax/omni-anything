#!/usr/bin/env bash
set -euo pipefail

pdf_path="${1:-build/main.pdf}"
workspace_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! -f "$pdf_path" ]]; then
  echo "missing PDF: $pdf_path" >&2
  exit 1
fi

if ! rg -q '^\\documentclass\[sigplan,10pt,anonymous,review\]\{acmart\}' "$workspace_dir/main.tex"; then
  echo "main.tex does not use the pinned EuroSys review class options" >&2
  exit 1
fi

if ! rg -q 'printfolios=true' "$workspace_dir/main.tex"; then
  echo "page numbering is not explicitly enabled" >&2
  exit 1
fi

if rg -n '\\(?:geometry|fontsize|linespread|textwidth|textheight|columnsep|baselinestretch)\b' \
  "$workspace_dir/main.tex" "$workspace_dir/macros.tex" "$workspace_dir/sections"; then
  echo "potentially non-compliant format override detected" >&2
  exit 1
fi

page_size="$(pdfinfo "$pdf_path" | awk -F: '/^Page size/ {gsub(/^[[:space:]]+/, "", $2); print $2}')"
if [[ "$page_size" != *"letter"* && "$page_size" != *"A4"* ]]; then
  echo "unexpected page size: $page_size" >&2
  exit 1
fi

if pdffonts "$pdf_path" | tail -n +3 | awk '{print $6}' | rg -q '^no$'; then
  echo "at least one PDF font is not embedded" >&2
  exit 1
fi

if pdfinfo "$pdf_path" | rg -i 'Author:.*[^[:space:]]' | rg -v -i 'Anonymous'; then
  echo "potential author metadata leak in PDF" >&2
  exit 1
fi

echo "basic EuroSys 2027 scaffold checks passed: $pdf_path"
echo "manual checks still required: technical-page boundary, 10pt figure text, grayscale readability, anonymity, and current CFP"
