---
name: research-paper-to-ppt
description: Use when asked to analyze an academic paper or technical article/PDF/source repository, produce a rigorous Markdown research report, and generate an editable 16:9 PowerPoint deck with rendered equations, extracted paper figures/tables, AI infra and implementation analysis, and screenshot-based QA.
---

# Research Paper to PPT

## Purpose

Turn a paper PDF, technical article, source folder, or code repository into:

1. a rigorous Markdown research report,
2. extracted figures/tables/equations and optional generated explanatory diagrams as reusable assets,
3. an editable 16:9 `.pptx` deck,
4. rendered QA images proving the deck is readable and not distorted.

Use this skill for requests like “analyze this paper and make slides”, “deep research this PDF then generate PPT”, “paper reading report PPT”, or “extract figures and equations into a presentation”.

This skill is generic. Do not hard-code paper IDs, project names, local paths, benchmark names, or one-off conclusions into the skill. Use placeholders such as `<input_pdf>`, `<slug>`, `<paper_title>`, `<repo_url>`, and `<output_dir>`.

## Analysis Standard

The report and deck should be rigorous, pragmatic, and traceable. Do not only state conclusions; show the reasoning chain:

```text
Claim -> Paper evidence/code evidence -> Reasoning/calculation -> Caveat or boundary condition
```

Required report framework:

1. Paper basic information: field, core problem, research goal.
2. Core contributions and innovations: the 3-5 most important ideas.
3. Research method: problem targeted, key idea, technical route, experiment design, and model/system architecture when applicable.
4. Key conclusions: main results, data-backed findings, and whether the evidence validates the proposed hypothesis.
5. Strengths and limitations: advantages, weaknesses, risks, and possible improvements.
6. Research implications: reusable ideas, follow-up experiments, and extension directions.

Every numerical claim, chart interpretation, and experimental result must cite the paper section, table, figure, appendix, or code location that supports it. If the evidence is inferred rather than directly stated, label it as an inference.

## Core Workflow

### 1. Inspect Inputs

- Locate the PDF, source package, `.tex`, `.bib`, figures, existing PPT/scripts, and package dependencies.
- Prefer paper source (`<source_dir>/main.tex`, `<source_dir>/reference.bib`, `<source_dir>/figs/`) over PDF-only extraction when available.
- For arXiv papers, prioritize downloading the arXiv source tarball before relying on PDF-only extraction. If the source contains `.tex`, tables, and figure files, use those assets as the primary evidence path because they preserve captions, formulas, tables, and figure fidelity much better than OCR or PDF region extraction.
- Record output paths before editing:
  - `deep_research_<slug>/`
  - `<paper_title_or_slug>_analysis.md`
  - `<paper_title_or_slug>_research_editable.pptx`
  - `<paper_title_or_slug>_research_editable_v2.pptx` if overwrite is blocked.
- If the user names other skills such as deep research or PPTX generation, compose with those skill instructions instead of replacing them.

### 2. Build Research Materials

Use a staged structure, but adapt scope to the user request:

```text
deep_research_<slug>/
├── paper_db.jsonl
├── phase1_frontier/frontier.md
├── phase2_survey/survey.md
├── phase3_deep_dive/selection.md
├── phase3_deep_dive/deep_dive.md
├── phase4_code/code_repos.md
├── phase5_synthesis/synthesis.md
├── phase5_synthesis/gaps.md
├── phase6_report/report.md
├── assets/formula/
├── assets/paper_figures/
├── assets/paper_figures_trimmed/
├── assets/generated_diagrams/
└── qa_render/
```

For a single-paper analysis, do not fake a broad literature search. Build a focused `paper_db.jsonl` from the target paper bibliography plus direct comparators.

The Markdown report must include the six required analysis sections above. It should also include:

- a related-work comparison table for the most relevant cited or directly competing papers,
- an AI infra implications section when the work affects compute, memory, bandwidth, networking, kernels, or serving,
- a code cross-check section when source code or implementation artifacts are available,
- an asset inventory listing each extracted figure/table/equation and its paper source.

### 3. Extract Paper Evidence

Extract rather than redraw whenever possible.

