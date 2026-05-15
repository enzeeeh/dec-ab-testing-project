# A/B Testing Framework

This project is a portfolio-grade A/B testing framework built around five real internal business experiments. It includes automated pre-analysis validation, appropriate statistical test selection, multi-metric analysis with multiple-testing correction, power analysis, and a batch runner that produces machine-readable summaries and human-readable reports.

## Features
- Auto-detection of metric types (binary, continuous, count, categorical).
- Appropriate statistical test selection based on data distribution and variant count.
- Pre-analysis validation: sample ratio mismatch, data integrity, covariate balance, temporal stability, outlier detection, power/MDE adequacy.
- Multiple testing correction (Bonferroni, Holm, BH-FDR) across all metrics in each experiment.
- Effect size calculations and confidence interval estimation.
- Visualization of results (distribution plots, bar charts).
- Batch runner for all datasets with consolidated CSV + markdown reports.
- Public-dataset cleaning mode (removes assignment mismatches, deduplicates users).

## Project Structure
```
├── data/                     # Datasets (internal + external)
│   └── external/             # Kaggle benchmark datasets
├── docs/                     # Human-readable reports
│   ├── BATCH_ANALYSIS_REPORT.md
│   └── PROJECT_REPORT.md
├── reports/                  # Machine-readable outputs
│   ├── figures/              # Distribution + bar chart PNGs
│   ├── statistical_results/  # Per-dataset CSVs, batch_summary.csv
│   └── validation_reports/   # Per-dataset validation reports
├── scripts/                  # Analysis and automation scripts
│   ├── statistical_analysis.py   # Core statistical engine
│   ├── validation.py             # Pre-analysis validation
│   ├── run_pipeline.py           # Single-dataset pipeline
│   └── run_batch_analysis.py     # Batch runner (all datasets)
└── README.md
```

## Getting Started

### Prerequisites
- Python 3.8+
- Required libraries: `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`

Install dependencies:
```bash
pip install -r requirements.txt
```

### Run a single dataset
```bash
python scripts/run_pipeline.py data/test1_menu.csv added_to_cart
```

### Run all datasets (recommended)
```bash
python scripts/run_batch_analysis.py
```
Outputs: `reports/statistical_results/batch_summary.csv`, `reports/statistical_results/batch_all_metrics.csv`, `docs/BATCH_ANALYSIS_REPORT.md`

---

## Portfolio Story

Each experiment below follows the format: **Problem → Method → Result → Recommendation**.

---

### Experiment 1 — Menu Navigation (`test1_menu.csv`)

**Problem:** The product team redesigned the site navigation from a horizontal menu to a collapsible dropdown. They wanted to know whether this change helped or hurt user purchasing behaviour.

**Method:** Two-proportion Z-test on `added_to_cart` rate (binary conversion metric), with Holm-corrected secondary analysis on `pages_viewed`, `bounced`, and `revenue`. Pre-analysis validation confirmed no sample ratio mismatch and adequate sample size.

**Result:** Highly significant negative impact. Control (horizontal menu) achieved a ~96% add-to-cart rate vs. ~86% for the treatment dropdown (p ≈ 8.4 × 10⁻⁴⁹). Effect confirmed across all secondary metrics under multiple-testing correction.

**Recommendation:** Do not ship the dropdown. Revert to the horizontal menu immediately. The ~10 percentage-point drop in add-to-cart rate represents a material revenue risk at production traffic volumes.

---

### Experiment 2 — Novelty Slider (`test2_novelty_slider.csv`)

**Problem:** The recommendations team built a new personalized novelty product slider. The hypothesis was that algorithmic curation would drive more new-product discovery than the manually curated slider.

**Method:** Two-proportion Z-test on `products_added_from_novelties`. Secondary metrics: `is_registered`, `novelty_revenue`. Holm correction applied.

**Result:** Strongly significant positive lift. The personalized slider increased the novelty add-to-cart rate from ~0.15% (control) to ~0.58% (treatment), a 283% relative increase (p ≈ 7.7 × 10⁻⁶).

**Recommendation:** Ship the personalized novelty slider. The lift is statistically robust and economically meaningful. Monitor `novelty_revenue` post-launch to confirm the engagement translates to revenue.

---

### Experiment 3 — Product Sliders (`test3_product_sliders.csv`)

**Problem:** Three slider variants (A, B, C) were evaluated for their effect on revenue from product recommendations. With three variants, pairwise comparisons risk inflated false-discovery rates.

**Method:** Kruskal-Wallis test (non-parametric, appropriate for non-normal revenue distributions with 3+ variants), followed by pairwise Mann-Whitney tests with Bonferroni correction. Secondary metrics: `add_to_cart_rate`, `slider_interactions`, `products_per_order`, `avg_product_price`.

**Result:** All three pairwise comparisons were significant (p ≈ 5.1 × 10⁻⁵³). The variants produce meaningfully different revenue distributions.

**Recommendation:** Select the variant with the highest median `revenue_from_recommendations`. Run a two-arm follow-up between the top variant and control to obtain a clean A/B estimate before full rollout.

---

### Experiment 4 — Reviews (`test4_reviews.csv`)

**Problem:** The CRO team hypothesised that featuring product reviews prominently on the product page would increase conversion rate and add-to-cart rate.

**Method:** Two-proportion Z-test on `converted` (primary) and `added_to_cart` (secondary). Holm correction applied across both metrics.

**Result:** No statistically significant effect. Control: 10.67%, Treatment: 10.75%, p = 0.776. The effect size is negligible (< 0.1 pp absolute) and the sample was adequately powered for the target MDE.

**Recommendation:** Do not ship this feature in its current form. The null result is reliable given adequate power. Consider qualitative user research to understand whether review presentation is even a decision factor before designing a follow-up experiment.

---

### Experiment 5 — Search Engine (`test5_search_engine.csv`)

**Problem:** The engineering team evaluated replacing the existing Hybris search engine with Algolia. The hypothesis was that better relevance would drive higher conversion.

**Method:** Two-proportion Z-test on `converted` (primary). Secondary metrics: `added_to_cart`, `interacted_with_search`, `avg_revenue_per_visitor`. Holm correction applied.

**Result:** No statistically significant effect on primary conversion (p = 0.371, control: 6.62%, treatment: 6.95%). The ~0.3 pp difference is within noise.

**Recommendation:** Do not use conversion rate alone as the decision signal for a search infrastructure change. `interacted_with_search` and `avg_revenue_per_visitor` should be the primary guardrail metrics, since search quality affects the full funnel, not just end-of-session conversion. Consider a longer experiment window and session-level segmentation.

---

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgments
- Kaggle for the public benchmark dataset used to validate the pipeline methodology.
- Python scientific community for open-source libraries: pandas, numpy, scipy, statsmodels, matplotlib, seaborn.
