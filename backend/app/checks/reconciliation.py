"""
Reconciliation checks: match-rate validation against reference truth.
This is the payments-specific differentiator dimension.
"""
import pandas as pd
from typing import Dict, Any, List, Optional


def check_bin_reconciliation(df: pd.DataFrame, bin_reference: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """
    Validate BIN (Bank Identification Number) against reference mapping.
    Checks if card BIN maps to correct issuer/network.
    """
    if bin_reference is None:
        return {
            "check_id": "reconciliation_bin",
            "passed": True,
            "severity": "low",
            "metrics": {"message": "No BIN reference data provided"}
        }
    
    # Find card number or BIN column
    card_cols = [col for col in df.columns if any(keyword in col.lower() 
                 for keyword in ['card', 'pan', 'bin'])]
    
    if not card_cols:
        return {
            "check_id": "reconciliation_bin",
            "passed": True,
            "severity": "low",
            "metrics": {"message": "No card/BIN columns found"}
        }
    
    card_col = card_cols[0]
    
    # Extract BIN (first 6 digits)
    bins = df[card_col].astype(str).str[:6]
    
    # Build BIN reference mapping
    if 'bin' not in bin_reference.columns:
        return {
            "check_id": "reconciliation_bin",
            "passed": True,
            "severity": "low",
            "metrics": {"message": "BIN reference format invalid"}
        }
    
    valid_bins = set(bin_reference['bin'].astype(str))
    
    # Check match rate
    matched_mask = bins.isin(valid_bins)
    unmatched_count = (~matched_mask & ~bins.isna()).sum()
    match_rate = matched_mask.sum() / len(df) if len(df) > 0 else 0
    
    # Get sample unmatched BINs
    unmatched_bins = bins[~matched_mask & ~bins.isna()].unique().tolist()[:10]
    
    passed = match_rate > 0.95  # Expect >95% match rate
    
    return {
        "check_id": "reconciliation_bin",
        "passed": passed,
        "severity": "high" if match_rate < 0.90 else "medium" if match_rate < 0.95 else "low",
        "metrics": {
            "card_column": card_col,
            "match_rate": float(match_rate),
            "matched_count": int(matched_mask.sum()),
            "unmatched_count": int(unmatched_count),
            "sample_unmatched_bins": unmatched_bins,
            "reference_bin_count": len(valid_bins)
        }
    }


def check_settlement_reconciliation(df: pd.DataFrame, 
                                    settlement_ledger: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """
    Reconcile transactions against settlement ledger.
    Checks txn_id match rate and amount/currency consistency.
    """
    if settlement_ledger is None:
        return {
            "check_id": "reconciliation_settlement",
            "passed": True,
            "severity": "low",
            "metrics": {"message": "No settlement ledger provided"}
        }
    
    # Find transaction ID column
    txn_id_cols = [col for col in df.columns if any(keyword in col.lower() 
                   for keyword in ['txn_id', 'transaction_id', 'id'])]
    
    if not txn_id_cols:
        return {
            "check_id": "reconciliation_settlement",
            "passed": True,
            "severity": "low",
            "metrics": {"message": "No transaction ID column found"}
        }
    
    txn_id_col = txn_id_cols[0]
    
    # Find settlement ledger ID column
    ledger_id_cols = [col for col in settlement_ledger.columns if any(keyword in col.lower() 
                      for keyword in ['txn_id', 'transaction_id', 'id'])]
    
    if not ledger_id_cols:
        return {
            "check_id": "reconciliation_settlement",
            "passed": True,
            "severity": "low",
            "metrics": {"message": "Settlement ledger format invalid"}
        }
    
    ledger_id_col = ledger_id_cols[0]
    
    # Check txn_id match rate
    ledger_ids = set(settlement_ledger[ledger_id_col].astype(str))
    df_ids = df[txn_id_col].astype(str)
    
    matched_mask = df_ids.isin(ledger_ids)
    match_rate = matched_mask.sum() / len(df) if len(df) > 0 else 0
    unmatched_count = (~matched_mask & ~df_ids.isna()).sum()
    
    # Check amount/currency consistency for matched records
    amount_mismatches = 0
    currency_mismatches = 0
    
    if 'amount' in df.columns and 'amount' in settlement_ledger.columns:
        # Merge on ID to compare amounts
        merged = df[[txn_id_col, 'amount']].merge(
            settlement_ledger[[ledger_id_col, 'amount']],
            left_on=txn_id_col,
            right_on=ledger_id_col,
            how='inner',
            suffixes=('_df', '_ledger')
        )
        
        # Allow small tolerance for floating point
        amount_diff = abs(pd.to_numeric(merged['amount_df'], errors='coerce') - 
                         pd.to_numeric(merged['amount_ledger'], errors='coerce'))
        amount_mismatches = (amount_diff > 0.01).sum()
    
    if 'currency' in df.columns and 'currency' in settlement_ledger.columns:
        merged = df[[txn_id_col, 'currency']].merge(
            settlement_ledger[[ledger_id_col, 'currency']],
            left_on=txn_id_col,
            right_on=ledger_id_col,
            how='inner',
            suffixes=('_df', '_ledger')
        )
        
        currency_mismatches = (merged['currency_df'].astype(str).str.upper() != 
                              merged['currency_ledger'].astype(str).str.upper()).sum()
    
    total_mismatches = unmatched_count + amount_mismatches + currency_mismatches
    overall_reconciliation_rate = 1 - (total_mismatches / len(df)) if len(df) > 0 else 0
    
    passed = overall_reconciliation_rate > 0.98  # Expect >98% reconciliation
    
    return {
        "check_id": "reconciliation_settlement",
        "passed": passed,
        "severity": "critical" if overall_reconciliation_rate < 0.95 else "high" if overall_reconciliation_rate < 0.98 else "low",
        "metrics": {
            "txn_id_column": txn_id_col,
            "txn_id_match_rate": float(match_rate),
            "unmatched_txn_count": int(unmatched_count),
            "amount_mismatches": int(amount_mismatches),
            "currency_mismatches": int(currency_mismatches),
            "overall_reconciliation_rate": float(overall_reconciliation_rate),
            "ledger_record_count": len(settlement_ledger)
        }
    }


def run_reconciliation_checks(df: pd.DataFrame, profile: Dict[str, Any],
                             bin_reference: Optional[pd.DataFrame] = None,
                             settlement_ledger: Optional[pd.DataFrame] = None) -> List[Dict[str, Any]]:
    """Run all reconciliation/truthfulness checks."""
    return [
        check_bin_reconciliation(df, bin_reference),
        check_settlement_reconciliation(df, settlement_ledger)
    ]
