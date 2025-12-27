"""
Price Service
"""

import aiohttp
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from io import BytesIO

from src.core.config import config


logger = logging.getLogger(__name__)


class PriceService:
    """Service for fetching and managing prices"""
    
    def __init__(self):
        self.cache = {}
        self.cache_time = {}
        self.cache_duration = 30  # seconds
        
    async def get_all_prices(self) -> Dict:
        """Get all prices"""
        tasks = [
            self.get_gold_prices(),
            self.get_currency_prices(),
            self.get_crypto_prices()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "gold": results[0] if not isinstance(results[0], Exception) else {},
            "currencies": results[1] if not isinstance(results[1], Exception) else {},
            "crypto": results[2] if not isinstance(results[2], Exception) else {}
        }
    
    async def get_gold_prices(self) -> Dict:
        """Get gold prices from TGJU API"""
        cache_key = "gold_prices"
        
        # Check cache
        if self._is_cached(cache_key):
            return self.cache[cache_key]
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(config.TGJU_API_URL) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Parse TGJU data
                        gold_data = {
                            "18k": self._extract_price(data, "price_gram_18k"),
                            "24k": self._extract_price(data, "price_gram_24k"),
                            "ounce": self._extract_price(data, "price_ounce"),
                            "mithqal": self._extract_price(data, "price_mithqal"),
                            "coin_emami": self._extract_price(data, "coin_emami"),
                            "coin_nim": self._extract_price(data, "coin_nim"),
                            "coin_rob": self._extract_price(data, "coin_rob"),
                            "coin_gerami": self._extract_price(data, "coin_gerami"),
                            "change_24h": self._extract_change(data, "price_gram_24k"),
                            "change_7d": 0.0,  # Would need historical data
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        # Cache the result
                        self.cache[cache_key] = gold_data
                        self.cache_time[cache_key] = datetime.now()
                        
                        return gold_data
                        
        except Exception as e:
            logger.error(f"Error fetching gold prices: {e}")
            
        # Return cached or empty data
        return self.cache.get(cache_key, {})
    
    async def get_crypto_prices(self) -> List[Dict]:
        """Get cryptocurrency prices from CoinGecko"""
        cache_key = "crypto_prices"
        
        if self._is_cached(cache_key):
            return self.cache[cache_key]
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{config.COINGECKO_API_URL}/coins/markets"
                params = {
                    "vs_currency": "usd",
                    "ids": "bitcoin,ethereum,binancecoin,solana,cardano",
                    "order": "market_cap_desc",
                    "per_page": 50,
                    "page": 1,
                    "sparkline": False
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        crypto_list = []
                        for coin in data:
                            crypto_list.append({
                                "id": coin["id"],
                                "symbol": coin["symbol"],
                                "name": coin["name"],
                                "price": coin["current_price"],
                                "change_24h": coin["price_change_percentage_24h"],
                                "market_cap": coin["market_cap"],
                                "volume": coin["total_volume"],
                                "image": coin["image"]
                            })
                        
                        self.cache[cache_key] = crypto_list
                        self.cache_time[cache_key] = datetime.now()
                        
                        return crypto_list
                        
        except Exception as e:
            logger.error(f"Error fetching crypto prices: {e}")
            
        return self.cache.get(cache_key, [])
    
    async def generate_chart(self, symbol: str, period: str = "7d") -> Optional[BytesIO]:
        """Generate price chart"""
        try:
            # This is a simplified version
            # In production, use real historical data
            
            # Generate sample data
            dates = pd.date_range(end=datetime.now(), periods=100, freq='H')
            prices = np.random.normal(100, 10, 100).cumsum()
            
            # Create plot
            plt.figure(figsize=(10, 6))
            plt.plot(dates, prices, linewidth=2)
            plt.title(f"Price Chart - {symbol.upper()}")
            plt.xlabel("Date")
            plt.ylabel("Price ($)")
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # Save to bytes
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=100)
            plt.close()
            buf.seek(0)
            
            return buf
            
        except Exception as e:
            logger.error(f"Error generating chart: {e}")
            return None
    
    def _extract_price(self, data: Dict, key: str) -> float:
        """Extract price from TGJU data"""
        try:
            if key in data and "p" in data[key]:
                return float(data[key]["p"])
        except:
            pass
        return 0.0
    
    def _extract_change(self, data: Dict, key: str) -> float:
        """Extract price change from TGJU data"""
        try:
            if key in data and "d" in data[key]:
                return float(data[key]["d"].replace("%", ""))
        except:
            pass
        return 0.0
    
    def _is_cached(self, key: str) -> bool:
        """Check if data is cached and valid"""
        if key in self.cache and key in self.cache_time:
            age = datetime.now() - self.cache_time[key]
            return age.total_seconds() < self.cache_duration
        return False