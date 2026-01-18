# src/tools/market_data.py
import FinanceDataReader as fdr
import pandas as pd
import datetime

class MarketDataTerminal:
    def __init__(self):
        # 섹터별 대표 대장주(Proxy) Ticker
        self.proxies = {
            "K-Beauty": ["000900", "192820", "237690"], # 아모레, 코스맥스, 클리오
            "Tech/SaaS": ["035420", "035720", "253450"], # 네이버, 카카오, 스튜디오드래곤
            "F&B": ["097950", "271560", "005300"],       # CJ, 오리온, 롯데칠성
            "Auto/Parts": ["005380", "012330", "009900"],# 현대차, 모비스, 명신산업
            "General": ["005930"]                        # 삼성전자 (지수 대용)
        }

    def get_sector_momentum(self, sector_name):
        """
        해당 섹터의 최근 3개월 주가 수익률(Momentum)을 계산하여
        멀티플 조정 계수(Adjustment Factor)를 반환.
        (예: 섹터가 10% 올랐으면 멀티플도 1.1배 상향)
        """
        print(f"   📈 Market Data: Analyzing momentum for '{sector_name}'...")
        
        # 1. 섹터 매핑
        target_key = "General"
        if "Beauty" in sector_name or "화장품" in sector_name: target_key = "K-Beauty"
        elif "Tech" in sector_name or "SaaS" in sector_name: target_key = "Tech/SaaS"
        elif "F&B" in sector_name or "식품" in sector_name: target_key = "F&B"
        elif "Manu" in sector_name or "제조" in sector_name: target_key = "Auto/Parts"

        tickers = self.proxies.get(target_key, self.proxies["General"])
        
        # 2. 데이터 조회 (최근 60일 = 약 3개월)
        avg_return = 0
        count = 0
        
        end_date = datetime.datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.datetime.now() - datetime.timedelta(days=60)).strftime("%Y-%m-%d")

        for code in tickers:
            try:
                df = fdr.DataReader(code, start_date, end_date)
                if not df.empty and len(df) > 10:
                    first = df['Close'].iloc[0]
                    last = df['Close'].iloc[-1]
                    ret = (last - first) / first
                    avg_return += ret
                    count += 1
            except:
                continue

        if count == 0: return 1.0 # 데이터 없으면 중립
        
        sector_trend = avg_return / count
        # 조정 계수: -20% ~ +20% 사이로 캡(Cap) 적용 (안전장치)
        adjustment = max(0.8, min(1.2, 1.0 + sector_trend))
        
        print(f"      👉 {target_key} Trend: {sector_trend*100:.1f}% -> Adj Factor: {adjustment:.2f}x")
        return adjustment