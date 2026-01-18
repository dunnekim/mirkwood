"""
WACC Calculator for WOOD DCF Engine

[FS Logic]
WACC (Weighted Average Cost of Capital) = Cost of Equity * E/(E+D) + Cost of Debt * D/(E+D) * (1 - Tax)
- For simplicity, we use unleveraged beta approach
- CAPM: Cost of Equity = Risk-Free Rate + Beta * Market Risk Premium
"""

from typing import Dict, List
import numpy as np


class WACCCalculator:
    """
    WACC 계산 전용 클래스
    
    Financial Logic:
    - CAPM을 사용하여 자기자본비용 계산
    - Peer Group의 평균 Beta를 사용
    - 시나리오별 Premium/Discount 적용 가능
    """
    
    def __init__(self, risk_free_rate: float = 0.035, market_premium: float = 0.06):
        """
        Args:
            risk_free_rate: 무위험 수익률 (국채 수익률, 기본값 3.5%)
            market_premium: 시장 위험 프리미엄 (기본값 6%)
        """
        self.risk_free_rate = risk_free_rate
        self.market_premium = market_premium
    
    def calculate_base_wacc(self, peer_group: List[Dict]) -> float:
        """
        Peer Group 기반 Base WACC 계산
        
        Args:
            peer_group: [{"name": str, "beta": float, "debt_ratio": float}, ...]
        
        Returns:
            Base WACC (소수점)
        """
        if not peer_group:
            # Default conservative beta
            avg_beta = 1.0
        else:
            avg_beta = np.mean([peer.get('beta', 1.0) for peer in peer_group])
        
        # CAPM: Cost of Equity
        cost_of_equity = self.risk_free_rate + (avg_beta * self.market_premium)
        
        # Simplified: Assume all equity financing for unleveraged DCF
        base_wacc = cost_of_equity
        
        return base_wacc
    
    def apply_scenario_adjustment(self, base_wacc: float, premium: float) -> float:
        """
        시나리오별 WACC 조정
        
        Args:
            base_wacc: 기본 WACC
            premium: 시나리오 프리미엄 (Bull: -0.01, Bear: +0.02)
        
        Returns:
            조정된 WACC
        """
        adjusted_wacc = base_wacc + premium
        
        # Sanity check: WACC는 2%~20% 범위 내
        adjusted_wacc = max(0.02, min(0.20, adjusted_wacc))
        
        return adjusted_wacc
    
    def calculate_scenario_wacc(self, peer_group: List[Dict], scenario_premium: float) -> Dict:
        """
        시나리오별 WACC 계산 (한번에)
        
        Returns:
            {"base_wacc": float, "adjusted_wacc": float, "cost_of_equity": float}
        """
        base_wacc = self.calculate_base_wacc(peer_group)
        adjusted_wacc = self.apply_scenario_adjustment(base_wacc, scenario_premium)
        
        return {
            "base_wacc": base_wacc,
            "adjusted_wacc": adjusted_wacc,
            "cost_of_equity": base_wacc  # Simplified unleveraged
        }
