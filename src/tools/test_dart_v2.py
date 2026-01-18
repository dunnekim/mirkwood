"""
Test DART Reader V2.0

Usage:
    python -m src.tools.test_dart_v2
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.tools.dart_reader import DartReader


def test_dart_reader():
    """Test DART Reader with various companies"""
    print("=" * 70)
    print("🧪 Testing DART Reader V2.0")
    print("=" * 70)
    
    reader = DartReader()
    
    # Test cases
    test_companies = [
        ("모비릭스", "Game company - uses '영업수익'"),
        ("삼성전자", "Large cap - uses '매출액'"),
        ("카카오", "Tech company"),
        ("넥슨", "Game company"),
        ("엔씨소프트", "Game company"),
    ]
    
    results = []
    
    for company_name, description in test_companies:
        print(f"\n{'─'*70}")
        print(f"Testing: {company_name} ({description})")
        print(f"{'─'*70}")
        
        result = reader.get_financial_summary(company_name)
        
        if result:
            print(f"\n✅ SUCCESS")
            print(f"   Revenue: {result['revenue_bn']:.1f}억 원")
            print(f"   OP: {result['op_bn']:.1f}억 원")
            print(f"   Source: {result['source']}")
            print(f"   Period: {result.get('period', 'N/A')}")
            
            results.append({
                'company': company_name,
                'success': True,
                'revenue': result['revenue_bn'],
                'op': result['op_bn'],
                'source': result['source']
            })
        else:
            print(f"\n❌ FAILED")
            results.append({
                'company': company_name,
                'success': False
            })
    
    # Summary
    print(f"\n{'='*70}")
    print("📊 Test Summary")
    print(f"{'='*70}")
    
    success_count = sum(1 for r in results if r['success'])
    print(f"\nTotal: {len(results)} tests")
    print(f"Success: {success_count}")
    print(f"Failed: {len(results) - success_count}")
    
    print(f"\n{'─'*70}")
    print("Successful Results:")
    print(f"{'─'*70}")
    
    for r in results:
        if r['success']:
            print(f"✅ {r['company']}: {r['revenue']:.1f}억 (Source: {r['source']})")
    
    if success_count < len(results):
        print(f"\n{'─'*70}")
        print("Failed Results:")
        print(f"{'─'*70}")
        
        for r in results:
            if not r['success']:
                print(f"❌ {r['company']}")
    
    print(f"\n{'='*70}")
    
    # Specific check for 모비릭스
    mobilis = next((r for r in results if r['company'] == '모비릭스'), None)
    if mobilis and mobilis['success']:
        if mobilis['revenue'] > 0:
            print("✅ 모비릭스 영업수익 인식 성공!")
            print(f"   Revenue: {mobilis['revenue']:.1f}억 (NOT 0억)")
        else:
            print("⚠️ 모비릭스 데이터는 찾았지만 매출이 0억입니다.")
    else:
        print("❌ 모비릭스 데이터 조회 실패")
    
    print("=" * 70)


if __name__ == "__main__":
    try:
        test_dart_reader()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
