"""
MIRKWOOD Deal OS - Streamlit Web Interface

[Features]
1. Access Control (mellon gate)
2. Historical Data Upload & Parsing
3. Driver-based Projection
4. DCF Valuation with Excel Export (formulas included)
5. Calculation transparency (show WACC, discount factors)
"""

import streamlit as st
import pandas as pd
import numpy as np
from io import StringIO, BytesIO
import os
import sys
from datetime import datetime
import tempfile
from typing import Optional, Dict, Any
import re
import zipfile

# Path Setup
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

# Import MIRKWOOD components (prefer V2, fallback to V1)
# NOTE: We keep V1 as fallback for compatibility, but default UI uses V2/V3.
WoodOrchestrator = None
WoodOrchestratorV2 = None
try:
    from src.engines.wood.orchestrator_v2 import WoodOrchestratorV2  # WOOD V2 (preferred)
except Exception:
    WoodOrchestratorV2 = None

try:
    from src.engines.orchestrator import WoodOrchestrator  # WOOD V1 (fallback)
except Exception:
    WoodOrchestrator = None

if WoodOrchestratorV2 is None and WoodOrchestrator is None:
    st.error("⚠️ WOOD engine import failed: neither `WoodOrchestratorV2` nor `WoodOrchestrator` is available.")
    st.stop()

# Check API keys before importing SmartIngestor
def _normalize_env_keys():
    """
    Normalize env var naming across modules.

    - Some modules expect DART_API_KEY
    - Some environments store OPENDART_API_KEY

    If OPENDART_API_KEY exists but DART_API_KEY doesn't, mirror it.
    """
    if not os.getenv("DART_API_KEY") and os.getenv("OPENDART_API_KEY"):
        os.environ["DART_API_KEY"] = os.getenv("OPENDART_API_KEY")  # pragma: no cover


def check_api_keys(require_openai: bool = True, require_dart: bool = True):
    """Check if required API keys are set (supports DART/OPENDART aliasing)."""
    _normalize_env_keys()

    missing_keys = []

    if require_openai and not os.getenv("OPENAI_API_KEY"):
        missing_keys.append("OPENAI_API_KEY")

    if require_dart and not (os.getenv("DART_API_KEY") or os.getenv("OPENDART_API_KEY")):
        missing_keys.append("DART_API_KEY (or OPENDART_API_KEY)")

    return missing_keys

# Lazy import function for SmartIngestor
def get_smart_ingestor():
    """Lazy load SmartIngestor only when needed"""
    try:
        from src.tools.smart_ingestor import SmartFinancialIngestor
        return SmartFinancialIngestor()
    except Exception as e:
        st.error(f"Failed to initialize SmartIngestor: {e}")
        st.info("Please set OPENAI_API_KEY and DART_API_KEY in Streamlit secrets")
        return None


@st.cache_resource(show_spinner=False)
def get_wood_orchestrator(use_live_beta: bool = True):
    """Cached WOOD orchestrator instance (V2 preferred)."""
    if WoodOrchestratorV2 is not None:
        return WoodOrchestratorV2(use_live_beta=use_live_beta)
    # Fallback to V1
    return WoodOrchestrator()


def get_dart_analyst():
    """Lazy load DartAnalyst (LTM-capable)."""
    _normalize_env_keys()
    try:
        from src.tools.dart_analyst import DartAnalyst
        return DartAnalyst()
    except Exception as e:
        st.error(f"Failed to initialize DartAnalyst: {e}")
        return None


def get_zulu_scout():
    """Lazy load ZuluScout (entity resolution)."""
    try:
        from src.agents.zulu_scout import ZuluScout
        return ZuluScout()
    except Exception as e:
        st.error(f"Failed to initialize ZuluScout: {e}")
        return None


@st.cache_data(show_spinner=False, ttl=5)
def _read_text_tail(path: str, max_chars: int = 8000) -> str:
    """Read tail of a text file safely (cached)."""
    if not path or not os.path.exists(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return content[-max_chars:] if len(content) > max_chars else content
    except Exception:
        return ""


def _extract_dcf_info_from_wood_v2_summary(summary_text: str) -> Dict[str, Any]:
    """
    Best-effort parse of WOOD V2 summary text to provide ALPHA-compatible dcf_info.

    Expected patterns (from `WoodOrchestratorV2._generate_summary_text`):
    - Enterprise Value Range: <min>~<max>억 원
    - (Base Case: <base>억)
    - [Base] EV: <ev>억 (WACC <wacc>%)

    Returns dict with keys used by `AlphaVP._synthesize_valuation_football_field`:
    - ev_min, ev_max, ev_base, wacc
    """
    txt = summary_text or ""
    info: Dict[str, Any] = {}

    # EV range
    m = re.search(r"Enterprise Value Range:\s*([0-9,.]+)\s*~\s*([0-9,.]+)\s*억", txt)
    if m:
        try:
            info["ev_min"] = float(m.group(1).replace(",", ""))
            info["ev_max"] = float(m.group(2).replace(",", ""))
        except Exception:
            pass

    # Base case EV (parenthesis line)
    m = re.search(r"\(Base Case:\s*([0-9,.]+)\s*억\)", txt)
    if m:
        try:
            info["ev_base"] = float(m.group(1).replace(",", ""))
        except Exception:
            pass

    # Base scenario WACC (best effort: try Base, else first scenario line)
    m = re.search(r"\*\*\[Base\]\*\*\s*EV:\s*\*\*([0-9,.]+)억\*\*\s*\(WACC\s*([0-9.]+)%\)", txt)
    if not m:
        m = re.search(r"\*\*\[[^\]]+\]\*\*\s*EV:\s*\*\*([0-9,.]+)억\*\*\s*\(WACC\s*([0-9.]+)%\)", txt)
    if m:
        try:
            if "ev_base" not in info:
                info["ev_base"] = float(m.group(1).replace(",", ""))
            info["wacc"] = float(m.group(2))
        except Exception:
            pass

    return info


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default

# ==============================================================================
# 🔒 ACCESS CONTROL (Mellon Gate)
# ==============================================================================

st.set_page_config(
    page_title="MIRKWOOD Partners",
    page_icon="🌲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Access control
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("### 🌲 MIRKWOOD Partners")
    st.markdown("*Boutique Investment Bank AI*")
    st.divider()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.info("🔒 This application is restricted. Please enter access code.")
        
        access_code = st.text_input(
            "Access Code",
            type="password",
            key="access_code",
            help="Hint: Speak friend and enter"
        )
        
        if st.button("Enter", use_container_width=True):
            if access_code == "mellon":
                st.session_state.authenticated = True
                st.success("✅ Access Granted")
                st.rerun()
            else:
                st.error("❌ Invalid Access Code")
    
    st.stop()

# ==============================================================================
# 🎨 MAIN UI (After Authentication)
# ==============================================================================

# Sidebar: Config
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    
    # Project Settings
    project_name = st.text_input(
        "Project Name",
        value="Project_Alpha",
        help="Codename for this deal"
    )
    
    st.divider()
    
    st.markdown("**🧩 Engine Settings**")
    use_live_beta = st.toggle("Use Live Beta (MarketScanner)", value=True, help="If yfinance is unavailable, engine will degrade gracefully.")

    with st.expander("🩺 System Health", expanded=False):
        missing = check_api_keys(require_openai=False, require_dart=False)
        st.caption("Environment")
        st.write(f"- OPENAI_API_KEY: {'✅' if os.getenv('OPENAI_API_KEY') else '❌'}")
        st.write(f"- DART_API_KEY/OPENDART_API_KEY: {'✅' if (os.getenv('DART_API_KEY') or os.getenv('OPENDART_API_KEY')) else '❌'}")
        st.write(f"- WOOD V2 Available: {'✅' if WoodOrchestratorV2 is not None else '❌'}")
        st.write(f"- WOOD V1 Available: {'✅' if WoodOrchestrator is not None else '❌'}")
        if missing:
            st.warning(f"Missing (optional for some tabs): {', '.join(missing)}")

    # Projection Settings
    st.markdown("**📊 Projection Settings**")
    
    projection_years = st.number_input(
        "Projection Years",
        min_value=3,
        max_value=10,
        value=5,
        help="Number of years to project"
    )
    
    terminal_growth = st.number_input(
        "Terminal Growth Rate (%)",
        min_value=0.0,
        max_value=5.0,
        value=1.5,
        step=0.1,
        help="Perpetual growth rate"
    )
    
    st.divider()
    
    # Quick Actions
    st.markdown("**🔧 Quick Actions**")
    
    if st.button("🔄 Reset Session", use_container_width=True):
        for key in list(st.session_state.keys()):
            if key != 'authenticated':
                del st.session_state[key]
        st.rerun()
    
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

# ==============================================================================
# MAIN CONTENT
# ==============================================================================

tab1 = tab2 = tab3 = tab4 = tab5 = tab6 = None  # predeclare for linters

st.title("🌲 MIRKWOOD Deal OS")
st.markdown("**Enterprise Valuation & Transaction Services Platform**")

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Data Collection",
    "📈 DCF Valuation",
    "🏗️ OPM Structuring",
    "🌲 Transaction Services",
    "📝 Notes",
    "🚀 Deal Pipeline (/run)"
])

