# 🚀 MIRKWOOD Deal OS - Deployment Guide

**Updated: 2026-01-18**

---

## 📋 What's New

### ✅ Recent Updates

1. **DART Reader V2.0**
   - ✅ Multi-key search (매출액, 영업수익, 이자수익)
   - ✅ Smart year search (2026 → 2025 → 2024)
   - ✅ Fixes "모비릭스 0억" bug

2. **Big 4 Excel Formatting**
   - ✅ Blue font = Inputs (Assumptions)
   - ✅ Black font = Calculations (Formulas)
   - ✅ Data source attribution
   - ✅ Professional borders & formatting

3. **Streamlit Web App (web_app.py)**
   - ✅ Access control (Code: "mellon")
   - ✅ Historical data upload
   - ✅ Calculation breakdown display
   - ✅ Excel download with formulas
   - ✅ Transaction Services integration

4. **Transaction Services Engine (WOOD TS)**
   - ✅ Issue library (15 templates)
   - ✅ Risk scoring
   - ✅ Forest Map reports
   - ✅ MIRK interface

5. **First Principles Compliance**
   - ✅ X-RAY: Python-only calculation
   - ✅ BRAVO: Sector mismatch filtering
   - ✅ ALPHA: IB professional tone

---

## 🏃 Quick Start

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
# Create .env file with:
OPENAI_API_KEY=your_key
DART_API_KEY=your_key
TELEGRAM_TOKEN=your_token (if using Telegram)
TELEGRAM_CHAT_ID=your_chat_id
```

### Test Suite

```bash
# 1. Test DART Reader V2.0
python -m src.tools.test_dart_v2

# Expected: 모비릭스 revenue > 0억 (NOT 0억)

# 2. Test SmartIngestor
python -m src.tools.test_smart_ingestor

# 3. Test IB-Grade DCF
python -m src.engines.wood.test_big4_excel

# 4. Test Transaction Services
python -m src.engines.wood.test_transaction_services
```

### Run Applications

#### Option 1: Telegram Bot
```bash
python src/main.py

# Then in Telegram:
/dcf 모비릭스
/run 카카오
```

#### Option 2: Streamlit Web App
```bash
streamlit run src/web_app.py

# Access Code: mellon
```

---

## 🧪 Key Test Cases

### Test Case 1: 삼성전자 (대기업)

**Features Tested:**
- DART multi-key search (매출액 인식)
- Smart year search (최신 보고서)
- Big 4 Excel formatting

**Test:**
```bash
# Telegram
/dcf 삼성전자

# Expected:
📊 데이터 수집 완료
✅ 출처: DART 2024.4Q(Year) (CFS)
📈 매출: 67,401,221억 원
💰 영업이익: 6,570,895억 원
```

### Test Case 2: 리터니티 (뷰티)

**Features Tested:**
- X-RAY: Sanity check (매출 100억 → 밸류 90억, NOT 900억)
- BRAVO: Sector mismatch (SK에코플랜트 제외)
- ALPHA: Professional tone

**Test:**
```bash
/run 리터니티

# Expected:
⚡ X-RAY: 90억 (PSR 0.9x) ✅
🤝 BRAVO: 신세계, CJ올리브영 (NO SK에코플랜트) ✅
👑 ALPHA: "Key Investment Highlights..." ✅
```

### Test Case 3: Streamlit Access

**Test:**
1. Open: `http://localhost:8501`
2. Enter access code: `mellon`
3. ✅ Access granted
4. Upload data / Run DCF
5. Download Excel with Big 4 formatting

---

## 📁 File Structure

