import sys
import os
import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv

# Path Fix
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

# Agents & Utils
from src.agents.zulu_scout import ZuluScout
from src.agents.xray_val import XrayValuation
from src.agents.bravo_matchmaker import BravoMatchmaker
from src.agents.alpha_chief import AlphaChief
from src.utils.llm_handler import LLMHandler # 대화용 LLM

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
ALLOWED_USER_ID = os.getenv("TELEGRAM_CHAT_ID")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ==============================================================================
# 🧠 Context & State
# ==============================================================================
class DealSession:
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.target = None
        self.valuation = None
        self.buyers = None
        self.is_running = False
        self.stop_flag = False

sessions = {}

def get_session(chat_id):
    if chat_id not in sessions: sessions[chat_id] = DealSession(chat_id)
    return sessions[chat_id]

# ==============================================================================
# 💬 Chat Logic (The Brain)
# ==============================================================================
async def agent_chat_response(agent_name, user_input, session):
    """
    현재 딜 데이터를 참고하여 에이전트가 답변을 생성
    """
    brain = LLMHandler()
    
    # Context 구성
    context_str = f"Current Deal Context:\n"
    if session.target: context_str += f"- Target: {session.target}\n"
    if session.valuation: context_str += f"- Valuation: {session.valuation}\n"
    if session.buyers: context_str += f"- Buyers: {session.buyers}\n"
    
    system_prompt = f"""
    You are {agent_name}, a specialized AI agent in a Deal Team.
    Your Tone: Professional, Sharp, Insightful (Korean).
    
    [Context]
    {context_str}
    
    [User Question]
    {user_input}
    
    Task: Answer the user's question based ONLY on the Context provided.
    If you are X-RAY, explain the numbers. If BRAVO, explain the buyers.
    """
    
    response = brain.call_llm(system_prompt, user_input, mode="smart")
    return response

# ==============================================================================
# 🎮 Handlers
# ==============================================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != str(ALLOWED_USER_ID): return
    await update.message.reply_text(
        "👔 **Deal OS Interactive Room**\n"
        "프로세스 제어: `/run [기업명]`, `잠깐`, `계속`\n"
        "대화하기: `@X-RAY [질문]`, `@BRAVO [질문]`, `@ALPHA [질문]`"
    )

async def run_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query: return
    asyncio.create_task(process_pipeline(update, context, query))

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    session = get_session(update.effective_chat.id)
    
    # 1. 프로세스 제어 명령
    if text in ["잠깐", "멈춰", "스톱", "stop", "중단"]:
        session.stop_flag = True
        await update.message.reply_text("🛑 **System**: 프로세스 일시 정지. (질문이나 피드백을 주세요)")
        return
        
    if text == "계속":
        await update.message.reply_text("▶️ 프로세스 재개 (기능 구현 중 - 현재는 다시 /run 필요)")
        return

    # 2. 에이전트 호출 (Interactive Chat)
    if "@" in text:
        agent_name = None
        if "X-RAY" in text.upper() or "엑스레이" in text: agent_name = "X-RAY"
        elif "BRAVO" in text.upper() or "브라보" in text: agent_name = "BRAVO"
        elif "ALPHA" in text.upper() or "알파" in text: agent_name = "ALPHA"
        elif "ZULU" in text.upper() or "줄루" in text: agent_name = "ZULU"
        
        if agent_name:
            if not session.target:
                await update.message.reply_text(f"🤖 **{agent_name}**: 현재 진행 중인 딜이 없습니다. `/run`으로 시작해주세요.")
                return
            
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING)
            
            # 비동기로 답변 생성
            loop = asyncio.get_running_loop()
            answer = await loop.run_in_executor(None, lambda: LLMHandler().call_llm(
                f"You are {agent_name}. Speak Korean. Context: {session.target} {session.valuation}", 
                f"User asked: {text}. Explain based on context.", "smart"
            ))
            
            await update.message.reply_text(f"🗣️ **{agent_name}**: {answer}")
            return

    # 그 외 잡담
    await update.message.reply_text("🤖 명령어를 입력하거나 에이전트를 호출(@)하세요.")

# ==============================================================================
# ⛓️ The Pipeline
# ==============================================================================
async def process_pipeline(update, context, query):
    session = get_session(update.effective_chat.id)
    session.is_running = True
    session.stop_flag = False
    
    # ZULU
    await update.message.reply_text(f"🕵️ **ZULU**: '{query}' 조사 시작.")
    zulu = ZuluScout()
    loop = asyncio.get_running_loop()
    leads = await loop.run_in_executor(None, zulu.search_leads, query)
    
    if not leads:
        await update.message.reply_text("🕵️ **ZULU**: 실패. 종료.")
        return
        
    target = leads[0]
    if "N/A" in target['company_name']: target['company_name'] = query
    session.target = target
    await update.message.reply_text(f"🕵️ **ZULU**: 타겟 '{target['company_name']}' 확보.\n👉 X-RAY 호출.")
    
    if session.stop_flag: await stop_msg(update); return
    await asyncio.sleep(1)

    # X-RAY
    xray = XrayValuation()
    val_result = await loop.run_in_executor(None, xray.run_valuation, target)
    session.valuation = val_result
    
    val_txt = f"💰 **{val_result['valuation']['target_value']}억** ({val_result['valuation']['method']})"
    await update.message.reply_text(f"⚡ **X-RAY**: 밸류 산출.\n{val_txt}\n👉 BRAVO 호출.")
    
    if session.stop_flag: await stop_msg(update); return
    await asyncio.sleep(1)

    # BRAVO
    bravo = BravoMatchmaker()
    buyers = await loop.run_in_executor(None, bravo.find_potential_buyers, target, val_result['financials'].get('sector', 'General'))
    session.buyers = buyers
    
    if buyers:
        b_names = ", ".join([b['buyer_name'] for b in buyers])
        await update.message.reply_text(f"🤝 **BRAVO**: {b_names}\n👉 ALPHA 검증/작성.")
    else:
        await update.message.reply_text("🤝 **BRAVO**: 매수자 없음.")
        
    if session.stop_flag: await stop_msg(update); return
    await asyncio.sleep(1)

    # ALPHA
    alpha = AlphaChief()
    audit = alpha.audit_deal_integrity(target, val_result, buyers)
    
    if not audit['passed']:
        await update.message.reply_text(f"👑 **ALPHA**: ⛔ 리포트 반려.\n이유: {audit['issues'][0]}")
    else:
        teaser = await loop.run_in_executor(None, alpha.generate_teaser, target, val_result, buyers)
        await update.message.reply_text(teaser)

    session.is_running = False

async def stop_msg(update):
    await update.message.reply_text("🛑 프로세스 정지됨. (대화 가능)")

if __name__ == '__main__':
    if not TOKEN: exit()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("run", run_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    print("=== 👔 Deal OS Interactive Server Running... ===")
    app.run_polling()