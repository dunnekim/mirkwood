# 🌲 WOOD DCF Engine

**WOOD** = **W**arranted **O**ff-market **O**pportunity **D**iscounter

MIRKWOOD AI의 DCF (Discounted Cash Flow) 밸류에이션 엔진입니다.

---

## 📋 Overview

WOOD DCF Engine은 시나리오 기반 기업가치 평가를 수행합니다:

- **Base Case**: 정상적인 성장률과 마진
- **Bull Case**: 높은 성장률, 개선된 마진, 낮은 할인율
- **Bear Case**: 저성장/무성장, 압축된 마진, 높은 할인율

### Financial Logic

```
DCF = Σ(FCF_t / (1+WACC)^t) + Terminal Value / (1+WACC)^n

Where:
- FCF = Free Cash Flow = NOPAT (Simplified)
- NOPAT = Operating Profit × (1 - Tax Rate)
- WACC = Risk-Free Rate + Beta × Market Risk Premium
- Terminal Value = FCF_last × (1+g) / (WACC - g)
```

---

## 🏗️ Architecture

### Modular Components

```
wood/
├── config.json                 # 설정 파일 (시나리오, 세율, Peer Group)
├── __init__.py
├── wacc_calculator.py          # WACC 계산 (CAPM 기반)
├── dcf_calculator.py           # DCF 계산 (FCF Projection & PV)
├── terminal_value.py           # 터미널 밸류 계산 (Gordon Growth)
├── scenario_runner.py          # 시나리오별 실행 및 취합
└── test_wood_engine.py         # 테스트 스크립트
```

### Class Structure

1. **WACCCalculator**: CAPM 기반 자기자본비용 계산
2. **DCFCalculator**: 재무제표 Projection 및 현재가치 계산
3. **TerminalValueCalculator**: Perpetual Growth Method 적용
4. **ScenarioRunner**: 전체 시나리오 조율 및 결과 취합
5. **WoodOrchestrator**: 엔진 전체 조율 및 Excel 출력

---

## 🚀 Usage

### Basic Usage

```python
from src.engines.orchestrator import WoodOrchestrator

# Initialize
orchestrator = WoodOrchestrator()

# Run valuation
filepath, summary = orchestrator.run_valuation(
    project_name="Company_Alpha",
    base_revenue=100.0  # 100억 원 매출
)

print(summary)
# Output:
# 🌲 **MIRKWOOD Valuation: Company_Alpha**
# **Valuation Range: 450~650억 원**
# (Base Case: 550억)
# ...
```

### Integration with Main Pipeline

```python
# In main.py or agent code
from src.engines.orchestrator import WoodOrchestrator

def run_full_valuation(lead_data):
    # Step 1: Multiple-based (X-RAY)
    xray_result = xray_agent.run_valuation(lead_data)
    
    # Step 2: DCF-based (WOOD)
    wood = WoodOrchestrator()
    filepath, summary = wood.run_valuation(
        project_name=lead_data['company_name'],
        base_revenue=xray_result['financials']['revenue_bn']
    )
    
    # Step 3: Cross-check
    multiple_value = xray_result['valuation']['target_value']
    dcf_range = parse_value_range(summary)
    
    if abs(multiple_value - dcf_range['base']) / multiple_value < 0.3:
        confidence = "HIGH"
    else:
        confidence = "REVIEW_NEEDED"
    
    return {
        "multiple_value": multiple_value,
        "dcf_range": dcf_range,
        "confidence": confidence,
        "excel_report": filepath
    }
```

### Configuration Customization

`config.json` 파일을 수정하여 설정 조정:

```json
{
  "project_settings": {
    "default_tax_rate": 0.22,        // 법인세율 22%
    "default_currency": "KRW",
    "unit_scale": 1000000            // 억 원 단위
  },
  "scenarios": {
    "Base": {
      "growth_rate": 0.05,           // 5% 성장
      "wacc_premium": 0.0,
      "margin": 0.15                 // 15% 마진
    },
    "Bull": {
      "growth_rate": 0.10,
      "wacc_premium": -0.01,         // WACC 1%p 감소
      "margin": 0.20
    },
    "Bear": {
      "growth_rate": 0.00,           // 0% 성장
      "wacc_premium": 0.02,          // WACC 2%p 증가
      "margin": 0.10
    }
  }
}
```

---

## 🧪 Testing

### Run All Tests

```bash
# From project root
python -m src.engines.wood.test_wood_engine
```

### Test Output Example

