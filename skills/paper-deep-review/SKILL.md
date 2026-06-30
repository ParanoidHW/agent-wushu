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
   - Build a **symbol table before the method/formula discussion**. For every symbol used in key equations or metrics, record its meaning, scope/indexing, units if any, source equation/section, and any paper-specific ambiguity. Do not assume a symbol has the same meaning across papers.
   - Add a short **terminology/data-construction clarification** for non-obvious terms such as regenerated data, teacher/student logits, oracle/target/draft model, temperature setting, budget, tree width/depth, or benchmark variants.
   - Separate **paper-level conceptual claims** from **implementation-level behavior**. If a term such as causal mask, tree mask, block mask, branch conditioning, verification, or drafting appears in multiple stages, state exactly which stage it belongs to and whether the code implements the same object.
   - When the paper's prose is imprecise, reconcile it against equations, figures, appendix text, and code before writing the review. Prefer a qualified statement over copying an ambiguous phrase.

5. **Compare related work.**
   - Extract the paper's own related-work groups.
   - Compare against the current paper by mechanism, benefit, limitation, and fairness of the comparison.
   - Avoid broad literature essays; focus on why the paper's design differs and what trade-off it makes.

6. **Analyze infrastructure requirements.**
   - Include compute, memory, bandwidth, interconnect, scheduler/runtime, and custom-operator implications when relevant.
   - Provide formulas for derived estimates, such as parameter count, activation/cache size, communication volume, expected throughput, or latency.
   - Separate paper-reported numbers from your own calculations.
   - Separate mechanism effects from system effects. For example, distinguish candidate-set quality, verification algorithm, custom kernels, batching, KV-cache layout, CUDA graphing, and scheduler policy. Do not attribute accepted-length gains to an execution kernel unless the paper/code shows that the kernel changes the candidate set or scoring.

7. **Cross-check code when available.**
   - Inspect configs, model architecture, loss, data pipeline, evaluation, and serving/inference paths.
   - Link local file paths and, when possible, stable GitHub URLs pinned to a commit.
   - State what is implemented, what is only described in the paper, and what remains ambiguous.
   - If public model weights/checkpoints are referenced, inspect their metadata and configuration when accessible: open/gated/private status, files present, commit/revision, parameter count, architecture class, critical hyperparameters, and paper-specific flags. Compare these configs against baseline checkpoints when the paper claims architectural or capacity differences.
   - For code/config comparisons, explicitly distinguish capacity changes (layers, width, heads, parameter count), algorithmic changes (masking, scoring, sampling, loss), and runtime changes (kernels, cache, graphing).
   - If network access or model metadata access fails, state the limitation and do not infer checkpoint configuration from README claims alone.

8. **Attribute gains carefully.**
   - When explaining why a method improves results, build a component-level attribution table if the paper has enough baselines: data/training objective, draft/candidate generation, search/tree construction, target verification, and serving/runtime.
   - Use bridge baselines (for example, baseline -> tree variant -> proposed method) to estimate contributions only as a rough decomposition. Mark such calculations as inferred, not paper-proven, unless the paper reports matched ablations.
   - Report both absolute and relative changes in the paper's primary metric, and identify when a component affects accepted length/quality versus latency/throughput.

9. **Write `analysis.md`.**
   - Use the reusable template in `references/markdown-template.md`.
   - Include a source/figure inventory near the top.
   - Include the symbol table near the top before the method section.
   - Include a terminology/data-construction clarification when the paper uses paper-specific names for datasets, variants, generated data, budgets, masks, or model roles.
   - Include images inline near the discussion they support.
   - End with practical limitations, research inspirations, and unresolved reading questions.

## Quality Checks

Before finishing:

- Confirm all Markdown image links resolve.
- Review all crops in a contact sheet or individually for full captions/titles and narrow clean boundaries; fix crops that include the next paragraph, page chrome, neighboring content, excessive whitespace, or any truncated caption.
- Confirm every key number in the review maps to a paper section/table/figure or a clearly stated calculation.
- Confirm code claims include file paths and commit hashes.
- Confirm the symbol table covers every variable used in key formulas, metrics, and tables.
- Confirm ambiguous mechanism terms are stage-qualified: drafting vs tree construction vs target verification vs serving/runtime.
- Confirm gain-attribution statements are supported by matched ablations or explicitly marked as rough/inferred decompositions.
- Confirm checkpoint/config claims are grounded in inspected metadata or clearly marked as unverified.
- If tests or extraction tools could not run, state that limitation in the final response.

## Resources

- `references/markdown-template.md`: reusable Chinese Markdown structure, including the standard paper review sections and "解读问题/待验证清单".
- `scripts/extract_pdf_assets.py`: optional helper to extract PDF text and render page PNGs for offline papers.
- `scripts/crop_pdf_figures.py`: optional helper to batch crop figures/tables from page PNGs and create a contact sheet for QA.
