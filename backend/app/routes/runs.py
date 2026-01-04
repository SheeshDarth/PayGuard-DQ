"""
Runs API routes.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, JSONResponse
from typing import List, Dict, Any
from .. import storage
from ..models import ArtifactType


router = APIRouter(prefix="/api", tags=["runs"])


@router.get("/runs")
async def get_runs():
    """Get all runs with metadata."""
    try:
        runs = storage.get_all_runs()
        
        return {
            "runs": [
                {
                    "run_id": run.run_id,
                    "dataset_name": run.dataset_name,
                    "row_count": run.row_count,
                    "column_count": run.column_count,
                    "timestamp": run.timestamp.isoformat(),
                    "status": run.status,
                    "composite_dqs": run.composite_dqs
                }
                for run in runs
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch runs: {str(e)}")


@router.get("/runs/{run_id}")
async def get_run(run_id: str):
    """Get full result bundle for a run."""
    try:
        # Get run metadata
        run = storage.get_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        
        # Get dimension scores
        dimension_scores = storage.get_dimension_scores(run_id)
        
        # Get check results
        check_results = storage.get_check_results(run_id)
        
        # Get agent logs
        agent_logs = storage.get_agent_logs(run_id)
        
        # Get artifacts
        artifacts = storage.get_artifacts(run_id)
        
        # Parse JSON artifacts
        scores_artifact = next((a for a in artifacts if a.artifact_type == ArtifactType.SCORES), None)
        remediation_artifact = next((a for a in artifacts if a.artifact_type == ArtifactType.REMEDIATION), None)
        narrative_artifact = next((a for a in artifacts if a.artifact_type == ArtifactType.NARRATIVE), None)
        
        import json
        
        scores_data = json.loads(scores_artifact.content) if scores_artifact else {}
        remediation_data = json.loads(remediation_artifact.content) if remediation_artifact else {}
        narrative = narrative_artifact.content if narrative_artifact else ""
        
        return {
            "run": {
                "run_id": run.run_id,
                "dataset_name": run.dataset_name,
                "dataset_fingerprint": run.dataset_fingerprint,
                "row_count": run.row_count,
                "column_count": run.column_count,
                "timestamp": run.timestamp.isoformat(),
                "status": run.status,
                "composite_dqs": run.composite_dqs,
                "error_message": run.error_message
            },
            "scores": {
                "composite_dqs": run.composite_dqs,
                "dimension_scores": [
                    {
                        "dimension": ds.dimension,
                        "score": ds.score,
                        "weight": ds.weight,
                        "explainability": ds.explainability
                    }
                    for ds in dimension_scores
                ],
                "dimension_weights": scores_data.get("dimension_weights", {})
            },
            "checks": [
                {
                    "check_id": cr.check_id,
                    "dimension": cr.dimension,
                    "passed": cr.passed,
                    "severity": cr.severity,
                    "metrics": cr.metrics
                }
                for cr in check_results
            ],
            "narrative": narrative,
            "remediation": remediation_data,
            "agent_logs": [
                {
                    "agent_name": log.agent_name,
                    "step_order": log.step_order,
                    "inputs": log.inputs,
                    "outputs": log.outputs,
                    "timestamp": log.timestamp.isoformat(),
                    "duration_ms": log.duration_ms
                }
                for log in agent_logs
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch run: {str(e)}")


@router.get("/runs/{run_id}/export/dbt")
async def export_dbt(run_id: str):
    """Download dbt tests YAML."""
    try:
        artifact = storage.get_artifact(run_id, ArtifactType.DBT)
        if not artifact:
            raise HTTPException(status_code=404, detail="dbt artifact not found")
        
        return Response(
            content=artifact.content,
            media_type="application/x-yaml",
            headers={
                "Content-Disposition": f"attachment; filename=dbt_tests_{run_id}.yml"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/runs/{run_id}/export/ge")
async def export_ge(run_id: str):
    """Download Great Expectations suite JSON."""
    try:
        artifact = storage.get_artifact(run_id, ArtifactType.GE)
        if not artifact:
            raise HTTPException(status_code=404, detail="GE artifact not found")
        
        return Response(
            content=artifact.content,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=ge_suite_{run_id}.json"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/runs/{run_id}/governance")
async def get_governance_report(run_id: str):
    """Get governance report."""
    try:
        artifact = storage.get_artifact(run_id, ArtifactType.GOVERNANCE)
        if not artifact:
            raise HTTPException(status_code=404, detail="Governance report not found")
        
        return {
            "run_id": run_id,
            "report": artifact.content,
            "format": "markdown"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch governance report: {str(e)}")
