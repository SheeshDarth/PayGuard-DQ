"""
Profiler Agent: Analyzes dataset schema and computes aggregate statistics.
NO RAW DATA in output - only aggregates and metadata.
"""
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime


class ProfilerAgent:
    """Agent responsible for dataset profiling."""
    
    def __init__(self):
        self.name = "ProfilerAgent"
    
    def profile(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Profile the dataset and return metadata + aggregates.
        
        Returns:
            ProfileResult with schema, statistics, and inferred column types.
        """
        start_time = datetime.now()
        
        profile = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": {},
            "inferred_types": {
                "id_columns": [],
                "timestamp_columns": [],
                "enum_columns": [],
                "numeric_columns": [],
                "text_columns": []
            }
        }
        
        for col in df.columns:
            col_profile = self._profile_column(df, col)
            profile["columns"][col] = col_profile
            
            # Classify column type
            if col_profile["is_id_like"]:
                profile["inferred_types"]["id_columns"].append(col)
            if col_profile["is_timestamp"]:
                profile["inferred_types"]["timestamp_columns"].append(col)
            if col_profile["is_enum_like"]:
                profile["inferred_types"]["enum_columns"].append(col)
            if col_profile["is_numeric"]:
                profile["inferred_types"]["numeric_columns"].append(col)
            if col_profile["is_text"]:
                profile["inferred_types"]["text_columns"].append(col)
        
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return {
            "profile": profile,
            "duration_ms": duration_ms
        }
    
    def _profile_column(self, df: pd.DataFrame, col: str) -> Dict[str, Any]:
        """Profile a single column."""
        series = df[col]
        
        col_profile = {
            "dtype": str(series.dtype),
            "null_count": int(series.isna().sum()),
            "null_rate": float(series.isna().sum() / len(df)) if len(df) > 0 else 0,
            "unique_count": int(series.nunique()),
            "cardinality_ratio": float(series.nunique() / len(df)) if len(df) > 0 else 0
        }
        
        # Infer column characteristics
        col_lower = col.lower()
        
        # ID-like column
        col_profile["is_id_like"] = (
            any(keyword in col_lower for keyword in ['id', 'key', 'uuid', 'guid', 'reference']) and
            col_profile["cardinality_ratio"] > 0.95
        )
        
        # Timestamp column
        col_profile["is_timestamp"] = (
            any(keyword in col_lower for keyword in ['time', 'date', 'timestamp', 'created', 'updated']) or
            pd.api.types.is_datetime64_any_dtype(series)
        )
        
        # Enum-like column (low cardinality categorical)
        col_profile["is_enum_like"] = (
            col_profile["unique_count"] < 50 and
            col_profile["cardinality_ratio"] < 0.1
        )
        
        # Numeric column
        col_profile["is_numeric"] = pd.api.types.is_numeric_dtype(series)
        
        # Text column
        col_profile["is_text"] = pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series)
        
        # Sample values (for enum-like columns only)
        if col_profile["is_enum_like"]:
            top_values = series.value_counts().head(10)
            col_profile["sample_values"] = {
                str(k): int(v) for k, v in top_values.items()
            }
        
        # Statistics for numeric columns
        if col_profile["is_numeric"]:
            col_profile["stats"] = {
                "min": float(series.min()) if not series.isna().all() else None,
                "max": float(series.max()) if not series.isna().all() else None,
                "mean": float(series.mean()) if not series.isna().all() else None,
                "median": float(series.median()) if not series.isna().all() else None,
                "std": float(series.std()) if not series.isna().all() else None
            }
        
        return col_profile