- From LaTeX source: use `rg` on `<source_dir>/main.tex` for sections, tables, captions, equations, hardware details, and result paragraphs.
- From figure PDFs:
  ```bash
  mkdir -p deep_research_<slug>/assets/paper_figures
  for f in <source_dir>/figs/*.pdf; do
    base=$(basename "$f" .pdf)
    pdftocairo -png -singlefile -r 220 "$f" "deep_research_<slug>/assets/paper_figures/$base"
  done
  ```
- Trim white margins without changing aspect ratio. See `references/asset-qa.md` for a Python snippet.
- If figures, tables, algorithms, or screenshots are not extractable:
  - create a clearly labeled placeholder in the Markdown and deck,
  - state which paper figure/table/algorithm the placeholder is reserved for,
  - tell the user what manual extraction or screenshot step is needed,
  - create a simple deterministic diagram in PPT shapes only when it is faithful to the paper,
  - use image generation only for non-factual illustrative raster visuals, not for factual charts.

Image generation can be used for slide-ready explanatory visuals in these cases:

- The paper or article is too short/simple and the deck needs a high-level overview or summary diagram.
- A key paper figure, table, algorithm flow, or screenshot cannot be extracted with acceptable fidelity.
- A key principle or mechanism has no visual in the source, but a conceptual diagram is necessary to explain it clearly.

When using image generation:

- Follow the `imagegen` skill and save project-bound assets under `deep_research_<slug>/assets/generated_diagrams/`.
- Label the image in the report/deck as a generated conceptual illustration or generated reconstruction.
- Do not invent numeric results, axes, tables, benchmark values, or paper claims in generated images.
- Keep paper-derived evidence separate from generated explanatory visuals.

### 4. Render Equations

If formulas need to look polished and do not need to be editable, render LaTeX to SVG and insert the SVG.

- Use `latex` + `dvisvgm`.
- Render formulas in a preprocessing step before running the Node/PptxGenJS deck generator. Do not shell out to LaTeX from inside the Node PPT generation path unless there is no practical alternative; precomputed SVGs are more stable, cacheable, and easier to QA.
- Cache generated SVG files; do not rerender every run.
- Keep original equation text in the Markdown report for traceability.
- Never stretch equation images. Compute display size from the SVG/image aspect ratio before inserting.

See `references/asset-qa.md` for fit-box logic.

### 5. Analyze Related Work, Code, and Infra

Related work:

- Compare the target work with the most relevant papers or systems mentioned in related work.
- Summarize advantages, disadvantages, and the specific axis of difference, such as accuracy, complexity, training cost, serving cost, hardware dependency, or deployment maturity.
- Avoid broad literature claims unless supported by the paper bibliography or a focused literature search.

Code cross-check:

- If open-source code exists, inspect the implementation and compare it with the paper description.
- Cite repository URLs, file paths, functions/classes, kernels, configs, and commit/version when available.
- Use source code to clarify under-specified paper details, but label this as code-derived evidence.
- Do not claim code/paper consistency unless the relevant implementation path has been inspected.

AI infra analysis:

- Analyze implications for compute, memory capacity, memory bandwidth, interconnect/network bandwidth, kernel design, data layout, quantization/dequantization, and serving behavior.
- Include formulas for derived data. Common examples:
  - `memory_bytes = num_elements * bytes_per_element`
  - `bandwidth_lower_bound = bytes_moved / runtime_seconds`
  - `actual_speedup = baseline_time / method_time`
  - `efficiency_vs_theory = actual_speedup / theoretical_speedup`
  - `gap_to_theory = theoretical_speedup - actual_speedup`
- Call out new or unusual custom operators/instructions, such as custom CUDA/Triton kernels, bit operations, tensor-core use, layout transforms, packing/unpacking, or fused kernels.
- Separate theoretical performance upside from measured performance and explain the gap.

See `references/analysis-framework.md` for a fuller template.

### 6. Generate the PPT

Prefer `pptxgenjs` for editable decks.

When generating, editing, inspecting, or QA-rendering `.pptx` files, also follow the installed `pptx` skill. Treat this skill as the paper-analysis, evidence, and narrative layer; treat `pptx` as the deck implementation, formatting, and PowerPoint QA layer. If formatting, layout, or PPTX implementation principles conflict, follow the `pptx` skill.

Design rules:

