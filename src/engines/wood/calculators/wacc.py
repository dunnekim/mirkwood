"""
WACC Calculator - WOOD V2 Engine

[Methodology]
Professional WACC calculation with:
1. Live market beta (yfinance + regression)
2. Peer group unlevering/re-levering
3. Korean SRP (Size Risk Premium) - 5-tier KICPA standard
4. Full build-up transparency

[Formula]
Cost of Equity (Ke) = Rf + (β × MRP) + SRP
WACC = Ke × (E/V) + Kd × (1-Tax) × (D/V)
"""

import logging
import numpy as np
from typing import List, Dict, Optional
from dataclasses import asdict

# Import models
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
wood_dir = os.path.dirname(current_dir)
sys.path.insert(0, wood_dir)

from models import Assumptions, PeerCompany, WACCOutput

# Import market scanner
from src.tools.market_scanner import MarketScanner


class WACCCalculator:
    """
    Investment Banking-grade WACC Calculator
    
    [Real IB Standard]
    - Live beta from market data (not textbook values)
    - Proper unlevering/re-levering (Hamada formula)
    - Korean SRP integration (KICPA standard)
    - Median peer beta (robust to outliers)
    
    [Process Flow]
    1. Fetch live betas for peer group (fallback to static)
    2. Unlever each peer beta
    3. Calculate median unlevered beta (robust proxy)
    4. Re-lever to target capital structure
    5. Apply CAPM + SRP
    6. Calculate WACC with capital structure weights
    """
    
    # ================================================================
    # SRP TABLE (Korean KICPA Standard)
    # ================================================================
    SRP_TABLE = [
        {
            "quintile": 1,
            "label": "1분위 (대형)",
            "srp": -0.0063,
            "mc_min": 1660780,  # 시가총액 1.66조 이상
            "na_min": 81600     # 순자산 816억 이상
        },
        {
            "quintile": 2,
            "label": "2분위 (중대형)",
            "srp": 0.0008,
            "mc_min": 609450,
            "na_min": 60200
        },
        {
            "quintile": 3,
            "label": "3분위 (중형)",
            "srp": 0.0127,
            "mc_min": 299250,
            "na_min": 39200
        },
        {
            "quintile": 4,
            "label": "4분위 (중소형)",
            "srp": 0.0247,
            "mc_min": 162910,
            "na_min": 32600
        },
        {
            "quintile": 5,
            "label": "5분위 (소형)",
            "srp": 0.0473,
            "mc_min": 0,
            "na_min": 0
        }
    ]
    
    def __init__(self, use_live_beta: bool = True):
        """
        Args:
            use_live_beta: Enable live market beta calculation
        """
        self.use_live_beta = use_live_beta
        
        if use_live_beta:
            try:
                self.scanner = MarketScanner()
                logging.info("✅ WACC Calculator: Live beta enabled")
            except Exception as e:
                logging.warning(f"⚠️ MarketScanner initialization failed: {e}")
                self.use_live_beta = False
                self.scanner = None
        else:
            self.scanner = None
    
    def _get_srp(
        self, 
        is_listed: bool, 
        size_mil_krw: float
    ) -> tuple:
        """
        Get Size Risk Premium from KICPA table
        
        Args:
            is_listed: Listed company (use market cap) vs unlisted (use net assets)
            size_mil_krw: Size metric in million KRW
        
        Returns:
            (srp, description, quintile)
        """
        key = "mc_min" if is_listed else "na_min"
        
        for row in self.SRP_TABLE:
            if size_mil_krw >= row[key]:
                return row['srp'], row['label'], row['quintile']
        
        # Default to quintile 5
        return 0.0473, "5분위 (소형)", 5
    
    def _unlever_beta(
        self, 
        levered_beta: float, 
        debt_equity_ratio: float, 
        tax_rate: float
    ) -> float:
        """
        Unlever beta using Hamada formula
        
        β_u = β_L / [1 + (1-Tax) × (D/E)]
        
        Args:
            levered_beta: Observed (levered) beta
            debt_equity_ratio: D/E ratio
            tax_rate: Tax rate
        
        Returns:
            Unlevered beta
        """
        return levered_beta / (1 + (1 - tax_rate) * debt_equity_ratio)
    
    def _relever_beta(
        self, 
        unlevered_beta: float, 
        target_debt_equity_ratio: float, 
        tax_rate: float
    ) -> float:
        """
        Re-lever beta to target capital structure
        
        β_L = β_u × [1 + (1-Tax) × (D/E)]
        
        Args:
            unlevered_beta: Unlevered beta
            target_debt_equity_ratio: Target D/E ratio
            tax_rate: Tax rate
        
        Returns:
            Re-levered beta
        """
        return unlevered_beta * (1 + (1 - tax_rate) * target_debt_equity_ratio)
    
    def _fetch_peer_betas(
        self, 
        peers: List[Dict]
    ) -> List[Dict]:
        """
        Fetch live betas for peer group
        
        Args:
            peers: List of peer dicts with keys: name, ticker, static_beta, debt_equity_ratio, tax_rate
        
        Returns:
            List of peer dicts with added 'live_beta' and 'beta_source' keys
        """
        results = []
        
        for peer in peers:
            peer_result = peer.copy()
            
            ticker = peer.get('ticker')
            static_beta = peer.get('static_beta', 1.0)
            
            if self.use_live_beta and ticker and self.scanner:
                try:
                    live_beta, source = self.scanner.get_beta(ticker, fallback_beta=static_beta)
                    peer_result['live_beta'] = live_beta
                    peer_result['beta_source'] = source
                except Exception as e:
                    logging.warning(f"Failed to fetch beta for {ticker}: {e}")
                    peer_result['live_beta'] = static_beta
                    peer_result['beta_source'] = "Fallback"
            else:
                peer_result['live_beta'] = static_beta
                peer_result['beta_source'] = "Static"
            
            results.append(peer_result)
        
        return results
    
    def calculate(
        self, 
        assumptions: Assumptions, 
        peers: List[Dict],
        scenario_wacc_premium: float = 0.0
    ) -> WACCOutput:
        """
        Calculate WACC with full IB-grade methodology
        
        [Process]
        1. Fetch live betas for peers (or use static)
        2. Unlever each peer beta
        3. Select MEDIAN unlevered beta (robust to outliers)
        4. Re-lever to target capital structure
        5. Calculate Cost of Equity: Rf + β×MRP + SRP
        6. Calculate WACC
        
        Args:
            assumptions: Core assumptions (Assumptions dataclass)
            peers: List of peer company dicts
            scenario_wacc_premium: Additional WACC adjustment (e.g., +0.01 for Bear)
        
        Returns:
            WACCOutput with full build-up details
        """
        logging.info(f"🔧 WACC Calculation: {len(peers)} peers, Live Beta = {self.use_live_beta}")
        
        # ============================================================
        # STEP 1: FETCH PEER BETAS
        # ============================================================
        peers_with_betas = self._fetch_peer_betas(peers)
        
        # Count live vs static
        live_count = sum(1 for p in peers_with_betas if p['beta_source'] == "Live")
        logging.info(f"   Beta Sources: {live_count} Live, {len(peers) - live_count} Static/Fallback")
        
        # ============================================================
        # STEP 2: UNLEVER PEER BETAS
        # ============================================================
        unlevered_betas = []
        
        for peer in peers_with_betas:
            beta = peer['live_beta']
            de_ratio = peer.get('debt_equity_ratio', 0.3)
            tax = peer.get('tax_rate', assumptions.tax_rate)
            
            beta_u = self._unlever_beta(beta, de_ratio, tax)
            unlevered_betas.append(beta_u)
            
            logging.debug(
                f"      {peer['name']}: β_L={beta:.3f} → β_u={beta_u:.3f} "
                f"(D/E={de_ratio:.2f}, Source={peer['beta_source']})"
            )
        
        # ============================================================
        # STEP 3: SELECT PROXY BETA (MEDIAN)
        # ============================================================
        if unlevered_betas:
            proxy_beta_u = float(np.median(unlevered_betas))
        else:
            proxy_beta_u = 1.0  # Fallback
        
        logging.info(f"   Proxy Unlevered Beta (Median): {proxy_beta_u:.3f}")
        
        # ============================================================
        # STEP 4: RE-LEVER TO TARGET STRUCTURE
        # ============================================================
        target_beta_l = self._relever_beta(
            proxy_beta_u, 
            assumptions.target_debt_ratio, 
            assumptions.tax_rate
        )
        
        logging.info(
            f"   Target Levered Beta: {target_beta_l:.3f} "
            f"(Target D/E={assumptions.target_debt_ratio:.2f})"
        )
        
        # ============================================================
        # STEP 5: SIZE RISK PREMIUM (SRP)
        # ============================================================
        srp, srp_desc, srp_quintile = self._get_srp(
            assumptions.is_listed, 
            assumptions.size_metric_mil_krw
        )
        
        logging.info(f"   SRP: {srp*100:.2f}% ({srp_desc})")
        
        # ============================================================
        # STEP 6: COST OF EQUITY (CAPM + SRP)
        # ============================================================
        cost_of_equity = (
            assumptions.risk_free_rate 
            + (target_beta_l * assumptions.market_risk_premium)
            + srp
        )
        
        logging.info(
            f"   Cost of Equity: {cost_of_equity*100:.2f}% "
            f"(Rf={assumptions.risk_free_rate*100:.1f}% + "
            f"β×MRP={target_beta_l*assumptions.market_risk_premium*100:.2f}% + "
            f"SRP={srp*100:.2f}%)"
        )
        
        # ============================================================
        # STEP 7: COST OF DEBT (AFTER-TAX)
        # ============================================================
        cost_of_debt_after_tax = assumptions.cost_of_debt_pretax * (1 - assumptions.tax_rate)
        
        # ============================================================
        # STEP 8: CAPITAL STRUCTURE WEIGHTS
        # ============================================================
        # D/E ratio to D/(D+E) and E/(D+E)
        total = 1 + assumptions.target_debt_ratio
        debt_weight = assumptions.target_debt_ratio / total
        equity_weight = 1 / total
        
        # ============================================================
        # STEP 9: WACC
        # ============================================================
        wacc_base = (
            cost_of_equity * equity_weight 
            + cost_of_debt_after_tax * debt_weight
        )
        
        # Apply scenario premium
        wacc_final = wacc_base + scenario_wacc_premium
        
        logging.info(
            f"   WACC (Base): {wacc_base*100:.2f}% "
            f"(Ke={cost_of_equity*100:.2f}% × {equity_weight*100:.1f}% + "
            f"Kd(AT)={cost_of_debt_after_tax*100:.2f}% × {debt_weight*100:.1f}%)"
        )
        
        if scenario_wacc_premium != 0:
            logging.info(
                f"   WACC (Adjusted): {wacc_final*100:.2f}% "
                f"(Premium: {scenario_wacc_premium*100:+.2f}%)"
            )
        
        # ============================================================
        # STEP 10: BUILD OUTPUT
        # ============================================================
        beta_source_summary = "Live" if live_count > 0 else "Static"
        
        output = WACCOutput(
            wacc=wacc_final,
            cost_of_equity=cost_of_equity,
            cost_of_debt_after_tax=cost_of_debt_after_tax,
            risk_free_rate=assumptions.risk_free_rate,
            beta_levered=target_beta_l,
            beta_unlevered=proxy_beta_u,
            market_risk_premium=assumptions.market_risk_premium,
            size_risk_premium=srp,
            srp_quintile=srp_quintile,
            srp_description=srp_desc,
            debt_weight=debt_weight,
            equity_weight=equity_weight,
            beta_source=beta_source_summary,
            peer_count=len(peers)
        )
        
        return output


