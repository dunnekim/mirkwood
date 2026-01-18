"""
Test script for WOOD Transaction Services Engine

Usage:
    python -m src.engines.wood.test_transaction_services
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.engines.wood.schema import ForestMap, Status
from src.engines.wood.library_v01 import get_issue_library, get_all_sectors
from src.engines.wood.generator import WoodReportGenerator
from src.engines.wood.interface import MirkInput, WoodOutput


def test_issue_library():
    """Test issue library loading"""
    print("=" * 70)
    print("📚 Testing Issue Library")
    print("=" * 70)
    
    sectors = get_all_sectors()
    print(f"\nAvailable sectors: {', '.join(sectors)}\n")
    
    for sector in ["Common", "Game", "Commerce", "Manufacturing"]:
        issues = get_issue_library(sector)
        print(f"✅ {sector}: {len(issues)} issues loaded")
        
        # Show first issue
        if issues:
            first = issues[0]
            print(f"   Example: {first.id} - {first.title}")
    
    print("\n" + "=" * 70)


def test_forest_map():
    """Test Forest Map creation and metrics"""
    print("\n" + "=" * 70)
    print("🌲 Testing Forest Map")
    print("=" * 70)
    
    # Create Forest Map
    forest = ForestMap(deal_name="Project_Alpha")
    
    # Load issues (Game sector)
    issues = get_issue_library("Game")
    
    # Add first 5 issues to forest
    forest.issues = issues[:5]
    
    # Calculate metrics
    forest.calculate_metrics()
    
    print(f"\nDeal: {forest.deal_name}")
    print(f"Total Issues: {len(forest.issues)}")
    print(f"Red Flags: {forest.red_flag_count}")
    print(f"Risk Score: {forest.risk_score}")
    print(f"Deal Status: {forest.deal_status}")
    print(f"\nAdjustments:")
    print(f"  QoE: {forest.total_qoe_adj:+.1f}억")
    print(f"  WC: {forest.total_wc_adj:+.1f}억")
    print(f"  Net Debt: {forest.total_net_debt_adj:+.1f}억")
    
    print("\n" + "=" * 70)
    
    return forest


def test_report_generation(forest: ForestMap):
    """Test report generation"""
    print("\n" + "=" * 70)
    print("📝 Testing Report Generation")
    print("=" * 70)
    
    generator = WoodReportGenerator()
    
    # 1. Markdown Report
    print("\n[1] Generating Markdown Report...")
    md_report = generator.generate_forest_map_md(forest)
    print(f"✅ Generated {len(md_report)} characters")
    print("\n--- Preview (first 500 chars) ---")
    print(md_report[:500] + "...")
    
    # 2. CSV Bridge
    print("\n[2] Generating CSV Bridge...")
    csv_data = generator.generate_bridge_csv(forest.issues)
    print(f"✅ Generated CSV with {len(csv_data.split(chr(10)))} lines")
    print("\n--- Preview ---")
    print(csv_data[:300] + "...")
    
    # 3. Summary Text
    print("\n[3] Generating Summary Text...")
    summary = generator.generate_summary_text(forest)
    print(f"✅ Generated summary:")
    print(summary)
    
    print("\n" + "=" * 70)


def test_mirk_interface():
    """Test MIRK ↔ WOOD interface"""
    print("\n" + "=" * 70)
    print("🔄 Testing MIRK Interface")
    print("=" * 70)
    
    # MIRK Input
    mirk_input = MirkInput(
        deal_name="Project_Beta",
        sector="Commerce",
        deal_rationale="Strategic acquisition for market expansion",
        valuation_method="EV/EBITDA 8.0x",
        target_ebitda=50.0,
        target_net_debt=20.0,
        constraints=["Management retention required", "Close by Q2 2026"],
        focus_areas=["Revenue quality", "Customer concentration"]
    )
    
    print("\n📥 MIRK Input:")
    print(f"  Deal: {mirk_input.deal_name}")
    print(f"  Sector: {mirk_input.sector}")
    print(f"  Rationale: {mirk_input.deal_rationale}")
    print(f"  Constraints: {len(mirk_input.constraints)}")
    
    # Simulate WOOD processing
    issues = get_issue_library(mirk_input.sector)
    forest = ForestMap(deal_name=mirk_input.deal_name)
    forest.issues = issues[:7]
    forest.calculate_metrics()
    
    # WOOD Output
    wood_output = WoodOutput(
        deal_name=mirk_input.deal_name,
        deal_status=forest.deal_status,
        risk_score=forest.risk_score,
        normalized_ebitda_range=f"{mirk_input.target_ebitda + forest.total_qoe_adj - 2:.1f} ~ {mirk_input.target_ebitda + forest.total_qoe_adj + 2:.1f}",
        net_debt_items=["Operating leases (15억)", "Customer deposits (8억)"],
        wc_peg_range="35.0 ~ 40.0",
        top_3_levers=[
            "Price adjustment: 5-8억 (Revenue recognition issue)",
            "Net Debt: Add 23억 for debt-like items",
            "SPA R&W: Revenue policy indemnity"
        ],
        red_flags=[issue.title for issue in forest.get_issues_by_severity(forest.issues[0].severity) if forest.issues[0].severity][:3]
    )
    
    print("\n📤 WOOD Output:")
    print(f"  Deal Status: {wood_output.deal_status}")
    print(f"  Risk Score: {wood_output.risk_score}")
    print(f"  Normalized EBITDA: {wood_output.normalized_ebitda_range}억")
    print(f"  Top Levers:")
    for lever in wood_output.top_3_levers:
        print(f"    - {lever}")
    
    print("\n" + "=" * 70)


def test_full_workflow():
    """Test complete TS workflow"""
    print("\n" + "=" * 70)
    print("🚀 Testing Full Workflow")
    print("=" * 70)
    
    # Step 1: MIRK provides deal context
    print("\n[Step 1] MIRK provides deal context")
    mirk_input = MirkInput(
        deal_name="Project_Gamma_GameCo",
        sector="Game",
        deal_rationale="Platform consolidation play",
        valuation_method="DCF + EV/EBITDA cross-check",
        target_ebitda=80.0,
        target_net_debt=30.0,
        focus_areas=["IP dependency", "Live ops volatility"]
    )
    print(f"✅ Deal: {mirk_input.deal_name}")
    
    # Step 2: WOOD loads issue library
    print("\n[Step 2] WOOD loads issue library")
    issues = get_issue_library(mirk_input.sector)
    print(f"✅ Loaded {len(issues)} issues for {mirk_input.sector} sector")
    
    # Step 3: WOOD builds Forest Map
    print("\n[Step 3] WOOD builds Forest Map")
    forest = ForestMap(deal_name=mirk_input.deal_name)
    forest.issues = issues[:10]  # Simulate identifying 10 issues
    forest.calculate_metrics()
    print(f"✅ Forest Map created: {forest.red_flag_count} red flags, risk score {forest.risk_score}")
    
    # Step 4: Generate reports
    print("\n[Step 4] Generate reports")
    generator = WoodReportGenerator()
    md_report = generator.generate_forest_map_md(forest)
    summary = generator.generate_summary_text(forest)
    print(f"✅ Reports generated (Markdown: {len(md_report)} chars)")
    
    # Step 5: WOOD outputs to MIRK
    print("\n[Step 5] WOOD outputs to MIRK")
    wood_output = WoodOutput(
        deal_name=mirk_input.deal_name,
        deal_status=forest.deal_status,
        risk_score=forest.risk_score,
        normalized_ebitda_range=f"{mirk_input.target_ebitda + forest.total_qoe_adj - 3:.1f} ~ {mirk_input.target_ebitda + forest.total_qoe_adj + 3:.1f}",
        net_debt_items=["Deferred revenue (12억)", "Operating leases (18억)"],
        wc_peg_range="45.0 ~ 50.0",
        top_3_levers=[
            "Structure: Earn-out tied to IP renewal",
            "Price: 8-12억 reduction for revenue normalization",
            "SPA: Live ops cost indemnity"
        ],
        structure_recommendations=[
            "Earn-out: 20% of price tied to top game retention",
            "Escrow: 10% for 12 months (IP risk)"
        ]
    )
    print(f"✅ WOOD output ready for MIRK")
    print(f"   Deal Status: {wood_output.deal_status}")
    print(f"   Adjusted EBITDA: {wood_output.normalized_ebitda_range}억")
    
    # Step 6: Display summary
    print("\n[Step 6] Summary for Telegram")
    print("\n" + "─" * 70)
    print(summary)
    print("─" * 70)
    
    print("\n✅ Full workflow completed!")
    print("=" * 70)


if __name__ == "__main__":
    try:
        print("\n")
        print("═" * 70)
        print("🌲 WOOD TRANSACTION SERVICES ENGINE - TEST SUITE")
        print("═" * 70)
        
        # Run tests
        test_issue_library()
        forest = test_forest_map()
        test_report_generation(forest)
        test_mirk_interface()
        test_full_workflow()
        
        print("\n")
        print("═" * 70)
        print("✅ ALL TESTS PASSED")
        print("═" * 70)
        print("\n💡 Next steps:")
        print("   1. Review generated reports")
        print("   2. Integrate with main.py for Telegram")
        print("   3. Add real DD data sources")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Test failed:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
