# A/B Testing Analysis - Complete Methodology and Formulas

## Executive Summary Documentation

**Project:** E-Commerce A/B Testing Analysis  
**Period:** March - June 2021  
**Tests Analyzed:** 5  
**Total Sessions:** 102,000+  
**Last Updated:** May 2026

---

This document provides all statistical methods, formulas, and decision criteria used in the complete A/B testing analysis.

---

## Table of Contents

1. [Validation Framework](#1-validation-framework)
2. [Statistical Testing Methods](#2-statistical-testing-methods)
3. [Test Selection Decision Tree](#3-test-selection-decision-tree)
4. [Multiple Testing Correction](#4-multiple-testing-correction)
5. [Results Summary](#5-results-summary)
6. [Business Recommendations](#6-business-recommendations)
7. [Methodology Summary](#7-methodology-summary)

---

## Enhanced A/B Testing Methodology

### Overview
A/B testing is a statistical method used to compare two or more variants of a feature to determine which performs better based on a specific metric.

### Key Concepts
1. **Variants**: Different versions being tested (e.g., A = control, B = treatment).
2. **Metrics**: Measurable outcomes (e.g., conversion rate, revenue).
3. **Randomization**: Assigning users randomly to variants to avoid bias.
4. **Statistical Testing**: Using statistical methods to determine if observed differences are significant.
5. **Effect Size**: Measuring the magnitude of the difference (e.g., relative lift, Cohen's d).
6. **Multiple Testing Correction**: Adjusting for false positives when testing multiple hypotheses.

### Workflow
1. **Define the Objective**:
   - Identify the goal of the test (e.g., increase sign-ups).
   - Define the primary metric (e.g., conversion rate).

2. **Design the Experiment**:
   - Formulate a hypothesis.
   - Calculate the required sample size.
   - Ensure randomization.

3. **Collect Data**:
   - Use tools like Google Analytics or custom tracking scripts.

4. **Analyze Results**:
   - Use statistical tests (e.g., t-test, chi-square).
   - Correct for multiple comparisons.

5. **Interpret Results**:
   - Assess statistical and practical significance.

6. **Take Action**:
   - Implement the winning variant.

### Statistical Methods
- **Two-Proportion Z-Test**: For binary metrics.
- **Welch's t-test**: For continuous metrics with unequal variances.
- **Mann-Whitney U Test**: For skewed continuous metrics.
- **Chi-Square Test**: For categorical outcomes.

### Visualization
- Use distribution plots and bar charts to interpret results visually.

### Example Workflow
1. Load the dataset using `run_pipeline.py`.
2. Perform statistical analysis.
3. Generate visualizations.
4. Save results and interpret findings.

### Public Dataset
For practice, use Kaggle's "AB Testing Dataset" ([link](https://www.kaggle.com/datasets/)).

---

# 1. Validation Framework

Before running statistical tests, all experiments were validated using 7 critical checks:

## 1.1 Sample Ratio Mismatch (SRM) Test

**Purpose:** Detect allocation bias in randomization

**Formula:** Chi-square test for goodness of fit

$$\chi^2 = \sum_{i=1}^{k} \frac{(O_i - E_i)^2}{E_i}$$

Where:
- $O_i$ = Observed count in variant $i$
- $E_i$ = Expected count in variant $i$ (total × expected ratio)
- $k$ = Number of variants

**Decision Rule:**
- If $p < 0.001$: SRM detected → **INVALIDATE TEST**
- If $p \geq 0.001$: No SRM → proceed

**Our Results:** All 5 tests passed (p = 1.0 for perfect 50/50 splits)

## 1.2 Covariate Balance Check

**Purpose:** Verify randomization balanced demographic variables

**Formula:** Standardized Mean Difference (SMD)

$$SMD = \frac{\bar{x}_A - \bar{x}_B}{\sqrt{\frac{s_A^2 + s_B^2}{2}}}$$

Where:
- $\bar{x}_A, \bar{x}_B$ = Mean of covariate in variants A and B
- $s_A, s_B$ = Standard deviations

**Decision Rule:**
- If $|SMD| < 0.1$: Excellent balance
- If $0.1 \leq |SMD| < 0.2$: Acceptable balance  
- If $|SMD| \geq 0.2$: **WARNING** - Imbalance detected

**Our Results:** Max SMD = 0.039 < 0.1 (Excellent balance on all demographics)

---

# 2. Statistical Testing Methods

After validation, appropriate statistical tests were selected based on metric type and data distribution.

## 2.1 Two-Proportion Z-Test (Binary Metrics)

**Used for:** Conversion rates, click-through rates, bounce rates

**Formula:** 

$$Z = \frac{p_B - p_A}{\sqrt{\hat{p}(1-\hat{p})\left(\frac{1}{n_A} + \frac{1}{n_B}\right)}}$$

Where:
- $p_A = \frac{x_A}{n_A}$, $p_B = \frac{x_B}{n_B}$ = Sample proportions
- $\hat{p} = \frac{x_A + x_B}{n_A + n_B}$ = Pooled proportion
- $n_A, n_B$ = Sample sizes

**95% Confidence Interval:**

$$CI = (p_B - p_A) \pm 1.96 \times SE$$

Where $SE = \sqrt{\hat{p}(1-\hat{p})\left(\frac{1}{n_A} + \frac{1}{n_B}\right)}$

**Effect Size:** Relative lift = $\frac{p_B - p_A}{p_A} \times 100\%$

**Applied to:**
- Menu: added_to_cart, bounced
- Novelty Slider: is_registered, products_added  
- Reviews: converted, added_to_cart
- Search Engine: converted, added_to_cart, interacted_with_search

## 2.2 Mann-Whitney U Test (Skewed Continuous Metrics)

**Used for:** Revenue, time-on-site (when data is skewed or has outliers)

**Formula:**

$$U_A = n_A n_B + \frac{n_A(n_A + 1)}{2} - R_A$$

Where:
- $R_A$ = Sum of ranks for group A
- $n_A, n_B$ = Sample sizes
- Test statistic: $U = \min(U_A, U_B)$

**P-value:** Compare U to Mann-Whitney distribution or use normal approximation for large samples:

$$Z = \frac{U - \frac{n_A n_B}{2}}{\sqrt{\frac{n_A n_B (n_A + n_B + 1)}{12}}}$$

**Effect Size:** Rank-biserial correlation

$$r = 1 - \frac{2U}{n_A n_B}$$

Interpretation:
- $|r| < 0.1$: Negligible
- $0.1 \leq |r| < 0.3$: Small  
- $0.3 \leq |r| < 0.5$: Medium
- $|r| \geq 0.5$: Large

**Applied to:**
- Menu: revenue, pages_viewed
- Novelty Slider: novelty_revenue
- Search Engine: avg_revenue_per_visitor

## 2.3 Kruskal-Wallis H-Test (3+ Variants)

**Used for:** Comparing 3+ variants on continuous metrics (non-parametric)

**Formula:**

$$H = \frac{12}{N(N+1)} \sum_{i=1}^{k} \frac{R_i^2}{n_i} - 3(N+1)$$

Where:
- $k$ = Number of groups
- $N$ = Total sample size
- $R_i$ = Sum of ranks in group $i$
- $n_i$ = Sample size of group $i$

**P-value:** Compare H to chi-square distribution with $df = k-1$

**Post-hoc:** Pairwise Mann-Whitney U tests with Holm-Bonferroni correction

**Applied to:**
- Product Sliders (3 variants):
  - revenue_from_recommendations
  - slider_interactions  
  - products_per_order
  - avg_product_price

---

# 3. Test Selection Decision Tree

```
START
  │
  ├─ Is metric BINARY (0/1)?  
  │   ├─ YES → Are there 2 variants?
  │   │   ├─ YES → TWO-PROPORTION Z-TEST
  │   │   └─ NO (3+) → CHI-SQUARE TEST
  │   │
  │   └─ NO → Is metric CONTINUOUS?
  │       ├─ YES → Check normality & skewness
  │       │   ├─ Normal & |skew| < 1 → Are there 2 variants?
  │       │   │   ├─ YES → WELCH'S T-TEST
  │       │   │   └─ NO (3+) → ANOVA
  │       │   │  
  │       │   └─ Skewed OR outliers → Are there 2 variants?
  │       │       ├─ YES → MANN-WHITNEY U TEST
  │       │       └─ NO (3+) → KRUSKAL-WALLIS H-TEST
  │       │
  │       └─ NO → Is metric CATEGORICAL?
  │           └─ YES → CHI-SQUARE TEST
```

**Normality Tests Used:**
- Small samples (n < 5000): Shapiro-Wilk test
- Large samples (n ≥ 5000): Anderson-Darling test
- Additionally check: |Skewness| < 2

**Our Implementation:** Fully automated test selection in [scripts/statistical_analysis.py](../scripts/statistical_analysis.py)

---

# 4. Multiple Testing Correction

When testing multiple metrics within the same experiment, we apply Holm-Bonferroni correction to control family-wise error rate (FWER).

## 4.1 Holm-Bonferroni Method

**Algorithm:**
1. Sort p-values in ascending order: $p_{(1)} \leq p_{(2)} \leq ... \leq p_{(m)}$
2. For each $i = 1, 2, ..., m$:
   - Compare $p_{(i)}$ to $\frac{\alpha}{m - i + 1}$
   - If $p_{(i)} \leq \frac{\alpha}{m - i + 1}$: Reject $H_{0(i)}$ and continue
   - Else: Stop and fail to reject remaining hypotheses

**Example:** Test 1 (Menu Navigation) with 4 metrics, α = 0.05

| Metric | Original p-value | Rank | Threshold | Decision |
|--------|-----------------|------|-----------|----------|
| revenue | 0.0000 | 1 | 0.05/4 = 0.0125 | ✅ Reject (significant) |
| added_to_cart | 0.0000 | 2 | 0.05/3 = 0.0167 | ✅ Reject (significant) |
| pages_viewed | 0.0675 | 3 | 0.05/2 = 0.0250 | ❌ Fail to reject |
| bounced | 0.3354 | 4 | 0.05/1 = 0.0500 | ❌ Fail to reject |

**Result:** 2 of 4 metrics remain significant after correction

---

# 5. Results Summary

## 5.1 Overall Statistics

| Metric | Value |
|--------|-------|
| Total Tests Analyzed | 5 |
| Total Sessions | 102,000 |
| Total Metrics Tested | 18 |
| Significant (Before Correction) | 8 |
| Significant (After Correction) | 8 |
| FWER Control Method | Holm-Bonferroni |

## 5.2 Test Results

### Test 1: Menu Navigation (Horizontal vs Dropdown)

| Metric | Test Used | p-value | Significant | Effect |
|--------|-----------|---------|-------------|--------|
| revenue | Mann-Whitney U | <0.001 | ✅ YES | Dropdown **lower** (r=-0.077) |
| added_to_cart | Z-Test | <0.001 | ✅ YES | Dropdown **-10.34%** |
| pages_viewed | Mann-Whitney U | 0.0675 | ❌ NO | - |
| bounced | Z-Test | 0.3354 | ❌ NO | - |

**Decision:** Keep Horizontal Menu (A)

### Test 2: Novelty Slider (Manual vs Personalized)

| Metric | Test Used | p-value | Significant | Effect |
|--------|-----------|---------|-------------|--------|
| novelty_revenue | Mann-Whitney U | <0.001 | ✅ YES | Personalized **higher** (r=0.050) |
| products_added | Z-Test | <0.001 | ✅ YES | Personalized **+283%** |
| is_registered | Z-Test | 0.8988 | ❌ NO | - |

**Decision:** Deploy Personalized Novelties (B) ✅

### Test 3: Product Sliders (3 Variants)

| Metric | Test Used | p-value | Significant |
|--------|-----------|---------|-------------|
| revenue_from_recommendations | Kruskal-Wallis | <0.001 | ✅ YES |
| products_per_order | Kruskal-Wallis | <0.001 | ✅ YES |
| avg_product_price | Kruskal-Wallis | <0.001 | ✅ YES |
| add_to_cart_rate | Chi-Square | 0.9888 | ❌ NO |
| slider_interactions | Kruskal-Wallis | 0.1622 | ❌ NO |

**Decision:** Review pairwise comparisons in detailed report

### Test 4: Reviews (No Featured vs Featured)

| Metric | Test Used | p-value | Significant |
|--------|-----------|---------|-------------|
| converted | Z-Test | 0.7764 | ❌ NO |
| added_to_cart | Z-Test | 0.2332 | ❌ NO |

**Decision:** No Effect - Skip Implementation

### Test 5: Search Engine (Hybris vs Algolia)

| Metric | Test Used | p-value | Significant | Effect |
|--------|-----------|---------|-------------|--------|
| added_to_cart | Z-Test | 0.0014 | ✅ YES | Algolia **+1.51%** |
| avg_revenue_per_visitor | Mann-Whitney U | 0.3461 | ❌ NO | - |
| converted | Z-Test | 0.3712 | ❌ NO | - |
| interacted_with_search | Z-Test | 0.4551 | ❌ NO | - |

**Decision:** Small improvement - Consider cost-benefit analysis

---

# 6. Business Recommendations

## Immediate Actions ✅

### 1. Deploy Personalized Novelties (Test 2 - Variant B)

- **Statistical Evidence:** p < 0.001 for both revenue and product additions
- **Business Impact:** 283% increase in products added from novelty section
- **Confidence:** High - robust effect across multiple metrics
- **Action:** Implement immediately

### 2. Keep Horizontal Menu (Test 1 - Variant A)

- **Statistical Evidence:** p < 0.001 for revenue and add-to-cart
- **Business Impact:** Dropdown menu decreases add-to-cart by 10.34%
- **Confidence:** High - negative impact confirmed
- **Action:** Do not implement dropdown menu

## Further Analysis Required 📊

### 3. Product Sliders (Test 3)

- **Statistical Evidence:** 3 of 5 metrics significant (p < 0.001)
- **Business Impact:** Requires pairwise comparison review
- **Action:** Review detailed report for optimal variant selection

## Consider Cost-Benefit 💰

### 4. Algolia Search Engine (Test 5 - Variant B)

- **Statistical Evidence:** p = 0.0014 for add-to-cart only
- **Business Impact:** Small improvement (+1.51%)
- **Confidence:** Weak - only one metric significant
- **Action:** Conduct cost-benefit analysis before deployment

## Skip Implementation ❌

### 5. Featured Reviews (Test 4)

- **Statistical Evidence:** No significant differences (p > 0.2 for all metrics)
- **Business Impact:** Zero measurable effect
- **Action:** Do not implement - allocate resources elsewhere

---

# 7. Methodology Summary

## Framework Strengths

✅ **Rigorous Validation**  
- 7-step validation process before any statistical testing
- No SRM detected in any test
- Excellent randomization balance (max SMD = 0.039)

✅ **Appropriate Test Selection**  
- Automatic detection of metric type
- Distribution checking (normality, skewness)
- Robust non-parametric methods for skewed data

✅ **Multiple Testing Control**  
- Holm-Bonferroni correction applied
- Family-wise error rate controlled at α = 0.05
- No inflation of Type I error

✅ **Effect Size Reporting**  
- Not just statistical significance, but practical importance
- Cohen's d, rank-biserial r, relative lift calculated
- Confidence intervals provided

## Tools & Implementation

**Code Location:**
- [scripts/validation.py](../scripts/validation.py) - Validation framework
- [scripts/statistical_analysis.py](../scripts/statistical_analysis.py) - Statistical testing engine
- [scripts/run_pipeline.py](../scripts/run_pipeline.py) - Single-dataset pipeline (validation + inference + plots)
- [scripts/run_batch_analysis.py](../scripts/run_batch_analysis.py) - Batch runner (all datasets, multi-metric, MDE)

**Reports Generated:**
- [reports/validation_reports/](../reports/validation_reports/) - Per-dataset validation reports
- [reports/statistical_results/batch_summary.csv](../reports/statistical_results/batch_summary.csv) - Primary metric summary
- [reports/statistical_results/batch_all_metrics.csv](../reports/statistical_results/batch_all_metrics.csv) - All metrics with Holm correction
- [docs/BATCH_ANALYSIS_REPORT.md](BATCH_ANALYSIS_REPORT.md) - Human-readable batch report

## Analysis Complete ✅

**Date Completed:** May 2026  
**Pipeline:** Fully automated batch runner — one command processes all datasets  
**Status:** Complete — validation, multi-metric analysis, MDE/power reporting, and consolidated reports all operational

---

**For questions or clarifications, see:**
- [BATCH_ANALYSIS_REPORT.md](BATCH_ANALYSIS_REPORT.md) - Full per-metric results with Holm correction and MDE
- [PROJECT_REPORT.md](PROJECT_REPORT.md) - Pipeline architecture, Kaggle cleaning, interview talking points
- Individual validation reports in [reports/validation_reports/](../reports/validation_reports/)

---

*This methodology can be reused for future A/B tests with confidence in its statistical rigor and automation capabilities.*
