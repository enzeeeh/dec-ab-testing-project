"""
Statistical Testing Framework for A/B Tests

This module provides comprehensive statistical analysis for A/B testing,
including automatic test selection, execution, and multiple testing correction.

Key Features:
- Auto-detection of metric type (binary, continuous, count, categorical)
- Appropriate test selection based on data distribution and variant count
- Multiple testing correction (Bonferroni, Holm, BH-FDR)
- Effect size calculations
- Confidence interval estimation
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import mannwhitneyu, kruskal, chi2_contingency
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import proportions_ztest
from typing import Dict, List, Tuple, Optional, Union
import warnings
warnings.filterwarnings('ignore')


class MetricType:
    """Enum for metric types"""
    BINARY = "binary"
    CONTINUOUS = "continuous"
    COUNT = "count"
    CATEGORICAL = "categorical"


class StatisticalAnalyzer:
    """
    Main class for A/B test statistical analysis.
    
    Handles test selection, execution, and interpretation for different
    metric types and experiment designs.
    """
    
    def __init__(self, alpha: float = 0.05):
        """
        Initialize analyzer.
        
        Parameters:
        -----------
        alpha : float
            Significance level (default: 0.05)
        """
        self.alpha = alpha
    
    
    def detect_metric_type(self, 
                          data: pd.Series, 
                          metric_name: str = None) -> str:
        """
        Automatically detect metric type from data.
        
        Parameters:
        -----------
        data : pd.Series
            Metric values
        metric_name : str, optional
            Name of metric (helps with detection)
            
        Returns:
        --------
        str : One of 'binary', 'continuous', 'count', 'categorical'
        """
        unique_vals = data.nunique()
        
        # Check if binary (0/1 or True/False)
        if unique_vals == 2 and set(data.dropna().unique()).issubset({0, 1, True, False}):
            return MetricType.BINARY
        
        # Check if categorical (non-numeric or few unique string values)
        if data.dtype == 'object' or data.dtype.name == 'category':
            return MetricType.CATEGORICAL
        
        # Check if count data (non-negative integers)
        if data.dtype in ['int64', 'int32'] and (data >= 0).all():
            # If mostly small integers, likely count data
            if data.max() < 20 and unique_vals < 15:
                return MetricType.COUNT
        
        # Check common metric name patterns
        if metric_name:
            metric_lower = metric_name.lower()
            if any(word in metric_lower for word in ['converted', 'conversion', 'clicked', 'bounced', 'registered']):
                return MetricType.BINARY
            if any(word in metric_lower for word in ['count', 'views', 'visits', 'items', 'products']):
                return MetricType.COUNT
        
        # Default to continuous
        return MetricType.CONTINUOUS
    
    
    def check_normality(self, data: pd.Series, sample_threshold: int = 5000) -> Dict:
        """
        Check if data is normally distributed.
        
        Uses Shapiro-Wilk for small samples (<5000), Anderson-Darling for larger.
        
        Parameters:
        -----------
        data : pd.Series
            Data to test
        sample_threshold : int
            Threshold for choosing test type
            
        Returns:
        --------
        dict : Contains test results and interpretation
        """
        clean_data = data.dropna()
        n = len(clean_data)
        
        result = {
            'is_normal': False,
            'test_used': None,
            'statistic': None,
            'p_value': None,
            'skewness': stats.skew(clean_data),
            'kurtosis': stats.kurtosis(clean_data)
        }
        
        # For small samples, use Shapiro-Wilk
        if n < sample_threshold:
            stat, p_value = stats.shapiro(clean_data)
            result['test_used'] = 'Shapiro-Wilk'
            result['statistic'] = stat
            result['p_value'] = p_value
            result['is_normal'] = p_value > 0.05
        else:
            # For large samples, use Anderson-Darling
            ad_result = stats.anderson(clean_data)
            result['test_used'] = 'Anderson-Darling'
            result['statistic'] = ad_result.statistic
            # Use 5% critical value
            result['is_normal'] = ad_result.statistic < ad_result.critical_values[2]
        
        # Check for severe skewness
        if abs(result['skewness']) > 2:
            result['is_normal'] = False
            result['note'] = 'Severe skewness detected'
        
        return result
    
    
    def two_proportion_test(self, 
                           df: pd.DataFrame, 
                           metric: str, 
                           variant_col: str = 'variant') -> Dict:
        """
        Two-sample proportion test (Z-test) for binary metrics.
        
        Compares conversion rates, click-through rates, etc. between two variants.
        
        Parameters:
        -----------
        df : pd.DataFrame
            Experiment data
        metric : str
            Binary metric column name
        variant_col : str
            Variant column name
            
        Returns:
        --------
        dict : Test results including p-value, effect size, CI
        """
        variants = df[variant_col].unique()
        if len(variants) != 2:
            raise ValueError("Two-proportion test requires exactly 2 variants")
        
        # Get counts for each variant
        group_A = df[df[variant_col] == variants[0]]
        group_B = df[df[variant_col] == variants[1]]
        
        count_A = group_A[metric].sum()
        count_B = group_B[metric].sum()
        nobs_A = len(group_A)
        nobs_B = len(group_B)
        
        # Calculate proportions
        prop_A = count_A / nobs_A
        prop_B = count_B / nobs_B
        
        # Run two-proportion z-test
        counts = np.array([count_A, count_B])
        nobs = np.array([nobs_A, nobs_B])
        
        z_stat, p_value = proportions_ztest(counts, nobs)
        
        # Calculate pooled proportion for SE
        pooled_prop = (count_A + count_B) / (nobs_A + nobs_B)
        se = np.sqrt(pooled_prop * (1 - pooled_prop) * (1/nobs_A + 1/nobs_B))
        
        # Confidence interval for difference
        diff = prop_B - prop_A
        ci_margin = 1.96 * se
        ci_lower = diff - ci_margin
        ci_upper = diff + ci_margin
        
        # Effect size (absolute and relative)
        absolute_lift = diff
        relative_lift = (diff / prop_A) if prop_A > 0 else np.nan
        
        return {
            'test_type': 'Two-Proportion Z-Test',
            'metric': metric,
            'variant_A': str(variants[0]),
            'variant_B': str(variants[1]),
            'n_A': nobs_A,
            'n_B': nobs_B,
            'successes_A': int(count_A),
            'successes_B': int(count_B),
            'rate_A': prop_A,
            'rate_B': prop_B,
            'z_statistic': z_stat,
            'p_value': p_value,
            'significant': p_value < self.alpha,
            'absolute_difference': absolute_lift,
            'relative_lift': relative_lift,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'interpretation': self._interpret_proportion_test(prop_A, prop_B, p_value, relative_lift)
        }
    
    
    def welch_t_test(self, 
                     df: pd.DataFrame, 
                     metric: str, 
                     variant_col: str = 'variant') -> Dict:
        """
        Welch's t-test for continuous metrics with unequal variances.
        
        Appropriate for revenue, time-on-site, etc. when data is approximately normal.
        
        Parameters:
        -----------
        df : pd.DataFrame
            Experiment data
        metric : str
            Continuous metric column name
        variant_col : str
            Variant column name
            
        Returns:
        --------
        dict : Test results
        """
        variants = df[variant_col].unique()
        if len(variants) != 2:
            raise ValueError("Welch's t-test requires exactly 2 variants")
        
        group_A = df[df[variant_col] == variants[0]][metric].dropna()
        group_B = df[df[variant_col] == variants[1]][metric].dropna()
        
        # Perform Welch's t-test (equal_var=False)
        t_stat, p_value = stats.ttest_ind(group_A, group_B, equal_var=False)
        
        # Calculate statistics
        mean_A = group_A.mean()
        mean_B = group_B.mean()
        std_A = group_A.std()
        std_B = group_B.std()
        n_A = len(group_A)
        n_B = len(group_B)
        
        # Effect size (Cohen's d)
        pooled_std = np.sqrt(((n_A - 1) * std_A**2 + (n_B - 1) * std_B**2) / (n_A + n_B - 2))
        cohens_d = (mean_B - mean_A) / pooled_std if pooled_std > 0 else 0
        
        # Confidence interval
        se = np.sqrt(std_A**2/n_A + std_B**2/n_B)
        df_welch = (std_A**2/n_A + std_B**2/n_B)**2 / (
            (std_A**2/n_A)**2/(n_A-1) + (std_B**2/n_B)**2/(n_B-1)
        )
        t_crit = stats.t.ppf(1 - self.alpha/2, df_welch)
        diff = mean_B - mean_A
        ci_lower = diff - t_crit * se
        ci_upper = diff + t_crit * se
        
        return {
            'test_type': "Welch's t-test",
            'metric': metric,
            'variant_A': str(variants[0]),
            'variant_B': str(variants[1]),
            'n_A': n_A,
            'n_B': n_B,
            'mean_A': mean_A,
            'mean_B': mean_B,
            'std_A': std_A,
            'std_B': std_B,
            't_statistic': t_stat,
            'p_value': p_value,
            'degrees_of_freedom': df_welch,
            'significant': p_value < self.alpha,
            'mean_difference': diff,
            'cohens_d': cohens_d,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'interpretation': self._interpret_continuous_test(mean_A, mean_B, p_value, cohens_d)
        }
    
    
    def mann_whitney_test(self, 
                         df: pd.DataFrame, 
                         metric: str, 
                         variant_col: str = 'variant') -> Dict:
        """
        Mann-Whitney U test for skewed continuous metrics.
        
        Non-parametric test that compares distributions using ranks.
        Robust to outliers, ideal for revenue data.
        
        Parameters:
        -----------
        df : pd.DataFrame
            Experiment data
        metric : str
            Continuous metric column name
        variant_col : str
            Variant column name
            
        Returns:
        --------
        dict : Test results
        """
        variants = df[variant_col].unique()
        if len(variants) != 2:
            raise ValueError("Mann-Whitney test requires exactly 2 variants")
        
        group_A = df[df[variant_col] == variants[0]][metric].dropna()
        group_B = df[df[variant_col] == variants[1]][metric].dropna()
        
        # Perform Mann-Whitney U test
        u_stat, p_value = mannwhitneyu(group_A, group_B, alternative='two-sided')
        
        # Calculate descriptive statistics
        median_A = group_A.median()
        median_B = group_B.median()
        mean_A = group_A.mean()
        mean_B = group_B.mean()
        n_A = len(group_A)
        n_B = len(group_B)
        
        # Effect size (rank-biserial correlation)
        r = 1 - (2*u_stat) / (n_A * n_B)
        
        return {
            'test_type': 'Mann-Whitney U Test',
            'metric': metric,
            'variant_A': str(variants[0]),
            'variant_B': str(variants[1]),
            'n_A': n_A,
            'n_B': n_B,
            'median_A': median_A,
            'median_B': median_B,
            'mean_A': mean_A,
            'mean_B': mean_B,
            'u_statistic': u_stat,
            'p_value': p_value,
            'significant': p_value < self.alpha,
            'rank_biserial_r': r,
            'median_difference': median_B - median_A,
            'mean_difference': mean_B - mean_A,
            'interpretation': self._interpret_mann_whitney(median_A, median_B, p_value, r)
        }
    
    
    def kruskal_wallis_test(self, 
                           df: pd.DataFrame, 
                           metric: str, 
                           variant_col: str = 'variant') -> Dict:
        """
        Kruskal-Wallis H-test for comparing 3+ variants (non-parametric).
        
        Extension of Mann-Whitney for multiple groups.
        
        Parameters:
        -----------
        df : pd.DataFrame
            Experiment data
        metric : str
            Continuous metric column name
        variant_col : str
            Variant column name
            
        Returns:
        --------
        dict : Test results with post-hoc pairwise comparisons
        """
        variants = df[variant_col].unique()
        if len(variants) < 3:
            raise ValueError("Kruskal-Wallis requires 3+ variants")
        
        # Prepare groups
        groups = [df[df[variant_col] == v][metric].dropna() for v in variants]
        
        # Perform Kruskal-Wallis test
        h_stat, p_value = kruskal(*groups)
        
        # Calculate descriptive stats per variant
        variant_stats = {}
        for v in variants:
            data = df[df[variant_col] == v][metric].dropna()
            variant_stats[str(v)] = {
                'n': len(data),
                'median': data.median(),
                'mean': data.mean(),
                'std': data.std()
            }
        
        # Post-hoc pairwise Mann-Whitney tests
        pairwise_results = []
        variant_list = list(variants)
        for i in range(len(variant_list)):
            for j in range(i+1, len(variant_list)):
                v1, v2 = variant_list[i], variant_list[j]
                g1 = df[df[variant_col] == v1][metric].dropna()
                g2 = df[df[variant_col] == v2][metric].dropna()
                u_stat, p_val = mannwhitneyu(g1, g2, alternative='two-sided')
                pairwise_results.append({
                    'variant_1': str(v1),
                    'variant_2': str(v2),
                    'p_value': p_val,
                    'median_1': g1.median(),
                    'median_2': g2.median()
                })
        
        return {
            'test_type': 'Kruskal-Wallis H-Test',
            'metric': metric,
            'n_variants': len(variants),
            'variants': [str(v) for v in variants],
            'h_statistic': h_stat,
            'p_value': p_value,
            'significant': p_value < self.alpha,
            'variant_stats': variant_stats,
            'pairwise_comparisons': pairwise_results,
            'interpretation': self._interpret_kruskal(p_value, pairwise_results)
        }
    
    
    def chi_square_test(self, 
                       df: pd.DataFrame, 
                       metric: str, 
                       variant_col: str = 'variant') -> Dict:
        """
        Chi-square test for categorical outcomes.
        
        Tests independence between variant and categorical outcome.
        
        Parameters:
        -----------
        df : pd.DataFrame
            Experiment data
        metric : str
            Categorical metric column name
        variant_col : str
            Variant column name
            
        Returns:
        --------
        dict : Test results including Cramér's V effect size
        """
        # Create contingency table
        contingency = pd.crosstab(df[variant_col], df[metric])
        
        # Perform chi-square test
        chi2, p_value, dof, expected = chi2_contingency(contingency)
        
        # Calculate Cramér's V effect size
        n = contingency.sum().sum()
        min_dim = min(contingency.shape) - 1
        cramers_v = np.sqrt(chi2 / (n * min_dim)) if min_dim > 0 else 0
        
        return {
            'test_type': 'Chi-Square Test',
            'metric': metric,
            'chi2_statistic': chi2,
            'p_value': p_value,
            'degrees_of_freedom': dof,
            'significant': p_value < self.alpha,
            'cramers_v': cramers_v,
            'contingency_table': contingency.to_dict(),
            'interpretation': self._interpret_chi_square(p_value, cramers_v)
        }
    
    
    def select_and_run_test(self, 
                           df: pd.DataFrame, 
                           metric: str, 
                           variant_col: str = 'variant',
                           force_test: str = None) -> Dict:
        """
        Automatically select and run the appropriate statistical test.
        
        Decision logic:
        1. Detect metric type
        2. Check number of variants
        3. For continuous: check normality and skewness
        4. Select appropriate test
        5. Run test and return results
        
        Parameters:
        -----------
        df : pd.DataFrame
            Experiment data
        metric : str
            Metric column name
        variant_col : str
            Variant column name
        force_test : str, optional
            Force a specific test type
            
        Returns:
        --------
        dict : Test results with metadata
        """
        variant_count = df[variant_col].nunique()
        metric_type = self.detect_metric_type(df[metric], metric)
        
        result = {
            'metric': metric,
            'metric_type': metric_type,
            'n_variants': variant_count,
            'total_n': len(df)
        }
        
        # Binary metrics
        if metric_type == MetricType.BINARY:
            if variant_count == 2:
                test_result = self.two_proportion_test(df, metric, variant_col)
            else:
                # For 3+ variants, use chi-square
                test_result = self.chi_square_test(df, metric, variant_col)
        
        # Continuous metrics
        elif metric_type == MetricType.CONTINUOUS:
            normality = self.check_normality(df[metric])
            result['normality_check'] = normality
            
            # Decide between parametric and non-parametric
            if normality['is_normal'] and abs(normality['skewness']) < 1:
                # Use parametric tests
                if variant_count == 2:
                    test_result = self.welch_t_test(df, metric, variant_col)
                else:
                    # Would use ANOVA here, but for robustness use Kruskal-Wallis
                    test_result = self.kruskal_wallis_test(df, metric, variant_col)
            else:
                # Use non-parametric tests for skewed data
                if variant_count == 2:
                    test_result = self.mann_whitney_test(df, metric, variant_col)
                else:
                    test_result = self.kruskal_wallis_test(df, metric, variant_col)
        
        # Count metrics (treat as continuous but prefer non-parametric)
        elif metric_type == MetricType.COUNT:
            if variant_count == 2:
                test_result = self.mann_whitney_test(df, metric, variant_col)
            else:
                test_result = self.kruskal_wallis_test(df, metric, variant_col)
        
        # Categorical metrics
        else:
            test_result = self.chi_square_test(df, metric, variant_col)
        
        result.update(test_result)
        return result
    
    
    def multiple_testing_correction(self, 
                                    p_values: List[float], 
                                    method: str = 'holm') -> Dict:
        """
        Apply multiple testing correction.
        
        Parameters:
        -----------
        p_values : list
            List of p-values from multiple tests
        method : str
            Correction method: 'bonferroni', 'holm', 'fdr_bh'
            
        Returns:
        --------
        dict : Corrected p-values and rejection decisions
        """
        reject, pvals_corrected, _, _ = multipletests(
            p_values, 
            alpha=self.alpha, 
            method=method
        )
        
        return {
            'method': method,
            'n_tests': len(p_values),
            'original_alpha': self.alpha,
            'adjusted_alpha': self.alpha / len(p_values) if method == 'bonferroni' else None,
            'original_p_values': p_values,
            'corrected_p_values': pvals_corrected.tolist(),
            'reject_null': reject.tolist(),
            'n_significant': sum(reject)
        }
    
    
    # ========================================================================
    # Helper Methods for Interpretation
    # ========================================================================
    
    def _interpret_proportion_test(self, rate_A, rate_B, p_value, relative_lift):
        """Generate interpretation for proportion test."""
        if p_value >= self.alpha:
            return f"No significant difference (p={p_value:.4f}). Cannot conclude variant B differs from A."
        
        direction = "higher" if rate_B > rate_A else "lower"
        return (f"Variant B has significantly {direction} rate (p={p_value:.4f}). "
                f"Relative lift: {relative_lift*100:.2f}%")
    
    def _interpret_continuous_test(self, mean_A, mean_B, p_value, cohens_d):
        """Generate interpretation for continuous test."""
        if p_value >= self.alpha:
            return f"No significant difference (p={p_value:.4f})."
        
        direction = "higher" if mean_B > mean_A else "lower"
        effect = "small" if abs(cohens_d) < 0.5 else "medium" if abs(cohens_d) < 0.8 else "large"
        return (f"Variant B has significantly {direction} mean (p={p_value:.4f}). "
                f"Effect size: {effect} (Cohen's d={cohens_d:.3f})")
    
    def _interpret_mann_whitney(self, median_A, median_B, p_value, r):
        """Generate interpretation for Mann-Whitney test."""
        if p_value >= self.alpha:
            return f"No significant difference in distributions (p={p_value:.4f})."
        
        direction = "higher" if median_B > median_A else "lower"
        return (f"Variant B has significantly {direction} median (p={p_value:.4f}). "
                f"Effect size r={r:.3f}")
    
    def _interpret_kruskal(self, p_value, pairwise_results):
        """Generate interpretation for Kruskal-Wallis test."""
        if p_value >= self.alpha:
            return f"No significant difference among variants (p={p_value:.4f})."
        
        sig_pairs = [p for p in pairwise_results if p['p_value'] < self.alpha]
        return (f"Significant difference detected (p={p_value:.4f}). "
                f"{len(sig_pairs)} pairwise comparison(s) significant.")
    
    def _interpret_chi_square(self, p_value, cramers_v):
        """Generate interpretation for chi-square test."""
        if p_value >= self.alpha:
            return f"No association between variant and outcome (p={p_value:.4f})."
        
        strength = "weak" if cramers_v < 0.1 else "moderate" if cramers_v < 0.3 else "strong"
        return (f"Significant association found (p={p_value:.4f}). "
                f"Effect: {strength} (Cramér's V={cramers_v:.3f})")
