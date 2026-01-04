"""
Utility functions for dataset fingerprinting.
"""
import hashlib
import pandas as pd
from typing import Dict, Any


def compute_dataset_fingerprint(df: pd.DataFrame) -> str:
    """
    Compute SHA256 fingerprint of dataset based on schema and sample data.
    Does NOT hash all raw data - only schema + row count + sample hash.
    """
    components = []
    
    # Schema: column names and types
    schema_str = ",".join([f"{col}:{dtype}" for col, dtype in df.dtypes.items()])
    components.append(schema_str)
    
    # Row count
    components.append(str(len(df)))
    
    # Sample hash: hash first 100 rows to detect content changes
    # This is a compromise - we don't hash all data but can detect major changes
    sample_size = min(100, len(df))
    if sample_size > 0:
        sample_hash = hashlib.sha256(
            df.head(sample_size).to_json().encode()
        ).hexdigest()
        components.append(sample_hash)
    
    # Combine and hash
    combined = "|".join(components)
    fingerprint = hashlib.sha256(combined.encode()).hexdigest()
    
    return fingerprint


def compute_reference_fingerprint(df: pd.DataFrame, ref_type: str) -> str:
    """
    Compute fingerprint for reference data.
    """
    components = [ref_type]
    
    # Schema
    schema_str = ",".join([f"{col}:{dtype}" for col, dtype in df.dtypes.items()])
    components.append(schema_str)
    
    # Row count
    components.append(str(len(df)))
    
    # Full content hash for reference data (usually smaller)
    content_hash = hashlib.sha256(df.to_json().encode()).hexdigest()
    components.append(content_hash)
    
    combined = "|".join(components)
    fingerprint = hashlib.sha256(combined.encode()).hexdigest()
    
    return fingerprint
