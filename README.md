# A/B Testing Analysis Project

![Status](https://img.shields.io/badge/status-validation_complete-green)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![Stage](https://img.shields.io/badge/stage-2%2F8-orange)

## 📊 Project Overview

Comprehensive statistical analysis of 5 A/B tests conducted on an e-commerce platform to determine which product variants should be implemented.

**Total Dataset Size:** 102,000 sessions  
**Test Period:** March - June 2021  
**Geographic Market:** Croatian e-commerce (Zagreb, Split, Rijeka, Osijek)  
**Current Status:** Stage 2 Complete - Data Validation ✅

---

## 🎯 Tests Analyzed

1. **Menu Navigation** (7K sessions) - Horizontal vs Dropdown Menu
2. **Novelty Slider** (16K sessions) - Manual vs Personalized Recommendations  
3. **Product Sliders** (18K sessions) - Social Proof Variations
4. **Reviews** (42K sessions) - Featured vs No Featured Reviews  
5. **Search Engine** (19K sessions) - Hybris vs Algolia Search

---

## 📁 Project Structure

```
dec-ab-testing-project/
├── data/                      # Raw CSV datasets (5 files)
├── scripts/                   # Python modules
│   ├── validation.py         # Data validation suite
│   ├── statistical_tests.py  # Statistical testing (TBD)
│   ├── visualization.py      # Plotting functions (TBD)
│   └── utils.py              # Helper functions
├── notebooks/                 # Analysis notebooks
│   └── run_validation.py     # Stage 1 & 2 validation
├── reports/                   # Generated reports
│   └── validation_reports/   # Validation results
├── figures/                   # Saved visualizations
├── PROJECT_SETUP.md          # Detailed project documentation
├── STAGE_1_2_SUMMARY.md      # Validation results summary
└── requirements.txt          # Python dependencies
```

---

## 🚀 Quick Start

### Installation
```powershell
pip install -r requirements.txt
```

### Run Validation (Stages 1 & 2)
```powershell
python notebooks/run_validation.py
```

View reports in `reports/validation_reports/`

---

## 📈 Current Status

- ✅ **Stage 0:** Project Setup - COMPLETE
- ✅ **Stage 1:** Data Loading & Inspection - COMPLETE  
- ✅ **Stage 2:** Data Validation - COMPLETE
- ⏳ **Stage 3:** Exploratory Data Analysis - PENDING
- ⏳ **Stage 4:** Statistical Testing - PENDING
- ⏳ **Stage 5:** Segmentation Analysis - PENDING
- ⏳ **Stage 6:** Business Impact - PENDING
- ⏳ **Stage 7:** Reporting - PENDING

---

## ✅ Validation Results

All 5 tests passed critical validation checks:
- ✅ No Sample Ratio Mismatch  
- ✅ Balanced Randomization
- ✅ Temporal Consistency
- ⚠️ Minor data quality issues (duplicate sessions)

See [STAGE_1_2_SUMMARY.md](STAGE_1_2_SUMMARY.md) for detailed results.

---

## 📚 Key Files

- **PROJECT_SETUP.md** - Complete methodology and project plan
- **STAGE_1_2_SUMMARY.md** - Validation results and findings
- **requirements.txt** - Python package dependencies
- **scripts/validation.py** - Comprehensive validation framework

---

## 🛠️ Technology Stack

- **Python 3.8+**
- **pandas** - Data manipulation
- **scipy** - Statistical tests  
- **matplotlib/seaborn** - Visualizations
- **statsmodels** - Advanced modeling

---

## 📖 Documentation

Full project methodology and analysis plan available in [PROJECT_SETUP.md](PROJECT_SETUP.md).

---

**Last Updated:** February 4, 2026  
**Current Stage:** 2 of 8 complete
