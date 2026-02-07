"""
Comprehensive Experimental Validation Framework for A/B Testing

MERGED VALIDATION SUITE - Combines Best Practices from Both Implementations

Implements ALL required validation checks:
1. Sample Ratio Mismatch (SRM) Detection 
2. Data Integrity Verification (duplicates, missing values, anomalies)
3. Covariate Balance Verification (SMD-based)
4. Temporal Stability Checks (CV and variance-based)
5. Outlier Detection (IQR method)
6. Sample Size Adequacy Tests
7. Multiple Testing Correction (Bonferroni, Holm, FDR)

Statistical Rigor + Practical Engineering Checks

When run directly, validates all 5 A/B tests with comprehensive reporting.

References:
- Bonferroni (1936)
- Holm (1979)
- Benjamini & Hochberg (1995)
"""

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests
from typing import Dict, List, Tuple, Optional, Union
import warnings
from datetime import datetime
import os


class ExperimentValidator:
    """
    Modular validation framework for A/B tests.
    
    Provides individual validation methods that can be called independently
    for maximum flexibility and reusability.
    """
    
    def __init__(self, 
                 srm_threshold: float = 0.001,
                 balance_threshold: float = 0.2,
                 temporal_threshold: float = 0.2):
        """
        Initialize validator with thresholds.
        
        Parameters:
        -----------
        srm_threshold : float
            P-value threshold for SRM detection (default: 0.001)
        balance_threshold : float
            SMD threshold for covariate balance (default: 0.2)
        temporal_threshold : float
            CV threshold for temporal stability (default: 0.2)
        """
        self.srm_threshold = srm_threshold
        self.balance_threshold = balance_threshold
        self.temporal_threshold = temporal_threshold
    
    def sample_ratio_mismatch_test(self,
                                   df: pd.DataFrame,
                                   variant_col: str,
                                   expected_ratio: Optional[Dict[str, float]] = None) -> Dict:
        """
        Sample Ratio Mismatch Detection using Chi-square test.
        
        SRM is a critical issue that invalidates the entire experiment.
        """
        
        observed = df[variant_col].value_counts().sort_index()
        total = len(df)
        n_variants = len(observed)
        
        if expected_ratio is None:
            expected = pd.Series([total / n_variants] * n_variants, index=observed.index)
        else:
            expected = pd.Series({k: v * total for k, v in expected_ratio.items()})
        
        chi2_stat = np.sum((observed - expected)**2 / expected)
        df_chi = n_variants - 1
        pvalue = 1 - stats.chi2.cdf(chi2_stat, df_chi)
        
        has_srm = pvalue < self.srm_threshold
        
        result = {
            'test': 'sample_ratio_mismatch',
            'chi2_statistic': chi2_stat,
            'degrees_of_freedom': df_chi,
            'pvalue': pvalue,
            'threshold': self.srm_threshold,
            'has_srm': has_srm,
            'observed_counts': observed.to_dict(),
            'expected_counts': expected.to_dict(),
            'observed_ratio': (observed / total).to_dict(),
            'expected_ratio': (expected / total).to_dict(),
            'passed': not has_srm
        }
        
        if has_srm:
            result['warning'] = f"❌ CRITICAL: SRM detected (p={pvalue:.6f} < {self.srm_threshold}). Experiment is INVALID."
        else:
            result['message'] = f"✅ No SRM detected (p={pvalue:.4f}). Allocation is as expected."
        
        return result
    
    def data_integrity_check(self, df: pd.DataFrame) -> Dict:
        """
        Check for data integrity issues:
        - Duplicate records
        - Missing values
        - Negative revenues
        - Future dates
        """
        
        issues = []
        
        # Duplicates
        duplicates = df.duplicated(subset=['session_id']).sum() if 'session_id' in df.columns else 0
        if duplicates > 0:
            issues.append(f"Duplicate session IDs: {duplicates}")
        
        # Missing values
        missing_counts = df.isnull().sum()
        missing_counts = missing_counts[missing_counts > 0]
        for col, count in missing_counts.items():
            pct = count / len(df) * 100
            issues.append(f"{col} has {count} missing values ({pct:.2f}%)")
        
        # Negative values in revenue metrics
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if 'revenue' in col.lower() or 'price' in col.lower():
                negative_count = (df[col] < 0).sum()
                if negative_count > 0:
                    issues.append(f"{col} has {negative_count} negative values")
        
        # Future dates
        if 'timestamp' in df.columns:
            df_temp = df.copy()
            df_temp['timestamp'] = pd.to_datetime(df_temp['timestamp'], errors='coerce')
            future = (df_temp['timestamp'] > pd.Timestamp.now()).sum()
            if future > 0:
                issues.append(f"Future dates detected: {future} records")
        
        # Status
        if len(issues) == 0:
            status = '✅ PASS'
            message = "No data integrity issues detected."
            passed = True
        elif len(issues) <= 2:
            status = '⚠️ WARNING'
            message = f"Minor data quality issues detected: {len(issues)} issue(s)."
            passed = True
        else:
            status = '❌ FAIL'
            message = f"Multiple data integrity issues: {len(issues)} issue(s)."
            passed = False
        
        return {
            'test': 'data_integrity',
            'issues': issues,
            'n_issues': len(issues),
            'status': status,
            'message': message,
            'passed': passed
        }
    
    def covariate_balance_check(self,
                                df: pd.DataFrame,
                                variant_col: str,
                                covariates: List[str],
                                threshold: Optional[float] = None) -> Dict:
        """
        Covariate balance verification using Standardized Mean Difference (SMD).
        
        SMD < 0.1: Excellent balance
        SMD 0.1-0.2: Good balance
        SMD > 0.2: Potential imbalance
        """
        
        if threshold is None:
            threshold = self.balance_threshold
        
        variants = df[variant_col].unique()
        
        if len(variants) < 2:
            return {'error': 'Need at least 2 variants for balance check', 'passed': False}
        
        balance_results = []
        imbalanced_covariates = []
        
        for covariate in covariates:
            if covariate not in df.columns:
                continue
            
            is_categorical = (
                df[covariate].dtype == 'object' or 
                df[covariate].dtype.name == 'category' or
                df[covariate].nunique() < 10
            )
            
            if is_categorical:
                # Categorical: SMD for proportions
                for category in df[covariate].unique():
                    proportions = {}
                    for variant in variants:
                        variant_data = df[df[variant_col] == variant][covariate]
                        proportions[variant] = (variant_data == category).mean()
                    
                    variant_list = list(variants)
                    p1 = proportions[variant_list[0]]
                    p2 = proportions[variant_list[1]]
                    p_pooled = (p1 + p2) / 2
                    
                    if p_pooled > 0 and p_pooled < 1:
                        smd = abs(p1 - p2) / np.sqrt(p_pooled * (1 - p_pooled))
                    else:
                        smd = 0.0
                    
                    is_imbalanced = smd > threshold
                    
                    balance_results.append({
                        'covariate': f"{covariate}={category}",
                        'type': 'categorical',
                        'smd': smd,
                        'imbalanced': is_imbalanced
                    })
                    
                    if is_imbalanced:
                        imbalanced_covariates.append(f"{covariate}={category}")
            else:
                # Continuous: SMD for means
                variant_stats = {}
                for variant in variants:
                    variant_data = df[df[variant_col] == variant][covariate]
                    variant_stats[variant] = {
                        'mean': variant_data.mean(),
                        'std': variant_data.std(),
                        'var': variant_data.var()
                    }
                
                variant_list = list(variants)
                v1, v2 = variant_list[0], variant_list[1]
                
                mean_diff = abs(variant_stats[v1]['mean'] - variant_stats[v2]['mean'])
                pooled_std = np.sqrt((variant_stats[v1]['var'] + variant_stats[v2]['var']) / 2)
                
                if pooled_std > 0:
                    smd = mean_diff / pooled_std
                else:
                    smd = 0.0
                
                is_imbalanced = smd > threshold
                
                balance_results.append({
                    'covariate': covariate,
                    'type': 'continuous',
                    'smd': smd,
                    'imbalanced': is_imbalanced
                })
                
                if is_imbalanced:
                    imbalanced_covariates.append(covariate)
        
        balance_df = pd.DataFrame(balance_results) if balance_results else pd.DataFrame()
        max_smd = balance_df['smd'].max() if len(balance_df) > 0 else 0
        n_imbalanced = len(imbalanced_covariates)
        
        if max_smd < 0.1:
            message = f"✅ Excellent balance (max SMD={max_smd:.3f} < 0.1)"
        elif max_smd < threshold:
            message = f"✅ Good balance (max SMD={max_smd:.3f} < {threshold})"
        else:
            message = f"⚠️ {n_imbalanced} covariate(s) imbalanced (max SMD={max_smd:.3f} ≥ {threshold})"
        
        return {
            'test': 'covariate_balance',
            'balance_results': balance_df,
            'imbalanced_covariates': imbalanced_covariates,
            'n_imbalanced': n_imbalanced,
            'max_smd': max_smd,
            'threshold': threshold,
            'message': message,
            'passed': max_smd < threshold
        }
    
    def temporal_stability_check(self,
                                df: pd.DataFrame,
                                variant_col: str,
                                date_col: str,
                                threshold: Optional[float] = None) -> Dict:
        """
        Temporal stability verification using Coefficient of Variation.
        
        Checks if variant allocation remains stable across time.
        """
        
        if threshold is None:
            threshold = self.temporal_threshold
        
        df = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        
        df['date'] = df[date_col].dt.date
        daily_counts = df.groupby(['date', variant_col]).size().unstack(fill_value=0)
        
        cv_results = {}
        for variant in daily_counts.columns:
            counts = daily_counts[variant]
            mean_count = counts.mean()
            std_count = counts.std()
            cv = std_count / mean_count if mean_count > 0 else 0.0
            cv_results[variant] = cv
        
        max_cv = max(cv_results.values()) if cv_results else 0
        is_stable = max_cv < threshold
        
        message = (
            f"✅ Stable allocation (max CV={max_cv:.3f} < {threshold})" if is_stable
            else f"⚠️ Unstable allocation (max CV={max_cv:.3f} ≥ {threshold})"
        )
        
        return {
            'test': 'temporal_stability',
            'cv_by_variant': cv_results,
            'max_cv': max_cv,
            'threshold': threshold,
            'is_stable': is_stable,
            'n_days': len(daily_counts),
            'message': message,
            'passed': is_stable
        }
    
    def outlier_detection(self, df: pd.DataFrame, n_cols: int = 5) -> Dict:
        """
        Detect outliers using IQR method.
        
        Outliers = values beyond 1.5*IQR from quartiles
        """
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        metric_cols = [col for col in numeric_cols if col not in ['session_id', 'user_id']]
        
        outlier_summary = {}
        total_outliers = 0
        
        for col in metric_cols[:n_cols]:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
            pct_outliers = outliers / len(df) * 100
            
            outlier_summary[col] = {
                'n_outliers': outliers,
                'pct_outliers': pct_outliers
            }
            total_outliers += outliers
        
        max_outlier_pct = max([v['pct_outliers'] for v in outlier_summary.values()]) if outlier_summary else 0
        
        if max_outlier_pct > 10:
            status = '⚠️ WARNING'
            message = f"High outlier percentage ({max_outlier_pct:.2f}%). Consider winsorization."
            passed = False
        else:
            status = '✅ PASS'
            message = "Outlier levels within acceptable range."
            passed = True
        
        return {
            'test': 'outlier_detection',
            'outlier_summary': outlier_summary,
            'max_outlier_pct': max_outlier_pct,
            'status': status,
            'message': message,
            'passed': passed
        }
    
    def sample_size_check(self,
                         df: pd.DataFrame,
                         variant_col: str,
                         desired_power: float = 0.8,
                         alpha: float = 0.05,
                         mde: float = 0.05) -> Dict:
        """
        Check if sample size is adequate.
        
        Uses simplified power calculation: n ≈ 16 * (1/mde)^2
        """
        
        variant_counts = df[variant_col].value_counts()
        min_sample = variant_counts.min()
        
        required_per_variant = int(16 / (mde ** 2))
        detectable_mde = np.sqrt(16 / min_sample) if min_sample > 0 else float('inf')
        
        if min_sample >= required_per_variant:
            status = '✅ ADEQUATE'
            message = f"Sample size sufficient for {mde*100}% MDE."
            passed = True
        elif min_sample >= required_per_variant * 0.7:
            status = '⚠️ BORDERLINE'
            message = f"Can detect approximately {detectable_mde*100:.1f}% effect."
            passed = True
        else:
            status = '❌ UNDERPOWERED'
            message = f"Only detects {detectable_mde*100:.1f}% effects (need {mde*100}%)."
            passed = False
        
        return {
            'test': 'sample_size',
            'variant_counts': variant_counts.to_dict(),
            'min_sample': int(min_sample),
            'required_sample': required_per_variant,
            'detectable_mde': detectable_mde,
            'status': status,
            'message': message,
            'passed': passed
        }
    
    def multiple_testing_correction(self,
                                    pvalues: List[float],
                                    method: str = 'holm',
                                    alpha: float = 0.05) -> Dict:
        """
        Multiple testing correction to control Type I error.
        
        Methods:
        - 'bonferroni': Most conservative (alpha/k)
        - 'holm': Holm-Bonferroni (recommended for 5-10 tests)
        - 'fdr_bh': Benjamini-Hochberg FDR (for >10 tests)
        """
        
        pvalues_array = np.array(pvalues)
        n_tests = len(pvalues_array)
        
        reject, pvals_corrected, alphacSidak, alphacBonf = multipletests(
            pvalues_array,
            alpha=alpha,
            method=method
        )
        
        method_names = {
            'bonferroni': 'Bonferroni',
            'holm': 'Holm-Bonferroni',
            'fdr_bh': 'Benjamini-Hochberg FDR'
        }
        
        return {
            'test': 'multiple_testing_correction',
            'method': method_names.get(method, method),
            'n_tests': n_tests,
            'alpha': alpha,
            'original_pvalues': pvalues_array.tolist(),
            'corrected_pvalues': pvals_corrected.tolist(),
            'reject': reject.tolist(),
            'n_significant_original': int(sum(pvalues_array < alpha)),
            'n_significant_corrected': int(sum(reject)),
            'message': (
                f"✓ Correction: {method_names.get(method, method)}\n"
                f"  Original significant: {sum(pvalues_array < alpha)}/{n_tests}\n"
                f"  Corrected significant: {sum(reject)}/{n_tests}"
            )
        }
    
    def run_all_validations(self,
                           df: pd.DataFrame,
                           variant_col: str,
                           covariates: Optional[List[str]] = None,
                           date_col: Optional[str] = None,
                           metric_pvalues: Optional[List[float]] = None,
                           correction_method: str = 'holm') -> Dict:
        """
        Run complete validation suite.
        """
        
        results = {}
        
        print("=" * 80)
        print("COMPREHENSIVE VALIDATION SUITE")
        print("=" * 80)
        
        # 1. SRM Test
        print("\n1. Sample Ratio Mismatch Test")
        print("-" * 80)
        srm_result = self.sample_ratio_mismatch_test(df, variant_col)
        results['srm'] = srm_result
        print(srm_result.get('message', srm_result.get('warning', '')))
        
        if srm_result['has_srm']:
            print("\n" + "=" * 80)
            print("VALIDATION FAILED: SRM DETECTED - EXPERIMENT IS INVALID")
            print("=" * 80)
            return results
        
        # 2. Data Integrity
        print("\n2. Data Integrity Check")
        print("-" * 80)
        integrity_result = self.data_integrity_check(df)
        results['data_integrity'] = integrity_result
        print(integrity_result.get('message', ''))
        if integrity_result['issues']:
            for issue in integrity_result['issues']:
                print(f"  - {issue}")
        
        # 3. Covariate Balance
        if covariates:
            print("\n3. Covariate Balance Check")
            print("-" * 80)
            balance_result = self.covariate_balance_check(df, variant_col, covariates)
            results['balance'] = balance_result
            print(balance_result.get('message', ''))
        
        # 4. Temporal Stability
        if date_col:
            print("\n4. Temporal Stability Check")
            print("-" * 80)
            temporal_result = self.temporal_stability_check(df, variant_col, date_col)
            results['temporal'] = temporal_result
            print(temporal_result.get('message', ''))
        
        # 5. Outlier Detection
        print("\n5. Outlier Detection")
        print("-" * 80)
        outlier_result = self.outlier_detection(df)
        results['outliers'] = outlier_result
        print(outlier_result.get('message', ''))
        
        # 6. Sample Size
        print("\n6. Sample Size Adequacy")
        print("-" * 80)
        sample_result = self.sample_size_check(df, variant_col)
        results['sample_size'] = sample_result
        print(f"Minimum sample: {sample_result['min_sample']:,}")
        print(f"Required sample: {sample_result['required_sample']:,}")
        print(sample_result.get('message', ''))
        
        # 7. Multiple Testing Correction
        if metric_pvalues:
            print("\n7. Multiple Testing Correction")
            print("-" * 80)
            correction_result = self.multiple_testing_correction(
                metric_pvalues,
                method=correction_method,
                alpha=0.05
            )
            results['multiple_testing'] = correction_result
            print(correction_result.get('message', ''))
        
        # Summary
        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        
        critical_passed = srm_result['passed'] and integrity_result['passed']
        all_passed = all(v.get('passed', True) for v in results.values())
        
        if critical_passed and all_passed:
            print("\n✅ ALL VALIDATION CHECKS PASSED")
            print("\nYou can proceed with statistical testing with full confidence.")
        elif critical_passed:
            print("\n⚠️ CRITICAL CHECKS PASSED, MINOR WARNINGS DETECTED")
            print("\nProceed with caution and consider adjustment methods.")
        else:
            print("\n❌ CRITICAL VALIDATION FAILURES")
            print("\nDO NOT analyze this experiment until issues are resolved.")
        
        print("=" * 80 + "\n")
        
        return results


