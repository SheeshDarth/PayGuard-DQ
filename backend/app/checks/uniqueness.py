"""
Uniqueness checks: duplicate detection on inferred keys.
"""
import pandas as pd
from typing import Dict, Any, List


def infer_key_columns(df: pd.DataFrame, profile: Dict[str, Any]) -> List[str]:
    """
    Infer potential key columns based on naming and cardinality.
    """
    key_columns = []
    
    for col in df.columns:
        col_lower = col.lower()
        
        # Check for ID-like naming
        if any(keyword in col_lower for keyword in [
            'id', 'key', 'uuid', 'guid', 'reference', 'ref'
        ]):
            # Check cardinality - should be high for a key
            unique_count = df[col].nunique()
            total_count = len(df)
            uniqueness_ratio = unique_count / total_count if total_count > 0 else 0
            
            # If >95% unique, likely a key
            if uniqueness_ratio > 0.95:
                key_columns.append(col)
    
    # Fallback: if no keys found, use first column if it's high cardinality
    if not key_columns and len(df.columns) > 0:
        first_col = df.columns[0]
        unique_count = df[first_col].nunique()
        total_count = len(df)
        if unique_count / total_count > 0.95:
            key_columns.append(first_col)
    
    return key_columns


def check_duplicates(df: pd.DataFrame, key_columns: List[str]) -> Dict[str, Any]:
    """
    Check for duplicate values in key columns.
    """
    if not key_columns:
        return {
            "check_id": "uniqueness_duplicates",
            "passed": True,
            "severity": "low",
            "metrics": {
                "message": "No key columns identified",
                "key_columns": []
            }
        }
    
    duplicate_info = {}
    total_duplicates = 0
    failing_columns = []
    
    for col in key_columns:
        if col in df.columns:
            duplicates = df[col].duplicated()
            dup_count = duplicates.sum()
            dup_rate = dup_count / len(df) if len(df) > 0 else 0
            
            duplicate_info[col] = {
                "duplicate_count": int(dup_count),
                "duplicate_rate": float(dup_rate),
                "unique_count": int(df[col].nunique()),
                "total_count": int(len(df))
            }
            
            total_duplicates += dup_count
            
            if dup_rate > 0:
                failing_columns.append({
                    "column": col,
                    "duplicate_rate": float(dup_rate),
                    "duplicate_count": int(dup_count)
                })
    
    overall_dup_rate = total_duplicates / (len(df) * len(key_columns)) if len(df) > 0 and key_columns else 0
    passed = overall_dup_rate == 0
    
    return {
        "check_id": "uniqueness_duplicates",
        "passed": passed,
        "severity": "critical" if overall_dup_rate > 0.01 else "high" if overall_dup_rate > 0 else "low",
        "metrics": {
            "key_columns": key_columns,
            "overall_duplicate_rate": float(overall_dup_rate),
            "duplicate_info": duplicate_info,
            "failing_columns": failing_columns
        }
    }


def run_uniqueness_checks(df: pd.DataFrame, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Run all uniqueness checks."""
    key_columns = infer_key_columns(df, profile)
    return [
        check_duplicates(df, key_columns)
    ]
