---
name: ai-algorithm-survey
description: Search, select, deep-review, and synthesize papers for a specific AI algorithm field. Use when the user provides an AI algorithm/topic/domain and wants literature discovery through search engines, arXiv, GitHub/awesome paper lists, and top AI conferences or journals such as CVPR, ICML, ICLR, NeurIPS, AAAI, TPAMI, TIP, IROS, ICRA, RA-L, with paper affiliations, repository popularity, citation/cross-reference frequency, and high-value paper signals recorded, then wants each key paper analyzed with $paper-deep-review and a final cross-paper lineage, relationship, and trend summary.
---

# AI Algorithm Survey

## Overview

Use this skill to turn a user-specified AI algorithm field into a traceable literature survey: search broadly, select the most relevant papers, run `$paper-deep-review` on each selected paper, then synthesize the technical lineage and evolution trend across the works.

Default output language is Chinese unless the user asks otherwise. Keep paper titles, method names, datasets, formulas, and code identifiers in their original language when that preserves precision.

## Output Layout

Create one workspace folder per survey:

```text
ai_algorithm_survey_<field_slug>/
├── search_log.md
├── github_sources.md
├── impact_signals.md
├── paper_db.jsonl
├── selection.md
├── papers/
│   └── <year>_<short-title>/
│       ├── paper.pdf
│       ├── source/
│       ├── figures/
│       └── analysis.md
└── synthesis.md
```

Use `references/synthesis-template.md` when writing `synthesis.md`.

## Workflow

### 1. Scope the Field

Extract or ask for only the missing high-impact constraints:

- target algorithm field or keyword set,
- expected paper count; default to 6 selected papers when not specified,
- time window; default to no hard cutoff but include seminal, bridge, and recent work,
- domain boundaries, such as CV, NLP, robotics, generative models, optimization, systems, or multimodal learning,
- whether to include surveys, benchmarks, code repositories, or only peer-reviewed papers.

Normalize the field into a compact slug, then create the output folder before searching.

### 2. Build Search Queries

Search must be current. Use the available internet/search tools and record exact query strings, source names, and search date in `search_log.md`.

Generate aliases before searching:

- exact user phrase,
- common abbreviations,
- related method names,
- benchmark/dataset names,
- predecessor and successor terms discovered during search.

Cover at least four source categories when possible:

- general search engine queries for broad discovery,
- GitHub repositories and `awesome-*` paper lists for actively maintained subfield collections,
- arXiv queries and arXiv IDs for preprints/source material,
- venue/proceedings queries for peer-reviewed versions.

Use venue-focused patterns such as:

```text
"<keyword>" arxiv
"<keyword>" github awesome papers
site:github.com "<keyword>" "awesome"
site:github.com "awesome-<keyword>"
site:github.com "<keyword>" "paper list"
"<keyword>" "CVPR" OR "ICCV" OR "ECCV"
"<keyword>" "ICML" OR "ICLR" OR "NeurIPS"
"<keyword>" "AAAI"
"<keyword>" "TPAMI" OR "T-PAMI" OR "IEEE Transactions on Pattern Analysis and Machine Intelligence"
"<keyword>" "TIP" OR "IEEE Transactions on Image Processing"
"<keyword>" "IROS" OR "ICRA" OR "RA-L"
site:openreview.net "<keyword>"
site:proceedings.mlr.press "<keyword>"
site:papers.nips.cc "<keyword>"
site:openaccess.thecvf.com "<keyword>"
site:ojs.aaai.org "<keyword>"
site:ieeexplore.ieee.org "<keyword>"
```

For NLP, data mining, graphics, systems, or theory topics, add the appropriate venues, such as ACL, EMNLP, NAACL, KDD, SIGIR, SIGGRAPH, MLSys, OSDI, SOSP, JMLR, IJCV, TNNLS, or COLT.

For GitHub/awesome sources:

