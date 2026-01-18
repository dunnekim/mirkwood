"""
WOOD Transaction Services Engine - Interface Contract

[Purpose]
Define data exchange contracts between MIRK (CF) and WOOD (TS).

MIRK = Corporate Finance (Deal origination, valuation)
WOOD = Transaction Services (Due diligence, risk assessment)
"""

from dataclasses import dataclass, field
from typing import List, Optional


# ========================================================================
# MIRK → WOOD (Input)
# ========================================================================

@dataclass
class MirkInput:
    """
    Input from MIRK to WOOD
    
    MIRK provides deal context so WOOD can tailor its analysis:
    - Deal rationale (why this target?)
    - Valuation approach (multiple vs DCF)
    - Constraints (non-negotiables)
    """
    
    deal_name: str
    """Deal codename or target company name"""
    
    sector: str
    """Target sector (Game, Commerce, Manufacturing, etc.)"""
    
    deal_rationale: str
    """
    Why this deal?
    e.g., "Strategic buyer seeking market entry in K-Beauty"
    """
    
    valuation_method: str
    """
    Valuation approach used by MIRK
    e.g., "EV/EBITDA multiple", "DCF", "PSR"
    """
    
    target_ebitda: Optional[float] = None
    """Target's reported EBITDA (bn KRW)"""
    
    target_net_debt: Optional[float] = None
    """Target's reported Net Debt (bn KRW)"""
    
    target_wc: Optional[float] = None
    """Target's working capital (bn KRW)"""
    
    constraints: List[str] = field(default_factory=list)
    """
    Non-negotiable constraints
    e.g., ["Management must stay", "No price reduction allowed", "Close by Q1"]
    """
    
    focus_areas: List[str] = field(default_factory=list)
    """
    Areas MIRK wants WOOD to focus on
    e.g., ["Revenue quality", "Customer concentration", "IP risks"]
    """
    
    timeline: str = "Standard"
    """DD timeline: Express (<1 week), Standard (2 weeks), Deep Dive (4+ weeks)"""


# ========================================================================
# WOOD → MIRK (Output)
# ========================================================================

@dataclass
class WoodOutput:
    """
    Output from WOOD to MIRK
    
    WOOD provides actionable findings that MIRK can use for:
    - Price negotiation
    - Deal structuring
    - SPA drafting
    """
    
    deal_name: str
    """Deal codename"""
    
    deal_status: str
    """
    Recommendation: Proceed / Hold / Kill
    """
    
    risk_score: int
    """Calculated risk score (High=3, Med=1, Low=0)"""
    
    normalized_ebitda_range: str
    """
    Adjusted EBITDA range after QoE adjustments
    e.g., "45.0 ~ 48.0"
    """
    
    net_debt_items: List[str]
    """
    Debt-like items that should be included in Net Debt definition
    e.g., ["Operating leases (15억)", "Customer deposits (8억)", "Guarantees (3억)"]
    """
    
    wc_peg_range: str
    """
    Recommended Working Capital peg (normalized level)
    e.g., "35.0 ~ 40.0"
    """
    
    top_3_levers: List[str]
    """
    Top 3 negotiation levers MIRK should focus on
    e.g., [
        "Price reduction: 8-12억 (Revenue cut-off issue)",
        "Net Debt adjustment: Add 15억 for leases",
        "SPA R&W: Revenue recognition policy indemnity"
    ]
    """
    
    red_flags: List[str] = field(default_factory=list)
    """
    High severity issues (deal breakers)
    """
    
    structure_recommendations: List[str] = field(default_factory=list)
    """
    Recommended deal structures to mitigate risks
    e.g., ["Earn-out tied to revenue retention", "Escrow 10% for 12 months"]
    """
    
    next_actions: List[str] = field(default_factory=list)
    """
    Immediate next steps for MIRK
    e.g., ["Request customer contracts", "Verify IP license terms", "Get auditor memo"]
    """
    
    full_report_path: Optional[str] = None
    """Path to full Forest Map report (Markdown/PDF)"""


# ========================================================================
# WOOD ↔ EXTERNAL (Data Sources)
# ========================================================================

@dataclass
class ExternalDataRequest:
    """
    Request for external data (from target company or advisors)
    
    WOOD needs this data to validate findings
    """
    
    document_type: str
    """Type of document requested (e.g., "Financial Statements", "Customer Contracts")"""
    
    description: str
    """Detailed description of what's needed"""
    
    purpose: str
    """Why WOOD needs this data"""
    
    urgency: str
    """High / Medium / Low"""
    
    owner: str
    """Who should provide this (Target CFO / Legal / etc.)"""
    
    due_date: Optional[str] = None
    """Deadline (YYYY-MM-DD)"""


@dataclass
class ExternalDataResponse:
    """
    Response with external data
    """
    
    request_id: str
    """ID of the original request"""
    
    document_name: str
    """Name of provided document"""
    
    file_path: Optional[str] = None
    """Path to file if uploaded"""
    
    summary: str
    """Brief summary of contents"""
    
    analyst_notes: Optional[str] = None
    """Notes from analyst who reviewed this"""


# ========================================================================
# WORKFLOW STATUS
# ========================================================================

@dataclass
class WoodWorkflowStatus:
    """
    Current status of WOOD analysis
    """
    
    deal_name: str
    """Deal codename"""
    
    stage: str
    """
    Current stage:
    - Initial: Just started
    - Data Collection: Gathering documents
    - Analysis: Identifying issues
    - Quantification: Calculating impacts
    - Report: Generating Forest Map
    - Complete: Done
    """
    
    progress_pct: int
    """Progress percentage (0-100)"""
    
    issues_identified: int
    """Number of issues identified so far"""
    
    red_flags: int
    """Number of High severity issues"""
    
    blockers: List[str] = field(default_factory=list)
    """What's blocking progress"""
    
    estimated_completion: Optional[str] = None
    """Estimated completion date (YYYY-MM-DD)"""
    
    last_updated: Optional[str] = None
    """Last update timestamp"""
