# Analysis Framework Reference

Use this reference when turning a paper or technical article into a Markdown report and PPT narrative. Keep the output specific to the current input; do not preserve paper-specific IDs, paths, or conclusions in reusable materials.

## Markdown Report Template

```markdown
# <paper_title> Research Analysis

## 1. Paper Basic Information

- Field:
- Core problem:
- Research goal:
- Target scenario/users:
- Evidence source: Section <x>, Figure <y>, Table <z>, or code link.

## 2. Core Contributions and Innovations

List 3-5 items. For each item:

- Contribution:
- Why it matters:
- Evidence:
- Boundary condition:

## 3. Research Method

- Problem being solved:
- Main idea:
- Technical route:
- Architecture or algorithm flow:
- Training/evaluation design:
- Key equations:
- Logic chain: problem -> design choice -> expected effect -> measurable result.

## 4. Key Conclusions

For each conclusion:

- Claim:
- Data source:
- Calculation, if derived:
- Reasoning chain:
- Caveat:

## 5. Strengths and Limitations

- Strengths:
- Limitations:
- Missing evidence:
- Practical risks:
- Possible improvements:

## 6. Research Implications

- Reusable ideas:
- Extension directions:
- Follow-up experiments:
- Deployment validation needed:

## Related Work Comparison

| Work | Core idea | Strength | Weakness | Difference from target paper | Evidence |
|---|---|---|---|---|---|

## AI Infra Analysis

| Dimension | Requirement or impact | Formula/data source | Risk or validation needed |
|---|---|---|---|
| Compute |  |  |  |
| Memory capacity |  |  |  |
| Memory bandwidth |  |  |  |
| Interconnect/network |  |  |  |
| Custom operator/kernel |  |  |  |
| Serving/latency |  |  |  |

## Code Cross-Check

| Paper claim | Code location | Match status | Notes |
|---|---|---|---|

## Asset Inventory

| Asset | Source in paper | Extraction method | Output path | Notes |
|---|---|---|---|---|
```

## Evidence Rules

Use this unit for important claims:

```text
Claim: <what the paper implies>
Evidence: Section/Figure/Table/Equation/Code link
Reasoning: <why the evidence supports the claim>
Calculation: <formula and substituted values, if any>
Caveat: <what is not proven or may not generalize>
```

If a number is derived, show the formula. If a chart is interpreted visually, say it is read from the chart. If a source is missing, use a placeholder and mark it as unresolved.

## Infra Formula Examples

Adapt formulas to the paper domain; do not force all of them into every report.

```text
memory_bytes = num_elements * bytes_per_element
activation_memory = batch_size * sequence_length * hidden_dim * bytes_per_element
attention_map_memory = batch_size * num_heads * sequence_length^2 * bytes_per_element
bytes_moved = read_bytes + write_bytes
bandwidth_lower_bound = bytes_moved / runtime_seconds
actual_speedup = baseline_time / method_time
efficiency_vs_theory = actual_speedup / theoretical_speedup
gap_to_theory = theoretical_speedup - actual_speedup
tokens_per_second = generated_tokens / latency_seconds
cost_per_token = serving_cost / generated_tokens
```

When analyzing kernels or custom operators, check whether gains come from reduced arithmetic, reduced memory traffic, better cache locality, lower precision/bit packing, fused operations, or hardware-specific instructions. Separate algorithmic savings from engineering savings.

## Figure and Placeholder Policy

Prefer this order:

1. Extract original figures/tables/algorithm blocks from source assets.
2. Screenshot the relevant PDF region if extraction is not available.
3. Reconstruct a faithful schematic with PPT shapes when the structure is simple.
4. Use image generation for a conceptual overview, generated reconstruction, or missing principle diagram when it improves explanation.
5. Use a placeholder when fidelity cannot be guaranteed.

Placeholder format:

```text
[PLACEHOLDER: <Figure/Table/Algorithm name> from Section <x>. 
Manual action needed: extract/screenshot <specific region or page>.]
```

For every inserted image, preserve the original aspect ratio. For plots, heatmaps, attention maps, and formulas, verify by rendering the PPT to images before final delivery.

## Image Generation Policy

Use image generation only for explanatory visuals, not for factual evidence. It is appropriate in these cases:

1. The paper or article has limited visual material, and the deck needs an overview or summary diagram.
2. A key source figure/table/algorithm flow cannot be extracted or screenshotted with acceptable quality.
3. A key mechanism has no source visual, and a conceptual diagram is needed to explain it.

Generated visuals must be saved under `deep_research_<slug>/assets/generated_diagrams/` when used in a project deliverable. Label them as `Generated conceptual illustration` or `Generated reconstruction`. Do not place fabricated axes, data values, table cells, benchmark numbers, or paper-specific claims inside generated images unless they are copied from cited paper/code evidence.
