"""
Dimension Selector Agent: Automatically identifies applicable quality dimensions.
"""
from typing import Dict, Any, List
from datetime import datetime


class DimensionSelectorAgent:
    """Agent responsible for selecting applicable quality dimensions."""
    
    def __init__(self):
        self.name = "DimensionSelectorAgent"
    
    def select_dimensions(self, profile: Dict[str, Any], 
                         has_references: Dict[str, bool]) -> Dict[str, Any]:
        """
        Select applicable quality dimensions based on dataset profile.
        
        Args:
            profile: Dataset profile from ProfilerAgent
            has_references: Dict indicating which reference datasets are available
        
        Returns:
            SelectedDimensions with dimension list and rationale
        """
        start_time = datetime.now()
        
        selected = []
        rationale = {}
        
        # Completeness: Always applicable
        selected.append("completeness")
        rationale["completeness"] = [
            "All datasets should be checked for missing values",
            f"Dataset has {profile['column_count']} columns to validate"
        ]
        
        # Uniqueness: If ID-like columns detected
        if profile["inferred_types"]["id_columns"]:
            selected.append("uniqueness")
            rationale["uniqueness"] = [
                f"Detected {len(profile['inferred_types']['id_columns'])} ID-like columns",
                f"Key columns: {', '.join(profile['inferred_types']['id_columns'][:3])}"
            ]
        
        # Validity: If enum/currency/country columns detected
        has_validity_targets = (
            profile["inferred_types"]["enum_columns"] or
            any('currency' in col.lower() for col in profile["columns"].keys()) or
            any('country' in col.lower() for col in profile["columns"].keys()) or
            any('mcc' in col.lower() for col in profile["columns"].keys()) or
            any('amount' in col.lower() for col in profile["columns"].keys())
        )
        
        if has_validity_targets:
            selected.append("validity")
            reasons = ["Detected columns requiring format/range validation:"]
            if any('currency' in col.lower() for col in profile["columns"].keys()):
                reasons.append("- Currency codes (ISO 4217)")
            if any('country' in col.lower() for col in profile["columns"].keys()):
                reasons.append("- Country codes (ISO 3166)")
            if any('mcc' in col.lower() for col in profile["columns"].keys()):
                reasons.append("- MCC codes (4-digit)")
            if any('amount' in col.lower() for col in profile["columns"].keys()):
                reasons.append("- Amount values (non-negative, outlier detection)")
            rationale["validity"] = reasons
        
        # Consistency: If multiple related fields detected
        has_consistency_targets = (
            any('status' in col.lower() for col in profile["columns"].keys()) or
            len(profile["inferred_types"]["timestamp_columns"]) > 1
        )
        
        if has_consistency_targets:
            selected.append("consistency")
            reasons = ["Detected related fields requiring cross-validation:"]
            if any('status' in col.lower() for col in profile["columns"].keys()):
                reasons.append("- Status fields with dependent data (e.g., settlement_date)")
            if len(profile["inferred_types"]["timestamp_columns"]) > 1:
                reasons.append("- Multiple timestamps requiring ordering validation")
            if any('currency' in col.lower() for col in profile["columns"].keys()):
                reasons.append("- Currency decimal consistency")
            rationale["consistency"] = reasons
        
        # Timeliness: If timestamp columns detected
        if profile["inferred_types"]["timestamp_columns"]:
            selected.append("timeliness")
            rationale["timeliness"] = [
                f"Detected {len(profile['inferred_types']['timestamp_columns'])} timestamp columns",
                f"Timestamp columns: {', '.join(profile['inferred_types']['timestamp_columns'][:3])}",
                "Will check event lag and processing delays"
            ]
        
        # Integrity: If reference datasets provided
        if has_references.get("merchants") or has_references.get("customers"):
            selected.append("integrity")
            reasons = ["Reference data available for integrity checks:"]
            if has_references.get("merchants"):
                reasons.append("- Merchant master data")
            if has_references.get("customers"):
                reasons.append("- Customer master data")
            rationale["integrity"] = reasons
        
        # Reconciliation: If settlement ledger or BIN map provided
        if has_references.get("settlement_ledger") or has_references.get("bin_map"):
            selected.append("reconciliation")
            reasons = [
                "PAYMENTS DIFFERENTIATOR: Reference truth data available for reconciliation:",
            ]
            if has_references.get("settlement_ledger"):
                reasons.append("- Settlement ledger for transaction matching")
            if has_references.get("bin_map"):
                reasons.append("- BIN reference for card validation")
            rationale["reconciliation"] = reasons
        
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return {
            "selected_dimensions": selected,
            "rationale": rationale,
            "duration_ms": duration_ms
        }