- Search for repositories named `awesome-<topic>`, `<topic>-papers`, `<topic>-survey`, `<topic>-reading-list`, and `<topic>-resources`.
- Prefer repositories with recent commits, maintained paper tables, venue/year fields, links to arXiv/OpenReview/proceedings, or taxonomy sections.
- Record useful repositories in `github_sources.md` with repo URL, owner, stars, forks, open issues or PR activity if visible, last update signal, accessed date, relevant sections, and what papers or subfields were discovered there.
- Treat GitHub lists as discovery sources, not authority. Verify each selected paper against arXiv, proceedings, OpenReview, journal pages, or the paper PDF before deep review.

### 3. Collect Impact Signals

For each serious candidate, collect lightweight popularity and value signals before final selection:

- repository popularity for official or widely used code: stars, forks, watchers if visible, recent commit/release date, issue/PR activity, license, and whether the repo is official or third-party,
- awesome/list frequency: how many GitHub lists or curated resources include the paper, and whether those lists are recently maintained,
- academic citation signal: citation count and source when visible from Google Scholar snippets, Semantic Scholar, OpenAlex, Crossref, Connected Papers, Papers with Code, publisher pages, or search results,
- cross-paper reference frequency inside the candidate set: how many other candidate/selected papers cite, compare against, benchmark against, or name the paper in related work,
- implementation adoption: whether the method has official code, multiple reimplementations, Papers with Code entries, benchmark leaderboards, or downstream libraries.

Write the signal summary to `impact_signals.md`. Always record the date and source of volatile metrics such as stars and citation counts. Treat all metrics as approximate unless obtained from a primary or API-backed source.

### 4. Normalize the Candidate Database

Write every serious candidate to `paper_db.jsonl`. Use one JSON object per paper:

```json
{
  "title": "...",
  "year": 2025,
  "venue": "ICLR",
  "authors": ["..."],
  "affiliations": ["University A", "Company B"],
  "affiliation_evidence": "paper first page / author block / OpenReview / project page / unknown",
  "paper_url": "https://...",
  "pdf_url": "https://...",
  "arxiv_id": "2501.00000",
  "code_url": "https://github.com/...",
  "repo_metrics": {
    "stars": 0,
    "forks": 0,
    "recent_update": "2026-07-05",
    "official": true,
    "evidence": "GitHub page accessed 2026-07-05"
  },
  "citation_metrics": {
    "count": 0,
    "source": "Semantic Scholar / Google Scholar snippet / OpenAlex / unknown",
    "accessed": "2026-07-05"
  },
  "cross_reference_count": 0,
  "cross_reference_evidence": ["cited by candidate paper X related work", "benchmarked by paper Y"],
  "awesome_list_count": 0,
  "source": ["arXiv", "OpenReview", "GitHub awesome list"],
  "github_discovery_source": "https://github.com/owner/awesome-topic#section",
  "value_signals": ["highly cited", "official repo widely starred", "frequently benchmarked"],
  "keywords": ["..."],
  "role": "seminal|core|bridge|variant|recent|survey|benchmark",
  "relevance_reason": "...",
  "selected": false
}
```

Deduplicate arXiv, OpenReview, proceedings, and journal entries. Prefer the peer-reviewed version for venue/year, but keep arXiv IDs and source URLs when they provide PDF or source access.

Record paper-level affiliations/organizations for every candidate when available. Extract them from the paper PDF author block, arXiv metadata, OpenReview page, proceedings page, project page, or official code README. Do not infer affiliations from author names alone. If affiliations are unavailable or ambiguous, use an empty list and set `affiliation_evidence` to `unknown` or a precise caveat.

### 5. Select Papers for Deep Review

Default selection is 6 papers. Adjust only when the user asks for a different scope or the field genuinely needs a smaller/larger set.

Select papers to cover the algorithmic evolution, not just the newest results:

- one or two seminal or problem-defining works,
- one or two core method papers that established the main mechanism,
- one bridge or variant paper that changed assumptions, training data, architecture, or evaluation,
- one or two recent or high-impact papers from top venues/journals,
- optional survey/benchmark paper for taxonomy only; do not count it as a method paper unless it contains a core technical contribution.

