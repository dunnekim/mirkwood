import os

def create_mirk_structure():
    # 1. 폴더 구조 정의 (4개 클러스터 및 Skills/Vault 반영)
    directories = [
        "src/agents",       # SCOUT, LOGIC, FILTER, CHIEF 로직
        "src/tools",        # Web Scraper, Multiple Engine, PDF Render
        "src/config",       # API Settings, Constants
        "src/utils",        # LLM Handler (Budget Guard)
        "src/dashboard",    # Streamlit UI
        "knowledge",        # Agent Skills (Valuation Rules, Sourcing Logic)
        "vault/leads",      # 분석 리드 데이터 저장소
        "vault/buyers",     # PE/SI 데이터베이스
        "vault/logs"        # 시스템 로그
    ]
    
    # 폴더 생성
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        # __init__.py 생성 (패키지 인식용)
        init_file = os.path.join(directory, "__init__.py")
        if not os.path.exists(init_file):
            open(init_file, 'w').close()
            
    # 2. 필수 초기 파일 생성
    files = {
        ".env": (
            "OPENAI_API_KEY=your_key_here\n"
            "ANTHROPIC_API_KEY=your_key_here\n"
            "TELEGRAM_TOKEN=your_token_here\n"
            "DAILY_BUDGET_USD=2.0\n"
        ),
        ".gitignore": ".env\nvault/\n__pycache__/\n*.pyc\n.cursorrules", # .cursorrules는 직접 관리 위해 제외 가능
        "requirements.txt": (
            "openai\nanthropic\nstreamlit\napscheduler\n"
            "python-telegram-bot\npandas\nrequests\nbeautifulsoup4\nlitellm"
        ),
        "README.md": "# MIRK Deal OS\nLevel 4 Edge Creator for M&A Sourcing",
        "src/config/settings.py": (
            "DEFAULT_MODEL_CHEAP = 'gpt-4o-mini'\n"
            "DEFAULT_MODEL_SMART = 'claude-3-5-sonnet'\n"
            "DAILY_CAP_USD = 2.0\n"
        )
    }

    for path, content in files.items():
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ Created: {path}")

    print("\n[Step 1 완료] 폴더 구조와 기본 파일이 세팅되었습니다.")
    print("다음 단계(Step 2)로 넘어가려면 말씀해주세요.")

if __name__ == "__main__":
    create_mirk_structure()