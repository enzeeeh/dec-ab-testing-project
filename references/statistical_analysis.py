"""
Author: Hilmi
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import chi2_contingency
from statsmodels.stats.multitest import multipletests
from typing import Dict, List, Tuple, Optional
import warnings

try:
    from validation import ExperimentValidator
    VALIDATION_AVAILABLE = True
except ImportError:
    VALIDATION_AVAILABLE = False
    warnings.warn("Validation module not available. Skipping validation checks.")


class ABTestAnalyzer:
    
    def __init__(self, alpha: float = 0.05):
        self.alpha = alpha
        if VALIDATION_AVAILABLE:
            self.validator = ExperimentValidator(srm_threshold=0.001)  
        else:
            self.validator = None
    
    def calculate_sample_size(self,
                            baseline_rate: float,
                            mde: float,
                            alpha: float = 0.05,
                            power: float = 0.80,
                            two_tailed: bool = True) -> int:
        
        # Critical values
        if two_tailed:
            z_alpha = stats.norm.ppf(1 - alpha/2)
        else:
            z_alpha = stats.norm.ppf(1 - alpha)
        
        z_beta = stats.norm.ppf(power)
        
        # Effect size
        p1 = baseline_rate
        p2 = baseline_rate * (1 + mde)
        
        # Ensure p2 is valid probability
        p2 = min(p2, 0.999)
        
        # Sample size calculation
        numerator = (z_alpha + z_beta) ** 2 * (p1 * (1 - p1) + p2 * (1 - p2))
        denominator = (p2 - p1) ** 2
        
        n = numerator / denominator
        
        return int(np.ceil(n))
    
    def two_sample_ttest(self,
                        control: np.ndarray,
                        treatment: np.ndarray,
                        metric_name: str,
                        equal_var: bool = False) -> Dict:
        
        # Remove NaN values
        control = control[~np.isnan(control)]
        treatment = treatment[~np.isnan(treatment)]
        
        # Calculate statistics
        control_mean = control.mean()
        treatment_mean = treatment.mean()
        control_std = control.std(ddof=1)
        treatment_std = treatment.std(ddof=1)
        n_control = len(control)
        n_treatment = len(treatment)
        
        # Perform t-test
        statistic, pvalue = stats.ttest_ind(treatment, control, equal_var=equal_var)
        
        # Calculate Cohen's d (effect size)
        # Reference: Cohen, J. (1988)
        pooled_std = np.sqrt((control_std**2 + treatment_std**2) / 2)
        cohens_d = (treatment_mean - control_mean) / pooled_std if pooled_std > 0 else 0
        
        # Calculate confidence interval for difference in means
        # Using Welch's approach for unequal variances
        se_diff = np.sqrt(control_std**2/n_control + treatment_std**2/n_treatment)
        
        # Degrees of freedom (Welch-Satterthwaite equation)
        if not equal_var:
            num = (control_std**2/n_control + treatment_std**2/n_treatment)**2
            denom = ((control_std**2/n_control)**2/(n_control-1) + 
                    (treatment_std**2/n_treatment)**2/(n_treatment-1))
            df = num / denom if denom > 0 else n_control + n_treatment - 2
        else:
            df = n_control + n_treatment - 2
        
        t_crit = stats.t.ppf(1 - self.alpha/2, df)
        diff = treatment_mean - control_mean
        ci_lower = diff - t_crit * se_diff
        ci_upper = diff + t_crit * se_diff
        
        # Relative lift percentage
        relative_lift_pct = (diff / control_mean * 100) if control_mean != 0 else 0
        
        return {
            'metric': metric_name,
            'test_type': 't-test',
            'statistic': statistic,
            'pvalue': pvalue,
            'significant': pvalue < self.alpha,
            'control_mean': control_mean,
            'treatment_mean': treatment_mean,
            'control_std': control_std,
            'treatment_std': treatment_std,
            'absolute_diff': diff,
            'relative_lift_pct': relative_lift_pct,
            'cohens_d': cohens_d,
            'effect_interpretation': self._interpret_cohens_d(cohens_d),
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'n_control': n_control,
            'n_treatment': n_treatment,
            'degrees_of_freedom': df
        }
    
    def proportion_test(self,
                       control_successes: int,
                       control_total: int,
                       treatment_successes: int,
                       treatment_total: int,
                       metric_name: str) -> Dict:
        
        # Calculate proportions
        p_control = control_successes / control_total
        p_treatment = treatment_successes / treatment_total
        
        # Pooled proportion
        p_pooled = (control_successes + treatment_successes) / (control_total + treatment_total)
        
        # Standard error
        se = np.sqrt(p_pooled * (1 - p_pooled) * (1/control_total + 1/treatment_total))
        
        # Z-statistic
        z_stat = (p_treatment - p_control) / se if se > 0 else 0
        
        # P-value (two-tailed)
        pvalue = 2 * (1 - stats.norm.cdf(abs(z_stat)))
        
        # Confidence interval for difference
        se_diff = np.sqrt(p_control*(1-p_control)/control_total + 
                         p_treatment*(1-p_treatment)/treatment_total)
        z_crit = stats.norm.ppf(1 - self.alpha/2)
        diff = p_treatment - p_control
        ci_lower = diff - z_crit * se_diff
        ci_upper = diff + z_crit * se_diff
        
        # Relative lift
        relative_lift_pct = (diff / p_control * 100) if p_control > 0 else 0
        
        return {
            'metric': metric_name,
            'test_type': 'proportion_test',
            'statistic': z_stat,
            'pvalue': pvalue,
            'significant': pvalue < self.alpha,
            'control_rate': p_control,
            'treatment_rate': p_treatment,
            'absolute_diff': diff,
            'relative_lift_pct': relative_lift_pct,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'n_control': control_total,
            'n_treatment': treatment_total
        }
    
    def chi_square_test(self,
                       control: np.ndarray,
                       treatment: np.ndarray,
                       metric_name: str) -> Dict:
        
        # Create contingency table
        combined = np.concatenate([control, treatment])
        labels = np.concatenate([np.zeros(len(control)), np.ones(len(treatment))])
        
        contingency_table = pd.crosstab(combined, labels)
        
        # Chi-square test
        chi2, pvalue, dof, expected = chi2_contingency(contingency_table)
        
        # Cramér's V effect size
        # Reference: Cramér, H. (1946)
        n = len(combined)
        min_dim = min(contingency_table.shape[0], contingency_table.shape[1]) - 1
        cramers_v = np.sqrt(chi2 / (n * min_dim)) if min_dim > 0 else 0
        
        return {
            'metric': metric_name,
            'test_type': 'chi_square',
            'statistic': chi2,
            'pvalue': pvalue,
            'significant': pvalue < self.alpha,
            'degrees_of_freedom': dof,
            'cramers_v': cramers_v,
            'effect_interpretation': self._interpret_cramers_v(cramers_v),
            'n_control': len(control),
            'n_treatment': len(treatment)
        }
    
    def mann_whitney_u_test(self,
                           control: np.ndarray,
                           treatment: np.ndarray,
                           metric_name: str) -> Dict:
        
        # Remove NaN
        control = control[~np.isnan(control)]
        treatment = treatment[~np.isnan(treatment)]
        
        # Mann-Whitney U test
        statistic, pvalue = stats.mannwhitneyu(treatment, control, alternative='two-sided')
        
        # Rank-biserial correlation (effect size for Mann-Whitney)
        # r = 1 - (2U)/(n₁×n₂)
        n1 = len(control)
        n2 = len(treatment)
        rank_biserial = 1 - (2*statistic) / (n1 * n2)
        
        # Medians for interpretation
        control_median = np.median(control)
        treatment_median = np.median(treatment)
        
        return {
            'metric': metric_name,
            'test_type': 'mann_whitney',
            'statistic': statistic,
            'pvalue': pvalue,
            'significant': pvalue < self.alpha,
            'control_median': control_median,
            'treatment_median': treatment_median,
            'rank_biserial': rank_biserial,
            'n_control': n1,
            'n_treatment': n2
        }
    
    def bootstrap_confidence_interval(self,
                                     control: np.ndarray,
                                     treatment: np.ndarray,
                                     metric_name: str,
                                     n_bootstrap: int = 10000,
                                     confidence_level: float = 0.95) -> Dict:
        
        np.random.seed(42)
        
        # Remove NaN
        control = control[~np.isnan(control)]
        treatment = treatment[~np.isnan(treatment)]
        
        # Bootstrap
        boot_diffs = []
        for _ in range(n_bootstrap):
            control_boot = np.random.choice(control, size=len(control), replace=True)
            treatment_boot = np.random.choice(treatment, size=len(treatment), replace=True)
            boot_diffs.append(treatment_boot.mean() - control_boot.mean())
        
        boot_diffs = np.array(boot_diffs)
        
        # Percentile method
        alpha_bootstrap = 1 - confidence_level
        ci_lower = np.percentile(boot_diffs, alpha_bootstrap/2 * 100)
        ci_upper = np.percentile(boot_diffs, (1 - alpha_bootstrap/2) * 100)
        
        # Point estimate
        observed_diff = treatment.mean() - control.mean()
        
        # Significance (if CI excludes 0)
        significant = not (ci_lower <= 0 <= ci_upper)
        
        return {
            'metric': metric_name,
            'test_type': 'bootstrap',
            'observed_diff': observed_diff,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'significant': significant,
            'confidence_level': confidence_level,
            'n_bootstrap': n_bootstrap
        }
    
    def multiple_testing_correction(self,
                                   p_values: List[float],
                                   method: str = 'holm') -> Dict:
        
        # Use statsmodels for correction
        reject, pvals_corrected, alphacSidak, alphacBonf = multipletests(
            p_values, 
            alpha=self.alpha, 
            method=method
        )
        
        # Family-Wise Error Rate without correction
        fwer_uncorrected = 1 - (1 - self.alpha) ** len(p_values)
        
        return {
            'method': method,
            'original_pvalues': p_values,
            'corrected_pvalues': pvals_corrected.tolist(),
            'reject': reject.tolist(),
            'fwer_uncorrected': fwer_uncorrected,
            'num_tests': len(p_values),
            'num_significant_uncorrected': sum(p < self.alpha for p in p_values),
            'num_significant_corrected': sum(reject)
        }
    
    def _check_normality(self, data: np.ndarray, sample_size: int = 5000) -> bool:
        data_clean = data[~np.isnan(data)]
        
        if len(data_clean) == 0:
            return False
        
        # Sample if too large (Shapiro-Wilk limit is 5000)
        if len(data_clean) > sample_size:
            np.random.seed(42)
            sample = np.random.choice(data_clean, size=sample_size, replace=False)
        else:
            sample = data_clean
        
        # Shapiro-Wilk test
        # H0: data comes from normal distribution
        # If p < 0.05, reject H0 (data is NOT normal)
        _, p_value = stats.shapiro(sample)
        
        return p_value >= 0.05  # Normal if p >= 0.05
    
    def analyze_test(self,
                    df: pd.DataFrame,
                    variant_col: str,
                    metrics: Dict,
                    run_validation: bool = True) -> pd.DataFrame:
        
        # Run validation if available and requested
        if run_validation and self.validator is not None:
            print("\n" + "="*80)
            print("RUNNING EXPERIMENTAL VALIDATION CHECKS")
            print("="*80)
            
            # Detect covariates (non-metric columns that could be confounders)
            covariates = []
            for col in df.columns:
                if col not in [variant_col] + [m['column'] for m in metrics.values()]:
                    if df[col].dtype in [np.int64, np.float64] or isinstance(df[col].dtype, pd.CategoricalDtype):
                        # Check if binary or low cardinality
                        if df[col].nunique() <= 10:
                            covariates.append(col)
            
            # SRM Test
            print("\n1. Sample Ratio Mismatch Test")
            print("-" * 80)
            srm_result = self.validator.sample_ratio_mismatch_test(df, variant_col)
            print(srm_result.get('message', srm_result.get('warning', '')))
            
            if srm_result['has_srm']:
                raise ValueError(
                    "⚠️ CRITICAL: Sample Ratio Mismatch detected. "
                    "Experiment is INVALID. Do not proceed with analysis."
                )
            
            # Covariate balance if covariates exist
            if covariates:
                print("\n2. Covariate Balance Check")
                print("-" * 80)
                balance_result = self.validator.covariate_balance_check(
                    df, variant_col, covariates
                )
                print(balance_result.get('message', ''))
            
            print("\n" + "="*80)
            print("VALIDATION COMPLETE - PROCEEDING WITH ANALYSIS")
            print("="*80 + "\n")
        
        # Get unique variants
        variants = df[variant_col].unique()
        
        if len(variants) != 2:
            warnings.warn(f"Found {len(variants)} variants. Analysis designed for 2-arm tests.")
        
        # Assume first variant is control
        control_variant = sorted(variants)[0]
        treatment_variant = sorted(variants)[1]
        
        control_df = df[df[variant_col] == control_variant]
        treatment_df = df[df[variant_col] == treatment_variant]
        
        results = []
        
        for metric_name, config in metrics.items():
            column = config['column']
            metric_type = config['type']
            
            # Extract data
            control_data = control_df[column].values
            treatment_data = treatment_df[column].values
            
            # Select appropriate test based on metric type
            if metric_type == 'binary':
                # Proportion test
                control_successes = int(control_data.sum())
                treatment_successes = int(treatment_data.sum())
                
                result = self.proportion_test(
                    control_successes, len(control_data),
                    treatment_successes, len(treatment_data),
                    metric_name
                )
                results.append(result)
                
                # Also run chi-square as alternative
                result_chi = self.chi_square_test(control_data, treatment_data, metric_name)
                results.append(result_chi)
                
            elif metric_type == 'continuous':
                # Check normality to decide which test to use
                control_normal = self._check_normality(control_data)
                treatment_normal = self._check_normality(treatment_data)
                
                print(f"\n  Normality Check for '{metric_name}':")
                print(f"    Control: {'Normal' if control_normal else 'Non-normal'}")
                print(f"    Treatment: {'Normal' if treatment_normal else 'Non-normal'}")
                
                if control_normal and treatment_normal:
                    # Both normal → Use Welch's t-test
                    print(f"    → Using Welch's t-test (parametric)")
                    result = self.two_sample_ttest(control_data, treatment_data, metric_name)
                    result['normality_check'] = 'normal_distribution'
                    result['test_selection'] = 'automatic_parametric'
                    results.append(result)
                else:
                    # Non-normal → Use Mann-Whitney U (primary)
                    print(f"    → Using Mann-Whitney U test (non-parametric)")
                    result = self.mann_whitney_u_test(control_data, treatment_data, metric_name)
                    result['normality_check'] = 'non_normal_distribution'
                    result['test_selection'] = 'automatic_nonparametric'
                    results.append(result)
                    
                    # Also include t-test for comparison (with warning)
                    result_t = self.two_sample_ttest(control_data, treatment_data, metric_name)
                    result_t['test_type'] = 'welch_t_test_comparison'
                    result_t['normality_check'] = 'non_normal_distribution'
                    result_t['warning'] = 'Data non-normal; prefer Mann-Whitney result above'
                    result_t['test_selection'] = 'comparison_only'
                    results.append(result_t)
        
        # Apply multiple testing correction within this experiment
        if len(results) > 1:
            print(f"\n{'='*80}")
            print(f"MULTIPLE TESTING CORRECTION (Per Experiment)")
            print(f"{'='*80}")
            print(f"Number of tests conducted: {len(results)}")
            
            # Extract p-values (only from primary tests, not comparison tests)
            primary_results = [r for r in results if r.get('test_selection') != 'comparison_only']
            p_values = [r['pvalue'] for r in primary_results if 'pvalue' in r]
            
            if len(p_values) > 1:
                # Apply Holm-Bonferroni correction
                correction_result = self.multiple_testing_correction(
                    p_values, 
                    method='holm'
                )
                
                print(f"Correction method: Holm-Bonferroni")
                print(f"Uncorrected significant: {correction_result['num_significant_uncorrected']}/{len(p_values)}")
                print(f"Corrected significant: {correction_result['num_significant_corrected']}/{len(p_values)}")
                print(f"FWER without correction: {correction_result['fwer_uncorrected']:.3f}")
                
                # Update primary results with corrected p-values
                p_idx = 0
                for result in primary_results:
                    if 'pvalue' in result:
                        result['pvalue_corrected'] = correction_result['corrected_pvalues'][p_idx]
                        result['significant_corrected'] = correction_result['reject'][p_idx]
                        result['correction_method'] = 'holm'
                        result['num_tests_corrected'] = len(p_values)
                        p_idx += 1
                
                print(f"{'='*80}\n")
            else:
                print("Only 1 primary test - no correction needed")
                print(f"{'='*80}\n")
        
        return pd.DataFrame(results)
    
    # Helper methods
    def _interpret_cohens_d(self, d: float) -> str:
        """Interpret Cohen's d effect size."""
        abs_d = abs(d)
        if abs_d < 0.2:
            return "Negligible"
        elif abs_d < 0.5:
            return "Small"
        elif abs_d < 0.8:
            return "Medium"
        else:
            return "Large"
    
    def _interpret_cramers_v(self, v: float) -> str:
        """Interpret Cramér's V effect size."""
        if v < 0.1:
            return "Negligible"
        elif v < 0.3:
            return "Small"
        elif v < 0.5:
            return "Medium"
        else:
            return "Large"


