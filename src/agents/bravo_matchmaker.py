"""
BRAVO Matchmaker - Rationale-based Deal Maker

[Phase 3 Upgrade]
Upgraded from simple sector matcher to professional M&A strategist.
Generates investment rationale (the "Why") for each buyer-target match.

[Key Features]
- Structured BuyerProfile with fit_score (0-100)
- Professional IB-style rationale generation
- Recent M&A activity tracking
- SI (Strategic Investor) vs FI (Financial Investor) classification
- Sector compatibility validation
"""

import json
import time
import re
from dataclasses import dataclass
from typing import List, Literal, Optional, Dict
from src.utils.llm_handler import LLMHandler

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS


@dataclass
class BuyerProfile:
    """
    Structured buyer profile with investment rationale
    
    [IB Standard]
    Professional buyer profile matching investment banking standards
    """
    name: str
    type: Literal["SI", "FI"]  # Strategic Investor or Financial Investor
    fit_score: int  # 0-100 strategic fit score
    rationale: str  # Professional investment rationale (Korean)
    recent_activity: str = ""  # Recent M&A/investment activity (e.g., "Acquired Company X in 2024")
    
    def __post_init__(self):
        """Validate fit_score range"""
        self.fit_score = max(0, min(100, self.fit_score))


class BravoMatchmaker:
    """
    Rationale-based M&A Deal Matchmaker
    
    [Evolution]
    V1: Simple sector matching (list companies)
    V2: Rationale-based matching with fit scores and investment logic
    
    [Process]
    1. Analyze target company (sector, revenue, core competency)
    2. Brainstorm potential buyers (LLM + Search)
    3. Fact-check recent activity (web search)
    4. Generate investment rationale (LLM)
    5. Calculate fit_score (0-100)
    6. Return structured BuyerProfile list
    """
    
    def __init__(self):
        self.brain = LLMHandler()
        self.role_prompt = """
        You are 'Agent BRAVO', a Senior M&A Strategist at MIRKWOOD Partners.
        
        [Your Mission]
        Find strategic buyers (SI) and financial investors (FI) for M&A deals.
        Provide professional investment rationale, not just company names.
        
        [Output Requirements]
        - Professional IB tone (Korean)
        - Specific synergy explanations (Vertical Integration, Market Expansion, Technology Acquisition)
        - Evidence-based (mention recent deals or strategic initiatives)
        - No generic statements ("They are a big company")
        
        [Quality Standards]
        Good: "최근 레인보우로보틱스 지분 투자 등 로봇 밸류체인을 강화하고 있으므로, 
              귀사의 감속기 기술과 결합 시 즉각적인 CapEx 절감 효과가 기대됩니다."
        Bad: "대기업이라 인수할 수 있습니다."
        """
        
        # Blacklist (generic/irrelevant entities)
        self.blacklist = [
            "트럼프", "위키백과", "나무위키", "뉴스", "채용", "사람인", "잡코리아",
            "국내 대기업", "중견기업", "유망 스타트업", "글로벌 기업",
            "김앤장", "삼일", "삼정", "안진", "한영",  # Advisory firms
            "공사", "공단", "진흥원", "재단", "협회", "Corporation", "Government", "Ministry",
            "Berkshire", "Hathaway", "BlackRock", "Vanguard", "Goldman", "Morgan",
            "Softbank", "Vision Fund", "Apple", "Google", "Microsoft", "Amazon"
        ]
        
        # Sector compatibility matrix (first principle logic)
        self.sector_mismatch = {
            "Consumer": ["Construction", "Heavy Industry", "Shipbuilding", "Steel", "Chemical", "에너지", "건설", "중공업", "조선", "철강"],
            "Beauty": ["Construction", "Heavy Industry", "Shipbuilding", "Steel", "Chemical", "에너지", "건설", "중공업", "조선", "철강"],
            "IT": ["Construction", "Heavy Industry", "에너지", "건설", "중공업"],
            "Bio": ["Construction", "Heavy Industry", "에너지", "건설", "중공업"],
            "Finance": ["Manufacturing", "Construction", "제조", "건설"]
        }
        
        # Sector fit keywords (positive signals)
        self.fit_keywords = {
            "Consumer": ["유통", "브랜드", "consumer", "retail", "fashion", "beauty", "cosmetic"],
            "Beauty": ["화장품", "뷰티", "beauty", "cosmetic", "신세계", "롯데", "CJ", "아모레"],
            "IT": ["소프트웨어", "플랫폼", "IT", "tech", "digital", "AI", "클라우드"],
            "Bio": ["제약", "바이오", "pharma", "bio", "healthcare", "의료"],
            "Finance": ["금융", "지주", "은행", "finance", "capital", "fund"]
        }
    
    def _clean_json(self, text: str) -> Optional[Dict]:
        """Extract JSON from LLM response"""
        try:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            return json.loads(match.group(0)) if match else None
        except:
            return None
    
    def _calculate_fit_score(
        self, 
        target_sector: str, 
        buyer_name: str, 
        buyer_context: str = "",
        has_recent_activity: bool = False,
        buyer_type: str = "SI"
    ) -> int:
        """
        Calculate strategic fit score (0-100)
        
        [Scoring Logic]
        - Base: 50 (neutral)
        - Sector match: +30
        - Recent activity: +10
        - SI (strategic): +10 bonus
        - FI (financial): +5 bonus (less strategic fit)
        
        Args:
            target_sector: Target company sector
            buyer_name: Buyer company name
            buyer_context: Search context/news about buyer
            has_recent_activity: Whether buyer has recent M&A activity
            buyer_type: "SI" or "FI"
        
        Returns:
            Fit score (0-100)
        """
        buyer_lower = buyer_name.lower()
        context_lower = buyer_context.lower()
        combined_text = f"{buyer_lower} {context_lower}"
        
        # 1. Hard rejection (sector mismatch)
        for target_key, incompatible_sectors in self.sector_mismatch.items():
            if target_key in target_sector:
                for bad_sector in incompatible_sectors:
                    if bad_sector.lower() in combined_text:
                        return 0
        
        # 2. Base score
        score = 50
        
        # 3. Sector fit bonus
        for target_key, keywords in self.fit_keywords.items():
            if target_key in target_sector:
                for keyword in keywords:
                    if keyword in combined_text:
                        score += 30
                        break
        
        # 4. Recent activity bonus
        if has_recent_activity:
            score += 10
        
        # 5. Buyer type bonus
        if buyer_type == "SI":
            score += 10  # Strategic investors have higher fit
        elif buyer_type == "FI":
            score += 5  # Financial investors (less strategic)
        
        # Cap at 100
        return min(100, score)
    
    def _extract_recent_activity(self, buyer_name: str, sector: str) -> str:
        """
        Search for recent M&A/investment activity
        
        Args:
            buyer_name: Buyer company name
            sector: Target sector
        
        Returns:
            Recent activity description (e.g., "2024년 레인보우로보틱스 지분 투자")
        """
        queries = [
            f"{buyer_name} 최근 인수합병 2024 2025",
            f"{buyer_name} {sector} 투자 전략",
            f"{buyer_name} M&A 사례"
        ]
        
        activity_text = ""
        
        try:
            with DDGS() as ddgs:
                for q in queries:
                    try:
                        results = ddgs.text(q, region='kr-kr', timelimit='y', max_results=1)
                        if results:
                            snippet = results[0].get('body', '')[:200]
                            activity_text += f"{snippet}\n"
                    except:
                        pass
                    time.sleep(0.3)
        except:
            pass
        
        return activity_text.strip()
    
    def _generate_rationale(
        self,
        target_name: str,
        target_sector: str,
        target_revenue: Optional[float],
        buyer_name: str,
        buyer_type: str,
        recent_activity: str,
        buyer_context: str
    ) -> str:
        """
        Generate professional investment rationale using LLM
        
        [Rationale Types]
        - Vertical Integration: "수직계열화를 통한 공급망 내부화"
        - Market Expansion: "신규 시장 진입 및 고객 기반 확대"
        - Technology Acquisition: "핵심 기술 확보 및 R&D 역량 강화"
        - Cost Synergy: "CapEx 절감 및 운영 효율화"
        
        Args:
            target_name: Target company name
            target_sector: Target sector
            target_revenue: Target revenue (optional)
            buyer_name: Buyer company name
            buyer_type: "SI" or "FI"
            recent_activity: Recent M&A activity
            buyer_context: Additional context from search
        
        Returns:
            Professional rationale in Korean
        """
        revenue_str = f"{target_revenue:.0f}억 원" if target_revenue else "중견 규모"
        
        prompt = f"""
        [Target Company]
        이름: {target_name}
        섹터: {target_sector}
        규모: {revenue_str}
        
        [Potential Buyer]
        이름: {buyer_name}
        유형: {"전략적 인수자 (SI)" if buyer_type == "SI" else "금융 투자자 (FI)"}
        최근 활동: {recent_activity if recent_activity else "정보 없음"}
        추가 맥락: {buyer_context[:300] if buyer_context else "정보 없음"}
        
        [Task]
        다음 형식으로 투자 논리(Rationale)를 작성하세요:
        
        1. **시너지 유형** (수직계열화 / 시장확장 / 기술확보 / 비용절감 중 선택)
        2. **구체적 근거** (최근 활동이나 전략적 이니셔티브 언급)
        3. **기대 효과** (정량적 또는 정성적)
        
        [Output Requirements]
        - 한국어로 작성
        - 전문적인 IB 톤 (투자은행 리포트 스타일)
        - 2-3문장으로 간결하게
        - 구체적 사실 기반 (추측 지양)
        
        [Example - Good]
        "최근 레인보우로보틱스 지분 투자 등 로봇 밸류체인을 강화하고 있으므로, 
         귀사의 감속기 기술과 결합 시 즉각적인 CapEx 절감 효과가 기대됩니다."
        
        [Example - Bad]
        "대기업이라 인수할 수 있습니다."
        
        Rationale:
        """
        
        rationale = self.brain.call_llm(self.role_prompt, prompt, mode="smart")
        
        # Clean and validate
        rationale = rationale.strip()
        if not rationale or len(rationale) < 20:
            # Fallback rationale
            if buyer_type == "SI":
                rationale = f"{buyer_name}은 {target_sector} 분야에서 전략적 시너지를 추구하고 있으며, {target_name}의 핵심 역량을 통해 사업 포트폴리오를 강화할 수 있습니다."
            else:
                rationale = f"{buyer_name}은 {target_sector} 분야에 대한 투자 관심이 있으며, {target_name}의 성장 잠재력을 바탕으로 가치 창출이 기대됩니다."
        
        return rationale
    
    def _brainstorm_buyers(
        self,
        target_name: str,
        target_sector: str,
        target_revenue: Optional[float]
    ) -> List[Dict]:
        """
        Brainstorm potential buyers using LLM
        
        Args:
            target_name: Target company name
            target_sector: Target sector
            target_revenue: Target revenue (optional)
        
        Returns:
            List of buyer candidates with name and type
        """
        revenue_str = f"{target_revenue:.0f}억 원 규모" if target_revenue else "중견 규모"
        
        prompt = f"""
        [Target Company]
        이름: {target_name}
        섹터: {target_sector}
        규모: {revenue_str}
        
        [Task]
        {target_name}의 잠재적 인수자(Strategic Buyer) 및 금융 투자자(Financial Investor)를 제안하세요.
        
        [Requirements]
        1. 한국 시장에서 활발한 M&A 활동을 보이는 기업
        2. SI (전략적 인수자) 3-4개, FI (금융 투자자) 1-2개 제안
        3. 구체적인 회사명 (일반명사 금지: "대기업", "PEF" 등)
        4. 최근 해당 섹터에서 투자/인수 경험이 있는 기업 우선
        
        [Output Format]
        JSON 배열:
        [
            {{"name": "회사명1", "type": "SI"}},
            {{"name": "회사명2", "type": "SI"}},
            {{"name": "회사명3", "type": "FI"}}
        ]
        
        [Important]
        - 실제 존재하는 회사명만 제시
        - {target_name}과 동일한 회사는 제외
        - 일반명사나 추상적 표현 금지
        """
        
        response = self.brain.call_llm(self.role_prompt, prompt, mode="smart")
        
        # Parse JSON
        data = self._clean_json(response)
        
        if data and isinstance(data, list):
            return data
        elif data and isinstance(data, dict) and "buyers" in data:
            return data["buyers"]
        else:
            # Fallback: try to extract from text
            candidates = []
            lines = response.split('\n')
            for line in lines:
                if '"name"' in line or '"type"' in line:
                    try:
                        candidate = self._clean_json(line)
                        if candidate and candidate.get('name'):
                            candidates.append(candidate)
                    except:
                        pass
            
            return candidates if candidates else []
    
    def find_buyers(
        self,
        target_info: Dict,
        valuation_info: Optional[Dict] = None
    ) -> List[BuyerProfile]:
        """
        Find potential buyers with investment rationale
        
        [Main Method]
        This is the primary entry point for BRAVO V2
        
        Args:
            target_info: Target company info
                {
                    "company_name": str,
                    "sector": str,
                    "revenue": float (optional, 억 원)
                }
            valuation_info: Optional valuation results from X-RAY/WOOD
                {
                    "enterprise_value": float,
                    "scenarios": [...]
                }
        
        Returns:
            List of BuyerProfile objects with rationale and fit_score
        """
        target_name = target_info.get('company_name', 'Unknown')
        target_sector = target_info.get('sector', 'General')
        target_revenue = target_info.get('revenue') or target_info.get('base_revenue')
        
        print(f"🤝 BRAVO V2: Rationale-based Matching for '{target_name}' ({target_sector})")
        
        # Clean target name
        target_core_name = target_name.replace("(주)", "").replace("주식회사", "").strip()
        
        # Step 1: Brainstorm buyers (LLM)
        print("   📋 Brainstorming potential buyers...")
        buyer_candidates = self._brainstorm_buyers(target_name, target_sector, target_revenue)
        
        if not buyer_candidates:
            print("   ⚠️ No buyers found via LLM brainstorming, using search fallback...")
            # Fallback to search-based discovery
            buyer_candidates = self._search_based_discovery(target_name, target_sector)
        
        # Step 2: Validate and enrich each candidate
        buyer_profiles = []
        seen_names = set()
        
        for candidate in buyer_candidates[:7]:  # Limit to 7 candidates
            buyer_name = candidate.get('name', '').strip()
            buyer_type = candidate.get('type', 'SI').upper()
            
            if not buyer_name or buyer_name.upper() in ["N/A", "UNKNOWN", "NO"]:
                continue
            
            # Clean name
            buyer_name = buyer_name.replace("(주)", "").replace("주식회사", "").strip()
            
            # Filter blacklist
            if any(bad in buyer_name for bad in self.blacklist):
                continue
            
            # Avoid duplicates
            if buyer_name in seen_names:
                continue
            
            # Avoid self-reference
            if target_core_name in buyer_name or buyer_name in target_core_name:
                continue
            
            seen_names.add(buyer_name)
            
            print(f"   🔍 Analyzing: {buyer_name} ({buyer_type})")
            
            # Step 3: Extract recent activity
            recent_activity = self._extract_recent_activity(buyer_name, target_sector)
            has_activity = bool(recent_activity)
            
            # Step 4: Gather context
            buyer_context = recent_activity  # Can be extended with more search
            
            # Step 5: Calculate fit score
            fit_score = self._calculate_fit_score(
                target_sector,
                buyer_name,
                buyer_context,
                has_activity,
                buyer_type
            )
            
            # Reject if fit score is 0
            if fit_score == 0:
                print(f"      ❌ Rejected: {buyer_name} (Sector Mismatch)")
                continue
            
            # Step 6: Generate rationale
            rationale = self._generate_rationale(
                target_name,
                target_sector,
                target_revenue,
                buyer_name,
                buyer_type,
                recent_activity,
                buyer_context
            )
            
            # Step 7: Create BuyerProfile
            profile = BuyerProfile(
                name=buyer_name,
                type=buyer_type,
                fit_score=fit_score,
                rationale=rationale,
                recent_activity=recent_activity[:200] if recent_activity else ""
            )
            
            buyer_profiles.append(profile)
            print(f"      ✅ Added: {buyer_name} (Fit: {fit_score}/100)")
            
            # Limit to top 5
            if len(buyer_profiles) >= 5:
                break
        
        # Sort by fit_score (descending)
        buyer_profiles.sort(key=lambda x: x.fit_score, reverse=True)
        
        print(f"   ✅ Found {len(buyer_profiles)} qualified buyers")
        
        return buyer_profiles
    
    def _search_based_discovery(self, target_name: str, sector: str) -> List[Dict]:
        """
        Fallback: Search-based buyer discovery
        
        Args:
            target_name: Target company name
            sector: Target sector
        
        Returns:
            List of buyer candidates
        """
        queries = [
            f"{sector} 관련 상장사 현금 부자",
            f"{sector} 신사업 진출 선언 기업",
            f"{sector} 분야 PEF 볼트온 전략"
        ]
        
        candidates = []
        
        try:
            with DDGS() as ddgs:
                for query in queries:
                    try:
                        results = ddgs.text(query, region='kr-kr', timelimit='y', max_results=2)
                        if not results:
                            continue
                        
                        for res in results:
                            snippet = (res.get('title', '') + " " + res.get('body', ''))[:300]
                            
                            prompt = f"""
                            Target: {target_name}
                            Context: "{query}"
                            Snippet: "{snippet}"
                            
                            Identify a SPECIFIC BUYER NAME.
                            Rules: NO Generics ("Big Corp"), NO Advisory ("PwC").
                            
                            Return JSON: {{ "name": "Exact Name", "type": "SI" or "FI" }}
                            """
                            
                            resp = self.brain.call_llm(self.role_prompt, prompt, mode="fast")
                            data = self._clean_json(resp)
                            
                            if data and data.get('name') and "NO" not in data['name']:
                                candidates.append(data)
                                if len(candidates) >= 5:
                                    break
                        
                        if len(candidates) >= 5:
                            break
                    except:
                        pass
                    time.sleep(0.5)
        except:
            pass
        
        return candidates
    
    # ============================================================================
    # LEGACY COMPATIBILITY (for existing pipeline)
    # ============================================================================
    
    def find_potential_buyers(self, deal_info: Dict, industry_keyword: str) -> List[Dict]:
        """
        Legacy method for backward compatibility
        
        Converts new BuyerProfile format to old dict format
        """
        target_info = {
            "company_name": deal_info.get('company_name', ''),
            "sector": industry_keyword,
            "revenue": deal_info.get('revenue')
        }
        
        profiles = self.find_buyers(target_info)
        
        # Convert to legacy format
        legacy_format = []
        for profile in profiles:
            legacy_format.append({
                "buyer_name": profile.name,
                "type": profile.type,
                "rationale": profile.rationale,
                "fit_score": profile.fit_score,
                "recent_activity": profile.recent_activity
            })
        
        return legacy_format
