import sys
import os
import asyncio
import logging
from datetime import datetime
from pytz import timezone

# [Path Setup]
# 현재 파일 위치: src/main.py -> project_root: MIRKWOOD AI/
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

# [Libraries]
from telegram import Update, BotCommand
from telegram.constants import ParseMode, ChatAction
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler 
from dotenv import load_dotenv

# [Agents]
from src.agents.zulu_scout import ZuluScout
from src.agents.xray_val import XrayValuation
from src.agents.bravo_matchmaker import BravoMatchmaker
from src.agents.alpha_chief import AlphaChief
from src.utils.llm_handler import LLMHandler

# [Engines]
# from src.engines.orchestrator import WoodOrchestrator  # WOOD V1 DCF Engine (Legacy - Preserved)
from src.engines.wood.orchestrator_v2 import WoodOrchestratorV2  # WOOD V2 Engine (Nexflex Std.)

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
# 허용된 사용자 ID 리스트 (쉼표로 구분)
ALLOWED_IDS = os.getenv("TELEGRAM_CHAT_ID", "").split(",")

# [Logging]
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ==============================================================================
# 🧠 Session Manager (Multi-Session Support)
# ==============================================================================
class DealSession:
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.is_running = False
        self.stop_flag = False
        self.mode = None # 'PIPELINE', 'DCF', 'STRUCT'
        self.data = {
            "target": None,
            "valuation": None,
            "buyers": None,
            "dcf_result": None
        }

    def reset(self):
        self.stop_flag = False
        self.mode = None
        self.data = {k: None for k in self.data}

sessions = {}

def get_session(chat_id):
    if chat_id not in sessions:
        sessions[chat_id] = DealSession(chat_id)
    return sessions[chat_id]

scheduler = AsyncIOScheduler(timezone=timezone('Asia/Seoul'))

# ==============================================================================
# 💬 Chat Logic (Interactive Agent)
# ==============================================================================
async def agent_chat_response(agent_name, user_input, session):
    brain = LLMHandler()
    
    # 컨텍스트 조립
    ctx_str = "Current Deal Context:\n"
    if session.data['target']: 
        ctx_str += f"- Target: {session.data['target'].get('company_name')} ({session.data['target'].get('sector')})\n"
    if session.data['valuation']: 
        val = session.data['valuation']['valuation']
        ctx_str += f"- Quick Val: {val['target_value']}Bn KRW (Method: {val['method']})\n"
    if session.data['buyers']:
        buyers = [b['buyer_name'] for b in session.data['buyers']]
        ctx_str += f"- Buyers: {', '.join(buyers)}\n"

    system_prompt = f"""
    You are {agent_name}, a partner at MIRKWOOD Partners.
    Respond to the user based on the Deal Context below.
    
    [Role]
    - X-RAY: Financials & Valuation Logic
    - BRAVO: Market Matching & Buyer Rationale
    - ALPHA: Overall Strategy & Structuring
    
    [Deal Context]
    {ctx_str}
    
    Task: Answer professionally in Korean. Be concise.
    """
    return await asyncio.get_running_loop().run_in_executor(
        None, lambda: brain.call_llm(system_prompt, user_input, mode="smart")
    )

# ==============================================================================
# 🚀 Command Handlers
# ==============================================================================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🌲 **MIRKWOOD Partners : Deal OS Manual**

**1. 🚀 Deal Pipeline**
`/run [기업명]` : 소싱 -> 밸류 -> 매칭 -> 리포트 (Full Process)

**2. 🛠️ Professional Tools**
`/dcf [프로젝트명] [매출액]` : 시나리오 DCF 분석 및 엑셀 생성 (WOOD Engine)
`/struct` : 메자닌/구조화 설계 도구 (Phase 4)

