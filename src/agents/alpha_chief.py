"""
ALPHA Chief - Final Report Generator

[Phase 4: Final Synthesizer]
ALPHA takes outputs from ZULU, X-RAY, WOOD, and BRAVO to generate
a professional Teaser Memo (Investment Memorandum style).

[Key Features]
- Structured Markdown report generation
- LLM-powered Investment Highlights
- Valuation Football Field summary
- Top buyer rationale integration
- Professional IB tone (Korean)
"""

import json
from typing import Dict, List, Optional
from src.utils.llm_handler import LLMHandler

# Import BuyerProfile if available
try:
    from src.agents.bravo_matchmaker import BuyerProfile
except ImportError:
    BuyerProfile = None


class AlphaChief:
    """
    Final Report Generator for M&A Deals
    
    [Role]
    Senior Deal Editor & IB Associate at MIRKWOOD Partners
    
    [Process]
    1. Analyze financials and calculate metrics
    2. Generate Investment Highlights (LLM)
    3. Synthesize Valuation (Multiple + DCF)
    4. Format Buyer Rationale (Top 2-3)
    5. Assemble into structured Markdown report
    """
    
    def __init__(self):
        self.brain = LLMHandler()
        self.role_prompt = """
        You are a Senior Managing Director at MIRKWOOD Partners, a boutique investment bank.
        
        [Tone Requirements]
        - Professional, Dry, Persuasive
        - Business Korean (Financial Standard)
        - NO casual language ("안녕하세요", "~해봤습니다")
        - Use terms: Top-line, EBITDA, Upside, Downside, Rationale
        
        [Output Style]
        - Factual, evidence-based
        - Concise bullet points
        - Professional IB terminology
        """
    
    def _format_number(self, value, unit="Bn") -> str:
        """
        Format number with Korean billion unit
        
        Args:
            value: Numeric value
            unit: Unit suffix ("Bn" for billion)
        
        Returns:
            Formatted string (e.g., "500 Bn KRW")
        """
        if value is None:
            return "N/A"
        
        try:
            num = float(value)
            if num == 0:
                return "N/A"
            return f"{num:,.0f} {unit} KRW"
        except (ValueError, TypeError):
            return "N/A"
    
    def _format_percentage(self, value) -> str:
        """Format percentage"""
        if value is None:
            return "N/A"
        
        try:
            num = float(value)
            return f"{num:.1f}%"
        except (ValueError, TypeError):
            return "N/A"
    
    def _calculate_financial_metrics(self, financials: Dict) -> Dict:
        """
        Calculate key financial metrics
        
        Args:
            financials: Financial data dict
        
        Returns:
            Calculated metrics dict
        """
        metrics = {}
        
        # Extract values
        revenue = financials.get('revenue_bn') or financials.get('revenue') or financials.get('est_revenue_bn', 0)
        op = financials.get('profit_bn') or financials.get('op_bn') or financials.get('operating_profit', 0)
        ebitda = financials.get('ebitda_bn') or financials.get('ebitda', 0)
        
        # Calculate margins
        if revenue and revenue > 0:
            metrics['op_margin'] = (op / revenue) * 100 if op else 0
            metrics['ebitda_margin'] = (ebitda / revenue) * 100 if ebitda else 0
        else:
            metrics['op_margin'] = None
            metrics['ebitda_margin'] = None
        
        # Growth (if available)
        metrics['revenue'] = revenue
        metrics['op'] = op
        metrics['ebitda'] = ebitda
        
        return metrics
    
    def _generate_investment_highlights(
        self,
        target: Dict,
        financials: Dict,
        metrics: Dict
    ) -> List[str]:
        """
        Generate Investment Highlights using LLM
        
        Args:
            target: Target company info
            financials: Financial data
            metrics: Calculated metrics
        
        Returns:
            List of highlight strings
        """
        sector = target.get('sector', 'General')
        company_name = target.get('company_name', 'Company')
        revenue = metrics.get('revenue', 0)
        op_margin = metrics.get('op_margin')
        
        prompt = f"""
        [Target Company]
        이름: {company_name}
        섹터: {sector}
        매출: {revenue:.0f}억 원
        영업이익률: {op_margin:.1f}% (if available)
        
        [Task]
        {company_name}의 투자 하이라이트 3가지를 작성하세요.
        
        [Highlights Types]
        1. 성장성 (High Growth): 매출 성장률, 시장 확장 잠재력
        2. 수익성 (Cash Cow): 높은 마진, 안정적 현금 창출
        3. 경쟁우위 (Tech Moat): 기술력, 시장 지위, 진입장벽
        4. 전략적 가치 (Strategic Value): 인수 후 시너지 가능성
        
        [Output Format]
        각 하이라이트를 1문장으로 작성 (한국어, 전문적 톤)
        
        예시:
        - "연평균 성장률 30% 이상의 고성장 섹터에서 선도적 시장 지위 확보"
        - "영업이익률 25% 이상의 높은 수익성 구조"
        - "핵심 기술 특허 포트폴리오를 통한 강력한 경쟁우위"
        
        [Requirements]
        - 구체적 수치 언급 (가능한 경우)
        - 섹터 특성 반영
        - 전문적 IB 톤
        - 3개 하이라이트 반드시 제공
        
        Investment Highlights (3개):
        """
        
        response = self.brain.call_llm(self.role_prompt, prompt, mode="smart")
        
        # Parse highlights (extract bullet points)
        highlights = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Remove bullet markers
            for marker in ['-', '*', '•', '1.', '2.', '3.']:
                if line.startswith(marker):
                    line = line[len(marker):].strip()
                    break
            
            # Remove emoji if present
            if line and line[0] not in ['🚀', '💰', '🛡️', '⭐', '📈']:
                if len(line) > 10:  # Valid highlight
                    highlights.append(line)
        
        # Ensure we have 3 highlights
        while len(highlights) < 3:
            highlights.append(f"{sector} 분야에서 성장 잠재력이 높은 기업")
        
        return highlights[:3]
    
    def _synthesize_valuation(
        self,
        valuation: Dict,
        dcf_range: Optional[Dict] = None
    ) -> Dict:
        """
        Synthesize valuation from multiple methods
        
        Args:
            valuation: Quick valuation (Multiple-based) from X-RAY
            dcf_range: Optional DCF range from WOOD V2
        
        Returns:
            Valuation summary dict
        """
        result = {
            'market_approach': None,
            'dcf_method': None,
            'comment': None
        }
        
        # Market Approach (Multiple-based)
        if valuation:
            val_data = valuation.get('valuation', {})
            target_value = val_data.get('target_value', 0)
            method = val_data.get('method', 'N/A')
            
            if target_value and target_value > 0:
                # Extract multiple if available
                multiple = val_data.get('multiple', 'N/A')
                result['market_approach'] = {
                    'range': f"{target_value:.0f}",
                    'method': method,
                    'multiple': multiple
                }
        
        # DCF Method (from WOOD V2)
        if dcf_range:
            ev_min = dcf_range.get('ev_min', 0)
            ev_max = dcf_range.get('ev_max', 0)
            ev_base = dcf_range.get('ev_base', 0)
            wacc = dcf_range.get('wacc', None)
            
            if ev_min and ev_max:
                result['dcf_method'] = {
                    'range': f"{ev_min:.0f} - {ev_max:.0f}",
                    'base': f"{ev_base:.0f}",
                    'wacc': wacc
                }
        
        # Generate comment
        if result['market_approach'] and result['dcf_method']:
            result['comment'] = "Multiple 기반 가치평가와 DCF 모델 결과를 종합하여 제시"
        elif result['market_approach']:
            result['comment'] = f"{result['market_approach']['method']} 기반 가치평가"
        elif result['dcf_method']:
            result['comment'] = "DCF 모델 기반 가치평가"
        else:
            result['comment'] = "가치평가 정보 없음"
        
        return result
    
    def _format_buyers(self, buyers: List) -> List[Dict]:
        """
        Format and select top buyers
        
        Args:
            buyers: List of buyer dicts or BuyerProfile objects
        
        Returns:
            List of formatted buyer dicts (top 2-3)
        """
        if not buyers:
            return []
        
        # Convert BuyerProfile to dict if needed
        formatted = []
        for buyer in buyers:
            if BuyerProfile and isinstance(buyer, BuyerProfile):
                formatted.append({
                    'name': buyer.name,
                    'type': buyer.type,
                    'rationale': buyer.rationale,
                    'fit_score': buyer.fit_score
                })
            elif isinstance(buyer, dict):
                formatted.append(buyer)
        
        # Sort by fit_score if available, otherwise keep order
        if formatted and 'fit_score' in formatted[0]:
            formatted.sort(key=lambda x: x.get('fit_score', 0), reverse=True)
        
        # Return top 2-3
        return formatted[:3]
    
    def generate_report(
        self,
        target: Dict,
        financials: Dict,
        valuation: Dict,
        buyers: List,
        dcf_info: Optional[Dict] = None
    ) -> str:
        """
        Generate professional Teaser Memo
        
        [Main Method]
        This is the primary entry point for ALPHA
        
        Args:
            target: Target company info
                {
                    "company_name": str,
                    "sector": str,
                    "summary": str (optional)
                }
            financials: Financial data
                {
                    "revenue_bn": float,
                    "op_bn": float,
                    "ebitda_bn": float (optional)
                }
            valuation: Valuation results from X-RAY
                {
                    "valuation": {
                        "target_value": float,
                        "method": str,
                        "multiple": str (optional)
                    }
                }
            buyers: List of BuyerProfile or dict from BRAVO
            dcf_info: Optional DCF results from WOOD V2
                {
                    "ev_min": float,
                    "ev_max": float,
                    "ev_base": float,
                    "wacc": float (optional)
                }
        
        Returns:
            Structured Markdown report (Korean)
        """
        # Extract data
        company_name = target.get('company_name', 'Company')
        sector = target.get('sector', 'General')
        
        # Calculate metrics
        metrics = self._calculate_financial_metrics(financials)
        
        # Generate Investment Highlights
        highlights = self._generate_investment_highlights(target, financials, metrics)
        
        # Synthesize Valuation
        val_summary = self._synthesize_valuation(valuation, dcf_info)
        
        # Format Buyers
        top_buyers = self._format_buyers(buyers)
        
        # Build Report
        report = []
        
        # Header
        report.append(f"🌲 **Project {company_name} : Teaser Memo**\n")
        
        # 1. Executive Summary
        report.append("**1. Executive Summary**")
        report.append(f"* **Sector:** {sector}")
        report.append(f"* **Key Financials:** Rev {self._format_number(metrics.get('revenue'))} | OP {self._format_number(metrics.get('op'))} (OPM {self._format_percentage(metrics.get('op_margin'))})")
        
        # Deal stage (if available)
        deal_stage = target.get('deal_stage', 'Confidential Process')
        report.append(f"* **Status:** {deal_stage}")
        report.append("")
        
        # 2. Investment Highlights
        report.append("**2. Investment Highlights**")
        emojis = ["🚀", "💰", "🛡️"]
        for i, highlight in enumerate(highlights):
            emoji = emojis[i] if i < len(emojis) else "⭐"
            report.append(f"* {emoji} **{highlight}**")
        report.append("")
        
        # 3. Valuation Overview
        report.append("**3. Valuation Overview (Indicative)**")
        
        if val_summary['market_approach']:
            market = val_summary['market_approach']
            multiple_str = f" ({market['multiple']})" if market.get('multiple') and market['multiple'] != 'N/A' else ""
            report.append(f"* **Market Approach:** {self._format_number(market['range'])} {multiple_str}")
        
        if val_summary['dcf_method']:
            dcf = val_summary['dcf_method']
            wacc_str = f" (WACC {self._format_percentage(dcf.get('wacc'))})" if dcf.get('wacc') else ""
            report.append(f"* **DCF Method:** {self._format_number(dcf['range'])} {wacc_str}")
        
        if not val_summary['market_approach'] and not val_summary['dcf_method']:
            report.append("* **Valuation:** N/A")
        
        report.append(f"* *Comment:* {val_summary['comment']}")
        report.append("")
        
        # 4. Potential Buyers
        report.append("**4. Potential Buyers (Top Picks)**")
        
        if top_buyers:
            for buyer in top_buyers:
                buyer_name = buyer.get('buyer_name') or buyer.get('name', 'Unknown')
                buyer_type = buyer.get('type', 'SI')
                rationale = buyer.get('rationale', 'N/A')
                
                report.append(f"* **[{buyer_name}]** ({buyer_type}): {rationale}")
        else:
            report.append("* N/A")
        
        report.append("")
        report.append("---")
        report.append("*Disclaimer: Indicative estimates for discussion only.*")
        
        return "\n".join(report)
    
    # ============================================================================
    # LEGACY COMPATIBILITY
    # ============================================================================
    
    def generate_teaser(
        self,
        target: Dict,
        valuation: Dict,
        buyers: List
    ) -> str:
        """
        Legacy method for backward compatibility
        
        Converts old format to new generate_report format
        """
        # Extract financials from valuation
        financials = valuation.get('financials', {})
        
        # Check for DCF info in valuation
        dcf_info = None
        if 'dcf_result' in valuation:
            dcf_info = valuation['dcf_result']
        elif 'scenarios' in valuation:
            # Try to extract from scenarios
            scenarios = valuation.get('scenarios', [])
            if scenarios:
                evs = [s.get('enterprise_value', 0) for s in scenarios if isinstance(s, dict)]
                if evs:
                    dcf_info = {
                        'ev_min': min(evs),
                        'ev_max': max(evs),
                        'ev_base': evs[0] if evs else 0
                    }
        
        return self.generate_report(
            target=target,
            financials=financials,
            valuation=valuation,
            buyers=buyers,
            dcf_info=dcf_info
        )
    
    def _generate_codename_llm(self, company_name, sector, summary):
        """
        [Legacy] Generate project codename (kept for compatibility)
        """
        prompt = f"""
        Task: Create a **cool, professional M&A Project Codename** for the target company.
        
        [Target Info]
        - Name: {company_name}
        - Sector: {sector}
        - Biz Summary: {summary}
        
        [Rules]
        1. Use a metaphor related to their business (e.g., Bio -> 'Project Life', 'Project Cell').
        2. Or use a color/mineral/star (e.g., 'Project Ruby', 'Project Vega').
        3. Try to match the first letter if possible, but Priority is "Coolness".
        4. Output format: Just the string "Project [Name]" (English).
        """
        codename = self.brain.call_llm("Creative Director", prompt, mode="fast").strip()
        if ":" in codename:
            codename = codename.split(":")[-1].strip()
        return codename.replace('"', '').replace("'", "")
    
    def audit_deal_integrity(self, target, valuation, buyers):
        """
        [Legacy] Audit deal integrity (kept for compatibility)
        """
        print(f"   👑 ALPHA: Auditing Deal Integrity for '{target.get('company_name', 'Unknown')}'...")
        issues = []
        critical_fail = False
        
        # 1. Target Check
        name = target.get('company_name', '')
        if name.upper() in ["N/A", "UNKNOWN", "NONE", "NULL"] or len(name) < 2:
            issues.append(f"❌ **Invalid Target**: 식별 불가 기업명('{name}')")
            critical_fail = True
        
        # 2. Financial Sanity Check
        if valuation:
            fin = valuation.get('financials', {})
            val = valuation.get('valuation', {})
            
            est_val = val.get('target_value', 0)
            rev = fin.get('revenue_bn', 0) or fin.get('est_revenue_bn', 0)
            
            is_exempt = val.get('is_asset_deal') or "PBR" in val.get('method', '') or "Bio" in target.get('sector', '')
            
            if not is_exempt:
                if rev == 0 and est_val > 50:
                    issues.append(f"⚠️ **Ghost Valuation**: 비(非)바이오/제조업인데 매출 0원, 가치 과대평가({est_val}억).")
        
        # 3. Buyer Check
        if not buyers:
            issues.append("⚠️ **No Buyers**: 매수자 리스트 공란.")
        
        return {"passed": not critical_fail, "issues": issues}
