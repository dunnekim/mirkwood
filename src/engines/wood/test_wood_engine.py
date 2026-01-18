"""
Test script for WOOD DCF Engine

Usage:
    python -m src.engines.wood.test_wood_engine
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.engines.orchestrator import WoodOrchestrator


def test_basic_valuation():
    """기본 DCF 밸류에이션 테스트"""
    print("=" * 60)
    print("🧪 WOOD DCF Engine Test")
    print("=" * 60)
    
    # Initialize orchestrator
    orchestrator = WoodOrchestrator()
    
    # Test Case 1: Small Company
    print("\n[Test 1] Small Beauty Tech Company")
    filepath1, summary1 = orchestrator.run_valuation(
        project_name="BeautyTech_Alpha",
        base_revenue=50.0  # 50억 원 매출
    )
    print(summary1)
    print(f"📁 File saved: {filepath1}")
    
    # Test Case 2: Mid-sized Company
    print("\n" + "=" * 60)
    print("[Test 2] Mid-sized Manufacturing Company")
    filepath2, summary2 = orchestrator.run_valuation(
        project_name="Manufacturing_Beta",
        base_revenue=200.0  # 200억 원 매출
    )
    print(summary2)
    print(f"📁 File saved: {filepath2}")
    
    # Test Case 3: Large Company
    print("\n" + "=" * 60)
    print("[Test 3] Large Tech Company")
    filepath3, summary3 = orchestrator.run_valuation(
        project_name="TechGiant_Gamma",
        base_revenue=1000.0  # 1000억 원 매출
    )
    print(summary3)
    print(f"📁 File saved: {filepath3}")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed successfully!")
    print("=" * 60)


def test_individual_components():
    """개별 컴포넌트 테스트"""
    print("\n" + "=" * 60)
    print("🔬 Testing Individual Components")
    print("=" * 60)
    
    from src.engines.wood.wacc_calculator import WACCCalculator
    from src.engines.wood.dcf_calculator import DCFCalculator
    from src.engines.wood.terminal_value import TerminalValueCalculator
    
    # Test WACC Calculator
    print("\n[1] WACC Calculator")
    wacc_calc = WACCCalculator()
    peer_group = [
        {"name": "Peer_A", "beta": 0.85, "debt_ratio": 0.2},
        {"name": "Peer_B", "beta": 1.15, "debt_ratio": 0.1}
    ]
    base_wacc = wacc_calc.calculate_base_wacc(peer_group)
    print(f"   Base WACC: {base_wacc*100:.2f}%")
    
    bull_wacc = wacc_calc.apply_scenario_adjustment(base_wacc, -0.01)
    print(f"   Bull WACC: {bull_wacc*100:.2f}%")
    
    bear_wacc = wacc_calc.apply_scenario_adjustment(base_wacc, 0.02)
    print(f"   Bear WACC: {bear_wacc*100:.2f}%")
    
    # Test DCF Calculator
    print("\n[2] DCF Calculator")
    dcf_calc = DCFCalculator(tax_rate=0.22)
    proj_df = dcf_calc.project_financials(
        base_revenue=100.0,
        growth_rate=0.10,
        margin=0.15
    )
    print("   5-Year Projection:")
    print(proj_df.to_string(index=False))
    
    # Test Terminal Value Calculator
    print("\n[3] Terminal Value Calculator")
    tv_calc = TerminalValueCalculator()
    last_fcf = proj_df['FCF'].iloc[-1]
    tv_result = tv_calc.calculate(last_fcf, base_wacc)
    print(f"   Terminal Value: {tv_result['terminal_value']:.2f}억")
    print(f"   Terminal Growth: {tv_result['terminal_growth']*100:.1f}%")
    print(f"   Sanity Check: {tv_result['sanity_check']}")
    
    print("\n✅ Component tests completed!")


if __name__ == "__main__":
    try:
        # Run basic valuation tests
        test_basic_valuation()
        
        # Run component tests
        test_individual_components()
        
    except Exception as e:
        print(f"\n❌ Test failed with error:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
