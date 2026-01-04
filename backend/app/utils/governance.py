"""
Governance utilities for generating compliance reports.
"""
from typing import Dict, Any, List
from datetime import datetime


def generate_governance_report(run_id: str,
                               profile: Dict[str, Any],
                               scoring_result: Dict[str, Any],
                               agent_logs: List[Dict[str, Any]]) -> str:
    """
    Generate governance report confirming compliance with no-raw-data policy.
    
    Returns:
        Markdown governance report
    """
    
    report_parts = []
    
    # Header
    report_parts.append("# Data Quality Governance Report\n")
    report_parts.append(f"**Run ID**: {run_id}\n")
    report_parts.append(f"**Generated**: {datetime.utcnow().isoformat()}Z\n")
    report_parts.append("\n---\n\n")
    
    # Compliance Statement
    report_parts.append("## Compliance Statement\n\n")
    report_parts.append("> [!IMPORTANT]\n")
    report_parts.append("> **NO RAW TRANSACTION DATA STORED**\n")
    report_parts.append(">\n")
    report_parts.append("> This system adheres to strict data governance policies. "
                       "Raw transaction data is processed in-memory only and is NOT persisted to any storage system.\n\n")
    
    # What is Stored
    report_parts.append("## Data Storage Policy\n\n")
    report_parts.append("### Metadata ONLY Storage\n\n")
    report_parts.append("The following metadata artifacts are stored:\n\n")
    
    stored_data = [
        ("Dataset Fingerprint", "SHA256 hash of schema + row count + sample hash"),
        ("Schema Information", "Column names, data types, cardinality ratios"),
        ("Profiling Aggregates", "Null rates, unique counts, distribution statistics"),
        ("Check Results", "Pass/fail status, error rates, severity levels"),
        ("Dimension Scores", "Per-dimension scores (0-100) with explainability"),
        ("Composite DQS", "Overall data quality score (0-100)"),
        ("Agent Execution Logs", "Agent names, step order, inputs/outputs (aggregates only)"),
        ("Test Artifacts", "dbt tests YAML, Great Expectations suite JSON"),
        ("Governance Reports", "This report and audit trail")
    ]
    
    for item, description in stored_data:
        report_parts.append(f"- **{item}**: {description}\n")
    
    report_parts.append("\n### What is NOT Stored\n\n")
    report_parts.append("- ❌ Raw transaction rows\n")
    report_parts.append("- ❌ Individual transaction IDs (except in aggregates)\n")
    report_parts.append("- ❌ Customer PII\n")
    report_parts.append("- ❌ Card numbers or payment credentials\n")
    report_parts.append("- ❌ Any field-level values (except sample enum values for low-cardinality fields)\n\n")
    
    # Dataset Summary
    report_parts.append("## Dataset Summary\n\n")
    report_parts.append(f"- **Row Count**: {profile['row_count']:,}\n")
    report_parts.append(f"- **Column Count**: {profile['column_count']}\n")
    report_parts.append(f"- **Composite DQS**: {scoring_result['composite_dqs']}/100\n\n")
    
    # Audit Trail
    report_parts.append("## Audit Trail\n\n")
    report_parts.append("### Agent Execution Sequence\n\n")
    
    for i, log in enumerate(agent_logs, 1):
        agent_name = log.get("agent_name", "Unknown")
        duration = log.get("duration_ms", 0)
        report_parts.append(f"{i}. **{agent_name}** (executed in {duration}ms)\n")
    
    report_parts.append("\n")
    
    # Redaction Policy
    report_parts.append("## Redaction Policy\n\n")
    report_parts.append("### LLM Data Handling\n\n")
    report_parts.append("If LLM-powered explanations are enabled:\n\n")
    report_parts.append("- ✅ LLM receives ONLY aggregated metrics and statistics\n")
    report_parts.append("- ✅ No row-level data is sent to LLM\n")
    report_parts.append("- ✅ No PII or sensitive fields are included in prompts\n")
    report_parts.append("- ✅ All prompts contain only: scores, error rates, column names, check IDs\n\n")
    
    report_parts.append("If LLM is not available, the system uses deterministic templates with the same data restrictions.\n\n")
    
    # Retention Policy
    report_parts.append("## Retention Policy\n\n")
    report_parts.append("### Metadata Retention\n\n")
    report_parts.append("- **Default Retention**: 90 days\n")
    report_parts.append("- **Configurable**: Retention period can be adjusted based on compliance requirements\n")
    report_parts.append("- **Purge Process**: Automated cleanup of metadata older than retention period\n")
    report_parts.append("- **Audit Logs**: Governance reports retained for 1 year for compliance audits\n\n")
    
    # Database Schema
    report_parts.append("## Database Schema\n\n")
    report_parts.append("### Tables and Fields\n\n")
    
    tables = [
        ("runs", ["run_id", "dataset_fingerprint", "row_count", "column_count", "timestamp", "status", "composite_dqs"]),
        ("dimension_scores", ["run_id", "dimension", "score", "weight", "explainability (JSON)"]),
        ("check_results", ["run_id", "check_id", "dimension", "passed", "severity", "metrics (JSON)"]),
        ("agent_logs", ["run_id", "agent_name", "step_order", "inputs (JSON)", "outputs (JSON)", "timestamp"]),
        ("references", ["reference_id", "reference_type", "fingerprint", "row_count", "uploaded_at"]),
        ("artifacts", ["run_id", "artifact_type", "content", "created_at"])
    ]
    
    for table, fields in tables:
        report_parts.append(f"**{table}**\n")
        for field in fields:
            report_parts.append(f"- {field}\n")
        report_parts.append("\n")
    
    # Verification
    report_parts.append("## Verification\n\n")
    report_parts.append("To verify compliance:\n\n")
    report_parts.append("1. Inspect SQLite database file: `data/dqs.db`\n")
    report_parts.append("2. Query tables to confirm only metadata is present\n")
    report_parts.append("3. Check artifacts directory: `artifacts/` - should contain only JSON/YAML/MD files\n")
    report_parts.append("4. Review agent logs to confirm no raw data in inputs/outputs\n\n")
    
    # Footer
    report_parts.append("---\n\n")
    report_parts.append("*This report was automatically generated by the Data Quality Scoring Agent.*\n")
    report_parts.append("*For questions or compliance inquiries, contact the Data Governance team.*\n")
    
    return "".join(report_parts)
