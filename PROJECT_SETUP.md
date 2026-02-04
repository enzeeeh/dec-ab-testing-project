# A/B Testing Analysis Project - Setup Documentation

## 📋 Project Overview

**Project Name:** E-Commerce A/B Testing Analysis  
**Start Date:** February 4, 2026  
**Objective:** Analyze 5 A/B tests to determine which product variants should be implemented

### Business Context
This project analyzes A/B test results from an e-commerce platform (Croatian market) to make data-driven decisions about UX improvements. Each test evaluates a different feature's impact on revenue, conversion, and engagement metrics.

---

## 🗂️ Project Structure

```
dec-ab-testing-project/
├── data/                           # Raw CSV datasets
│   ├── test1_menu.csv             (7,002 sessions)
│   ├── test2_novelty_slider.csv   (16,002 sessions)
│   ├── test3_product_sliders.csv  (18,002 sessions)
│   ├── test4_reviews.csv          (42,002 sessions)
│   └── test5_search_engine.csv    (19,002 sessions)
│
├── notebooks/                      # Jupyter analysis notebooks
│   ├── 01_data_loading.ipynb
│   ├── 02_validation.ipynb
│   ├── 03_eda.ipynb
│   ├── 04_statistical_tests.ipynb
│   ├── 05_segmentation.ipynb
│   └── 06_reporting.ipynb
│
├── scripts/                        # Python modules
│   ├── __init__.py
│   ├── data_loader.py             # Load and parse datasets
│   ├── validation.py              # Data validation functions
│   ├── statistical_tests.py       # Statistical testing suite
│   ├── visualization.py           # Plotting functions
│   ├── business_impact.py         # ROI calculations
│   └── utils.py                   # Helper functions
│
├── reports/                        # Output reports
│   ├── validation_reports/
│   ├── statistical_results/
│   └── executive_summaries/
│
├── figures/                        # Saved visualizations
│   ├── validation/
│   ├── eda/
│   ├── statistical/
│   └── final/
│
├── requirements.txt                # Python dependencies
├── PROJECT_SETUP.md               # This file
└── README.md                      # Project documentation
```

---

## 🎯 Test Descriptions

### Test 1: Menu Navigation
- **Period:** March 1-7, 2021 (7 days)
- **Sample Size:** 7,002 sessions
- **Variants:** A_horizontal_menu vs alternative
- **Primary Metric:** Revenue
- **Secondary Metrics:** Pages viewed, bounce rate, add-to-cart rate
- **Goal:** Improve navigation and engagement

### Test 2: Novelty Slider
- **Period:** March 9-21, 2021 (12 days)
- **Sample Size:** 16,002 sessions
- **Variants:** A_manual_novelties vs automated
- **Primary Metric:** Novelty revenue
- **Secondary Metrics:** Products added from novelties
- **Segmentation:** Registered vs guest users
- **Goal:** Increase product discovery revenue

### Test 3: Product Sliders
- **Period:** March 23 - April 5, 2021 (14 days)
- **Sample Size:** 18,002 sessions
- **Variants:** A_selected_by_others_only vs alternatives
- **Primary Metric:** Revenue from recommendations
- **Secondary Metrics:** Slider interactions, add-to-cart rate, basket size
- **Goal:** Boost recommendation engine performance

### Test 4: Reviews
- **Period:** April 8 - May 11, 2021 (34 days)
- **Sample Size:** 42,002 sessions (LARGEST)
- **Variants:** A_no_featured_reviews vs featured reviews
- **Primary Metric:** Conversion rate
- **Secondary Metrics:** Add-to-cart rate
- **Goal:** Increase conversion through social proof

### Test 5: Search Engine
- **Period:** June 11-17, 2021 (7 days)
- **Sample Size:** 19,002 sessions
- **Variants:** A_hybris_search vs alternative
- **Primary Metric:** Revenue per visitor
- **Secondary Metrics:** Conversion, search interaction rate
- **Goal:** Improve search functionality and revenue

---

## 📊 Analysis Workflow

### Stage 0: Project Setup ✅
- Create folder structure
- Install dependencies
- Configure environment
- Document project

### Stage 1: Data Loading & Initial Inspection
- Load all 5 CSV files
- Inspect data structure
- Calculate basic statistics
- Identify data types and metrics

### Stage 2: Data Validation & Quality Checks ⚠️ CRITICAL
- **Sample Ratio Mismatch (SRM) Test**
- **Data Integrity Checks**
- **Randomization Balance**
- **Invariant Metrics Validation**
- **Temporal Consistency**
- **Outlier Detection**
- **Sample Size Adequacy**

