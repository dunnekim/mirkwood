import requests
from bs4 import BeautifulSoup
import re

class NaverStockScout:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def _get_code(self, company_name):
        """기업명으로 네이버 종목코드 검색"""
        try:
            # 검색 페이지
            url = f"https://finance.naver.com/search/searchList.naver?query={company_name}"
            res = requests.get(url, headers=self.headers, timeout=5)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 검색 결과 테이블에서 첫 번째 종목 코드 추출
            td = soup.select_one('td.tit > a')
            if td:
                href = td['href']
                # href format: /item/main.naver?code=005930
                code = href.split('=')[-1]
                return code
        except: pass
        return None

    def get_market_multiple(self, target_name):
        """
        [Main] 기업명 -> 네이버 검색 -> 동일업종비교 -> 평균 PER 산출
        """
        # 이름 정제 (주식회사 등 제거)
        clean_name = re.sub(r'\(.*?\)|주식회사|\(주\)', '', target_name).strip()
        
        code = self._get_code(clean_name)
        if not code:
            # 상장사가 아니면 None 반환 (Proxy 로직으로 넘어감)
            return None

        print(f"   🔎 NaverStock: Tracking Peers for '{clean_name}' ({code})...")
        
        try:
            # 종목 메인 페이지
            url = f"https://finance.naver.com/item/main.naver?code={code}"
            res = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # '동일업종비교' 섹션 찾기
            compare_div = soup.select_one('div.section.trade_compare')
            if not compare_div: return None
            
            # 테이블 행(Rows) 추출
            rows = compare_div.select('table.tbl_home tr')
            
            pers = []
            # 테이블을 순회하며 'PER' 행을 찾음
            for row in rows:
                th = row.select_one('th')
                if th and 'PER' in th.text:
                    tds = row.select('td')
                    for td in tds:
                        try:
                            # 쉼표 제거 후 float 변환
                            txt = td.text.replace(',', '').strip()
                            if not txt or txt == 'N/A': continue
                            val = float(txt)
                            
                            # 유효한 PER만 수집 (0 이하, 200 이상 아웃라이어 제외)
                            if 0 < val < 200: 
                                pers.append(val)
                        except: pass
                    break
            
            if not pers: return None
            
            # 평균 PER 계산
            avg_per = sum(pers) / len(pers)
            print(f"      📊 Live Peer PER (Avg): {avg_per:.2f}x (Based on {len(pers)} peers)")
            
            return {"PER": avg_per, "Peers_Count": len(pers)}

        except Exception as e:
            print(f"      ⚠️ Peer Error: {e}")
            return None

    def get_proxy_multiple(self, sector_keyword):
        """
        비상장사를 위해 섹터 대표주(Proxy)의 PER를 가져옴
        """
        # 섹터별 대표주 매핑
        proxy_map = {
            "Bio": "삼성바이오로직스",
            "IT": "NAVER",
            "Game": "크래프톤",
            "Consumer": "아모레퍼시픽",
            "Manufacturing": "LG에너지솔루션",
            "Finance": "KB금융",
            "Logistics": "CJ대한통운"
        }
        
        proxy_name = proxy_map.get(sector_keyword)
        if not proxy_name: return 15.0 # Fallback Default
        
        print(f"   🔄 NaverStock: Using Proxy '{proxy_name}' for sector '{sector_keyword}'")
        data = self.get_market_multiple(proxy_name)
        return data['PER'] if data else 15.0