```
🧪 WOOD DCF Engine Test
============================================================

[Test 1] Small Beauty Tech Company
🌲 WOOD Engine: Processing 'BeautyTech_Alpha' (Rev: 50억)...
   ✅ Exported: C:\...\vault\reports\BeautyTech_Alpha_Valuation_Package.xlsx

🌲 **MIRKWOOD Valuation: BeautyTech_Alpha**

**Valuation Range: 225~338억 원**
(Base Case: 276억)

**[Base]** Value: **276.4억** (Growth 5%, Margin 15%)
**[Bull]** Value: **337.8억** (Growth 10%, Margin 20%)
**[Bear]** Value: **225.0억** (Growth 0%, Margin 10%)

⚠️ *Indicative estimates for discussion only.*
```

---

## 📊 Excel Output Structure

생성된 Excel 파일 구조:

### Sheet 1: Summary
| Scenario | WACC | Growth | Margin | Value(Bn) |
|----------|------|--------|--------|-----------|
| Base     | 8.5% | 5.0%   | 15.0%  | 276.4     |
| Bull     | 7.5% | 10.0%  | 20.0%  | 337.8     |
| Bear     | 10.5%| 0.0%   | 10.0%  | 225.0     |

### Sheet 2-4: DCF_[Scenario]
| Year | Revenue | OP   | Tax  | NOPAT | FCF  | Discount_Factor | PV_FCF |
|------|---------|------|------|-------|------|-----------------|--------|
| 2026 | 52.5    | 7.9  | 1.7  | 6.1   | 6.1  | 0.922           | 5.6    |
| 2027 | 55.1    | 8.3  | 1.8  | 6.5   | 6.5  | 0.850           | 5.5    |
| ...  | ...     | ...  | ...  | ...   | ...  | ...             | ...    |
| TV   | -       | -    | -    | -     | -    | -               | 186.2  |
| EV   | -       | -    | -    | -     | -    | -               | 276.4  |

---

## 🔧 Troubleshooting

### Error: "WACC must be > Terminal Growth"

**원인**: WACC가 터미널 성장률보다 낮을 때 발생  
**해결**: `config.json`에서 `wacc_premium` 조정 또는 터미널 성장률 감소

### Negative FCF Warning

**원인**: 영업이익이 적자일 때 FCF가 음수  
**해결**: 
- Terminal Value가 0으로 설정됨 (자동 보호)
- 실제 재무제표 확인 필요

### Value Range Too Wide

**원인**: Bull/Bear 시나리오 차이가 클 때  
**해결**: 
- 시나리오 파라미터 조정
- Multiple-based 밸류에이션과 Cross-check
- "REVIEW_NEEDED" 플래그 처리

---

## 📚 References

### Financial Concepts

- **WACC**: Weighted Average Cost of Capital
- **CAPM**: Capital Asset Pricing Model
- **NOPAT**: Net Operating Profit After Tax
- **FCF**: Free Cash Flow
- **Terminal Value**: Perpetual value beyond projection period

### Related Files

- `src/agents/xray_val.py`: Multiple-based 밸류에이션 (비교 대상)
- `src/tools/multiple_lab.py`: Rulebook 기반 Multiple 계산
- `knowledge/valuation_rules.json`: 섹터별 Multiple 기준
- `knowledge/skill_valuation.md`: Valuation 스킬 가이드

---

## ⚠️ Important Notes

### Project Constitution 상충 주의

현재 MIRKWOOD AI Operating Constitution:
> "NO DCF: Discounted Cash Flow is forbidden. Use Multiple-based valuation ONLY."

WOOD DCF Engine은 다음 용도로 제한적 사용:
1. **Cross-check**: Multiple-based 밸류에이션 검증
2. **Investor Presentation**: LP/GP가 DCF 선호 시
3. **Sensitivity Analysis**: 성장률/마진 변화 영향 분석

**Primary Valuation은 여전히 Multiple-based (X-RAY Agent) 사용**

---

## 🛠️ Future Enhancements

- [ ] **Debt Adjustment**: Net Debt 반영하여 Equity Value 계산
- [ ] **Working Capital**: NWC 변동 반영
- [ ] **CapEx**: 자본적지출 반영
- [ ] **Tax Shield**: 부채 세금 효과 반영
- [ ] **Monte Carlo**: 확률적 시나리오 시뮬레이션
- [ ] **Sensitivity Table**: Excel에 민감도 분석 시트 추가

---

*Indicative estimates for discussion only.*
