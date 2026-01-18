"""
WOOD Transaction Services Engine - Issue Library v0.1

[Purpose]
Curated library of common transaction services issues by sector.

This is the "playbook" that WOOD uses to identify risks in target companies.
"""

from typing import List
from .schema import WoodIssue, Status


# ========================================================================
# ISSUE LIBRARY - COMMON CORE
# ========================================================================

COMMON_ISSUES = [
    {
        "id": "WOOD-CORE-01",
        "title": "Revenue Cut-off / Recognition",
        "tags": ["QoE", "High", "EBITDA_Down", "RevenueQuality"],
        "description": "매출 인식 시점이 계약서, 현금 흐름, 또는 실질적 인도 시점과 불일치. Revenue recognition policy가 aggressive하거나 기준이 불명확할 가능성.",
        "evidence": [
            "미청구매출(Unbilled Revenue) 급증",
            "선수금(Deferred Revenue)과 매출의 불일치",
            "기말 매출 spike (month-end loading)"
        ],
        "quantification": "-5.0 ~ -10.0",
        "lever": "가격조정 (매출 정상화) / SPA R&W (Revenue Recognition Policy)",
        "next_action": "TS Team: 매출 인식 정책 문서 요청 / 고객 컨펌 샘플링",
        "quantifiable": True,
        "decision_impact": True,
        "status": "Open"
    },
    {
        "id": "WOOD-CORE-02",
        "title": "One-off / Non-recurring Items",
        "tags": ["QoE", "Med", "EBITDA_Down"],
        "description": "일회성 비용·수익이 정상화(Normalization)되지 않아 EBITDA가 왜곡됨. 컨설팅비, 소송합의금, 구조조정 비용 등이 포함된 경우.",
        "evidence": [
            "전문용역비(Consulting fee) 급증",
            "소송 관련 비용 또는 합의금",
            "비정상적인 마케팅 캠페인 비용"
        ],
        "quantification": "+2.0 ~ +5.0",
        "lever": "QoE 조정 합의 (Normalized EBITDA 재정의)",
        "next_action": "TS: 비용 항목별 분석 (월별 추이 확인)",
        "quantifiable": True,
        "decision_impact": False,
        "status": "Open"
    },
    {
        "id": "WOOD-CORE-03",
        "title": "Capitalized Expenses",
        "tags": ["QoE", "High", "EBITDA_Down"],
        "description": "비용의 자산화(Capitalization)로 EBITDA가 과대 계상됨. 개발비, 수선비, 마케팅비 등이 자산으로 처리된 경우.",
        "evidence": [
            "개발비 자산 계상 (R&D capitalization)",
            "수선비의 자본적 지출 분류",
            "소프트웨어 개발비 자산화 비율 높음"
        ],
        "quantification": "-3.0 ~ -8.0",
        "lever": "EBITDA 조정 (비용 정상화) / 가격 재협상",
        "next_action": "TS: 자산화 정책 검토 / 업계 비교",
        "quantifiable": True,
        "decision_impact": True,
        "status": "Open"
    },
    {
        "id": "WOOD-CORE-04",
        "title": "Debt-like Items",
        "tags": ["NetDebt", "High", "NetDebt_Up"],
        "description": "차입금 외 채무성 항목이 Net Debt 정의에서 누락됨. 리스부채, 지급보증, 선수금, 미지급 배당 등.",
        "evidence": [
            "운영리스(Operating Lease) 규모 큼",
            "보증채무 또는 우발채무 존재",
            "선수금(Customer Deposits)이 환불 가능"
        ],
        "quantification": "+10.0 ~ +30.0",
        "lever": "Net Debt 정의 확장 (SPA Schedule 수정) / 가격 조정",
        "next_action": "TS: 리스 계약서 검토 / 보증 내역 확인",
        "quantifiable": True,
        "decision_impact": True,
        "status": "Open"
    },
    {
        "id": "WOOD-CORE-05",
        "title": "Working Capital Seasonality",
        "tags": ["WC", "Med", "WC_Up"],
        "description": "기준시점(Closing Date)의 Working Capital이 정상 수준(Normal Level)이 아님. 계절성 또는 일시적 요인으로 왜곡.",
        "evidence": [
            "분기별 WC 편차 큼 (>20%)",
            "매출채권 회수 지연 (DSO 증가)",
            "재고자산 적체 (Inventory turnover 하락)"
        ],
        "quantification": "+5.0 ~ +15.0",
        "lever": "WC Peg 재설정 (정상화된 WC target 합의) / True-up 메커니즘",
        "next_action": "TS: 과거 12개월 WC 추이 분석",
        "quantifiable": True,
        "decision_impact": False,
        "status": "Open"
    }
]


