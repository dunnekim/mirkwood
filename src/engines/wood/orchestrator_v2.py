"""
WOOD V2 Engine - Orchestrator (Nexflex Standard)

[Architecture]
Modular, testable, IB-grade DCF valuation system with:
1. Live market beta integration
2. Korean SRP (KICPA standard)
3. Full FCF build-up (EBIT → NOPAT → FCF)
4. Dual terminal value methods
5. Multi-scenario analysis
6. Professional Excel export

[Changes from V1]
- Modular calculator structure (wacc/, fcf/, terminal_value/)
- Live beta from market data (MarketScanner)
- Typed data models (dataclasses)
- Enhanced Excel exporter (9-sheet model)
"""

import os
import json
import logging
from datetime import datetime
from typing import Tuple, List
import pandas as pd

# Local imports
from .models import (
    Assumptions, ScenarioParameters, PeerCompany,
    DCFOutput, ValuationSummary, WACCOutput
)
from .calculators.wacc import WACCCalculator
from .calculators.fcf import FCFCalculator
from .calculators.terminal_value import TerminalValueCalculator


class WoodOrchestratorV2:
    """
    WOOD V2 Engine - Main orchestrator
    
    [IB Standard]
    Professional DCF valuation with:
    - Live market data integration
    - Korean KICPA standards (SRP, MRP)
    - Transparent build-up (audit trail)
    - Multi-scenario analysis
    - Sensitivity tables
    
    [Usage]
    orchestrator = WoodOrchestratorV2()
    filepath, summary = orchestrator.run_valuation(
        "CompanyA", 
        base_revenue=500.0,
        data_source="DART 2024.3Q"
    )
    """
    
    def __init__(self, config_path: str = None, use_live_beta: bool = True):
        """
        Args:
            config_path: Path to config.json (default: auto-detect)
            use_live_beta: Enable live beta calculation
        """
        # Paths
        if config_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, 'config.json')
        
        self.config_path = config_path
        self.config = self._load_config()
        
        # Output directory
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.output_dir = os.path.join(project_root, 'vault', 'reports')
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize calculators
        self.wacc_calculator = WACCCalculator(use_live_beta=use_live_beta)
        self.fcf_calculator = FCFCalculator()
        self.tv_calculator = TerminalValueCalculator(exit_multiple=8.0)
        
        logging.info("🌲 WOOD V2 Engine initialized (Nexflex Standard)")
        if use_live_beta:
            logging.info("   📊 Live market beta: Enabled")
    
    def _load_config(self) -> dict:
        """Load config.json"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _build_assumptions(self) -> Assumptions:
        """
        Build Assumptions object from config
        """
        settings = self.config['project_settings']
        
        return Assumptions(
            risk_free_rate=settings.get('risk_free_rate', 0.035),
            market_risk_premium=settings.get('market_risk_premium', 0.08),
            tax_rate=settings.get('tax_rate', 0.22),
            terminal_growth_rate=settings.get('terminal_growth_rate', 0.02),
            target_debt_ratio=0.30,  # Default D/E
            cost_of_debt_pretax=0.045,
            is_listed=False,  # Default unlisted
            size_metric_mil_krw=15000,  # 150억 KRW
            projection_years=5
        )
    
    def _build_scenario(self, name: str, params: dict) -> ScenarioParameters:
        """
        Build ScenarioParameters from config dict
        """
        return ScenarioParameters(
            name=name,
            revenue_growth=params['revenue_growth'],
            ebitda_margin=params.get('ebitda_margin', params['ebit_margin'] + 0.03),
            ebit_margin=params['ebit_margin'],
            da_ratio=params.get('da_ratio', 0.03),
            capex_ratio=params.get('capex_ratio', 0.03),
            nwc_ratio=params.get('nwc_ratio', 0.05),
            wacc_premium=params.get('wacc_premium', 0.0)
        )
    
    def _build_peers(self) -> List[dict]:
        """
        Build peer list from config
        """
        peer_group = self.config.get('peer_group', [])
        
        peers = []
        for peer in peer_group:
            peers.append({
                'name': peer['name'],
                'ticker': peer.get('ticker'),
                'static_beta': peer.get('beta', 1.0),
                'debt_equity_ratio': peer.get('debt_equity_ratio', 0.30),
                'tax_rate': peer.get('tax_rate', 0.22)
            })
        
        return peers
    
    def _calculate_dcf_scenario(
        self,
        scenario: ScenarioParameters,
        base_revenue: float,
        assumptions: Assumptions,
        peers: List[dict]
    ) -> DCFOutput:
        """
        Execute DCF valuation for one scenario
        
        [Process]
        1. Calculate WACC (live beta + SRP)
        2. Project FCF (detailed waterfall)
        3. Discount FCFs to present value
        4. Calculate terminal value (dual method)
        5. Sum to enterprise value
        
        Args:
            scenario: Scenario parameters
            base_revenue: Base revenue
            assumptions: Core assumptions
            peers: Peer company list
        
        Returns:
            DCFOutput with full results
        """
        logging.info(f"   📊 Scenario: {scenario.name}")
        
        # ============================================================
        # STEP 1: WACC
        # ============================================================
        wacc_output = self.wacc_calculator.calculate(
            assumptions, 
            peers,
            scenario_wacc_premium=scenario.wacc_premium
        )
        
        wacc = wacc_output.wacc
        logging.info(f"      WACC: {wacc*100:.2f}%")
        
        # ============================================================
        # STEP 2: FCF PROJECTION
        # ============================================================
        fcf_df = self.fcf_calculator.project(
            base_revenue, 
            scenario, 
            assumptions
        )
        
        fcf_series = fcf_df['FCF'].tolist()
        
        # ============================================================
        # STEP 3: DISCOUNT FCFs
        # ============================================================
        discount_factors = [1 / ((1 + wacc) ** i) for i in range(1, len(fcf_series) + 1)]
        pv_fcfs = [fcf * df for fcf, df in zip(fcf_series, discount_factors)]
        sum_pv_fcf = sum(pv_fcfs)
        
        # Add PV columns to DataFrame
        fcf_df['Discount_Factor'] = discount_factors
        fcf_df['PV_FCF'] = pv_fcfs
        
        # ============================================================
        # STEP 4: TERMINAL VALUE
        # ============================================================
        last_fcf = fcf_series[-1]
        last_ebitda = fcf_df['EBITDA'].iloc[-1]
        
        tv_output = self.tv_calculator.calculate(
            last_fcf,
            last_ebitda,
            wacc,
            assumptions.terminal_growth_rate
        )
        
        # PV of Terminal Value
        pv_terminal = tv_output.tv_gordon * discount_factors[-1]
        
        # ============================================================
        # STEP 5: ENTERPRISE VALUE
        # ============================================================
        enterprise_value = sum_pv_fcf + pv_terminal
        
        logging.info(f"      EV: {enterprise_value:.1f}억 원")
        
        # ============================================================
        # BUILD OUTPUT
        # ============================================================
        return DCFOutput(
            scenario_name=scenario.name,
            enterprise_value=enterprise_value,
            pv_fcf=sum_pv_fcf,
            pv_terminal=pv_terminal,
            wacc_output=wacc_output,
            terminal_value_output=tv_output,
            fcf_projection=fcf_series,
            revenue_projection=fcf_df['Revenue'].tolist(),
            ebitda_projection=fcf_df['EBITDA'].tolist()
        )
    
    def run_valuation(
        self,
        project_name: str,
        base_revenue: float = 100.0,
        data_source: str = "User Input"
    ) -> Tuple[str, str]:
        """
        Execute full multi-scenario DCF valuation
        
        Args:
            project_name: Company/project name
            base_revenue: Base year revenue (억 원)
            data_source: Data attribution (e.g., "DART 2024.3Q")
        
        Returns:
            (filepath, summary_text): Excel file path and summary
        """
        logging.info(f"🌲 WOOD V2: DCF Valuation for '{project_name}'")
        logging.info(f"   Base Revenue: {base_revenue:.1f}억 원")
        logging.info(f"   Data Source: {data_source}")
        
        # ============================================================
        # SETUP
        # ============================================================
        assumptions = self._build_assumptions()
        peers = self._build_peers()
        scenarios_config = self.config['scenarios']
        
        # ============================================================
        # RUN SCENARIOS
        # ============================================================
        dcf_results: List[DCFOutput] = []
        
        for scenario_name, scenario_params in scenarios_config.items():
            scenario = self._build_scenario(scenario_name, scenario_params)
            
            result = self._calculate_dcf_scenario(
                scenario,
                base_revenue,
                assumptions,
                peers
            )
            
            dcf_results.append(result)
        
        # ============================================================
        # VALUATION SUMMARY
        # ============================================================
        evs = [r.enterprise_value for r in dcf_results]
        
        valuation_summary = ValuationSummary(
            project_name=project_name,
            data_source=data_source,
            base_revenue=base_revenue,
            scenarios=dcf_results,
            ev_min=min(evs),
            ev_max=max(evs),
            ev_base=dcf_results[0].enterprise_value,  # Base scenario
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        # ============================================================
        # GENERATE SUMMARY TEXT
        # ============================================================
        summary_text = self._generate_summary_text(valuation_summary)
        
        # ============================================================
        # EXPORT TO EXCEL
        # ============================================================
        filepath = self._export_to_excel(valuation_summary, assumptions, peers)
        
        logging.info(f"✅ Valuation complete: {filepath}")
        
        return filepath, summary_text
    
    def _generate_summary_text(self, summary: ValuationSummary) -> str:
        """
        Generate Telegram summary message
        """
        text = f"🌲 **WOOD V2 Valuation: {summary.project_name}**\n\n"
        text += f"**Enterprise Value Range: {summary.ev_min:.0f}~{summary.ev_max:.0f}억 원**\n"
        text += f"(Base Case: {summary.ev_base:.0f}억)\n\n"
        
        for scenario in summary.scenarios:
            wacc = scenario.wacc_output.wacc
            text += f"**[{scenario.scenario_name}]** EV: **{scenario.enterprise_value:.1f}억** (WACC {wacc*100:.2f}%)\n"
        
        text += "\n⚡ *WOOD V2 Engine with live market beta integration*"
        
        return text
    
    def _export_to_excel(
        self, 
        summary: ValuationSummary,
        assumptions: Assumptions,
        peers: List[dict]
    ) -> str:
        """
        Export valuation to Excel (9-sheet model)
        
        [Sheets]
        1. Summary
        2. Assumptions
        3. WACC
        4. DCF_Base
        5. DCF_Bull
        6. DCF_Bear
        7. Sensitivity
        8. Peer Group
        9. Data Source
        
        Args:
            summary: Valuation summary
            assumptions: Assumptions
            peers: Peer list
        
        Returns:
            File path
        """
        from .exporter import ExcelExporter
        
        exporter = ExcelExporter()
        filepath = exporter.export(summary, assumptions, peers, self.output_dir)
        
        return filepath


# ==============================================================================
# CONVENIENCE FUNCTION
# ==============================================================================

def run_quick_valuation(company_name: str, revenue: float) -> Tuple[str, str]:
    """
    Quick valuation with default settings
    
    Usage:
        filepath, summary = run_quick_valuation("CompanyA", 500.0)
    """
    orchestrator = WoodOrchestratorV2()
    return orchestrator.run_valuation(company_name, revenue)
