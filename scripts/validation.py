"""
Data validation functions for A/B testing analysis
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Tuple, List, Any
import warnings


class ABTestValidator:
    """
    Comprehensive A/B test validation class.
    """
    
    def __init__(self, df: pd.DataFrame, test_name: str, variant_col: str = 'variant'):
        """
        Initialize validator.
        
        Parameters:
        -----------
        df : pd.DataFrame
            Test data
        test_name : str
            Name of the test
        variant_col : str
            Column name for variants
        """
        self.df = df.copy()
        self.test_name = test_name
        self.variant_col = variant_col
        self.validation_results = {}
        
    def run_all_validations(self) -> Dict[str, Any]:
        """
        Run all validation checks.
        
        Returns:
        --------
        Dict[str, Any]
            Validation results
        """
        print(f"\n{'='*70}")
        print(f"RUNNING VALIDATION FOR: {self.test_name}")
        print(f"{'='*70}\n")
        
        # Run all validation checks
        self.check_sample_ratio_mismatch()
        self.check_data_integrity()
        self.check_randomization_balance()
        self.check_temporal_consistency()
        self.check_outliers()
        self.check_sample_size()
        
        # Overall assessment
        self.assess_overall_validity()
        
        return self.validation_results
    
    def check_sample_ratio_mismatch(self, expected_ratio: List[float] = None):
        """
        Check for Sample Ratio Mismatch (SRM).
        
        Parameters:
        -----------
        expected_ratio : List[float]
            Expected ratio for each variant (default: equal split)
        """
        print("1. Sample Ratio Mismatch (SRM) Test")
        print("-" * 70)
        
        variant_counts = self.df[self.variant_col].value_counts().sort_index()
        total = len(self.df)
        
        # Default to equal split if not specified
        if expected_ratio is None:
            n_variants = len(variant_counts)
            expected_ratio = [1/n_variants] * n_variants
        
        expected_counts = [total * ratio for ratio in expected_ratio]
        observed_counts = variant_counts.values
        
        # Chi-square test
        chi2_stat, p_value = stats.chisquare(observed_counts, expected_counts)
        
        # Results
        print(f"\nObserved Distribution:")
        for variant, count in variant_counts.items():
            pct = count / total * 100
            print(f"  {variant}: {count:,} ({pct:.2f}%)")
        
        print(f"\nExpected Distribution:")
        for i, (variant, ratio) in enumerate(zip(variant_counts.index, expected_ratio)):
            expected = total * ratio
            print(f"  {variant}: {expected:,.0f} ({ratio*100:.2f}%)")
        
        print(f"\nChi-square statistic: {chi2_stat:.4f}")
        print(f"P-value: {p_value:.6f}")
        
        # Interpretation
        if p_value < 0.001:
            status = "❌ CRITICAL FAILURE"
            message = "Strong evidence of Sample Ratio Mismatch! Test validity questionable."
        elif p_value < 0.05:
            status = "⚠️ WARNING"
            message = "Possible Sample Ratio Mismatch detected. Investigate further."
        else:
            status = "✅ PASS"
            message = "No Sample Ratio Mismatch detected."
        
        print(f"\nStatus: {status}")
        print(f"Conclusion: {message}")
        print()
        
        self.validation_results['srm'] = {
            'chi2_statistic': chi2_stat,
            'p_value': p_value,
            'status': status,
            'message': message,
            'observed': variant_counts.to_dict(),
            'passed': p_value >= 0.05
        }
    
    def check_data_integrity(self):
        """
        Check data integrity issues.
        """
        print("2. Data Integrity Checks")
        print("-" * 70)
        
        issues = []
        
        # Check for duplicates
        duplicates = self.df.duplicated(subset=['session_id']).sum()
        print(f"\nDuplicate session_ids: {duplicates:,}")
        if duplicates > 0:
            issues.append(f"Found {duplicates} duplicate session IDs")
        
        # Check for missing values
        missing = self.df.isnull().sum()
        missing = missing[missing > 0]
        if len(missing) > 0:
            print(f"\nMissing values detected:")
            for col, count in missing.items():
                pct = count / len(self.df) * 100
                print(f"  {col}: {count:,} ({pct:.2f}%)")
                issues.append(f"{col} has {count} missing values ({pct:.2f}%)")
        else:
            print("\nNo missing values detected ✅")
        
        # Check timestamp validity
        if 'timestamp' in self.df.columns:
            self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
            min_date = self.df['timestamp'].min()
            max_date = self.df['timestamp'].max()
            print(f"\nDate range: {min_date.date()} to {max_date.date()}")
            
            # Check for future dates
            if max_date > pd.Timestamp.now():
                issues.append(f"Future dates detected: {max_date}")
        
        # Check for negative values in metrics that should be positive
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if 'revenue' in col.lower() or 'price' in col.lower():
                negative_count = (self.df[col] < 0).sum()
                if negative_count > 0:
                    print(f"\n⚠️ {col}: {negative_count} negative values detected")
                    issues.append(f"{col} has {negative_count} negative values")
        
        # Overall status
        if len(issues) == 0:
            status = "✅ PASS"
            message = "No data integrity issues detected."
        elif len(issues) <= 2:
            status = "⚠️ WARNING"
            message = f"Minor data quality issues detected: {len(issues)} issue(s)."
        else:
            status = "❌ FAIL"
            message = f"Multiple data quality issues detected: {len(issues)} issue(s)."
        
        print(f"\nStatus: {status}")
        print(f"Conclusion: {message}")
        print()
        
        self.validation_results['data_integrity'] = {
            'duplicates': int(duplicates),
            'missing_values': missing.to_dict() if len(missing) > 0 else {},
            'issues': issues,
            'status': status,
            'message': message,
            'passed': len(issues) == 0
        }
    
    def check_randomization_balance(self):
        """
        Check if randomization is balanced across demographic variables.
        """
        print("3. Randomization Balance Check")
        print("-" * 70)
        
        demographic_vars = ['device_type', 'browser', 'region']
        balance_results = {}
        imbalanced = []
        
        for var in demographic_vars:
            if var not in self.df.columns:
                continue
            
            print(f"\n{var.upper()}:")
            
            # Create contingency table
            contingency = pd.crosstab(self.df[self.variant_col], self.df[var])
            
            # Chi-square test
            chi2, p_value, dof, expected = stats.chi2_contingency(contingency)
            
            # Display distribution
            proportions = contingency.div(contingency.sum(axis=1), axis=0) * 100
            print(proportions.round(2))
            
            print(f"\nChi-square: {chi2:.4f}, p-value: {p_value:.4f}")
            
            if p_value < 0.05:
                print(f"⚠️ Imbalanced distribution detected (p < 0.05)")
                imbalanced.append(var)
            else:
                print(f"✅ Balanced distribution (p >= 0.05)")
            
            balance_results[var] = {
                'chi2': chi2,
                'p_value': p_value,
                'balanced': p_value >= 0.05
            }
        
        # Overall status
        if len(imbalanced) == 0:
            status = "✅ PASS"
            message = "Randomization appears balanced across all demographic variables."
        else:
            status = "⚠️ WARNING"
            message = f"Imbalanced randomization detected in: {', '.join(imbalanced)}. Consider stratified analysis."
        
        print(f"\nStatus: {status}")
        print(f"Conclusion: {message}")
        print()
        
        self.validation_results['randomization_balance'] = {
            'results': balance_results,
            'imbalanced_vars': imbalanced,
            'status': status,
            'message': message,
            'passed': len(imbalanced) == 0
        }
    
    def check_temporal_consistency(self):
        """
        Check temporal consistency of variant split.
        """
        print("4. Temporal Consistency Check")
        print("-" * 70)
        
        if 'timestamp' not in self.df.columns:
            print("⚠️ Timestamp column not found. Skipping temporal check.\n")
            self.validation_results['temporal_consistency'] = {
                'status': 'SKIPPED',
                'message': 'No timestamp data available',
                'passed': True
            }
            return
        
        # Daily variant split
        self.df['date'] = pd.to_datetime(self.df['timestamp']).dt.date
        daily_split = pd.crosstab(self.df['date'], self.df[self.variant_col], normalize='index') * 100
        
        print(f"\nDaily Variant Split (first 10 days):")
        print(daily_split.head(10).round(2))
        
        # Calculate variance in daily split
        variants = self.df[self.variant_col].unique()
        variance_by_variant = {}
        
        for variant in variants:
            variance = daily_split[variant].var()
            variance_by_variant[variant] = variance
            print(f"\nVariance in daily % for {variant}: {variance:.2f}")
        
        # Check if variance is too high (indicating instability)
        max_variance = max(variance_by_variant.values())
        
        if max_variance > 25:  # If daily % varies by more than 5% std dev
            status = "⚠️ WARNING"
            message = "High variance in daily variant split detected. Check for traffic routing issues."
        else:
            status = "✅ PASS"
            message = "Variant split is temporally consistent."
        
        print(f"\nStatus: {status}")
        print(f"Conclusion: {message}")
        print()
        
        self.validation_results['temporal_consistency'] = {
            'daily_variance': variance_by_variant,
            'max_variance': max_variance,
            'status': status,
            'message': message,
            'passed': max_variance <= 25
        }
    
    def check_outliers(self):
        """
        Detect outliers in numeric metrics.
        """
        print("5. Outlier Detection")
        print("-" * 70)
        
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        metric_cols = [col for col in numeric_cols if col not in ['session_id', 'user_id']]
        
        outlier_summary = {}
        
        for col in metric_cols[:5]:  # Check first 5 numeric columns
            # IQR method
            Q1 = self.df[col].quantile(0.25)
            Q3 = self.df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = self.df[(self.df[col] < lower_bound) | (self.df[col] > upper_bound)]
            n_outliers = len(outliers)
            pct_outliers = n_outliers / len(self.df) * 100
            
            print(f"\n{col}:")
            print(f"  Range: [{self.df[col].min():.2f}, {self.df[col].max():.2f}]")
            print(f"  IQR bounds: [{lower_bound:.2f}, {upper_bound:.2f}]")
            print(f"  Outliers: {n_outliers:,} ({pct_outliers:.2f}%)")
            
            outlier_summary[col] = {
                'n_outliers': n_outliers,
                'pct_outliers': pct_outliers,
                'lower_bound': lower_bound,
                'upper_bound': upper_bound
            }
        
        # Overall assessment
        max_outlier_pct = max([v['pct_outliers'] for v in outlier_summary.values()])
        
        if max_outlier_pct > 10:
            status = "⚠️ WARNING"
            message = f"High percentage of outliers detected ({max_outlier_pct:.2f}%). Consider winsorization."
        else:
            status = "✅ PASS"
            message = "Outlier levels are within acceptable range."
        
        print(f"\nStatus: {status}")
        print(f"Conclusion: {message}")
        print()
        
        self.validation_results['outliers'] = {
            'summary': outlier_summary,
            'max_outlier_pct': max_outlier_pct,
            'status': status,
            'message': message,
            'passed': max_outlier_pct <= 10
        }
    
    def check_sample_size(self, desired_power: float = 0.8, alpha: float = 0.05, mde: float = 0.05):
        """
        Check if sample size is adequate.
        
        Parameters:
        -----------
        desired_power : float
            Desired statistical power
        alpha : float
            Significance level
        mde : float
            Minimum detectable effect (relative)
        """
        print("6. Sample Size Adequacy Check")
        print("-" * 70)
        
        variant_counts = self.df[self.variant_col].value_counts()
        min_sample = variant_counts.min()
        
        print(f"\nSample sizes by variant:")
        for variant, count in variant_counts.items():
            print(f"  {variant}: {count:,}")
        
        print(f"\nSmallest variant: {min_sample:,} samples")
        
        # Rough sample size calculation for conversion rate test
        # Using simplified formula: n ≈ 16 * (1/mde)^2 for 80% power, α=0.05
        required_per_variant = int(16 / (mde ** 2))
        
        print(f"\nFor {mde*100}% MDE with {desired_power*100}% power:")
        print(f"  Required per variant: ~{required_per_variant:,}")
        print(f"  Actual minimum: {min_sample:,}")
        
        if min_sample >= required_per_variant:
            status = "✅ PASS"
            message = f"Sample size is adequate for detecting {mde*100}% effect."
        elif min_sample >= required_per_variant * 0.7:
            status = "⚠️ WARNING"
            message = f"Sample size may be underpowered. Can detect ~{np.sqrt(16/min_sample)*100:.1f}% effect."
        else:
            status = "❌ UNDERPOWERED"
            message = f"Sample size is too small. Can only detect ~{np.sqrt(16/min_sample)*100:.1f}% effect."
        
        print(f"\nStatus: {status}")
        print(f"Conclusion: {message}")
        print()
        
        self.validation_results['sample_size'] = {
            'variant_counts': variant_counts.to_dict(),
            'min_sample': int(min_sample),
            'required_sample': required_per_variant,
            'status': status,
            'message': message,
            'passed': min_sample >= required_per_variant * 0.7
        }
    
    def assess_overall_validity(self):
        """
        Provide overall assessment of test validity.
        """
        print("\n" + "="*70)
        print("OVERALL VALIDATION SUMMARY")
        print("="*70 + "\n")
        
        # Count passes and failures
        critical_checks = ['srm', 'data_integrity']
        important_checks = ['randomization_balance', 'temporal_consistency']
        
        critical_passed = all([self.validation_results[check].get('passed', False) 
                              for check in critical_checks if check in self.validation_results])
        
        important_issues = [check for check in important_checks 
                           if check in self.validation_results and not self.validation_results[check].get('passed', True)]
        
        # Summary table
        print(f"{'Check':<30} {'Status':<20} {'Result'}")
        print("-" * 70)
        
        for check, results in self.validation_results.items():
            if check != 'overall':
                status = results.get('status', 'UNKNOWN')
                passed = '✅' if results.get('passed', False) else '⚠️' if 'WARNING' in status else '❌'
                print(f"{check.replace('_', ' ').title():<30} {status:<20} {passed}")
        
        # Overall verdict
        print("\n" + "="*70)
        
        if critical_passed and len(important_issues) == 0:
            overall_status = "✅ VALID"
            overall_message = "Test passes all validation checks. Proceed with statistical analysis."
            recommendation = "GREEN LIGHT: Continue to statistical testing."
        elif critical_passed and len(important_issues) <= 1:
            overall_status = "⚠️ PROCEED WITH CAUTION"
            overall_message = f"Test has minor issues in: {', '.join(important_issues)}. Consider stratified analysis."
            recommendation = "YELLOW LIGHT: Proceed with statistical testing but note limitations."
        else:
            overall_status = "❌ QUESTIONABLE"
            overall_message = "Test has significant validity issues. Results may not be trustworthy."
            recommendation = "RED LIGHT: Fix issues before proceeding or consider test invalid."
        
        print(f"\nOVERALL STATUS: {overall_status}")
        print(f"Assessment: {overall_message}")
        print(f"Recommendation: {recommendation}")
        print("\n" + "="*70 + "\n")
        
        self.validation_results['overall'] = {
            'status': overall_status,
            'message': overall_message,
            'recommendation': recommendation,
            'critical_passed': critical_passed,
            'important_issues': important_issues
        }


def save_validation_report(validation_results: Dict[str, Any], test_name: str, output_path: str):
    """
    Save validation results to a text file.
    
    Parameters:
    -----------
    validation_results : Dict
        Validation results from ABTestValidator
    test_name : str
        Name of the test
    output_path : str
        Path to save the report
    """
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
    
    print(f"✅ Validation report saved to: {output_path}")
