import streamlit as st
import time
import pandas as pd
from agents.zulu_scout import ZuluScout
from agents.xray_val import XrayValuation
from agents.bravo_matchmaker import BravoMatchmaker
from agents.alpha_chief import AlphaChief

st.set_page_config(page_title="Dunne's Deal OS", page_icon="💼", layout="wide")

# [Fix] 한글 잘림 방지 및 가독성 향상 CSS
st.markdown("""
<style>
    /* 텍스트 줄바꿈 강제 */
    .stMarkdown, .stText, p, div {
        word-wrap: break-word !important;
        white-space: pre-wrap !important; 
        font-family: "Malgun Gothic", "Apple SD Gothic Neo", sans-serif;
    }
    .metric-card {
        background-color: #1E1E1E;
        border: 1px solid #444;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .buyer-card {
        background-color: #262730;
        border-left: 5px solid #FF4B4B;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 10px;
        height: 100%; /* 카드 높이 맞춤 */
    }
    .si-tag { color: #4DA6FF; font-weight: bold; }
    .fi-tag { color: #52FF76; font-weight: bold; }
    .amc-tag { color: #D488FF; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# [Fix] 쿼리 고도화 (IB 전문 용어 결합)
THEMES = {
    "🏭 제조 & 뿌리산업": [
        '"가업승계" 포기 매물', 
        '"법정관리" 인가 전 M&A', 
        '"자동차 부품" 경영권 매각', 
        '"사모펀드" 보유 제조사 엑시트'
    ],
    "💄 소비재 & F&B": [
        '"건기식" 지분 매각 추진', 
        '"화장품" 브랜드 경영권 양도', 
        '"프랜차이즈" 직영점 매각', 
        '"푸드테크" 시리즈B 투자 유치 난항'
    ],
    "💻 Tech & SaaS": [
        '"플랫폼" 경영권 매각 티저', 
        '"스타트업" 폐업 후 자산 매각', 
        '"핀테크" 구조조정 매물', 
        '"SaaS" 기업 인수합병 제안'
    ],
    "🏦 NPL & 특수물건": [
        '"물류센터" 선매입 확약 부도', 
        '"PF 사업장" 공매 공고', 
        '"골프장" 회원제 대중화 매각', 
        '"데이터센터" 부지 급매'
    ]
}

def run_analysis(target_query):
    # 상태창 UI 개선
    status_container = st.status("🚀 Deal Process Initiated...", expanded=True)
    
    try:
        # 1. ZULU
        status_container.write(f"🕵️ ZULU: Scouting '{target_query}'...")
        zulu = ZuluScout()
        leads = zulu.search_leads(target_query)
        
        if not leads:
            status_container.update(label="No Leads Found", state="error")
            st.error("해당 쿼리로 유의미한 딜 시그널을 찾지 못했습니다. 쿼리를 변경해보세요.")
            return
        
        target = leads[0]
        st.session_state['target'] = target
        
        # 2. X-RAY
        status_container.write(f"⚡ X-RAY: Valuating '{target['company_name']}'...")
        xray = XrayValuation()
        val_result = xray.run_valuation(target)
        st.session_state['val_result'] = val_result
        
        # 3. BRAVO
        status_container.write(f"🤝 BRAVO: Matching Buyers...")
        bravo = BravoMatchmaker()
        industry = val_result['financials'].get('sector') or target.get('sector', 'General')
        buyer_list = bravo.find_potential_buyers(target, industry)
        st.session_state['buyer_list'] = buyer_list
        
        # 4. ALPHA
        status_container.write("👑 ALPHA: Drafting Strategy...")
        alpha = AlphaChief()
        teaser = alpha.generate_teaser(target, val_result, buyer_list)
        st.session_state['teaser'] = teaser
        
        status_container.update(label="All Process Complete!", state="complete", expanded=False)

    except Exception as e:
        status_container.update(label="System Error", state="error")
        st.error(f"오류 발생: {str(e)}")

# Sidebar & Main UI는 기존과 유사하되, 텍스트가 잘리지 않도록 레이아웃 유지
with st.sidebar:
    st.title("💼 Deal OS Pro")
    theme = st.selectbox("Industry Theme", list(THEMES.keys()))
    
    # Custom Query 지원
    use_custom = st.toggle("Custom Query 입력")
    if use_custom:
        query = st.text_input("직접 입력", placeholder='"SaaS" 경영권 매각')
    else:
        query = st.selectbox("Target Query", THEMES[theme])
    
    if st.button("Start Scan", type="primary"):
        run_analysis(query)

# 메인 화면 로직 (기존과 동일하되 CSS 적용됨)
if 'target' in st.session_state:
    # ... (기존 display 로직 유지)
    # Alpha 리포트 부분에서 markdown이 잘리지 않음
    st.title("Deal Flow Dashboard")
    # ...
    # (코드가 길어지므로 app.py의 나머지 UI 출력 부분은 기존 코드를 그대로 쓰셔도 CSS 덕분에 해결됩니다)
    
    # 아래는 예시용 짧은 렌더링 코드
    t = st.session_state['target']
    v = st.session_state['val_result']
    b = st.session_state['buyer_list']
    
    st.markdown(f"### 🎯 Target: {t['company_name']}")
    st.info(f"Signal: {t['signal_reason']}")
    st.divider()
    
    # Valuation
    fin = v['financials']
    val = v['valuation']
    c1, c2, c3 = st.columns(3)
    c1.metric("Revenue", f"{fin.get('revenue_bn', 0)}억")
    c2.metric("Op. Profit", f"{fin.get('profit_bn', 0)}억")
    c3.metric("Target Value", f"{val['target_value']}억")
    
    with st.expander("📝 Valuation Logic"):
        st.write(val.get('commentary', {}))
    st.divider()
    
    # Buyers
    st.markdown("### 🤝 Potential Buyers")
    if b:
        cols = st.columns(3)
        for i, buyer in enumerate(b):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="buyer-card">
                    <div class="big-font">{buyer['buyer_name']}</div>
                    <div class="{'si-tag' if buyer['type']=='SI' else 'fi-tag'}">{buyer['type']}</div>
                    <div style="font-size:13px; margin-top:5px;">{buyer['rationale']}</div>
                </div>
                """, unsafe_allow_html=True)
    st.divider()
    
    # Alpha Report
    st.markdown("### 📜 Strategy Note")
    st.markdown(st.session_state['teaser']) # CSS로 줄바꿈 자동 적용됨
else:
    st.info("좌측 사이드바에서 쿼리를 선택하고 스캔을 시작하세요.")