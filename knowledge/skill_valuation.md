# Skill: Hybrid Valuation & Calibration

## Objective
Calculate a credible valuation range by combining Rulebook (static) and Web Data (dynamic).

## Process
1. **Market Evidence Check**: Search for recent M&A deals or peer trading multiples.
2. **Base Multiple Selection**:
   - If market evidence is "High" confidence: Use (Market * 0.7) + (Rulebook * 0.3).
   - If no market evidence: Use Rulebook Mid-point.
3. **G-P-L Adjustment**:
   - G (Growth): Add 0.5x to multiple if CAGR > 15%.
   - P (Profit): Adjust ±0.2x based on margin gap vs industry typical.
   - L (Leverage): Discount if ND/EBITDA > 4.0x.
4. **Triangulation**: Present the final value as a range between (Conservative) and (Optimistic).