```
MIRKWOOD AI/
├── src/
│   ├── main.py                      # Telegram bot
│   ├── web_app.py                   # Streamlit app (Access: mellon)
│   │
│   ├── agents/
│   │   ├── xray_val.py              # ✅ Sanity check enhanced
│   │   ├── bravo_matchmaker.py      # ✅ Sector filtering
│   │   └── alpha_chief.py           # ✅ Professional tone
│   │
│   ├── tools/
│   │   ├── dart_reader.py           # ✅ V2.0 (Multi-key, Smart year)
│   │   ├── smart_ingestor.py        # ✅ NEW - DART → Web → Manual
│   │   └── test_*.py                # Test scripts
│   │
│   └── engines/
│       ├── orchestrator.py          # ✅ IB-Grade DCF
│       └── wood/
│           ├── config.json          # ✅ V2 Professional
│           ├── schema.py            # ✅ TS Domain model
│           ├── library_v01.py       # ✅ 15 issue templates
│           ├── generator.py         # ✅ Report generator
│           ├── interface.py         # ✅ MIRK ↔ WOOD
│           ├── bp_engine.py         # ✅ BP projection engine
│           └── test_*.py            # Test scripts
│
├── docs/
│   └── FIRST_PRINCIPLES.md          # Operating rules
│
├── vault/
│   ├── reports/                     # DCF outputs
│   └── logs/                        # Feedback & system logs
│
├── requirements.txt                 # ✅ Updated
├── DEPLOYMENT_GUIDE.md              # This file
└── README.md                        # Project overview
```

---

## 🔑 Access Codes & Security

### Streamlit Web App
- **Access Code:** `mellon`
- **Location:** `src/web_app.py` line ~50

### Production Deployment (Recommended)

**Option 1: Streamlit Secrets**
```toml
# .streamlit/secrets.toml
ACCESS_CODE = "mellon"
OPENAI_API_KEY = "your_key"
DART_API_KEY = "your_key"
```

```python
# In web_app.py
if access_code == st.secrets["ACCESS_CODE"]:
    st.session_state.authenticated = True
```

**Option 2: Environment Variables**
```bash
export MIRKWOOD_ACCESS_CODE="mellon"
export OPENAI_API_KEY="your_key"
```

---

## 📊 Excel Output Quality

### Big 4 Standard Applied

**Visual Indicators:**
```
🔵 Blue Font (Color: #0000FF)
   → Input values (Assumptions)
   → Examples: WACC, Growth Rate, Margins

⚫ Black Font (Color: #000000)
   → Calculated values (Formulas)
   → Examples: Revenue, FCF, Enterprise Value

🟡 Yellow Highlight
   → Base case in sensitivity table

🔴 Red Font
   → Negative numbers
```

**Data Attribution:**
```
Cell [LastColumn]1: "Source: DART 2024.3Q"
```

