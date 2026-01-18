import OpenDartReader
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

class DartReader:
    def __init__(self):
        # API Key 로드 (환경변수 없으면 하드코딩된 키 사용)
        api_key = os.getenv("DART_API_KEY", "1bc069b4d38cfd0dafd1445c19348771ed58f471")
        self.dart = OpenDartReader(api_key)

    def get_financial_summary(self, corp_name):
        print(f"   🔍 DART: Searching official records for '{corp_name}'...")
        try:
            # [CRITICAL FIX] 함수명: finstate (NOT fin_stat)
            # 2023년 사업보고서 (코드 11011)
            df = self.dart.finstate(corp_name, 2023, "11011") 
            
            if df is None or df.empty:
                print("      -> DART 데이터 없음 (비외감/이름불일치)")
                return None

            def _extract(names):
                for n in names:
                    rows = df[df['account_nm'].str.contains(n, na=False)]
                    if not rows.empty:
                        val = rows.iloc[0]['thstrm_amount']
                        try:
                            return round(float(str(val).replace(",","")) / 100000000, 1)
                        except: continue
                return 0

            return {
                "revenue_bn": _extract(["매출액", "영업수익"]),
                "profit_bn": _extract(["영업이익", "영업손실"]),
                "assets_bn": _extract(["자산총계"]),
                "debt_bn": _extract(["부채총계"]),
                "source": "OpenDart (Audit)"
            }

        except Exception as e:
            # fin_stat 에러가 또 나면 여기서 잡힙니다.
            print(f"      ⚠️ DART Error: {e}")
            return None