if __name__ == "__main__":
    np.random.seed(42)
    
    # Sample size calculation
    analyzer = ABTestAnalyzer()
    
    required_n = analyzer.calculate_sample_size(
        baseline_rate=0.05,
        mde=0.10,
        power=0.80
    )
    print(f"Required sample size per variant: {required_n:,}\n")
    
    # Generate example data
    n = 5000
    df = pd.DataFrame({
        'variant': np.random.choice(['control', 'treatment'], n),
        'conversion': np.random.binomial(1, 0.05, n),
        'revenue': np.random.gamma(2, 3, n),
        'device_type': np.random.choice(['mobile', 'desktop'], n)
    })
    
    # Add treatment effect
    treatment_mask = df['variant'] == 'treatment'
    df.loc[treatment_mask, 'conversion'] = np.random.binomial(1, 0.055, treatment_mask.sum())
    df.loc[treatment_mask, 'revenue'] = np.random.gamma(2.2, 3, treatment_mask.sum())
    
    # Define metrics
    metrics = {
        'Conversion Rate': {'column': 'conversion', 'type': 'binary'},
        'Revenue per User': {'column': 'revenue', 'type': 'continuous'}
    }
    
    # Analyze
    results = analyzer.analyze_test(df, 'variant', metrics, run_validation=True)
    
    print("\nTest Results:")
    print("="*80)
    print(results[['metric', 'test_type', 'pvalue', 'significant', 'relative_lift_pct']])