### Stage 3: Exploratory Data Analysis
- Summary statistics by variant
- Distribution visualizations
- Temporal patterns
- Preliminary insights

### Stage 4: Statistical Testing
- T-tests for continuous metrics
- Proportion tests for binary metrics
- Confidence intervals
- Effect size calculations
- Multiple testing correction

### Stage 5: Segmentation Analysis
- Device type analysis
- Regional breakdowns
- Browser comparisons
- Interaction effects

### Stage 6: Business Impact Calculation
- Revenue lift estimation
- ROI calculations
- Sensitivity analysis
- Implementation priorities

### Stage 7: Reporting & Recommendations
- Executive summaries
- Technical reports
- Visualization packages
- Implementation roadmap

### Stage 8: Final Deliverables
- Code documentation
- Knowledge transfer
- Archive and handoff

---

## 🔧 Technical Stack

### Core Libraries
- **pandas** - Data manipulation and analysis
- **numpy** - Numerical computations
- **scipy** - Statistical tests
- **statsmodels** - Advanced statistical modeling
- **pingouin** - Effect sizes and power analysis

### Visualization
- **matplotlib** - Base plotting
- **seaborn** - Statistical visualizations
- **plotly** - Interactive dashboards

### Environment
- **Python 3.8+**
- **Jupyter Notebook** - Interactive analysis
- **PowerShell** - Terminal operations (Windows)

---

## 📈 Key Metrics Dictionary

### Common Across Tests
- `session_id` - Unique session identifier
- `user_id` - User identifier
- `timestamp` - Session date
- `device_type` - mobile/desktop/tablet
- `browser` - Chrome/Safari/Firefox/Edge
- `region` - Zagreb/Split/Rijeka/Osijek/Other
- `variant` - A (control) or B (treatment)

### Test-Specific Metrics

**Test 1 (Menu):**
- `pages_viewed` - Number of pages in session
- `added_to_cart` - Binary (0/1)
- `bounced` - Binary (0/1)
- `revenue` - Revenue generated

**Test 2 (Novelty Slider):**
- `is_registered` - User registration status
- `novelty_revenue` - Revenue from novelty items
- `products_added_from_novelties` - Count

**Test 3 (Product Sliders):**
- `add_to_cart_rate` - Rate metric
- `slider_interactions` - Number of interactions
- `revenue_from_recommendations` - Revenue
- `products_per_order` - Basket size
- `avg_product_price` - Average price

**Test 4 (Reviews):**
- `converted` - Binary (0/1)
- `added_to_cart` - Binary (0/1)

**Test 5 (Search Engine):**
- `avg_revenue_per_visitor` - Revenue metric
- `added_to_cart` - Binary (0/1)
- `converted` - Binary (0/1)
- `interacted_with_search` - Binary (0/1)

---

## ⚠️ Critical Validation Checks

### Must-Pass Criteria
1. **No Sample Ratio Mismatch** (p > 0.05)
2. **No duplicate sessions**
3. **All dates within test period**
4. **Balanced randomization** across demographics
5. **Stable variant split** over time
6. **Adequate sample size** for 80% power

### If Validation Fails
- Document the issue
- Investigate root cause
- Determine if test can be salvaged
- Consider excluding problematic data
- May need to invalidate entire test

---

## 📝 Success Criteria

This project is successful when we can answer for each test:

✅ Was the test properly conducted?  
✅ Is the data trustworthy?  
✅ Which variant performed better?  
✅ Is the difference statistically significant?  
✅ Is the difference practically meaningful?  
✅ What's the expected business impact?  
✅ Should we implement the change?  
✅ For which user segments?

---

## 🚀 Implementation Priority Framework

Tests will be ranked by:
1. **Statistical Significance** (p-value)
2. **Effect Size** (Cohen's d)
3. **Business Impact** (revenue lift)
4. **Implementation Difficulty** (dev effort)
5. **Risk Level** (confidence in results)

---

## 📞 Contact & Documentation

**Analyst:** [Your Name]  
**Start Date:** February 4, 2026  
**Status:** In Progress - Stage 2 (Validation)  
**Last Updated:** February 4, 2026

---

## 🔄 Version History

- **v1.0** (Feb 4, 2026) - Initial project setup and structure
- **v1.1** (Feb 4, 2026) - Completed data validation (Stage 2)

---

## 📚 References

- Statistical testing methodology: scipy.stats documentation
- A/B testing best practices: Trustworthy Online Controlled Experiments
- Effect size interpretation: Cohen's Statistical Power Analysis
- Multiple testing correction: Benjamini-Hochberg procedure
