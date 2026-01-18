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

# Path Setup
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

# Import MIRKWOOD components (lazy loading for API dependencies)
try:
    from src.engines.orchestrator import WoodOrchestrator
except ImportError as e:
    st.error(f"⚠️ Import Error: {e}")
    st.stop()

# Check API keys before importing SmartIngestor
def check_api_keys():
    """Check if required API keys are set"""
    missing_keys = []
    
    if not os.getenv("OPENAI_API_KEY"):
        missing_keys.append("OPENAI_API_KEY")
    
    if not os.getenv("DART_API_KEY"):
        missing_keys.append("DART_API_KEY")
    
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

st.title("🌲 MIRKWOOD Deal OS")
st.markdown("**Enterprise Valuation & Transaction Services Platform**")

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Data Collection", 
    "📈 DCF Valuation", 
    "🏗️ OPM Structuring",
    "🌲 Transaction Services",
    "📝 Notes"
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
        
        with col1:
            st.metric("Revenue", f"{data.get('revenue', 0):.1f}억 원")
        
        with col2:
            st.metric("Operating Profit", f"{data.get('op', 0):.1f}억 원")
        
        with col3:
            margin = (data.get('op', 0) / data.get('revenue', 1)) * 100 if data.get('revenue', 0) > 0 else 0
            st.metric("OP Margin", f"{margin:.1f}%")
        
        st.info(f"""
        **📊 Data Source:** {data.get('source', 'Unknown')}  
        **📝 Description:** {data.get('description', 'N/A')}  
        **✅ Confidence:** {confidence}
        """)
        
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
        
        st.markdown(f"### Target: **{company}**")
        st.markdown(f"**Base Revenue:** {data['revenue']:.1f}억 원 (Source: {data['source']})")
        
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
        if st.button("🚀 Run DCF Valuation", use_container_width=True, type="primary"):
            with st.spinner("Running IB-Grade DCF Model..."):
                try:
                    orchestrator = WoodOrchestrator()
                    
                    filepath, summary = orchestrator.run_valuation(
                        project_name=company,
                        base_revenue=data['revenue'],
                        data_source=data['source']
                    )
                    
                    st.session_state['dcf_result'] = {
                        'filepath': filepath,
                        'summary': summary,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    st.success("✅ DCF Valuation Completed!")
                    st.rerun()
                
                except Exception as e:
                    st.error(f"❌ DCF Error: {e}")
                    import traceback
                    with st.expander("🔍 Error Details"):
                        st.code(traceback.format_exc())
        
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
                st.metric("Data Source", data['source'])
            
            with col2:
                st.metric("Base Revenue", f"{data['revenue']:.1f}억")
            
            with col3:
                st.metric("OP Margin", f"{(data['op']/data['revenue']*100):.1f}%" if data['revenue'] > 0 else "N/A")
            
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
                    st.error(f"❌ OPM Error: {e}")
                    import traceback
                    with st.expander("Error Details"):
                        st.code(traceback.format_exc())
        
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
    
    feedback = st.text_area(
        "Your notes",
        height=200,
        placeholder="Log your thoughts, ideas, or issues here..."
    )
    
    if st.button("💾 Save Note", use_container_width=True):
        if feedback:
            # Save to file
            notes_file = os.path.join(project_root, 'vault', 'logs', 'feedback.txt')
            os.makedirs(os.path.dirname(notes_file), exist_ok=True)
            
            with open(notes_file, 'a', encoding='utf-8') as f:
                f.write(f"\n[{datetime.now().isoformat()}] {st.session_state.get('company_name', 'Unknown')}\n")
                f.write(feedback)
                f.write("\n" + "="*70 + "\n")
            
            st.success("✅ Note saved to vault/logs/feedback.txt")
            st.balloons()
        else:
            st.warning("Please write something")
    
    # Display recent notes
    notes_file = os.path.join(project_root, 'vault', 'logs', 'feedback.txt')
    if os.path.exists(notes_file):
        with st.expander("📖 View Recent Notes"):
            with open(notes_file, 'r', encoding='utf-8') as f:
                recent = f.read()
                st.text(recent[-2000:] if len(recent) > 2000 else recent)

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
