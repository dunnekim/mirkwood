"""
Terminal Value Calculator - WOOD V2 Engine

[Methodology]
Dual terminal value calculation:
1. Gordon Growth Model (Primary)
2. Exit Multiple Method (Reference)

[Formula]
TV_Gordon = FCF_n × (1 + g) / (WACC - g)
TV_Exit = EBITDA_n × Exit_Multiple
"""

import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
wood_dir = os.path.dirname(current_dir)
sys.path.insert(0, wood_dir)

from models import TerminalValueOutput


class TerminalValueCalculator:
    """
    Terminal value calculator with dual methods
    
    [IB Standard]
    - Gordon Growth: Perpetual growth assumption
    - Exit Multiple: Market-based valuation
    - Sanity check: Implied EBITDA multiple
    """
    
    def __init__(self, exit_multiple: float = 8.0):
        """
        Args:
            exit_multiple: Default EV/EBITDA exit multiple
        """
        self.exit_multiple = exit_multiple
    
    def calculate(
        self,
        last_fcf: float,
        last_ebitda: float,
        wacc: float,
        terminal_growth_rate: float
    ) -> TerminalValueOutput:
        """
        Calculate terminal value using dual methods
        
        Args:
            last_fcf: Final year FCF
            last_ebitda: Final year EBITDA
            wacc: Discount rate
            terminal_growth_rate: Perpetual growth rate (g)
        
        Returns:
            TerminalValueOutput with both methods
        """
        # Method 1: Gordon Growth
        if wacc > terminal_growth_rate:
            tv_gordon = (last_fcf * (1 + terminal_growth_rate)) / (wacc - terminal_growth_rate)
        else:
            # Invalid assumption: use FCF multiple fallback
            tv_gordon = last_fcf * 20  # 20x FCF
        
        # Method 2: Exit Multiple
        tv_exit = last_ebitda * self.exit_multiple
        
        # Implied EBITDA multiple from Gordon
        if last_ebitda > 0:
            implied_multiple = tv_gordon / last_ebitda
        else:
            implied_multiple = 0.0
        
        return TerminalValueOutput(
            tv_gordon=tv_gordon,
            tv_exit_multiple=tv_exit,
            implied_ebitda_multiple=implied_multiple,
            terminal_growth_rate=terminal_growth_rate,
            exit_multiple_assumption=self.exit_multiple
        )
