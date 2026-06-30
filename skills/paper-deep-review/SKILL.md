---
name: paper-deep-review
description: Rigorous academic paper and technical-report review workflow. Use when Codex is asked to deeply read, analyze, summarize, or structure a paper, arXiv article, PDF, LaTeX source, technical whitepaper, or model/system report; produce Markdown with figures, formulas, evidence chains, related-work comparison, infrastructure analysis, and optional source-code cross-checks.
---

# Paper Deep Review

## Overview

Use this skill to turn a paper or technical report into a rigorous Markdown review grounded in the source document, figures/tables, related work, system implications, and implementation code when available.

## Workflow

1. **Create or reuse a paper folder.** Use `<paper-id>_<short-title>` when no folder exists; reuse the user-provided folder for offline papers. Keep materials under that folder:
   - `paper.pdf` or original PDF name
   - `source/` for LaTeX/source archives when available
   - `extracted_text/`
   - `figures/page_png/`
   - `figures/crops/`
   - `code/<repo-name>/`
   - `analysis.md`

2. **Acquire source material.**
   - If the user gives a local/offline PDF, use it as the primary source and do not assume arXiv/source exists.
   - If the user gives an arXiv ID or paper URL, fetch the PDF and source archive when network access is allowed; use original LaTeX figures when available.
   - If a code repo is provided, clone it into `code/`, record remote URL and commit hash, and inspect code rather than relying only on README claims.

3. **Extract text and figures.**
   - Prefer original LaTeX/vector assets if source exists.
   - If source does not exist, render PDF pages to PNG and crop figures/tables manually. Clearly state that screenshots are PDF crops, not original assets.
   - Use `scripts/extract_pdf_assets.py` for offline PDFs when PyMuPDF is available, or use Poppler tools (`pdftoppm`, `pdftocairo`) when installed.
   - Use `scripts/crop_pdf_figures.py` to batch crop figures from rendered page PNGs using a JSON crop spec, then generate a contact sheet for visual review.
   - Screenshot/crop requirements are strict:
     - Every Markdown-embedded screenshot of a Figure/Table must include its full caption. A crop without the visible `Figure`, `Fig.`, or `Table` label and caption text is incomplete and must be recropped.
     - Keep crop margins narrow: include only the figure/table body, its title/legend/axis labels, and the complete caption. Leave a small readable border, but avoid surrounding paragraphs, headers/footers, page numbers, neighboring figures, or excess whitespace.
     - Do not crop the caption separately from the visual unless the paper layout makes one combined crop unreadable. If split crops are unavoidable, embed the visual and caption together in adjacent Markdown and label both paths in the figure inventory.
     - Preserve enough resolution for axis labels, legends, table entries, and caption text to be readable at normal Markdown viewing width. Re-render pages at higher DPI before accepting blurry crops.
     - Name crops by source and semantic target, for example `fig3_method_caption.png` or `table2_main_results_caption.png`, so the file name signals that the caption is included.
   - For every figure embedded in Markdown, verify it includes the intended plot/table and full caption/title, has narrow clean boundaries, and excludes unrelated surrounding text.

4. **Read with evidence discipline.**
   - Map every important claim to a paper section, figure, table, appendix, or code path.
   - Explain the logic chain: problem -> assumption -> method -> measurement -> conclusion.
   - Use LaTeX math for formulas. Do not leave formulas as plain-text approximations when exact notation matters.
   - Mark assumptions and inferred calculations explicitly.

5. **Compare related work.**
   - Extract the paper's own related-work groups.
   - Compare against the current paper by mechanism, benefit, limitation, and fairness of the comparison.
   - Avoid broad literature essays; focus on why the paper's design differs and what trade-off it makes.

6. **Analyze infrastructure requirements.**
   - Include compute, memory, bandwidth, interconnect, scheduler/runtime, and custom-operator implications when relevant.
   - Provide formulas for derived estimates, such as parameter count, activation/cache size, communication volume, expected throughput, or latency.
   - Separate paper-reported numbers from your own calculations.

7. **Cross-check code when available.**
   - Inspect configs, model architecture, loss, data pipeline, evaluation, and serving/inference paths.
   - Link local file paths and, when possible, stable GitHub URLs pinned to a commit.
   - State what is implemented, what is only described in the paper, and what remains ambiguous.

8. **Write `analysis.md`.**
   - Use the reusable template in `references/markdown-template.md`.
   - Include a source/figure inventory near the top.
   - Include images inline near the discussion they support.
   - End with practical limitations, research inspirations, and unresolved reading questions.

## Quality Checks

Before finishing:

- Confirm all Markdown image links resolve.
- Review all crops in a contact sheet or individually for full captions/titles and narrow clean boundaries; fix crops that include the next paragraph, page chrome, neighboring content, excessive whitespace, or any truncated caption.
- Confirm every key number in the review maps to a paper section/table/figure or a clearly stated calculation.
- Confirm code claims include file paths and commit hashes.
- If tests or extraction tools could not run, state that limitation in the final response.

## Resources

- `references/markdown-template.md`: reusable Chinese Markdown structure, including the standard paper review sections and "解读问题/待验证清单".
- `scripts/extract_pdf_assets.py`: optional helper to extract PDF text and render page PNGs for offline papers.
- `scripts/crop_pdf_figures.py`: optional helper to batch crop figures/tables from page PNGs and create a contact sheet for QA.
