# 🏦 IB-Grade DCF Model Guide

**Investment Banking Standard DCF Valuation Engine**

---

## 📋 Overview

This module implements **institutional-grade DCF valuation** following Wall Street standards, suitable for:
- M&A advisory presentations
- Fairness opinions
- Equity research reports
- Private equity valuations

### Key Features

✅ **CAPM-based WACC** with proper beta unlevering/re-levering  
✅ **Detailed FCF Waterfall** (EBIT → NOPAT → FCF)  
✅ **Dual Terminal Value** (Gordon Growth + Exit Multiple)  
✅ **Sensitivity Analysis** (WACC × Terminal Growth matrix)  
✅ **Professional Excel Output** (IB presentation quality)

---

## 🧮 Financial Methodology

### 1. WACC Calculation

#### Formula:
```
WACC = Re × (E/V) + Rd × (1 - Tax) × (D/V)
```

#### Process:

**Step 1: Unlever Peer Betas**
```python
βu = βL / [1 + (1 - Tax) × (D/E)]
```

**Step 2: Average Unlevered Beta**
```python
Average βu = mean(βu_peer1, βu_peer2, ...)
```

**Step 3: Re-lever to Target Structure**
```python
βL_target = βu × [1 + (1 - Tax) × (D/E)_target]
```

**Step 4: CAPM for Cost of Equity**
```python
Re = Rf + βL_target × MRP
```
- Rf = Risk-free rate (3.5%)
- MRP = Market risk premium (6.0%)

**Step 5: Weighted Average**
```python
WACC = Re × (E/V) + Rd × (1 - Tax) × (D/V)
```

#### Example:
```
Peer Group:
- Peer A: βL = 0.85, D/E = 0.20
- Peer B: βL = 1.15, D/E = 0.10

Step 1: Unlever
- Peer A: βu = 0.85 / [1 + (1-0.22) × 0.20] = 0.72
- Peer B: βu = 1.15 / [1 + (1-0.22) × 0.10] = 1.06

Step 2: Average βu = (0.72 + 1.06) / 2 = 0.89

Step 3: Re-lever (Target D/E = 0.30)
- βL = 0.89 × [1 + (1-0.22) × 0.30] = 1.10

Step 4: CAPM
- Re = 3.5% + 1.10 × 6.0% = 10.1%

Step 5: WACC (D/V = 0.30/1.30 = 23.1%)
- WACC = 10.1% × 76.9% + 4.5% × (1-0.22) × 23.1% = 8.6%
```

---

### 2. FCF Build-up (The Waterfall)

#### Formula:
```
FCF = EBIT × (1 - Tax) + D&A - Capex - Δ NWC
```

#### Detailed Waterfall:

```
Revenue                           1,000억
× EBITDA Margin (15%)              
= EBITDA                            150억
- D&A (5% of Revenue)               -50억
= EBIT                              100억
- Tax (22% × EBIT)                  -22억
= NOPAT                              78억
+ D&A (add back non-cash)           +50억
- Capex (4% of Revenue)             -40억
- Δ NWC (15% of Δ Revenue)          -15억
= Free Cash Flow                     73억
```

#### Key Parameters (config.json):
```json
"fcf_assumptions": {
  "da_pct_of_revenue": 0.05,      // D&A = 5% of Revenue
  "capex_pct_of_revenue": 0.04,   // Capex = 4% of Revenue
  "nwc_pct_of_revenue": 0.15      // NWC = 15% of Revenue
}
```

---

### 3. Terminal Value (Dual Method)

#### Method 1: Perpetual Growth (Gordon Growth Model)

**Formula:**
```
TV = FCF_n × (1 + g) / (WACC - g)
```

**Example:**
```
Last Year FCF (Year 5) = 100억
Terminal Growth (g) = 2%
WACC = 8.6%

TV = 100억 × (1.02) / (0.086 - 0.02) = 1,545억
```

#### Method 2: Exit Multiple (Reference)

**Formula:**
```
TV = EBITDA_n × Exit Multiple
```

**Example:**
```
Last Year EBITDA (Year 5) = 150억
Exit Multiple = 8.0x

TV = 150억 × 8.0 = 1,200억
```

#### Implied Multiple Check:

```python
Implied EV/EBITDA = TV_gordon / EBITDA_last
                  = 1,545억 / 150억
                  = 10.3x

# Sanity check: Is 10.3x reasonable for this sector?
```

---

### 4. Enterprise Value Calculation

#### Formula:
```
EV = Σ PV(FCF_t) + PV(Terminal Value)
```

