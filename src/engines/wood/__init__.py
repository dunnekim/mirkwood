"""
WOOD Engine - Dual Module System

Module 1: DCF Valuation (Financial Modeling)
Module 2: Transaction Services (Risk Assessment)

[DCF Components]
- WACCCalculator: CAPM-based discount rate calculation
- DCFCalculator: Free cash flow projection and present value
- TerminalValueCalculator: Perpetual growth terminal value
- ScenarioRunner: Multi-scenario orchestration
- WoodOrchestrator: IB-grade DCF execution

[Transaction Services Components]
- WoodIssue, ForestMap: Domain models for TS findings
- WoodReportGenerator: Generate Forest Map reports
- MirkInput, WoodOutput: Interface contracts
- Issue Library: Sector-specific TS issue templates

Usage:
    # DCF Valuation
    from src.engines.orchestrator import WoodOrchestrator
    
    # Transaction Services
    from src.engines.wood import ForestMap, WoodReportGenerator
    from src.engines.wood.library_v01 import get_issue_library
"""

# DCF Components
from .wacc_calculator import WACCCalculator
from .dcf_calculator import DCFCalculator
from .terminal_value import TerminalValueCalculator
from .scenario_runner import ScenarioRunner

# Transaction Services Components
from .schema import (
    WoodIssue, ForestMap, 
    Severity, IssueType, Direction, Status
)
from .generator import WoodReportGenerator
from .interface import MirkInput, WoodOutput, WoodWorkflowStatus

__all__ = [
    # DCF
    'WACCCalculator',
    'DCFCalculator',
    'TerminalValueCalculator',
    'ScenarioRunner',
    
    # Transaction Services
    'WoodIssue',
    'ForestMap',
    'Severity',
    'IssueType',
    'Direction',
    'Status',
    'WoodReportGenerator',
    'MirkInput',
    'WoodOutput',
    'WoodWorkflowStatus'
]
