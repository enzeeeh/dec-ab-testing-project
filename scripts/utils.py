"""
Utility functions for A/B testing analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any


def load_test_data(file_path: str) -> pd.DataFrame:
    """
    Load test data from CSV file.
    
    Parameters:
    -----------
    file_path : str
        Path to the CSV file
        
    Returns:
    --------
    pd.DataFrame
        Loaded dataframe
    """
    df = pd.read_csv(file_path)
    
    # Convert timestamp to datetime if exists
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    return df


def get_variant_names(df: pd.DataFrame) -> List[str]:
    """
    Extract variant names from dataframe.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Test data
        
    Returns:
    --------
    List[str]
        List of variant names
    """
    return df['variant'].unique().tolist()


def calculate_basic_stats(df: pd.DataFrame, metric: str, variant_col: str = 'variant') -> pd.DataFrame:
    """
    Calculate basic statistics by variant.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Test data
    metric : str
        Metric column name
    variant_col : str
        Variant column name
        
    Returns:
    --------
    pd.DataFrame
        Summary statistics
    """
    stats = df.groupby(variant_col)[metric].agg([
        ('count', 'count'),
        ('mean', 'mean'),
        ('median', 'median'),
        ('std', 'std'),
        ('min', 'min'),
        ('max', 'max')
    ]).round(4)
    
    return stats


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format value as percentage.
    
    Parameters:
    -----------
    value : float
        Value to format
    decimals : int
        Number of decimal places
        
    Returns:
    --------
    str
        Formatted percentage
    """
    return f"{value * 100:.{decimals}f}%"


def get_test_info(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Extract test information from dataframe.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Test data
        
    Returns:
    --------
    Dict[str, Any]
        Dictionary with test information
    """
    info = {
        'total_sessions': len(df),
        'unique_users': df['user_id'].nunique(),
        'variants': df['variant'].unique().tolist(),
        'variant_counts': df['variant'].value_counts().to_dict(),
        'date_range': (df['timestamp'].min(), df['timestamp'].max()) if 'timestamp' in df.columns else None,
        'test_duration_days': (df['timestamp'].max() - df['timestamp'].min()).days + 1 if 'timestamp' in df.columns else None,
        'columns': df.columns.tolist(),
        'device_types': df['device_type'].unique().tolist() if 'device_type' in df.columns else None,
        'regions': df['region'].unique().tolist() if 'region' in df.columns else None,
    }
    
    return info


def print_test_summary(test_name: str, df: pd.DataFrame):
    """
    Print formatted test summary.
    
    Parameters:
    -----------
    test_name : str
        Name of the test
    df : pd.DataFrame
        Test data
    """
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
