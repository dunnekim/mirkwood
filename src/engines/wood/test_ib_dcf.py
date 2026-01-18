"""
Test script for IB-Grade DCF Model

Usage:
    python -m src.engines.wood.test_ib_dcf
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.engines.orchestrator import WoodOrchestrator


def test_ib_grade_dcf():
    """
    Test IB-Grade DCF with realistic scenarios
    """
    print("=" * 70)
    print("🏦 WOOD DCF Engine - IB-Grade Model Test")
    print("=" * 70)
    
    orchestrator = WoodOrchestrator()
    
    # Test Case 1: Small Growth Company
    print("\n[Test 1] Small Growth Tech Company")
    print("-" * 70)
    filepath1, summary1 = orchestrator.run_valuation(
        project_name="TechGrowth_Alpha",
        base_revenue=80.0  # 80억 원
    )
    print("\n" + summary1)
    print(f"\n📁 Excel: {filepath1}")
    
    # Test Case 2: Mid-sized Profitable Company
    print("\n" + "=" * 70)
    print("[Test 2] Mid-sized Manufacturing Company")
    print("-" * 70)
    filepath2, summary2 = orchestrator.run_valuation(
        project_name="Manufacturing_Beta",
        base_revenue=300.0  # 300억 원
    )
    print("\n" + summary2)
    print(f"\n📁 Excel: {filepath2}")
    
    # Test Case 3: Large Enterprise
    print("\n" + "=" * 70)
    print("[Test 3] Large Consumer Brand")
    print("-" * 70)
    filepath3, summary3 = orchestrator.run_valuation(
        project_name="ConsumerBrand_Gamma",
        base_revenue=800.0  # 800억 원
    )
    print("\n" + summary3)
    print(f"\n📁 Excel: {filepath3}")
    
    print("\n" + "=" * 70)
    print("✅ All IB-Grade DCF Tests Completed!")
    print("=" * 70)
    print("\n📊 Excel Files Generated with:")
    print("   • Professional formatting (Bold headers, colors)")
    print("   • Detailed FCF waterfall (EBIT → D&A → Capex → NWC)")
    print("   • WACC calculation (Unlevered Beta → Re-levering)")
    print("   • Dual Terminal Value (Gordon Growth + Exit Multiple)")
    print("   • Sensitivity Analysis (WACC × Terminal Growth)")
    print("\n🎯 Next Step: Open Excel files to verify institutional quality")


def explain_methodology():
    """
    Print detailed methodology explanation
    """
    print("\n" + "=" * 70)
    print("📚 IB-GRADE DCF METHODOLOGY")
    print("=" * 70)
    
    methodology = """
    
1. WACC CALCULATION (CAPM-based)
   
   Step 1: Unlever peer betas
      βu = βL / [1 + (1 - Tax) × (D/E)]
   
   Step 2: Calculate average unlevered beta
   
   Step 3: Re-lever to target capital structure
      βL = βu × [1 + (1 - Tax) × (D/E)]
   
   Step 4: Apply CAPM
      Re = Rf + β × MRP
   
   Step 5: Calculate WACC
      WACC = Re × (E/V) + Rd × (1-Tax) × (D/V)

2. FCF BUILD-UP (The Waterfall)
   
   Revenue
   × EBITDA Margin
   = EBITDA
   - D&A
   = EBIT
   - Tax (EBIT × Tax Rate)
   = NOPAT
   + D&A (add back non-cash)
   - Capex
   - Δ NWC (Change in Net Working Capital)
   = Free Cash Flow

3. TERMINAL VALUE (Dual Method)
   
   Method 1 (Primary): Gordon Growth Model
      TV = FCF_last × (1 + g) / (WACC - g)
   
   Method 2 (Reference): Exit Multiple
      TV = EBITDA_last × Exit Multiple
   
   Implied Multiple Check:
      Implied EV/EBITDA = TV_gordon / EBITDA_last

4. ENTERPRISE VALUE
   
   EV = Σ PV(FCF) + PV(Terminal Value)
   
   where:
      PV(FCF_t) = FCF_t / (1 + WACC)^t
      PV(TV) = TV / (1 + WACC)^n

5. SENSITIVITY ANALYSIS
   
   Two-way sensitivity table:
   - X-axis: WACC variations (±0.5%, ±1.0%)
   - Y-axis: Terminal Growth variations (±0.5%, ±1.0%)
   - Output: Enterprise Value matrix

"""
    
    print(methodology)
    print("=" * 70)


if __name__ == "__main__":
    try:
        # Explain methodology first
        explain_methodology()
        
        # Run tests
        input("\nPress Enter to run DCF tests...")
        test_ib_grade_dcf()
        
    except Exception as e:
        print(f"\n❌ Test failed with error:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
