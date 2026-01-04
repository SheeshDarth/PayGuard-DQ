"""
Validity checks: regex/range validation for currencies, countries, MCC, amounts.
"""
import pandas as pd
import re
from typing import Dict, Any, List, Optional


# ISO 4217 currency codes (major ones)
VALID_CURRENCIES = {
    'USD', 'EUR', 'GBP', 'JPY', 'CNY', 'AUD', 'CAD', 'CHF', 'HKD', 'SGD',
    'SEK', 'KRW', 'NOK', 'NZD', 'INR', 'MXN', 'ZAR', 'BRL', 'RUB', 'TRY',
    'AED', 'SAR', 'THB', 'MYR', 'IDR', 'PHP', 'DKK', 'PLN', 'CZK', 'HUF'
}

# ISO 3166 country codes (major ones)
VALID_COUNTRIES = {
    'US', 'GB', 'CA', 'AU', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'CH', 'AT',
    'SE', 'NO', 'DK', 'FI', 'IE', 'PT', 'GR', 'PL', 'CZ', 'HU', 'RO', 'BG',
    'JP', 'CN', 'KR', 'IN', 'SG', 'HK', 'TH', 'MY', 'ID', 'PH', 'VN', 'NZ',
    'MX', 'BR', 'AR', 'CL', 'CO', 'PE', 'ZA', 'AE', 'SA', 'TR', 'RU', 'IL'
}


def check_currency_validity(df: pd.DataFrame) -> Dict[str, Any]:
    """Check if currency codes are valid ISO 4217."""
    currency_cols = [col for col in df.columns if 'currency' in col.lower()]
    
    if not currency_cols:
        return {
            "check_id": "validity_currency",
            "passed": True,
            "severity": "low",
            "metrics": {"message": "No currency columns found"}
        }
    
    invalid_info = {}
    total_invalid = 0
    failing_columns = []
    
    for col in currency_cols:
        if col in df.columns:
            # Convert to string and uppercase
            values = df[col].astype(str).str.upper()
            invalid_mask = ~values.isin(VALID_CURRENCIES) & ~values.isna()
            invalid_count = invalid_mask.sum()
            invalid_rate = invalid_count / len(df) if len(df) > 0 else 0
            
            invalid_values = values[invalid_mask].unique().tolist()[:10]  # Top 10
            
            invalid_info[col] = {
                "invalid_count": int(invalid_count),
                "invalid_rate": float(invalid_rate),
                "sample_invalid_values": invalid_values
            }
            
            total_invalid += invalid_count
            
            if invalid_rate > 0:
                failing_columns.append({
                    "column": col,
                    "invalid_rate": float(invalid_rate)
                })
    
    overall_invalid_rate = total_invalid / (len(df) * len(currency_cols)) if len(df) > 0 and currency_cols else 0
    passed = overall_invalid_rate == 0
    
    return {
        "check_id": "validity_currency",
        "passed": passed,
        "severity": "high" if overall_invalid_rate > 0.01 else "medium" if overall_invalid_rate > 0 else "low",
        "metrics": {
            "currency_columns": currency_cols,
            "overall_invalid_rate": float(overall_invalid_rate),
            "invalid_info": invalid_info,
            "failing_columns": failing_columns
        }
    }


def check_country_validity(df: pd.DataFrame) -> Dict[str, Any]:
    """Check if country codes are valid ISO 3166."""
    country_cols = [col for col in df.columns if 'country' in col.lower()]
    
    if not country_cols:
        return {
            "check_id": "validity_country",
            "passed": True,
            "severity": "low",
            "metrics": {"message": "No country columns found"}
        }
    
    invalid_info = {}
    total_invalid = 0
    failing_columns = []
    
    for col in country_cols:
        if col in df.columns:
            values = df[col].astype(str).str.upper()
            invalid_mask = ~values.isin(VALID_COUNTRIES) & ~values.isna()
            invalid_count = invalid_mask.sum()
            invalid_rate = invalid_count / len(df) if len(df) > 0 else 0
            
            invalid_values = values[invalid_mask].unique().tolist()[:10]
            
            invalid_info[col] = {
                "invalid_count": int(invalid_count),
                "invalid_rate": float(invalid_rate),
                "sample_invalid_values": invalid_values
            }
            
            total_invalid += invalid_count
            
            if invalid_rate > 0:
                failing_columns.append({
                    "column": col,
                    "invalid_rate": float(invalid_rate)
                })
    
    overall_invalid_rate = total_invalid / (len(df) * len(country_cols)) if len(df) > 0 and country_cols else 0
    passed = overall_invalid_rate == 0
    
    return {
        "check_id": "validity_country",
        "passed": passed,
        "severity": "medium" if overall_invalid_rate > 0.01 else "low",
        "metrics": {
            "country_columns": country_cols,
            "overall_invalid_rate": float(overall_invalid_rate),
            "invalid_info": invalid_info,
            "failing_columns": failing_columns
        }
    }


