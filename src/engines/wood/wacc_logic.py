"""
Korean WACC Calculator (KICPA Standard)

[Reference]
- KICPA (한국공인회계사회) 가치평가 가이드라인
- DataGuide 규모위험 프리미엄 (Size Risk Premium) 테이블
- 국고채 10년물 수익률 (Risk-Free Rate)

[Key Features]
1. Size Risk Premium (SRP) - 5분위수 기준
2. Korean Market Risk Premium (MRP) - KICPA 권고 8.0%
3. Listed vs Unlisted distinction
   - Listed: Market Cap 기준
   - Unlisted: Net Assets 기준
4. Real Beta Calculation - Market scanner integration
"""

from typing import Dict, List, Tuple, Optional
import numpy as np

# Optional import (graceful degradation if not available)
try:
    from src.tools.market_scanner import MarketScanner
    MARKET_SCANNER_AVAILABLE = True
except ImportError:
    MARKET_SCANNER_AVAILABLE = False
    print("⚠️ MarketScanner not available. Using provided betas only.")


class KoreanWACCCalculator:
    """
    한국 M&A 실무 표준 WACC 계산기
    
    [Financial Logic]
    Cost of Equity (Ke) = Rf + (β × MRP) + SRP
    
    Where:
    - Rf: Risk-Free Rate (국고채 10년)
    - β: Levered Beta (재레버리징)
    - MRP: Market Risk Premium (KICPA 권고 8.0%)
    - SRP: Size Risk Premium (규모위험 프리미엄)
    
    WACC = Ke × (E/V) + Kd × (1-Tax) × (D/V)
    """
    
    def __init__(self, tax_rate: float = 0.22, use_live_beta: bool = False):
        """
        Args:
            tax_rate: 법인세율 (한국 기본 22%)
            use_live_beta: True면 MarketScanner로 실시간 베타 계산
        """
        self.tax_rate = tax_rate
        self.use_live_beta = use_live_beta and MARKET_SCANNER_AVAILABLE
        
        if self.use_live_beta:
            self.scanner = MarketScanner()
            print("   📊 Korean WACC: Live beta calculation enabled")
        
        # ================================================================
        # SRP TABLE (규모위험 프리미엄)
        # ================================================================
        # [Reference] DataGuide / KICPA 가이드라인
        # 단위: 백만 원 (Million KRW)
        
        self.SRP_TABLE = [
            # 1분위 (대형주) - 음수 프리미엄 (규모 효과로 할인)
            {
                "quintile": 1,
                "label": "1분위 (대형)",
                "srp": -0.0063,
                "mc_min": 1660780,  # 시가총액 1.66조 이상
                "na_min": 81600     # 순자산 816억 이상
            },
            # 2분위
            {
                "quintile": 2,
                "label": "2분위 (중대형)",
                "srp": 0.0008,
                "mc_min": 609450,   # 시가총액 6,095억 이상
                "na_min": 60200     # 순자산 602억 이상
            },
            # 3분위 (중형)
            {
                "quintile": 3,
                "label": "3분위 (중형)",
                "srp": 0.0127,
                "mc_min": 299250,   # 시가총액 2,993억 이상
                "na_min": 39200     # 순자산 392억 이상
            },
            # 4분위 (중소형)
            {
                "quintile": 4,
                "label": "4분위 (중소형)",
                "srp": 0.0247,
                "mc_min": 162910,   # 시가총액 1,629억 이상
                "na_min": 32600     # 순자산 326억 이상
            },
            # 5분위 (소형주) - 최고 프리미엄
            {
                "quintile": 5,
                "label": "5분위 (소형)",
                "srp": 0.0473,
                "mc_min": 0,        # 그 이하 모두
                "na_min": 0
            }
        ]
    
    def _get_korean_srp(
        self, 
        is_listed: bool, 
        value_million_krw: float
    ) -> Tuple[float, str, int]:
        """
        규모위험 프리미엄 산출
        
        Args:
            is_listed: 상장 여부
            value_million_krw: 시가총액 or 순자산 (백만 원)
        
        Returns:
            (srp: float, description: str, quintile: int)
        """
        key = "mc_min" if is_listed else "na_min"
        
        # 큰 규모(1분위)부터 순차 비교
        for row in self.SRP_TABLE:
            if value_million_krw >= row[key]:
                return row['srp'], row['label'], row['quintile']
        
        # Fallback (shouldn't reach here due to quintile 5 with min=0)
        return 0.0473, "5분위 (소형)", 5
    
    def _calculate_unlevered_beta(
        self, 
        levered_beta: float, 
        debt_equity_ratio: float, 
        tax_rate: float
    ) -> float:
        """
        Hamada Equation: Unlever Beta
        
        β_u = β_L / [1 + (1-Tax) × (D/E)]
        """
        return levered_beta / (1 + (1 - tax_rate) * debt_equity_ratio)
    
    def _calculate_relevered_beta(
        self, 
        unlevered_beta: float, 
        target_debt_equity_ratio: float, 
        tax_rate: float
    ) -> float:
        """
        Hamada Equation: Re-lever Beta
        
        β_L = β_u × [1 + (1-Tax) × (D/E)]
        """
        return unlevered_beta * (1 + (1 - tax_rate) * target_debt_equity_ratio)
    
    def calculate(
        self,
        peers: List[Dict],
        target_debt_ratio: float,
        cost_of_debt_pretax: float,
        is_listed: bool,
        size_metric_mil_krw: float,
        rf: float = 0.035,
        mrp: float = 0.08,
        peer_tickers: Optional[List[str]] = None
    ) -> Dict:
        """
        한국 표준 WACC 계산
        
        Args:
            peers: Peer group data
                [{"beta": float, "tax_rate": float, "debt_equity_ratio": float}, ...]
            target_debt_ratio: Target D/E ratio
            cost_of_debt_pretax: Pre-tax cost of debt (%)
            is_listed: 상장 여부
            size_metric_mil_krw: 시가총액(상장) or 순자산(비상장) in Million KRW
            rf: Risk-Free Rate (국고채 10년, default 3.5%)
            mrp: Market Risk Premium (KICPA 권고 8.0%)
        
        Returns:
            {
                "WACC": float,
                "Ke": float,
                "Kd_post_tax": float,
                "Beta_Levered": float,
                "Beta_Unlevered": float,
                "SRP": float,
                "SRP_Quintile": int,
                "SRP_Description": str,
                "Rf": float,
                "MRP": float,
                "Weight_Equity": float,
                "Weight_Debt": float
            }
        """
        # ================================================================
        # 1. BETA CALCULATION (Unlevering → Average → Re-levering)
        # ================================================================
        
        # Option A: Use live beta calculation (Real IB method)
        if self.use_live_beta and peer_tickers:
            print("      🔬 Using live beta calculation (Regression)...")
            unlevered_betas = []
            
            for i, peer in enumerate(peers):
                # Get live beta if ticker provided
                if i < len(peer_tickers) and peer_tickers[i]:
                    beta_result = self.scanner.calculate_beta(peer_tickers[i])
                    
                    if beta_result['success'] and beta_result['confidence'] != 'Low':
                        levered_beta = beta_result['adjusted_beta']
                        print(f"         Peer {i+1}: Adjusted Beta {levered_beta:.3f} (R²: {beta_result['r_squared']:.2f})")
                    else:
                        levered_beta = peer.get('beta', 1.0)
                        print(f"         Peer {i+1}: Fallback to provided beta {levered_beta:.3f}")
                else:
                    levered_beta = peer.get('beta', 1.0)
                
                # Unlever
                beta_u = self._calculate_unlevered_beta(
                    levered_beta=levered_beta,
                    debt_equity_ratio=peer['debt_equity_ratio'],
                    tax_rate=peer['tax_rate']
                )
                unlevered_betas.append(beta_u)
        
        # Option B: Use provided betas (Traditional method)
        else:
            unlevered_betas = []
            for peer in peers:
                beta_u = self._calculate_unlevered_beta(
                    levered_beta=peer['beta'],
                    debt_equity_ratio=peer['debt_equity_ratio'],
                    tax_rate=peer['tax_rate']
                )
                unlevered_betas.append(beta_u)
        
        # Use median instead of mean (more robust to outliers)
        avg_beta_u = np.median(unlevered_betas) if unlevered_betas else 1.0
        
        # Re-lever to target structure
        target_beta_l = self._calculate_relevered_beta(
            unlevered_beta=avg_beta_u,
            target_debt_equity_ratio=target_debt_ratio,
            tax_rate=self.tax_rate
        )
        
        # ================================================================
        # 2. SIZE RISK PREMIUM (SRP) - Korean Specific
        # ================================================================
        
        srp_value, srp_desc, srp_quintile = self._get_korean_srp(
            is_listed=is_listed,
            value_million_krw=size_metric_mil_krw
        )
        
        # ================================================================
        # 3. COST OF EQUITY (Ke)
        # ================================================================
        
        # CAPM Base
        ke_base = rf + (target_beta_l * mrp)
        
        # Add SRP (Korean adjustment)
        ke_final = ke_base + srp_value
        
        # ================================================================
        # 4. COST OF DEBT (Kd)
        # ================================================================
        
        kd_post_tax = cost_of_debt_pretax * (1 - self.tax_rate)
        
        # ================================================================
        # 5. WACC
        # ================================================================
        
        # Weights
        weight_equity = 1 / (1 + target_debt_ratio)
        weight_debt = target_debt_ratio / (1 + target_debt_ratio)
        
        # WACC = Ke × (E/V) + Kd × (D/V)
        wacc = (ke_final * weight_equity) + (kd_post_tax * weight_debt)
        
        return {
            "WACC": wacc,
            "Ke": ke_final,
            "Ke_Base": ke_base,
            "Kd_post_tax": kd_post_tax,
            "Beta_Levered": target_beta_l,
            "Beta_Unlevered": avg_beta_u,
            "SRP": srp_value,
            "SRP_Quintile": srp_quintile,
            "SRP_Description": srp_desc,
            "Rf": rf,
            "MRP": mrp,
            "Weight_Equity": weight_equity,
            "Weight_Debt": weight_debt,
            "Target_D/E": target_debt_ratio
        }
    
    def explain_calculation(self, wacc_result: Dict) -> str:
        """
        WACC 계산 과정을 사람이 읽을 수 있는 텍스트로 설명
        
        Args:
            wacc_result: calculate() 결과
        
        Returns:
            Markdown formatted explanation
        """
        r = wacc_result
        
        explanation = f"""
## 📊 WACC 계산 과정 (KICPA 표준)

### 1️⃣ Cost of Equity (자기자본비용)

**CAPM Base:**
```
Ke_base = Rf + (β × MRP)
        = {r['Rf']*100:.2f}% + ({r['Beta_Levered']:.3f} × {r['MRP']*100:.1f}%)
        = {r['Ke_Base']*100:.2f}%
```

**Size Risk Premium (규모위험 프리미엄):**
```
SRP = {r['SRP']*100:.2f}% ({r['SRP_Description']})
```

**Final Cost of Equity:**
```
Ke = Ke_base + SRP
   = {r['Ke_Base']*100:.2f}% + {r['SRP']*100:.2f}%
   = {r['Ke']*100:.2f}%
```

### 2️⃣ Cost of Debt (타인자본비용)

```
Kd (After-Tax) = {r['Kd_post_tax']*100:.2f}%
```

### 3️⃣ WACC (가중평균자본비용)

**Capital Structure:**
- Equity Weight: {r['Weight_Equity']*100:.1f}%
- Debt Weight: {r['Weight_Debt']*100:.1f}%
- Target D/E: {r['Target_D/E']:.2f}

**Calculation:**
```
WACC = Ke × (E/V) + Kd × (D/V)
     = {r['Ke']*100:.2f}% × {r['Weight_Equity']*100:.1f}% + {r['Kd_post_tax']*100:.2f}% × {r['Weight_Debt']*100:.1f}%
     = {r['WACC']*100:.2f}%
```

### 📚 References
- **Rf**: 국고채 10년물 기준
- **MRP**: KICPA 권고 8.0%
- **SRP**: DataGuide 5분위수 테이블
- **Beta**: Hamada equation (unlevering/re-levering)
"""
        
        return explanation
