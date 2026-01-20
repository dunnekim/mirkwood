"""
WOOD V2 Engine - Data Models (Pydantic-based)

[Architecture]
These are the typed data structures for WOOD V2 Engine.
Using dataclasses for simplicity and type safety.
"""

from dataclasses import dataclass, field
from typing import List, Optional


# ==============================================================================
# INPUT MODELS
# ==============================================================================

@dataclass
class Assumptions:
    """
    Core assumptions for DCF valuation
    
    [IB Standard]
    All rates are in decimal format (e.g., 0.10 = 10%)
    """
    # Market parameters
    risk_free_rate: float = 0.035  # 3.5% KRW 3Y Treasury
    market_risk_premium: float = 0.08  # 8.0% (KICPA Standard for Korea)
    
    # Company-specific
    tax_rate: float = 0.22  # 22% Korean corporate tax
    terminal_growth_rate: float = 0.02  # 2% perpetual growth
    
    # Capital structure
    target_debt_ratio: float = 0.30  # D/E ratio
    cost_of_debt_pretax: float = 0.045  # 4.5%
    
    # Size risk premium (for Korean unlisted companies)
    is_listed: bool = False
    size_metric_mil_krw: float = 15000  # 150억 KRW (net assets or market cap)
    
    # Projection settings
    projection_years: int = 5


@dataclass
class ScenarioParameters:
    """
    Scenario-specific parameters (Base/Bull/Bear)
    """
    name: str
    revenue_growth: float
    ebitda_margin: float
    ebit_margin: float
    
    # FCF build-up ratios
    da_ratio: float = 0.05  # D&A as % of revenue
    capex_ratio: float = 0.04  # Capex as % of revenue
    nwc_ratio: float = 0.10  # NWC as % of revenue
    
    # WACC adjustment
    wacc_premium: float = 0.0  # Additional premium/discount to WACC


@dataclass
class PeerCompany:
    """
    Peer company data for beta calculation
    """
    name: str
    ticker: Optional[str] = None  # For live beta fetch (e.g., "005930.KS")
    static_beta: float = 1.0  # Fallback beta
    debt_equity_ratio: float = 0.30
    tax_rate: float = 0.22


# ==============================================================================
# OUTPUT MODELS
# ==============================================================================

@dataclass
class WACCOutput:
    """
    Detailed WACC calculation output
    
    [IB Transparency]
    Shows full build-up for audit trail
    """
    # Final outputs
    wacc: float
    cost_of_equity: float
    cost_of_debt_after_tax: float
    
    # Build-up components
    risk_free_rate: float
    beta_levered: float
    beta_unlevered: float
    market_risk_premium: float
    size_risk_premium: float
    srp_quintile: int
    srp_description: str
    
    # Capital structure
    debt_weight: float
    equity_weight: float
    
    # Metadata
    beta_source: str = "Static"  # "Live" or "Static"
    peer_count: int = 0


@dataclass
class TerminalValueOutput:
    """
    Terminal value calculation output
    """
    tv_gordon: float  # Gordon Growth Model
    tv_exit_multiple: float  # Exit Multiple Method
    implied_ebitda_multiple: float
    terminal_growth_rate: float
    exit_multiple_assumption: float


@dataclass
class DCFOutput:
    """
    Complete DCF valuation output for one scenario
    """
    scenario_name: str
    enterprise_value: float
    pv_fcf: float
    pv_terminal: float
    
    wacc_output: WACCOutput
    terminal_value_output: TerminalValueOutput
    
    # Additional metrics
    fcf_projection: List[float] = field(default_factory=list)
    revenue_projection: List[float] = field(default_factory=list)
    ebitda_projection: List[float] = field(default_factory=list)


@dataclass
class ValuationSummary:
    """
    Multi-scenario valuation summary
    """
    project_name: str
    data_source: str
    base_revenue: float
    
    scenarios: List[DCFOutput]
    
    # Range analysis
    ev_min: float
    ev_max: float
    ev_base: float
    
    # Timestamp
    created_at: str = ""
