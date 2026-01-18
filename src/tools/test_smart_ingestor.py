"""
Test SmartFinancialIngestor

Usage:
    python -m src.tools.test_smart_ingestor
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.tools.smart_ingestor import SmartFinancialIngestor


def test_ingestor():
    """Test SmartIngestor with various companies"""
    print("=" * 70)
    print("🔬 Testing SmartFinancialIngestor")
    print("=" * 70)
    
    ingestor = SmartFinancialIngestor()
    
    # Test cases
    companies = [
        "삼성전자",      # Should work with DART
        "카카오",        # Should work with DART
        "리터니티",      # May need web search
        "모비릭스"       # May need web search
    ]
    
    for company in companies:
        print(f"\n{'─'*70}")
        print(f"Testing: {company}")
        print(f"{'─'*70}")
        
        result = ingestor.ingest(company)
        
        print(f"\n📊 Result:")
        print(f"   Revenue: {result.get('revenue', 'N/A')}억 원")
        print(f"   OP: {result.get('op', 'N/A')}억 원")
        print(f"   EBITDA: {result.get('ebitda', 'N/A')}억 원")
        print(f"   Source: {result.get('source', 'N/A')}")
        print(f"   Confidence: {result.get('confidence', 'N/A')}")
        print(f"   Description: {result.get('description', 'N/A')}")
        print(f"   Requires Input: {result.get('requires_input', False)}")
    
    print(f"\n{'='*70}")
    print("✅ Test completed")
    print("=" * 70)


if __name__ == "__main__":
    try:
        test_ingestor()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