def check_mcc_validity(df: pd.DataFrame, mcc_reference: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """Check if MCC codes are valid 4-digit codes."""
    mcc_cols = [col for col in df.columns if 'mcc' in col.lower()]
    
    if not mcc_cols:
        return {
            "check_id": "validity_mcc",
            "passed": True,
            "severity": "low",
            "metrics": {"message": "No MCC columns found"}
        }
    
    invalid_info = {}
    total_invalid = 0
    failing_columns = []
    
    for col in mcc_cols:
        if col in df.columns:
            values = df[col].astype(str)
            
            # Check format: 4 digits
            format_invalid_mask = ~values.str.match(r'^\d{4}$') & ~values.isna()
            
            # If reference provided, also check against it
            if mcc_reference is not None and 'mcc' in mcc_reference.columns:
                valid_mccs = set(mcc_reference['mcc'].astype(str))
                reference_invalid_mask = ~values.isin(valid_mccs) & ~values.isna()
                invalid_mask = format_invalid_mask | reference_invalid_mask
            else:
                invalid_mask = format_invalid_mask
            
            invalid_count = invalid_mask.sum()
            invalid_rate = invalid_count / len(df) if len(df) > 0 else 0
            
            invalid_values = values[invalid_mask].unique().tolist()[:10]
            
            invalid_info[col] = {
                "invalid_count": int(invalid_count),
                "invalid_rate": float(invalid_rate),
                "sample_invalid_values": invalid_values
            }
            
            total_invalid += invalid_count
            
            if invalid_rate > 0:
                failing_columns.append({
                    "column": col,
                    "invalid_rate": float(invalid_rate)
                })
    
    overall_invalid_rate = total_invalid / (len(df) * len(mcc_cols)) if len(df) > 0 and mcc_cols else 0
    passed = overall_invalid_rate == 0
    
    return {
        "check_id": "validity_mcc",
        "passed": passed,
        "severity": "medium" if overall_invalid_rate > 0.01 else "low",
        "metrics": {
            "mcc_columns": mcc_cols,
            "overall_invalid_rate": float(overall_invalid_rate),
            "invalid_info": invalid_info,
            "failing_columns": failing_columns,
            "reference_used": mcc_reference is not None
        }
    }


def check_amount_validity(df: pd.DataFrame) -> Dict[str, Any]:
    """Check if amounts are valid (non-negative, reasonable bounds)."""
    amount_cols = [col for col in df.columns if 'amount' in col.lower()]
    
    if not amount_cols:
        return {
            "check_id": "validity_amount",
            "passed": True,
            "severity": "low",
            "metrics": {"message": "No amount columns found"}
        }
    
    invalid_info = {}
    total_invalid = 0
    failing_columns = []
    
    for col in amount_cols:
        if col in df.columns:
            # Convert to numeric
            values = pd.to_numeric(df[col], errors='coerce')
            
            # Check for negative amounts
            negative_mask = values < 0
            negative_count = negative_mask.sum()
            
            # Check for unreasonable outliers using IQR method
            q1 = values.quantile(0.25)
            q3 = values.quantile(0.75)
            iqr = q3 - q1
            outlier_mask = (values > q3 + 3 * iqr) | (values < q1 - 3 * iqr)
            outlier_count = outlier_mask.sum()
            
            invalid_count = negative_count + outlier_count
            invalid_rate = invalid_count / len(df) if len(df) > 0 else 0
            
            invalid_info[col] = {
                "invalid_count": int(invalid_count),
                "invalid_rate": float(invalid_rate),
                "negative_count": int(negative_count),
                "outlier_count": int(outlier_count),
                "min": float(values.min()) if not values.isna().all() else None,
                "max": float(values.max()) if not values.isna().all() else None,
                "median": float(values.median()) if not values.isna().all() else None
            }
            
            total_invalid += invalid_count
            
            if invalid_rate > 0:
                failing_columns.append({
                    "column": col,
                    "invalid_rate": float(invalid_rate)
                })
    
    overall_invalid_rate = total_invalid / (len(df) * len(amount_cols)) if len(df) > 0 and amount_cols else 0
    passed = overall_invalid_rate < 0.01  # Allow <1% outliers
    
    return {
        "check_id": "validity_amount",
        "passed": passed,
        "severity": "critical" if overall_invalid_rate > 0.05 else "high" if overall_invalid_rate > 0.01 else "low",
        "metrics": {
            "amount_columns": amount_cols,
            "overall_invalid_rate": float(overall_invalid_rate),
            "invalid_info": invalid_info,
            "failing_columns": failing_columns
        }
    }


def run_validity_checks(df: pd.DataFrame, profile: Dict[str, Any], 
                       mcc_reference: Optional[pd.DataFrame] = None) -> List[Dict[str, Any]]:
    """Run all validity checks."""
    return [
        check_currency_validity(df),
        check_country_validity(df),
        check_mcc_validity(df, mcc_reference),
        check_amount_validity(df)
    ]
