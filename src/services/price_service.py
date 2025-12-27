"""
Price Service - Fetch and manage prices
"""

import aiohttp
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from cachetools import TTLCache

logger = logging.getLogger(__name__)


class PriceService:
    """Service for fetching and managing prices"""
    
    def __init__(self):
        # Cache for 30 seconds
        self.cache = TTLCache(maxsize=100, ttl=30)
        
    async def get_all_prices(self) -> Dict[str, Any]:
        """Get all prices (gold, currency, crypto)"""
        try:
            # Check cache first
            cache_key = "all_prices"
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            # Fetch prices concurrently
            gold_task = self.get_gold_prices()
            currency_task = self.get_currency_prices()
            crypto_task = self.get_crypto_prices(limit=3)
            
            gold_data, currency_data, crypto_data = await asyncio.gather(
                gold_task, currency_task, crypto_task,
                return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(gold_data, Exception):
                logger.error(f"Error fetching gold: {gold_data}")
                gold_data = {}
            
            if isinstance(currency_data, Exception):
                logger.error(f"Error fetching currency: {currency_data}")
                currency_data = {}
            
            if isinstance(crypto_data, Exception):
                logger.error(f"Error fetching crypto: {crypto_data}")
                crypto_data = []
            
            # Combine results
            prices = {
                **gold_data,
                **currency_data,
                "crypto_list": crypto_data
            }
            
            # Add Bitcoin separately for easy access
            if crypto_data and len(crypto_data) > 0:
                btc = next((c for c in crypto_data if c['symbol'] == 'btc'), None)
                if btc:
                    prices['bitcoin'] = btc['price']
                    prices['bitcoin_change_24h'] = btc['change_24h']
            
            # Cache the result
            self.cache[cache_key] = prices
            
            return prices
            
        except Exception as e:
            logger.error(f"Error in get_all_prices: {e}")
            return {}
    
    async def get_gold_prices(self) -> Dict[str, float]:
        """Get gold prices from TGJU API"""
        try:
            cache_key = "gold_prices"
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.tgju.org/v1/data/sana.json",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Parse TGJU data
                        gold_prices = {}
                        
                        # Extract prices from TGJU format
                        for key, value in data.items():
                            if isinstance(value, dict) and 'p' in value:
                                price = value['p']
                                try:
                                    # Convert to float
                                    gold_prices[key] = float(price)
                                except (ValueError, TypeError):
                                    pass
                        
                        # Map to our format
                        result = {
                            # Iranian gold prices (in Tomans)
                            'gold_18k': gold_prices.get('price_gram_18k', 0),
                            'gold_24k': gold_prices.get('price_gram_24k', 0),
                            'coin_emami': gold_prices.get('coin_emami', 0),
                            'coin_nim': gold_prices.get('coin_nim', 0),
                            'coin_rob': gold_prices.get('coin_rob', 0),
                            'coin_gerami': gold_prices.get('coin_gerami', 0),
                            
                            # Global gold prices (in USD)
                            'ounce': gold_prices.get('price_ounce', 0),
                            'mithqal': gold_prices.get('price_mithqal', 0),
                            
                            # Changes
                            'gold_change_24h': 0.0,  # TGJU doesn't provide this directly
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        self.cache[cache_key] = result
                        return result
            
            return {}
            
        except asyncio.TimeoutError:
            logger.error("Timeout fetching gold prices")
            return {}
        except Exception as e:
            logger.error(f"Error fetching gold prices: {e}")
            return {}
    
    async def get_currency_prices(self) -> Dict[str, float]:
        """Get currency prices from TGJU API"""
        try:
            cache_key = "currency_prices"
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.tgju.org/v1/data/sana.json",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Parse currency data
                        currencies = {}
                        
                        # Extract currency prices
                        currency_mapping = {
                            'usd': 'price_dollar_rl',
                            'eur': 'price_eur',
                            'gbp': 'price_gbp',
                            'aed': 'price_aed',
                            'try': 'price_try'
                        }
                        
                        for key, tgju_key in currency_mapping.items():
                            if tgju_key in data and 'p' in data[tgju_key]:
                                try:
                                    currencies[key] = float(data[tgju_key]['p'])
                                except (ValueError, TypeError):
                                    currencies[key] = 0
                        
                        # Add changes if available
                        currencies['usd_change_24h'] = 0.0
                        currencies['timestamp'] = datetime.now().isoformat()
                        
                        self.cache[cache_key] = currencies
                        return currencies
            
            return {}
            
        except asyncio.TimeoutError:
            logger.error("Timeout fetching currency prices")
            return {}
        except Exception as e:
            logger.error(f"Error fetching currency prices: {e}")
            return {}
    
    async def get_crypto_prices(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get cryptocurrency prices from CoinGecko"""
        try:
            cache_key = f"crypto_prices_{limit}"
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            # Popular cryptocurrencies
            coin_ids = [
                "bitcoin", "ethereum", "binancecoin", 
                "solana", "cardano", "ripple",
                "dogecoin", "polkadot", "litecoin",
                "chainlink"
            ][:limit]
            
            ids_param = ",".join(coin_ids)
            
            async with aiohttp.ClientSession() as session:
                url = "https://api.coingecko.com/api/v3/coins/markets"
                params = {
                    "vs_currency": "usd",
                    "ids": ids_param,
                    "order": "market_cap_desc",
                    "per_page": limit,
                    "page": 1,
                    "sparkline": False,
                    "price_change_percentage": "24h"
                }
                
                headers = {
                    "User-Agent": "MarketPulsePro/1.0"
                }
                
                async with session.get(
                    url, params=params, headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        cryptos = []
                        for coin in data:
                            cryptos.append({
                                "id": coin["id"],
                                "symbol": coin["symbol"],
                                "name": coin["name"],
                                "price": coin["current_price"],
                                "change_24h": coin.get("price_change_percentage_24h", 0),
                                "market_cap": coin["market_cap"],
                                "volume": coin["total_volume"],
                                "image": coin["image"]
                            })
                        
                        self.cache[cache_key] = cryptos
                        return cryptos
                    else:
                        logger.error(f"CoinGecko API error: {response.status}")
                        return []
            
        except asyncio.TimeoutError:
            logger.error("Timeout fetching crypto prices")
            return []
        except Exception as e:
            logger.error(f"Error fetching crypto prices: {e}")
            return []
    
    async def get_specific_price(self, symbol: str) -> Optional[float]:
        """Get specific price by symbol"""
        try:
            symbol = symbol.lower()
            
            if symbol in ['gold', 'طلا']:
                prices = await self.get_gold_prices()
                return prices.get('gold_24k')
            
            elif symbol in ['usd', 'دلار']:
                prices = await self.get_currency_prices()
                return prices.get('usd')
            
            elif symbol in ['btc', 'bitcoin', 'بیت‌کوین']:
                cryptos = await self.get_crypto_prices(limit=1)
                if cryptos and cryptos[0]['symbol'] == 'btc':
                    return cryptos[0]['price']
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting specific price for {symbol}: {e}")
            return None
