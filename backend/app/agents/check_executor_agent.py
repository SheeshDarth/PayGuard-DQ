"""
Check Executor Agent: Runs all checks for selected dimensions.
"""
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime
from ..checks import completeness, uniqueness, validity, consistency, timeliness, integrity, reconciliation


class CheckExecutorAgent:
    """Agent responsible for executing data quality checks."""
    
    def __init__(self):
        self.name = "CheckExecutorAgent"
    
    def execute_checks(self,
                      df: pd.DataFrame,
                      profile: Dict[str, Any],
                      selected_dimensions: List[str],
                      reference_data: Optional[Dict[str, pd.DataFrame]] = None) -> Dict[str, Any]:
        """
        Execute all checks for selected dimensions.
        
        Args:
            df: Dataset to check (in-memory only, not persisted)
            profile: Profile from ProfilerAgent
            selected_dimensions: Dimensions to check
            reference_data: Optional reference datasets
        
        Returns:
            CheckResults with all check outcomes
        """
        start_time = datetime.now()
        
        if reference_data is None:
            reference_data = {}
        
        all_results = []
        
        # Execute checks by dimension
        if "completeness" in selected_dimensions:
            results = completeness.run_completeness_checks(df, profile)
            for result in results:
                result["dimension"] = "completeness"
            all_results.extend(results)
        
        if "uniqueness" in selected_dimensions:
            results = uniqueness.run_uniqueness_checks(df, profile)
            for result in results:
                result["dimension"] = "uniqueness"
            all_results.extend(results)
        
        if "validity" in selected_dimensions:
            mcc_ref = reference_data.get("mcc_codes")
            results = validity.run_validity_checks(df, profile, mcc_ref)
            for result in results:
                result["dimension"] = "validity"
            all_results.extend(results)
        
        if "consistency" in selected_dimensions:
            currency_rules = reference_data.get("currency_rules")
            results = consistency.run_consistency_checks(df, profile, currency_rules)
            for result in results:
                result["dimension"] = "consistency"
            all_results.extend(results)
        
        if "timeliness" in selected_dimensions:
            results = timeliness.run_timeliness_checks(df, profile)
            for result in results:
                result["dimension"] = "timeliness"
            all_results.extend(results)
        
        if "integrity" in selected_dimensions:
            results = integrity.run_integrity_checks(df, profile, reference_data)
            for result in results:
                result["dimension"] = "integrity"
            all_results.extend(results)
        
        if "reconciliation" in selected_dimensions:
            bin_ref = reference_data.get("bin_map")
            settlement_ref = reference_data.get("settlement_ledger")
            results = reconciliation.run_reconciliation_checks(df, profile, bin_ref, settlement_ref)
            for result in results:
                result["dimension"] = "reconciliation"
            all_results.extend(results)
        
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return {
            "check_results": all_results,
            "total_checks": len(all_results),
            "duration_ms": duration_ms
        }