#### Example (5-year projection):
```
Year    FCF      Discount Factor    PV(FCF)
2026    73억     0.921              67억
2027    77억     0.848              65억
2028    81억     0.781              63억
2029    85億     0.719              61억
2030    89억     0.662              59억
                                    ---
Sum of PV(FCF)                      315억

Terminal Value (Year 5)             1,545억
× Discount Factor                   × 0.662
= PV(Terminal Value)                1,023억

Enterprise Value                    1,338억
```

---

### 5. Sensitivity Analysis

#### Two-Way Data Table:

**Structure:**
- **X-axis**: WACC variations (±1.0%, ±0.5%, Base, +0.5%, +1.0%)
- **Y-axis**: Terminal Growth variations (1.0%, 1.5%, 2.0%, 2.5%, 3.0%)

**Example Output:**

| Terminal Growth ↓ / WACC → | 7.6% | 8.1% | 8.6% | 9.1% | 9.6% |
|---------------------------|------|------|------|------|------|
| 1.0%                      | 1,205| 1,138| 1,078| 1,024| 975  |
| 1.5%                      | 1,277| 1,204| 1,138| 1,078| 1,024|
| **2.0% (Base)**           | **1,361**|**1,281**|**1,208**|**1,141**|**1,080**|
| 2.5%                      | 1,458| 1,368| 1,287| 1,214| 1,146|
| 3.0%                      | 1,573| 1,468| 1,376| 1,293| 1,218|

**Interpretation:**
- **High sensitivity to WACC**: 1% change → ~15% EV change
- **Moderate sensitivity to Terminal Growth**: 1% change → ~10% EV change
- **Range**: 975억 (worst) ~ 1,573억 (best)

---

## 📊 Excel Output Structure

### Sheet 1: Summary
| Scenario | WACC | Cost of Equity | Cost of Debt (AT) | Enterprise Value |
|----------|------|----------------|-------------------|------------------|
| Base     | 8.6% | 10.1%          | 3.5%              | 1,338억          |
| Bull     | 7.6% | 9.5%           | 3.5%              | 1,587억          |
| Bear     | 10.6%| 11.7%          | 3.5%              | 1,102억          |

### Sheet 2: Assumptions
| Parameter | Value |
|-----------|-------|
| Risk-Free Rate | 3.5% |
| Market Risk Premium | 6.0% |
| Cost of Debt | 4.5% |
| Tax Rate | 22% |
| Terminal Growth Rate | 2.0% |
| Exit Multiple (EV/EBITDA) | 8.0x |
| D&A % of Revenue | 5% |
| Capex % of Revenue | 4% |
| NWC % of Revenue | 15% |

### Sheet 3: DCF_Base (FCF Waterfall)
| Year | Revenue | EBITDA | D&A | EBIT | Tax | NOPAT | Add: D&A | Less: Capex | Less: Δ NWC | FCF | Discount Factor | PV(FCF) |
|------|---------|--------|-----|------|-----|-------|----------|-------------|-------------|-----|-----------------|---------|
| 2026 | 1,050   | 158    | 53  | 105  | 23  | 82    | 53       | 42          | 8           | 85  | 0.921           | 78      |
| ...  | ...     | ...    | ... | ...  | ... | ...   | ...      | ...         | ...         | ... | ...             | ...     |

### Sheet 4: Sensitivity
| Terminal Growth ↓ / WACC → | 7.6% | 8.1% | **8.6%** | 9.1% | 9.6% |
|---------------------------|------|------|----------|------|------|
| 1.0%                      | 1,205| 1,138| 1,078    | 1,024| 975  |
| **2.0%**                  | 1,361| 1,281| **1,208**| 1,141| 1,080|
| 3.0%                      | 1,573| 1,468| 1,376    | 1,293| 1,218|

