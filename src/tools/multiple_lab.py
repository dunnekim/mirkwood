from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field

# ==========================================
# 1. Data Structures (Standardization)
# ==========================================

class SectorType(str, Enum):
    IT = "IT"
    GAME = "Game"
    BIO = "Bio"
    MANU = "Manufacturing"
    CONSUMER = "Consumer"
    LOGISTICS = "Logistics"
    CONSTRUCTION = "Construction"
    BANK = "Bank"
    CAPITAL = "Capital"
    INSURANCE = "Insurance"
    GENERAL = "General"

class FinancialInput(BaseModel):
    """재무 데이터 입력 스키마 (단위: 십억 원)"""
    revenue_bn: float = Field(..., description="연간 매출액")
    op_bn: float = Field(0, description="영업이익")
    ebitda_bn: float = Field(0, description="EBITDA")
    net_debt_bn: float = Field(0, description="순차입금")
    equity_bn: float = Field(0, description="자본총계")

class ValuationOutput(BaseModel):
    """최종 산출물 스키마"""
    target_value_bn: float
    methodology: str
    logic_summary: str
    calculation_detail: str
    warning_flags: List[str] = Field(default_factory=list)

# ==========================================
# 2. Rulebook (Configuration)
# ==========================================

class ValuationConfig:
    # [EV/EBITDA Band, PSR Band]
    NON_FS_MULTIPLES = {
        SectorType.IT: {"ev_ebitda": [8.0, 10.0, 12.0], "psr": [2.0, 3.0, 4.0]}, 
        SectorType.GAME: {"ev_ebitda": [10.0, 13.0, 16.0], "psr": [2.5, 3.5, 4.5]},
        SectorType.BIO: {"ev_ebitda": [15.0, 20.0, 25.0], "psr": [5.0, 7.0, 10.0]},
        SectorType.MANU: {"ev_ebitda": [4.0, 5.5, 7.0], "psr": [0.4, 0.6, 0.8]},
        SectorType.CONSUMER: {"ev_ebitda": [7.0, 9.0, 11.0], "psr": [0.8, 1.2, 1.5]},
        SectorType.GENERAL: {"ev_ebitda": [6.0, 8.0, 10.0], "psr": [0.6, 0.9, 1.2]}
    }
    
    # [PBR Band]
    FS_MULTIPLES = {
        SectorType.BANK: {"pbr": [0.3, 0.5, 0.7]},
        SectorType.CAPITAL: {"pbr": [0.6, 0.9, 1.2]},
        SectorType.INSURANCE: {"pbr": [0.4, 0.7, 1.0]},
        SectorType.GENERAL: {"pbr": [0.5, 0.8, 1.0]}
    }

    SECTOR_KR_MAP = {
        SectorType.IT: "IT/소프트웨어", SectorType.GAME: "게임/컨텐츠",
        SectorType.BIO: "바이오/헬스케어", SectorType.MANU: "제조업",
        SectorType.CONSUMER: "소비재/유통", SectorType.LOGISTICS: "물류/운송",
        SectorType.CONSTRUCTION: "건설", SectorType.BANK: "은행/지주",
        SectorType.CAPITAL: "캐피탈/증권", SectorType.INSURANCE: "보험",
        SectorType.GENERAL: "일반 제조업"
    }

# ==========================================
# 3. Main Logic Engine
# ==========================================

