# A/B Testing Analysis Project

![Status](https://img.shields.io/badge/status-validation_complete-green)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![Tests](https://img.shields.io/badge/tests-5-blue)

## 📊 Project Overview

Statistical analysis of **5 A/B tests** on an e-commerce platform covering 102,000+ sessions (March - June 2021).

## 🎯 Tests Analyzed

| Test | Sessions | Key Comparison | Metric |
|------|----------|-----------------|--------|
| Menu Navigation | 7,000 | Horizontal vs Dropdown | Revenue/Bounce |
| Novelty Slider | 16,000 | Manual vs Personalized | Registration |
| Product Sliders | 18,000 | 3-way Social Proof | Add-to-Cart |
| Reviews | 42,000 | Featured vs No-Featured | Conversion |
| Search Engine | 19,000 | Hybris vs Algolia | Revenue |

## ✅ Validation Results Summary

**Critical Checks:** All PASS ✅
- Sample Ratio Mismatch (SRM): All balanced
- Randomization Balance: Excellent (max SMD=0.039)
- Temporal Stability: Stable (max CV=0.057)

**Test Status:**
- ✅ **Novelty Slider Test** - Ready for analysis
- ✅ **Product Sliders Test** - Ready for analysis
- ✅ **Search Engine Test** - Ready for analysis
- ⚠️ **Menu Navigation Test** - Underpowered (6.8% MDE)
- ⚠️ **Reviews Test** - High outliers (17.1%)

## 📁 Project Structure

```
dec-ab-testing-project/
├── data/                          # 5 test CSV files
├── scripts/                       # Python modules
│   ├── validation.py             # Data validation framework
│   ├── run_validation.py         # Validation runner
│   └── utils.py                  # Helper functions
├── reports/validation_reports/   # Validation results
├── docs/                         # Documentation
└── requirements.txt
```

## 🚀 Quick Start

### Installation
```bash
pip install -r requirements.txt
```

### Run Validation
```bash
python scripts/run_validation.py
```

Generates reports in `reports/validation_reports/`:
- Individual test reports (5 files)
- Summary validation report

## 📊 Reports Location

`reports/validation_reports/`:
- `validation_summary.txt` - Overview of all tests
- `test1_menu_validation_report.txt`
- `test2_novelty_slider_validation_report.txt`
- `test3_product_sliders_validation_report.txt`
- `test4_reviews_validation_report.txt`
- `test5_search_engine_validation_report.txt`

## 🔧 Requirements

- Python 3.8+
- See `requirements.txt` for dependencies

---

**Last Updated:** February 7, 2026
