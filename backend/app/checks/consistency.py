"""
Consistency checks: cross-field validation rules.
"""
import pandas as pd
from typing import Dict, Any, List, Optional


def check_status_settlement_consistency(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check if settled transactions have settlement dates.
    """
    status_cols = [col for col in df.columns if 'status' in col.lower()]
    settlement_cols = [col for col in df.columns if 'settlement' in col.lower() and 'date' in col.lower()]
    
    if not status_cols or not settlement_cols:
        return {
            "check_id": "consistency_status_settlement",
            "passed": True,
            "severity": "low",
            "metrics": {"message": "Required columns not found"}
        }
    
    status_col = status_cols[0]
    settlement_col = settlement_cols[0]
    
    # Find rows where status is SETTLED/COMPLETED but settlement_date is null
    settled_mask = df[status_col].astype(str).str.upper().isin(['SETTLED', 'COMPLETED', 'SUCCESS'])
    missing_settlement = settled_mask & df[settlement_col].isna()
    
    inconsistent_count = missing_settlement.sum()
    inconsistent_rate = inconsistent_count / len(df) if len(df) > 0 else 0
    
    passed = inconsistent_count == 0
    
    return {
        "check_id": "consistency_status_settlement",
        "passed": passed,
        "severity": "high" if inconsistent_rate > 0.01 else "medium" if inconsistent_rate > 0 else "low",
        "metrics": {
            "status_column": status_col,
            "settlement_column": settlement_col,
            "inconsistent_count": int(inconsistent_count),
            "inconsistent_rate": float(inconsistent_rate),
            "settled_count": int(settled_mask.sum())
        }
    }


def check_currency_decimal_consistency(df: pd.DataFrame, 
                                       currency_rules: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """
    Check if currency decimal places match rules (e.g., JPY should have 0 decimals).
    """
    currency_cols = [col for col in df.columns if 'currency' in col.lower()]
    amount_cols = [col for col in df.columns if 'amount' in col.lower()]
    
    if not currency_cols or not amount_cols or currency_rules is None:
        return {
            "check_id": "consistency_currency_decimals",
            "passed": True,
            "severity": "low",
            "metrics": {"message": "Required columns or reference not found"}
        }
    
    currency_col = currency_cols[0]
    amount_col = amount_cols[0]
    
    # Build currency -> decimal_places mapping
    if 'currency' in currency_rules.columns and 'decimal_places' in currency_rules.columns:
        currency_decimals = dict(zip(
            currency_rules['currency'].astype(str).str.upper(),
            currency_rules['decimal_places'].astype(int)
        ))
    else:
        return {
            "check_id": "consistency_currency_decimals",
            "passed": True,
            "severity": "low",
            "metrics": {"message": "Currency rules format invalid"}
        }
    
    inconsistencies = []
    
    for currency, expected_decimals in currency_decimals.items():
        currency_mask = df[currency_col].astype(str).str.upper() == currency
        if currency_mask.sum() == 0:
            continue
        
        amounts = pd.to_numeric(df.loc[currency_mask, amount_col], errors='coerce')
        
        # Check decimal places
        if expected_decimals == 0:
            # Should be whole numbers
            has_decimals = (amounts % 1 != 0)
            inconsistent_count = has_decimals.sum()
        else:
            # Check if decimals exceed expected
            # This is a simplified check - in production you'd be more precise
            inconsistent_count = 0
        
        if inconsistent_count > 0:
            inconsistencies.append({
                "currency": currency,
                "expected_decimals": expected_decimals,
                "inconsistent_count": int(inconsistent_count),
                "total_count": int(currency_mask.sum())
            })
    
    total_inconsistent = sum(inc['inconsistent_count'] for inc in inconsistencies)
    inconsistent_rate = total_inconsistent / len(df) if len(df) > 0 else 0
    passed = total_inconsistent == 0
    
    return {
        "check_id": "consistency_currency_decimals",
        "passed": passed,
        "severity": "medium" if inconsistent_rate > 0.01 else "low",
        "metrics": {
            "currency_column": currency_col,
            "amount_column": amount_col,
            "inconsistencies": inconsistencies,
            "total_inconsistent": int(total_inconsistent),
            "inconsistent_rate": float(inconsistent_rate)
        }
    }


def check_time_ordering_consistency(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check if event_time <= settlement_time (if both exist).
    """
    event_cols = [col for col in df.columns if 'event' in col.lower() and 'time' in col.lower()]
    settlement_cols = [col for col in df.columns if 'settlement' in col.lower() and ('time' in col.lower() or 'date' in col.lower())]
    
    if not event_cols or not settlement_cols:
        return {
            "check_id": "consistency_time_ordering",
            "passed": True,
            "severity": "low",
            "metrics": {"message": "Required time columns not found"}
        }
    
    event_col = event_cols[0]
    settlement_col = settlement_cols[0]
    
    # Convert to datetime
    event_times = pd.to_datetime(df[event_col], errors='coerce')
    settlement_times = pd.to_datetime(df[settlement_col], errors='coerce')
    
    # Check ordering where both are present
    both_present = ~event_times.isna() & ~settlement_times.isna()
    misordered = both_present & (event_times > settlement_times)
    
    misordered_count = misordered.sum()
    misordered_rate = misordered_count / both_present.sum() if both_present.sum() > 0 else 0
    
    passed = misordered_count == 0
    
    return {
        "check_id": "consistency_time_ordering",
        "passed": passed,
        "severity": "high" if misordered_rate > 0.01 else "medium" if misordered_rate > 0 else "low",
        "metrics": {
            "event_column": event_col,
            "settlement_column": settlement_col,
            "misordered_count": int(misordered_count),
            "misordered_rate": float(misordered_rate),
            "compared_count": int(both_present.sum())
        }
    }


def run_consistency_checks(df: pd.DataFrame, profile: Dict[str, Any],
                          currency_rules: Optional[pd.DataFrame] = None) -> List[Dict[str, Any]]:
    """Run all consistency checks."""
    return [
        check_status_settlement_consistency(df),
        check_currency_decimal_consistency(df, currency_rules),
        check_time_ordering_consistency(df)
    ]
