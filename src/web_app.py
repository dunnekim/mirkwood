import streamlit as st
import pandas as pd
from io import StringIO
import os
import sys

# [Path Setup] Deal OS 모듈 가져오기
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

# [Engine] WOOD Engine 연결 (가정)
try:
    from src.engines.wood.orchestrator import WoodOrchestrator
except ImportError:
    # 엔진이 없을 경우 Mock Class (테스트용)
    class WoodOrchestrator:
        def run_valuation(self, name, rev): return "mock_path.xlsx", "Valuation Done"

# ==============================================================================
# 🎨 UI Configuration
# ==============================================================================
st.set_page_config(
    page_title="MIRKWOOD Partners",
    page_icon="🌲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 🔒 Access Control (Mellon Gate)
# ==============================================================================
if 'auth' not in st.session_state:
    st.session_state.auth = False

def check_password():
    """
    Access Code: "mellon"
    
    [Security Note]
    For production, use st.secrets["ACCESS_CODE"] instead of hardcoded value.
    """
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("### 🌲 MIRKWOOD Partners")
        st.markdown("*Boutique Investment Bank AI*")
        st.divider()
        st.info("🔒 This application is restricted. Please enter access code.")
    
    with col2:
        st.markdown("")
        st.markdown("")
        st.markdown("")
        pwd = st.text_input("Access Code", type="password", key="access_code_input")
        
        if st.button("Enter", use_container_width=True):
            if pwd == "mellon":  # [Security] Access code
                st.session_state.auth = True
                st.success("✅ Access Granted")
                st.rerun()
            else:
                st.error("❌ Invalid Code")

if not st.session_state.auth:
    check_password()
    st.stop()

# ==============================================================================
# 🧠 Logic: Excel Parser
# ==============================================================================
def parse_pasted_data(raw_text):
    """
    엑셀에서 복사한 데이터(Tab으로 구분됨)를 DataFrame으로 변환
    """
    try:
        data = StringIO(raw_text)
        df = pd.read_csv(data, sep='\t')
        return df
    except Exception as e:
        return None

def save_feedback(msg):
    """피드백을 로컬 파일(또는 DB)에 저장"""
    with open("feedback_log.txt", "a", encoding="utf-8") as f:
        f.write(f"[{pd.Timestamp.now()}] {msg}\n")

# ==============================================================================
# 📱 Main Layout
# ==============================================================================
st.title("🌲 MIRKWOOD Deal OS")

# Tabs
tab1, tab2, tab3 = st.tabs(["📉 Quick Valuation", "🏗️ Structuring", "📝 Memo & Feedback"])

# --- Tab 1: Valuation (Excel Paste) ---
with tab1:
    st.header("Financial Projection & Valuation")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("1. Input Data")
        st.info("엑셀의 BS/PL 데이터를 드래그하여 복사(Ctrl+C) 후 아래에 붙여넣으세요.")
        
        project_name = st.text_input("Project Name (Anonymous)", "Project_Alpha")
        
        # [핵심] 엑셀 붙여넣기 창
        raw_data = st.text_area("Paste Excel Data Here:", height=300, placeholder="Year\tRevenue\tOP\t...\n2023\t100\t10\n2024\t120\t15")
        
        if st.button("🚀 Run WOOD Engine"):
            if raw_data:
                df = parse_pasted_data(raw_data)
                if df is not None:
                    st.session_state['input_df'] = df
                    st.success("Data Parsed Successfully!")
                    
                    # [Engine Call]
                    # 실제로는 df 데이터를 WOOD 엔진에 주입하는 로직 필요
                    # 여기서는 Base Revenue만 추출해서 호출한다고 가정
                    try:
                        base_rev = float(df.iloc[-1, 1]) # 마지막 행, 2번째 열을 매출로 가정
                    except:
                        base_rev = 100.0
                        
                    wood = WoodOrchestrator()
                    # path, summary = wood.run_valuation(project_name, base_rev)
                    # st.session_state['val_result'] = summary
                    
                    # (화면 표시용 Mock)
                    st.session_state['val_result'] = f"**{project_name}** Valuation Complete.\nEstimated Value: {base_rev * 2:.1f}억 (Mock)"
                else:
                    st.error("데이터 형식이 올바르지 않습니다. (Tab 구분 확인)")
            else:
                st.warning("데이터를 붙여넣어주세요.")

    with col2:
        st.subheader("2. Analysis Result")
        
        if 'input_df' in st.session_state:
            st.caption("Input Preview:")
            st.dataframe(st.session_state['input_df'], use_container_width=True)
            
        st.divider()
        
        if 'val_result' in st.session_state:
            st.markdown(st.session_state['val_result'])
            # 엑셀 다운로드 버튼 (Engine 결과 파일이 있다면)
            # with open("output/Project_Alpha_Valuation.xlsx", "rb") as f:
            #    st.download_button("📥 Download Excel Package", f, file_name="Valuation.xlsx")

# --- Tab 2: Structuring (Placeholder) ---
with tab2:
    st.header("Deal Structuring (Mezzanine)")
    st.write("Phase 4에서 구현될 CB/BW 시뮬레이션 화면입니다.")

# --- Tab 3: Feedback (Async Work) ---
with tab3:
    st.header("📝 Feedback & Notes")
    st.write("업무 중 떠오른 아이디어나 버그를 기록하세요. (집에서 확인용)")
    
    feedback = st.text_area("Log your thoughts:", height=150)
    if st.button("Save Log"):
        if feedback:
            save_feedback(feedback)
            st.toast("피드백이 저장되었습니다! 🏠 집에서 확인하세요.")