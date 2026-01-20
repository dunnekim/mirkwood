"""
Market Scanner - Live Beta Calculation from Market Data

[Quantitative Finance]
This module calculates Adjusted Beta using:
1. Historical price data (5 years monthly)
2. Linear regression (Covariance/Variance method)
3. Blume's Adjustment: Adj Beta = 0.67 * Raw Beta + 0.33

[Data Source]
- yfinance: Yahoo Finance API wrapper
- Market Index: ^KS11 (KOSPI) for Korean stocks
"""

import logging
import warnings
import numpy as np
import pandas as pd
from typing import Optional, Tuple
from datetime import datetime, timedelta

# Suppress yfinance warnings
warnings.filterwarnings('ignore', category=FutureWarning)
logging.getLogger('yfinance').setLevel(logging.ERROR)

try:
    import yfinance as yf
except ImportError:
    raise ImportError(
        "yfinance is required for live beta calculation. "
        "Install with: pip install yfinance"
    )


class MarketScanner:
    """
    Real-time market data scanner for beta calculation
    
    [Methodology]
    - Uses 5 years of monthly adjusted close prices
    - Regression: Beta = Cov(Stock, Market) / Var(Market)
    - Blume's Adjustment for mean reversion
    
    [Korean Market]
    - Default market index: ^KS11 (KOSPI)
    - Ticker format: [6-digit code].KS (e.g., 005930.KS for Samsung)
    """
    
    def __init__(
        self, 
        market_index: str = "^KS11",
        lookback_years: int = 5,
        frequency: str = "1mo"
    ):
        """
        Args:
            market_index: Market benchmark ticker (default: KOSPI)
            lookback_years: Historical data period (default: 5 years)
            frequency: Data frequency ('1d', '1wk', '1mo')
        """
        self.market_index = market_index
        self.lookback_years = lookback_years
        self.frequency = frequency
        self.min_data_points = 24  # Minimum 2 years of monthly data
        
        # Cache for performance
        self._market_returns_cache = None
        self._cache_timestamp = None
        
        print(f"📡 MarketScanner initialized (Index: {market_index}, Lookback: {lookback_years}Y)")
    
    def _normalize_korean_ticker(self, ticker: str) -> str:
        """
        Normalize Korean stock tickers
        
        Examples:
            "005930" -> "005930.KS"
            "005930.KS" -> "005930.KS"
            "AAPL" -> "AAPL" (US stocks unchanged)
        
        Args:
            ticker: Input ticker
        
        Returns:
            Normalized ticker for yfinance
        """
        if not ticker:
            return ticker
        
        # If it's a 6-digit code without suffix, add .KS
        if ticker.isdigit() and len(ticker) == 6:
            return f"{ticker}.KS"
        
        return ticker
    
    def _fetch_returns(
        self, 
        ticker: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Optional[pd.Series]:
        """
        Fetch historical returns for a ticker
        
        Args:
            ticker: Stock ticker
            start_date: Start date
            end_date: End date
        
        Returns:
            Series of returns, or None if failed
        """
        try:
            # Download data
            data = yf.download(
                ticker, 
                start=start_date, 
                end=end_date, 
                interval=self.frequency,
                progress=False,
                show_errors=False
            )
            
            if data.empty or len(data) < self.min_data_points:
                logging.warning(
                    f"Insufficient data for {ticker}: {len(data)} points "
                    f"(minimum: {self.min_data_points})"
                )
                return None
            
            # Calculate returns
            if 'Adj Close' in data.columns:
                prices = data['Adj Close']
            elif 'Close' in data.columns:
                prices = data['Close']
            else:
                logging.error(f"No price data found for {ticker}")
                return None
            
            returns = prices.pct_change().dropna()
            
            if len(returns) < self.min_data_points:
                return None
            
            return returns
        
        except Exception as e:
            logging.warning(f"Failed to fetch data for {ticker}: {e}")
            return None
    
    def _get_market_returns(self) -> Optional[pd.Series]:
        """
        Get market index returns (with caching)
        
        Returns:
            Series of market returns
        """
        # Check cache (valid for 1 hour)
        if self._market_returns_cache is not None:
            if self._cache_timestamp and \
               (datetime.now() - self._cache_timestamp).seconds < 3600:
                return self._market_returns_cache
        
        # Fetch fresh data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * self.lookback_years)
        
        market_returns = self._fetch_returns(
            self.market_index, 
            start_date, 
            end_date
        )
        
        if market_returns is not None:
            self._market_returns_cache = market_returns
            self._cache_timestamp = datetime.now()
        
        return market_returns
    
    def _calculate_raw_beta(
        self, 
        stock_returns: pd.Series, 
        market_returns: pd.Series
    ) -> Optional[float]:
        """
        Calculate raw beta using covariance method
        
        Beta = Cov(Stock, Market) / Var(Market)
        
        Args:
            stock_returns: Stock return series
            market_returns: Market return series
        
        Returns:
            Raw beta, or None if calculation fails
        """
        try:
            # Align data (use intersection of dates)
            aligned = pd.concat([stock_returns, market_returns], axis=1, join='inner')
            aligned.columns = ['stock', 'market']
            aligned = aligned.dropna()
            
            if len(aligned) < self.min_data_points:
                logging.warning(
                    f"Insufficient aligned data: {len(aligned)} points "
                    f"(minimum: {self.min_data_points})"
                )
                return None
            
            # Calculate beta
            covariance = aligned['stock'].cov(aligned['market'])
            market_variance = aligned['market'].var()
            
            if market_variance == 0:
                logging.error("Market variance is zero, cannot calculate beta")
                return None
            
            raw_beta = covariance / market_variance
            
            return raw_beta
        
        except Exception as e:
            logging.error(f"Beta calculation failed: {e}")
            return None
    
    def _apply_blume_adjustment(self, raw_beta: float) -> float:
        """
        Apply Blume's Adjustment for beta mean reversion
        
        Adjusted Beta = (2/3) * Raw Beta + (1/3) * 1.0
        
        [Academic Basis]
        Blume (1971, 1975): Betas tend to revert toward market beta (1.0)
        Industry standard: Bloomberg, FactSet use this adjustment
        
        Args:
            raw_beta: Raw regression beta
        
        Returns:
            Adjusted beta
        """
        adjusted_beta = (raw_beta * 0.67) + (1.0 * 0.33)
        return adjusted_beta
    
    def get_beta(
        self, 
        ticker: str, 
        apply_blume: bool = True,
        fallback_beta: float = 1.0
    ) -> Tuple[float, str]:
        """
        Get adjusted beta for a stock ticker
        
        [Process]
        1. Normalize ticker (Korean format)
        2. Fetch stock and market returns
        3. Calculate raw beta via regression
        4. Apply Blume's adjustment (optional)
        5. Return fallback if any step fails
        
        Args:
            ticker: Stock ticker (e.g., "005930" or "005930.KS")
            apply_blume: Apply Blume's adjustment (default: True)
            fallback_beta: Fallback value if calculation fails
        
        Returns:
            (beta, source): Beta value and source indicator
                source: "Live", "Fallback"
        """
        # Normalize ticker
        normalized_ticker = self._normalize_korean_ticker(ticker)
        
        # Get market returns
        market_returns = self._get_market_returns()
        if market_returns is None:
            logging.warning(
                f"Failed to fetch market data for {self.market_index}, "
                f"using fallback beta: {fallback_beta}"
            )
            return fallback_beta, "Fallback"
        
        # Get stock returns
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * self.lookback_years)
        
        stock_returns = self._fetch_returns(
            normalized_ticker, 
            start_date, 
            end_date
        )
        
        if stock_returns is None:
            logging.warning(
                f"Failed to fetch stock data for {normalized_ticker}, "
                f"using fallback beta: {fallback_beta}"
            )
            return fallback_beta, "Fallback"
        
        # Calculate raw beta
        raw_beta = self._calculate_raw_beta(stock_returns, market_returns)
        
        if raw_beta is None:
            logging.warning(
                f"Beta calculation failed for {normalized_ticker}, "
                f"using fallback beta: {fallback_beta}"
            )
            return fallback_beta, "Fallback"
        
        # Apply Blume's adjustment
        if apply_blume:
            adjusted_beta = self._apply_blume_adjustment(raw_beta)
            logging.info(
                f"✅ {normalized_ticker}: Raw Beta = {raw_beta:.3f}, "
                f"Adjusted Beta = {adjusted_beta:.3f}"
            )
        else:
            adjusted_beta = raw_beta
            logging.info(f"✅ {normalized_ticker}: Raw Beta = {raw_beta:.3f}")
        
        return adjusted_beta, "Live"
    
    def get_beta_batch(
        self, 
        tickers: list, 
        apply_blume: bool = True,
        fallback_beta: float = 1.0
    ) -> dict:
        """
        Get betas for multiple tickers (sequential processing)
        
        Args:
            tickers: List of ticker symbols
            apply_blume: Apply Blume's adjustment
            fallback_beta: Fallback value
        
        Returns:
            {ticker: {"beta": float, "source": str}}
        """
        results = {}
        
        for ticker in tickers:
            if not ticker:
                continue
            
            beta, source = self.get_beta(ticker, apply_blume, fallback_beta)
            results[ticker] = {
                "beta": beta,
                "source": source
            }
        
        return results


# ==============================================================================
# TESTING UTILITIES
# ==============================================================================

def test_market_scanner():
    """
    Test MarketScanner with sample Korean stocks
    """
    print("=" * 70)
    print("🧪 MarketScanner Test - Korean Market")
    print("=" * 70)
    
    scanner = MarketScanner()
    
    # Test cases: (ticker, expected_range)
    test_cases = [
        ("005930", "Samsung Electronics - should be around 0.9-1.2"),
        ("000660", "SK Hynix - semiconductor, volatile, expect > 1.0"),
        ("035720", "Kakao - tech, high beta expected"),
        ("INVALID", "Invalid ticker - should use fallback"),
    ]
    
    for ticker, description in test_cases:
        print(f"\n📊 Testing: {ticker} ({description})")
        beta, source = scanner.get_beta(ticker)
        print(f"   Result: Beta = {beta:.3f}, Source = {source}")
    
    print("\n" + "=" * 70)
    print("✅ Test completed")
    print("=" * 70)


if __name__ == "__main__":
    # Run test if executed directly
    test_market_scanner()
