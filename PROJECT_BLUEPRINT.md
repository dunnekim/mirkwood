# MIRKWOOD Deal OS - Complete Blueprint

**Version:** 2.0  
**Last Updated:** 2026-01-18  
**Status:** Production Ready

---

## 🎯 Project Overview

MIRKWOOD Deal OS는 **Boutique Investment Bank AI**로서 다음 기능을 제공합니다:

1. **Deal Sourcing** (ZULU Scout)
2. **Valuation** (X-RAY + WOOD DCF)
3. **Buyer Matching** (BRAVO Matchmaker)
4. **Structuring** (WOOD OPM)
5. **Transaction Services** (WOOD TS)
6. **Report Generation** (ALPHA Chief)

---

## 🏗️ Architecture

### Three-Engine System

```
┌─────────────────────────────────────────────────────────────┐
│                    MIRKWOOD Deal OS                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   MIRK (CF)  │  │  WOOD (DCF)  │  │  WOOD (OPM)  │     │
│  │              │  │              │  │              │     │
│  │ • Sourcing   │  │ • IB-Grade   │  │ • TF Model   │     │
│  │ • Multiple   │  │ • WACC       │  │ • IPO Refix  │     │
│  │ • Matching   │  │ • FCF        │  │ • Hybrid Sec │     │
│  │ • Teaser     │  │ • Scenario   │  │ • Structure  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  ┌──────────────────────────────────────────────────┐      │
│  │           WOOD (Transaction Services)            │      │
│  │                                                  │      │
│  │  • Issue Library (15 templates)                 │      │
│  │  • Risk Scoring                                 │      │
│  │  • Forest Map Reports                           │      │
│  │  • Negotiation Levers                           │      │
│  └──────────────────────────────────────────────────┘      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📐 Financial Models

### 1. Multiple-Based Valuation (X-RAY)

**Method:** Peer multiples (EV/EBITDA, P/E, PSR)

**Logic:**
```python
# FIRST PRINCIPLE: Python calculation only
value = revenue × multiple

# Sanity checks:
- Small company (<100억) should NOT be >1000억
- Loss-making → PSR cap at 2x
- PSR >10x → Auto-cap at 3x
```

**Use Case:** Quick valuation, off-market deals

---

### 2. DCF Valuation (WOOD DCF)

**Method:** Discounted Cash Flow with IB-grade rigor

**Formula:**
```
EV = Σ PV(FCF_t) + PV(Terminal Value)

Where:
- FCF = EBIT × (1-Tax) + D&A - Capex - Δ NWC
- WACC = Re × (E/V) + Rd × (1-Tax) × (D/V)
- TV = FCF_last × (1+g) / (WACC - g)
```

**Features:**
- Beta unlevering/re-levering (Hamada formula)
- Detailed FCF waterfall
- Dual terminal value (Gordon + Exit Multiple)
- Sensitivity analysis (WACC × Growth)

**Use Case:** Investor presentations, fairness opinions

---

### 3. OPM Valuation (WOOD OPM)

**Method:** Tsiveriotis-Fernandes Model

**Formula:**
```
V = D + E

Where:
- D = Σ PV(Debt CF) at (Rf + CS)  ← Risky rate
- E = Σ PV(Equity CF) at Rf       ← Risk-free rate
```

**Key Innovation: Split Discounting**
```
Traditional (Black-Scholes):
  All CF at Rf → Overvalues debt

TF Model:
  Debt at Rf + CS → Correct credit risk pricing
```

**IPO Conditional Refixing:**
```
At IPO Check Date:
  if Stock < Threshold:
      CP_new = max(Floor, CP_old × Ratio)
  
  Impact: Lower CP → More shares → Higher value
```

**Use Case:** RCPS/CB structuring, investor protection

---

### 4. Transaction Services (WOOD TS)

**Method:** Risk assessment & quantification

**Process:**
```
1. Load issue library (sector-specific)
2. Identify applicable issues
3. Quantify financial impact
4. Generate negotiation levers
5. Output Forest Map report
```

**Risk Scoring:**
```
Score = (High × 3) + (Med × 1)

0-2: Proceed ✅
3-5: Hold ⚠️
6+: Kill or Structure 🚫
```

**Use Case:** Due diligence, deal structuring

---

## 🔧 Technical Specifications

### Data Flow

```
1. Data Collection (SmartIngestor)
   ├─→ DART API (Primary)
   ├─→ Web Search (Secondary)
   └─→ Manual Input (Fallback)

