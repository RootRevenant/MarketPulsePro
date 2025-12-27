"""
News Service - Fetch and manage news
"""

import aiohttp
import feedparser
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from cachetools import TTLCache
import html

logger = logging.getLogger(__name__)


class NewsService:
    """Service for fetching and managing news"""
    
    def __init__(self):
        self.cache = TTLCache(maxsize=50, ttl=1800)  # 30 minutes cache
        
    async def get_latest_news(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get latest news from RSS feeds"""
        try:
            cache_key = f"news_{limit}"
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            # RSS feeds (Iranian economic news)
            rss_feeds = [
                "https://www.tasnimnews.com/fa/rss/feed/0/7/اقتصادی",
                "https://www.farsnews.ir/rss/economy",
                "https://www.isna.ir/rss/tp/14",  # اقتصادی
                "https://www.mehrnews.com/rss/tp/109"  # اقتصادی
            ]
            
            # Fetch all feeds concurrently
            tasks = [self._fetch_feed(feed) for feed in rss_feeds]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine and filter results
            all_news = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Error fetching feed: {result}")
                    continue
                if result:
                    all_news.extend(result)
            
            # Sort by date (newest first)
            all_news.sort(key=lambda x: x.get('published', datetime.min), reverse=True)
            
            # Remove duplicates based on title similarity
            unique_news = self._remove_duplicates(all_news)
            
            # Take only requested number of items
            latest_news = unique_news[:limit]
            
            # Cache the result
            self.cache[cache_key] = latest_news
            
            return latest_news
            
        except Exception as e:
            logger.error(f"Error in get_latest_news: {e}")
            return []
    
    async def _fetch_feed(self, feed_url: str) -> List[Dict[str, Any]]:
        """Fetch and parse a single RSS feed"""
        try:
            # Use feedparser with aiohttp for better performance
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    feed_url,
                    timeout=aiohttp.ClientTimeout(total=10),
                    headers={'User-Agent': 'MarketPulsePro/1.0'}
                ) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Parse with feedparser
                        feed = feedparser.parse(content)
                        
                        news_items = []
                        for entry in feed.entries[:10]:  # Get first 10 entries
                            try:
                                # Parse date
                                published = entry.get('published_parsed')
                                if published:
                                    published_dt = datetime(*published[:6])
                                else:
                                    published_dt = datetime.now()
                                
                                # Clean title
                                title = html.unescape(entry.title)
                                title = title.strip()
                                
                                # Get source from feed
                                source = feed.feed.get('title', 'منبع نامشخص')
                                if not source or source == 'نامشخص':
                                    source = self._extract_source_from_url(feed_url)
                                
                                # Create news item
                                news_item = {
                                    'title': title[:200],  # Limit title length
                                    'link': entry.get('link', ''),
                                    'description': html.unescape(entry.get('summary', '')[:300]),
                                    'source': source,
                                    'published': published_dt,
                                    'category': 'اقتصادی'
                                }
                                
                                news_items.append(news_item)
                                
                            except Exception as e:
                                logger.debug(f"Error parsing entry: {e}")
                                continue
                        
                        return news_items
                    
                    else:
                        logger.error(f"Failed to fetch feed {feed_url}: {response.status}")
                        return []
                        
        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching feed: {feed_url}")
            return []
        except Exception as e:
            logger.error(f"Error fetching feed {feed_url}: {e}")
            return []
    
    def _remove_duplicates(self, news_items: List[Dict]) -> List[Dict]:
        """Remove duplicate news items based on title similarity"""
        seen_titles = set()
        unique_items = []
        
        for item in news_items:
            title = item['title'].lower()
            
            # Check if similar title already seen
            is_duplicate = False
            for seen_title in seen_titles:
                if self._similarity(title, seen_title) > 0.8:  # 80% similarity
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen_titles.add(title)
                unique_items.append(item)
        
        return unique_items
    
    def _similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity (simple version)"""
        # Remove common words
        common_words = {'در', 'با', 'از', 'به', 'برای', 'و', 'یا', 'هم', 'نیز'}
        words1 = set(str1.split()) - common_words
        words2 = set(str2.split()) - common_words
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _extract_source_from_url(self, url: str) -> str:
        """Extract source name from URL"""
        url = url.lower()
        
        if 'tasnim' in url:
            return 'تسنیم'
        elif 'fars' in url:
            return 'فارس'
        elif 'isna' in url:
            return 'ایسنا'
        elif 'mehr' in url:
            return 'مهر'
        elif 'irna' in url:
            return 'ایرنا'
        elif 'bbc' in url:
            return 'بی‌بی‌سی فارسی'
        else:
            return 'منبع خبر'
    
    async def get_world_news(self, limit: int = 3) -> List[Dict[str, Any]]:
        """Get world economic news (placeholder for future implementation)"""
        # This is a placeholder - would need international news sources
        # For now, return empty list
        return []
