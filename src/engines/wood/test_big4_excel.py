"""
Test Big 4 Excel Formatting

Usage:
    python -m src.engines.wood.test_big4_excel
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.engines.orchestrator import WoodOrchestrator


def test_big4_excel():
    """Test Big 4 style Excel generation"""
    print("=" * 70)
    print("📊 Testing Big 4 Excel Formatting")
    print("=" * 70)
    
    orchestrator = WoodOrchestrator()
    
    # Test with different data sources
    test_cases = [
        {
            "project_name": "TestCo_DART",
            "base_revenue": 100.0,
            "data_source": "DART 2024.3Q"
        },
        {
            "project_name": "TestCo_WebSearch",
            "base_revenue": 50.0,
            "data_source": "Estimate (Web Search)"
        },
        {
            "project_name": "TestCo_Manual",
            "base_revenue": 200.0,
            "data_source": "User Input (Manual Override)"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n{'─'*70}")
        print(f"Test Case: {test_case['project_name']}")
        print(f"{'─'*70}")
        
        filepath, summary = orchestrator.run_valuation(
            project_name=test_case['project_name'],
            base_revenue=test_case['base_revenue'],
            data_source=test_case['data_source']
        )
        
        print(f"\n✅ Excel generated: {filepath}")
        print(f"\n📋 Summary:\n{summary}")
    
    print(f"\n{'='*70}")
    print("✅ All tests completed!")
    print("\n💡 Open the Excel files to verify:")
    print("   • Blue font for assumptions (WACC, Growth, Margin)")
    print("   • Black font for calculated values")
    print("   • Data source in top-right corner")
    print("   • Professional borders and alignment")
    print("   • Thousand separators for numbers")
    print("=" * 70)


if __name__ == "__main__":
    try:
        test_big4_excel()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
