# A/B Testing Project Report

## Executive Summary

This project provides a fully automated A/B testing pipeline covering two kinds of evaluation:

1. **Internal business experiments** — 5 datasets in `data/`, each tied to a real product decision question
2. **External benchmark** — Kaggle public dataset in `data/external/kaggle_ab_data.csv`, used to demonstrate pipeline portability and data-cleaning rigor

All datasets are processed in a single command via [scripts/run_batch_analysis.py](../scripts/run_batch_analysis.py), which produces validation reports, per-dataset result CSVs, figures, and a consolidated markdown report.

---

## Pipeline Architecture

### `scripts/run_pipeline.py` — Single-dataset pipeline
- Accepts any CSV path and an optional metric override
- Auto-detects the variant column from candidates: `variant`, `group`, `arm`, `experiment_group`
- Auto-detects the primary metric or uses the override
- Runs pre-analysis validation before inference
- Generates distribution plot and bar chart
- Saves per-dataset result CSV and validation report
- Supports a `clean_rules` parameter for public-dataset cleaning (see below)

### `scripts/validation.py` — Pre-analysis validation
Six checks run before any statistical test:
1. Sample ratio mismatch (chi-square)
2. Data integrity (duplicate session IDs, duplicate user IDs, assignment consistency)
3. Covariate balance (standardised mean differences)
4. Temporal stability (allocation CV over time)
5. Outlier detection
6. Sample size adequacy (MDE at 80% power, α=0.05)

### `scripts/statistical_analysis.py` — Statistical engine
- Detects metric type: binary, continuous, count, or categorical
- Selects appropriate test: Two-Proportion Z-Test, Welch t-test, Mann-Whitney, Kruskal-Wallis, Chi-Square
- Returns effect sizes, relative lift, confidence intervals, and interpretation text

### `scripts/run_batch_analysis.py` — Batch runner
- Runs the full pipeline for every registered dataset
- Tests all available metrics per experiment (not just one)
- Applies Holm-Bonferroni correction across all metrics within each experiment
- Computes power analysis and MDE for binary-metric experiments
- Applies automatic data cleaning for external/public datasets
- Outputs:
  - `reports/statistical_results/batch_summary.csv` — primary metric per dataset
  - `reports/statistical_results/batch_all_metrics.csv` — all metrics with correction flags
  - `docs/BATCH_ANALYSIS_REPORT.md` — human-readable report with tables

---

## Key Improvements Over Initial Version

| Improvement | Details |
|---|---|
| Reusable pipeline | `analyze_dataset()` is a callable function, not a top-level script |
| Pre-analysis validation | 6 checks run before inference on every dataset |
| Binary plot fix | Binary metrics use positive-rate bar chart instead of blank boxplot |
| Multi-metric analysis | All columns tested per experiment, not just one |
| Holm-Bonferroni correction | Controls family-wise error rate across metrics within each experiment |
| Power analysis & MDE | Minimum detectable effect computed from actual sample sizes |
| Public-dataset cleaning | `clean_public_dataset()` removes mismatches and deduplicates users before inference |
| Batch runner | One command processes all 6 datasets end-to-end |
| Consolidated reports | `batch_summary.csv` and `batch_all_metrics.csv` cover all experiments |

---

## Internal Experiment Results (Summary)

See [BATCH_ANALYSIS_REPORT.md](BATCH_ANALYSIS_REPORT.md) for the full per-metric breakdown.

| Experiment | Primary metric | Result | Key finding |
|---|---|---|---|
| Menu Navigation | `added_to_cart` | **Significant** | Dropdown menu reduced add-to-cart by ~10 pp — do not ship |
| Novelty Slider | `products_added_from_novelties` | **Significant** | Personalized slider drove +283% relative lift — ship it |
| Product Sliders | `revenue_from_recommendations` | **Significant** | B (similar products top) generates highest revenue — follow-up A/B needed |
| Reviews | `converted` | Not significant | No measurable effect; insufficient evidence to ship |
| Search Engine | `converted` | Not significant | Conversion alone insufficient signal; extend experiment window |

---

## External Kaggle Result

### Dataset
- Source: `data/external/kaggle_ab_data.csv` (294,480 rows raw)
- Schema: `user_id`, `timestamp`, `group`, `landing_page`, `converted`

### Data cleaning applied automatically
The pipeline's `clean_rules` mechanism removed:
- 3,895 duplicate users (keep first)
- 2,044 rows with assignment mismatches (`group` ↔ `landing_page` disagreement)
- Clean sample: **288,541 rows** (144,226 control / 144,315 treatment)

### Result on cleaned data
- Control conversion: 12.03%
- Treatment conversion: 11.87%
- Absolute difference: −0.16 pp
- P-value: 0.195
- Conclusion: **not significant** — the new landing page does not improve conversion

### Why this matters for the portfolio
This dataset demonstrates that the pipeline handles public/messy data correctly — it detects data quality issues during validation, applies cleaning transparently, and still produces a reproducible inference result.

---

## Cross-Source Comparison Rule

| Use case | Appropriate? |
|---|---|
| Testing whether the pipeline works on a different schema | Yes |
| Demonstrating validation logic catches real issues | Yes |
| Comparing effect sizes or winners between internal and Kaggle | **No** |
| Making business decisions from the Kaggle result | **No** |

Internal datasets are the decision track. The external dataset is the methodology demonstration track.

---

## What to Emphasise in Interviews

This project demonstrates that A/B testing is not just about running a t-test. The full workflow includes:

- **Experiment design** — what metric, what variant, what sample size is needed
- **Pre-analysis validation** — SRM, data integrity, covariate balance, power
- **Test selection** — the right test for the metric type and variant count
- **Multiple testing control** — Holm correction when testing multiple metrics
- **Public data hygiene** — deduplication and assignment mismatch detection
- **Business interpretation** — practical significance, not just statistical significance
- **Automation** — reproducible batch runs with a single command