# ==============================================================================
# TAB 1: DATA COLLECTION
# ==============================================================================

with tab1:
    st.header("📊 Data Collection")
    st.markdown("Collect target company financial data from multiple sources.")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🔍 Automated Search")
        
        company_name = st.text_input(
            "Company Name",
            placeholder="e.g., 삼성전자, 네이버",
            help="Exact legal name for best results"
        )
        
        if st.button("🔎 Search Data", use_container_width=True):
            if company_name:
                # Check API keys first
                missing_keys = check_api_keys()
                
                if missing_keys:
                    st.error(f"❌ Missing API Keys: {', '.join(missing_keys)}")
                    st.info("""
                    **To fix this:**
                    1. Go to Streamlit Cloud dashboard
                    2. Click 'Manage app'
                    3. Go to 'Secrets' section
                    4. Add:
                    ```
                    OPENAI_API_KEY = "your_key"
                    DART_API_KEY = "your_key"
                    ```
                    """)
                    st.stop()
                
                with st.spinner("Searching DART and Web..."):
                    ingestor = get_smart_ingestor()
                    
                    if ingestor is None:
                        st.error("Failed to initialize data collector")
                        st.stop()
                    
                    result = ingestor.ingest(company_name)
                    
                    st.session_state['collected_data'] = result
                    st.session_state['company_name'] = company_name
                
                st.rerun()
            else:
                st.warning("Please enter company name")
    
    with col2:
        st.subheader("📝 Manual Override")
        
        manual_revenue = st.number_input(
            "Revenue (억 원)",
            min_value=0.0,
            value=0.0,
            step=10.0,
            help="Manual revenue input"
        )
        
        manual_op = st.number_input(
            "Operating Profit (억 원)",
            value=0.0,
            step=1.0,
            help="Manual OP input"
        )
        
        if st.button("💾 Use Manual Data", use_container_width=True):
            if manual_revenue > 0:
                st.session_state['collected_data'] = {
                    'revenue': manual_revenue,
                    'op': manual_op,
                    'ebitda': manual_op * 1.15,
                    'source': 'User Input (Manual Override)',
                    'description': f'Manually provided: Rev {manual_revenue}bn, OP {manual_op}bn',
                    'confidence': 'User-Provided',
                    'requires_input': False
                }
                st.session_state['company_name'] = project_name
                st.success("✅ Manual data saved")
            else:
                st.warning("Revenue must be > 0")
    
    # Display collected data
    if 'collected_data' in st.session_state:
        st.divider()
        
        data = st.session_state['collected_data']
        
        # Confidence indicator
        confidence = data.get('confidence', 'Unknown')
        confidence_colors = {
            'High': '🟢',
            'Medium': '🟡',
            'User-Provided': '🔵',
            'Unknown': '⚪'
        }
        emoji = confidence_colors.get(confidence, '⚪')
        
        st.success(f"### {emoji} Data Collected")
        
        col1, col2, col3 = st.columns(3)
        
        # Handle None values safely
        revenue = data.get('revenue') or 0
        op = data.get('op') or 0
        
        with col1:
            st.metric("Revenue", f"{float(revenue):.1f}억 원")
        
        with col2:
            st.metric("Operating Profit", f"{float(op):.1f}억 원")
        
        with col3:
            margin = (float(op) / float(revenue)) * 100 if float(revenue) > 0 else 0
            st.metric("OP Margin", f"{margin:.1f}%")
        
        st.info(f"""
        **📊 Data Source:** {data.get('source', 'Unknown')}  
        **📝 Description:** {data.get('description', 'N/A')}  
        **✅ Confidence:** {confidence}
        """)

        # ------------------------------------------------------------------
        # 🩻 X-RAY (LTM) Card: ZuluScout.resolve_entity → DartAnalyst.get_ltm_financials
        # ------------------------------------------------------------------
        st.markdown("---")
        st.subheader("🩻 X-RAY Financials (LTM)")
        st.caption("ZuluScout로 엔티티를 정규화한 뒤, DartAnalyst로 LTM(최근 12개월) 기준 수익력을 산출합니다.")

        ltm_target = st.text_input(
            "X-RAY Target (for LTM)",
            value=st.session_state.get("company_name", ""),
            placeholder="e.g., Target_Co",
            help="가능하면 공식 법인명 입력 (ZuluScout가 보정).",
            key="xray_ltm_target"
        )

        col_a, col_b, col_c = st.columns([1, 1, 1])
        with col_a:
            unit_mode = st.selectbox(
                "Display Unit",
                options=["십억 원", "억 원"],
                index=0,
                help="DartAnalyst 내부 값은 억 원 기반입니다. 표시 단위만 변환합니다.",
                key="xray_ltm_unit"
            )

        with col_b:
            manual_corp_code = st.text_input(
                "Corp Code (Optional)",
                value="",
                placeholder="8-digit corp code",
                help="ZuluScout가 DART 코드를 못 찾을 때만 입력하세요.",
                key="xray_ltm_corp_code"
            )

        with col_c:
            run_ltm = st.button("🧾 Run X-RAY (LTM)", use_container_width=True)

        def _fmt_money(v_uk: float) -> str:
            # v_uk: 억 원
            try:
                v = float(v_uk or 0)
            except Exception:
                v = 0.0
            if unit_mode == "십억 원":
                return f"{(v/10.0):,.1f}"
            return f"{v:,.1f}"

        if run_ltm:
            if not ltm_target and not manual_corp_code:
                st.warning("회사명 또는 Corp Code 중 하나는 입력되어야 합니다.")
            else:
                missing = check_api_keys(require_openai=True, require_dart=True)
                if missing and not manual_corp_code:
                    st.error(f"❌ Missing API Keys: {', '.join(missing)}")
                    st.info("ZuluScout(DART 코드 탐색) 및 DART 조회에는 키가 필요합니다. Corp Code를 직접 넣으면 일부 과정을 우회할 수 있습니다.")
                else:
                    with st.spinner("Running X-RAY LTM..."):
                        try:
                            zulu = get_zulu_scout()
                            analyst = get_dart_analyst()

                            corp_code = manual_corp_code.strip() if manual_corp_code else None
                            entity_info = None

                            if not corp_code:
                                if not zulu:
                                    st.error("ZuluScout 초기화 실패")
                                    st.stop()
                                entity_info = zulu.resolve_entity(ltm_target.strip())
                                corp_code = entity_info.get("dart_code")

                            if not corp_code:
                                st.error("DART Corp Code를 찾지 못했습니다. (Corp Code를 직접 입력해 주세요)")
                                st.stop()

                            if not analyst:
                                st.error("DartAnalyst 초기화 실패")
                                st.stop()

                            fin = analyst.get_ltm_financials(corp_code)
                            if not fin:
                                st.error("LTM 재무 데이터 수집에 실패했습니다. (DART 응답/기간 이슈 가능)")
                                st.stop()

                            st.session_state["xray_ltm"] = {
                                "entity": entity_info,
                                "corp_code": corp_code,
                                "financials": fin,
                                "timestamp": datetime.now().isoformat(),
                            }
                            st.success("✅ X-RAY LTM 완료")
                            st.rerun()

                        except Exception as e:
                            import traceback
                            st.session_state["last_error"] = traceback.format_exc()
                            st.error(f"❌ X-RAY LTM Error: {e}")
                            with st.expander("🔍 Error Details"):
                                st.code(st.session_state["last_error"])

        if "xray_ltm" in st.session_state:
            fin = st.session_state["xray_ltm"]["financials"]
            entity = st.session_state["xray_ltm"].get("entity") or {}

            st.markdown("#### [Financial Analysis (LTM Basis)]")
            st.caption(f"Period: {fin.get('period', 'N/A')} | Method: {fin.get('ltm_method', 'N/A')} | FS: {fin.get('fs_type', 'N/A')}")

            revenue = fin.get("revenue_bn", 0) or 0
            ebitda = fin.get("ebitda_bn", 0) or 0
            op_bn = fin.get("op_bn", 0) or 0
            ni = fin.get("net_income_bn", 0) or 0

            roe = fin.get("roe", 0) or 0
            debt_ratio = fin.get("debt_ratio", 0) or 0
            ebitda_margin = fin.get("ebitda_margin", 0) or 0

            table_rows = [
                {"Item": "Revenue", "Value": _fmt_money(revenue), "Note": unit_mode},
                {"Item": "EBITDA", "Value": _fmt_money(ebitda), "Note": f"Margin {ebitda_margin:.1f}% {fin.get('ebitda_method', '')}".strip()},
                {"Item": "Op. Profit", "Value": _fmt_money(op_bn), "Note": "LTM"},
                {"Item": "Net Income", "Value": _fmt_money(ni), "Note": "LTM"},
                {"Item": "ROE", "Value": f"{roe:.1f}%", "Note": "LTM basis (simplified)"},
                {"Item": "Debt Ratio", "Value": f"{debt_ratio:.1f}%", "Note": "Liabilities / Equity"},
            ]

            st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

            with st.expander("🔎 Entity Resolution Details"):
                st.json({
                    "query": entity.get("query"),
                    "official_name": entity.get("official_name"),
                    "dart_code": entity.get("dart_code"),
                    "stock_code": entity.get("stock_code"),
                    "is_listed": entity.get("is_listed"),
                    "confidence": entity.get("confidence"),
                    "dart_name": entity.get("dart_name"),
                })
        
        # Historical data upload (optional)
        st.markdown("---")
        st.markdown("#### 📂 Upload Historical Data (Optional)")
        st.markdown("Upload Excel with historical P&L for more accurate projections")
        
        uploaded_file = st.file_uploader(
            "Upload Excel/CSV",
            type=['xlsx', 'csv'],
            help="Format: Columns = Years, Rows = Accounts"
        )
        
        if uploaded_file:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_hist = pd.read_csv(uploaded_file)
                else:
                    df_hist = pd.read_excel(uploaded_file)
                
                st.session_state['historical_data'] = df_hist
                st.success(f"✅ Loaded {len(df_hist)} rows × {len(df_hist.columns)} columns")
                st.dataframe(df_hist.head(10), use_container_width=True)
            except Exception as e:
                st.error(f"❌ Failed to parse file: {e}")

