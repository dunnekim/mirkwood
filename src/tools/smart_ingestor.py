"""
Smart Financial Ingestor

[Purpose]
Intelligent data collection from multiple sources with transparency.

Priority Order:
1. DART (Primary - Official financial statements)
2. Web Search (Secondary - News/estimates)
3. User Input (Fallback - Manual override)

[Big 4 Standard]
Always specify data source for audit trail.
"""

import re
from typing import Dict, Optional
from .dart_reader import DartReader
from src.utils.llm_handler import LLMHandler

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS


class SmartFinancialIngestor:
    """
    Smart financial data collector with source attribution
    
    Big 4 Principle: "Every number must have a source"
    """
    
    def __init__(self):
        self.dart = DartReader()
        self.llm = LLMHandler()
    
    def ingest(self, company_name: str) -> Dict:
        """
        Collect financial data with multi-source fallback
        
        Args:
            company_name: Target company name
        
        Returns:
            {
                "revenue": float (bn KRW),
                "op": float (bn KRW),
                "ebitda": float (bn KRW),
                "source": str (e.g., "DART 2024.3Q"),
                "description": str (source details),
                "confidence": str ("High"/"Medium"/"Low"),
                "requires_input": bool (True if failed)
            }
        """
        print(f"🔎 SmartIngestor: Collecting data for '{company_name}'...")
        
        # ============================================================
        # METHOD 1: DART (Primary Source - Official)
        # ============================================================
        print("   [1] Attempting DART (Official Financial Statements)...")
        dart_result = self._try_dart(company_name)
        
        if dart_result['success']:
            print(f"      ✅ DART Success: {dart_result['source']}")
            return dart_result['data']
        else:
            print(f"      ❌ DART Failed: {dart_result['reason']}")
        
        # ============================================================
        # METHOD 2: Web Search (Secondary - Estimates)
        # ============================================================
        print("   [2] Attempting Web Search (News/Estimates)...")
        web_result = self._try_web_search(company_name)
        
        if web_result['success']:
            print(f"      ✅ Web Search Success: {web_result['source']}")
            return web_result['data']
        else:
            print(f"      ❌ Web Search Failed: {web_result['reason']}")
        
        # ============================================================
        # METHOD 3: User Input Required (Fallback)
        # ============================================================
        print("      ⚠️ All automated methods failed. User input required.")
        
        return {
            "revenue": None,
            "op": None,
            "ebitda": None,
            "source": "User Input Required",
            "description": "Automated data collection failed. Please provide manual input.",
            "confidence": "Unknown",
            "requires_input": True
        }
    
    def _try_dart(self, company_name: str) -> Dict:
        """
        Attempt to fetch from DART
        
        Returns:
            {"success": bool, "data": dict, "source": str, "reason": str}
        """
        try:
            fin_data = self.dart.get_financial_summary(company_name)
            
            if not fin_data:
                return {
                    "success": False,
                    "reason": "No DART data found (company may be unlisted or name mismatch)"
                }
            
            # Extract data
            revenue = float(fin_data.get('revenue_bn', 0) or 0)
            op = float(fin_data.get('profit_bn', 0) or fin_data.get('op_bn', 0) or 0)
            ebitda = op * 1.15 if op > 0 else op  # EBITDA estimate
            
            # Sanity check
            if revenue == 0 and op == 0:
                return {
                    "success": False,
                    "reason": "DART returned zero values"
                }
            
            # Determine period (try to extract from response)
            period = "2024.3Q"  # Default
            if 'period' in fin_data:
                period = fin_data['period']
            
            return {
                "success": True,
                "data": {
                    "revenue": revenue,
                    "op": op,
                    "ebitda": ebitda,
                    "source": f"DART {period}",
                    "description": f"Official financial statement from DART OpenAPI (Period: {period})",
                    "confidence": "High",
                    "requires_input": False
                },
                "source": f"DART {period}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "reason": f"DART API Error: {str(e)}"
            }
    
    def _try_web_search(self, company_name: str) -> Dict:
        """
        Attempt to fetch from web search + LLM parsing
        
        Returns:
            {"success": bool, "data": dict, "source": str, "reason": str}
        """
        try:
            # Search query
            query = f"{company_name} 매출 영업이익 2024 실적"
            
            context = ""
            with DDGS() as ddgs:
                results = ddgs.text(query, region='kr-kr', timelimit='y', max_results=5)
                if not results:
                    return {
                        "success": False,
                        "reason": "No search results found"
                    }
                
                for res in results:
                    context += f"- {res.get('title', '')}: {res.get('body', '')}\n"
            
            if not context:
                return {
                    "success": False,
                    "reason": "Search returned empty context"
                }
            
            # LLM parsing
            prompt = f"""
            Extract financial data for '{company_name}' from the following search results.
            
            [Search Results]
            {context}
            
            [Rules]
            - Extract MOST RECENT revenue and operating profit
            - Unit: Billion KRW (십억 원)
            - Example: "300억 원" → 30.0
            - If multiple sources conflict, use the most credible one (avoid estimates)
            - If data not found, return null
            
            Return JSON:
            {{
                "revenue_bn": float or null,
                "op_bn": float or null,
                "source_detail": "Brief description of where data came from"
            }}
            """
            
            response = self.llm.call_llm(
                "Financial Data Analyst", 
                prompt, 
                mode="smart"
            )
            
            # Parse JSON
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if not match:
                return {
                    "success": False,
                    "reason": "LLM failed to parse data"
                }
            
            import json
            parsed = json.loads(match.group(0))
            
            revenue = parsed.get('revenue_bn')
            op = parsed.get('op_bn')
            
            if revenue is None or op is None:
                return {
                    "success": False,
                    "reason": "LLM could not extract revenue or operating profit"
                }
            
            # Convert to float
            revenue = float(revenue)
            op = float(op)
            ebitda = op * 1.15 if op > 0 else op
            
            return {
                "success": True,
                "data": {
                    "revenue": revenue,
                    "op": op,
                    "ebitda": ebitda,
                    "source": "Estimate (Web Search)",
                    "description": f"Estimated from web search: {parsed.get('source_detail', 'Multiple sources')}",
                    "confidence": "Medium",
                    "requires_input": False
                },
                "source": "Web Search Estimate"
            }
            
        except Exception as e:
            return {
                "success": False,
                "reason": f"Web search error: {str(e)}"
            }
    
    def ingest_with_override(
        self, 
        company_name: str, 
        manual_revenue: Optional[float] = None,
        manual_op: Optional[float] = None
    ) -> Dict:
        """
        Ingest with manual override option
        
        Args:
            company_name: Company name
            manual_revenue: Manual revenue override (bn KRW)
            manual_op: Manual operating profit override (bn KRW)
        
        Returns:
            Financial data dict
        """
        # Try automated methods first
        result = self.ingest(company_name)
        
        # Override if provided
        if manual_revenue is not None and manual_op is not None:
            ebitda = manual_op * 1.15 if manual_op > 0 else manual_op
            
            return {
                "revenue": manual_revenue,
                "op": manual_op,
                "ebitda": ebitda,
                "source": "User Input (Manual Override)",
                "description": f"Manually provided by user (Rev: {manual_revenue}bn, OP: {manual_op}bn)",
                "confidence": "User-Provided",
                "requires_input": False
            }
        
        return result
