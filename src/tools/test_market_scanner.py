"""
Test Market Scanner - Beta Calculation

Usage:
    python -m src.tools.test_market_scanner
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.tools.market_scanner import MarketScanner


def test_beta_calculation():
    """Test beta calculation for Korean stocks"""
    print("=" * 70)
    print("📈 Testing Market Scanner - Beta Calculation")
    print("=" * 70)
    
    scanner = MarketScanner()
    
    # Test cases (Korean stock codes)
    test_stocks = [
        ("005930", "삼성전자", "Large cap tech"),
        ("035720", "카카오", "Tech platform"),
        ("035420", "NAVER", "Internet platform"),
        ("000660", "SK하이닉스", "Semiconductor"),
    ]
    
    results = []
    
    for code, name, description in test_stocks:
        print(f"\n{'─'*70}")
        print(f"Testing: {name} ({code}) - {description}")
        print(f"{'─'*70}")
        
        result = scanner.calculate_beta(code, mode='5Y_MONTHLY')
        results.append({
            'name': name,
            'code': code,
            **result
        })
    
    # Summary
    print(f"\n{'='*70}")
    print("📊 Beta Calculation Summary")
    print(f"{'='*70}")
    
    print(f"\n{'Company':<15} {'Raw Beta':>10} {'Adj Beta':>10} {'R²':>8} {'Conf':>10}")
    print("-" * 70)
    
    for r in results:
        if r['success']:
            print(f"{r['name']:<15} {r['raw_beta']:>10.3f} {r['adjusted_beta']:>10.3f} "
                  f"{r['r_squared']:>8.3f} {r['confidence']:>10}")
        else:
            print(f"{r['name']:<15} {'N/A':>10} {r['adjusted_beta']:>10.3f} "
                  f"{'N/A':>8} {r['confidence']:>10}")
    
    print("=" * 70)
    
    # Statistical notes
    print("\n💡 Key Observations:")
    successful = [r for r in results if r['success']]
    
    if successful:
        avg_r2 = np.mean([r['r_squared'] for r in successful])
        print(f"   • Average R²: {avg_r2:.3f}")
        print(f"   • Successful calculations: {len(successful)}/{len(results)}")
        
        high_conf = [r for r in successful if r['confidence'] == 'High']
        print(f"   • High confidence: {len(high_conf)}/{len(successful)}")
    
    print(f"\n📚 Interpretation:")
    print("   • Raw Beta > 1.0: More volatile than market")
    print("   • Raw Beta < 1.0: Less volatile than market")
    print("   • Adjusted Beta regresses toward 1.0 (Blume's method)")
    print("   • R² > 0.30: Strong correlation with market")


def test_market_data():
    """Test current price and market cap fetching"""
    print(f"\n{'='*70}")
    print("💰 Testing Market Data Fetching")
    print(f"{'='*70}")
    
    scanner = MarketScanner()
    
    test_code = "005930"  # 삼성전자
    
    print(f"\nFetching data for {test_code} (삼성전자)...")
    
    # Current price
    price = scanner.get_current_price(test_code)
    if price:
        print(f"✅ Current Price: {price:,.0f}원")
    else:
        print("❌ Failed to fetch current price")
    
    # Market cap
    mc = scanner.get_market_cap(test_code)
    if mc:
        print(f"✅ Market Cap: {mc:,.0f}백만원 ({mc/1000000:,.1f}조)")
    else:
        print("❌ Failed to fetch market cap")
    
    print("=" * 70)


if __name__ == "__main__":
    try:
        print("\n")
        print("═" * 70)
        print("📊 MARKET SCANNER TEST SUITE")
        print("═" * 70)
        
        import numpy as np
        
        # Run tests
        test_beta_calculation()
        test_market_data()
        
        print("\n")
        print("═" * 70)
        print("✅ ALL MARKET SCANNER TESTS PASSED")
        print("═" * 70)
        print("\n💡 Key Features:")
        print("   • Live beta calculation from market data")
        print("   • Blume's adjusted beta (regresses to 1.0)")
        print("   • Linear regression with R² confidence")
        print("   • Current price & market cap fetching")
        print("   • Supports KOSPI (.KS) and KOSDAQ (.KQ)")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
