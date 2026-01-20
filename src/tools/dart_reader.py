"""
DART Reader V2.0

[Improvements]
1. Multi-Key Search: 매출액, 영업수익, 이자수익 등 동의어 처리
2. Smart Year Search: 최신 보고서부터 역순 검색 (2026 → 2025 → 2024)
3. Unit Scaling: 원 → 억 원 자동 변환
4. Consolidated Priority: 연결재무제표 우선, 별도 fallback

[Fix]
- 모비릭스 같은 게임사의 "영업수익" 인식
- 2026년 1월 기준 최신 보고서 검색
"""

import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class DartReader:
    def __init__(self):
        self.api_key = os.getenv("DART_API_KEY")
        if not self.api_key:
            print("⚠️ DART_API_KEY is missing. Please check .env file")
            print("   DART features will be disabled.")
        else:
            # API 키가 있으면 간단히 검증 (길이 체크)
            if len(self.api_key) < 20:
                print("⚠️ DART_API_KEY seems invalid (too short). Please check .env file")
        
        # [핵심 1] 동의어 사전 (Synonyms Dictionary)
        # 업종별로 매출/이익을 부르는 이름이 다름을 처리
        self.ACCOUNT_MAP = {
            "revenue": [
                "매출액", "영업수익", "수익(매출액)", "매출", 
                "이자수익", "보험료수익"  # 금융사 대비
            ],
            "profit": [
                "영업이익", "영업이익(손실)", "영업손실", "당기순이익"
            ],
            "net_income": [
                "당기순이익", "당기순이익(손실)", "연결당기순이익"
            ]
        }
    
    def _get_corp_code(self, company_name):
        """
        기업명 → 고유번호(corp_code) 변환
        
        [Improvement]
        - 정확 일치 우선
        - 부분 매칭 (포함 검색)
        - 괄호/주식회사 등 제거 후 비교
        
        [Note]
        corpCode.xml을 매번 다운받으면 느리므로 로컬 캐싱 권장
        """
        xml_file = 'corp_code.xml'
        
        # API 키 확인
        if not self.api_key:
            print("   ❌ DART_API_KEY is missing. Cannot search DART.")
            return None
        
        # XML 파일이 없으면 다운로드
        if not os.path.exists(xml_file):
            url = 'https://opendart.fss.or.kr/api/corpCode.xml'
            params = {'crtfc_key': self.api_key}
            try:
                print("   📥 Downloading corp_code.xml from DART...")
                resp = requests.get(url, params=params, timeout=10)
                if resp.status_code != 200:
                    print(f"   ❌ DART API Error: HTTP {resp.status_code}")
                    if resp.status_code == 401:
                        print("      Hint: Check if DART_API_KEY is valid")
                    return None
                with open(xml_file, 'wb') as f:
                    f.write(resp.content)
                print("   ✅ Downloaded corp_code.xml")
            except Exception as e:
                print(f"   ❌ Failed to download corp_code.xml: {e}")
                return None
        
        # 입력 기업명 정규화 (괄호, 주식회사 등 제거)
        def normalize_name(name):
            """기업명 정규화"""
            if not name:
                return ""
            # 괄호 내용 제거: "삼성전자(주)" → "삼성전자"
            import re
            name = re.sub(r'\([^)]*\)', '', name)
            # 주식회사, (주) 등 제거
            name = name.replace('주식회사', '').replace('(주)', '').replace('(유)', '').strip()
            return name
        
        normalized_input = normalize_name(company_name)
        
        # XML 파싱
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # 1차: 정확 일치
            for child in root.findall('list'):
                nm = child.find('corp_name')
                if nm is not None and nm.text:
                    corp_name = nm.text.strip()
                    if corp_name == company_name:
                        code = child.find('corp_code')
                        if code is not None and code.text:
                            print(f"   ✅ Exact match found: '{corp_name}'")
                            return code.text.strip()
            
            # 2차: 정규화 후 일치
            for child in root.findall('list'):
                nm = child.find('corp_name')
                if nm is not None and nm.text:
                    corp_name = nm.text.strip()
                    normalized_corp = normalize_name(corp_name)
                    if normalized_corp == normalized_input and normalized_input:
                        code = child.find('corp_code')
                        if code is not None and code.text:
                            print(f"   ✅ Normalized match found: '{corp_name}' (input: '{company_name}')")
                            return code.text.strip()
            
            # 3차: 부분 포함 검색 (입력이 회사명에 포함되거나 그 반대)
            for child in root.findall('list'):
                nm = child.find('corp_name')
                if nm is not None and nm.text:
                    corp_name = nm.text.strip()
                    normalized_corp = normalize_name(corp_name)
                    
                    # 양방향 포함 검색
                    if normalized_input and normalized_corp:
                        if normalized_input in normalized_corp or normalized_corp in normalized_input:
                            # 최소 길이 체크 (너무 짧은 매칭 방지)
                            min_len = min(len(normalized_input), len(normalized_corp))
                            if min_len >= 2:  # 최소 2글자 이상
                                code = child.find('corp_code')
                                if code is not None and code.text:
                                    print(f"   ⚠️ Partial match found: '{corp_name}' (input: '{company_name}')")
                                    return code.text.strip()
            
        except Exception as e:
            print(f"   ❌ Error parsing corp_code.xml: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"   ❌ No matching company found in DART for '{company_name}'")
        print(f"      Hint: Try using exact legal name (e.g., '삼성전자(주)')")
        return None
    
    def _find_value_by_keys(self, row_dict, keys):
        """
        여러 계정명 키워드 중 하나라도 매칭되면 값 반환
        
        Args:
            row_dict: DART API response item
            keys: 찾을 계정명 리스트 (e.g., ["매출액", "영업수익"])
        
        Returns:
            float or None
        """
        acct_name = row_dict.get('account_nm', '').replace(" ", "")
        
        # 정확히 일치하거나, 포함되는 경우 체크
        for key in keys:
            if key in acct_name:
                val = row_dict.get('thstrm_amount', '0').strip()  # 당기 금액
                if not val:
                    val = '0'
                try:
                    return float(val.replace(',', ''))
                except:
                    return 0.0
        
        return None
    
    def get_financial_summary(self, company_name):
        """
        DART에서 최신 재무 데이터 조회
        
        [Logic]
        1. 기업명 → corp_code 변환
        2. 최신 연도부터 역순 검색 (2026 → 2025 → 2024)
        3. 보고서 우선순위: 사업보고서(11011) > 3분기(11014) > 반기(11012) > 1분기(11013)
        4. 연결재무제표(CFS) 우선, 없으면 별도(OFS)
        5. 계정명 동의어 처리 (매출액/영업수익/이자수익 등)
        
        Args:
            company_name: 회사명 (정확한 법인명)
        
        Returns:
            {
                "revenue_bn": float,
                "op_bn": float,
                "source": str
            } or None
        """
        # API 키 확인
        if not self.api_key:
            print(f"   ❌ DART: API key not configured")
            return None
        
        corp_code = self._get_corp_code(company_name)
        if not corp_code:
            print(f"   ❌ DART: Corp code not found for '{company_name}'")
            print(f"      Hint: Company may not be listed or name mismatch")
            print(f"      Try: Use exact legal name from DART website")
            return None
        
        # [핵심 2] 최신 보고서 찾기 (역순 검색)
        current_year = datetime.now().year
        target_years = [current_year, current_year - 1, current_year - 2]  # 올해, 작년, 재작년
        
        # 보고서 코드 우선순위: 11011(사업), 11014(3분기), 11012(반기), 11013(1분기)
        report_codes = ['11011', '11014', '11012', '11013']
        
        final_data = {}
        found_report = False
        source_tag = ""
        
        print(f"   🔎 Searching DART for '{company_name}' (Corp Code: {corp_code})...")
        
        for year in target_years:
            if found_report:
                break
            
            # 단일판매 공급계약 등 수시공시는 제외, 정기공시만 조회
            # 주요 계정 조회 API (fnlttSinglAcnt) 사용
            url = "https://opendart.fss.or.kr/api/fnlttSinglAcnt.json"
            
            for reprt_code in report_codes:
                params = {
                    'crtfc_key': self.api_key,
                    'corp_code': corp_code,
                    'bsns_year': str(year),
                    'reprt_code': reprt_code,
                }
                
                try:
                    response = requests.get(url, params=params, timeout=10)
                    
                    # HTTP 에러 체크
                    if response.status_code != 200:
                        if response.status_code == 401:
                            print(f"   ❌ DART API Authentication Error (401)")
                            print(f"      Hint: Check if DART_API_KEY is valid")
                            return None
                        continue  # 다음 보고서 시도
                    
                    res = response.json()
                    
                    # API 응답 상태 체크
                    status = res.get('status')
                    if status != '000':
                        error_msg = res.get('message', 'Unknown error')
                        if status == '013':
                            # 해당 보고서 없음 - 정상 (다음 보고서 시도)
                            continue
                        elif status == '800' or status == '900':
                            print(f"   ❌ DART API Error: {error_msg} (Status: {status})")
                            if status == '800':
                                print(f"      Hint: API key may be invalid or expired")
                            return None
                        # 기타 에러는 무시하고 다음 시도
                        continue
                    
                    if res.get('list'):
                        # 데이터 찾음!
                        data_list = res['list']
                        
                        rev = 0
                        op = 0
                        
                        # 연결재무제표 우선 (CFS), 없으면 별도(OFS)
                        # DART API는 섞여서 오므로 'fs_div' 확인 필요
                        # 'CFS': 연결, 'OFS': 별도
                        
                        is_consolidated = False
                        
                        # 1차 패스: 연결(CFS) 찾기
                        for item in data_list:
                            if item.get('fs_div') == 'CFS':
                                is_consolidated = True
                                
                                v_rev = self._find_value_by_keys(item, self.ACCOUNT_MAP['revenue'])
                                if v_rev and rev == 0:
                                    rev = v_rev
                                
                                v_op = self._find_value_by_keys(item, self.ACCOUNT_MAP['profit'])
                                if v_op and op == 0:
                                    op = v_op
                        
                        # 연결 데이터가 없거나 0이면 별도(OFS)로 재시도
                        if rev == 0:
                            for item in data_list:
                                if item.get('fs_div') == 'OFS':
                                    v_rev = self._find_value_by_keys(item, self.ACCOUNT_MAP['revenue'])
                                    if v_rev and rev == 0:
                                        rev = v_rev
                                    
                                    v_op = self._find_value_by_keys(item, self.ACCOUNT_MAP['profit'])
                                    if v_op and op == 0:
                                        op = v_op
                        
                        # 단위 보정 (DART는 기본 단위가 원)
                        # 억 단위로 변환
                        rev_bn = rev / 100000000
                        op_bn = op / 100000000
                        
                        # 보고서 이름 매핑
                        report_name_map = {
                            '11011': '4Q(Year)', 
                            '11012': '2Q', 
                            '11013': '1Q', 
                            '11014': '3Q'
                        }
                        period_name = report_name_map.get(reprt_code, reprt_code)
                        
                        source_tag = f"DART {year}.{period_name} ({'CFS' if is_consolidated else 'OFS'})"
                        
                        final_data = {
                            "revenue_bn": rev_bn,
                            "op_bn": op_bn,
                            "source": source_tag,
                            "period": f"{year}.{period_name}"
                        }
                        
                        print(f"      ✅ Found: {source_tag}")
                        print(f"         Revenue: {rev_bn:.1f}억, OP: {op_bn:.1f}억")
                        
                        found_report = True
                        break  # Break report code loop
                
                except requests.exceptions.Timeout:
                    print(f"      ⏱️ DART API timeout for {year}.{reprt_code}")
                    continue
                except Exception as e:
                    print(f"      ⚠️ Error parsing DART {year}.{reprt_code}: {e}")
                    continue
        
        if not final_data:
            print("   ❌ No data found in DART")
            print("      Possible reasons:")
            print("      - Company name mismatch (try exact legal name)")
            print("      - Not a listed company")
            print("      - No recent financial reports filed")
            return None
        
        return final_data