class MultipleLab:
    def __init__(self):
        self.config = ValuationConfig()

    def _map_sector(self, sector_str: str) -> SectorType:
        s = str(sector_str).upper()
        # Generic finance label normalization
        if "FINANCE" in s or "금융" in s:
            return SectorType.BANK
        if "BANK" in s or "은행" in s: return SectorType.BANK
        if "저축은행" in s: return SectorType.BANK
        if "CAPITAL" in s or "CARD" in s or "증권" in s or "투자" in s: return SectorType.CAPITAL
        if "INSUR" in s or "LIFE" in s or "보험" in s: return SectorType.INSURANCE
        if "GAME" in s or "게임" in s: return SectorType.GAME
        if "BIO" in s or "PHARM" in s or "바이오" in s: return SectorType.BIO
        if "IT" in s or "TECH" in s or "SW" in s or "플랫폼" in s: return SectorType.IT
        if "MANU" in s or "CHEM" in s or "AUTO" in s or "제조" in s: return SectorType.MANU
        if "LOGIS" in s or "물류" in s: return SectorType.LOGISTICS
        return SectorType.GENERAL

    def calculate(self, sector_str: str, financials: FinancialInput) -> ValuationOutput:
        sector = self._map_sector(sector_str)
        sector_kr = self.config.SECTOR_KR_MAP.get(sector, "기타")
        is_finance = sector in [SectorType.BANK, SectorType.CAPITAL, SectorType.INSURANCE]
        
        if is_finance:
            return self._calculate_fs(sector, sector_kr, financials)
        else:
            return self._calculate_non_fs(sector, sector_kr, financials)

    def _calculate_fs(self, sector: SectorType, sector_kr: str, fin: FinancialInput) -> ValuationOutput:
        rules = self.config.FS_MULTIPLES.get(sector, self.config.FS_MULTIPLES[SectorType.GENERAL])
        multiple = rules["pbr"][1] # Mid 값 적용
        
        target_value = fin.equity_bn * multiple
        flags = []
        
        if fin.equity_bn <= 0:
            target_value = 0
            flags.append("Critical: 완전자본잠식 (지분가치 0 수렴)")

        return ValuationOutput(
            target_value_bn=round(target_value, 1),
            methodology=f"PBR {multiple:.2f}x ({sector_kr})",
            logic_summary=f"금융업({sector_kr}) 특성 반영: 자본총계 {fin.equity_bn:,.0f}억 × PBR {multiple:.2f}x",
            calculation_detail=f"Equity {fin.equity_bn:,.1f}bn × PBR {multiple:.2f}",
            warning_flags=flags
        )

    def _calculate_non_fs(self, sector: SectorType, sector_kr: str, fin: FinancialInput) -> ValuationOutput:
        rules = self.config.NON_FS_MULTIPLES.get(sector, self.config.NON_FS_MULTIPLES[SectorType.GENERAL])
        flags = []
        
        # 1. Primary: EV/EBITDA
        if fin.ebitda_bn > 0:
            multiple = rules["ev_ebitda"][1]
            ev = fin.ebitda_bn * multiple
            equity_value = ev - fin.net_debt_bn
            
            if equity_value < 0:
                equity_value = 0
                flags.append("Distressed: 순차입금 > EV (지분가치 0)")

            return ValuationOutput(
                target_value_bn=round(equity_value, 1),
                methodology=f"EV/EBITDA {multiple:.1f}x ({sector_kr})",
                logic_summary=f"{sector_kr} 표준 멀티플 적용: EBITDA {fin.ebitda_bn:,.0f}억 × {multiple:.1f}x - 순차입금",
                calculation_detail=f"(EBITDA {fin.ebitda_bn:,.1f} × {multiple}) - NetDebt {fin.net_debt_bn:,.1f}",
                warning_flags=flags
            )

        # 2. Fallback: PSR
        else:
            multiple = rules["psr"][1]
            equity_value = fin.revenue_bn * multiple
            flags.append("Note: 적자/미미한 이익으로 PSR 적용")
            
            return ValuationOutput(
                target_value_bn=round(equity_value, 1),
                methodology=f"PSR {multiple:.1f}x (적자기업)",
                logic_summary=f"성장성 지표 적용: 매출 {fin.revenue_bn:,.0f}억 × PSR {multiple:.1f}x",
                calculation_detail=f"Revenue {fin.revenue_bn:,.1f} × PSR {multiple:.1f}",
                warning_flags=flags
            )