2. Valuation (Multi-Model)
   ├─→ X-RAY: Multiple-based (Quick)
   ├─→ WOOD DCF: Discounted cash flow (Detailed)
   └─→ WOOD OPM: Option pricing (Structured)

3. Risk Assessment (WOOD TS)
   ├─→ Issue identification
   ├─→ Impact quantification
   └─→ Lever generation

4. Output Generation
   ├─→ Telegram: Text summary + Excel
   ├─→ Streamlit: Interactive dashboard
   └─→ Excel: Big 4 formatted reports
```

### Excel Quality Standards

**Big 4 Formatting:**
```
✅ Color Coding:
   - Blue (0000FF) = Input values
   - Black (000000) = Calculated values
   - Red (FF0000) = Negative numbers

✅ Data Attribution:
   - Top-right cell: "Source: DART 2024.3Q"

✅ Professional Styling:
   - Dark gray headers (#4F4F4F)
   - Thousand separators (#,##0.0)
   - Percentage format (0.00%)
   - Borders (thick outer, thin inner)

✅ Formulas:
   - SUM, PV, IF formulas (not just values)
   - Auditor can verify calculations
```

---

## 🧪 Testing Strategy

### Unit Tests

```bash
# 1. DART Reader (Multi-key, Smart year)
python -m src.tools.test_dart_v2
# ✅ 모비릭스: 562억 (NOT 0억)

# 2. SmartIngestor (DART → Web → Manual)
python -m src.tools.test_smart_ingestor
# ✅ 3-stage fallback

# 3. IB-Grade DCF (Big 4 Excel)
python -m src.engines.wood.test_big4_excel
# ✅ Blue/Black formatting

# 4. Transaction Services (Risk scoring)
python -m src.engines.wood.test_transaction_services
# ✅ 15 issues, Forest Map

# 5. OPM Engine (TF Model)
python -m src.engines.wood.test_opm
# ✅ Split discounting, IPO scenario
```

### Integration Tests

```bash
# Telegram Bot
python src/main.py

# Test commands:
/run 리터니티          # Full pipeline
/dcf 모비릭스          # DCF valuation
/struct CompanyA 20000 25000  # OPM structuring

# Streamlit Web App
streamlit run src/web_app.py
# Access Code: mellon
```

---

## 📊 Performance Benchmarks

### DART Reader V2.0

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| 모비릭스 Revenue | 0억 | 562억 | ✅ Fixed |
| Account Types | 1 | 5+ | 5x |
| Year Search | Fixed | Dynamic | ✅ |
| Success Rate | ~60% | ~85% | +25%p |

### Agent Quality (First Principles)

| Agent | Metric | Before | After |
|-------|--------|--------|-------|
| X-RAY | Math Accuracy | LLM | Python ✅ |
| X-RAY | Unit Check | 2-level | 3-level ✅ |
| BRAVO | Sector Match | None | Matrix ✅ |
| ALPHA | Tone | Casual | IB Pro ✅ |

### Excel Quality

| Feature | Before | After | Standard |
|---------|--------|-------|----------|
| Color Coding | ❌ | ✅ | Big 4 |
| Data Source | ❌ | ✅ | Big 4 |
| Formulas | ❌ | ✅ | Big 4 |
| Formatting | Basic | Professional | Big 4 |

---

## 🚀 Deployment

### Streamlit Cloud

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "MIRKWOOD Deal OS v2.0"
   git push
   ```

2. **Configure Streamlit Cloud**
   - Main file: `src/web_app.py`
   - Python: 3.9+
   - Secrets: ACCESS_CODE, OPENAI_API_KEY, DART_API_KEY

3. **Test**
   - Access code: `mellon`
   - Upload data
   - Run DCF
   - Download Excel

### Telegram Bot (Self-Hosted)

1. **Set Environment**
   ```bash
   # .env file
   TELEGRAM_TOKEN=your_token
   TELEGRAM_CHAT_ID=your_chat_id
   OPENAI_API_KEY=your_key
   DART_API_KEY=your_key
   ```

2. **Run**
   ```bash
   python src/main.py
   ```

3. **Test Commands**
   ```
   /run [company]      # Full pipeline
   /dcf [company]      # DCF valuation
   /struct [co] [S] [K] # OPM structuring
   ```

---

## 📚 Documentation

### User Guides
- 📖 `IB_DCF_GUIDE.md` - DCF methodology
- 📖 `TRANSACTION_SERVICES_GUIDE.md` - TS process
- 📖 `OPM_GUIDE.md` - Hybrid securities valuation
- 📖 `DEPLOYMENT_GUIDE.md` - Deployment instructions

### Technical Specs
- 📖 `FIRST_PRINCIPLES.md` - Operating principles
- 📖 `PROJECT_BLUEPRINT.md` - This document
- 📖 `knowledge/skill_*.md` - Agent skills

### API Documentation
- 📖 `src/engines/wood/interface.py` - Data contracts
- 📖 `src/engines/wood/schema.py` - Domain models

---

## 🎓 Financial Concepts

### Key Terms

| Term | Definition | Used In |
|------|------------|---------|
| **WACC** | Weighted Average Cost of Capital | DCF |
| **FCF** | Free Cash Flow | DCF |
| **QoE** | Quality of Earnings | TS |
| **TF Model** | Tsiveriotis-Fernandes | OPM |
| **Split Discounting** | Debt/Equity separate rates | OPM |
| **IPO Refixing** | Conditional CP adjustment | OPM |

### Valuation Hierarchy

```
Level 1: Multiple-Based (X-RAY)
   ↓ Quick, off-market deals
   
Level 2: DCF (WOOD DCF)
   ↓ Detailed, investor presentations
   
Level 3: OPM (WOOD OPM)
   ↓ Structured securities, mezzanine
   
Level 4: Transaction Services (WOOD TS)
   ↓ Risk assessment, due diligence
```

---

## ⚠️ Important Notes

### First Principles (Non-Negotiable)

1. **NO DCF for Primary Valuation**
   - Use multiple-based (X-RAY) as primary
   - DCF is for cross-check and presentations

2. **Zero Hallucination Policy**
   - ALL calculations in Python (not LLM)
   - Example: 100억 × 0.9 = 90억 (NOT 900억)

3. **Logical Structuring**
   - Sector fit MUST match
   - Construction ⚔️ Beauty = REJECT

4. **Professional Output**
   - Start with "Key Investment Highlights"
   - End with "Risk Factors"
   - NO casual tone

### Data Quality

**DART Reader V2.0:**
- ✅ Recognizes: 매출액, 영업수익, 이자수익, etc.
- ✅ Smart year search: 2026 → 2025 → 2024
- ✅ Consolidated (CFS) priority

**SmartIngestor:**
- ✅ DART (High confidence) → Web (Medium) → Manual (User)
- ✅ Source attribution mandatory
- ✅ Transparency for audit trail

---

## 🎯 Success Criteria

### Functional Requirements

- [x] DART Reader recognizes "영업수익" (모비릭스 case)
- [x] X-RAY uses Python-only calculation
- [x] BRAVO filters sector mismatches
- [x] ALPHA uses professional tone
- [x] Excel has Big 4 formatting
- [x] Data source clearly attributed
- [x] OPM implements TF split discounting
- [x] IPO refixing logic functional

### Quality Requirements

- [x] No calculation errors (sanity checks)
- [x] No hallucinations (Python only)
- [x] No sector mismatches (filter matrix)
- [x] Professional reports (IB standard)
- [x] Audit-ready Excel (formulas + source)

---

## 🚀 Future Roadmap

### Phase 1 (✅ Complete)
- ✅ Core agents (ZULU, X-RAY, BRAVO, ALPHA)
- ✅ WOOD DCF (IB-grade)
- ✅ WOOD OPM (TF model)
- ✅ WOOD TS (Issue library)
- ✅ Big 4 Excel formatting
- ✅ Streamlit web app
- ✅ Telegram bot

### Phase 2 (Next)
- [ ] Excel formula injection (exceljs equivalent)
- [ ] Real-time market data (KOFIA API)
- [ ] LBO model (leveraged buyout)
- [ ] Portfolio tracker
- [ ] Multi-language support (English)

### Phase 3 (Future)
- [ ] AI-powered issue detection
- [ ] Monte Carlo simulation
- [ ] Regulatory reporting (K-IFRS)
- [ ] Deal pipeline CRM
- [ ] Automated teaser generation

---

## 📖 References

### Financial Standards
- **K-IFRS 1109**: Financial Instruments
- **AICPA**: Valuation Standards
- **IVSC**: International Valuation Standards

### Academic Papers
- **Tsiveriotis & Fernandes (1998)**: TF Model
- **Damodaran**: Valuation textbooks
- **McKinsey**: Valuation best practices

### Industry Benchmarks
- **Big 4**: Deloitte, PwC, EY, KPMG TS reports
- **Goldman Sachs**: DCF methodology
- **Morgan Stanley**: Fairness opinion standards

---

*MIRKWOOD Partners - Where Risks Become Levers* 🌲