# ============================================================================
# CONVENIENCE FUNCTION FOR QUICK VALIDATION REPORT
# ============================================================================

def validate_test(test_name: str, df: pd.DataFrame) -> Dict:
    """
    Quick validation of a single test.
    
    Returns summary dictionary with key metrics.
    """
    
    validator = ExperimentValidator()
    
    # Run validations
    srm = validator.sample_ratio_mismatch_test(df, 'variant')
    integrity = validator.data_integrity_check(df)
    balance = validator.covariate_balance_check(
        df, 'variant', ['device_type', 'browser', 'region']
    )
    temporal = validator.temporal_stability_check(df, 'variant', 'timestamp')
    outliers = validator.outlier_detection(df)
    sample_size = validator.sample_size_check(df, 'variant')
    
    return {
        'test': test_name,
        'n_sessions': len(df),
        'n_variants': len(df['variant'].unique()),
        'srm_pvalue': round(srm['pvalue'], 6),
        'srm_passed': srm['passed'],
        'integrity_passed': integrity['passed'],
        'balance_smd': round(balance['max_smd'], 3),
        'balance_passed': balance['passed'],
        'temporal_cv': round(temporal['max_cv'], 3),
        'temporal_passed': temporal['passed'],
        'outlier_pct': round(outliers['max_outlier_pct'], 2),
        'outlier_passed': outliers['passed'],
        'min_sample': sample_size['min_sample'],
        'sample_passed': sample_size['passed'],
        'validity': 'VALID' if (srm['passed'] and integrity['passed']) else 'INVALID'
    }