# ==============================================================================
# TAB 2: DCF VALUATION
# ==============================================================================

with tab2:
    st.header("📈 DCF Valuation")
    
    if 'collected_data' not in st.session_state:
        st.warning("⚠️ Please collect data in Tab 1 first")
    else:
        data = st.session_state['collected_data']
        company = st.session_state.get('company_name', 'Unknown')

        # Robust numeric parsing (Streamlit Cloud-safe)
        def _as_float(x, default=0.0):
            try:
                if x is None:
                    return default
                if isinstance(x, str):
                    x = x.replace(",", "").strip()
                return float(x)
            except Exception:
                return default

        base_rev = _as_float(data.get("revenue"))
        base_source = data.get("source", "Unknown")
        
        st.markdown(f"### Target: **{company}**")
        st.markdown(f"**Base Revenue:** {base_rev:.1f}억 원 (Source: {base_source})")
        
        st.divider()
        
        # Scenario Configuration
        st.subheader("🎯 Scenario Configuration")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Base Case**")
            base_growth = st.number_input("Revenue Growth (%)", value=10.0, key="base_growth") / 100
            base_margin = st.number_input("EBIT Margin (%)", value=15.0, key="base_margin") / 100
        
        with col2:
            st.markdown("**Bull Case**")
            bull_growth = st.number_input("Revenue Growth (%)", value=15.0, key="bull_growth") / 100
            bull_margin = st.number_input("EBIT Margin (%)", value=20.0, key="bull_margin") / 100
        
        with col3:
            st.markdown("**Bear Case**")
            bear_growth = st.number_input("Revenue Growth (%)", value=5.0, key="bear_growth") / 100
            bear_margin = st.number_input("EBIT Margin (%)", value=8.0, key="bear_margin") / 100
        
        st.divider()
        
        # Run DCF
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("🚀 Run DCF (WOOD V2)", use_container_width=True, type="primary"):
                with st.spinner("Running WOOD V2 (Nexflex Std.)..."):
                    try:
                        orchestrator = get_wood_orchestrator(use_live_beta=use_live_beta)

                        filepath, summary = orchestrator.run_valuation(
                            project_name=company,
                            base_revenue=float(data.get('revenue') or 0),
                            data_source=str(data.get('source') or "User Input")
                        )

                        st.session_state['dcf_result'] = {
                            'filepath': filepath,
                            'summary': summary,
                            'timestamp': datetime.now().isoformat(),
                            'engine': 'WOOD_V2',
                            'project_name': company,
                            'dcf_info': _extract_dcf_info_from_wood_v2_summary(summary),
                        }

                        st.success("✅ DCF Valuation Completed (WOOD V2)")
                        st.rerun()

                    except Exception as e:
                        import traceback
                        st.session_state["last_error"] = traceback.format_exc()
                        st.error(f"❌ DCF Error: {e}")
                        with st.expander("🔍 Error Details"):
                            st.code(st.session_state["last_error"])

        with c2:
            if st.button("📊 Build Live Excel (WOOD V3)", use_container_width=True):
                with st.spinner("Building WOOD V3 Live (Formula-Linked) model..."):
                    try:
                        from src.engines.wood.exporter_v3 import LiveExcelBuilder

                        assumptions = {
                            "tax_rate": 0.22,
                            "terminal_growth": float(terminal_growth) / 100.0,
                            "projection_years": int(projection_years),
                            # WACC inputs (fallback defaults; can be edited in Excel)
                            "risk_free_rate": 0.035,
                            "market_risk_premium": 0.08,
                            "beta": 1.0,
                            "cost_of_debt": 0.045,
                        }

                        scenarios = {
                            "Base": {"revenue_growth": float(base_growth), "ebit_margin": float(base_margin)},
                            "Bull": {"revenue_growth": float(bull_growth), "ebit_margin": float(bull_margin)},
                            "Bear": {"revenue_growth": float(bear_growth), "ebit_margin": float(bear_margin)},
                        }

                        # Optional historical_data from upload (best-effort)
                        historical_data = None
                        if 'historical_data' in st.session_state:
                            try:
                                df_hist = st.session_state['historical_data']
                                # Accept either dict-like already or attempt minimal conversion
                                if isinstance(df_hist, pd.DataFrame):
                                    # Heuristic: if it has 'Account' column and year columns
                                    historical_data = {"raw": df_hist.to_dict(orient="list")}
                            except Exception:
                                historical_data = None

                        # Build temp file and read bytes for download
                        reports_dir = os.path.join(project_root, 'vault', 'reports')
                        os.makedirs(reports_dir, exist_ok=True)
                        filename = f"{company}_DCF_WOOD_V3_LIVE_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                        filepath = os.path.join(reports_dir, filename)

                        builder = LiveExcelBuilder(filepath)
                        builder.build(
                            project_name=company,
                            base_revenue=float(data.get('revenue') or 0),
                            assumptions=assumptions,
                            scenarios=scenarios,
                            historical_data=historical_data
                        )

                        with open(filepath, "rb") as f:
                            excel_bytes = f.read()

                        st.session_state['dcf_v3_live'] = {
                            "filepath": filepath,
                            "filename": filename,
                            "bytes": excel_bytes,
                            "timestamp": datetime.now().isoformat(),
                            "engine": "WOOD_V3_LIVE",
                            "project_name": company,
                        }

                        st.success("✅ Live Excel model built (WOOD V3)")
                        st.rerun()

                    except Exception as e:
                        import traceback
                        st.session_state["last_error"] = traceback.format_exc()
                        st.error(f"❌ WOOD V3 Build Error: {e}")
                        with st.expander("🔍 Error Details"):
                            st.code(st.session_state["last_error"])
        
        # Display results
        if 'dcf_result' in st.session_state:
            result = st.session_state['dcf_result']
            
            st.divider()
            st.markdown("### 📊 Valuation Results")
            
            # Summary in nice cards
            col1, col2, col3 = st.columns(3)
            
            # Parse summary for values (quick hack)
            summary_text = result['summary']
            
            with col1:
                st.metric("Data Source", data.get('source', 'Unknown'))
            
            with col2:
                st.metric("Base Revenue", f"{_as_float(data.get('revenue')):.1f}억")
            
            with col3:
                rev = _as_float(data.get("revenue"))
                op = _as_float(data.get("op"))
                st.metric("OP Margin", f"{(op/rev*100):.1f}%" if rev > 0 else "N/A")
            
            st.markdown("---")
            
            # Full summary
            st.markdown(result['summary'])
            
            st.divider()
            
            # Download Section
            st.markdown("### 📥 Download Excel Package")
            
            if os.path.exists(result['filepath']):
                # Excel download
                with open(result['filepath'], 'rb') as f:
                    excel_data = f.read()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.download_button(
                        label="📊 Download DCF Model (Big 4 Style)",
                        data=excel_data,
                        file_name=os.path.basename(result['filepath']),
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
                with col2:
                    # Also allow downloading summary as PDF/MD
                    st.download_button(
                        label="📄 Download Summary (Markdown)",
                        data=result['summary'],
                        file_name=f"{company}_Summary.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
                
                st.success("""
                **✅ Excel Features:**
                - 🔵 Blue font = Input values (Assumptions)
                - ⚫ Black font = Calculated values (Formulas)
                - 📊 Data source in top-right corner
                - 📈 Sensitivity analysis table (WACC × Growth)
                - 🎨 Professional Big 4 formatting
                - 📐 Borders and thousand separators
                """)

        # WOOD V3 Live download (separate from V2 run)
        if 'dcf_v3_live' in st.session_state:
            live = st.session_state['dcf_v3_live']
            st.divider()
            st.markdown("### 🧮 WOOD V3 Live Model (Formula-Linked)")
            st.caption("Assumptions are editable in Excel; valuation updates automatically via formulas.")
            st.download_button(
                label="📥 Download Live Excel (WOOD V3)",
                data=live["bytes"],
                file_name=live["filename"],
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
            st.markdown("---")
            
            # Detailed calculation breakdown
            with st.expander("🔍 Detailed Calculation Breakdown"):
                
                # Load config for actual values
                import json
                config_path = os.path.join(os.path.dirname(__file__), 'engines', 'wood', 'config.json')
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                    
                    settings = config['project_settings']
                    peer_group = config['peer_group']
                    
                    st.markdown("### 1️⃣ WACC Calculation (Step-by-Step)")
                    
                    st.code(f"""
Risk-Free Rate (Rf):    {settings['risk_free_rate']*100:.2f}%
Market Risk Premium:    {settings['market_risk_premium']*100:.2f}%
Tax Rate:               {settings['tax_rate']*100:.1f}%

Peer Group:
{chr(10).join([f"  - {p['name']}: Beta {p['beta']}, D/E {p['debt_equity_ratio']}" for p in peer_group])}

Step 1: Unlever peer betas
  βu = βL / [1 + (1-Tax) × (D/E)]

Step 2: Average unlevered beta
  Avg βu ≈ {np.mean([p['beta'] for p in peer_group]):.2f}

Step 3: Re-lever to target structure (D/E = {np.mean([p['debt_equity_ratio'] for p in peer_group]):.2f})
  βL = βu × [1 + (1-Tax) × (D/E)]

Step 4: CAPM
  Re = Rf + βL × MRP
  Re ≈ {settings['risk_free_rate']*100:.2f}% + β × {settings['market_risk_premium']*100:.2f}%

Step 5: WACC
  WACC = Re × (E/V) + Rd × (1-Tax) × (D/V)
  WACC ≈ 8-9% (depends on scenario)
                    """, language="text")
                    
                except:
                    st.info("Config file not available")
                
                st.markdown("### 2️⃣ FCF Waterfall")
                
                st.code("""
Year 1 Example (Base Case):

Revenue                 1,000억
× EBIT Margin (15%)
= EBIT                    150억
× (1 - Tax 22%)
= NOPAT                   117억
+ D&A (3% of Rev)         +30억
- Capex (3% of Rev)       -30억
- Δ NWC (5% of Δ Rev)     -5억
= Free Cash Flow          112억

Discount Factor (WACC 8.5%, Year 1):
  PV Factor = 1 / (1.085)^1 = 0.922

PV(FCF) = 112억 × 0.922 = 103억
                """, language="text")
                
                st.markdown("### 3️⃣ Terminal Value")
                
                st.code("""
Gordon Growth Method (Primary):

Last Year FCF (Year 5):  150억
Terminal Growth:         1.5%
WACC:                    8.5%

TV = FCF × (1 + g) / (WACC - g)
   = 150억 × 1.015 / (0.085 - 0.015)
   = 2,175억

PV(TV) = 2,175억 × Discount Factor(Year 5)
       = 2,175억 × 0.665
       = 1,446억
                """, language="text")
                
                st.markdown("### 4️⃣ Enterprise Value")
                
                st.code("""
Sum of PV(FCF Years 1-5):     450억
+ PV(Terminal Value):       1,446억
= Enterprise Value:         1,896억

Sanity Check:
  Implied EV/Revenue (Year 1): 1.9x
  Implied EV/EBITDA (Year 1): 12.6x
                """, language="text")
                
                st.markdown("### 5️⃣ Historical vs Projection")
                
                # Show historical data if available
                if 'historical_data' in st.session_state:
                    st.markdown("**📊 Historical Data:**")
                    st.dataframe(st.session_state['historical_data'].head(), use_container_width=True)
                    st.markdown("**→ Used for:** Cost ratio calculation, growth trend analysis")
                else:
                    st.info("No historical data uploaded. Using default assumptions.")
                
                st.markdown("**📈 Projection Data:**")
                st.markdown("Generated using scenario assumptions (Base/Bull/Bear)")

# ==============================================================================
# TAB 3: OPM STRUCTURING
# ==============================================================================

with tab3:
    st.header("🏗️ OPM Structuring Engine")
    st.markdown("*Hybrid Securities Valuation (RCPS, CB, CPS)*")
    
    from src.engines.wood.opm_engine import OPMCalculator, IPOScenario
    from datetime import timedelta
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📋 Security Terms")
        
        company_opm = st.text_input(
            "Company Name",
            value=st.session_state.get('company_name', project_name),
            key="opm_company"
        )
        
        security_type = st.selectbox(
            "Security Type",
            options=["RCPS", "CB", "CPS"],
            help="Redeemable Convertible Preferred Stock / Convertible Bond / Convertible Preferred Stock"
        )
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            stock_price_opm = st.number_input(
                "Current Stock Price (S0)",
                min_value=0.0,
                value=20000.0,
                step=1000.0,
                help="Current market price"
            )
        
        with col_b:
            conversion_price = st.number_input(
                "Conversion Price (CP)",
                min_value=0.0,
                value=25000.0,
                step=1000.0,
                help="Initial conversion price"
            )
        
        col_c, col_d = st.columns(2)
        
        with col_c:
            face_value = st.number_input(
                "Face Value per Share",
                min_value=0.0,
                value=50000.0,
                step=5000.0
            )
        
        with col_d:
            num_shares_opm = st.number_input(
                "Number of Shares",
                min_value=0.0,
                value=10000.0,
                step=1000.0
            )
        
        years_to_mat = st.number_input(
            "Years to Maturity",
            min_value=0.5,
            max_value=10.0,
            value=3.0,
            step=0.5
        )
        
        volatility_opm = st.number_input(
            "Volatility (%)",
            min_value=0.0,
            max_value=100.0,
            value=35.0,
            step=5.0,
            help="Annualized stock volatility"
        ) / 100
        
        st.divider()
        
        st.markdown("**🎯 IPO Scenario (Optional)**")
        
        enable_ipo = st.checkbox("Enable IPO Refixing Scenario", value=False)
        
        if enable_ipo:
            ipo_date = st.date_input(
                "IPO Check Date",
                value=datetime.now() + timedelta(days=180)
            )
            
            ipo_threshold = st.number_input(
                "Threshold Price",
                value=28000.0,
                step=1000.0,
                help="If stock price < threshold, refixing triggers"
            )
            
            ipo_ratio = st.number_input(
                "Failure Refix Ratio",
                min_value=0.0,
                max_value=1.0,
                value=0.70,
                step=0.05,
                help="New CP = Old CP × Ratio"
            )
    
    with col2:
        st.subheader("📊 Valuation Results")
        
        if st.button("🚀 Run OPM Valuation", use_container_width=True, type="primary"):
            with st.spinner("Running TF Model..."):
                try:
                    calculator = OPMCalculator()
                    
                    # Build IPO scenario if enabled
                    ipo_scenario_dict = None
                    if enable_ipo:
                        ipo_scenario_dict = {
                            'check_date': datetime.combine(ipo_date, datetime.min.time()),
                            'threshold': ipo_threshold,
                            'ratio': ipo_ratio
                        }
                    
                    # Run valuation
                    result = calculator.quick_rcps_valuation(
                        company_name=company_opm,
                        stock_price=stock_price_opm,
                        conversion_price=conversion_price,
                        face_value=face_value,
                        num_shares=num_shares_opm,
                        years_to_maturity=years_to_mat,
                        volatility=volatility_opm,
                        ipo_scenario=ipo_scenario_dict
                    )
                    
                    st.session_state['opm_result'] = result
                    st.success("✅ OPM Valuation Complete!")
                    st.rerun()
                
                except Exception as e:
                    import traceback
                    st.session_state["last_error"] = traceback.format_exc()
                    st.error(f"❌ OPM Error: {e}")
                    with st.expander("Error Details"):
                        st.code(st.session_state["last_error"])
        
        # Display results
        if 'opm_result' in st.session_state:
            result = st.session_state['opm_result']
            
            st.markdown("### 💰 Fair Value")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Total Value",
                    f"{result['total_value']:,.0f}원",
                    help="Total fair value (TF Model)"
                )
            
            with col2:
                st.metric(
                    "Host (Debt)",
                    f"{result['debt_component']:,.0f}원",
                    delta=f"{result['debt_component']/result['total_value']*100:.1f}%"
                )
            
            with col3:
                st.metric(
                    "Option (Equity)",
                    f"{result['equity_component']:,.0f}원",
                    delta=f"{result['equity_component']/result['total_value']*100:.1f}%"
                )
            
            st.divider()
            
            # TF Model Explanation
            with st.expander("🔍 TF Model Breakdown"):
                params = result['parameters']
                
                st.markdown(f"""
                **Tsiveriotis-Fernandes Model:**
                
                ```
                V = D + E
                
                Where:
                - D (Debt Component) = Σ PV(Debt CF) at Risky Rate
                - E (Equity Component) = Σ PV(Equity CF) at Risk-Free Rate
                ```
                
                **Parameters:**
                - Stock Price (S0): {params['S0']:,.0f}원
                - Conversion Price (K): {params['K_init']:,.0f}원
                - Volatility (σ): {params['vol']*100:.1f}%
                - Risk-Free Rate: {params['rf']*100:.2f}%
                - Credit Spread: {params['cs']*100:.2f}%
                - **Risky Rate:** {(params['rf']+params['cs'])*100:.2f}%
                
                **Discount Factors (per step):**
                - df_risky = {params['df_risky']:.6f} (for Debt)
                - df_rf = {params['df_rf']:.6f} (for Equity)
                
                **Lattice:**
                - Steps: {result['lattice_steps']}
                - Size: {result['lattice_size']}
                - Model: {result['model']}
                """)
            
            # IPO scenario impact
            if enable_ipo:
                st.markdown("---")
                st.markdown("### 🎯 IPO Scenario Impact")
                
                st.info(f"""
                **IPO Refixing Condition:**
                - Check Date: {ipo_date}
                - Threshold: {ipo_threshold:,.0f}원
                - Refix Ratio: {ipo_ratio*100:.0f}%
                
                **Impact:**
                - If stock < {ipo_threshold:,.0f}원 at check date
                - Then CP adjusts to {conversion_price * ipo_ratio:,.0f}원
                - **Result:** Equity component increases (lower CP = more shares)
                """)

# ==============================================================================
# TAB 4: TRANSACTION SERVICES
# ==============================================================================

with tab4:
    st.header("🌲 Transaction Services (WOOD)")
    st.markdown("*Risk Assessment & Deal Structuring*")
    
    from src.engines.wood import ForestMap, WoodReportGenerator
    from src.engines.wood.library_v01 import get_issue_library, get_all_sectors
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("🎯 Configuration")
        
        ts_deal_name = st.text_input(
            "Deal Name",
            value=st.session_state.get('company_name', project_name),
            key="ts_deal_name"
        )
        
        sector = st.selectbox(
            "Sector",
            options=get_all_sectors(),
            index=0,
            help="Select sector for issue library"
        )
        
        if st.button("🌲 Run Transaction Services", use_container_width=True, type="primary"):
            with st.spinner("Loading issue library..."):
                try:
                    # Load issues
                    issues = get_issue_library(sector)
                    
                    # Create Forest Map
                    forest = ForestMap(deal_name=ts_deal_name)
                    forest.issues = issues
                    forest.calculate_metrics()
                    
                    # Generate reports
                    generator = WoodReportGenerator()
                    md_report = generator.generate_forest_map_md(forest)
                    summary = generator.generate_summary_text(forest)
                    csv_bridge = generator.generate_bridge_csv(forest.issues)
                    
                    st.session_state['ts_result'] = {
                        'forest': forest,
                        'md_report': md_report,
                        'summary': summary,
                        'csv_bridge': csv_bridge
                    }
                    
                    st.success("✅ Transaction Services Complete!")
                    st.rerun()
                except Exception as e:
                    import traceback
                    st.session_state["last_error"] = traceback.format_exc()
                    st.error(f"❌ Transaction Services Error: {e}")
                    with st.expander("🔍 Error Details"):
                        st.code(st.session_state["last_error"])
    
    with col2:
        st.subheader("📋 Results")
        
        if 'ts_result' in st.session_state:
            result = st.session_state['ts_result']
            forest = result['forest']
            
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Risk Score", forest.risk_score)
            
            with col2:
                st.metric("Red Flags", forest.red_flag_count)
            
            with col3:
                st.metric("QoE Adj", f"{forest.total_qoe_adj:+.1f}억")
            
            with col4:
                status_color = {
                    "✅ Proceed": "🟢",
                    "⚠️ Hold (Need Validation)": "🟡",
                    "🚫 Kill or Structure Required": "🔴"
                }
                st.metric("Status", status_color.get(forest.deal_status, "⚪"))
            
            st.divider()
            
            # Summary
            st.markdown("### 📊 Summary")
            st.markdown(result['summary'])
            
            # Downloads
            st.markdown("---")
            st.markdown("### 📥 Downloads")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.download_button(
                    label="📄 Download Forest Map (Markdown)",
                    data=result['md_report'],
                    file_name=f"{ts_deal_name}_ForestMap.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            
            with col2:
                st.download_button(
                    label="📊 Download Bridge CSV",
                    data=result['csv_bridge'],
                    file_name=f"{ts_deal_name}_Bridge.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            # Full report viewer
            with st.expander("📖 View Full Report"):
                st.markdown(result['md_report'])
        
        else:
            st.info("Run Transaction Services to see results")

# ==============================================================================
# TAB 5: NOTES & FEEDBACK
# ==============================================================================

with tab5:
    st.header("📝 Notes & Feedback")

    notes_file = os.path.join(project_root, "vault", "logs", "feedback.txt")
    system_log_file = os.path.join(project_root, "vault", "logs", "system.log")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        feedback = st.text_area(
            "Your notes",
            height=180,
            placeholder="Log your thoughts, ideas, or issues here...",
            key="feedback_text"
        )
    with c2:
        if st.button("💾 Save Note", use_container_width=True):
            if not feedback.strip():
                st.warning("내용을 입력해 주세요.")
            else:
                try:
                    os.makedirs(os.path.dirname(notes_file), exist_ok=True)
                    with open(notes_file, "a", encoding="utf-8") as f:
                        f.write(f"\n[{datetime.now().isoformat()}] {st.session_state.get('company_name', 'Unknown')}\n")
                        f.write(feedback.strip())
                        f.write("\n" + "=" * 70 + "\n")

                    _read_text_tail.clear()
                    st.session_state["feedback_text"] = ""
                    st.success("✅ Note saved")
                except Exception as e:
                    import traceback
                    st.session_state["last_error"] = traceback.format_exc()
                    st.error(f"❌ Save failed: {e}")
                    with st.expander("🔍 Error Details"):
                        st.code(st.session_state["last_error"])
    with c3:
        if st.button("🔄 Refresh View", use_container_width=True):
            _read_text_tail.clear()
            st.rerun()

    st.divider()

    col_a, col_b = st.columns([1, 1])
    with col_a:
        with st.expander("📖 View Recent Notes", expanded=True):
            recent = _read_text_tail(notes_file, max_chars=8000)
            if recent:
                st.text(recent)
            else:
                st.info("No notes yet.")

    with col_b:
        with st.expander("🧾 System Log (tail)", expanded=True):
            log_tail = _read_text_tail(system_log_file, max_chars=12000)
            if log_tail:
                st.text(log_tail)
            else:
                st.info("No system.log found (or empty).")

        with st.expander("🚨 Error Console (Last Error)", expanded=False):
            last_error = st.session_state.get("last_error")
            if last_error:
                st.code(last_error)
            else:
                st.caption("No captured errors in this session.")


# ==============================================================================
# TAB 6: DEAL PIPELINE (/run) - Web Orchestrator
# ==============================================================================

with tab6:
    st.header("🚀 Deal Pipeline (/run)")
    st.markdown("Zulu → X-RAY(LTM) → BRAVO → ALPHA를 웹에서 한번에 실행합니다.")

    pipeline_query = st.text_input(
        "Pipeline Target",
        value=st.session_state.get("company_name", ""),
        placeholder="e.g., Target_Co",
        key="pipeline_query"
    )

    st.markdown("#### ⚙️ Pipeline Options")
    opt1, opt2, opt3, opt4 = st.columns([1, 1, 1, 1])
    with opt1:
        include_wood_dcf = st.toggle(
            "Include DCF (V2)",
            value=True,
            help="X-RAY 이후 WOOD V2 DCF를 자동 실행/재사용합니다.",
            key="pipeline_include_wood"
        )
    with opt2:
        include_wood_v3 = st.toggle(
            "Include Live (V3)",
            value=True,
            help="Formula-linked Live Excel(WOOD V3)을 자동 생성/재사용합니다.",
            key="pipeline_include_wood_v3"
        )
    with opt3:
        reuse_existing_dcf = st.toggle(
            "Reuse DCF",
            value=True,
            help="이미 DCF 탭에서 돌린 결과가 있으면 재사용합니다.",
            key="pipeline_reuse_dcf"
        )
    with opt4:
        reuse_existing_v3 = st.toggle(
            "Reuse Live",
            value=True,
            help="이미 생성된 WOOD V3 Live가 있으면 재사용합니다.",
            key="pipeline_reuse_v3"
        )

    col1, col2 = st.columns([1, 2])
    with col1:
        run_pipeline = st.button("🚀 Run Full Pipeline", use_container_width=True, type="primary")
    with col2:
        st.caption("결과는 Teaser(스토리) + DCF(V2) + Live Excel(V3)까지 결합되어 ZIP 패키지로 다운로드 가능합니다.")

    if run_pipeline:
        missing = check_api_keys(require_openai=True, require_dart=False)
        if missing:
            st.error(f"❌ Missing API Keys: {', '.join(missing)}")
        elif not pipeline_query.strip():
            st.warning("타겟을 입력해 주세요.")
        else:
            try:
                import traceback

                zulu = get_zulu_scout()
                if not zulu:
                    st.error("ZuluScout 초기화 실패")
                    st.stop()

                with st.status("🚀 Running Pipeline...", expanded=True) as status:
                    status.update(label="🚀 ZULU: Targeting...", state="running")
                    leads = zulu.search_leads(pipeline_query.strip())
                    if not leads:
                        status.update(label="❌ ZULU: Target Not Found", state="error")
                        st.stop()

                    lead = leads[0]
                    status.update(label=f"✅ ZULU: Found {lead.get('company_name', 'N/A')}", state="running")

                    status.update(label="⚡ X-RAY: Analyzing financials (LTM)...", state="running")
                    from src.agents.xray_val import XrayValuation
                    xray = XrayValuation()
                    xray_result = xray.run_valuation(lead)

                    # Optional: WOOD DCF (V2) - auto-run or reuse
                    dcf_info = None
                    v3_live = None
                    if include_wood_dcf:
                        status.update(label="🌲 WOOD: Preparing DCF...", state="running")

                        existing = st.session_state.get("dcf_result") if reuse_existing_dcf else None
                        existing_ok = False
                        if existing and isinstance(existing, dict):
                            if existing.get("project_name") == (lead.get("company_name") or st.session_state.get("company_name")):
                                existing_ok = True

                        if existing_ok:
                            status.update(label="🌲 WOOD: Reusing existing DCF result", state="running")
                            dcf_info = (existing.get("dcf_info") or {}) if isinstance(existing, dict) else None
                        else:
                            status.update(label="🌲 WOOD: Running DCF (WOOD V2)...", state="running")
                            orchestrator = get_wood_orchestrator(use_live_beta=use_live_beta)

                            # Prefer X-RAY LTM revenue; fallback to collected_data if exists
                            base_rev = (
                                xray_result.get("financials", {}).get("revenue_bn")
                                or st.session_state.get("collected_data", {}).get("revenue")
                                or 0
                            )
                            data_source = xray_result.get("financials", {}).get("source") or "X-RAY LTM"

                            filepath, summary = orchestrator.run_valuation(
                                project_name=lead.get("company_name") or pipeline_query.strip(),
                                base_revenue=float(base_rev),
                                data_source=str(data_source),
                            )

                            dcf_info = _extract_dcf_info_from_wood_v2_summary(summary)
                            st.session_state["dcf_result"] = {
                                "filepath": filepath,
                                "summary": summary,
                                "timestamp": datetime.now().isoformat(),
                                "engine": "WOOD_V2",
                                "project_name": lead.get("company_name") or pipeline_query.strip(),
                                "dcf_info": dcf_info,
                            }
                            status.update(label="✅ WOOD: DCF complete", state="running")

                    # Optional: WOOD V3 Live Excel (Formula-Linked)
                    if include_wood_v3:
                        status.update(label="🧮 WOOD V3: Preparing Live Excel...", state="running")

                        existing_live = st.session_state.get("dcf_v3_live") if reuse_existing_v3 else None
                        live_ok = False
                        if existing_live and isinstance(existing_live, dict):
                            if existing_live.get("project_name") == (lead.get("company_name") or st.session_state.get("company_name")):
                                live_ok = True

                        if live_ok:
                            status.update(label="🧮 WOOD V3: Reusing existing Live model", state="running")
                            v3_live = existing_live
                        else:
                            status.update(label="🧮 WOOD V3: Building Live model (Formula-Linked)...", state="running")
                            from src.engines.wood.exporter_v3 import LiveExcelBuilder

                            # Scenario inputs: reuse DCF tab inputs if present; else use defaults
                            bg = _safe_float(st.session_state.get("base_growth", 0.10), 0.10)
                            bm = _safe_float(st.session_state.get("base_margin", 0.15), 0.15)
                            bulg = _safe_float(st.session_state.get("bull_growth", 0.15), 0.15)
                            bulm = _safe_float(st.session_state.get("bull_margin", 0.20), 0.20)
                            beg = _safe_float(st.session_state.get("bear_growth", 0.05), 0.05)
                            bem = _safe_float(st.session_state.get("bear_margin", 0.08), 0.08)

                            base_rev_for_v3 = (
                                xray_result.get("financials", {}).get("revenue_bn")
                                or st.session_state.get("collected_data", {}).get("revenue")
                                or 0
                            )

                            assumptions = {
                                "tax_rate": 0.22,
                                "terminal_growth": _safe_float(terminal_growth, 1.5) / 100.0,
                                "projection_years": int(projection_years),
                                # WACC inputs (editable in Excel)
                                "risk_free_rate": 0.035,
                                "market_risk_premium": 0.08,
                                "beta": 1.0,
                                "cost_of_debt": 0.045,
                            }

                            scenarios = {
                                "Base": {"revenue_growth": float(bg), "ebit_margin": float(bm)},
                                "Bull": {"revenue_growth": float(bulg), "ebit_margin": float(bulm)},
                                "Bear": {"revenue_growth": float(beg), "ebit_margin": float(bem)},
                            }

                            historical_data = None
                            if "historical_data" in st.session_state:
                                try:
                                    df_hist = st.session_state["historical_data"]
                                    if isinstance(df_hist, pd.DataFrame):
                                        historical_data = {"raw": df_hist.to_dict(orient="list")}
                                except Exception:
                                    historical_data = None

                            reports_dir = os.path.join(project_root, "vault", "reports")
                            os.makedirs(reports_dir, exist_ok=True)
                            pname = lead.get("company_name") or pipeline_query.strip()
                            filename = f"{pname}_DCF_WOOD_V3_LIVE_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                            filepath = os.path.join(reports_dir, filename)

                            builder = LiveExcelBuilder(filepath)
                            builder.build(
                                project_name=pname,
                                base_revenue=float(base_rev_for_v3),
                                assumptions=assumptions,
                                scenarios=scenarios,
                                historical_data=historical_data,
                            )

                            with open(filepath, "rb") as f:
                                excel_bytes = f.read()

                            v3_live = {
                                "filepath": filepath,
                                "filename": filename,
                                "bytes": excel_bytes,
                                "timestamp": datetime.now().isoformat(),
                                "engine": "WOOD_V3_LIVE",
                                "project_name": pname,
                            }
                            st.session_state["dcf_v3_live"] = v3_live
                            status.update(label="✅ WOOD V3: Live model built", state="running")

                    status.update(label="🤝 BRAVO: Matching buyers...", state="running")
                    from src.agents.bravo_matchmaker import BravoMatchmaker
                    bravo = BravoMatchmaker()

                    target_info = {
                        "company_name": lead.get("company_name"),
                        "sector": lead.get("sector"),
                        "summary": lead.get("summary"),
                        "revenue": (xray_result.get("financials", {}).get("revenue_bn") or 0),
                    }
                    buyers = bravo.find_buyers(target_info=target_info, valuation_info=xray_result.get("valuation"))

                    # Normalize buyer objects to dicts for display
                    buyer_dicts = []
                    for b in buyers or []:
                        if hasattr(b, "dict"):
                            buyer_dicts.append(b.dict())
                        elif isinstance(b, dict):
                            buyer_dicts.append(b)
                        else:
                            buyer_dicts.append({"name": str(b)})

                    status.update(label="🖋️ ALPHA: Writing teaser...", state="running")
                    from src.agents.alpha_vp import AlphaChief
                    alpha = AlphaChief()
                    teaser_md = alpha.generate_report(
                        target={"company_name": lead.get("company_name"), "sector": lead.get("sector"), "summary": lead.get("summary")},
                        financials=xray_result.get("financials", {}),
                        valuation=xray_result.get("valuation", {}),
                        buyers=buyer_dicts,
                        dcf_info=dcf_info or (st.session_state.get("dcf_result", {}) if isinstance(st.session_state.get("dcf_result"), dict) else None) or None,
                    )

                    st.session_state["pipeline_result"] = {
                        "lead": lead,
                        "xray": xray_result,
                        "buyers": buyer_dicts,
                        "teaser": teaser_md,
                        "dcf": st.session_state.get("dcf_result") if include_wood_dcf else None,
                        "live_v3": v3_live if include_wood_v3 else None,
                        "timestamp": datetime.now().isoformat(),
                    }

                    status.update(label="✅ Pipeline Complete", state="complete")
                    st.success("✅ Full pipeline completed")
                    st.rerun()

            except Exception as e:
                st.session_state["last_error"] = traceback.format_exc()
                st.error(f"❌ Pipeline Error: {e}")
                with st.expander("🔍 Error Details"):
                    st.code(st.session_state["last_error"])

    if "pipeline_result" in st.session_state:
        res = st.session_state["pipeline_result"]
        st.divider()

        # DCF snapshot (numbers + download) if available
        dcf_res = res.get("dcf") or st.session_state.get("dcf_result")
        if dcf_res and isinstance(dcf_res, dict):
            dcf_info = dcf_res.get("dcf_info") or {}
            if dcf_info:
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("EV (Base)", f"{dcf_info.get('ev_base', 0):,.0f}억" if dcf_info.get("ev_base") else "N/A")
                with c2:
                    st.metric("EV (Min)", f"{dcf_info.get('ev_min', 0):,.0f}억" if dcf_info.get("ev_min") else "N/A")
                with c3:
                    st.metric("EV (Max)", f"{dcf_info.get('ev_max', 0):,.0f}억" if dcf_info.get("ev_max") else "N/A")
                with c4:
                    st.metric("WACC", f"{dcf_info.get('wacc', 0):.2f}%" if dcf_info.get("wacc") else "N/A")

            with st.expander("🌲 WOOD DCF Summary (raw)"):
                st.markdown(dcf_res.get("summary", ""))

            if dcf_res.get("filepath") and os.path.exists(dcf_res["filepath"]):
                with open(dcf_res["filepath"], "rb") as f:
                    excel_bytes = f.read()
                st.download_button(
                    label="📥 Download DCF Excel (WOOD V2)",
                    data=excel_bytes,
                    file_name=os.path.basename(dcf_res["filepath"]),
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

        # Live model (WOOD V3) download if available
        live_res = res.get("live_v3") or st.session_state.get("dcf_v3_live")
        if live_res and isinstance(live_res, dict) and live_res.get("bytes"):
            st.divider()
            st.subheader("🧮 WOOD V3 Live Model (Formula-Linked)")
            st.caption("Assumptions 시트 입력(블루) 변경 시, Summary/DCF가 자동 업데이트됩니다.")
            st.download_button(
                label="📥 Download Live Excel (WOOD V3)",
                data=live_res["bytes"],
                file_name=live_res.get("filename") or "WOOD_V3_LIVE.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        # One-click package (ZIP: Teaser + DCF(V2) + Live(V3))
        st.divider()
        st.subheader("📦 One-click Package (ZIP)")
        zip_name = f"{(res.get('lead', {}).get('company_name') or 'Deal')}_Package_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            teaser_text = res.get("teaser", "")
            zf.writestr("01_Teaser.md", teaser_text.encode("utf-8"))

            if dcf_res and isinstance(dcf_res, dict) and dcf_res.get("filepath") and os.path.exists(dcf_res["filepath"]):
                zf.write(dcf_res["filepath"], arcname=f"02_DCF_WOOD_V2_{os.path.basename(dcf_res['filepath'])}")

            if live_res and isinstance(live_res, dict) and live_res.get("bytes"):
                zf.writestr(f"03_DCF_WOOD_V3_LIVE_{live_res.get('filename','WOOD_V3_LIVE.xlsx')}", live_res["bytes"])

        zip_buffer.seek(0)
        st.download_button(
            label="⬇️ Download Full Package (ZIP)",
            data=zip_buffer.getvalue(),
            file_name=zip_name,
            mime="application/zip",
            use_container_width=True,
            type="primary"
        )

        st.subheader("🧾 ALPHA Teaser (Markdown)")
        st.markdown(res.get("teaser", ""))

        st.download_button(
            label="📄 Download Teaser (Markdown)",
            data=res.get("teaser", ""),
            file_name=f"{(res.get('lead', {}).get('company_name') or 'Teaser')}_Teaser.md",
            mime="text/markdown",
            use_container_width=True
        )

# ==============================================================================
# FOOTER
# ==============================================================================

st.divider()
st.markdown("""
<div style='text-align: center; color: #6B7280; font-size: 12px;'>
    🌲 MIRKWOOD Partners - Deal OS v1.0<br/>
    <em>Risk to Price. Price to Structure.</em>
</div>
""", unsafe_allow_html=True)
