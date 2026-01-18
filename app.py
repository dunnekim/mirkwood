import streamlit as st
import time
import json
import os
from src.agents.zulu_scout import ZuluScout
from src.agents.xray_val import XrayValuation
from src.agents.alpha_chief import AlphaChief

# 페이지 설정
st.set_page_config(page_title="MIRK Deal OS", page_icon="💼", layout="wide")

# 스타일 커스텀 (IB 느낌의 Dark Theme)
st.markdown("""
<style>
    .stApp {background-color: #0e1117;}
    .metric-card {background-color: #262730; padding: 20px; border-radius: 10px; color: white;}
</style>
""", unsafe_allow_html=True)

st.title("💼 MIRK Deal OS <v1.0>")
st.caption("Level 4 Autonomous M&A Sourcing Engine | Powered by Local LLM")

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ Operation Panel")
    target_keyword = st.text_input("Sourcing Keyword", "투자 유치 희망 스타트업")
    run_btn = st.button("🚀 Start Deal Sourcing", type="primary")
    st.divider()
    st.info("System Status: Online\nLLM: Ollama (Llama3)")

# 메인 실행 로직
if run_btn:
    # 1. ZULU Stage
    st.subheader("1️⃣ ZULU Scout: Scanning Market Signals...")
    zulu = ZuluScout()
    with st.spinner("Searching & Analyzing News..."):
        leads = zulu.search_leads(target_keyword)
    
    if not leads:
        st.error("No significant leads found.")
    else:
        # 탭 생성 (리드별로 보여주기)
        tabs = st.tabs([f"🏢 {lead['company_name']}" for lead in leads])
        
        for i, lead in enumerate(leads):
            with tabs[i]:
                col1, col2 = st.columns([1, 1])
                
                # 왼쪽: 시그널 정보
                with col1:
                    st.markdown("### 📡 Market Signal")
                    st.info(f"**Reason:** {lead['signal_reason']}")
                    st.write(f"**Source:** {lead['url']}")
                    st.markdown(f"**Strength:** {lead['signal_strength']}")

                # 2. X-RAY Stage
                xray = XrayValuation()
                with st.spinner("Running Financial X-RAY..."):
                    val_result = xray.run_valuation(lead)
                
                # 오른쪽: 밸류에이션 정보
                with col2:
                    st.markdown("### 💰 Valuation X-RAY")
                    st.metric("Est. Revenue", f"{val_result['financials']['revenue']} 억")
                    st.metric("Est. Value Range", 
                              f"{val_result['value_range_krw_bn'][0]} ~ {val_result['value_range_krw_bn'][1]} 억")
                    st.caption(f"Applied: {val_result['metric']} x{val_result['multiple_applied']}")

                st.divider()

                # 3. ALPHA Stage
                st.markdown("### 👑 ALPHA: Investment Teaser")
                alpha = AlphaChief()
                with st.spinner("Drafting 1-Page Teaser..."):
                    report = alpha.generate_teaser(lead, val_result)
                
                # 리포트 출력
                st.markdown(report)
                
                # 다운로드 버튼
                st.download_button(
                    label="📄 Download Teaser (Markdown)",
                    data=report,
                    file_name=f"Teaser_{lead['company_name']}.md",
                    mime="text/markdown"
                )