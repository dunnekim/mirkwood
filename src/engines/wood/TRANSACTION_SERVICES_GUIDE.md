```markdown
# 🌲 WOOD Transaction Services Engine

**"Risks → Price & Structure"**

투자은행/PE 실무에서 사용하는 Transaction Services (TS) 방법론을 코드화한 엔진입니다.

---

## 📋 Overview

### What is Transaction Services?

Transaction Services는 M&A 딜에서 **재무 실사(Financial DD)**를 수행하고, 발견된 리스크를 다음으로 번역합니다:
- **가격 조정** (Price): Quality of Earnings (QoE) 조정
- **구조화** (Structure): Earn-out, Escrow, SPA 조항
- **협상 레버** (Levers): Net Debt 정의, WC Peg, R&W

### WOOD TS Engine의 역할

1. **이슈 식별**: 섹터별 이슈 라이브러리 기반 자동 스캐닝
2. **리스크 정량화**: EBITDA/Net Debt/WC 영향 계산
3. **협상 레버 생성**: 가격/구조/SPA 제안사항 도출
4. **Forest Map 리포트**: IB 수준의 TS 리포트 자동 생성

---

## 🏗️ Architecture

### Module Structure

```
src/engines/wood/
├── schema.py                    # 도메인 모델 (Pydantic)
├── library_v01.py               # 이슈 라이브러리 (템플릿)
├── generator.py                 # 리포트 생성 로직
├── interface.py                 # MIRK ↔ WOOD 인터페이스
├── test_transaction_services.py # 테스트 스크립트
└── TRANSACTION_SERVICES_GUIDE.md  # 이 문서
```

### Domain Model (schema.py)

```python
WoodIssue               # 단일 TS 이슈
  ├── id                # WOOD-CORE-01
  ├── title             # 이슈 제목
  ├── tags              # [Type, Severity, Direction]
  ├── description       # What
  ├── evidence          # 근거 데이터
  ├── quantification    # 영향 범위 (억 원)
  ├── lever             # 해결 방안
  └── decision_impact   # Proceed/Hold/Kill 영향 여부

ForestMap               # TS 대시보드
  ├── total_qoe_adj     # QoE 조정 합계
  ├── total_wc_adj      # WC 조정 합계
  ├── total_net_debt_adj # Net Debt 조정 합계
  ├── red_flag_count    # High severity 개수
  ├── risk_score        # 리스크 점수
  ├── deal_status       # Proceed / Hold / Kill
  └── issues[]          # 전체 이슈 리스트
```

### Risk Scoring

```python
risk_score = (High 개수 × 3) + (Med 개수 × 1)

Deal Status:
- 0~2: Proceed ✅
- 3~5: Hold (Need Validation) ⚠️
- 6+: Kill or Structure Required 🚫
```

---

## 📚 Issue Library (library_v01.py)

### Common Core Issues (모든 섹터)

| ID | Issue | Severity | Impact |
|----|-------|----------|--------|
| WOOD-CORE-01 | Revenue Cut-off / Recognition | High | EBITDA_Down |
| WOOD-CORE-02 | One-off / Non-recurring Items | Med | EBITDA_Down/Up |
| WOOD-CORE-03 | Capitalized Expenses | High | EBITDA_Down |
| WOOD-CORE-04 | Debt-like Items | High | NetDebt_Up |
| WOOD-CORE-05 | Working Capital Seasonality | Med | WC_Up/Down |

### Sector-Specific Issues

#### Game/Content
- WOOD-GAME-01: Deferred Revenue Misclassification
- WOOD-GAME-02: Live Ops Cost Volatility
- WOOD-GAME-03: IP Dependency Risk

#### Commerce/Platform
- WOOD-COM-01: Gross vs Net Revenue Confusion
- WOOD-COM-02: Refund / Return Provision

#### Manufacturing
- WOOD-MFG-01: Inventory Obsolescence
- WOOD-MFG-02: Customer Concentration Risk

#### Financial Services
- WOOD-FS-01: Yield Normalization Issue

### Usage

```python
from src.engines.wood.library_v01 import get_issue_library

# Load common + sector issues
issues = get_issue_library("Game")  # 5 Common + 3 Game = 8 issues

# Search by keyword
matching_issues = search_issues("revenue", "Commerce")
```

---

## 🚀 Usage

### Basic Workflow

```python
from src.engines.wood import ForestMap, WoodReportGenerator
from src.engines.wood.library_v01 import get_issue_library

# Step 1: Create Forest Map
forest = ForestMap(deal_name="Project_Alpha")

# Step 2: Load issue library
issues = get_issue_library("Game")

# Step 3: Add issues (in practice, filtered by actual DD findings)
forest.issues = issues[:5]  # Top 5 issues

