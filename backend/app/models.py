"""
Database models for metadata-only storage.
CRITICAL: No raw transaction data is stored - only metadata, aggregates, and scoring outputs.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from sqlmodel import SQLModel, Field, JSON, Column
from enum import Enum


class RunStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ReferenceType(str, Enum):
    BIN_MAP = "bin_map"
    CURRENCY_RULES = "currency_rules"
    MCC_CODES = "mcc_codes"
    SETTLEMENT_LEDGER = "settlement_ledger"


class ArtifactType(str, Enum):
    DBT = "dbt"
    GE = "ge"
    GOVERNANCE = "governance"
    PROFILE = "profile"
    DIMENSIONS = "dimensions"
    CHECKS = "checks"
    SCORES = "scores"
    NARRATIVE = "narrative"
    REMEDIATION = "remediation"


# Main run metadata
class Run(SQLModel, table=True):
    __tablename__ = "runs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: str = Field(unique=True, index=True)
    dataset_name: Optional[str] = None
    dataset_fingerprint: str  # SHA256 hash
    row_count: int
    column_count: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: RunStatus = RunStatus.PENDING
    composite_dqs: Optional[float] = None
    error_message: Optional[str] = None


# Per-dimension scores with explainability
class DimensionScore(SQLModel, table=True):
    __tablename__ = "dimension_scores"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: str = Field(foreign_key="runs.run_id", index=True)
    dimension: str
    score: float
    weight: float
    explainability: Dict[str, Any] = Field(sa_column=Column(JSON))
    # explainability contains: metrics, error_rates, top_failing_checks, impacted_columns, formula


# Individual check results
class CheckResult(SQLModel, table=True):
    __tablename__ = "check_results"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: str = Field(foreign_key="runs.run_id", index=True)
    check_id: str
    dimension: str
    passed: bool
    severity: str  # critical, high, medium, low
    metrics: Dict[str, Any] = Field(sa_column=Column(JSON))
    # metrics contains: error_rate, affected_rows, failing_columns, etc.


# Agent execution logs
class AgentLog(SQLModel, table=True):
    __tablename__ = "agent_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: str = Field(foreign_key="runs.run_id", index=True)
    agent_name: str
    step_order: int
    inputs: Dict[str, Any] = Field(sa_column=Column(JSON))
    outputs: Dict[str, Any] = Field(sa_column=Column(JSON))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration_ms: Optional[int] = None


# Reference data metadata
class Reference(SQLModel, table=True):
    __tablename__ = "references"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    reference_id: str = Field(unique=True, index=True)
    reference_type: ReferenceType
    fingerprint: str  # SHA256 hash
    row_count: int
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    # Note: We store the reference data in memory during processing
    # For persistence, we could store it separately, but for hackathon we'll keep in memory


# Artifacts (test exports, governance reports, etc.)
class Artifact(SQLModel, table=True):
    __tablename__ = "artifacts"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: str = Field(foreign_key="runs.run_id", index=True)
    artifact_type: ArtifactType
    content: str  # JSON, YAML, or Markdown content
    created_at: datetime = Field(default_factory=datetime.utcnow)