- Unless the user explicitly requests another language, write the PPT slide titles, bullets, takeaways, table labels, and speaker-facing explanatory text in Chinese. Keep paper titles, method names, dataset names, code symbols, equations, and citation labels in their original language when that improves precision.
- Use 16:9 widescreen layout.
- Keep a professional palette. Outside black and white, use no more than four colors; prefer gray/charcoal plus one restrained accent and one red highlight color for critical points.
- Tune information density to the deck purpose. For an external introduction deck, do not make it a thin abstract or an appendix dump: include design rationale, evidence chains, and boundary conditions, but integrate them into readable topic pages.
- Use dense but organized pages: one main claim, 2-4 evidence blocks, one emphasized takeaway when useful.
- Use tables for comparisons and infra implications. Center tables by default, especially metric tables, ablation tables, and method comparison tables in report-style decks.
- Use extracted paper figures for evidence; cite them on-slide with `Fig.` labels.
- Use generated diagrams only as conceptual aids, and label them as generated or reconstructed.
- Do not stretch images, equations, heatmaps, plots, or attention maps. Use aspect-ratio fit logic for every figure and formula.
- Render formulas as LaTeX images unless the user explicitly requires editable formulas.
- Use red bold styling or red outline callouts sparingly for high-priority information only.
- After the first PPT draft, perform a content integration pass: newly discovered details should be merged into the most relevant existing topic slide instead of being appended mechanically at the end. Add new slides only when the material forms a distinct argument or evidence block.
- Avoid production-process wording in user-facing slides, including phrases such as `对外口径`, `讲解要点`, `不要过度声称`, `制作说明`, `占位`, and `TODO`. Rewrite these as natural content statements, evidence caveats, or speaker notes that do not expose the creation process.
- Include AI infra/implementation analysis when relevant:
  - required hardware instructions,
  - theoretical throughput,
  - actual speedup gap,
  - kernel overhead,
  - memory/cache behavior,
  - training/quantization release cost,
  - serving metrics to validate.

Recommended slide structure:

1. Title and main judgement.
2. Executive summary.
3. Technical positioning.
4. Method decomposition with formulas.
5. Theory and assumptions.
6. Ablation or recipe analysis.
7. Efficiency evidence from paper figures.
8. Method/attention map visual evidence.
9. Task-level evidence.
10. AI infra / serving cost model.
11. Deployment risks.
12. Final takeaways and next experiments.

### 7. QA the Deck

Always render the deck before declaring done.

```bash
libreoffice --headless --nologo \
  -env:UserInstallation=file:///tmp/codex-lo-profile \
  --convert-to pdf --outdir /tmp/codex-lo-out deck.pptx

pdftoppm -jpeg -r 150 deck.pdf qa_render/slide
```

Then inspect a contact sheet and any high-risk slides:

- equations,
- paper figures,
- dense tables,
- dark title slides,
- slides with red highlight boxes.

Check for:

- image or equation distortion,
- text overflow,
- weak contrast,
- excessive whitespace,
- table text too small,
- title/tag collision,
- leftover placeholders,
- English slide titles or UI labels when the user did not request an English deck,
- production-process wording such as `对外口径`, `讲解要点`, `不要过度声称`, `制作说明`, `占位`, `TODO`, `TBD`, or `placeholder`.

Also run a text QA pass with `markitdown` or equivalent PPTX text extraction:

```bash
python -m markitdown deck.pptx > qa_render/deck_text.md
rg -n "PLACEHOLDER|TODO|TBD|placeholder|对外口径|讲解要点|不要过度声称|制作说明|占位" qa_render/deck_text.md
```

Use this extracted text to catch residual placeholders, English headings in a default-Chinese deck, and authoring artifacts that may not stand out in rendered screenshots.

If visual QA finds issues, patch the generator script and regenerate.

## Output Contract

Final response should include:

- Markdown report path,
- PPTX path,
- extracted asset path,
- QA render/contact sheet path,
- known limitations, such as overwrite failure due to file lock.

Keep the final answer concise and identify the newest usable PPTX if multiple versions exist.

## When to Read References

- Read `references/asset-qa.md` when implementing equation/figure extraction, aspect-ratio fitting, or rendered QA.
- Read `references/analysis-framework.md` when shaping the Markdown report, related-work comparison, code cross-check, or AI infra analysis.