# Step 4: Calculate metrics
forest.calculate_metrics()

# Step 5: Generate report
generator = WoodReportGenerator()
md_report = generator.generate_forest_map_md(forest)
print(md_report)
```

### MIRK ↔ WOOD Integration

```python
from src.engines.wood.interface import MirkInput, WoodOutput

# MIRK provides context
mirk_input = MirkInput(
    deal_name="Project_Beta",
    sector="Commerce",
    deal_rationale="Strategic acquisition",
    valuation_method="EV/EBITDA 8x",
    target_ebitda=50.0,
    constraints=["Management retention", "Close by Q2"]
)

# WOOD processes
forest = process_transaction_services(mirk_input)  # Your logic

# WOOD outputs
wood_output = WoodOutput(
    deal_name=mirk_input.deal_name,
    deal_status=forest.deal_status,
    risk_score=forest.risk_score,
    normalized_ebitda_range="45.0 ~ 48.0",
    net_debt_items=["Leases (15억)", "Deposits (8억)"],
    top_3_levers=[
        "Price: 5-8억 reduction",
        "Net Debt: Add 23억",
        "SPA R&W: Revenue policy"
    ]
)

# MIRK uses output for negotiation
```

---

## 📊 Report Formats

### 1. Forest Map (Markdown)

```markdown
# 🌲 WOOD Forest Map: Project_Alpha

## 📊 Executive Summary
| Metric | Value |
|--------|-------|
| QoE Adjustment | -8.5억 |
| WC Adjustment | +5.2억 |
| Net Debt Adjustment | +15.3억 |
| Red Flags | 3 |
| Risk Score | 11 |
| Deal Status | Hold (Need Validation) |

### 🚨 Critical Actions
- Revenue Recognition: SPA R&W required
- Debt-like Items: Net Debt adjustment +15억
- ...

## 🔍 Top Issues
### 1. 🔴 Revenue Cut-off Issue [WOOD-CORE-01]
...
```

### 2. CSV Bridge (for Excel)

```csv
Line Item,Amount (bn KRW),Category,Evidence,Issue ID
Revenue Cut-off,-6.0,EBITDA_Down,Unbilled revenue spike,WOOD-CORE-01
One-off Costs,+3.5,EBITDA_Up,Consulting fees,WOOD-CORE-02
Leases,+15.0,NetDebt_Up,Operating leases,WOOD-CORE-04
```

### 3. Summary Text (for Telegram)

```
🌲 **WOOD Analysis: Project_Alpha**

**Deal Status:** ⚠️ Hold (Need Validation)
**Risk Score:** 11 (Red Flags: 3)

**Adjustments:**
• QoE: -8.5억
• WC: +5.2억
• Net Debt: +15.3억

**Top Issues:**
🔴 Revenue Cut-off
🔴 Debt-like Items
🟡 WC Seasonality
```

---

## 🧪 Testing

### Run Test Suite

```bash
python -m src.engines.wood.test_transaction_services
```

### Expected Output

```
═══════════════════════════════════════════════════════════════════
🌲 WOOD TRANSACTION SERVICES ENGINE - TEST SUITE
═══════════════════════════════════════════════════════════════════

📚 Testing Issue Library
──────────────────────────────────────────────────────────────────
Available sectors: Common, Game, Content, Commerce, Platform, ...

✅ Common: 5 issues loaded
   Example: WOOD-CORE-01 - Revenue Cut-off / Recognition
✅ Game: 8 issues loaded
   Example: WOOD-CORE-01 - Revenue Cut-off / Recognition
...

🌲 Testing Forest Map
──────────────────────────────────────────────────────────────────
Deal: Project_Alpha
Total Issues: 5
Red Flags: 2
Risk Score: 7
Deal Status: Kill or Structure Required

Adjustments:
  QoE: -10.5억
  WC: +5.0억
  Net Debt: +12.5억
...

✅ ALL TESTS PASSED
```

---

## 🎯 Use Cases

### 1. Sell-side DD (Vendor Due Diligence)

**Scenario:** 매각 준비 단계에서 미리 이슈 점검

```python
forest = ForestMap(deal_name="Company_A_VDD")
issues = get_issue_library("Commerce")

# 예상 질문에 대한 답변 준비
for issue in issues:
    if issue.severity == Severity.HIGH:
        print(f"Prepare for: {issue.title}")
        print(f"Expected question: {issue.description}")
        print(f"Recommended response: {issue.lever}")
```

### 2. Buy-side DD (Acquisition Due Diligence)

**Scenario:** 인수 검토 단계에서 리스크 파악

```python
# MIRK provides target info
mirk_input = MirkInput(
    deal_name="Target_Company",
    sector="Game",
    target_ebitda=80.0,
    focus_areas=["IP risks", "Revenue quality"]
)

