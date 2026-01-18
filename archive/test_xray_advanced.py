from src.agents.xray_val import XrayValuation

def test_multiple_lab_logic():
    print("=== ⚡ X-RAY: Multiple Lab Logic Test ===\n")
    
    # Case 1: 적자지만 매출은 있는 SaaS 스타트업
    lead_tech = {
        "company_name": "코드브릭(SaaS)",
        "signal_reason": "시리즈B 실패, 런웨이 고갈",
        "body": "AI 코딩 솔루션 개발사. 이용자 급증했으나 수익화 지연으로 자금난. 매출 50억, 영업손실 20억."
    }
    
    # Case 2: 잘나가는 K-뷰티 브랜드
    lead_beauty = {
        "company_name": "퓨어스킨(K-Beauty)",
        "signal_reason": "수출 대박, 운영자금 확보 필요",
        "body": "미국 아마존 1위 달성. 매출 300억, 영업이익 50억. 재고 확보를 위한 투자 유치 희망."
    }

    # Case 3: 급매로 나온 지방 공장
    lead_factory = {
        "company_name": "대성정밀(제조)",
        "signal_reason": "70대 오너 건강악화, 폐업 고려",
        "body": "시화공단 자동차 부품 제조. 매출 100억, 이익 5억. 오너가 빨리 처분하고 싶어함(Urgency High)."
    }

    xray = XrayValuation()
    
    for lead in [lead_tech, lead_beauty, lead_factory]:
        print(f"target: {lead['company_name']}")
        res = xray.run_valuation(lead)
        val = res['valuation']
        fin = res['financials']
        
        print(f"  - Sector: {val['logic_applied']['sector']}")
        print(f"  - Financials: Rev {fin['est_revenue_bn']}억 / Op {fin['est_profit_bn']}억")
        print(f"  - Method: {val['method']}")
        print(f"  - Value: {val['target_value']} 억 KRW")
        print(f"  - Strategy: {res['deal_strategy']}")
        print("-" * 50)

if __name__ == "__main__":
    test_multiple_lab_logic()