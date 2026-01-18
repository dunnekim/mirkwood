"""
WOOD Transaction Services Engine - Domain Model

[Purpose]
Define the schema for transaction services issues, risk assessment,
and deal structuring recommendations.

Transaction Services = Translating Risks into Price & Structure
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


# ========================================================================
# ENUMS
# ========================================================================

class Severity(str, Enum):
    """Issue severity classification"""
    HIGH = "High"      # Red flag - Deal breaker or major price impact
    MED = "Med"        # Yellow - Requires validation
    LOW = "Low"        # Green - Monitor only


class IssueType(str, Enum):
    """Issue categorization by financial impact area"""
    QOE = "QoE"                        # Quality of Earnings adjustment
    WC = "WC"                          # Working Capital normalization
    NET_DEBT = "NetDebt"               # Net Debt definition issues
    LEGAL_TAX = "Legal/Tax"            # Legal or tax exposures
    OPS = "Ops"                        # Operational risks
    REVENUE_QUALITY = "RevenueQuality" # Revenue recognition issues


class Direction(str, Enum):
    """Impact direction on deal metrics"""
    EBITDA_DOWN = "EBITDA_Down"        # Reduces normalized EBITDA
    EBITDA_UP = "EBITDA_Up"            # Increases normalized EBITDA
    NET_DEBT_UP = "NetDebt_Up"         # Increases net debt (debt-like items)
    NET_DEBT_DOWN = "NetDebt_Down"     # Reduces net debt
    WC_UP = "WC_Up"                    # Increases working capital need
    WC_DOWN = "WC_Down"                # Reduces working capital
    RISK_ONLY = "Risk_Only"            # Qualitative risk, no quantification


class Status(str, Enum):
    """Issue lifecycle status"""
    OPEN = "Open"                      # Identified but not analyzed
    VALIDATED = "Validated"            # Evidence confirmed
    QUANTIFIED = "Quantified"          # Impact calculated
    LEVERED = "Levered"                # Solution proposed
    CLOSED = "Closed"                  # Resolved or agreed


# ========================================================================
# DOMAIN MODELS
# ========================================================================

class WoodIssue(BaseModel):
    """
    Single transaction services issue
    
    Follows Wall Street TS report structure:
    - What (Description)
    - Why it matters (Impact)
    - How to solve (Lever)
    """
    id: str = Field(..., description="Unique issue ID (e.g., WOOD-CORE-01)")
    
    title: str = Field(..., description="Issue title")
    
    tags: List[str] = Field(
        default_factory=list,
        description="Classification tags (Type, Severity, Direction)"
    )
    
    description: str = Field(
        ...,
        description="What: Clear description of the issue"
    )
    
    evidence: List[str] = Field(
        default_factory=list,
        description="Supporting evidence or red flags observed"
    )
    
    quantification: Optional[str] = Field(
        None,
        description="Indicative impact range (e.g., '-5.0 ~ -7.0bn KRW')"
    )
    
    lever: str = Field(
        ...,
        description="How to solve: Price adjustment, structure, or SPA provision"
    )
    
    next_action: Optional[str] = Field(
        None,
        description="Action owner and due date"
    )
    
    quantifiable: bool = Field(
        default=True,
        description="Whether this issue can be quantified"
    )
    
    decision_impact: bool = Field(
        default=False,
        description="Whether this affects Proceed/Hold/Kill decision"
    )
    
    status: Status = Field(
        default=Status.OPEN,
        description="Current issue status"
    )
    
    # Parsed from tags for easy access
    @property
    def severity(self) -> Optional[Severity]:
        """Extract severity from tags"""
        for tag in self.tags:
            try:
                return Severity(tag)
            except ValueError:
                continue
        return None
    
    @property
    def issue_type(self) -> Optional[IssueType]:
        """Extract issue type from tags"""
        for tag in self.tags:
            try:
                return IssueType(tag)
            except ValueError:
                continue
        return None
    
    @property
    def direction(self) -> Optional[Direction]:
        """Extract impact direction from tags"""
        for tag in self.tags:
            try:
                return Direction(tag)
            except ValueError:
                continue
        return None


class ForestMap(BaseModel):
    """
    WOOD Dashboard - Complete view of transaction services findings
    
    The "Forest Map" shows all trees (issues) and the overall health
    of the target company.
    """
    deal_name: str = Field(..., description="Target company or deal codename")
    
    total_qoe_adj: float = Field(
        0.0,
        description="Total Quality of Earnings adjustment (bn KRW)"
    )
    
    total_wc_adj: float = Field(
        0.0,
        description="Total Working Capital adjustment (bn KRW)"
    )
    
    total_net_debt_adj: float = Field(
        0.0,
        description="Total Net Debt adjustment (bn KRW)"
    )
    
    red_flag_count: int = Field(
        0,
        description="Number of High severity issues"
    )
    
    issues: List[WoodIssue] = Field(
        default_factory=list,
        description="All identified issues"
    )
    
    risk_score: int = Field(
        0,
        description="Calculated risk score (High=3, Med=1, Low=0)"
    )
    
    deal_status: str = Field(
        "Unknown",
        description="Proceed / Hold / Kill recommendation"
    )
    
    def calculate_metrics(self):
        """
        Calculate all derived metrics from issues
        
        This should be called after adding all issues to update
        aggregated metrics.
        """
        # Reset metrics
        self.total_qoe_adj = 0.0
        self.total_wc_adj = 0.0
        self.total_net_debt_adj = 0.0
        self.red_flag_count = 0
        self.risk_score = 0
        
        for issue in self.issues:
            # Count red flags
            if issue.severity == Severity.HIGH:
                self.red_flag_count += 1
                self.risk_score += 3
            elif issue.severity == Severity.MED:
                self.risk_score += 1
            
            # Sum financial impacts (if quantifiable)
            if issue.quantification and issue.quantifiable:
                try:
                    # Parse quantification string (e.g., "-5.0 ~ -7.0")
                    parts = issue.quantification.replace("~", "").split()
                    if len(parts) >= 2:
                        # Take average of range
                        low = float(parts[0])
                        high = float(parts[1])
                        avg_impact = (low + high) / 2
                        
                        # Allocate to appropriate category
                        if issue.direction == Direction.EBITDA_DOWN:
                            self.total_qoe_adj += avg_impact
                        elif issue.direction == Direction.EBITDA_UP:
                            self.total_qoe_adj += avg_impact
                        elif issue.direction in [Direction.NET_DEBT_UP, Direction.NET_DEBT_DOWN]:
                            self.total_net_debt_adj += avg_impact
                        elif issue.direction in [Direction.WC_UP, Direction.WC_DOWN]:
                            self.total_wc_adj += avg_impact
                except:
                    # If parsing fails, skip
                    pass
        
        # Determine deal status based on risk score
        if self.risk_score <= 2:
            self.deal_status = "Proceed"
        elif self.risk_score <= 5:
            self.deal_status = "Hold (Need Validation)"
        else:
            self.deal_status = "Kill or Structure Required"
    
    def get_top_issues(self, limit: int = 10) -> List[WoodIssue]:
        """
        Get top issues by severity
        
        Sorted by: High > Med > Low, then by decision_impact
        """
        severity_order = {Severity.HIGH: 0, Severity.MED: 1, Severity.LOW: 2}
        
        sorted_issues = sorted(
            self.issues,
            key=lambda x: (
                severity_order.get(x.severity, 3),
                not x.decision_impact
            )
        )
        
        return sorted_issues[:limit]
    
    def get_issues_by_severity(self, severity: Severity) -> List[WoodIssue]:
        """Get all issues of specific severity"""
        return [issue for issue in self.issues if issue.severity == severity]
    
    def get_issues_by_type(self, issue_type: IssueType) -> List[WoodIssue]:
        """Get all issues of specific type"""
        return [issue for issue in self.issues if issue.issue_type == issue_type]