# WOOD identifies issues
forest = run_dd_analysis(mirk_input)

# Negotiate based on findings
if forest.deal_status == "Kill or Structure Required":
    print("Recommendation: Structure with Earn-out")
```

### 3. Post-merger Integration (PMI)

**Scenario:** 인수 후 실사 결과 재검증

```python
# Load original DD issues
original_forest = load_forest_map("deal_archive/Project_X.json")

# 100일 후 재점검
current_issues = validate_post_close(original_forest.issues)

# 변화 추적
for issue in current_issues:
    if issue.status == Status.CLOSED:
        print(f"✅ Resolved: {issue.title}")
    else:
        print(f"⚠️ Still open: {issue.title}")
```

---

## 🔧 Customization

### Add Custom Issues

```python
# In library_v01.py
CUSTOM_ISSUES = [
    {
        "id": "WOOD-CUSTOM-01",
        "title": "Your Custom Issue",
        "tags": ["QoE", "High", "EBITDA_Down"],
        "description": "...",
        "evidence": ["..."],
        "quantification": "-5.0 ~ -10.0",
        "lever": "...",
        "quantifiable": True,
        "decision_impact": True
    }
]

# Add to library loader
def get_issue_library(sector: str):
    all_issues = COMMON_ISSUES + CUSTOM_ISSUES
    ...
```

### Customize Risk Scoring

```python
# In generator.py
def calculate_risk_score(self, issues: List[WoodIssue]) -> int:
    score = 0
    for issue in issues:
        if issue.severity == Severity.HIGH:
            if issue.decision_impact:
                score += 5  # Critical
            else:
                score += 3
        elif issue.severity == Severity.MED:
            score += 1
    return score
```

---

## 📖 References

### IB/PE Transaction Services Standards

- **Big 4 TS Reports**: Deloitte, PwC, EY, KPMG
- **QofE (Quality of Earnings)**: EBITDA normalization methodology
- **Net Debt Definitions**: ICAEW guidelines
- **Working Capital**: Normal level vs closing level

### Related MIRKWOOD Modules

- **MIRK (CF)**: Deal origination, valuation
- **X-RAY**: Financial analysis, multiple-based valuation
- **ALPHA**: Teaser generation, deal structuring

---

## 🚧 Roadmap

### v0.2 (Next Release)

- [ ] **Data Source Integration**: Auto-pull from financial statements
- [ ] **AI-powered Issue Detection**: LLM scans for anomalies
- [ ] **Benchmarking**: Compare against industry norms
- [ ] **Waterfall Charts**: Visual EBITDA bridge

### v0.3 (Future)

- [ ] **SPA Generator**: Auto-generate R&W clauses
- [ ] **Earn-out Calculator**: Structure simulator
- [ ] **Risk Heatmap**: Visual dashboard
- [ ] **Multi-language**: English report support

---

## ⚠️ Important Notes

### Limitations

1. **Not a substitute for real DD**: This is a template/playbook, not actual analysis
2. **Quantification is indicative**: Real impacts require detailed audit
3. **Sector coverage**: v0.1 covers 4 sectors, expand as needed

### Best Practices

1. **Always customize**: Tailor issues to specific deal context
2. **Validate with auditors**: Cross-check findings with Big 4
3. **Update library**: Add new issues as you encounter them
4. **Document assumptions**: Quantification basis should be clear

---

## 🤝 Integration with Main Pipeline

### Telegram Command

```python
# In main.py
async def run_wood_ts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /wood_ts [deal_name] [sector]
    """
    deal_name = context.args[0]
    sector = context.args[1] if len(context.args) > 1 else "Common"
    
    # Load library
    issues = get_issue_library(sector)
    
    # Create forest
    forest = ForestMap(deal_name=deal_name)
    forest.issues = issues
    forest.calculate_metrics()
    
    # Generate report
    generator = WoodReportGenerator()
    summary = generator.generate_summary_text(forest)
    
    await update.message.reply_text(summary)
    
    # Send full report
    md_report = generator.generate_forest_map_md(forest)
    # Save to file and send as document
```

### Pipeline Integration

```python
# After X-RAY valuation
xray_result = xray.run_valuation(target)

# Run WOOD TS
wood_input = MirkInput(
    deal_name=target['company_name'],
    sector=target['sector'],
    target_ebitda=xray_result['financials']['op_bn'],
    ...
)

wood_forest = run_wood_ts(wood_input)

# Combine for ALPHA report
alpha_input = {
    'valuation': xray_result,
    'ts_findings': wood_forest,
    'buyers': bravo_result
}

teaser = alpha.generate_teaser(alpha_input)
```

---

*WOOD Transaction Services Engine - MIRKWOOD Partners*
*"We turn risks into levers."*
```