**3. ⚙️ Controls**
`잠깐`, `중단` : 프로세스 강제 종료
`@X-RAY [질문]` : 에이전트와 대화
`/id` : 현재 채팅방 ID 확인
    """
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def run_pipeline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    query = " ".join(context.args)
    
    if not query:
        await update.message.reply_text("⚠️ 사용법: `/run [기업명]`")
        return

    session = get_session(chat_id)
    if session.is_running:
        await update.message.reply_text("⚠️ 이미 작업 중입니다. `중단` 후 다시 시도하세요.")
        return

    session.reset()
    session.is_running = True
    session.mode = 'PIPELINE'
    
    try:
        # 1. ZULU
        if session.stop_flag: raise InterruptedError()
        await update.message.reply_text(f"🕵️ **ZULU**: '{query}' 타겟팅 시작...")
        
        zulu = ZuluScout()
        loop = asyncio.get_running_loop()
        leads = await loop.run_in_executor(None, zulu.search_leads, query)

        if not leads:
            await update.message.reply_text("💤 **ZULU**: 타겟 발굴 실패.")
            return

        target = leads[0]
        if "N/A" in target['company_name']: target['company_name'] = query
        session.data['target'] = target
        
        await update.message.reply_text(f"✅ **ZULU**: {target['company_name']} ({target.get('sector')})\n👉 X-RAY 이관")

        # 2. X-RAY
        if session.stop_flag: raise InterruptedError()
        await update.message.reply_text("⚡ **X-RAY**: 재무 분석 및 Quick Valuation...")
        
        xray = XrayValuation()
        val_result = await loop.run_in_executor(None, xray.run_valuation, target)
        session.data['valuation'] = val_result
        
        val = val_result['valuation']
        await update.message.reply_text(f"⚡ **X-RAY**: {val['target_value']}억 (Method: {val['method']})\n👉 BRAVO 이관")

        # 3. BRAVO
        if session.stop_flag: raise InterruptedError()
        await update.message.reply_text("🤝 **BRAVO**: 인수 후보자 스크리닝...")
        
        bravo = BravoMatchmaker()
        industry = val_result['financials'].get('sector') or target.get('sector', 'General')
        buyers = await loop.run_in_executor(None, bravo.find_potential_buyers, target, industry)
        session.data['buyers'] = buyers
        
        b_list = ", ".join([b['buyer_name'] for b in buyers]) if buyers else "없음"
        await update.message.reply_text(f"🤝 **BRAVO**: {b_list}\n👉 ALPHA 리포트 작성")

        # 4. ALPHA
        if session.stop_flag: raise InterruptedError()
        alpha = AlphaChief()
        teaser = await loop.run_in_executor(None, alpha.generate_teaser, target, val_result, buyers)
        await update.message.reply_text(teaser)

    except InterruptedError:
        await update.message.reply_text("🛑 프로세스 중단됨.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
        print(f"Pipeline Error: {e}")
    finally:
        session.is_running = False

async def run_dcf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    [WOOD Engine] 시나리오 DCF 수행 및 엑셀 파일 전송
    
    Usage: /dcf [기업명] [매출액(선택)]
    
    Process:
    1. SmartIngestor가 DART → 웹검색 순으로 데이터 수집
    2. 데이터 출처를 사용자에게 고지
    3. Big 4 스타일 엑셀 생성 및 전송
    """
    from src.tools.smart_ingestor import SmartFinancialIngestor
    
    chat_id = update.effective_chat.id
    args = context.args
    if not args:
        await update.message.reply_text(
            "⚠️ **사용법:**\n"
            "`/dcf [기업명]` - 자동 데이터 수집\n"
            "`/dcf [기업명] [매출액]` - 수동 입력",
            parse_mode='Markdown'
        )
        return

    company_name = args[0]
    manual_revenue = float(args[1]) if len(args) > 1 else None

    session = get_session(chat_id)
    session.reset()
    session.is_running = True
    session.mode = 'DCF'

    try:
        loop = asyncio.get_running_loop()
        
        # ================================================================
        # STEP 1: SMART DATA INGESTION
        # ================================================================
        await update.message.reply_text(
            f"🔎 **'{company_name}' 데이터 수집 중...**\n"
            "1️⃣ DART 공식 재무제표 확인\n"
            "2️⃣ 웹 검색 (뉴스/실적 추정)\n"
            "3️⃣ 사용자 입력 대기"
        )
        
        ingestor = SmartFinancialIngestor()
        
        # Try automated data collection
        if manual_revenue is not None:
            # Manual override mode
            fin_data = await loop.run_in_executor(
                None, 
                ingestor.ingest_with_override, 
                company_name, 
                manual_revenue, 
                manual_revenue * 0.1  # Assume 10% OP margin
            )
        else:
            # Automated mode
            fin_data = await loop.run_in_executor(
                None, 
                ingestor.ingest, 
                company_name
            )
        
        # Check if user input required
        if fin_data.get('requires_input'):
            await update.message.reply_text(
                "❌ **데이터 수집 실패**\n\n"
                "자동 데이터 수집에 실패했습니다.\n"
                "수동 입력으로 다시 시도해주세요:\n\n"
                "`/dcf {} [매출액(억원)]`".format(company_name),
                parse_mode='Markdown'
            )
            return
        
        base_revenue = fin_data['revenue']
        data_source = fin_data['source']
        confidence = fin_data.get('confidence', 'Unknown')
        
        # ================================================================
        # STEP 2: DATA CONFIRMATION MESSAGE
        # ================================================================
        confidence_emoji = {
            "High": "✅",
            "Medium": "⚠️",
            "User-Provided": "👤"
        }
        emoji = confidence_emoji.get(confidence, "ℹ️")
        
        await update.message.reply_text(
            f"📊 **데이터 수집 완료**\n\n"
            f"{emoji} **출처:** {data_source}\n"
            f"📈 **매출:** {base_revenue:.1f}억 원\n"
            f"💰 **영업이익:** {fin_data['op']:.1f}억 원\n\n"
            f"_{fin_data['description']}_\n\n"
            f"🌲 **WOOD V2**: '{company_name}' 정밀 밸류에이션(Nexflex Std.) 수행 중...",
            parse_mode='Markdown'
        )
        
        # ================================================================
        # STEP 3: GENERATE DCF VALUATION (WOOD V2)
        # ================================================================
        wood = WoodOrchestratorV2()
        
        # 엑셀 생성 (CPU-bound, Blocking I/O) -> Executor 사용
        filepath, summary = await loop.run_in_executor(
            None, 
            wood.run_valuation, 
            company_name, 
            base_revenue,
            data_source  # Pass data source for Excel attribution
        )
        
        # ================================================================
        # STEP 4: SEND RESULTS
        # ================================================================
        
        # 1. 요약 텍스트
        await update.message.reply_text(summary, parse_mode='Markdown')
        
        # 2. 엑셀 파일 전송
        await update.message.reply_document(
            document=open(filepath, 'rb'),
            filename=os.path.basename(filepath),
            caption=(
                f"📊 **{company_name} DCF Valuation Package**\n\n"
                f"✅ Big 4 회계법인 스타일 적용:\n"
                f"• 파란색 = 입력값 (Assumptions)\n"
                f"• 검은색 = 계산값 (Formulas)\n"
                f"• 데이터 출처: {data_source}\n\n"
                f"📑 **(Detailed 9-Sheet Model included)**"
            )
        )

    except Exception as e:
        await update.message.reply_text(f"❌ WOOD Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.is_running = False

async def run_struct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    [OPM Engine] Hybrid securities valuation (RCPS, CB)
    
    Usage: /struct [기업명] [주가] [전환가]
    """
    from src.engines.wood.opm_engine import OPMCalculator
    
    args = context.args
    if len(args) < 3:
        await update.message.reply_text(
            "🏗️ **OPM Structuring Engine**\n\n"
            "**사용법:**\n"
            "`/struct [기업명] [현재주가] [전환가]`\n\n"
            "**예시:**\n"
            "`/struct CompanyA 20000 25000`\n\n"
            "**기능:**\n"
            "• TF 모델 (Debt/Equity 분리 할인)\n"
            "• IPO 조건부 리픽싱 시뮬레이션\n"
            "• 구조화 옵션 제안",
            parse_mode='Markdown'
        )
        return
    
    company_name = args[0]
    stock_price = float(args[1])
    conversion_price = float(args[2])
    
    await update.message.reply_text(
        f"🏗️ **OPM Engine**\n"
        f"'{company_name}' 하이브리드 증권 평가 중...\n\n"
        f"• 주가: {stock_price:,.0f}원\n"
        f"• 전환가: {conversion_price:,.0f}원"
    )
    
    try:
        loop = asyncio.get_running_loop()
        calculator = OPMCalculator()
        
        # Quick valuation (default assumptions)
        result = await loop.run_in_executor(
            None,
            calculator.quick_rcps_valuation,
            company_name,
            stock_price,
            conversion_price,
            50000,  # Face value per share (default)
            10000,  # Number of shares (default)
            3.0     # 3 years to maturity
        )
        
        # Format response
        response = f"""
🏗️ **{company_name} OPM 평가 결과**

**[TF Model - Split Discounting]**

**Total Fair Value:** {result['total_value']:,.0f}원
  • Host (Debt Component): {result['debt_component']:,.0f}원
  • Option (Equity Component): {result['equity_component']:,.0f}원

**Split Ratio:** {result['split_ratio']*100:.1f}% (Equity / Total)

**Model Details:**
• Lattice Steps: {result['lattice_steps']}
• Final Conversion Price: {result['conversion_price_final']:,.0f}원
• Model: {result['model']} (Tsiveriotis-Fernandes)

**Interpretation:**
• Debt Component는 {result['parameters']['rf']*100:.1f}% + {result['parameters']['cs']*100:.1f}% = {(result['parameters']['rf']+result['parameters']['cs'])*100:.1f}%로 할인
• Equity Component는 {result['parameters']['rf']*100:.1f}% (Risk-Free)로 할인

⚠️ *Professional OPM model with TF split discounting*
"""
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ OPM Error: {e}")
        import traceback
        traceback.print_exc()


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text
    session = get_session(chat_id)

    # 1. 제어 명령
    if text in ["잠깐", "멈춰", "중단", "stop"]:
        if session.is_running:
            session.stop_flag = True
            await update.message.reply_text("🛑 중단 신호 접수.")
        else:
            await update.message.reply_text("💤 실행 중인 프로세스 없음.")
        return

    # 2. ID 확인
    if text == "/id":
        await update.message.reply_text(f"🆔 Chat ID: `{chat_id}`")
        return

    # 3. 에이전트 대화
    if "@" in text:
        agent_name = None
        if "X-RAY" in text.upper() or "엑스레이" in text: agent_name = "X-RAY"
        elif "BRAVO" in text.upper() or "브라보" in text: agent_name = "BRAVO"
        elif "ALPHA" in text.upper() or "알파" in text: agent_name = "ALPHA"
        
        if agent_name:
            await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
            response = await agent_chat_response(agent_name, text, session)
            await update.message.reply_text(f"🗣️ **{agent_name}**: {response}")

# ==============================================================================
# ⏰ Scheduler & Lifecycle
# ==============================================================================
async def scheduled_alert(app, query):
    # 등록된 첫 번째 사용자에게 알림 (파트너님)
    target_chat_id = ALLOWED_IDS[0] if ALLOWED_IDS else None
    if not target_chat_id: return
    
    # 세션 확인 (이미 사용 중이면 패스)
    if get_session(target_chat_id).is_running: return
    
    await app.bot.send_message(chat_id=target_chat_id, text=f"🔔 **Daily Opportunity**: '{query}' 확인 요망.")

async def post_init(application):
    print("🟢 MIRKWOOD Server Started. Configuring...")
    
    # 1. 메뉴 버튼 설정
    commands = [
        ("run", "🚀 Deal Pipeline (Full)"),
        ("dcf", "📉 DCF Scenario Tool (Excel)"),
        ("struct", "🏗️ Structuring Tool"),
        ("help", "📚 Manual"),
        ("id", "🆔 Check Chat ID")
    ]
    await application.bot.set_my_commands(commands)
    
    # 2. 스케줄러 시작
    scheduler.start()
    scheduler.add_job(scheduled_alert, 'cron', hour=9, args=[application, '"법인회생" 제조'])
    scheduler.add_job(scheduled_alert, 'cron', hour=14, args=[application, '"스타트업" M&A'])
    
    # 3. 부팅 알림
    for chat_id in ALLOWED_IDS:
        try:
            if chat_id:
                await application.bot.send_message(chat_id=chat_id, text="🌲 **MIRKWOOD Partners Online**\nReady to serve.")
        except: pass

# ==============================================================================
# 🚀 Main Entry
# ==============================================================================
if __name__ == '__main__':
    if not TOKEN: 
        print("❌ Error: TELEGRAM_TOKEN missing in .env")
        exit()
    
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    
    app.add_handler(CommandHandler("run", run_pipeline))
    app.add_handler(CommandHandler("dcf", run_dcf))
    app.add_handler(CommandHandler("struct", run_struct))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    
    print("=== 🌲 MIRKWOOD AI Lab Server Running ===")
    app.run_polling()