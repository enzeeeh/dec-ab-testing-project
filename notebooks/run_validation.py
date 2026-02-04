"""
Stage 1 & 2: Data Loading, Initial Inspection, and Validation (Console-Safe Version)

This script performs:
- Stage 1: Load all 5 datasets and perform initial inspection
- Stage 2: Comprehensive data validation and quality checks
"""

import sys
import os
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# Configure output encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add scripts directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from utils import load_test_data, get_test_info
from validation import ABTestValidator


def print_test_summary_safe(test_name: str, df: pd.DataFrame):
    """Print test summary without emojis."""
    info = get_test_info(df)
    
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"{'='*60}")
    print(f"Total Sessions: {info['total_sessions']:,}")
    print(f"Unique Users: {info['unique_users']:,}")
    
    if info['date_range']:
        print(f"Date Range: {info['date_range'][0].date()} to {info['date_range'][1].date()}")
        print(f"Duration: {info['test_duration_days']} days")
    
    print(f"\nVariants:")
    for variant, count in info['variant_counts'].items():
        pct = count / info['total_sessions'] * 100
        print(f"  {variant}: {count:,} ({pct:.2f}%)")
    
    print(f"\nAvailable Metrics:")
    metrics = [col for col in info['columns'] if col not in 
               ['session_id', 'user_id', 'timestamp', 'device_type', 'browser', 'region', 'variant']]
    for metric in metrics:
        print(f"  - {metric}")
    
    print(f"{'='*60}\n")


