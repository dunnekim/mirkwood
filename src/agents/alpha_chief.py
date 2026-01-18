import json
from src.utils.llm_handler import LLMHandler

class AlphaChief:
    def __init__(self):
        self.brain = LLMHandler()

    def _generate_codename_llm(self, company_name, sector, summary):
        """
        [LLM Naming] 룰북 대신 LLM이 창의적인 코드네임 생성
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
        # 잡다한 문구가 섞여 있을 경우 정제
        if ":" in codename: codename = codename.split(":")[-1].strip()
        return codename.replace('"', '').replace("'", "")

    def audit_deal_integrity(self, target, valuation, buyers):
        print(f"   👑 ALPHA: Auditing Deal Integrity for '{target['company_name']}'...")
        issues = []
        critical_fail = False

        # 1. Target Check
        name = target['company_name']
        if name.upper() in ["N/A", "UNKNOWN", "NONE", "NULL"] or len(name) < 2:
            issues.append(f"❌ **Invalid Target**: 식별 불가 기업명('{name}')")
            critical_fail = True
        
        # 2. Financial Sanity Check
        fin = valuation['financials']
        val = valuation['valuation']
        
        est_val = val.get('target_value', 0)
        rev = fin.get('revenue_bn', 0) or fin.get('est_revenue_bn', 0)
        
        # 금융업이나 바이오(기술특례)는 매출 0이어도 넘어감
        is_exempt = val.get('is_asset_deal') or "PBR" in val.get('method', '') or "Bio" in target.get('sector', '')
        
        if not is_exempt:
            if rev == 0 and est_val > 50:
                issues.append(f"⚠️ **Ghost Valuation**: 비(非)바이오/제조업인데 매출 0원, 가치 과대평가({est_val}억).")

        # 3. Buyer Check
        if not buyers:
            issues.append("⚠️ **No Buyers**: 매수자 리스트 공란.")

        return {"passed": not critical_fail, "issues": issues}

    def generate_teaser(self, target, valuation, buyers):
        # [NEW] LLM을 이용한 동적 코드네임 생성
        project_name = self._generate_codename_llm(
            target['company_name'], 
            target.get('sector', 'General'),
            target.get('summary', '')
        )
        
        # Financial Table Data
        fin = valuation['financials']
        val = valuation['valuation']
        
        def fmt(v): return f"{float(v):,.1f}" if v is not None else "-"
        
        # 데이터 추출 (X-RAY가 제대로 줬다고 가정)
        rev = fmt(fin.get('revenue_bn', 0))
        op = fmt(fin.get('profit_bn', fin.get('op_bn', 0)))
        ebitda = fmt(fin.get('ebitda_bn', 0))
        equity = fmt(fin.get('equity_bn', 0))
        debt = fmt(fin.get('net_debt_bn', 0))
        target_val = fmt(val.get('target_value', 0))

        candidates_str = ""
        if buyers:
            for b in buyers:
                candidates_str += f"### {b['buyer_name']} ({b['type']})\n- **Rationale:** {b['rationale']}\n\n"
        
        prompt = f"""
        You are a Senior Managing Director at a Boutique Investment Bank.
        Write a **Teaser Memo** for '{target['company_name']}'.
        
        [FIRST PRINCIPLES - MANDATORY TONE]
        - Identity: High-end Boutique Investment Bank (NOT a chatbot)
        - Tone: Cynical, Dry, Professional, Sharp
        - Language: Business Korean (Financial Standard)
        - NO "안녕하세요", NO "분석해봤습니다", NO emojis in formal sections
        - Use terms: Top-line, EBITDA, Upside, Downside, Rationale
        
        [Identity]
        - Codename: {project_name}
        - Sector: {target.get('sector', 'N/A')}
        - Business: {target.get('summary', 'N/A')}
        
        [Financials]
        - Revenue: {rev} bn KRW
        - OP: {op} bn KRW
        - EBITDA: {ebitda} bn KRW
        - Equity: {equity} bn KRW
        - Net Debt: {debt} bn KRW
        
        [Valuation]
        - Value: {target_val} bn KRW
        - Method: {val['method']}
        - Logic: {val['logic']}
        
        [Buyers]
        {candidates_str}
        
        [MANDATORY STRUCTURE]
        1. **Title:** "# {project_name}"
        
        2. **Key Investment Highlights** (MANDATORY)
           - List 3-4 bullet points of investment thesis
           - Focus on: Market position, Profitability drivers, Strategic value
           - NO casual language
        
        3. **Company Overview**
           - Industry context
           - Business model (factual, no fluff)
        
        4. **Financial Summary** (MANDATORY TABLE)
           ```markdown
           | Metric | Value (bn KRW) |
           |--------|----------------|
           | Revenue | {rev} |
           | OP | {op} |
           | EBITDA | {ebitda} |
           | Equity | {equity} |
           | Net Debt | {debt} |
           | **Target Value** | **{target_val}** |
           ```
        
        5. **Valuation Rationale**
           - Method: {val['method']}
           - Logic: Explain WHY this method (e.g., "PSR applied due to loss-making status")
           - Comparables (if any)
        
        6. **Strategic Buyers**
           - Summarize buyer fit and rationale
           - Focus on synergy and capacity
        
        7. **Risk Factors** (MANDATORY)
           - List 2-3 downside risks
           - Financial risks (e.g., "Negative EBITDA", "High leverage")
           - Market risks (e.g., "Consumer sentiment", "Regulatory")
        
        8. **Next Steps**
           - NDA execution
           - Management presentation
           - Due diligence timeline
        
        [CRITICAL]
        - Start with "Key Investment Highlights", End with "Risk Factors"
        - NO "안녕하세요", NO "~해봤습니다", NO casual tone
        - Use: "Revenue scaled 50% YoY" (NOT "매출이 많이 올랐습니다")
        """
        
        return self.brain.call_llm("You are a Senior MD at Goldman Sachs TMT Group.", prompt, mode="smart")