# ============================================================================
# MAIN VALIDATION RUNNER FOR ALL 5 TESTS
# ============================================================================

def validate_all_tests():
    """Run validation on all 5 A/B tests and generate summary report."""
    
    print("="*80)
    print("COMPREHENSIVE VALIDATION FOR ALL 5 A/B TESTS")
    print("="*80)
    
    tests = [
        ('Test 1: Menu Design', 'data/test1_menu.csv'),
        ('Test 2: Novelty Slider', 'data/test2_novelty_slider.csv'),
        ('Test 3: Product Sliders', 'data/test3_product_sliders.csv'),
        ('Test 4: Customer Reviews', 'data/test4_reviews.csv'),
        ('Test 5: Search Engine', 'data/test5_search_engine.csv')
    ]
    
    results = []
    
    for test_name, filepath in tests:
        print(f"\n{'='*80}")
        print(f"VALIDATING: {test_name}")
        print('='*80)
        
        try:
            df = pd.read_csv(filepath)
            print(f"✓ Loaded: {len(df):,} rows\n")
            
            result = validate_test(test_name, df)
            results.append(result)
            
        except FileNotFoundError:
            print(f"✗ File not found: {filepath}")
            print("  Run data_generation.py first!")
            continue
    
    # Summary table
    if results:
        print(f"\n\n{'='*80}")
        print("VALIDATION SUMMARY TABLE")
        print('='*80)
        
        summary_df = pd.DataFrame(results)
        
        print(f"\n{'Test':<30} {'N':>8} {'Valid':>10} {'SRM':<8} {'Balance':<8} {'Temporal':<8}")
        print('-'*80)
        
        for _, row in summary_df.iterrows():
            test = row['test'][:28]
            n = f"{int(row['n_sessions']):,}"
            valid = row['validity']
            srm = "✅" if row['srm_passed'] else "❌"
            balance = "✅" if row['balance_passed'] else "⚠️"
            temporal = "✅" if row['temporal_passed'] else "⚠️"
            
            print(f"{test:<30} {n:>8} {valid:>10} {srm:<8} {balance:<8} {temporal:<8}")
        
        # Stats
        print(f"\n{'='*80}")
        print("OVERALL STATISTICS")
        print('='*80)
        
        total_sessions = summary_df['n_sessions'].sum()
        n_valid = (summary_df['validity'] == 'VALID').sum()
        
        print(f"\nTotal sessions: {total_sessions:,}")
        print(f"Valid tests: {n_valid}/{len(results)}")
        
        if n_valid == len(results):
            print("\n✅ ALL TESTS ARE VALID")
            print("Proceed to Stage 4: Statistical Testing")
        else:
            invalid = summary_df[summary_df['validity'] == 'INVALID']
            print(f"\n❌ {len(invalid)} INVALID TEST(S):")
            for _, row in invalid.iterrows():
                print(f"   - {row['test']}")


if __name__ == "__main__":
    validate_all_tests()
