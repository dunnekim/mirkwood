"""
Scenario Runner for WOOD DCF Engine

[FS Logic]
Scenarios (Base/Bull/Bear) represent different market conditions:
- Base: Normalized growth and margins
- Bull: High growth, better margins, lower discount rate
- Bear: Low/no growth, compressed margins, higher discount rate
"""

from typing import Dict, List
import pandas as pd
from .wacc_calculator import WACCCalculator
from .dcf_calculator import DCFCalculator
from .terminal_value import TerminalValueCalculator


class ScenarioRunner:
    """
    시나리오별 DCF 실행 및 결과 취합 클래스
    
    Financial Logic:
    - 각 시나리오(Base/Bull/Bear)마다 독립적인 DCF 계산
    - WACC, 성장률, 마진을 시나리오별로 조정
    - 결과를 범위(Range)로 제시하여 의사결정 지원
    """
    
    def __init__(self, config: Dict):
        """
        Args:
            config: WOOD config.json 전체 설정
        """
        self.config = config
        self.tax_rate = config['project_settings']['default_tax_rate']
        self.currency = config['project_settings']['default_currency']
        
        # Initialize calculators
        self.wacc_calc = WACCCalculator()
        self.dcf_calc = DCFCalculator(tax_rate=self.tax_rate)
        self.tv_calc = TerminalValueCalculator()
    
    def run_scenario(
        self, 
        scenario_name: str, 
        base_revenue: float
    ) -> Dict:
        """
        단일 시나리오 DCF 실행
        
        Args:
            scenario_name: "Base", "Bull", "Bear"
            base_revenue: 기준 매출 (억 원)
        
        Returns:
            {
                "scenario": str,
                "enterprise_value": float,
                "projection_df": pd.DataFrame,
                "wacc": float,
                "growth_rate": float,
                "margin": float,
                "terminal_value": float
            }
        """
        # Load scenario parameters
        scenario_params = self.config['scenarios'][scenario_name]
        growth_rate = scenario_params['growth_rate']
        margin = scenario_params['margin']
        wacc_premium = scenario_params['wacc_premium']
        
        # Calculate WACC
        peer_group = self.config.get('peer_group_defaults', [])
        wacc_result = self.wacc_calc.calculate_scenario_wacc(peer_group, wacc_premium)
        wacc = wacc_result['adjusted_wacc']
        
        # Project financials (temporary)
        proj_df_temp = self.dcf_calc.project_financials(base_revenue, growth_rate, margin)
        last_fcf = proj_df_temp['FCF'].iloc[-1]
        
        # Calculate Terminal Value
        tv_result = self.tv_calc.calculate(last_fcf, wacc)
        
        # Full DCF calculation
        dcf_result = self.dcf_calc.calculate_enterprise_value(
            base_revenue=base_revenue,
            growth_rate=growth_rate,
            margin=margin,
            wacc=wacc,
            terminal_value_pv=self.tv_calc.calculate_pv_terminal(
                tv_result['terminal_value'], 
                dcf_result['last_discount_factor'] if 'dcf_result' in locals() else proj_df_temp['FCF'].iloc[-1]
            )
        )
        
        # Recalculate with correct terminal value
        last_discount_factor = dcf_result['last_discount_factor']
        pv_terminal = self.tv_calc.calculate_pv_terminal(tv_result['terminal_value'], last_discount_factor)
        
        enterprise_value = dcf_result['pv_fcf'] + pv_terminal
        
        return {
            "scenario": scenario_name,
            "enterprise_value": enterprise_value,
            "projection_df": dcf_result['projection_df'],
            "wacc": wacc,
            "growth_rate": growth_rate,
            "margin": margin,
            "terminal_value": tv_result['terminal_value'],
            "pv_terminal": pv_terminal,
            "pv_fcf": dcf_result['pv_fcf']
        }
    
    def run_all_scenarios(self, base_revenue: float) -> Dict:
        """
        전체 시나리오 실행 및 결과 취합
        
        Args:
            base_revenue: 기준 매출 (억 원)
        
        Returns:
            {
                "results": [scenario_result_1, ...],
                "summary_df": pd.DataFrame,
                "value_range": {"min": float, "max": float, "base": float}
            }
        """
        results = []
        summary_rows = []
        
        for scenario_name in self.config['scenarios'].keys():
            result = self.run_scenario(scenario_name, base_revenue)
            results.append(result)
            
            summary_rows.append({
                "Scenario": scenario_name,
                "WACC": f"{result['wacc']*100:.1f}%",
                "Growth": f"{result['growth_rate']*100:.1f}%",
                "Margin": f"{result['margin']*100:.1f}%",
                "Value(Bn)": round(result['enterprise_value'], 1)
            })
        
        summary_df = pd.DataFrame(summary_rows)
        
        # Extract value range
        values = [r['enterprise_value'] for r in results]
        value_range = {
            "min": min(values),
            "max": max(values),
            "base": next((r['enterprise_value'] for r in results if r['scenario'] == 'Base'), values[0])
        }
        
        return {
            "results": results,
            "summary_df": summary_df,
            "value_range": value_range
        }
    
    def generate_summary_text(self, run_result: Dict, project_name: str) -> str:
        """
        사람이 읽을 수 있는 요약 텍스트 생성
        
        Args:
            run_result: run_all_scenarios() 결과
            project_name: 프로젝트/회사명
        
        Returns:
            Markdown 형식 요약
        """
        value_range = run_result['value_range']
        
        summary = f"🌲 **MIRKWOOD Valuation: {project_name}**\n\n"
        summary += f"**Valuation Range: {value_range['min']:.0f}~{value_range['max']:.0f}억 원**\n"
        summary += f"(Base Case: {value_range['base']:.0f}억)\n\n"
        
        for result in run_result['results']:
            summary += f"**[{result['scenario']}]** "
            summary += f"Value: **{result['enterprise_value']:.1f}억** "
            summary += f"(Growth {result['growth_rate']*100:.0f}%, Margin {result['margin']*100:.0f}%)\n"
        
        summary += "\n⚠️ *Indicative estimates for discussion only.*"
        
        return summary
