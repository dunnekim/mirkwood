# 🚀 MIRKWOOD Deal OS - Quick Start Guide

**Get up and running in 5 minutes!**

---

## ⚡ Prerequisites

### Required
- Python 3.9+
- pip (Python package manager)

### API Keys Needed
- OpenAI API Key (for LLM)
- DART API Key (for Korean financial data)
- Telegram Token (optional, for bot)

---

## 📦 Installation

### Step 1: Clone & Install

```bash
# Navigate to project directory
cd "C:\Users\두현\Desktop\AI Lab\MIRKWOOD AI"

# Install dependencies
pip install -r requirements.txt
```

**Key packages:**
- `yfinance` - Live market data & beta calculation
- `scipy` - Statistical regression
- `openpyxl` - Excel generation
- `streamlit` - Web interface
- `python-telegram-bot` - Telegram bot

### Step 2: Configure API Keys

Create `.env` file in project root:

```bash
# .env
OPENAI_API_KEY=sk-your-key-here
DART_API_KEY=your-dart-key-here
TELEGRAM_TOKEN=your-token (optional)
TELEGRAM_CHAT_ID=your-chat-id (optional)
```

---

## 🧪 Quick Test

### Run Complete Test Suite

**Windows:**
```bash
RUN_ALL_TESTS.bat
```

**Mac/Linux:**
```bash
chmod +x RUN_ALL_TESTS.sh
./RUN_ALL_TESTS.sh
```

**Expected Output:**
```
═══════════════════════════════════════════════════════════════════════
🌲 MIRKWOOD Deal OS - Complete Test Suite
═══════════════════════════════════════════════════════════════════════

📊 DATA COLLECTION TESTS
  ✅ PASSED: DART Reader V2.0
  ✅ PASSED: Smart Ingestor
  ✅ PASSED: Market Scanner (Live Beta)

💰 VALUATION ENGINE TESTS
  ✅ PASSED: Korean WACC (KICPA + SRP)
  ✅ PASSED: Live Beta + WACC Integration
  ✅ PASSED: IB-Grade DCF (Big 4 Excel)
  ✅ PASSED: OPM Engine (TF Model)

🌲 TRANSACTION SERVICES TESTS
  ✅ PASSED: Transaction Services Engine

═══════════════════════════════════════════════════════════════════════
🎉 ALL TESTS PASSED - SYSTEM READY FOR PRODUCTION
═══════════════════════════════════════════════════════════════════════
```

---

## 🚀 Run Applications

### Option 1: Streamlit Web App

```bash
streamlit run src/web_app.py
```

**Access:**
- URL: `http://localhost:8501`
- Access Code: `mellon`

**Features:**
- 📊 Data Collection (DART/Web/Manual)
- 📈 DCF Valuation (Korean WACC)
- 🏗️ OPM Structuring (TF Model)
- 🌲 Transaction Services (Forest Map)

### Option 2: Telegram Bot

```bash
python src/main.py
```

**Commands:**
```
/run [company]           # Full pipeline
/dcf [company]           # DCF valuation
/struct [co] [S] [K]     # OPM structuring
/help                    # Show manual
```

---

## 💡 Quick Examples

### Example 1: DCF Valuation (Telegram)

```
You: /dcf 삼성전자

Bot: 🔎 '삼성전자' 데이터 수집 중...
     1️⃣ DART 공식 재무제표 확인
     2️⃣ 웹 검색 (뉴스/실적 추정)
     3️⃣ 사용자 입력 대기

Bot: 📊 데이터 수집 완료
     ✅ 출처: DART 2024.4Q(Year) (CFS)
     📈 매출: 67,401,221억 원
     💰 영업이익: 6,570,895억 원

Bot: 🌲 **MIRKWOOD Valuation: 삼성전자**
     **Enterprise Value Range: ...**
     
Bot: 📊 [Excel File] 삼성전자_DCF_IB_Grade.xlsx
     ✅ Big 4 회계법인 스타일 적용
```

### Example 2: Web App (Streamlit)

```
1. Open: http://localhost:8501
2. Enter access code: mellon
3. Tab 1 (Data Collection):
   - Enter: 네이버
   - Click: 🔎 Search Data
   - ✅ DART data loaded

4. Tab 2 (DCF Valuation):
   - Configure scenarios
   - Click: 🚀 Run DCF Valuation
   - Download: Big 4 Excel

5. Tab 3 (OPM):
   - Enter security terms
   - Click: 🚀 Run OPM
   - View: TF Model results
```

