import json
from src.utils.llm_handler import LLMHandler

class AlphaChief:
    def __init__(self):
        self.brain = LLMHandler()

    def generate_teaser(self, lead_data, valuation_data, buyer_list):
        print(f"   👑 ALPHA: Synthesizing Final Strategy for '{lead_data['company_name']}'...")
        
        # 데이터 전처리: Bravo의 분석 내용을 포함하여 전달
        candidates_str = ""
        for b in buyer_list:
            candidates_str += f"- {b['buyer_name']} (Type: {b['type']}, Note: {b['rationale']})\n"

        target_sector = valuation_data['valuation'].get('logic_applied', {}).get('sector', 'Manufacturing')
        
        prompt = f"""
        You are a Chief Deal Strategist at a top-tier IB.
        Review the 'Buyer Candidates' provided by junior agents and select the Top 3 Valid Buyers.
        
        [Target Asset]
        - Company: {lead_data['company_name']}
        - Sector: {target_sector} (Context: {lead_data.get('signal_reason')})
        - Value: {valuation_data['valuation']['target_value']}B KRW
        
        [Candidate List from Bravo]
        {candidates_str}
        
        [CRITICAL FILTERING RULES]
        1. **Sector Match:** If Target is 'Manufacturing/Auto', REJECT 'Media', 'Entertainment', 'Platform', 'Bio' companies.
           (e.g., 'Samhwa Networks' is Media -> REJECT. 'Hyundai' is Auto -> ACCEPT).
        2. **Size Match:** If Target is SME, favor Mid-sized/Large Corps or PEs.
        3. **Sanity Check:** Do NOT halluncinate. If a famous company (like Hyundai, Samsung) is in the list, they are usually the best fit.
        
        [Output Format: Korean Markdown]
        # 👑 Project {lead_data['company_name'][:2]} Deal Memo
        
        ## 1. Executive Summary
        * **Opportunity:** (1 sentence summary)
        * **Valuation:** {valuation_data['valuation']['target_value']}B KRW ({valuation_data['valuation']['method']})
        
        ## 2. Target Buyer Selection (Filtered)
        * **1st Priority:** [Company Name]
          - **Why:** (Explain sector fit & synergy)
        * **2nd Priority:** [Company Name]
          - **Why:** ...
        * **3rd Priority:** [Company Name]
          - **Why:** ...
          
        (If fewer than 3 valid candidates exist, list only valid ones. Do not force invalid matches.)
        """
        
        response = self.brain.call_llm("You are a strict Gatekeeper.", prompt)
        return response