"""
DCF Calculator for WOOD DCF Engine

[FS Logic]
DCF (Discounted Cash Flow) = Σ(FCF_t / (1+WACC)^t) + Terminal Value / (1+WACC)^n
- Projects future Free Cash Flows
- Discounts to Present Value using WACC
- Adds Terminal Value for perpetual growth
"""

from typing import Dict, List
import pandas as pd


class DCFCalculator:
    """
    DCF 계산 전용 클래스
    
    Financial Logic:
    1. Revenue Projection (성장률 기반)
    2. Operating Profit = Revenue * Margin
    3. NOPAT = Operating Profit * (1 - Tax Rate)
    4. FCF = NOPAT (Simplified, no CapEx adjustment)
    5. PV(FCF) = FCF / (1 + WACC)^t
    6. Enterprise Value = Σ PV(FCF) + PV(Terminal Value)
    """
    
    def __init__(self, tax_rate: float = 0.22, projection_years: int = 5):
        """
        Args:
            tax_rate: 법인세율 (기본 22%)
            projection_years: 예측 기간 (기본 5년)
        """
        self.tax_rate = tax_rate
        self.projection_years = projection_years
    
    def project_financials(
        self, 
        base_revenue: float, 
        growth_rate: float, 
        margin: float,
        start_year: int = 2026
    ) -> pd.DataFrame:
        """
        재무제표 Projection
        
        Args:
            base_revenue: 기준 매출 (현재 Year 0 매출, 억 원)
            growth_rate: 연평균 성장률 (소수점)
            margin: 영업이익률 (소수점)
            start_year: 시작 연도
        
        Returns:
            DataFrame with columns: Year, Revenue, OP, Tax, NOPAT, FCF
        """
        years = [start_year + i for i in range(self.projection_years)]
        revenues = [base_revenue * ((1 + growth_rate) ** (i + 1)) for i in range(self.projection_years)]
        
        op_profits = [rev * margin for rev in revenues]
        taxes = [op * self.tax_rate for op in op_profits]
        nopats = [op - tax for op, tax in zip(op_profits, taxes)]
        
        # Simplified FCF = NOPAT (no CapEx, NWC changes)
        fcfs = nopats
        
        df = pd.DataFrame({
            "Year": years,
            "Revenue": revenues,
            "OP": op_profits,
            "Tax": taxes,
            "NOPAT": nopats,
            "FCF": fcfs
        })
        
        return df
    
    def calculate_present_value(
        self, 
        fcf_series: List[float], 
        wacc: float
    ) -> Dict:
        """
        FCF의 현재가치 계산
        
        Args:
            fcf_series: FCF 리스트 [FCF_1, FCF_2, ..., FCF_n]
            wacc: Weighted Average Cost of Capital
        
        Returns:
            {
                "discount_factors": List[float],
                "pv_fcfs": List[float],
                "sum_pv_fcf": float
            }
        """
        discount_factors = [1 / ((1 + wacc) ** (i + 1)) for i in range(len(fcf_series))]
        pv_fcfs = [fcf * df for fcf, df in zip(fcf_series, discount_factors)]
        
        return {
            "discount_factors": discount_factors,
            "pv_fcfs": pv_fcfs,
            "sum_pv_fcf": sum(pv_fcfs)
        }
    
    def calculate_enterprise_value(
        self, 
        base_revenue: float, 
        growth_rate: float, 
        margin: float, 
        wacc: float,
        terminal_value_pv: float
    ) -> Dict:
        """
        통합 Enterprise Value 계산
        
        Args:
            base_revenue: 기준 매출 (억 원)
            growth_rate: 성장률
            margin: 영업이익률
            wacc: WACC
            terminal_value_pv: 터미널 밸류 현재가치
        
        Returns:
            {
                "projection_df": pd.DataFrame,
                "pv_fcf": float,
                "pv_terminal": float,
                "enterprise_value": float
            }
        """
        # Step 1: Project financials
        proj_df = self.project_financials(base_revenue, growth_rate, margin)
        
        # Step 2: Calculate PV of FCFs
        fcf_series = proj_df['FCF'].tolist()
        pv_result = self.calculate_present_value(fcf_series, wacc)
        
        # Add PV columns to DataFrame
        proj_df['Discount_Factor'] = pv_result['discount_factors']
        proj_df['PV_FCF'] = pv_result['pv_fcfs']
        
        # Step 3: Enterprise Value
        enterprise_value = pv_result['sum_pv_fcf'] + terminal_value_pv
        
        return {
            "projection_df": proj_df,
            "pv_fcf": pv_result['sum_pv_fcf'],
            "pv_terminal": terminal_value_pv,
            "enterprise_value": enterprise_value,
            "last_fcf": fcf_series[-1],
            "last_discount_factor": pv_result['discount_factors'][-1]
        }
