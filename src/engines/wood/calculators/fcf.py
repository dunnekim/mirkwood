"""
FCF Calculator - WOOD V2 Engine

[Methodology]
Free Cash Flow Build-up (IB Standard waterfall):

EBIT
× (1 - Tax Rate)
= NOPAT
+ D&A (non-cash)
- Capex
- Δ NWC
= Free Cash Flow

[Output]
Full projection DataFrame with all intermediate steps
"""

import pandas as pd
from typing import List
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
wood_dir = os.path.dirname(current_dir)
sys.path.insert(0, wood_dir)

from models import Assumptions, ScenarioParameters


class FCFCalculator:
    """
    Free Cash Flow projection calculator
    
    [IB Standard]
    Detailed FCF waterfall showing:
    - Revenue growth
    - EBITDA/EBIT margins
    - Tax shield
    - Working capital changes
    - Capex requirements
    """
    
    def __init__(self):
        pass
    
    def project(
        self,
        base_revenue: float,
        scenario: ScenarioParameters,
        assumptions: Assumptions
    ) -> pd.DataFrame:
        """
        Project Free Cash Flows for the scenario
        
        Args:
            base_revenue: Base year revenue (억 원)
            scenario: Scenario parameters
            assumptions: Core assumptions (tax rate, projection years)
        
        Returns:
            DataFrame with FCF waterfall
        """
        years = range(1, assumptions.projection_years + 1)
        growth = scenario.revenue_growth
        
        # Build projections
        data = []
        
        for year in years:
            # Revenue
            revenue = base_revenue * ((1 + growth) ** year)
            
            # EBITDA
            ebitda = revenue * scenario.ebitda_margin
            
            # D&A
            da = revenue * scenario.da_ratio
            
            # EBIT
            ebit = ebitda - da
            
            # Tax
            tax = ebit * assumptions.tax_rate if ebit > 0 else 0
            
            # NOPAT
            nopat = ebit - tax
            
            # Add back D&A
            nopat_plus_da = nopat + da
            
            # Capex
            capex = revenue * scenario.capex_ratio
            
            # NWC (simplified: constant % of revenue)
            nwc = revenue * scenario.nwc_ratio
            
            data.append({
                'Year': 2026 + year - 1,
                'Revenue': revenue,
                'EBITDA': ebitda,
                'D&A': da,
                'EBIT': ebit,
                'Tax': tax,
                'NOPAT': nopat,
                'Add_DA': da,
                'Less_Capex': capex,
                'NWC': nwc,
            })
        
        df = pd.DataFrame(data)
        
        # Calculate NWC changes
        df['Delta_NWC'] = df['NWC'].diff().fillna(df['NWC'].iloc[0])
        
        # FCF = NOPAT + D&A - Capex - Δ NWC
        df['FCF'] = df['NOPAT'] + df['Add_DA'] - df['Less_Capex'] - df['Delta_NWC']
        
        return df
