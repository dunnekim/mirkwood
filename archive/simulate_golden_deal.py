import time
from src.agents.xray_val import XrayValuation
from src.agents.alpha_chief import AlphaChief
from src.utils.telegram_sender import send_agent_log

def simulate_perfect_lead():
    print("=== 🎰 Deal OS: Golden Deal Simulation ===")
    send_agent_log("SYSTEM", "🧪", "시뮬레이션 모드: 가상의 '완벽한 딜'을 파이프라인에 주입합니다.")
    
    # 1. ZULU가 찾았다고 가정하는 '완벽한 리드' 데이터
    fake_lead = {
        "company_name": "(주)대성정밀 (가칭)",
        "signal_strength": "High",
        "signal_reason": "시화공단 30년 업력 주물 제조사. 78세 대표 건강 악화로 승계 포기 및 급매(Asset Deal) 희망 의사 피력 인터뷰.",
        "url": "http://simulation.test/news/12345",
        "body": "시화국가산단에 위치한 (주)대성정밀(대표 김철수, 78)이 매물로 나왔다. 작년 매출 220억, 영업이익 15억을 기록한 알짜 기업이지만, 자녀들의 승계 거부와 대표의 건강 악화로 폐업 대신 매각을 선택했다. 금융권 관계자는 '청산가치 수준의 매각도 고려 중'이라고 전했다."
    }

    send_agent_log("ZULU", "🕵️", 
                   f"📍 **[SIMULATION] Hidden Deal 발견!**\n\n"
                   f"기업: {fake_lead['company_name']}\n"
                   f"사유: {fake_lead['signal_reason']}\n"
                   f"@X-RAY, 긴급 밸류에이션 요청.")
    
    time.sleep(3)

    # 2. X-RAY: 가치 평가 (SME Logic 검증)
    print("\n⚡ X-RAY: Valuating...")
    xray = XrayValuation()
    val_result = xray.run_valuation(fake_lead)
    
    # 결과 로그 전송
    urgency = val_result['financials'].get('urgency_score', 0)
    send_agent_log("X-RAY", "⚡", 
                   f"**분석 완료**\n"
                   f"Target: {val_result['company']}\n"
                   f"Urgency: {urgency}/10 (매우 급함)\n"
                   f"Est. Value: {val_result['valuation']['target_value']} 억\n"
                   f"Strategy: {val_result['deal_strategy']}")
    
    time.sleep(3)

    # 3. ALPHA: 티저 작성 (Final Output 검증)
    print("\n👑 ALPHA: Writing Teaser...")
    alpha = AlphaChief()
    teaser = alpha.generate_teaser(fake_lead, val_result)
    
    send_agent_log("ALPHA", "👑", 
                   f"**Investment Teaser (SIMULATION)**\n\n"
                   f"{teaser[:300]}...\n\n"
                   f"👉 **Decision: [STRONG BUY]**")

if __name__ == "__main__":
    simulate_perfect_lead()