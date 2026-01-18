import sys
import os
import time
import datetime
import schedule
import random
import asyncio

# [CRITICAL] 프로젝트 루트 경로 강제 지정 (bot_server와 동일하게)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = current_dir # run_daily_rotation은 루트에 있으므로 그대로
sys.path.append(project_root)

# 최신 모듈 임포트
from src.agents.zulu_scout import ZuluScout
from src.agents.xray_val import XrayValuation
from src.agents.bravo_matchmaker import BravoMatchmaker
from src.agents.alpha_chief import AlphaChief
from src.utils.telegram_sender import send_agent_log

# [Theme Definition]
THEMES = {
    "MORNING": {
        "name": "🏭 제조 & 뿌리산업 (SME Distress)",
        "queries": ['"법인회생" 신청 제조 기업', '"공장 경매" 진행', '"가업승계" 포기 매물']
    },
    "NOON": {
        "name": "💄 소비재 & F&B (Small Cap)",
        "queries": ['"프랜차이즈" 매물', '"화장품" 브랜드 경영권 매각', '"건기식" 지분 매각']
    },
    "AFTERNOON": {
        "name": "💻 Tech & SaaS (Series B Crunch)",
        "queries": ['"스타트업" 경영권 매각', '"플랫폼" 서비스 종료', '"핀테크" 구조조정']
    },
    "NIGHT": {
        "name": "🏦 NPL & 특수물건 (Asset Deal)",
        "queries": ['"부실채권" 매각 공고', '"물류센터" 급매', '"골프장" 매물 M&A']
    }
}

def get_current_theme():
    hour = datetime.datetime.now().hour
    if 5 <= hour < 10: return THEMES["MORNING"]
    elif 10 <= hour < 14: return THEMES["NOON"]
    elif 14 <= hour < 18: return THEMES["AFTERNOON"]
    else: return THEMES["NIGHT"]

async def run_pipeline_async():
    """비동기 파이프라인 실행 (Server Logic과 동일 품질 보장)"""
    try:
        # 0. 테마 선정
        theme = get_current_theme()
        target_query = random.choice(theme["queries"])

        send_agent_log("SYSTEM", "🔄", f"**[Daily Rotation]**\n테마: {theme['name']}\nTarget Query: {target_query}")
        
        loop = asyncio.get_running_loop()

        # 1. ZULU
        zulu = ZuluScout()
        leads = await loop.run_in_executor(None, zulu.search_leads, target_query)
        if not leads: 
            send_agent_log("SYSTEM", "💤", "유의미한 시그널 없음.")
            return

        target = leads[0]
        # N/A 보정
        if "N/A" in target['company_name']: target['company_name'] = target_query
        
        send_agent_log("ZULU", "🕵️", f"Lead 포착: {target['company_name']}\n👉 X-RAY 호출")
        time.sleep(1)

        # 2. X-RAY (Rulebook 적용됨)
        xray = XrayValuation()
        val_result = await loop.run_in_executor(None, xray.run_valuation, target)
        
        val = val_result['valuation']
        # Skip 조건 체크
        if val_result.get('status') == "HOLD_TOO_BIG":
            send_agent_log("X_RAY", "⚠️", f"분석 보류 (Too Big)\n{val['target_value']}억 - 부티크 타겟 초과")
            return

        send_agent_log("X_RAY", "⚡", f"가치 산정: {val['target_value']}억 KRW\nMethod: {val['method']}\n👉 BRAVO 호출")
        time.sleep(1)

        # 3. BRAVO
        bravo = BravoMatchmaker()
        industry = val_result['financials'].get('sector') or "General"
        buyers = await loop.run_in_executor(None, bravo.find_potential_buyers, target, industry)
        
        buyer_msg = "적절한 매수자 못 찾음"
        if buyers:
            buyer_msg = f"Candidates: {', '.join([b['buyer_name'] for b in buyers])}"
        
        send_agent_log("BRAVO", "🤝", f"{buyer_msg}\n👉 ALPHA 호출")
        time.sleep(1)

        # 4. ALPHA (Audit & Codename 적용)
        alpha = AlphaChief()
        
        # Audit 수행
        audit = alpha.audit_deal_integrity(target, val_result, buyers)
        if not audit['passed']:
            send_agent_log("ALPHA", "⛔", f"리포트 반려\n이유: {audit['issues'][0]}")
            return

        teaser = await loop.run_in_executor(None, alpha.generate_teaser, target, val_result, buyers)
        send_agent_log("ALPHA", "👑", f"{teaser}")

    except Exception as e:
        send_agent_log("SYSTEM", "❌", f"오퍼레이션 오류: {str(e)}")
        print(f"Error: {e}")

def run_rotation_mission():
    """스케줄러에서 호출하는 동기 래퍼"""
    asyncio.run(run_pipeline_async())

if __name__ == "__main__":
    print("=== Deal OS: Daily Bot Mode Activated (Synced with Pro Logic) ===")
    
    # 테스트용 1회 즉시 실행
    run_rotation_mission()
    
    schedule.every().day.at("08:00").do(run_rotation_mission)
    schedule.every().day.at("12:00").do(run_rotation_mission)
    schedule.every().day.at("16:00").do(run_rotation_mission)
    schedule.every().day.at("20:00").do(run_rotation_mission)

    while True:
        schedule.run_pending()
        time.sleep(1)