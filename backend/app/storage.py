"""
Database storage layer with SQLite.
Ensures metadata-only storage - no raw transaction data persisted.
"""
import os
from sqlmodel import SQLModel, create_engine, Session, select
from typing import List, Optional
from .models import Run, DimensionScore, CheckResult, AgentLog, Reference, Artifact


# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/dqs.db")
engine = create_engine(DATABASE_URL, echo=False)


def init_db():
    """Initialize database tables."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get database session."""
    with Session(engine) as session:
        yield session


# CRUD operations
def create_run(run: Run) -> Run:
    """Create a new run record."""
    with Session(engine) as session:
        session.add(run)
        session.commit()
        session.refresh(run)
        return run


def update_run(run_id: str, **kwargs) -> Optional[Run]:
    """Update run record."""
    with Session(engine) as session:
        statement = select(Run).where(Run.run_id == run_id)
        run = session.exec(statement).first()
        if run:
            for key, value in kwargs.items():
                setattr(run, key, value)
            session.add(run)
            session.commit()
            session.refresh(run)
        return run


def get_run(run_id: str) -> Optional[Run]:
    """Get run by ID."""
    with Session(engine) as session:
        statement = select(Run).where(Run.run_id == run_id)
        return session.exec(statement).first()


def get_all_runs() -> List[Run]:
    """Get all runs."""
    with Session(engine) as session:
        statement = select(Run).order_by(Run.timestamp.desc())
        return list(session.exec(statement).all())


def create_dimension_scores(scores: List[DimensionScore]):
    """Create dimension score records."""
    with Session(engine) as session:
        for score in scores:
            session.add(score)
        session.commit()


def get_dimension_scores(run_id: str) -> List[DimensionScore]:
    """Get dimension scores for a run."""
    with Session(engine) as session:
        statement = select(DimensionScore).where(DimensionScore.run_id == run_id)
        return list(session.exec(statement).all())


def create_check_results(results: List[CheckResult]):
    """Create check result records."""
    with Session(engine) as session:
        for result in results:
            session.add(result)
        session.commit()


def get_check_results(run_id: str) -> List[CheckResult]:
    """Get check results for a run."""
    with Session(engine) as session:
        statement = select(CheckResult).where(CheckResult.run_id == run_id)
        return list(session.exec(statement).all())


def create_agent_log(log: AgentLog):
    """Create agent log record."""
    with Session(engine) as session:
        session.add(log)
        session.commit()


def get_agent_logs(run_id: str) -> List[AgentLog]:
    """Get agent logs for a run."""
    with Session(engine) as session:
        statement = select(AgentLog).where(AgentLog.run_id == run_id).order_by(AgentLog.step_order)
        return list(session.exec(statement).all())


def create_reference(reference: Reference) -> Reference:
    """Create reference record."""
    with Session(engine) as session:
        session.add(reference)
        session.commit()
        session.refresh(reference)
        return reference


def get_reference(reference_id: str) -> Optional[Reference]:
    """Get reference by ID."""
    with Session(engine) as session:
        statement = select(Reference).where(Reference.reference_id == reference_id)
        return session.exec(statement).first()


def get_references_by_type(reference_type: str) -> List[Reference]:
    """Get references by type."""
    with Session(engine) as session:
        statement = select(Reference).where(Reference.reference_type == reference_type)
        return list(session.exec(statement).all())


def create_artifact(artifact: Artifact):
    """Create artifact record."""
    with Session(engine) as session:
        session.add(artifact)
        session.commit()


def get_artifact(run_id: str, artifact_type: str) -> Optional[Artifact]:
    """Get artifact by run ID and type."""
    with Session(engine) as session:
        statement = select(Artifact).where(
            Artifact.run_id == run_id,
            Artifact.artifact_type == artifact_type
        )
        return session.exec(statement).first()


def get_artifacts(run_id: str) -> List[Artifact]:
    """Get all artifacts for a run."""
    with Session(engine) as session:
        statement = select(Artifact).where(Artifact.run_id == run_id)
        return list(session.exec(statement).all())
