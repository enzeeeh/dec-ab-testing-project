# A/B Testing Analysis Project

![Status](https://img.shields.io/badge/status-analysis_complete-brightgreen)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![Tests](https://img.shields.io/badge/tests-5-blue)

## 📊 Project Overview

Complete statistical analysis of **5 A/B tests** on an e-commerce platform (102,000+ sessions, March-June 2021).

**Status:** ✅ Analysis Complete | 🎯 Results Ready for Business Decisions

## 🎯 Key Results

| Test | Winner | Key Finding |
|------|--------|-------------|
| Menu Navigation | **Variant A** ✅ | Horizontal menu: 10% higher add-to-cart |
| Novelty Slider | **Variant B** ✅ | Personalized: 283% more products added |
| Product Sliders | **See Details** | 3 significant metrics, review pairwise |
| Reviews | **No Effect** | Featured reviews show no impact |
| Search Engine | **Variant B** | Algolia: 1.5% add-to-cart increase |

## ✅ Analysis Summary

**Validation:** All tests passed critical checks (SRM, balance, temporal stability)  
**Statistical Tests:** Automatic selection based on metric type  
**Correction:** Holm-Bonferroni applied for multiple testing  
**Significant Findings:** 8 of 18 metrics significant after correction

## 📁 Project Structure

```
dec-ab-testing-project/
├── data/                          # 5 test CSV files
├── scripts/                       # Python modules
│   ├── validation.py             # Data validation framework
│   ├── statistical_analysis.py   # Statistical testing framework  
│   ├── run_validation.py         # Validation runner
│   ├── run_statistical_tests.py  # Statistical testing runner
│   └── utils.py                  # Helper functions
├── reports/
│   ├── validation_reports/       # Validation results
│   └── statistical_results/      # Statistical test results
├── docs/                         # Documentation
│   ├── AB_Testing_Methodology.md # Complete methodology & formulas
│   ├── VALIDATION_SUMMARY.md    # Validation summary
│   └── STATISTICAL_RESULTS.md   # Statistical findings
├── notebooks/                    # Jupyter notebooks
│   └── AB_Testing_Methodology_and_Formulas.ipynb
├── EXECUTIVE_SUMMARY.md          # Business-ready executive summary
└── requirements.txt
```

## 🚀 Quick Start

### Installation
```bash
pip install -r requirements.txt
```

### Run Complete Analysis
```bash
# Step 1: Validate data quality
python scripts/run_validation.py

# Step 2: Run statistical tests
python scripts/run_statistical_tests.py
```

## 📊 Reports & Documentation

### Executive Documentation
- **[EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md)** - Complete business summary with actionable recommendations and implementation roadmap
- **[docs/AB_Testing_Methodology.md](docs/AB_Testing_Methodology.md)** - Full methodology with mathematical formulas, decision trees, and test selection logic (GitHub-optimized Markdown)

### Methodology Notebook
- **[notebooks/AB_Testing_Methodology_and_Formulas.ipynb](notebooks/AB_Testing_Methodology_and_Formulas.ipynb)** - Interactive Jupyter notebook containing:
  - Complete validation framework with SRM and balance checks
  - Statistical testing methods (Two-Proportion Z-Test, Mann-Whitney U, Kruskal-Wallis H)
  - LaTeX formulas for all statistical procedures
  - Test selection decision tree with automation logic
  - Multiple testing correction (Holm-Bonferroni) algorithm
  - Comprehensive results tables for all 5 tests
  - Business recommendations with confidence levels

### Validation Reports
`reports/validation_reports/`:
- All 5 tests passed validation ✅
- No SRM detected, balanced randomization
- See [docs/VALIDATION_SUMMARY.md](docs/VALIDATION_SUMMARY.md)

### Statistical Results
`reports/statistical_results/`:
- 8 of 18 metrics significant
- Holm-Bonferroni correction applied
- See [docs/STATISTICAL_RESULTS.md](docs/STATISTICAL_RESULTS.md)

## 🔧 Requirements

- Python 3.8+
- See `requirements.txt` for dependencies

---

**Last Updated:** February 7, 2026
