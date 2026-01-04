"""
Completeness checks: null rates and required fields validation.
"""
import pandas as pd
from typing import Dict, Any, List


def check_null_rates(df: pd.DataFrame, profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check null rates for all columns.
    Returns metrics about missing data.
    """
    null_rates = {}
    failing_columns = []
    
    for col in df.columns:
        null_count = df[col].isna().sum()
        null_rate = null_count / len(df) if len(df) > 0 else 0
        null_rates[col] = {
            "null_count": int(null_count),
            "null_rate": float(null_rate)
        }
        
        # Flag columns with >5% null rate as concerning
        if null_rate > 0.05:
            failing_columns.append({
                "column": col,
                "null_rate": float(null_rate)
            })
    
    overall_null_rate = df.isna().sum().sum() / (len(df) * len(df.columns)) if len(df) > 0 else 0
    
    return {
        "check_id": "completeness_null_rates",
        "passed": overall_null_rate < 0.05,
        "severity": "high" if overall_null_rate > 0.10 else "medium" if overall_null_rate > 0.05 else "low",
        "metrics": {
            "overall_null_rate": float(overall_null_rate),
            "null_rates_by_column": null_rates,
            "failing_columns": failing_columns,
            "total_missing_values": int(df.isna().sum().sum())
        }
    }


def check_required_fields(df: pd.DataFrame, required_fields: List[str] = None) -> Dict[str, Any]:
    """
    Check that required fields are present and non-null.
    Auto-infers critical fields if not specified.
    """
    if required_fields is None:
        # Auto-infer required fields for payments data
        required_fields = []
        for col in df.columns:
            col_lower = col.lower()
            # Critical payment fields
            if any(keyword in col_lower for keyword in [
                'txn_id', 'transaction_id', 'event_id', 'id',
                'amount', 'currency', 'status'
            ]):
                required_fields.append(col)
    
    missing_fields = [field for field in required_fields if field not in df.columns]
    
    field_completeness = {}
    failing_fields = []
    
    for field in required_fields:
        if field in df.columns:
            null_count = df[field].isna().sum()
            null_rate = null_count / len(df) if len(df) > 0 else 0
            field_completeness[field] = {
                "null_count": int(null_count),
                "null_rate": float(null_rate),
                "present": True
            }
            
            if null_rate > 0:
                failing_fields.append({
                    "field": field,
                    "null_rate": float(null_rate)
                })
        else:
            field_completeness[field] = {
                "present": False
            }
    
    passed = len(missing_fields) == 0 and len(failing_fields) == 0
    
    return {
        "check_id": "completeness_required_fields",
        "passed": passed,
        "severity": "critical" if len(missing_fields) > 0 or len(failing_fields) > 0 else "low",
        "metrics": {
            "required_fields": required_fields,
            "missing_fields": missing_fields,
            "field_completeness": field_completeness,
            "failing_fields": failing_fields
        }
    }


def run_completeness_checks(df: pd.DataFrame, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Run all completeness checks."""
    return [
        check_null_rates(df, profile),
        check_required_fields(df)
    ]
