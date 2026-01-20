import json
import time
import re
from src.utils.llm_handler import LLMHandler
from difflib import SequenceMatcher # [NEW] 문자열 비교 도구

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

class ZuluScout:
    def __init__(self):
        self.brain = LLMHandler()
        self.role_prompt = "You are Agent ZULU. Find Targets. Accuracy is Key."
        self.blacklist = [
            "PEF", "사모펀드", "금융지주", "은행", "카드", "라이프", 
            "삼성", "현대", "SK", "LG", "네이버", "카카오", 
            "인수 완료", "매각 완료", "계약 체결", "정부", "금융당국"
        ]

    def _clean_json(self, text):
        try:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            return json.loads(match.group(0)) if match else None
        except: return None

    def _is_similar(self, query, target):
        """
        [Logic] 사용자 입력(Query)과 검색된 이름(Target)의 유사도 검사
        - 부분 포함(Substring)되거나, 유사도가 40% 이상이어야 통과
        """
        query_clean = query.replace(" ", "").upper()
        target_clean = target.replace(" ", "").upper()
        
        if query_clean in target_clean: return True
        
        similarity = SequenceMatcher(None, query_clean, target_clean).ratio()
        return similarity > 0.4  # "퀀타매트릭스" vs "비아이매트릭스" -> 유사도 낮음 -> False

    def search_leads(self, query):
        print(f"\n🕵️ ZULU: Scouting '{query}' (Target Lock Mode)...")
        
        # 1. Product/Tech 키워드 추가
        enhanced_query = f"{query} 주요제품 기술 매각"
        
        # original_query(사용자 입력)를 인자로 넘김
        leads = self._execute_search(enhanced_query, timelimit='m', mode='HOT', original_query=query)
        
        if not leads:
            print(f"   💤 Switching to Deep Dive...")
            leads = self._execute_search(query, timelimit=None, mode='COLD', original_query=query)
            
        return leads

    def _execute_search(self, query, timelimit, mode, original_query):
        leads = []
        # If the user's query contains a blacklist token (e.g., "은행"),
        # don't filter it out. This prevents false Target Not Found for banks.
        effective_blacklist = []
        oq = (original_query or "")
        for bad in self.blacklist:
            if bad and bad in oq:
                continue
            effective_blacklist.append(bad)
        try:
            with DDGS() as ddgs:
                results = ddgs.news(query, region='kr-kr', timelimit=timelimit, max_results=5)
                if not results:
                    results = ddgs.text(query, region='kr-kr', timelimit=timelimit, max_results=5)

                if not results: return []

                for res in results:
                    title = res.get('title', '')
                    body = res.get('body') or res.get('text') or title
                    
                    if any(x in (title + body) for x in ["인수 완료", "매각 종결"]): continue

                    prompt = f"""
                    Analyze this snippet for "{original_query}".
                    News: {title}
                    Context: {body}
                    
                    Task:
                    1. Identify Company Name.
                    2. Summarize Main Product/Business in 1 sentence.
                    3. Determine Sector (Bio, IT, etc).
                    
                    Return JSON: {{ "company_name": "Name", "summary": "Biz", "sector": "Industry" }}
                    """

                    analysis = self.brain.call_llm(self.role_prompt, prompt, mode="fast")
                    data = self._clean_json(analysis)
                    
                    if data and data.get('company_name'):
                        name = data['company_name']
                        
                        # [CRITICAL CHECK] 이름 검증
                        if not self._is_similar(original_query, name):
                            # print(f"   ❌ Rejected: {name} (Not matching {original_query})")
                            continue

                        if name.upper() in ["N/A", "UNKNOWN"]: continue
                        if any(bad in name for bad in effective_blacklist): continue
                        
                        data['url'] = res.get('url')
                        leads.append(data)
                        print(f"   ✅ SIGNAL: {name} | {data.get('sector')} | {data.get('summary')}")
                        if leads: break
                        
        except Exception as e:
            print(f"   ⚠️ ZULU Error: {e}")
            
        return leads