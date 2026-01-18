"""
WOOD Transaction Services Engine - Report Generator

[Purpose]
Generate transaction services reports (Forest Map) in various formats:
- Markdown (for Telegram/documents)
- CSV (for Excel import)
- JSON (for API)
"""

from typing import List, Dict
from .schema import WoodIssue, ForestMap, Severity, IssueType
import csv
from io import StringIO


class WoodReportGenerator:
    """
    Generate transaction services reports
    
    Outputs follow IB/PE standard TS report format:
    1. Executive Summary (Key metrics)
    2. Top Issues (High/Med only)
    3. Negotiation Levers (Price/Structure/SPA)
    4. Detailed Findings (All issues)
    """
    
    def __init__(self):
        pass
    
    # ====================================================================
    # RISK SCORING
    # ====================================================================
    
    def calculate_risk_score(self, issues: List[WoodIssue]) -> int:
        """
        Calculate risk score from issues
        
        Scoring:
        - High severity: 3 points
        - Med severity: 1 point
        - Low severity: 0 points
        
        Returns:
            Total risk score
        """
        score = 0
        for issue in issues:
            if issue.severity == Severity.HIGH:
                score += 3
            elif issue.severity == Severity.MED:
                score += 1
        return score
    
    def assess_deal_status(self, score: int) -> str:
        """
        Assess deal recommendation based on risk score
        
        Thresholds:
        - 0-2: Proceed (Green light)
        - 3-5: Hold (Need validation)
        - 6+: Kill or Structure Required (Red light)
        
        Args:
            score: Risk score
        
        Returns:
            Deal status recommendation
        """
        if score <= 2:
            return "✅ Proceed"
        elif score <= 5:
            return "⚠️ Hold (Need Validation)"
        else:
            return "🚫 Kill or Structure Required"
    
    # ====================================================================
    # MARKDOWN REPORT
    # ====================================================================
    
    def generate_forest_map_md(self, forest_map: ForestMap) -> str:
        """
        Generate Forest Map report in Markdown
        
        Structure:
        1. Executive Summary
        2. Top Issues
        3. Negotiation Levers
        4. All Issues (detailed)
        
        Args:
            forest_map: ForestMap object
        
        Returns:
            Markdown formatted report
        """
        # Ensure metrics are calculated
        forest_map.calculate_metrics()
        
        md = []
        
        # ================================================================
        # HEADER: Executive Summary
        # ================================================================
        md.append(f"# 🌲 WOOD Forest Map: {forest_map.deal_name}\n")
        md.append("## 📊 Executive Summary\n")
        md.append("| Metric | Value |")
        md.append("|--------|-------|")
        md.append(f"| **QoE Adjustment** | **{forest_map.total_qoe_adj:+.1f}억** |")
        md.append(f"| **WC Adjustment** | **{forest_map.total_wc_adj:+.1f}억** |")
        md.append(f"| **Net Debt Adjustment** | **{forest_map.total_net_debt_adj:+.1f}억** |")
        md.append(f"| **Red Flags (High)** | **{forest_map.red_flag_count}** |")
        md.append(f"| **Risk Score** | **{forest_map.risk_score}** |")
        md.append(f"| **Deal Status** | **{forest_map.deal_status}** |\n")
        
        # Critical Actions
        high_issues = forest_map.get_issues_by_severity(Severity.HIGH)
        if high_issues:
            md.append("### 🚨 Critical Actions Required\n")
            for issue in high_issues[:3]:  # Top 3 critical
                md.append(f"- **{issue.title}**: {issue.lever}")
        md.append("")
        
        # ================================================================
        # TOP ISSUES: High and Med severity only
        # ================================================================
        md.append("## 🔍 Top Issues\n")
        
        top_issues = forest_map.get_top_issues(limit=10)
        high_and_med = [i for i in top_issues if i.severity in [Severity.HIGH, Severity.MED]]
        
        if not high_and_med:
            md.append("_No significant issues identified._\n")
        else:
            for idx, issue in enumerate(high_and_med, 1):
                severity_emoji = {
                    Severity.HIGH: "🔴",
                    Severity.MED: "🟡",
                    Severity.LOW: "🟢"
                }
                emoji = severity_emoji.get(issue.severity, "⚪")
                
                md.append(f"### {idx}. {emoji} {issue.title} `[{issue.id}]`\n")
                md.append(f"**Tags:** {', '.join(issue.tags)}\n")
                md.append(f"**What:** {issue.description}\n")
                
                if issue.evidence:
                    md.append(f"**Evidence:**")
                    for evd in issue.evidence:
                        md.append(f"- {evd}")
                    md.append("")
                
                if issue.quantification:
                    md.append(f"**Impact:** {issue.quantification}억 원\n")
                
                md.append(f"**Lever:** {issue.lever}\n")
                
                if issue.next_action:
                    md.append(f"**Next:** {issue.next_action}\n")
                
                md.append("---\n")
        
        # ================================================================
        # NEGOTIATION LEVERS: Grouped by category
        # ================================================================
        md.append("## 🎯 Negotiation Levers\n")
        
        levers = self._extract_levers(forest_map.issues)
        
        if levers['price']:
            md.append("### 💰 Price Adjustments\n")
            for lever in levers['price']:
                md.append(f"- {lever}")
            md.append("")
        
        if levers['net_debt']:
            md.append("### 📊 Net Debt Adjustments\n")
            for lever in levers['net_debt']:
                md.append(f"- {lever}")
            md.append("")
        
        if levers['structure']:
            md.append("### 🏗️ Structure / SPA Provisions\n")
            for lever in levers['structure']:
                md.append(f"- {lever}")
            md.append("")
        
        # ================================================================
        # APPENDIX: All Issues
        # ================================================================
        md.append("## 📋 All Issues (Detailed)\n")
        md.append(f"_Total: {len(forest_map.issues)} issues_\n")
        
        for issue in forest_map.issues:
            severity_emoji = {
                Severity.HIGH: "🔴",
                Severity.MED: "🟡",
                Severity.LOW: "🟢"
            }
            emoji = severity_emoji.get(issue.severity, "⚪")
            
            md.append(f"- {emoji} **{issue.title}** `[{issue.id}]` - {issue.lever}")
        
        md.append("\n---\n")
        md.append("_WOOD Transaction Services Engine - MIRKWOOD Partners_")
        
        return "\n".join(md)
    
    def _extract_levers(self, issues: List[WoodIssue]) -> Dict[str, List[str]]:
        """
        Extract and categorize negotiation levers from issues
        
        Categories:
        - price: Direct price adjustments
        - net_debt: Net debt definition changes
        - structure: Deal structure, SPA provisions, earn-outs
        
        Returns:
            Dict of categorized levers
        """
        levers = {
            'price': [],
            'net_debt': [],
            'structure': []
        }
        
        for issue in issues:
            lever_lower = issue.lever.lower()
            
            # Categorize by keywords
            if any(kw in lever_lower for kw in ['가격', '조정', 'price', 'qoe', 'ebitda']):
                levers['price'].append(f"{issue.title}: {issue.lever}")
            elif any(kw in lever_lower for kw in ['net debt', 'debt-like', '차입', '부채']):
                levers['net_debt'].append(f"{issue.title}: {issue.lever}")
            elif any(kw in lever_lower for kw in ['spa', 'r&w', 'earn-out', 'escrow', '구조', 'structure']):
                levers['structure'].append(f"{issue.title}: {issue.lever}")
            else:
                # Default to structure
                levers['structure'].append(f"{issue.title}: {issue.lever}")
        
        return levers
    
    # ====================================================================
    # CSV EXPORT (Bridge Analysis)
    # ====================================================================
    
    def generate_bridge_csv(self, issues: List[WoodIssue]) -> str:
        """
        Generate CSV for EBITDA/Net Debt bridge analysis
        
        Format:
        line_item, amount, tag, evidence_ref
        
        Args:
            issues: List of issues
        
        Returns:
            CSV formatted string
        """
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Line Item', 'Amount (bn KRW)', 'Category', 'Evidence', 'Issue ID'])
        
        # Data rows
        for issue in issues:
            if not issue.quantifiable or not issue.quantification:
                continue
            
            try:
                # Parse quantification (e.g., "-5.0 ~ -7.0")
                parts = issue.quantification.replace("~", "").split()
                if len(parts) >= 2:
                    low = float(parts[0])
                    high = float(parts[1])
                    avg_amount = (low + high) / 2
                else:
                    avg_amount = float(parts[0])
                
                # Get primary evidence
                evidence_text = issue.evidence[0] if issue.evidence else "N/A"
                
                # Get category from direction
                category = str(issue.direction.value) if issue.direction else "Other"
                
                writer.writerow([
                    issue.title,
                    f"{avg_amount:.1f}",
                    category,
                    evidence_text,
                    issue.id
                ])
            except:
                # Skip if parsing fails
                continue
        
        csv_content = output.getvalue()
        output.close()
        
        return csv_content
    
    # ====================================================================
    # SUMMARY TEXT (for Telegram)
    # ====================================================================
    
    def generate_summary_text(self, forest_map: ForestMap) -> str:
        """
        Generate compact summary for Telegram
        
        Args:
            forest_map: ForestMap object
        
        Returns:
            Short text summary
        """
        forest_map.calculate_metrics()
        
        text = f"🌲 **WOOD Analysis: {forest_map.deal_name}**\n\n"
        text += f"**Deal Status:** {forest_map.deal_status}\n"
        text += f"**Risk Score:** {forest_map.risk_score} (Red Flags: {forest_map.red_flag_count})\n\n"
        
        text += f"**Adjustments:**\n"
        text += f"• QoE: {forest_map.total_qoe_adj:+.1f}억\n"
        text += f"• WC: {forest_map.total_wc_adj:+.1f}억\n"
        text += f"• Net Debt: {forest_map.total_net_debt_adj:+.1f}억\n\n"
        
        # Top 3 issues
        high_issues = forest_map.get_issues_by_severity(Severity.HIGH)
        if high_issues:
            text += f"**Top Issues:**\n"
            for issue in high_issues[:3]:
                text += f"🔴 {issue.title}\n"
        
        text += "\n_Use /wood_report for detailed Forest Map_"
        
        return text
    
    # ====================================================================
    # JSON EXPORT
    # ====================================================================
    
    def generate_json(self, forest_map: ForestMap) -> dict:
        """
        Generate JSON representation of Forest Map
        
        Args:
            forest_map: ForestMap object
        
        Returns:
            Dict (JSON-serializable)
        """
        forest_map.calculate_metrics()
        return forest_map.dict()
