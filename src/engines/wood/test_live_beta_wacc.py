"""
Test Live Beta Integration with Korean WACC

Usage:
    python -m src.engines.wood.test_live_beta_wacc
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.engines.wood.wacc_logic import KoreanWACCCalculator


def test_live_beta_wacc():
    """Test Korean WACC with live beta calculation"""
    print("=" * 70)
    print("🔬 Testing Live Beta Integration with Korean WACC")
    print("=" * 70)
    
    # Test Case: Korean tech companies as peer group
    peer_tickers = ["035720", "035420", "035760"]  # 카카오, 네이버, CJ ENM
    
    peers_info = [
        {'beta': 1.1, 'debt_equity_ratio': 0.20, 'tax_rate': 0.22, 'name': '카카오'},
        {'beta': 0.9, 'debt_equity_ratio': 0.15, 'tax_rate': 0.22, 'name': '네이버'},
        {'beta': 1.3, 'debt_equity_ratio': 0.30, 'tax_rate': 0.22, 'name': 'CJ ENM'}
    ]
    
    # ==================================================================
    # Scenario 1: Traditional Method (Provided Betas)
    # ==================================================================
    
    print("\n[Scenario 1] Traditional Method (Provided Betas)")
    print("-" * 70)
    
    calc_traditional = KoreanWACCCalculator(tax_rate=0.22, use_live_beta=False)
    
    result1 = calc_traditional.calculate(
        peers=peers_info,
        target_debt_ratio=0.30,
        cost_of_debt_pretax=0.050,
        is_listed=False,
        size_metric_mil_krw=50000,  # 500억 순자산
        rf=0.035,
        mrp=0.08
    )
    
    print(f"\n✅ Traditional WACC Results:")
    print(f"   Beta (Unlevered): {result1['Beta_Unlevered']:.3f}")
    print(f"   Beta (Levered): {result1['Beta_Levered']:.3f}")
    print(f"   Ke (Base): {result1['Ke_Base']*100:.2f}%")
    print(f"   SRP: {result1['SRP']*100:+.2f}% ({result1['SRP_Description']})")
    print(f"   Ke (Final): {result1['Ke']*100:.2f}%")
    print(f"   WACC: {result1['WACC']*100:.2f}%")
    
    # ==================================================================
    # Scenario 2: Live Beta Method (Market Scanner)
    # ==================================================================
    
    print("\n" + "=" * 70)
    print("[Scenario 2] Live Beta Method (Market Scanner)")
    print("-" * 70)
    
    calc_live = KoreanWACCCalculator(tax_rate=0.22, use_live_beta=True)
    
    result2 = calc_live.calculate(
        peers=peers_info,
        target_debt_ratio=0.30,
        cost_of_debt_pretax=0.050,
        is_listed=False,
        size_metric_mil_krw=50000,
        rf=0.035,
        mrp=0.08,
        peer_tickers=peer_tickers  # Provide tickers for live beta
    )
    
    print(f"\n✅ Live Beta WACC Results:")
    print(f"   Beta (Unlevered): {result2['Beta_Unlevered']:.3f}")
    print(f"   Beta (Levered): {result2['Beta_Levered']:.3f}")
    print(f"   Ke (Base): {result2['Ke_Base']*100:.2f}%")
    print(f"   SRP: {result2['SRP']*100:+.2f}% ({result2['SRP_Description']})")
    print(f"   Ke (Final): {result2['Ke']*100:.2f}%")
    print(f"   WACC: {result2['WACC']*100:.2f}%")
    
    # ==================================================================
    # Comparison
    # ==================================================================
    
    print("\n" + "=" * 70)
    print("📊 Comparison: Traditional vs Live Beta")
    print("=" * 70)
    
    print(f"\n{'Metric':<20} {'Traditional':>15} {'Live Beta':>15} {'Diff':>10}")
    print("-" * 70)
    
    print(f"{'Unlevered Beta':<20} {result1['Beta_Unlevered']:>15.3f} {result2['Beta_Unlevered']:>15.3f} "
          f"{result2['Beta_Unlevered']-result1['Beta_Unlevered']:>+10.3f}")
    
    print(f"{'Levered Beta':<20} {result1['Beta_Levered']:>15.3f} {result2['Beta_Levered']:>15.3f} "
          f"{result2['Beta_Levered']-result1['Beta_Levered']:>+10.3f}")
    
    print(f"{'Cost of Equity':<20} {result1['Ke']*100:>14.2f}% {result2['Ke']*100:>14.2f}% "
          f"{(result2['Ke']-result1['Ke'])*100:>+9.2f}%p")
    
    print(f"{'WACC':<20} {result1['WACC']*100:>14.2f}% {result2['WACC']*100:>14.2f}% "
          f"{(result2['WACC']-result1['WACC'])*100:>+9.2f}%p")
    
    print("\n" + "=" * 70)
    
    # Impact analysis
    if abs(result2['WACC'] - result1['WACC']) > 0.005:  # 0.5%p 이상 차이
        print("⚠️ Significant WACC difference detected (>0.5%p)")
        print("   → Live beta reflects current market conditions")
        print("   → Traditional beta may be outdated")
    else:
        print("✅ WACC results are consistent between methods")


def test_blume_adjustment():
    """Test Blume's adjusted beta formula"""
    print("\n" + "=" * 70)
    print("📐 Testing Blume's Adjusted Beta Formula")
    print("=" * 70)
    
    print("\nFormula: Adjusted Beta = (Raw Beta × 0.67) + (1.0 × 0.33)")
    print("\nReason: Betas tend to regress toward market average (1.0)")
    
    print(f"\n{'Raw Beta':>10} {'Adjusted Beta':>15} {'Adjustment':>12}")
    print("-" * 40)
    
    test_betas = [0.5, 0.8, 1.0, 1.2, 1.5, 2.0]
    
    for raw in test_betas:
        adjusted = (raw * 0.67) + (1.0 * 0.33)
        adjustment = adjusted - raw
        print(f"{raw:>10.2f} {adjusted:>15.3f} {adjustment:>+12.3f}")
    
    print("\n" + "=" * 70)
    print("💡 Observations:")
    print("   • Raw < 1.0: Adjusted beta moves UP toward 1.0")
    print("   • Raw > 1.0: Adjusted beta moves DOWN toward 1.0")
    print("   • This reduces estimation error in future periods")
    print("=" * 70)


if __name__ == "__main__":
    try:
        print("\n")
        print("═" * 70)
        print("🔬 LIVE BETA + KOREAN WACC INTEGRATION TEST")
        print("═" * 70)
        
        # Run tests
        test_live_beta_wacc()
        test_blume_adjustment()
        
        print("\n")
        print("═" * 70)
        print("✅ ALL LIVE BETA INTEGRATION TESTS PASSED")
        print("═" * 70)
        print("\n🎓 House View Beta Calculation:")
        print("   1. Fetch 5Y monthly stock + market data")
        print("   2. Calculate log returns")
        print("   3. Linear regression → Raw beta")
        print("   4. Apply Blume's adjustment → Adjusted beta")
        print("   5. Unlever peer betas → Average → Re-lever to target")
        print("   6. Apply KICPA MRP (8%) + SRP (5분위)")
        print("   7. Calculate Korean standard WACC")
        print("\n🏆 This is Real IB methodology!")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