Prioritize high-value papers when they also serve the evolution narrative. High value is not one metric; use a combined judgment from:

- academic impact: citation count, cross-reference frequency, and whether later papers use it as a baseline or taxonomy anchor,
- practical impact: official repo popularity, active maintenance, forks/reimplementations, and downstream adoption,
- conceptual impact: introduces a problem formulation, mechanism, benchmark, or evaluation protocol that later papers inherit,
- recency-adjusted impact: recent papers may have low citation counts but high GitHub/list activity or strong top-venue placement.

Do not let raw GitHub stars override paper relevance or evidence quality. Mark popularity-only papers as such if the method is not central to the field's technical lineage.

Write `selection.md` with:

- selected papers and why each was selected,
- important candidates excluded and why,
- evidence that search covered GitHub/awesome sources, arXiv, and top venues/journals relevant to the field,
- organization/university distribution of selected papers, with caveats for missing affiliations,
- high-value signal summary, including citation counts, cross-reference counts, repo popularity, and awesome/list frequency where available,
- access limitations such as paywalls, missing PDF, or blocked code.

### 6. Deep-Review Each Selected Paper

For every selected paper, use `$paper-deep-review` and follow its required workflow. Do not replace the deep review with a short abstract summary.

For each paper:

- create `papers/<year>_<short-title>/`,
- acquire PDF/source/code when available,
- run the single-paper analysis using `$paper-deep-review`,
- write the result as `papers/<year>_<short-title>/analysis.md`,
- preserve paper/source/code URLs and commit hashes when code is inspected.

If `$paper-deep-review` is unavailable, stop and tell the user it must be installed or provided before the batch survey can meet the requested standard.

### 7. Synthesize the Field

After all selected papers have `analysis.md`, write `synthesis.md` from the deep-review outputs and original paper metadata.

Include:

- search scope and selection criteria,
- GitHub/awesome repositories used as discovery sources and what they contributed,
- high-heat/high-value paper ranking with evidence, separating academic citations, cross-paper references, GitHub popularity, and conceptual importance,
- timeline of the selected works,
- affiliation/organization distribution across candidate and selected papers,
- taxonomy of method families,
- lineage graph or relation table showing which paper extends, replaces, critiques, or benchmarks against which earlier work,
- comparison table by problem formulation, core mechanism, data/benchmark, metrics, compute/system cost, strengths, and limitations,
- evolution of assumptions, architectures, training objectives, inference procedures, and evaluation protocols,
- trend summary: what is converging, what remains unsettled, and where the next likely research directions are,
- caveats about evidence quality, venue status, and whether claims come from paper text, code inspection, or your own inference.

Do not claim a paper is the "latest" or "state of the art" unless the current search supports that statement and the search date is recorded.

## Quality Checks

Before finishing:

- Confirm `search_log.md`, `github_sources.md`, `impact_signals.md`, `paper_db.jsonl`, `selection.md`, each selected paper `analysis.md`, and `synthesis.md` exist.
- Confirm search covered general search, GitHub/awesome repositories, arXiv, and relevant top venues/journals when available.
- Confirm candidate papers record `affiliations` and `affiliation_evidence`, using explicit caveats where affiliations are unavailable.
- Confirm candidate papers record impact signals: repo metrics, citation metrics, cross-reference count/evidence, and awesome-list frequency where available.
- Confirm every selected paper has a clear role in the evolution narrative.
- Confirm each selected method paper was analyzed with `$paper-deep-review`.
- Confirm synthesis claims cite selected papers or their `analysis.md` files; label cross-paper inferences explicitly.
- Separate peer-reviewed versions from arXiv-only preprints.
- State missing access, blocked downloads, paywalls, unavailable code, or extraction failures in the final response.

## Resources

- `references/synthesis-template.md`: Chinese structure for the final cross-paper survey and trend synthesis.