def save_validation_report_safe(validation_results: dict, test_name: str, output_path: str):
    """Save validation results to file (emoji-safe)."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"VALIDATION REPORT: {test_name}\n")
        f.write(f"{'='*70}\n\n")
        
        for check, results in validation_results.items():
            f.write(f"{check.replace('_', ' ').upper()}\n")
            f.write(f"{'-'*70}\n")
            f.write(f"Status: {results.get('status', 'N/A')}\n")
            f.write(f"Message: {results.get('message', 'N/A')}\n")
            f.write(f"Passed: {results.get('passed', 'N/A')}\n\n")
        
        f.write(f"{'='*70}\n")
        f.write(f"Report generated: {pd.Timestamp.now()}\n")
    
    print(f"[OK] Validation report saved to: {output_path}")


def main():
    """Main execution function for Stages 1 and 2."""
    
    # Define paths
    data_dir = r"d:\Enzi-Folder\personal-project\dec-ab-testing-project\data"
    reports_dir = r"d:\Enzi-Folder\personal-project\dec-ab-testing-project\reports\validation_reports"
    
    # Test configurations
    tests = {
        'test1_menu': {
            'file': 'test1_menu.csv',
            'name': 'Menu Navigation Test',
            'description': 'Horizontal vs Vertical Menu'
        },
        'test2_novelty_slider': {
            'file': 'test2_novelty_slider.csv',
            'name': 'Novelty Slider Test',
            'description': 'Manual vs Automated Novelties'
        },
        'test3_product_sliders': {
            'file': 'test3_product_sliders.csv',
            'name': 'Product Sliders Test',
            'description': 'Social Proof Recommendations'
        },
        'test4_reviews': {
            'file': 'test4_reviews.csv',
            'name': 'Reviews Test',
            'description': 'No Featured vs Featured Reviews'
        },
        'test5_search_engine': {
            'file': 'test5_search_engine.csv',
            'name': 'Search Engine Test',
            'description': 'Hybris vs Alternative Search'
        }
    }
    
    print("\n" + "="*80)
    print("A/B TESTING ANALYSIS - STAGES 1 & 2")
    print("Stage 1: Data Loading & Initial Inspection")
    print("Stage 2: Data Validation & Quality Checks")
    print("="*80)
    
    # Store all validation results
    all_validation_results = {}
    all_dataframes = {}
    
    # ========================================================================
    # STAGE 1: DATA LOADING & INITIAL INSPECTION
    # ========================================================================
    
    print("\n" + "#"*80)
    print("# STAGE 1: DATA LOADING & INITIAL INSPECTION")
    print("#"*80)
    
    for test_id, test_config in tests.items():
        file_path = os.path.join(data_dir, test_config['file'])
        
        print(f"\nLoading: {test_config['name']}")
        print(f"File: {test_config['file']}")
        
        # Load data
        df = load_test_data(file_path)
        all_dataframes[test_id] = df
        
        # Print summary
        print_test_summary_safe(test_config['name'], df)
        
        # Quick peek at data
        print(f"Sample rows:")
        print(df.head(3).to_string())
        print()
    
    # ========================================================================
    # STAGE 2: DATA VALIDATION & QUALITY CHECKS
    # ========================================================================
    
    print("\n" + "#"*80)
    print("# STAGE 2: DATA VALIDATION & QUALITY CHECKS")
    print("#"*80)
    print("\n[INFO] Running validation checks... (output saved to files)")
    print("[INFO] This may take a few moments...\n")
    
    for test_id, test_config in tests.items():
        df = all_dataframes[test_id]
        
        print(f"Processing: {test_config['name']}...")
        
        # Create validator
        validator = ABTestValidator(df, test_config['name'])
        
        # Run all validations (output to file)
        validation_results = validator.run_all_validations()
        
        # Store results
        all_validation_results[test_id] = validation_results
        
        # Save individual report
        report_path = os.path.join(reports_dir, f"{test_id}_validation_report.txt")
        save_validation_report_safe(validation_results, test_config['name'], report_path)
        
        # Print brief status
        overall = validation_results.get('overall', {})
        print(f"  Status: {overall.get('status', 'UNKNOWN')}")
        print()
    
    # ========================================================================
    # SUMMARY OF ALL TESTS
    # ========================================================================
    
    print("\n" + "#"*80)
    print("# VALIDATION SUMMARY - ALL TESTS")
    print("#"*80 + "\n")
    
    summary_data = []
    
    for test_id, test_config in tests.items():
        results = all_validation_results[test_id]
        overall = results.get('overall', {})
        
        srm_pass = 'PASS' if results.get('srm', {}).get('passed', False) else 'FAIL'
        data_pass = 'PASS' if results.get('data_integrity', {}).get('passed', False) else 'WARN'
        rand_pass = 'PASS' if results.get('randomization_balance', {}).get('passed', False) else 'WARN'
        temp_pass = 'PASS' if results.get('temporal_consistency', {}).get('passed', True) else 'WARN'
        
        summary_data.append({
            'Test': test_config['name'],
            'Sample Size': len(all_dataframes[test_id]),
            'SRM': srm_pass,
            'Data Integrity': data_pass,
            'Randomization': rand_pass,
            'Temporal': temp_pass,
            'Overall Status': overall.get('status', 'UNKNOWN').replace('✅', 'PASS').replace('⚠️', 'WARN').replace('❌', 'FAIL')
        })
    
    summary_df = pd.DataFrame(summary_data)
    print(summary_df.to_string(index=False))
    
    # Save summary
    summary_path = os.path.join(reports_dir, "validation_summary.txt")
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("VALIDATION SUMMARY - ALL TESTS\n")
        f.write("="*80 + "\n\n")
        f.write(summary_df.to_string(index=False))
        f.write(f"\n\nGenerated: {pd.Timestamp.now()}\n")
    
    print(f"\n[OK] Summary report saved to: {summary_path}")
    
    # ========================================================================
    # FINAL RECOMMENDATIONS
    # ========================================================================
    
    print("\n" + "#"*80)
    print("# FINAL RECOMMENDATIONS")
    print("#"*80 + "\n")
    
    valid_tests = []
    caution_tests = []
    invalid_tests = []
    
    for test_id, test_config in tests.items():
        overall = all_validation_results[test_id].get('overall', {})
        status = overall.get('status', '')
        
        if 'VALID' in status and 'WARN' not in status and 'FAIL' not in status:
            valid_tests.append(test_config['name'])
        elif 'CAUTION' in status or 'WARN' in status:
            caution_tests.append(test_config['name'])
        else:
            invalid_tests.append(test_config['name'])
    
    print("[PASS] READY FOR STATISTICAL ANALYSIS:")
    if valid_tests:
        for test in valid_tests:
            print(f"   - {test}")
    else:
        print("   None")
    
    print("\n[WARN] PROCEED WITH CAUTION (minor issues):")
    if caution_tests:
        for test in caution_tests:
            print(f"   - {test}")
    else:
        print("   None")
    
    print("\n[FAIL] NEEDS ATTENTION (significant issues):")
    if invalid_tests:
        for test in invalid_tests:
            print(f"   - {test}")
    else:
        print("   None")
    
    print("\n" + "="*80)
    print("STAGE 1 & 2 COMPLETE!")
    print("="*80)
    print("\nNext Steps:")
    print("1. Review detailed validation reports in: reports/validation_reports/")
    print("2. Address any critical issues found")
    print("3. Proceed to Stage 3: Exploratory Data Analysis")
    print(f"\n{len(tests)} tests processed successfully.")
    print("\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