# ==============================================================================
# TESTING
# ==============================================================================

def test_wacc_calculator():
    """
    Test WACC Calculator with sample Korean peers
    """
    print("=" * 70)
    print("🧪 WACC Calculator Test - Korean Market")
    print("=" * 70)
    
    # Sample assumptions
    assumptions = Assumptions(
        risk_free_rate=0.035,
        market_risk_premium=0.08,
        tax_rate=0.22,
        terminal_growth_rate=0.02,
        target_debt_ratio=0.30,
        cost_of_debt_pretax=0.045,
        is_listed=False,
        size_metric_mil_krw=15000  # 150억 KRW
    )
    
    # Sample peer group (Korean semiconductor companies)
    peers = [
        {
            "name": "Samsung Electronics",
            "ticker": "005930",
            "static_beta": 1.1,
            "debt_equity_ratio": 0.15,
            "tax_rate": 0.22
        },
        {
            "name": "SK Hynix",
            "ticker": "000660",
            "static_beta": 1.3,
            "debt_equity_ratio": 0.25,
            "tax_rate": 0.22
        },
        {
            "name": "LG Display",
            "ticker": "034220",
            "static_beta": 1.2,
            "debt_equity_ratio": 0.40,
            "tax_rate": 0.22
        }
    ]
    
    # Test with live beta
    calculator = WACCCalculator(use_live_beta=True)
    result = calculator.calculate(assumptions, peers)
    
    print("\n📊 WACC Calculation Results:")
    print(f"   WACC: {result.wacc*100:.2f}%")
    print(f"   Cost of Equity: {result.cost_of_equity*100:.2f}%")
    print(f"   Cost of Debt (AT): {result.cost_of_debt_after_tax*100:.2f}%")
    print(f"   Levered Beta: {result.beta_levered:.3f}")
    print(f"   Unlevered Beta: {result.beta_unlevered:.3f}")
    print(f"   SRP: {result.size_risk_premium*100:.2f}% ({result.srp_description})")
    print(f"   Beta Source: {result.beta_source}")
    print(f"   Peer Count: {result.peer_count}")
    
    print("\n" + "=" * 70)
    print("✅ Test completed")
    print("=" * 70)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_wacc_calculator()
