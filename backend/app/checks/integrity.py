"""
Integrity checks: referential presence validation.
"""
import pandas as pd
from typing import Dict, Any, List, Optional


def check_referential_integrity(df: pd.DataFrame, 
                                reference_data: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
    """
    Check if foreign key values exist in reference data.
    """
    results = []
    
    # Check merchant_id if merchant reference exists
    if 'merchants' in reference_data:
        merchant_cols = [col for col in df.columns if 'merchant' in col.lower() and 'id' in col.lower()]
        if merchant_cols:
            merchant_col = merchant_cols[0]
            ref_df = reference_data['merchants']
            ref_id_col = [col for col in ref_df.columns if 'id' in col.lower()][0] if any('id' in col.lower() for col in ref_df.columns) else ref_df.columns[0]
            
            valid_ids = set(ref_df[ref_id_col].astype(str))
            df_ids = df[merchant_col].astype(str)
            
            missing_mask = ~df_ids.isin(valid_ids) & ~df_ids.isna()
            missing_count = missing_mask.sum()
            missing_rate = missing_count / len(df) if len(df) > 0 else 0
            
            results.append({
                "check_id": "integrity_merchant_reference",
                "passed": missing_count == 0,
                "severity": "high" if missing_rate > 0.01 else "medium" if missing_rate > 0 else "low",
                "metrics": {
                    "column": merchant_col,
                    "reference_table": "merchants",
                    "missing_count": int(missing_count),
                    "missing_rate": float(missing_rate),
                    "total_unique_values": int(df_ids.nunique())
                }
            })
    
    # Check customer_id if customer reference exists
    if 'customers' in reference_data:
        customer_cols = [col for col in df.columns if 'customer' in col.lower() and 'id' in col.lower()]
        if customer_cols:
            customer_col = customer_cols[0]
            ref_df = reference_data['customers']
            ref_id_col = [col for col in ref_df.columns if 'id' in col.lower()][0] if any('id' in col.lower() for col in ref_df.columns) else ref_df.columns[0]
            
            valid_ids = set(ref_df[ref_id_col].astype(str))
            df_ids = df[customer_col].astype(str)
            
            missing_mask = ~df_ids.isin(valid_ids) & ~df_ids.isna()
            missing_count = missing_mask.sum()
            missing_rate = missing_count / len(df) if len(df) > 0 else 0
            
            results.append({
                "check_id": "integrity_customer_reference",
                "passed": missing_count == 0,
                "severity": "high" if missing_rate > 0.01 else "medium" if missing_rate > 0 else "low",
                "metrics": {
                    "column": customer_col,
                    "reference_table": "customers",
                    "missing_count": int(missing_count),
                    "missing_rate": float(missing_rate),
                    "total_unique_values": int(df_ids.nunique())
                }
            })
    
    # If no reference data, return a pass
    if not results:
        results.append({
            "check_id": "integrity_referential",
            "passed": True,
            "severity": "low",
            "metrics": {"message": "No reference data provided for integrity checks"}
        })
    
    return results


def run_integrity_checks(df: pd.DataFrame, profile: Dict[str, Any],
                        reference_data: Optional[Dict[str, pd.DataFrame]] = None) -> List[Dict[str, Any]]:
    """Run all integrity checks."""
    if reference_data is None:
        reference_data = {}
    
    return check_referential_integrity(df, reference_data)