**Professional Formatting:**
- ✅ Bold headers with blue background
- ✅ Thousand separators (#,##0.0)
- ✅ Percentage format (0.00%)
- ✅ Auto-adjusted column widths
- ✅ Centered headers

---

## 🚀 Usage

### Basic Usage

```python
from src.engines.orchestrator import WoodOrchestrator

# Initialize
orchestrator = WoodOrchestrator()

# Run IB-grade DCF
filepath, summary = orchestrator.run_valuation(
    project_name="Target_Company",
    base_revenue=500.0  # 500억 원
)

print(summary)
# Output:
# 🌲 **MIRKWOOD Valuation: Target_Company**
# **Enterprise Value Range: 1,102~1,587억 원**
# (Base Case: 1,338억)
```

### Telegram Integration

```python
# In main.py
/dcf Target_Company 500

# Output:
# Excel file with IB-grade DCF model automatically sent
```

### Customization via config.json

```json
{
  "project_settings": {
    "risk_free_rate": 0.035,           // Adjust to current 10Y treasury
    "market_risk_premium": 0.06,       // Adjust for market conditions
    "cost_of_debt": 0.045,             // Target's borrowing rate
    "terminal_growth_rate": 0.02,      // Conservative GDP growth
    "exit_multiple_ebitda": 8.0        // Sector-appropriate multiple
  },
  "fcf_assumptions": {
    "da_pct_of_revenue": 0.05,         // Asset-heavy: 7-10%, Asset-light: 3-5%
    "capex_pct_of_revenue": 0.04,      // Maintenance capex assumption
    "nwc_pct_of_revenue": 0.15         // Working capital intensity
  }
}
```

---

## 🧪 Testing

### Run IB-Grade DCF Test

```bash
python -m src.engines.wood.test_ib_dcf
```

### Expected Output

```
======================================================================
🏦 WOOD DCF Engine - IB-Grade Model Test
======================================================================

[Test 1] Small Growth Tech Company
----------------------------------------------------------------------
🌲 WOOD Engine: IB-Grade DCF for 'TechGrowth_Alpha' (Rev: 80억)
      📊 Scenario: Base
         WACC: 8.57%
         EV: 267.5억
      📊 Scenario: Bull
         WACC: 7.57%
         EV: 318.2억
      📊 Scenario: Bear
         WACC: 10.57%
         EV: 220.3억

🌲 **MIRKWOOD Valuation: TechGrowth_Alpha**

**Enterprise Value Range: 220~318억 원**
(Base Case: 268억)

**[Base]** EV: **267.5억** (WACC 8.57%)
**[Bull]** EV: **318.2억** (WACC 7.57%)
**[Bear]** EV: **220.3억** (WACC 10.57%)

⚠️ *IB-grade DCF model with professional FCF build-up and dual terminal value.*

📁 Excel: C:\...\vault\reports\TechGrowth_Alpha_DCF_IB_Grade.xlsx
```

---

## 🎯 Use Cases

### 1. M&A Advisory
- **Seller-side**: Justify asking price with professional DCF
- **Buyer-side**: Validate target's projections
- **Fairness Opinion**: Support fairness committee review

### 2. Private Equity
- **LBO Model**: Use FCF projections for debt capacity
- **Portfolio Company**: Monitor value creation
- **Exit Planning**: Estimate exit value range

### 3. Equity Research
- **Initiation Reports**: Full DCF valuation section
- **Target Price**: Justify price targets with sensitivity
- **Peer Comparison**: Compare implied multiples

### 4. Strategic Planning
- **Investment Committee**: Present capex decisions
- **Board Meetings**: Show value impact scenarios
- **Budget Planning**: Link strategy to value creation

---

## ⚠️ Important Notes

### Limitations

1. **Simplified FCF**: No explicit modeling of:
   - Deferred taxes
   - Stock-based compensation
   - One-time items / restructuring costs

2. **Static Capital Structure**: Assumes constant D/E ratio
   - Real LBOs have dynamic debt paydown schedules

3. **No Equity Bridge**: Missing:
   - Net Debt adjustment
   - Minority interest
   - Pension liabilities

### When to Use

✅ **Good for:**
- Early-stage M&A discussions
- Quick valuation ranges
- Management presentations
- Teaching/learning DCF

❌ **NOT sufficient for:**
- Binding fairness opinions (need full audit)
- Complex capital structures (convertibles, warrants)
- Distressed situations (need APV model)

---

## 📚 References

### Financial Textbooks
- **Damodaran on Valuation** (Aswath Damodaran)
- **Investment Banking** (Rosenbaum & Pearl)
- **Valuation** (McKinsey & Company)

### Industry Standards
- **CFA Level II**: Equity Valuation (DCF models)
- **IB Training Programs**: Goldman Sachs, Morgan Stanley, JPM

### Related Files
- `src/engines/wood/wacc_calculator.py`: Detailed WACC logic
- `src/engines/wood/dcf_calculator.py`: FCF projection engine
- `src/engines/wood/terminal_value.py`: Terminal value methods
- `knowledge/valuation_rules.json`: Sector-specific multiples

---

## 🔧 Advanced Customization

### Add Custom Scenarios

```json
// In config.json
"scenarios": {
  "Aggressive": {
    "growth_rate": 0.15,
    "wacc_premium": -0.02,
    "ebitda_margin": 0.25,
    "target_debt_ratio": 0.20
  }
}
```

### Change Projection Period

```python
# In orchestrator.py
fcf_df = self._build_fcf_projection(
    base_revenue, 
    scenario_params, 
    projection_years=7  # Change from 5 to 7
)
```

### Add Equity Value Calculation

```python
# After calculating EV
net_debt = 100  # 100억 debt
equity_value = enterprise_value - net_debt
shares_outstanding = 10  # million shares
price_per_share = (equity_value * 100) / shares_outstanding  # in KRW
```

---

*IB-Grade DCF Model by MIRKWOOD Partners*