---

## 🔬 Key Features to Test

### 1. Live Beta Calculation

```python
from src.tools.market_scanner import MarketScanner

scanner = MarketScanner()
result = scanner.calculate_beta("005930")  # 삼성전자

# Output:
# Raw Beta: 0.98
# Adjusted Beta: 0.99 (Blume)
# R²: 0.45
# Confidence: High
```

### 2. Korean WACC

```python
from src.engines.wood.wacc_logic import KoreanWACCCalculator

calculator = KoreanWACCCalculator(use_live_beta=True)

result = calculator.calculate(
    peers=[...],
    peer_tickers=["035420", "035720"],  # 네이버, 카카오
    is_listed=True,
    size_metric_mil_krw=1000000  # 1조 시총
)

# Output:
# WACC: 11.34%
# SRP: +1.27% (3분위)
# Beta: Live calculated from market
```

### 3. Big 4 Excel

**Check Excel file for:**
- ✅ Blue font = Inputs (WACC, Growth, Margin)
- ✅ Black font = Calculations (Revenue, FCF, EV)
- ✅ Top-right cell: "Source: DART 2024.3Q"
- ✅ Thousand separators: 14,500.0
- ✅ Professional borders

---

## 🐛 Troubleshooting

### Issue: yfinance not found

```bash
pip install yfinance scipy
```

### Issue: DART returns no data

**Solution:**
- Use exact legal name: "삼성전자" not "삼성"
- Try: 삼성전자, 네이버, 카카오 (confirmed working)

### Issue: Beta calculation fails

**Solution:**
- Check internet connection
- Verify ticker code is correct
- System will fallback to default beta (1.0)

### Issue: Streamlit API key error

**Solution:**
```bash
# Create .env file
echo OPENAI_API_KEY=sk-your-key > .env
echo DART_API_KEY=your-key >> .env
```

---

## 📚 Documentation

### Essential Guides
- 📖 `QUICK_START.md` - This file
- 📖 `DEPLOYMENT_GUIDE.md` - Full deployment
- 📖 `STREAMLIT_CLOUD_SETUP.md` - Cloud deployment
- 📖 `LIVE_BETA_GUIDE.md` - Beta calculation methodology

### Technical Docs
- 📖 `PROJECT_BLUEPRINT.md` - System architecture
- 📖 `FIRST_PRINCIPLES.md` - Operating principles
- 📖 `src/engines/wood/IB_DCF_GUIDE.md` - DCF methodology
- 📖 `src/engines/wood/OPM_GUIDE.md` - OPM methodology

---

## ✅ Verification Checklist

After setup, verify:

- [ ] All tests pass (`RUN_ALL_TESTS.bat`)
- [ ] Streamlit app starts (Access: mellon)
- [ ] DART data loads (Test: 삼성전자)
- [ ] Live beta calculates (Check logs)
- [ ] Excel downloads with Big 4 formatting
- [ ] Korean WACC shows SRP quintile

---

## 🎯 What You Get

**Fully Automated:**
- ✅ Data collection (DART → Web → Manual)
- ✅ Beta calculation (Regression + Blume)
- ✅ WACC calculation (KICPA + SRP)
- ✅ DCF valuation (IB-grade)
- ✅ OPM structuring (TF Model)
- ✅ Risk assessment (TS Engine)
- ✅ Report generation (Big 4 Excel)

**No External Dependencies:**
- ❌ No Bloomberg needed
- ❌ No DataGuide subscription
- ❌ No manual beta lookup
- ✅ Self-sufficient House View

---

## 🎉 Success!

**If all tests pass, you now have:**

✅ **Production-ready** Investment Bank AI  
✅ **Korean market specialized** (KICPA + SRP)  
✅ **Real IB methodology** (Live beta calculation)  
✅ **Institutional quality** (Big 4 Excel)  
✅ **Fully automated** (No manual lookups)

**Start valuing companies now!** 🚀

---

## 📞 Quick Commands Reference

```bash
# Test everything
RUN_ALL_TESTS.bat

# Run web app
streamlit run src/web_app.py

# Run telegram bot
python src/main.py

# Test specific component
python -m src.tools.test_market_scanner
python -m src.engines.wood.test_korean_wacc
python -m src.engines.wood.test_live_beta_wacc
```

---

*MIRKWOOD Partners - Deal OS v2.0*  
*"Calculate, Don't Copy"* 🔬🌲
