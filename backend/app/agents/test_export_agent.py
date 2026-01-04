"""
Test Export Agent: Generates dbt tests and Great Expectations suite.
"""
import yaml
import json
from typing import Dict, Any, List
from datetime import datetime


class TestExportAgent:
    """Agent responsible for generating test artifacts."""
    
    def __init__(self):
        self.name = "TestExportAgent"
    
    def export_tests(self,
                    check_results: List[Dict[str, Any]],
                    profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate dbt tests and Great Expectations suite.
        
        Returns:
            TestExportResult with dbt_yaml and ge_suite_json
        """
        start_time = datetime.now()
        
        dbt_yaml = self._generate_dbt_tests(check_results, profile)
        ge_suite = self._generate_ge_suite(check_results, profile)
        
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return {
            "dbt_yaml": dbt_yaml,
            "ge_suite_json": json.dumps(ge_suite, indent=2),
            "duration_ms": duration_ms
        }
    
    def _generate_dbt_tests(self,
                           check_results: List[Dict[str, Any]],
                           profile: Dict[str, Any]) -> str:
        """Generate dbt schema tests YAML."""
        
        # Build dbt schema structure
        dbt_schema = {
            "version": 2,
            "models": [
                {
                    "name": "transactions",
                    "description": "Payment transactions dataset",
                    "columns": []
                }
            ]
        }
        
        columns_dict = {}
        
        # Process check results to generate tests
        for check in check_results:
            check_id = check.get("check_id", "")
            metrics = check.get("metrics", {})
            
            # Completeness -> not_null tests
            if "completeness" in check_id:
                required_fields = metrics.get("required_fields", [])
                for field in required_fields:
                    if field not in columns_dict:
                        columns_dict[field] = {
                            "name": field,
                            "description": f"Column {field}",
                            "tests": []
                        }
                    columns_dict[field]["tests"].append("not_null")
            
            # Uniqueness -> unique tests
            elif "uniqueness" in check_id:
                key_columns = metrics.get("key_columns", [])
                for col in key_columns:
                    if col not in columns_dict:
                        columns_dict[col] = {
                            "name": col,
                            "description": f"Column {col}",
                            "tests": []
                        }
                    columns_dict[col]["tests"].append("unique")
            
            # Validity -> accepted_values tests
            elif "validity_currency" in check_id:
                currency_cols = metrics.get("currency_columns", [])
                for col in currency_cols:
                    if col not in columns_dict:
                        columns_dict[col] = {
                            "name": col,
                            "description": f"Column {col}",
                            "tests": []
                        }
                    columns_dict[col]["tests"].append({
                        "accepted_values": {
                            "values": ["USD", "EUR", "GBP", "JPY", "CNY", "AUD", "CAD"]
                        }
                    })
            
            # Validity -> amount range
            elif "validity_amount" in check_id:
                amount_cols = metrics.get("amount_columns", [])
                for col in amount_cols:
                    if col not in columns_dict:
                        columns_dict[col] = {
                            "name": col,
                            "description": f"Column {col}",
                            "tests": []
                        }
                    columns_dict[col]["tests"].append({
                        "dbt_utils.expression_is_true": {
                            "expression": f"{col} >= 0"
                        }
                    })
        
        # Add columns to schema
        dbt_schema["models"][0]["columns"] = list(columns_dict.values())
        
        # Convert to YAML
        yaml_str = yaml.dump(dbt_schema, default_flow_style=False, sort_keys=False)
        
        return yaml_str
    
    def _generate_ge_suite(self,
                          check_results: List[Dict[str, Any]],
                          profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Great Expectations suite JSON."""
        
        ge_suite = {
            "data_asset_type": "Dataset",
            "expectation_suite_name": "payment_transactions_suite",
            "expectations": [],
            "meta": {
                "great_expectations_version": "0.18.0",
                "generated_by": "DQS_Agent"
            }
        }
        
        # Process check results to generate expectations
        for check in check_results:
            check_id = check.get("check_id", "")
            metrics = check.get("metrics", {})
            
            # Completeness -> expect_column_values_to_not_be_null
            if "completeness" in check_id:
                required_fields = metrics.get("required_fields", [])
                for field in required_fields:
                    ge_suite["expectations"].append({
                        "expectation_type": "expect_column_values_to_not_be_null",
                        "kwargs": {
                            "column": field,
                            "mostly": 0.95
                        }
                    })
            
            # Uniqueness -> expect_column_values_to_be_unique
            elif "uniqueness" in check_id:
                key_columns = metrics.get("key_columns", [])
                for col in key_columns:
                    ge_suite["expectations"].append({
                        "expectation_type": "expect_column_values_to_be_unique",
                        "kwargs": {
                            "column": col
                        }
                    })
            
            # Validity currency -> expect_column_values_to_be_in_set
            elif "validity_currency" in check_id:
                currency_cols = metrics.get("currency_columns", [])
                for col in currency_cols:
                    ge_suite["expectations"].append({
                        "expectation_type": "expect_column_values_to_be_in_set",
                        "kwargs": {
                            "column": col,
                            "value_set": ["USD", "EUR", "GBP", "JPY", "CNY", "AUD", "CAD", "CHF", "HKD", "SGD"]
                        }
                    })
            
            # Validity amount -> expect_column_values_to_be_between
            elif "validity_amount" in check_id:
                amount_cols = metrics.get("amount_columns", [])
                for col in amount_cols:
                    ge_suite["expectations"].append({
                        "expectation_type": "expect_column_values_to_be_between",
                        "kwargs": {
                            "column": col,
                            "min_value": 0,
                            "mostly": 0.99
                        }
                    })
            
            # Consistency time ordering
            elif "consistency_time_ordering" in check_id:
                event_col = metrics.get("event_column")
                settlement_col = metrics.get("settlement_column")
                if event_col and settlement_col:
                    ge_suite["expectations"].append({
                        "expectation_type": "expect_column_pair_values_A_to_be_greater_than_B",
                        "kwargs": {
                            "column_A": settlement_col,
                            "column_B": event_col,
                            "or_equal": True,
                            "mostly": 0.99
                        }
                    })
        
        return ge_suite
