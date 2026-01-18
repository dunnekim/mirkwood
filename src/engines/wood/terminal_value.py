"""
Terminal Value Calculator for WOOD DCF Engine

[FS Logic]
Terminal Value = Last Year FCF * (1 + g) / (WACC - g)
- Perpetual Growth Method (Gordon Growth Model)
- Conservative terminal growth rate (typically 1~3%)
"""

from typing import Dict


class TerminalValueCalculator:
    """
    터미널 밸류 계산 전용 클래스
    
    Financial Logic:
    - Perpetual Growth Method 사용
    - Terminal Growth Rate는 보수적으로 설정 (GDP 성장률 수준)
    - WACC > Terminal Growth Rate 조건 필수
    """
    
    def __init__(self, default_terminal_growth: float = 0.01):
        """
        Args:
            default_terminal_growth: 기본 영구성장률 (1%)
        """
        self.default_terminal_growth = default_terminal_growth
    
    def calculate(
        self, 
        last_fcf: float, 
        wacc: float, 
        terminal_growth: float = None
    ) -> Dict:
        """
        터미널 밸류 계산
        
        Args:
            last_fcf: 마지막 연도의 FCF
            wacc: Weighted Average Cost of Capital
            terminal_growth: 영구성장률 (None이면 기본값 사용)
        
        Returns:
            {
                "terminal_value": float,  # 터미널 밸류 (명목가치)
                "terminal_growth": float,  # 사용된 영구성장률
                "sanity_check": str  # 경고 메시지
            }
        """
        if terminal_growth is None:
            terminal_growth = self.default_terminal_growth
        
        # Sanity Check: WACC > Terminal Growth
        if wacc <= terminal_growth:
            warning = f"⚠️ WACC ({wacc:.1%}) must be > Terminal Growth ({terminal_growth:.1%}). Adjusting..."
            terminal_growth = wacc * 0.5  # Force to half of WACC
        else:
            warning = "OK"
        
        # Gordon Growth Model
        terminal_value = (last_fcf * (1 + terminal_growth)) / (wacc - terminal_growth)
        
        # Negative FCF protection
        if last_fcf < 0:
            warning += " | Negative FCF detected. TV set to 0."
            terminal_value = 0
        
        return {
            "terminal_value": terminal_value,
            "terminal_growth": terminal_growth,
            "sanity_check": warning
        }
    
    def calculate_pv_terminal(
        self, 
        terminal_value: float, 
        discount_factor: float
    ) -> float:
        """
        터미널 밸류의 현재가치 계산
        
        Args:
            terminal_value: 터미널 밸류 (명목가치)
            discount_factor: 마지막 연도의 할인율 (1 / (1+WACC)^n)
        
        Returns:
            터미널 밸류 현재가치
        """
        return terminal_value * discount_factor
