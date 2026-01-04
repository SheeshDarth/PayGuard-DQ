"""
Explainer Agent: Generates human-readable narratives and issue summaries.
Supports both LLM mode (OpenAI-compatible) and deterministic stub mode.
"""
import os
from typing import Dict, Any, List, Optional
from datetime import datetime


class ExplainerAgent:
    """Agent responsible for generating explanations and narratives."""
    
    def __init__(self, use_llm: bool = None):
        self.name = "ExplainerAgent"
        
        # Auto-detect LLM availability
        if use_llm is None:
            api_key = os.getenv("OPENAI_API_KEY", "")
            self.use_llm = bool(api_key and api_key.strip())
        else:
            self.use_llm = use_llm
        
        if self.use_llm:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            except Exception:
                self.use_llm = False
                self.client = None
        else:
            self.client = None
    
    def explain(self,
               scoring_result: Dict[str, Any],
               check_results: List[Dict[str, Any]],
               profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate explanations and issue summaries.
        
        Returns:
            ExplainerResult with narrative and issue summaries
        """
        start_time = datetime.now()
        
        if self.use_llm and self.client:
            result = self._explain_with_llm(scoring_result, check_results, profile)
        else:
            result = self._explain_with_stub(scoring_result, check_results, profile)
        
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        result["duration_ms"] = duration_ms
        result["mode"] = "llm" if self.use_llm else "stub"
        
        return result
    
    def _explain_with_llm(self,
                         scoring_result: Dict[str, Any],
                         check_results: List[Dict[str, Any]],
                         profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate explanations using LLM."""
        
        # Prepare aggregated data for LLM (NO RAW DATA)
        summary_data = {
            "composite_dqs": scoring_result["composite_dqs"],
            "dimension_scores": {
                dim: data["score"] 
                for dim, data in scoring_result["dimension_scores"].items()
            },
            "row_count": profile["row_count"],
            "column_count": profile["column_count"],
            "failing_checks": []
        }
        
        for check in check_results:
            if not check.get("passed", True):
                summary_data["failing_checks"].append({
                    "check_id": check["check_id"],
                    "dimension": check["dimension"],
                    "severity": check["severity"],
                    "metrics": check.get("metrics", {})
                })
        
        # Create prompt
        prompt = f"""You are a data quality expert analyzing payment transaction data.

Dataset Summary:
- Rows: {summary_data['row_count']}
- Columns: {summary_data['column_count']}
- Overall DQS: {summary_data['composite_dqs']}/100

Dimension Scores:
{self._format_dimension_scores(summary_data['dimension_scores'])}

Failing Checks: {len(summary_data['failing_checks'])}

Generate a concise narrative (2-3 paragraphs) explaining:
1. Overall data quality assessment
2. Key issues and their business impact
3. Priority areas for remediation

Keep it professional and actionable."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a data quality expert for payment systems."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            narrative = response.choices[0].message.content
        except Exception as e:
            # Fallback to stub if LLM fails
            narrative = f"LLM generation failed: {str(e)}. Falling back to deterministic mode."
            return self._explain_with_stub(scoring_result, check_results, profile)
        
        # Generate issue summaries
        issue_summaries = self._generate_issue_summaries(check_results)
        
        return {
            "narrative": narrative,
            "issue_summaries": issue_summaries
        }
    
    def _explain_with_stub(self,
                          scoring_result: Dict[str, Any],
                          check_results: List[Dict[str, Any]],
                          profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate explanations using deterministic templates."""
        
        composite_dqs = scoring_result["composite_dqs"]
        dimension_scores = scoring_result["dimension_scores"]
        
        # Generate narrative using templates
        narrative_parts = []
        
        # Overall assessment
        if composite_dqs >= 90:
            quality_level = "excellent"
            assessment = "The dataset demonstrates excellent data quality with minimal issues."
        elif composite_dqs >= 75:
            quality_level = "good"
            assessment = "The dataset shows good data quality with some areas requiring attention."
        elif composite_dqs >= 60:
            quality_level = "fair"
            assessment = "The dataset has fair data quality with several issues that need remediation."
        else:
            quality_level = "poor"
            assessment = "The dataset exhibits poor data quality with critical issues requiring immediate attention."
        
        narrative_parts.append(
            f"**Overall Assessment**: The dataset achieved a Data Quality Score (DQS) of {composite_dqs}/100, "
            f"indicating {quality_level} quality. {assessment}"
        )
        
        # Dimension analysis
        failing_dimensions = [
            (dim, data["score"]) 
            for dim, data in dimension_scores.items() 
            if data["score"] < 80
        ]
        
        if failing_dimensions:
            failing_dimensions.sort(key=lambda x: x[1])  # Sort by score ascending
            dim_list = ", ".join([f"{dim} ({score:.1f})" for dim, score in failing_dimensions[:3]])
            narrative_parts.append(
                f"\n\n**Key Issues**: The primary quality concerns are in {dim_list}. "
                f"These dimensions show elevated error rates that could impact downstream processing and analytics."
            )
        else:
            narrative_parts.append(
                "\n\n**Key Issues**: All quality dimensions meet acceptable thresholds. "
                "Continue monitoring for any degradation in future batches."
            )
        
        # Remediation priority
        critical_checks = [c for c in check_results if c.get("severity") == "critical" and not c.get("passed", True)]
        high_checks = [c for c in check_results if c.get("severity") == "high" and not c.get("passed", True)]
        
        if critical_checks:
            narrative_parts.append(
                f"\n\n**Priority Actions**: {len(critical_checks)} critical issues require immediate remediation. "
                f"Focus on {critical_checks[0]['dimension']} dimension first, as it has the highest business impact. "
                f"Additionally, {len(high_checks)} high-severity issues should be addressed in the next sprint."
            )
        elif high_checks:
            narrative_parts.append(
                f"\n\n**Priority Actions**: {len(high_checks)} high-severity issues should be addressed. "
                f"While not critical, these issues could lead to operational inefficiencies if left unresolved."
            )
        else:
            narrative_parts.append(
                "\n\n**Priority Actions**: No critical or high-severity issues detected. "
                "Focus on continuous improvement and monitoring of medium/low severity items."
            )
        
        narrative = "".join(narrative_parts)
        
        # Generate issue summaries
        issue_summaries = self._generate_issue_summaries(check_results)
        
        return {
            "narrative": narrative,
            "issue_summaries": issue_summaries
        }
    
    def _generate_issue_summaries(self, check_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate structured issue summaries."""
        
        summaries = []
        
        for check in check_results:
            if not check.get("passed", True):
                summary = {
                    "check_id": check["check_id"],
                    "dimension": check["dimension"],
                    "severity": check["severity"],
                    "what": self._describe_what(check),
                    "where": self._describe_where(check),
                    "root_cause": self._infer_root_cause(check)
                }
                summaries.append(summary)
        
        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        summaries.sort(key=lambda x: severity_order.get(x["severity"], 3))
        
        return summaries
    
    def _describe_what(self, check: Dict[str, Any]) -> str:
        """Describe what failed."""
        check_id = check["check_id"]
        metrics = check.get("metrics", {})
        
        templates = {
            "completeness_null_rates": f"High null rate detected ({metrics.get('overall_null_rate', 0):.1%})",
            "completeness_required_fields": f"Required fields missing or incomplete",
            "uniqueness_duplicates": f"Duplicate records found ({metrics.get('overall_duplicate_rate', 0):.1%})",
            "validity_currency": f"Invalid currency codes ({metrics.get('overall_invalid_rate', 0):.1%})",
            "validity_country": f"Invalid country codes ({metrics.get('overall_invalid_rate', 0):.1%})",
            "validity_mcc": f"Invalid MCC codes ({metrics.get('overall_invalid_rate', 0):.1%})",
            "validity_amount": f"Invalid amounts (negative or outliers)",
            "consistency_status_settlement": f"Status-settlement inconsistencies ({metrics.get('inconsistent_rate', 0):.1%})",
            "consistency_currency_decimals": f"Currency decimal mismatches",
            "consistency_time_ordering": f"Time ordering violations ({metrics.get('misordered_rate', 0):.1%})",
            "timeliness_event_lag": f"SLA violations ({metrics.get('violation_rate', 0):.1%})",
            "timeliness_processing_delay": f"Excessive processing delays",
            "reconciliation_bin": f"BIN reconciliation failures ({1 - metrics.get('match_rate', 1):.1%})",
            "reconciliation_settlement": f"Settlement reconciliation failures ({1 - metrics.get('overall_reconciliation_rate', 1):.1%})"
        }
        
        return templates.get(check_id, f"Check {check_id} failed")
    
    def _describe_where(self, check: Dict[str, Any]) -> str:
        """Describe where the issue occurs."""
        metrics = check.get("metrics", {})
        
        failing_columns = metrics.get("failing_columns", [])
        if failing_columns:
            if isinstance(failing_columns[0], dict):
                cols = [fc["column"] for fc in failing_columns[:3]]
            else:
                cols = failing_columns[:3]
            return f"Columns: {', '.join(cols)}"
        
        # Check for specific column references
        for key in ["currency_column", "amount_column", "status_column", "txn_id_column"]:
            if key in metrics:
                return f"Column: {metrics[key]}"
        
        return "Multiple columns affected"
    
    def _infer_root_cause(self, check: Dict[str, Any]) -> str:
        """Infer probable root cause."""
        dimension = check["dimension"]
        check_id = check["check_id"]
        
        root_causes = {
            "completeness": "Upstream data source may be incomplete or extraction process is missing fields",
            "uniqueness": "Duplicate data ingestion or missing deduplication logic",
            "validity": "Data transformation errors or missing validation at source",
            "consistency": "Cross-field validation missing or business logic errors",
            "timeliness": "Processing delays or batch scheduling issues",
            "integrity": "Reference data out of sync or missing foreign key validation",
            "reconciliation": "Data drift between systems or settlement process errors"
        }
        
        return root_causes.get(dimension, "Unknown root cause")
    
    def _format_dimension_scores(self, scores: Dict[str, float]) -> str:
        """Format dimension scores for LLM prompt."""
        return "\n".join([f"- {dim}: {score:.1f}/100" for dim, score in scores.items()])