# ========================================================================
# SECTOR-SPECIFIC ISSUES
# ========================================================================

GAME_CONTENT_ISSUES = [
    {
        "id": "WOOD-GAME-01",
        "title": "Deferred Revenue Misclassification",
        "tags": ["NetDebt", "High", "NetDebt_Up"],
        "description": "선수금(Deferred Revenue)의 성격이 불명확. 환불 가능 여부, 서비스 제공 의무 등에 따라 Debt-like item 해당 가능.",
        "evidence": [
            "ARPU 대비 선수금 급증",
            "게임 서버 종료 시 환불 정책 불명확",
            "미사용 게임머니(Virtual Currency) 환불 가능"
        ],
        "quantification": "+5.0 ~ +15.0",
        "lever": "Net Debt 포함 (선수금의 일정 비율) / 에스크로 계정",
        "next_action": "Legal: 약관 검토 / TS: 환불율 분석",
        "quantifiable": True,
        "decision_impact": True,
        "status": "Open"
    },
    {
        "id": "WOOD-GAME-02",
        "title": "Live Ops Cost Volatility",
        "tags": ["QoE", "Med", "EBITDA_Down"],
        "description": "라이브 이벤트, UA(User Acquisition) 비용의 변동성이 커서 정상 EBITDA 산출 어려움.",
        "evidence": [
            "마케팅비 spike (신규 출시 또는 이벤트)",
            "월별 UA 비용 편차 >50%",
            "외주 개발비 불규칙"
        ],
        "quantification": "-2.0 ~ -5.0",
        "lever": "정상화 EBITDA 재정의 (Trailing 12M 평균) / Earn-out 구조",
        "next_action": "TS: 월별 비용 추이 분석 / 향후 런칭 계획 확인",
        "quantifiable": True,
        "decision_impact": False,
        "status": "Open"
    },
    {
        "id": "WOOD-GAME-03",
        "title": "IP Dependency Risk",
        "tags": ["Ops", "High", "Risk_Only"],
        "description": "특정 IP(지적재산권)에 매출이 집중되어, 라이선스 종료 또는 인기 하락 시 사업 존속 위험.",
        "evidence": [
            "Top 1 IP가 전체 매출의 60% 이상",
            "IP 라이선스 계약 만료 임박",
            "신규 IP 파이프라인 부재"
        ],
        "quantification": None,
        "lever": "멀티플 할인 (10-20% discount) / SPA Indemnity / Earn-out",
        "next_action": "BD: IP 계약서 검토 / 갱신 가능성 확인",
        "quantifiable": False,
        "decision_impact": True,
        "status": "Open"
    }
]

COMMERCE_PLATFORM_ISSUES = [
    {
        "id": "WOOD-COM-01",
        "title": "Gross vs Net Revenue Confusion",
        "tags": ["QoE", "High", "EBITDA_Down", "RevenueQuality"],
        "description": "Gross Revenue(총 거래액)와 Net Revenue(순 수수료)가 혼재되어 매출이 과대 계상됨. 플랫폼 비즈니스에서 흔함.",
        "evidence": [
            "매출액 대비 매출원가 비율이 >80% (수수료 사업 치고 높음)",
            "수수료(Commission) 구조 불명확",
            "GMV(Gross Merchandise Value)와 매출 혼용"
        ],
        "quantification": "-20.0 ~ -50.0",
        "lever": "매출 정의 재합의 (Net Revenue 기준) / 가격 재협상",
        "next_action": "TS: Revenue Waterfall 작성 / 회계정책 확인",
        "quantifiable": True,
        "decision_impact": True,
        "status": "Open"
    },
    {
        "id": "WOOD-COM-02",
        "title": "Refund / Return Provision",
        "tags": ["QoE", "Med", "EBITDA_Down"],
        "description": "반품(Return) 또는 환불(Refund) 충당금이 과소 설정되어 EBITDA 과대.",
        "evidence": [
            "반품률 상승 추세 (최근 6개월 증가)",
            "충당금 설정률 < 업계 평균",
            "고객 클레임 건수 급증"
        ],
        "quantification": "-1.0 ~ -3.0",
        "lever": "QoE 조정 (충당금 정상화) / 가격 조정",
        "next_action": "TS: 반품 데이터 분석 / 업계 벤치마크",
        "quantifiable": True,
        "decision_impact": False,
        "status": "Open"
    }
]

