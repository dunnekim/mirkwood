import os
import requests
from dotenv import load_dotenv

load_dotenv()

def send_agent_log(agent_name, icon, message):
    """
    텔레그램으로 로그 전송 (설정 없으면 콘솔 출력만 수행)
    """
    # 1. 무조건 콘솔에는 출력 (디버깅용)
    print(f"\n[{icon} {agent_name}] {message}\n")

    # 2. 텔레그램 전송 시도
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        # 키가 없으면 조용히 리턴 (에러 발생 X)
        return

    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id, 
            "text": f"{icon} **{agent_name}**\n\n{message}", 
            "parse_mode": "Markdown"
        }
        requests.post(url, json=payload, timeout=3)
    except Exception as e:
        print(f"⚠️ Telegram Error: {e}")