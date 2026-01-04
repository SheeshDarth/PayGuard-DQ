"""
Ingestion API routes.
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import pandas as pd
import io
from ..orchestrator import Orchestrator
from ..models import Reference, ReferenceType
from .. import storage
from ..utils.hashing import compute_reference_fingerprint
import uuid


router = APIRouter(prefix="/api", tags=["ingestion"])

# Global reference data store (in-memory)
reference_store: dict = {}


@router.post("/ingest")
async def ingest_dataset(
    dataset_file: UploadFile = File(...),
    dataset_name: Optional[str] = Form(None)
):
    """
    Ingest dataset and trigger DQS pipeline.
    
    CRITICAL: Dataset is processed in-memory only and NOT persisted.
    Only metadata artifacts are stored.
    """
    try:
        # Read file content
        content = await dataset_file.read()
        
        # Parse CSV
        df = pd.read_csv(io.BytesIO(content))
        
        # Validate dataset
        if df.empty:
            raise HTTPException(status_code=400, detail="Dataset is empty")
        
        # Process through orchestrator
        orchestrator = Orchestrator()
        run_id = await orchestrator.process_dataset(
            df,
            dataset_name=dataset_name or dataset_file.filename,
            reference_data=reference_store if reference_store else None
        )
        
        return {
            "run_id": run_id,
            "message": "Dataset processed successfully",
            "row_count": len(df),
            "column_count": len(df.columns)
        }
        
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="Invalid CSV file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.post("/ingest-reference")
async def ingest_reference(
    reference_file: UploadFile = File(...),
    reference_type: str = Form(...)
):
    """
    Ingest reference data (BIN map, currency rules, settlement ledger, etc.).
    
    Reference data is stored in-memory for use in checks.
    """
    try:
        # Validate reference type
        valid_types = ["bin_map", "currency_rules", "mcc_codes", "settlement_ledger"]
        if reference_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid reference_type. Must be one of: {', '.join(valid_types)}"
            )
        
        # Read file content
        content = await reference_file.read()
        
        # Parse CSV
        df = pd.read_csv(io.BytesIO(content))
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Reference file is empty")
        
        # Compute fingerprint
        fingerprint = compute_reference_fingerprint(df, reference_type)
        
        # Generate reference ID
        reference_id = f"ref_{uuid.uuid4().hex[:12]}"
        
        # Store reference metadata
        reference = Reference(
            reference_id=reference_id,
            reference_type=ReferenceType(reference_type),
            fingerprint=fingerprint,
            row_count=len(df)
        )
        storage.create_reference(reference)
        
        # Store reference data in memory
        reference_store[reference_type] = df
        
        return {
            "reference_id": reference_id,
            "reference_type": reference_type,
            "row_count": len(df),
            "message": "Reference data ingested successfully"
        }
        
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="Invalid CSV file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
