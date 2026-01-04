"""
Remediation Agent: Generates prioritized recommendations and remediation plans.
"""
from typing import Dict, Any, List
from datetime import datetime


class RemediationAgent:
    """Agent responsible for generating remediation recommendations."""
    
    def __init__(self):
        self.name = "RemediationAgent"
    
    def generate_remediation(self,
                           check_results: List[Dict[str, Any]],
                           scoring_result: Dict[str, Any],
                           issue_summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate prioritized remediation plan.
        
        Returns:
            RemediationResult with top issues, plan, and expected impact
        """
        start_time = datetime.now()
        
        # Rank issues by impact * frequency * criticality
        ranked_issues = self._rank_issues(check_results, scoring_result)
        
        # Generate remediation plan
        remediation_plan = self._generate_plan(ranked_issues)
        
        # Generate ticket payloads (optional)
        ticket_payloads = self._generate_tickets(ranked_issues[:5])  # Top 5
        
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return {
            "top_issues": ranked_issues[:10],  # Top 10
            "remediation_plan": remediation_plan,
            "ticket_payloads": ticket_payloads,
            "duration_ms": duration_ms
        }
    
    def _rank_issues(self,
                    check_results: List[Dict[str, Any]],
                    scoring_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Rank issues by priority score."""
        
        issues = []
        
        severity_scores = {
            "critical": 10,
            "high": 7,
            "medium": 4,
            "low": 2
        }
        
        impact_categories = {
            "completeness": "Operational",
            "uniqueness": "Financial",
            "validity": "Operational",
            "consistency": "Financial",
            "timeliness": "Operational",
            "integrity": "Regulatory",
            "reconciliation": "Financial"
        }
        
        for check in check_results:
            if not check.get("passed", True):
                # Calculate priority score
                severity = check.get("severity", "medium")
                severity_score = severity_scores.get(severity, 4)
                
                # Get frequency (error rate)
                frequency = self._extract_frequency(check)
                
                # Get criticality (dimension weight)
                dimension = check.get("dimension", "unknown")
                dim_score_data = scoring_result["dimension_scores"].get(dimension, {})
                criticality = dim_score_data.get("weight", 1.0)
                
                priority_score = severity_score * frequency * criticality
                
                # Simulate score gain if fixed
                expected_gain = self._estimate_score_gain(check, scoring_result)
                
                issue = {
                    "check_id": check["check_id"],
                    "dimension": dimension,
                    "severity": severity,
                    "priority_score": round(priority_score, 2),
                    "what": self._describe_issue(check),
                    "where": self._get_affected_columns(check),
                    "impact_category": impact_categories.get(dimension, "Operational"),
                    "frequency": round(frequency, 4),
                    "root_cause": self._infer_root_cause(check),
                    "fix_steps": self._generate_fix_steps(check),
                    "expected_score_gain": round(expected_gain, 2)
                }
                
                issues.append(issue)
        
        # Sort by priority score descending
        issues.sort(key=lambda x: x["priority_score"], reverse=True)
        
        return issues
    
    def _extract_frequency(self, check: Dict[str, Any]) -> float:
        """Extract error frequency from check metrics."""
        metrics = check.get("metrics", {})
        
        for field in ["overall_null_rate", "overall_duplicate_rate", "overall_invalid_rate",
                     "inconsistent_rate", "violation_rate", "excessive_delay_rate"]:
            if field in metrics:
                return float(metrics[field])
        
        for field in ["match_rate", "overall_reconciliation_rate"]:
            if field in metrics:
                return 1.0 - float(metrics[field])
        
        return 0.05  # Default
    
    def _estimate_score_gain(self, check: Dict[str, Any], scoring_result: Dict[str, Any]) -> float:
        """Estimate score gain if this issue is fixed."""
        dimension = check.get("dimension", "unknown")
        dim_score_data = scoring_result["dimension_scores"].get(dimension, {})
        current_score = dim_score_data.get("score", 100)
        
        # Estimate: fixing this check would improve dimension score
        frequency = self._extract_frequency(check)
        severity_multiplier = {
            "critical": 1.0,
            "high": 0.7,
            "medium": 0.4,
            "low": 0.2
        }
        
        severity = check.get("severity", "medium")
        multiplier = severity_multiplier.get(severity, 0.4)
        
        # Potential gain: frequency * 100 * multiplier
        potential_gain = frequency * 100 * multiplier
        
        # Cap at remaining headroom
        headroom = 100 - current_score
        gain = min(potential_gain, headroom)
        
        return gain
    
    def _describe_issue(self, check: Dict[str, Any]) -> str:
        """Describe the issue."""
        check_id = check["check_id"]
        metrics = check.get("metrics", {})
        
        descriptions = {
            "completeness_null_rates": "High percentage of missing values across dataset",
            "completeness_required_fields": "Critical required fields are missing or incomplete",
            "uniqueness_duplicates": "Duplicate transaction records detected",
            "validity_currency": "Invalid or non-standard currency codes",
            "validity_country": "Invalid or non-standard country codes",
            "validity_mcc": "Invalid MCC codes (not 4-digit or not in reference)",
            "validity_amount": "Invalid transaction amounts (negative or extreme outliers)",
            "consistency_status_settlement": "Settled transactions missing settlement dates",
            "consistency_currency_decimals": "Currency decimal places don't match rules",
            "consistency_time_ordering": "Event timestamps after settlement timestamps",
            "timeliness_event_lag": "Events processed beyond SLA timeframe",
            "timeliness_processing_delay": "Excessive delay between event and settlement",
            "reconciliation_bin": "Card BINs not found in reference mapping",
            "reconciliation_settlement": "Transactions don't match settlement ledger"
        }
        
        return descriptions.get(check_id, f"Issue in {check_id}")
    
    def _get_affected_columns(self, check: Dict[str, Any]) -> List[str]:
        """Get list of affected columns."""
        metrics = check.get("metrics", {})
        
        failing_columns = metrics.get("failing_columns", [])
        if failing_columns:
            if isinstance(failing_columns[0], dict):
                return [fc["column"] for fc in failing_columns]
            return failing_columns
        
        # Check for specific column references
        cols = []
        for key in ["currency_column", "amount_column", "status_column", "txn_id_column",
                   "settlement_column", "event_column"]:
            if key in metrics:
                cols.append(metrics[key])
        
        return cols if cols else ["multiple"]
    
    def _infer_root_cause(self, check: Dict[str, Any]) -> str:
        """Infer probable root cause."""
        check_id = check["check_id"]
        
        root_causes = {
            "completeness_null_rates": "Upstream system not populating all fields",
            "completeness_required_fields": "Data extraction incomplete or schema mismatch",
            "uniqueness_duplicates": "Missing deduplication logic or duplicate ingestion",
            "validity_currency": "Transformation error or non-standard source data",
            "validity_country": "Mapping error or invalid source values",
            "validity_mcc": "Merchant data quality issue or outdated reference",
            "validity_amount": "Data type conversion error or upstream calculation bug",
            "consistency_status_settlement": "Business logic gap in settlement process",
            "consistency_currency_decimals": "Currency conversion logic error",
            "consistency_time_ordering": "Clock skew or incorrect timestamp assignment",
            "timeliness_event_lag": "Batch processing delay or infrastructure bottleneck",
            "timeliness_processing_delay": "Settlement system performance issue",
            "reconciliation_bin": "BIN reference data incomplete or outdated",
            "reconciliation_settlement": "Settlement ledger sync issue or data drift"
        }
        
        return root_causes.get(check_id, "Unknown - requires investigation")
    
    def _generate_fix_steps(self, check: Dict[str, Any]) -> List[str]:
        """Generate actionable fix steps."""
        check_id = check["check_id"]
        
        fix_steps = {
            "completeness_null_rates": [
                "Investigate upstream data source for missing fields",
                "Add validation at ingestion to reject incomplete records",
                "Implement default values or imputation where appropriate"
            ],
            "completeness_required_fields": [
                "Update extraction query to include all required fields",
                "Add schema validation before processing",
                "Coordinate with upstream team to ensure field population"
            ],
            "uniqueness_duplicates": [
                "Implement deduplication logic based on transaction ID",
                "Add unique constraint to prevent duplicate ingestion",
                "Investigate source of duplicate data"
            ],
            "validity_currency": [
                "Add currency code validation against ISO 4217",
                "Standardize currency codes in transformation layer",
                "Update source system to use standard codes"
            ],
            "validity_country": [
                "Add country code validation against ISO 3166",
                "Implement mapping table for non-standard codes",
                "Cleanse existing data with correct codes"
            ],
            "validity_mcc": [
                "Validate MCC codes against reference list",
                "Update merchant data with correct MCC codes",
                "Refresh MCC reference data"
            ],
            "validity_amount": [
                "Add range validation for transaction amounts",
                "Investigate negative amounts and correct source",
                "Implement outlier detection and alerting"
            ],
            "consistency_status_settlement": [
                "Add business rule: SETTLED status requires settlement_date",
                "Backfill missing settlement dates where possible",
                "Update settlement process to populate dates"
            ],
            "consistency_currency_decimals": [
                "Implement currency-specific decimal validation",
                "Correct JPY and other zero-decimal currencies",
                "Add validation rule to transformation pipeline"
            ],
            "consistency_time_ordering": [
                "Investigate timestamp assignment logic",
                "Add validation: event_time <= settlement_time",
                "Fix clock synchronization issues if present"
            ],
            "timeliness_event_lag": [
                "Optimize batch processing schedule",
                "Add real-time processing for time-sensitive events",
                "Investigate and resolve infrastructure bottlenecks"
            ],
            "timeliness_processing_delay": [
                "Analyze settlement system performance",
                "Optimize settlement processing logic",
                "Add monitoring and alerting for delays"
            ],
            "reconciliation_bin": [
                "Update BIN reference data with missing entries",
                "Implement regular BIN data refresh process",
                "Add fallback logic for unknown BINs"
            ],
            "reconciliation_settlement": [
                "Investigate settlement ledger sync process",
                "Implement reconciliation workflow to identify mismatches",
                "Add automated alerts for reconciliation failures"
            ]
        }
        
        return fix_steps.get(check_id, [
            "Investigate root cause",
            "Implement validation logic",
            "Monitor for recurrence"
        ])
    
    def _generate_plan(self, ranked_issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate phased remediation plan."""
        
        # Phase 0 (P0): Critical and high severity with high priority
        p0_issues = [
            issue for issue in ranked_issues
            if issue["severity"] in ["critical", "high"] and issue["priority_score"] > 50
        ]
        
        # Phase 1 (P1): Remaining high severity or medium with high priority
        p1_issues = [
            issue for issue in ranked_issues
            if issue not in p0_issues and (
                issue["severity"] == "high" or
                (issue["severity"] == "medium" and issue["priority_score"] > 20)
            )
        ]
        
        # Phase 2 (P2): Everything else
        p2_issues = [
            issue for issue in ranked_issues
            if issue not in p0_issues and issue not in p1_issues
        ]
        
        return {
            "P0_immediate": {
                "count": len(p0_issues),
                "issues": [issue["check_id"] for issue in p0_issues],
                "expected_total_gain": sum(issue["expected_score_gain"] for issue in p0_issues),
                "timeline": "Immediate (1-2 days)"
            },
            "P1_next_sprint": {
                "count": len(p1_issues),
                "issues": [issue["check_id"] for issue in p1_issues],
                "expected_total_gain": sum(issue["expected_score_gain"] for issue in p1_issues),
                "timeline": "Next sprint (1-2 weeks)"
            },
            "P2_backlog": {
                "count": len(p2_issues),
                "issues": [issue["check_id"] for issue in p2_issues],
                "expected_total_gain": sum(issue["expected_score_gain"] for issue in p2_issues),
                "timeline": "Backlog (as capacity allows)"
            }
        }
    
    def _generate_tickets(self, top_issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate Jira-like ticket payloads."""
        
        tickets = []
        
        for issue in top_issues:
            ticket = {
                "title": f"[DQ] {issue['what']}",
                "description": f"""**Issue**: {issue['what']}

**Dimension**: {issue['dimension']}
**Severity**: {issue['severity']}
**Impact Category**: {issue['impact_category']}
**Affected Columns**: {', '.join(issue['where'])}

**Root Cause**: {issue['root_cause']}

**Fix Steps**:
{chr(10).join([f"{i+1}. {step}" for i, step in enumerate(issue['fix_steps'])])}

**Expected Score Gain**: +{issue['expected_score_gain']:.1f} points
**Priority Score**: {issue['priority_score']:.1f}
""",
                "priority": issue["severity"].upper(),
                "labels": ["data-quality", issue["dimension"], issue["impact_category"].lower()],
                "estimated_effort": self._estimate_effort(issue)
            }
            
            tickets.append(ticket)
        
        return tickets
    
    def _estimate_effort(self, issue: Dict[str, Any]) -> str:
        """Estimate effort to fix."""
        severity = issue["severity"]
        
        if severity == "critical":
            return "High (3-5 days)"
        elif severity == "high":
            return "Medium (1-3 days)"
        elif severity == "medium":
            return "Low (0.5-1 day)"
        else:
            return "Minimal (< 0.5 day)"
