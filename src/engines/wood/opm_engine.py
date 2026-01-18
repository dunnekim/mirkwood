"""
OPM Engine - Option Pricing Model for Hybrid Securities

[Financial Logic]
Implements Tsiveriotis-Fernandes (TF) Model for valuing:
- RCPS (Redeemable Convertible Preferred Stock)
- CB (Convertible Bond)
- CPS (Convertible Preferred Stock)

[Core Principles]
1. Split Discounting: V = D + E
   - Debt Component (D): Discounted at Risky Rate (Rf + Credit Spread)
   - Equity Component (E): Discounted at Risk-Free Rate (Rf)

2. IPO Conditional Refixing: Path-dependent conversion price adjustment
3. Date-Adaptive Lattice: Daily step precision
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class IPOScenario:
    """IPO conditional refixing parameters"""
    check_date: datetime
    threshold_price: float
    failure_refix_ratio: float  # e.g., 0.70 (30% down)


@dataclass
class HybridSecurity:
    """Hybrid security specification"""
    security_id: str
    security_type: str  # RCPS, CB, CPS
    
    # Dates
    valuation_date: datetime
    maturity_date: datetime
    
    # Market parameters
    current_stock_price: float  # S0
    volatility: float  # σ (annualized)
    risk_free_rate: float  # Rf
    credit_spread: float  # Credit risk premium
    
    # Security terms
    conversion_price: float  # Initial CP
    face_value: float  # Per unit
    redemption_premium: float  # % (e.g., 0.05 = 5%)
    refix_floor: float  # Minimum CP allowed
    
    # Issue details
    total_amount: float
    num_shares: float
    
    # Optional features
    ipo_scenario: Optional[IPOScenario] = None


class TFEngine:
    """
    Tsiveriotis-Fernandes Model Engine
    
    [Reference]
    Tsiveriotis, K., & Fernandes, C. (1998). 
    "Valuing convertible bonds with credit risk."
    Journal of Fixed Income, 8(2), 95-102.
    """
    
    def __init__(self, max_steps: int = 300):
        """
        Args:
            max_steps: Maximum lattice steps (performance cap for large maturities)
        """
        self.max_steps = max_steps
    
    def price_hybrid_security(self, security: HybridSecurity) -> Dict:
        """
        Price hybrid security using TF model
        
        Args:
            security: HybridSecurity specification
        
        Returns:
            {
                'total_value': float,
                'debt_component': float,
                'equity_component': float,
                'per_share_value': float,
                'conversion_price_final': float,
                'lattice_steps': int,
                'model': 'TF'
            }
        """
        # Extract parameters
        S0 = security.current_stock_price
        K_init = security.conversion_price
        vol = security.volatility
        T_days = (security.maturity_date - security.valuation_date).days
        T_years = T_days / 365.0
        
        rf = security.risk_free_rate
        cs = security.credit_spread
        
        face = security.face_value
        redemption_value = face * (1 + security.redemption_premium)
        floor = security.refix_floor
        
        # ================================================================
        # 1. LATTICE SETUP (Date-Adaptive)
        # ================================================================
        
        N = min(T_days, self.max_steps)  # Daily steps, capped for performance
        dt = T_years / N
        
        print(f"   🌲 TF Engine: {security.security_id}")
        print(f"      Steps: {N}, Days: {T_days}, dt: {dt:.6f}")
        
        # ================================================================
        # 2. CRR PARAMETERS
        # ================================================================
        
        u = np.exp(vol * np.sqrt(dt))
        d = 1 / u
        
        # Risk-neutral probability
        q = (np.exp(rf * dt) - d) / (u - d)
        
        # Discount factors (TF Split)
        df_risky = np.exp(-(rf + cs) * dt)  # For Debt Component
        df_rf = np.exp(-rf * dt)             # For Equity Component
        
        print(f"      WACC: Rf {rf*100:.2f}% + CS {cs*100:.2f}% = {(rf+cs)*100:.2f}%")
        print(f"      Discount: Risky {df_risky:.6f}, RF {df_rf:.6f}")
        
        # ================================================================
        # 3. FORWARD PASS: Stock Price & Conversion Price
        # ================================================================
        
        S = np.zeros((N+1, N+1))
        CP = np.zeros((N+1, N+1))
        
        for t in range(N+1):
            # Current date of this step
            step_days = t * (T_days / N)
            step_date = security.valuation_date + timedelta(days=step_days)
            
            # Check IPO event trigger
            is_ipo_trigger = False
            if security.ipo_scenario:
                ipo_date = security.ipo_scenario.check_date
                days_diff = abs((step_date - ipo_date).days)
                
                # Within 1 step of IPO date
                if days_diff <= (T_days / N) / 2 + 0.5:
                    is_ipo_trigger = True
            
            for i in range(t+1):
                # Stock price at node (t, i)
                S[t, i] = S0 * (u ** i) * (d ** (t - i))
                
                # Conversion price at node
                node_cp = K_init
                
                # IPO conditional refixing
                if security.ipo_scenario and step_date >= security.ipo_scenario.check_date:
                    # If stock price < threshold, apply refixing
                    if S[t, i] < security.ipo_scenario.threshold_price:
                        node_cp = max(
                            floor,
                            node_cp * security.ipo_scenario.failure_refix_ratio
                        )
                
                CP[t, i] = node_cp
        
        # ================================================================
        # 4. BACKWARD INDUCTION (TF Split)
        # ================================================================
        
        D = np.zeros((N+1, N+1))  # Debt component
        E = np.zeros((N+1, N+1))  # Equity component
        
        # Terminal nodes (t = N, maturity)
        for i in range(N+1):
            conversion_value = S[N, i] * (face / CP[N, i])
            holding_value = redemption_value
            
            # Rational decision at maturity
            if conversion_value > holding_value:
                # Convert
                D[N, i] = 0
                E[N, i] = conversion_value
            else:
                # Hold/Redeem
                D[N, i] = holding_value
                E[N, i] = 0
        
        # Step backward
        for t in range(N-1, -1, -1):
            for i in range(t+1):
                # Expected continuation values
                exp_D = q * D[t+1, i+1] + (1-q) * D[t+1, i]
                exp_E = q * E[t+1, i+1] + (1-q) * E[t+1, i]
                
                # TF Split Discounting (CRITICAL)
                cont_D = exp_D * df_risky  # Discount debt at risky rate
                cont_E = exp_E * df_rf      # Discount equity at risk-free rate
                
                cont_total = cont_D + cont_E
                
                # Conversion value at this node
                conversion_value = S[t, i] * (face / CP[t, i])
                
                # American exercise check
                if conversion_value > cont_total:
                    # Early conversion
                    D[t, i] = 0
                    E[t, i] = conversion_value
                else:
                    # Continue holding
                    D[t, i] = cont_D
                    E[t, i] = cont_E
        
        # ================================================================
        # 5. RESULTS
        # ================================================================
        
        per_unit_host = D[0, 0]
        per_unit_equity = E[0, 0]
        per_unit_total = per_unit_host + per_unit_equity
        
        total_host = per_unit_host * security.num_shares
        total_equity = per_unit_equity * security.num_shares
        total_value = per_unit_total * security.num_shares
        
        print(f"      Host (Debt): {total_host:,.0f}")
        print(f"      Equity (Option): {total_equity:,.0f}")
        print(f"      Total: {total_value:,.0f}")
        
        return {
            'total_value': total_value,
            'debt_component': total_host,
            'equity_component': total_equity,
            'per_share_value': per_unit_total,
            'conversion_price_final': CP[0, 0],
            'lattice_steps': N,
            'model': 'TF',
            'split_ratio': total_equity / total_value if total_value > 0 else 0,
            'lattice_size': (N+1, N+1),
            # For audit trail
            'parameters': {
                'S0': S0,
                'K_init': K_init,
                'vol': vol,
                'rf': rf,
                'cs': cs,
                'T_years': T_years,
                'u': u,
                'd': d,
                'q': q,
                'df_risky': df_risky,
                'df_rf': df_rf
            }
        }
    
    def price_portfolio(self, securities: List[HybridSecurity]) -> Dict:
        """
        Price multiple hybrid securities
        
        Args:
            securities: List of HybridSecurity objects
        
        Returns:
            {
                'total_value': float,
                'total_debt': float,
                'total_equity': float,
                'securities': List[Dict],
                'summary': str
            }
        """
        results = []
        total_value = 0
        total_debt = 0
        total_equity = 0
        
        for sec in securities:
            result = self.price_hybrid_security(sec)
            results.append({
                'security_id': sec.security_id,
                'type': sec.security_type,
                **result
            })
            
            total_value += result['total_value']
            total_debt += result['debt_component']
            total_equity += result['equity_component']
        
        summary = f"""