MANUFACTURING_ISSUES = [
    {
        "id": "WOOD-MFG-01",
        "title": "Inventory Obsolescence",
        "tags": ["QoE", "High", "EBITDA_Down", "WC_Up"],
        "description": "장기 재고가 누적되어 평가손실 위험. 또는 재고자산 평가충당금 부족.",
        "evidence": [
            "Aging 분석: 12개월 이상 재고 >30%",
            "재고회전율(Inventory Turnover) 하락",
            "불용 재고(Obsolete Inventory) 확인"
        ],
        "quantification": "-3.0 ~ -10.0",
        "lever": "WC Peg 조정 (불용 재고 제외) / 가격 조정 / 처분 계획 요구",
        "next_action": "TS: 재고 실사(Physical Count) / Aging 분석",
        "quantifiable": True,
        "decision_impact": True,
        "status": "Open"
    },
    {
        "id": "WOOD-MFG-02",
        "title": "Customer Concentration Risk",
        "tags": ["Ops", "High", "Risk_Only"],
        "description": "특정 거래처(Customer)에 매출이 집중되어, 계약 종료 시 사업 타격.",
        "evidence": [
            "Top 1 고객 매출 비중 >40%",
            "장기 계약 미체결 (년 단위 발주)",
            "대체 고객 확보 어려움 (시장 협소)"
        ],
        "quantification": None,
        "lever": "구조화: Earn-out (매출 유지 조건) / 에스크로 / 멀티플 할인",
        "next_action": "BD: 주요 고객 계약서 검토 / 계약 갱신 가능성 확인",
        "quantifiable": False,
        "decision_impact": True,
        "status": "Open"
    }
]

FINANCIAL_SERVICES_ISSUES = [
    {
        "id": "WOOD-FS-01",
        "title": "Yield Normalization Issue",
        "tags": ["QoE", "High", "EBITDA_Down"],
        "description": "일시적 고수익 구간이 반영되어 정상 EBITDA 과대. 연체율, 조달금리 변동성 고려 필요.",
        "evidence": [
            "최근 6개월 연체율 급증",
            "조달금리(Cost of Funds) 상승 추세",
            "대손충당금 적립률 < 업계 평균"
        ],
        "quantification": "-5.0 ~ -15.0",
        "lever": "정상화 가정 재설정 (Long-term average yield) / 가격 조정",
        "next_action": "TS: Vintage 분석 / 조달금리 추이 확인",
        "quantifiable": True,
        "decision_impact": True,
        "status": "Open"
    }
]


# ========================================================================
# LIBRARY LOADER
# ========================================================================

def get_issue_library(sector: str = "Common") -> List[WoodIssue]:
    """
    Load issue library by sector
    
    Args:
        sector: Sector name (Common, Game, Commerce, Manufacturing, FinancialServices)
    
    Returns:
        List of WoodIssue objects
    """
    # Always include common issues
    all_issues_data = COMMON_ISSUES.copy()
    
    # Add sector-specific issues
    sector_map = {
        "Game": GAME_CONTENT_ISSUES,
        "Content": GAME_CONTENT_ISSUES,
        "Commerce": COMMERCE_PLATFORM_ISSUES,
        "Platform": COMMERCE_PLATFORM_ISSUES,
        "Manufacturing": MANUFACTURING_ISSUES,
        "Manu": MANUFACTURING_ISSUES,
        "FinancialServices": FINANCIAL_SERVICES_ISSUES,
        "Finance": FINANCIAL_SERVICES_ISSUES,
        "FS": FINANCIAL_SERVICES_ISSUES
    }
    
    if sector in sector_map:
        all_issues_data.extend(sector_map[sector])
    
    # Convert dict to WoodIssue objects
    issues = []
    for issue_data in all_issues_data:
        try:
            issue = WoodIssue(**issue_data)
            issues.append(issue)
        except Exception as e:
            print(f"⚠️ Failed to load issue {issue_data.get('id', 'Unknown')}: {e}")
    
    return issues


def get_all_sectors() -> List[str]:
    """Get list of available sectors"""
    return ["Common", "Game", "Content", "Commerce", "Platform", 
            "Manufacturing", "Manu", "FinancialServices", "Finance", "FS"]


def search_issues(keyword: str, sector: str = "Common") -> List[WoodIssue]:
    """
    Search issues by keyword in title or description
    
    Args:
        keyword: Search keyword
        sector: Sector to search in
    
    Returns:
        Matching issues
    """
    all_issues = get_issue_library(sector)
    keyword_lower = keyword.lower()
    
    matches = []
    for issue in all_issues:
        if (keyword_lower in issue.title.lower() or 
            keyword_lower in issue.description.lower() or
            any(keyword_lower in tag.lower() for tag in issue.tags)):
            matches.append(issue)
    
    return matches
