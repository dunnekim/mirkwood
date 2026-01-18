import json
import time
import re
from src.utils.llm_handler import LLMHandler

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

class BravoMatchmaker:
    def __init__(self):
        self.brain = LLMHandler()
        self.role_prompt = """
        You are 'Agent BRAVO', an M&A Deal Matchmaker.
        Your goal is to find 'Strategic Buyers' (SI) or 'Financial Investors' (FI).
        
        [CRITICAL]
        Do not just list big companies.
        You must find a specific "Strategic Rationale" or "Financial Capacity" (Dry Powder).
        """
        self.blacklist = [
            "트럼프", "위키백과", "나무위키", "뉴스", "채용", "사람인", "잡코리아",
            "삼성전자", "현대차", "SK하이닉스", "LG전자", # 무지성 대기업 제외
            "국내 대기업", "중견기업", "유망 스타트업", "글로벌 기업",
            "김앤장", "삼일", "삼정", "안진", "한영", # 자문사 제외
            "공사", "공단", "진흥원", "재단", "협회", "Corporation", "Government", "Ministry", # 공공기관 제외
            "Berkshire", "Hathaway", "BlackRock", "Vanguard", "Goldman", "Morgan",
            "Softbank", "Vision Fund", "Apple", "Google", "Microsoft", "Amazon" # 글로벌 거인 필터 (현실성 강화)
        ]
        
        # [FIRST PRINCIPLE: SECTOR LOGIC]
        # Sector compatibility matrix
        self.sector_mismatch = {
            "Consumer": ["Construction", "Heavy Industry", "Shipbuilding", "Steel", "Chemical", "에너지", "건설", "중공업", "조선", "철강"],
            "Beauty": ["Construction", "Heavy Industry", "Shipbuilding", "Steel", "Chemical", "에너지", "건설", "중공업", "조선", "철강"],
            "IT": ["Construction", "Heavy Industry", "에너지", "건설", "중공업"],
            "Bio": ["Construction", "Heavy Industry", "에너지", "건설", "중공업"],
            "Finance": ["Manufacturing", "Construction", "제조", "건설"]
        }

    def _clean_json(self, text):
        try:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            return json.loads(match.group(0)) if match else None
        except: return None

    def _check_sector_fit(self, target_sector, buyer_name, buyer_context=""):
        """
        [FIRST PRINCIPLE: LOGIC RULE]
        Sector Fit 검증 - 건설사가 뷰티 브랜드 인수하는 황당한 매칭 방지
        
        Returns: (fit_score: 0~100, penalty_reason: str)
        """
        buyer_lower = buyer_name.lower()
        context_lower = buyer_context.lower()
        
        # 1. Explicit Mismatch Detection
        for target_key, incompatible_sectors in self.sector_mismatch.items():
            if target_key in target_sector:
                for bad_sector in incompatible_sectors:
                    if bad_sector.lower() in buyer_lower or bad_sector.lower() in context_lower:
                        print(f"         🚫 SECTOR MISMATCH: {buyer_name} ({bad_sector}) ⚔️ Target ({target_sector})")
                        return 0, f"Sector Incompatible: {bad_sector} vs {target_sector}"
        
        # 2. Explicit Good Fit Bonus
        fit_keywords = {
            "Consumer": ["유통", "브랜드", "consumer", "retail", "fashion", "beauty", "cosmetic"],
            "Beauty": ["화장품", "뷰티", "beauty", "cosmetic", "신세계", "롯데", "CJ", "아모레"],
            "IT": ["소프트웨어", "플랫폼", "IT", "tech", "digital", "AI", "클라우드"],
            "Bio": ["제약", "바이오", "pharma", "bio", "healthcare", "의료"],
            "Finance": ["금융", "지주", "은행", "finance", "capital", "fund"]
        }
        
        bonus = 0
        for target_key, keywords in fit_keywords.items():
            if target_key in target_sector:
                for keyword in keywords:
                    if keyword in buyer_lower or keyword in context_lower:
                        bonus = 30  # Good fit bonus
                        break
        
        base_score = 50 + bonus  # Neutral: 50, Good fit: 80
        return base_score, "OK"
    
    def _analyze_buyer_capability(self, target_name, buyer_name, sector):
        """
        [Deep Dive] 후보자로 선정된 기업의 '인수 여력'과 '전략적 적합성'을 2차 검증
        """
        print(f"         🔬 Deep Diving into '{buyer_name}'...")
        
        # 1. 뒷조사 쿼리 (현금 여력, 최근 전략)
        queries = [
            f"{buyer_name} 현금성자산 M&A 실탄",
            f"{buyer_name} {sector} 신사업 투자 전략 2025",
            f"{buyer_name} 최근 인수합병 사례"
        ]
        
        context_text = ""
        with DDGS() as ddgs:
            for q in queries:
                try:
                    results = ddgs.text(q, region='kr-kr', timelimit='y', max_results=1)
                    if results:
                        context_text += f"- {results[0]['body']}\n"
                except: pass
                time.sleep(0.5)
        
        # [FIRST PRINCIPLE: SECTOR FIT CHECK]
        fit_score, fit_reason = self._check_sector_fit(sector, buyer_name, context_text)
        
        if fit_score == 0:
            # Hard reject
            return None  # Signal to skip this buyer
        
        # 2. LLM 논리 생성 (Logic Synthesis)
        prompt = f"""
        Target: {target_name} ({sector})
        Buyer: {buyer_name}
        Context (News):
        {context_text}
        
        Task: Explain WHY {buyer_name} would buy {target_name}.
        Focus on:
        1. **Synergy:** Specific business fit.
        2. **Capacity:** Cash reserves or recent fund raising (Dry Powder).
        3. **Track Record:** Similar past deals.
        
        Output (Korean, 1-2 sentences, Professional Tone):
        """
        
        rationale = self.brain.call_llm(self.role_prompt, prompt, mode="fast")
        
        # Add fit score to rationale
        if fit_score >= 80:
            return f"[High Fit] {rationale.strip()}"
        elif fit_score >= 50:
            return rationale.strip()
        else:
            return f"[Weak Fit] {rationale.strip()}"

    def find_potential_buyers(self, deal_info, industry_keyword):
        target_name = deal_info.get('company_name', '')
        target_core_name = target_name.replace("풀필먼트", "").replace("서비스", "").replace("(주)", "").strip()
        
        is_asset_deal = deal_info.get('deal_strategy') == "Asset Deal"
        is_finance = "Finance" in industry_keyword or "금융" in industry_keyword
        
        clean_ind = re.sub(r'\(.*?\)', '', industry_keyword).strip()
        print(f"   🤝 BRAVO: Scouting Buyers for '{clean_ind}'...")
        
        candidates = []
        seen_names = set()

        # 1. Broad Search (후보군 탐색)
        queries = []
        if is_asset_deal:
            queries = [f"국내 {clean_ind} 블라인드 펀드 드라이파우더", f"{clean_ind} 전문 운용사"]
        elif is_finance:
            queries = ["금융지주 비은행 강화 전략", "저축은행 인수 희망", "PEF 금융업 투자"]
        else:
            queries = [
                f"{clean_ind} 관련 상장사 현금 부자",
                f"{clean_ind} 신사업 진출 선언 기업",
                f"{clean_ind} 분야 PEF 볼트온 전략"
            ]

        with DDGS() as ddgs:
            for query in queries:
                try:
                    results = ddgs.text(query, region='kr-kr', timelimit='y', max_results=3)
                    if not results: continue

                    for res in results:
                        snippet = (res.get('title','') + " " + res.get('body',''))[:300]
                        
                        prompt = f"""
                        Target: {target_name}
                        Context: "{query}"
                        Snippet: "{snippet}"
                        
                        Identify a SPECIFIC BUYER NAME.
                        Rules: NO Generics ("Big Corp"), NO Advisory ("PwC"), Exclude {target_core_name}.
                        
                        Return JSON: {{ "name": "Exact Name", "type": "SI/FI" }}
                        """
                        
                        resp = self.brain.call_llm(self.role_prompt, prompt, mode="smart")
                        data = self._clean_json(resp)
                        
                        if data and data.get('name') and "NO" not in data['name']:
                            raw_name = data['name'].replace("(주)","").strip()
                            
                            # Filter
                            if any(bad in raw_name for bad in self.blacklist): continue
                            if target_core_name in raw_name: continue
                            
                            if raw_name not in seen_names:
                                # [CRITICAL UPDATE] 후보자 심층 검증 (Deep Dive)
                                rationale = self._analyze_buyer_capability(target_name, raw_name, clean_ind)
                                
                                # [FIRST PRINCIPLE: SECTOR FIT] Reject if mismatch
                                if rationale is None:
                                    print(f"         ❌ REJECTED: {raw_name} (Sector Mismatch)")
                                    continue
                                
                                candidates.append({
                                    "buyer_name": raw_name,
                                    "type": data.get('type', 'SI'),
                                    "rationale": rationale  # 심층 분석 결과 탑재
                                })
                                seen_names.add(raw_name)
                                print(f"         ✅ Candidate: {raw_name} (Deep Analysis Completed)")
                                
                                if len(candidates) >= 3: break  # Top 3만 엄선
                        time.sleep(0.5)
                    if len(candidates) >= 3: break
                except: pass

        return candidates