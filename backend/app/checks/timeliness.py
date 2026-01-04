"""
Timeliness checks: event lag and SLA validation.
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List


def check_event_lag(df: pd.DataFrame, sla_hours: int = 24) -> Dict[str, Any]:
    """
    Check if events are processed within SLA timeframe.
    Measures lag between event_time and current time or batch_time.
    """
    time_cols = [col for col in df.columns if any(keyword in col.lower() 
                 for keyword in ['event_time', 'created_at', 'timestamp'])]
    
    if not time_cols:
        return {
            "check_id": "timeliness_event_lag",
            "passed": True,
            "severity": "low",
            "metrics": {"message": "No timestamp columns found"}
        }
    
    time_col = time_cols[0]
    
    # Convert to datetime
    event_times = pd.to_datetime(df[time_col], errors='coerce')
    
    # Use current time as reference
    current_time = pd.Timestamp.now()
    
    # Calculate lag in hours
    lags = (current_time - event_times).dt.total_seconds() / 3600
    
    # Check SLA violations
    sla_violations = lags > sla_hours
    violation_count = sla_violations.sum()
    violation_rate = violation_count / len(df) if len(df) > 0 else 0
    
    # Statistics
    valid_lags = lags[~lags.isna()]
    
    passed = violation_rate < 0.05  # Allow <5% violations
    
    return {
        "check_id": "timeliness_event_lag",
        "passed": passed,
        "severity": "high" if violation_rate > 0.10 else "medium" if violation_rate > 0.05 else "low",
        "metrics": {
            "time_column": time_col,
            "sla_hours": sla_hours,
            "violation_count": int(violation_count),
            "violation_rate": float(violation_rate),
            "avg_lag_hours": float(valid_lags.mean()) if len(valid_lags) > 0 else None,
            "max_lag_hours": float(valid_lags.max()) if len(valid_lags) > 0 else None,
            "p95_lag_hours": float(valid_lags.quantile(0.95)) if len(valid_lags) > 0 else None
        }
    }


def check_processing_delay(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check delay between event_time and settlement_time.
    """
    event_cols = [col for col in df.columns if 'event' in col.lower() and 'time' in col.lower()]
    settlement_cols = [col for col in df.columns if 'settlement' in col.lower() and ('time' in col.lower() or 'date' in col.lower())]
    
    if not event_cols or not settlement_cols:
        return {
            "check_id": "timeliness_processing_delay",
            "passed": True,
            "severity": "low",
            "metrics": {"message": "Required time columns not found"}
        }
    
    event_col = event_cols[0]
    settlement_col = settlement_cols[0]
    
    # Convert to datetime
    event_times = pd.to_datetime(df[event_col], errors='coerce')
    settlement_times = pd.to_datetime(df[settlement_col], errors='coerce')
    
    # Calculate delay in hours
    both_present = ~event_times.isna() & ~settlement_times.isna()
    delays = (settlement_times - event_times).dt.total_seconds() / 3600
    
    # Typical settlement should be within 48 hours
    excessive_delays = (delays > 48) & both_present
    excessive_count = excessive_delays.sum()
    excessive_rate = excessive_count / both_present.sum() if both_present.sum() > 0 else 0
    
    valid_delays = delays[both_present]
    
    passed = excessive_rate < 0.05
    
    return {
        "check_id": "timeliness_processing_delay",
        "passed": passed,
        "severity": "medium" if excessive_rate > 0.10 else "low",
        "metrics": {
            "event_column": event_col,
            "settlement_column": settlement_col,
            "excessive_delay_count": int(excessive_count),
            "excessive_delay_rate": float(excessive_rate),
            "avg_delay_hours": float(valid_delays.mean()) if len(valid_delays) > 0 else None,
            "max_delay_hours": float(valid_delays.max()) if len(valid_delays) > 0 else None,
            "p95_delay_hours": float(valid_delays.quantile(0.95)) if len(valid_delays) > 0 else None
        }
    }


def run_timeliness_checks(df: pd.DataFrame, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Run all timeliness checks."""
    return [
        check_event_lag(df),
        check_processing_delay(df)
    ]