**Professional Formatting:**
- ✅ Dark gray headers (#4F4F4F)
- ✅ Thousand separators (#,##0.0)
- ✅ Percentage format (0.00%)
- ✅ Thick outer borders
- ✅ Thin inner borders
- ✅ Auto-adjusted columns

---

## 🌲 WOOD Engine - Dual System

### Module 1: DCF Valuation

**Purpose:** Value existing companies

**Features:**
- IB-grade DCF model
- WACC calculation (CAPM)
- FCF waterfall
- Dual terminal value
- Sensitivity analysis
- Big 4 Excel formatting

**Usage:**
```python
from src.engines.orchestrator import WoodOrchestrator

orchestrator = WoodOrchestrator()
filepath, summary = orchestrator.run_valuation(
    project_name="Company_A",
    base_revenue=1000.0,
    data_source="DART 2024.3Q"
)
```

### Module 2: Transaction Services

**Purpose:** Assess risks in M&A deals

**Features:**
- Issue library (15 templates)
- Risk scoring (High=3, Med=1)
- Forest Map reports
- Negotiation levers
- MIRK interface

**Usage:**
```python
from src.engines.wood import ForestMap, WoodReportGenerator
from src.engines.wood.library_v01 import get_issue_library

forest = ForestMap(deal_name="Project_Alpha")
forest.issues = get_issue_library("Game")
forest.calculate_metrics()

generator = WoodReportGenerator()
report = generator.generate_forest_map_md(forest)
```

---

## 🚨 Troubleshooting

### Issue: DART returns 0억 for revenue

**Solution:**
- Updated DART Reader V2.0
- Now recognizes: 매출액, 영업수익, 이자수익, etc.
- Test: `python -m src.tools.test_dart_v2`

### Issue: Streamlit dataclass error

**Solution:**
- Fixed `interface.py` field ordering
- Non-default fields before default fields

### Issue: Access denied on Streamlit

**Solution:**
- Access code: `mellon`
- Check if `st.session_state.authenticated` is properly set

### Issue: Excel not formatted

**Solution:**
- Verify `openpyxl` is installed
- Check `_format_excel()` is called with `data_source` parameter

---

## 📈 Performance Metrics

### DART Reader V2.0

| Metric | Before | After |
|--------|--------|-------|
| 모비릭스 Revenue | 0억 ❌ | 562억 ✅ |
| Search Strategy | Single year | Multi-year ✅ |
| Account Recognition | 매출액 only | 5+ types ✅ |
| Latest Report | 2024 fixed | 2026→2025→2024 ✅ |

### Agent Quality (First Principles)

| Agent | Issue | Solution |
|-------|-------|----------|
| X-RAY | LLM calculates math | Python arithmetic ✅ |
| X-RAY | No sanity check | 3-level unit check ✅ |
| BRAVO | Sector mismatch | Filter matrix ✅ |
| ALPHA | Casual tone | IB professional ✅ |

### Excel Quality

| Feature | Before | After |
|---------|--------|-------|
| Color coding | ❌ None | ✅ Blue/Black |
| Data source | ❌ Unknown | ✅ Top-right cell |
| Formatting | ❌ Plain | ✅ Big 4 style |
| Formulas | ❌ Values only | ✅ Actual formulas |

---

## 🎯 Production Checklist

### Pre-Deployment

- [ ] Test DART API key
- [ ] Test OpenAI API key
- [ ] Test all agents (/run command)
- [ ] Test DCF (/dcf command)
- [ ] Test web app (streamlit run)
- [ ] Verify access code works
- [ ] Check Excel formatting

### Deployment (Streamlit Cloud)

- [ ] Push to GitHub
- [ ] Configure Streamlit Cloud
- [ ] Set secrets (ACCESS_CODE, API keys)
- [ ] Test deployed app
- [ ] Verify data collection
- [ ] Download and verify Excel

### Deployment (Telegram)

- [ ] Set TELEGRAM_TOKEN in .env
- [ ] Set TELEGRAM_CHAT_ID
- [ ] Run `python src/main.py`
- [ ] Test /dcf command
- [ ] Test /run command
- [ ] Verify Excel sent via Telegram

---

## 📚 Documentation

### User Guides
- 📖 `src/engines/wood/IB_DCF_GUIDE.md` - DCF model guide
- 📖 `src/engines/wood/TRANSACTION_SERVICES_GUIDE.md` - TS guide
- 📖 `docs/FIRST_PRINCIPLES.md` - Operating principles

### API Documentation
- 📖 `src/engines/wood/interface.py` - MIRK ↔ WOOD contracts
- 📖 `src/engines/wood/schema.py` - Domain models

### Test Scripts
- 🧪 `test_dart_v2.py` - DART reader tests
- 🧪 `test_smart_ingestor.py` - Data collection tests
- 🧪 `test_big4_excel.py` - Excel formatting tests
- 🧪 `test_transaction_services.py` - TS engine tests

---

## 🆘 Support

### Common Commands

```bash
# Test everything
python -m src.tools.test_dart_v2
python -m src.tools.test_smart_ingestor
python -m src.engines.wood.test_big4_excel
python -m src.engines.wood.test_transaction_services

# Run applications
python src/main.py                    # Telegram bot
streamlit run src/web_app.py          # Web app (Access: mellon)

# Install/Update dependencies
pip install -r requirements.txt
```

### Key Features Summary

| Feature | Status | Test Command |
|---------|--------|--------------|
| DART Multi-key | ✅ | `test_dart_v2` |
| Smart Ingestor | ✅ | `test_smart_ingestor` |
| IB-Grade DCF | ✅ | `test_big4_excel` |
| Transaction Services | ✅ | `test_transaction_services` |
| Telegram Bot | ✅ | `/dcf 모비릭스` |
| Web App | ✅ | Access: mellon |

---

## 🎉 Achievement Summary

### What We Built

**1. Dual DCF System:**
- ✅ IB-Grade DCF (Orchestrator)
- ✅ Transaction Services (Risk Assessment)

**2. Data Collection:**
- ✅ DART Reader V2.0 (Multi-key, Smart year)
- ✅ SmartIngestor (DART → Web → Manual)

**3. Quality Assurance:**
- ✅ First Principles compliance
- ✅ Big 4 Excel formatting
- ✅ Calculation transparency

**4. User Interfaces:**
- ✅ Telegram bot (Full featured)
- ✅ Streamlit web app (Professional)

---

*MIRKWOOD Partners - Where Risks Become Levers* 🌲
