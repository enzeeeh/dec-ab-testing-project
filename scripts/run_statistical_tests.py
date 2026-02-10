"""
Statistical Testing Runner for A/B Tests

Runs comprehensive statistical analysis on all 5 A/B tests with:
- Automatic test selection based on metric type
- Multiple testing correction
- Detailed reporting

Usage:
    python scripts/run_statistical_tests.py
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Add scripts to path
sys.path.append(os.path.dirname(__file__))

from statistical_analysis import StatisticalAnalyzer
from utils import load_test_data


def get_test_metrics(test_name: str) -> list:
    """
    Define primary metrics for each test.
    
    Returns metrics to analyze for each test.
    """
    metrics_map = {
        'test1_menu': ['revenue', 'pages_viewed', 'added_to_cart', 'bounced'],
        'test2_novelty_slider': ['novelty_revenue', 'is_registered', 'products_added_from_novelties'],
        'test3_product_sliders': ['revenue_from_recommendations', 'add_to_cart_rate', 
                                 'slider_interactions', 'products_per_order', 'avg_product_price'],
        'test4_reviews': ['converted', 'added_to_cart'],
        'test5_search_engine': ['avg_revenue_per_visitor', 'converted', 
                               'added_to_cart', 'interacted_with_search']
    }
    return metrics_map.get(test_name, [])


def format_result_summary(result: dict) -> str:
    """Format a test result into readable text."""
    lines = []
    lines.append(f"\nMETRIC: {result['metric']}")
    lines.append("=" * 70)
    lines.append(f"Test Type: {result['test_type']}")
    lines.append(f"Metric Type: {result['metric_type']}")
    lines.append(f"Sample Size: {result['total_n']:,}")
    
    # Show test-specific results
    if 'p_value' in result:
        lines.append(f"\nP-Value: {result['p_value']:.6f}")
        lines.append(f"Significant: {'YES ✅' if result.get('significant', False) else 'NO'}")
    
    # For two-sample tests
    if 'variant_A' in result and 'variant_B' in result:
        lines.append(f"\nVariant A ({result['variant_A']}): n={result['n_A']:,}")
        lines.append(f"Variant B ({result['variant_B']}): n={result['n_B']:,}")
        
        # Show appropriate metrics
        if 'rate_A' in result:
            lines.append(f"\nConversion Rate A: {result['rate_A']:.4f} ({result['rate_A']*100:.2f}%)")
            lines.append(f"Conversion Rate B: {result['rate_B']:.4f} ({result['rate_B']*100:.2f}%)")
            lines.append(f"Absolute Difference: {result['absolute_difference']:.4f}")
            if not pd.isna(result.get('relative_lift')):
                lines.append(f"Relative Lift: {result['relative_lift']*100:.2f}%")
            if 'ci_lower' in result and 'ci_upper' in result:
                lines.append(f"95% CI: [{result['ci_lower']:.4f}, {result['ci_upper']:.4f}]")
        
        elif 'mean_A' in result:
            lines.append(f"\nMean A: {result['mean_A']:.4f}")
            lines.append(f"Mean B: {result['mean_B']:.4f}")
            lines.append(f"Difference: {result['mean_difference']:.4f}")
            if 'cohens_d' in result:
                lines.append(f"Cohen's d: {result['cohens_d']:.3f}")
            if 'ci_lower' in result and 'ci_upper' in result:
                lines.append(f"95% CI: [{result['ci_lower']:.4f}, {result['ci_upper']:.4f}]")
        
        elif 'median_A' in result:
            lines.append(f"\nMedian A: {result['median_A']:.4f}")
            lines.append(f"Median B: {result['median_B']:.4f}")
            lines.append(f"Median Difference: {result['median_difference']:.4f}")
            if 'rank_biserial_r' in result:
                lines.append(f"Rank-Biserial r: {result['rank_biserial_r']:.3f}")
    
    # For multi-variant tests
    if 'pairwise_comparisons' in result:
        lines.append(f"\nPairwise Comparisons ({len(result['pairwise_comparisons'])} total):")
        for comp in result['pairwise_comparisons']:
            sig_marker = " ✅" if comp['p_value'] < 0.05 else ""
            lines.append(f"  {comp['variant_1']} vs {comp['variant_2']}: p={comp['p_value']:.4f}{sig_marker}")
    
    lines.append(f"\nInterpretation:")
    lines.append(result.get('interpretation', 'No interpretation available'))
    lines.append("=" * 70)
    
    return "\n".join(lines)


def save_test_report(test_name: str, test_results: list, correction_results: dict, output_dir: str):
    """Save detailed report for a single test."""
    report_path = os.path.join(output_dir, f"{test_name}_statistical_report.txt")
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write(f"STATISTICAL ANALYSIS REPORT: {test_name.upper()}\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now()}\n")
        f.write("=" * 80 + "\n\n")
        
        # Write individual metric results
        for result in test_results:
            f.write(format_result_summary(result))
            f.write("\n\n")
        
        # Write multiple testing correction results
        f.write("\n" + "=" * 80 + "\n")
        f.write("MULTIPLE TESTING CORRECTION\n")
        f.write("=" * 80 + "\n")
        f.write(f"Method: {correction_results['method'].upper()}\n")
        f.write(f"Number of tests: {correction_results['n_tests']}\n")
        f.write(f"Original alpha: {correction_results['original_alpha']}\n")
        f.write(f"Significant after correction: {correction_results['n_significant']}\n\n")
        
        for i, (orig_p, corr_p, reject) in enumerate(zip(
            correction_results['original_p_values'],
            correction_results['corrected_p_values'],
            correction_results['reject_null']
        )):
            metric_name = test_results[i]['metric'] if i < len(test_results) else f"Test {i+1}"
            status = "SIGNIFICANT ✅" if reject else "NOT SIGNIFICANT"
            f.write(f"{metric_name}:\n")
            f.write(f"  Original p-value: {orig_p:.6f}\n")
            f.write(f"  Corrected p-value: {corr_p:.6f}\n")
            f.write(f"  Decision: {status}\n\n")
        
        f.write("=" * 80 + "\n")
    
    print(f"[OK] Report saved: {report_path}")


def run_test_analysis(test_id: str, test_config: dict, data_dir: str, reports_dir: str):
    """Run statistical analysis for a single test."""
    print(f"\n{'='*80}")
    print(f"ANALYZING: {test_config['name']}")
    print('='*80)
    
    # Load data
    file_path = os.path.join(data_dir, test_config['file'])
    df = load_test_data(file_path)
    
    print(f"Loaded {len(df):,} sessions")
    print(f"Variants: {df['variant'].unique().tolist()}")
    
    # Get metrics to test
    metrics = get_test_metrics(test_id)
    print(f"Testing {len(metrics)} metrics: {metrics}")
    
    # Initialize analyzer
    analyzer = StatisticalAnalyzer(alpha=0.05)
    
    # Run tests for each metric
    test_results = []
    p_values = []
    
    for metric in metrics:
        print(f"\n  Testing metric: {metric}...")
        try:
            result = analyzer.select_and_run_test(df, metric, variant_col='variant')
            test_results.append(result)
            p_values.append(result['p_value'])
            
            # Quick summary
            sig_marker = "✅ SIGNIFICANT" if result['significant'] else "NOT SIGNIFICANT"
            print(f"    {result['test_type']}: p={result['p_value']:.4f} - {sig_marker}")
            
        except Exception as e:
            print(f"    ERROR: {str(e)}")
            continue
    
    # Apply multiple testing correction
    if len(p_values) > 1:
        print(f"\n  Applying Holm-Bonferroni correction...")
        correction_results = analyzer.multiple_testing_correction(p_values, method='holm')
        print(f"    {correction_results['n_significant']} of {len(p_values)} remain significant")
    else:
        correction_results = {
            'method': 'none',
            'n_tests': len(p_values),
            'original_alpha': 0.05,
            'original_p_values': p_values,
            'corrected_p_values': p_values,
            'reject_null': [p < 0.05 for p in p_values],
            'n_significant': sum([p < 0.05 for p in p_values])
        }
    
    # Save report
    save_test_report(test_id, test_results, correction_results, reports_dir)
    
    return {
        'test_id': test_id,
        'test_name': test_config['name'],
        'n_metrics': len(metrics),
        'n_significant_before': sum([r['significant'] for r in test_results]),
        'n_significant_after': correction_results['n_significant'],
        'results': test_results,
        'correction': correction_results
    }


def generate_summary_report(all_test_results: list, output_path: str):
    """Generate overall summary report for all tests."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("A/B TESTING - STATISTICAL ANALYSIS SUMMARY\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now()}\n")
        f.write(f"Total Tests Analyzed: {len(all_test_results)}\n")
        f.write("=" * 80 + "\n\n")
        
        # Summary table
        f.write("SUMMARY TABLE\n")
        f.write("-" * 80 + "\n")
        f.write(f"{'Test':<30} {'Metrics':<10} {'Sig (Raw)':<12} {'Sig (Corrected)':<15}\n")
        f.write("-" * 80 + "\n")
        
        for result in all_test_results:
            f.write(f"{result['test_name']:<30} "
                   f"{result['n_metrics']:<10} "
                   f"{result['n_significant_before']:<12} "
                   f"{result['n_significant_after']:<15}\n")
        
        f.write("-" * 80 + "\n\n")
        
        # Detailed findings per test
        f.write("DETAILED FINDINGS\n")
        f.write("=" * 80 + "\n\n")
        
        for test_result in all_test_results:
            f.write(f"{test_result['test_name']}\n")
            f.write("-" * 80 + "\n")
            
            significant_metrics = []
            for i, metric_result in enumerate(test_result['results']):
                is_sig_after = test_result['correction']['reject_null'][i]
                if is_sig_after:
                    significant_metrics.append(metric_result['metric'])
                    f.write(f"  ✅ {metric_result['metric']}: {metric_result['interpretation']}\n")
            
            if not significant_metrics:
                f.write("  No significant findings after correction.\n")
            
            f.write("\n")
        
        f.write("=" * 80 + "\n")
        f.write("END OF REPORT\n")
        f.write("=" * 80 + "\n")
    
    print(f"\n[OK] Summary report saved: {output_path}")


