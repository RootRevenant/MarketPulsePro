import aiohttp
import asyncio
import logging
from datetime import datetime
from cachetools import TTLCache

logger = logging.getLogger(__name__)

class PriceService:
    def __init__(self):
        self.cache = TTLCache(maxsize=100, ttl=30)
    
    async def get_all_prices(self):
        try:
            cache_key = "all_prices"
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            gold_task = self.get_gold_prices()
            currency_task = self.get_currency_prices()
            
            gold_data, currency_data = await asyncio.gather(
                gold_task, currency_task, return_exceptions=True
            )
            
            prices = {}
            if not isinstance(gold_data, Exception):
                prices.update(gold_data)
            if not isinstance(currency_data, Exception):
                prices.update(currency_data)
            
            self.cache[cache_key] = prices
            return prices
            
        except Exception as e:
            logger.error(f"Error in get_all_prices: {e}")
            return {}
    
    async def get_gold_prices(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.tgju.org/v1/data/sana.json",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        gold_prices = {}
                        for key, value in data.items():
                            if isinstance(value, dict) and 'p' in value:
                                try:
                                    gold_prices[key] = float(value['p'])
                                except:
                                    pass
                        
                        result = {
                            'gold_18k': gold_prices.get('price_gram_18k', 0),
                            'gold_24k': gold_prices.get('price_gram_24k', 0),
                            'coin_emami': gold_prices.get('coin_emami', 0),
                            'ounce': gold_prices.get('price_ounce', 0),
                            'timestamp': datetime.now().isoformat()
                        }
                        return result
            return {}
        except Exception as e:
            logger.error(f"Error fetching gold prices: {e}")
            return {}
    
    async def get_currency_prices(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.tgju.org/v1/data/sana.json",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        currencies = {}
                        currency_mapping = {
                            'usd': 'price_dollar_rl',
                            'eur': 'price_eur',
                            'gbp': 'price_gbp'
                        }
                        for key, tgju_key in currency_mapping.items():
                            if tgju_key in data and 'p' in data[tgju_key]:
                                try:
                                    currencies[key] = float(data[tgju_key]['p'])
                                except:
                                    currencies[key] = 0
                        currencies['timestamp'] = datetime.now().isoformat()
                        return currencies
            return {}
        except Exception as e:
            logger.error(f"Error fetching currency prices: {e}")
            return {}