Portfolio Valuation Summary:

Total Fair Value:     {total_value:,.0f} KRW
  - Debt Component:   {total_debt:,.0f} KRW ({total_debt/total_value*100:.1f}%)
  - Equity Component: {total_equity:,.0f} KRW ({total_equity/total_value*100:.1f}%)

Model: Tsiveriotis-Fernandes (TF) with IPO scenario analysis
Securities: {len(securities)}
"""
        
        return {
            'total_value': total_value,
            'total_debt': total_debt,
            'total_equity': total_equity,
            'securities': results,
            'summary': summary
        }


class OPMCalculator:
    """
    OPM Calculator - High-level interface
    
    Simplifies TF Engine usage for common scenarios
    """
    
    def __init__(self):
        self.engine = TFEngine()
    
    def quick_rcps_valuation(
        self,
        company_name: str,
        stock_price: float,
        conversion_price: float,
        face_value: float,
        num_shares: float,
        years_to_maturity: float,
        volatility: float = 0.35,
        ipo_scenario: Optional[Dict] = None
    ) -> Dict:
        """
        Quick RCPS valuation with sensible defaults
        
        Args:
            company_name: Company name
            stock_price: Current stock price (S0)
            conversion_price: Initial conversion price (CP)
            face_value: Face value per share
            num_shares: Number of shares issued
            years_to_maturity: Years to maturity
            volatility: Stock volatility (default 35%)
            ipo_scenario: Optional IPO refixing scenario
                {
                    'check_date': datetime,
                    'threshold': float,
                    'ratio': float
                }
        
        Returns:
            Valuation result dict
        """
        val_date = datetime.now()
        mat_date = val_date + timedelta(days=int(years_to_maturity * 365))
        
        # Build IPO scenario if provided
        ipo_obj = None
        if ipo_scenario:
            ipo_obj = IPOScenario(
                check_date=ipo_scenario['check_date'],
                threshold_price=ipo_scenario['threshold'],
                failure_refix_ratio=ipo_scenario['ratio']
            )
        
        security = HybridSecurity(
            security_id=company_name,
            security_type="RCPS",
            valuation_date=val_date,
            maturity_date=mat_date,
            current_stock_price=stock_price,
            volatility=volatility,
            risk_free_rate=0.035,  # Default 3.5%
            credit_spread=0.020,   # Default 2.0%
            conversion_price=conversion_price,
            face_value=face_value,
            redemption_premium=0.05,  # Default 5%
            refix_floor=conversion_price * 0.70,  # 30% floor
            total_amount=face_value * num_shares,
            num_shares=num_shares,
            ipo_scenario=ipo_obj
        )
        
        result = self.engine.price_hybrid_security(security)
        
        return result