def main():
    """Main execution function."""
    # Setup paths
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_root, 'data')
    reports_dir = os.path.join(project_root, 'reports', 'statistical_results')
    
    # Create reports directory
    os.makedirs(reports_dir, exist_ok=True)
    
    # Define tests
    tests = {
        'test1_menu': {
            'file': 'test1_menu.csv',
            'name': 'Menu Navigation Test'
        },
        'test2_novelty_slider': {
            'file': 'test2_novelty_slider.csv',
            'name': 'Novelty Slider Test'
        },
        'test3_product_sliders': {
            'file': 'test3_product_sliders.csv',
            'name': 'Product Sliders Test'
        },
        'test4_reviews': {
            'file': 'test4_reviews.csv',
            'name': 'Reviews Test'
        },
        'test5_search_engine': {
            'file': 'test5_search_engine.csv',
            'name': 'Search Engine Test'
        }
    }
    
    print("=" * 80)
    print("STATISTICAL TESTING - A/B TEST ANALYSIS")
    print("=" * 80)
    print(f"\nAnalyzing {len(tests)} A/B tests...")
    print(f"Reports will be saved to: {reports_dir}")
    
    # Run analysis for each test
    all_results = []
    for test_id, test_config in tests.items():
        try:
            result = run_test_analysis(test_id, test_config, data_dir, reports_dir)
            all_results.append(result)
        except Exception as e:
            print(f"\n[ERROR] Failed to analyze {test_id}: {str(e)}")
            continue
    
    # Generate summary report
    summary_path = os.path.join(reports_dir, 'statistical_summary.txt')
    generate_summary_report(all_results, summary_path)
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE!")
    print("=" * 80)
    print(f"\nResults saved in: {reports_dir}")
    print(f"  - Individual test reports: 5 files")
    print(f"  - Summary report: statistical_summary.txt")
    print("\nNext Steps:")
    print("  1. Review statistical_summary.txt for overview")
    print("  2. Check individual test reports for detailed results")
    print("  3. Focus on metrics that remain significant after correction")
    print("=" * 80)


if __name__ == '__main__':
    main()
