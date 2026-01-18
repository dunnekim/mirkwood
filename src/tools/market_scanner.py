"""
Market Scanner - Real-time Beta Calculation

[Purpose]
Calculate beta from actual market data (not just using published numbers).

[Method]
1. Fetch historical prices (yfinance)
2. Calculate log returns
3. Linear regression (Stock returns vs Market returns)
4. Apply Blume's adjustment: Adjusted Beta = (Raw Beta × 0.67) + (1.0 × 0.33)

[IB Standard]
This is how real investment banks calculate beta for valuation work.
Bloomberg/Reuters betas are reference only - we build our own House View.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Optional, Tuple


class MarketScanner:
    """
    Market data scanner and beta calculator
    
    [Korean Market]
    - KOSPI stocks: ticker.KS (e.g., 005930.KS = Samsung)
    - KOSDAQ stocks: ticker.KQ
    - Market index: ^KS11 (KOSPI Composite)
    """
    
    def __init__(self, market_index: str = "^KS11"):
        """
        Args:
            market_index: Market index ticker (default: ^KS11 for KOSPI)
        """
        self.market_index = market_index
        
        # Beta calculation modes
        self.MODES = {
            '5Y_MONTHLY': {'period': '5y', 'interval': '1mo', 'min_points': 40},
            '2Y_WEEKLY': {'period': '2y', 'interval': '1wk', 'min_points': 70},
            '1Y_DAILY': {'period': '1y', 'interval': '1d', 'min_points': 180}
        }
    
    def _get_ticker_symbol(self, company_code: str, exchange: str = 'KS') -> str:
        """
        종목코드를 야후파이낸스 심볼로 변환
        
        Args:
            company_code: 6-digit stock code (e.g., '005930')
            exchange: 'KS' (KOSPI) or 'KQ' (KOSDAQ)
        
        Returns:
            Yahoo Finance ticker (e.g., '005930.KS')
        """
        # Remove any existing suffix
        code = company_code.replace('.KS', '').replace('.KQ', '')
        return f"{code}.{exchange}"
    
    def _try_both_exchanges(self, company_code: str, period: str, interval: str) -> Optional[pd.DataFrame]:
        """
        Try both KOSPI and KOSDAQ exchanges
        
        Returns:
            DataFrame or None
        """
        for exchange in ['KS', 'KQ']:
            try:
                ticker = self._get_ticker_symbol(company_code, exchange)
                data = yf.download(
                    ticker, 
                    period=period, 
                    interval=interval, 
                    progress=False,
                    show_errors=False
                )
                
                if not data.empty and len(data) > 10:
                    print(f"      ✅ Found on {exchange} exchange")
                    return data
            
            except:
                continue
        
        return None
    
    def calculate_beta(
        self, 
        company_code: str, 
        mode: str = '5Y_MONTHLY'
    ) -> Dict:
        """
        Calculate beta using linear regression
        
        [Process]
        1. Fetch historical prices (Stock + Market)
        2. Calculate returns (log returns)
        3. Linear regression: Stock returns ~ Market returns
        4. Apply Blume's adjustment
        
        Args:
            company_code: 6-digit Korean stock code (e.g., '005930')
            mode: '5Y_MONTHLY', '2Y_WEEKLY', or '1Y_DAILY'
        
        Returns:
            {
                'raw_beta': float,
                'adjusted_beta': float,
                'r_squared': float,
                'p_value': float,
                'data_points': int,
                'method': str,
                'confidence': str ('High'/'Medium'/'Low')
            }
        """
        if mode not in self.MODES:
            mode = '5Y_MONTHLY'
        
        config = self.MODES[mode]
        period = config['period']
        interval = config['interval']
        min_points = config['min_points']
        
        print(f"   📈 MarketScanner: Calculating Beta for {company_code}")
        print(f"      Mode: {mode} (Period: {period}, Interval: {interval})")
        
        try:
            # ============================================================
            # 1. FETCH DATA (Stock + Market)
            # ============================================================
            
            # Try to get stock data from both exchanges
            stock_data = self._try_both_exchanges(company_code, period, interval)
            
            if stock_data is None or stock_data.empty:
                print(f"      ❌ No data available for {company_code}")
                return self._default_beta("No data available")
            
            # Fetch market index
            market_data = yf.download(
                self.market_index, 
                period=period, 
                interval=interval, 
                progress=False,
                show_errors=False
            )
            
            if market_data.empty:
                print(f"      ❌ Market index data unavailable")
                return self._default_beta("Market data unavailable")
            
            # ============================================================
            # 2. CALCULATE RETURNS
            # ============================================================
            
            # Get Adjusted Close prices
            stock_prices = stock_data['Adj Close'] if 'Adj Close' in stock_data.columns else stock_data['Close']
            market_prices = market_data['Adj Close'] if 'Adj Close' in market_data.columns else market_data['Close']
            
            # Align dates (inner join)
            aligned = pd.DataFrame({
                'stock': stock_prices,
                'market': market_prices
            }).dropna()
            
            if len(aligned) < min_points:
                print(f"      ⚠️ Insufficient data points: {len(aligned)} < {min_points}")
                return self._default_beta(f"Insufficient data ({len(aligned)} points)")
            
            # Calculate percentage returns
            stock_returns = aligned['stock'].pct_change().dropna()
            market_returns = aligned['market'].pct_change().dropna()
            
            # Align returns
            returns_df = pd.DataFrame({
                'stock': stock_returns,
                'market': market_returns
            }).dropna()
            
            if len(returns_df) < min_points * 0.7:
                print(f"      ⚠️ Too many NaN after returns: {len(returns_df)}")
                return self._default_beta("Insufficient valid returns")
            
            # ============================================================
            # 3. LINEAR REGRESSION
            # ============================================================
            
            # Regression: Stock ~ Market
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                returns_df['market'], 
                returns_df['stock']
            )
            
            raw_beta = slope
            r_squared = r_value ** 2
            
            # ============================================================
            # 4. ADJUSTED BETA (Blume's Method)
            # ============================================================
            
            # Blume (1971): Betas tend to regress toward 1
            # Adjusted Beta = (Raw Beta × 2/3) + (Market Beta × 1/3)
            # Market Beta = 1.0
            
            adjusted_beta = (raw_beta * 0.67) + (1.0 * 0.33)
            
            # ============================================================
            # 5. CONFIDENCE ASSESSMENT
            # ============================================================
            
            confidence = "Low"
            if r_squared >= 0.30 and p_value < 0.05:
                confidence = "High"
            elif r_squared >= 0.15 or p_value < 0.10:
                confidence = "Medium"
            
            print(f"      📊 Raw Beta: {raw_beta:.3f}")
            print(f"      📊 Adjusted Beta: {adjusted_beta:.3f} (Blume)")
            print(f"      📊 R²: {r_squared:.3f}, p-value: {p_value:.4f}")
            print(f"      📊 Data Points: {len(returns_df)}, Confidence: {confidence}")
            
            return {
                'raw_beta': raw_beta,
                'adjusted_beta': adjusted_beta,
                'r_squared': r_squared,
                'p_value': p_value,
                'data_points': len(returns_df),
                'method': mode,
                'confidence': confidence,
                'intercept': intercept,
                'std_error': std_err,
                'success': True
            }
        
        except Exception as e:
            print(f"      ❌ Beta calculation error: {e}")
            return self._default_beta(f"Calculation error: {str(e)}")
    
    def _default_beta(self, reason: str) -> Dict:
        """
        Return default beta when calculation fails
        
        Args:
            reason: Failure reason
        
        Returns:
            Default beta result (1.0)
        """
        print(f"      ⚠️ Using Default Beta (1.0): {reason}")
        
        return {
            'raw_beta': 1.0,
            'adjusted_beta': 1.0,
            'r_squared': 0.0,
            'p_value': 1.0,
            'data_points': 0,
            'method': 'default',
            'confidence': 'Default',
            'success': False,
            'reason': reason
        }
    
    def get_beta(
        self, 
        company_code: str, 
        mode: str = '5Y_MONTHLY'
    ) -> float:
        """
        Get adjusted beta (convenience method)
        
        Args:
            company_code: Stock code
            mode: Calculation mode
        
        Returns:
            Adjusted beta (float)
        """
        result = self.calculate_beta(company_code, mode)
        return result['adjusted_beta']
    
    def get_current_price(self, company_code: str) -> Optional[float]:
        """
        Get current stock price
        
        Args:
            company_code: Stock code
        
        Returns:
            Current price or None
        """
        try:
            # Try both exchanges
            for exchange in ['KS', 'KQ']:
                ticker = self._get_ticker_symbol(company_code, exchange)
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # Try different price fields
                for field in ['currentPrice', 'regularMarketPrice', 'previousClose']:
                    if field in info and info[field]:
                        price = float(info[field])
                        if price > 0:
                            print(f"      💰 Current Price: {price:,.0f}원 ({exchange})")
                            return price
            
            return None
        
        except Exception as e:
            print(f"      ⚠️ Price fetch error: {e}")
            return None
    
    def get_market_cap(self, company_code: str) -> Optional[float]:
        """
        Get market capitalization
        
        Args:
            company_code: Stock code
        
        Returns:
            Market cap in million KRW or None
        """
        try:
            for exchange in ['KS', 'KQ']:
                ticker = self._get_ticker_symbol(company_code, exchange)
                stock = yf.Ticker(ticker)
                info = stock.info
                
                if 'marketCap' in info and info['marketCap']:
                    # yfinance returns market cap in company's currency (KRW for Korean stocks)
                    mc_krw = float(info['marketCap'])
                    mc_mil = mc_krw / 1000000  # Convert to million KRW
                    
                    print(f"      📊 Market Cap: {mc_mil:,.0f}백만원 ({exchange})")
                    return mc_mil
            
            return None
        
        except Exception as e:
            print(f"      ⚠️ Market cap fetch error: {e}")
            return None
