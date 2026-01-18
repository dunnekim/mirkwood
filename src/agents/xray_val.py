import json
import re
from src.utils.llm_handler import LLMHandler
from src.tools.dart_reader import DartReader
from src.tools.multiple_lab import MultipleLab, FinancialInput
from src.tools.naver_stock import NaverStockScout # [NEW] Phase 2

# [Dependency Check] 검색 도구
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

class XrayValuation:
    def __init__(self):
        self.brain = LLMHandler()
        self.dart = DartReader()
        self.lab = MultipleLab()
        self.market = NaverStockScout() # [NEW] Phase 2 Market Data

    def _extract_json(self, text):
        try:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            return json.loads(match.group(0)) if match else None
        except: return None
    
    def _calculate_valuation_sanity_check(self, val_output, lab_input, sector_str, target_name):
        """
        [FIRST PRINCIPLE: THE MATH RULE]
        Python 산술 연산으로 밸류에이션 검증
        
        Example: 리터니티 (매출 100억, 적자) -> PSR 0.9x = 90억 (NOT 900억)
        """
        rev = lab_input.revenue_bn
        op = lab_input.op_bn
        calculated_val = val_output.target_value_bn
        
        # Rule 1: Small brand (<100억 Revenue) should NOT be valued >1000억
        if rev < 100 and calculated_val > 1000:
            print(f"      🚨 BUBBLE ALERT: Rev {rev}억 -> Val {calculated_val}억 (10x+ Revenue Multiple)")
            # Force cap to 5x Revenue (aggressive for small companies)
            calculated_val = rev * 5.0
            val_output.target_value_bn = calculated_val
            val_output.warning_flags.append("BUBBLE_CAPPED")
            val_output.logic_summary += " | ⚠️ Bubble Capped (5x Rev)"
        
        # Rule 2: Loss-making companies -> Conservative PSR (not >2x)
        if op < 0:
            max_psr_val = rev * 2.0  # Max 2x PSR for loss-making
            if calculated_val > max_psr_val:
                print(f"      🚨 LOSS-MAKING OVERVALUED: Op {op}억, Val {calculated_val}억 -> Capped to {max_psr_val}억")
                calculated_val = max_psr_val
                val_output.target_value_bn = calculated_val
                val_output.warning_flags.append("LOSS_ADJUSTED")
                val_output.logic_summary += " | ⚠️ Loss-Making Discount Applied (2x PSR)"
        
        # Rule 3: Manual Calculation Verification (예: 매출 100억 * 0.9 = 90억)
        # PSR 기반 역산
        if "PSR" in val_output.methodology:
            implied_psr = calculated_val / rev if rev > 0 else 0
            print(f"      🧮 Math Check: {rev}억 Rev * {implied_psr:.2f}x PSR = {calculated_val:.1f}억")
            
            # PSR이 10배 이상이면 오류
            if implied_psr > 10:
                print(f"      🚨 PSR ANOMALY: {implied_psr:.1f}x is unrealistic. Capping to 3x.")
                calculated_val = rev * 3.0
                val_output.target_value_bn = calculated_val
                val_output.warning_flags.append("PSR_CAPPED")
                val_output.logic_summary += " | ⚠️ PSR Capped (3x)"
        
        return val_output

    def _normalize_unit(self, value, target_name):
        """
        [FIRST PRINCIPLE: ZERO HALLUCINATION]
        단위 오류 보정 (1000배, 10배 오류 방지)
        
        Rule: Small companies (<1000억 revenue) should NOT have values >10000억.
        """
        if value is None: return 0
        try:
            val = float(value)
        except: return 0
        
        # 예외: 대기업은 큰 숫자 인정
        is_chaebol = any(x in target_name.upper() for x in ["SAMSUNG", "HYUNDAI", "SK", "LG", "POSCO", "HANWHA", "NAVER", "KAKAO"])
        
        if not is_chaebol:
            # Aggressive Sanity Check
            if val > 10000:  # 10조 이상 -> 확실한 오류
                print(f"      🚨 CRITICAL Unit Fix: {val} -> {val/1000} (10000배 오류)")
                return val / 1000
            elif val > 5000:  # 5조~10조 -> 1/1000 (단위:원 가능성)
                print(f"      ⚠️ Unit Fix: {val} -> {val/1000} (1000배 오류 의심)")
                return val / 1000 
            elif val > 1000:  # 1조~5조 -> 1/10 (단위 실수)
                print(f"      ⚠️ Unit Fix: {val} -> {val/10} (10배 오류 의심)")
                return val / 10
        return val

    def _search_financials(self, company_name):
        """[RAG] DART 실패 시 웹 검색"""
        print(f"   🔎 X-RAY: Web Searching Financials for '{company_name}'...")
        query = f"{company_name} 매출액 영업이익 2023 2024 실적"
        
        context = ""
        try:
            with DDGS() as ddgs:
                results = ddgs.text(query, region='kr-kr', timelimit='y', max_results=3)
                for res in results:
                    context += f"- {res['body']}\n"
        except Exception as e:
            print(f"      ⚠️ Search Error: {e}")
        
        if not context: return None

        prompt = f"""
        Extract recent financials for '{company_name}'.
        [Context]
        {context}
        [Rules]
        - Unit: **Billion KRW (십억 원)**.
        - e.g., "300억" -> 30.0
        Return JSON: {{ "revenue_bn": float, "op_bn": float, "net_debt_bn": float, "equity_bn": float }}
        """
        resp = self.brain.call_llm("Financial Analyst", prompt, mode="smart")
        return self._extract_json(resp)

    def run_valuation(self, lead_data):
        target_name = lead_data['company_name']
        summary = lead_data.get('summary', target_name)
        
        print(f"   ⚡ X-RAY: Analyzing '{target_name}'...")
        
        # 1. Sector Classification
        summary_lower = str(summary).lower()
        if any(x in summary_lower for x in ["cosmetic", "device", "skin", "care", "brand", "화장품", "미용", "디바이스", "뷰티"]):
            sector_str = "Consumer" # Force Consumer for Beauty
        else:
            sector_prompt = f"Company: {target_name}, Biz: {summary}. Classify into [IT, Bio, Manu, Consumer, Finance]. Return Key."
            sector_str = self.brain.call_llm("Sector Analyst", sector_prompt, mode="fast").strip()
            sector_str = re.sub(r'[^a-zA-Z]', '', sector_str)
        
        lead_data['sector'] = sector_str
        print(f"      🏷️ Rulebook Key: {sector_str}")

        # 2. Data Fetch
        fin_data = self.dart.get_financial_summary(target_name)
        source = "OpenDart"
        
        if not fin_data:
            fin_data = self._search_financials(target_name)
            source = "Web Search"
            
        if not fin_data:
            fin_data = {"revenue_bn": 10, "op_bn": -2, "net_debt_bn": 0, "equity_bn": 5}
            source = "Conservative Estimate"

        # 3. Data Mapping & Normalization
        try:
            rev = self._normalize_unit(float(fin_data.get('revenue_bn', 0) or 0), target_name)
            op = self._normalize_unit(float(fin_data.get('profit_bn', 0) or fin_data.get('op_bn', 0) or 0), target_name)
            equity = self._normalize_unit(float(fin_data.get('equity_bn', 0) or 0), target_name)
            debt = self._normalize_unit(float(fin_data.get('net_debt_bn', 0) or 0), target_name)
            
            ebitda = op * 1.2 if op > 0 else op 
            if "Finance" in sector_str and equity < 10: equity = 30

            lab_input = FinancialInput(revenue_bn=rev, op_bn=op, ebitda_bn=ebitda, net_debt_bn=debt, equity_bn=equity)
        except Exception as e:
            print(f"      ⚠️ Mapping Error: {e}")
            lab_input = FinancialInput(revenue_bn=10, op_bn=-1, ebitda_bn=-1, net_debt_bn=0, equity_bn=5)

        # 4. Calculation (Rulebook + Live Market) - [FIRST PRINCIPLE: PYTHON ONLY]
        val_output = self.lab.calculate(sector_str, lab_input)
        
        # [NEW] Phase 2: Live Market Adjustment
        live_per = None
        # 상장사인지 체크 (이름 기반 단순 체크)
        market_data = self.market.get_market_multiple(target_name)
        
        if market_data:
            live_per = market_data['PER']
        else:
            # 비상장사면 Proxy 사용
            live_per = self.market.get_proxy_multiple(sector_str)
            
        # 시장 PER가 있고, 영업이익이 흑자일 때만 블렌딩
        if live_per and lab_input.op_bn > 0:
            market_val = lab_input.op_bn * live_per
            # Rulebook(정적) 50% + Market(동적) 50%
            blended_val = (val_output.target_value_bn * 0.5) + (market_val * 0.5)
            
            val_output.target_value_bn = blended_val
            val_output.logic_summary += f" | 📡 Market PER {live_per:.1f}x Blended (50%)"
        
        # [FIRST PRINCIPLE: SANITY CHECK]
        val_output = self._calculate_valuation_sanity_check(
            val_output, lab_input, sector_str, target_name
        )
        
        # 5. Packaging
        fin_data['revenue_bn'] = lab_input.revenue_bn
        fin_data['op_bn'] = lab_input.op_bn
        fin_data['equity_bn'] = lab_input.equity_bn
        fin_data['source'] = source

        status = "GO"
        if val_output.target_value_bn > 1000: status = "HOLD_TOO_BIG"
        
        return {
            "company": target_name,
            "financials": fin_data,
            "valuation": {
                "target_value": val_output.target_value_bn,
                "method": val_output.methodology,
                "logic": val_output.logic_summary,
                "detail": val_output.calculation_detail,
                "warnings": val_output.warning_flags
            },
            "status": status
        }