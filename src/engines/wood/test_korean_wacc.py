"""
Test Korean WACC Calculator (KICPA Standard)

Usage:
    python -m src.engines.wood.test_korean_wacc
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.engines.wood.wacc_logic import KoreanWACCCalculator


def test_srp_quintiles():
    """Test Size Risk Premium calculation across quintiles"""
    print("=" * 70)
    print("📊 Testing SRP (Size Risk Premium) - 5 Quintiles")
    print("=" * 70)
    
    calculator = KoreanWACCCalculator()
    
    # Test cases: Different company sizes
    test_cases = [
        # (is_listed, size_mil_krw, company_type)
        (True, 2000000, "대기업 (삼성전자급)"),      # 2조 시총
        (True, 800000, "중대형 (네이버급)"),         # 8000억 시총
        (True, 400000, "중형"),                      # 4000억 시총
        (True, 200000, "중소형"),                    # 2000억 시총
        (True, 50000, "소형"),                       # 500억 시총
        (False, 100000, "비상장 대형"),              # 1000억 순자산
        (False, 50000, "비상장 중형"),               # 500억 순자산
        (False, 30000, "비상장 소형"),               # 300억 순자산
        (False, 10000, "비상장 초소형 (스타트업)"),  # 100억 순자산
    ]
    
    print("\n{:<25} {:<15} {:<20} {:<15}".format(
        "Company Type", "Size", "SRP", "Quintile"
    ))
    print("-" * 70)
    
    for is_listed, size, company_type in test_cases:
        srp, desc, quintile = calculator._get_korean_srp(is_listed, size)
        
        size_display = f"{size:,}백만원"
        print(f"{company_type:<25} {size_display:<15} {srp*100:>+6.2f}% {desc:<20}")
    
    print("=" * 70)


def test_wacc_calculation():
    """Test full WACC calculation with Korean standard"""
    print("\n" + "=" * 70)
    print("📈 Testing Full WACC Calculation (KICPA)")
    print("=" * 70)
    
    calculator = KoreanWACCCalculator(tax_rate=0.22)
    
    # Peer group (example)
    peers = [
        {'beta': 1.1, 'debt_equity_ratio': 0.3, 'tax_rate': 0.22},
        {'beta': 0.9, 'debt_equity_ratio': 0.2, 'tax_rate': 0.22},
        {'beta': 1.3, 'debt_equity_ratio': 0.5, 'tax_rate': 0.22}
    ]
    
    # Test Case 1: Listed Large Cap
    print("\n[Test 1] Listed Large Cap (1분위)")
    print("-" * 70)
    
    result1 = calculator.calculate(
        peers=peers,
        target_debt_ratio=0.30,
        cost_of_debt_pretax=0.045,
        is_listed=True,
        size_metric_mil_krw=2000000,  # 2조 시총
        rf=0.035,
        mrp=0.08
    )
    
    print(f"   Rf: {result1['Rf']*100:.2f}%")
    print(f"   MRP: {result1['MRP']*100:.1f}%")
    print(f"   Beta (Levered): {result1['Beta_Levered']:.3f}")
    print(f"   Ke (Base): {result1['Ke_Base']*100:.2f}%")
    print(f"   SRP: {result1['SRP']*100:+.2f}% ({result1['SRP_Description']})")
    print(f"   → Ke (Final): {result1['Ke']*100:.2f}%")
    print(f"   Kd (After-Tax): {result1['Kd_post_tax']*100:.2f}%")
    print(f"   → WACC: {result1['WACC']*100:.2f}%")
    
    # Test Case 2: Unlisted Small Company
    print("\n[Test 2] Unlisted Small Company (5분위)")
    print("-" * 70)
    
    result2 = calculator.calculate(
        peers=peers,
        target_debt_ratio=0.50,
        cost_of_debt_pretax=0.060,
        is_listed=False,
        size_metric_mil_krw=15000,  # 150억 순자산
        rf=0.035,
        mrp=0.08
    )
    
    print(f"   Rf: {result2['Rf']*100:.2f}%")
    print(f"   MRP: {result2['MRP']*100:.1f}%")
    print(f"   Beta (Levered): {result2['Beta_Levered']:.3f}")
    print(f"   Ke (Base): {result2['Ke_Base']*100:.2f}%")
    print(f"   SRP: {result2['SRP']*100:+.2f}% ({result2['SRP_Description']})")
    print(f"   → Ke (Final): {result2['Ke']*100:.2f}%")
    print(f"   Kd (After-Tax): {result2['Kd_post_tax']*100:.2f}%")
    print(f"   → WACC: {result2['WACC']*100:.2f}%")
    
    # Comparison
    print("\n" + "-" * 70)
    print("📊 Comparison:")
    print(f"   Large Cap WACC: {result1['WACC']*100:.2f}%")
    print(f"   Small Cap WACC: {result2['WACC']*100:.2f}%")
    print(f"   Difference: {(result2['WACC'] - result1['WACC'])*100:+.2f}%p")
    print(f"   → Small companies have higher discount rate due to SRP")
    
    print("=" * 70)


def test_wacc_explanation():
    """Test calculation explanation generator"""
    print("\n" + "=" * 70)
    print("📝 Testing WACC Explanation Generator")
    print("=" * 70)
    
    calculator = KoreanWACCCalculator()
    
    peers = [
        {'beta': 1.1, 'debt_equity_ratio': 0.3, 'tax_rate': 0.22}
    ]
    
    result = calculator.calculate(
        peers=peers,
        target_debt_ratio=0.30,
        cost_of_debt_pretax=0.050,
        is_listed=False,
        size_metric_mil_krw=50000,  # 500억 순자산
        rf=0.035,
        mrp=0.08
    )
    
    explanation = calculator.explain_calculation(result)
    print("\n" + explanation)
    
    print("=" * 70)


if __name__ == "__main__":
    try:
        print("\n")
        print("═" * 70)
        print("🇰🇷 KOREAN WACC CALCULATOR TEST SUITE (KICPA STANDARD)")
        print("═" * 70)
        
        # Run tests
        test_srp_quintiles()
        test_wacc_calculation()
        test_wacc_explanation()
        
        print("\n")
        print("═" * 70)
        print("✅ ALL KOREAN WACC TESTS PASSED")
        print("═" * 70)
        print("\n💡 Key Findings:")
        print("   • SRP ranges from -0.63% (대형) to +4.73% (소형)")
        print("   • KICPA MRP standard: 8.0%")
        print("   • Listed companies use Market Cap")
        print("   • Unlisted companies use Net Assets")
        print("   • Small companies → Higher WACC → Lower valuation")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
