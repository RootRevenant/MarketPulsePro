"""
News Service - Fetch and manage news
"""

import aiohttp
import feedparser
import asyncio
import logging
from datetime import datetime
from typing import List, Dict

logger = logging.getLogger(__name__)

class NewsService:
    """Service for fetching and managing news"""
    
    async def get_latest_news(self, limit: int = 3) -> List[Dict]:
        """Get latest news from RSS feeds"""
        try:
            rss_feeds = [
                "https://www.tasnimnews.com/fa/rss/feed/0/7/اقتصادی",
                "https://www.farsnews.ir/rss/economy"
            ]
            
            all_news = []
            for feed_url in rss_feeds:
                try:
                    news_items = await self._fetch_feed(feed_url)
                    all_news.extend(news_items[:2])  # Take 2 from each
                except Exception as e:
                    logger.error(f"Error fetching {feed_url}: {e}")
                    continue
            
            # Sort by date and limit
            all_news.sort(key=lambda x: x.get('published', datetime.min), reverse=True)
            return all_news[:limit]
            
        except Exception as e:
            logger.error(f"Error in get_latest_news: {e}")
            return []
    
    async def _fetch_feed(self, feed_url: str) -> List[Dict]:
        """Fetch and parse a single RSS feed"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(feed_url, timeout=10) as response:
                    if response.status == 200:
                        content = await response.text()
                        feed = feedparser.parse(content)
                        
                        news_items = []
                        for entry in feed.entries[:5]:
                            try:
                                # Get date
                                published = entry.get('published_parsed')
                                if published:
                                    published_dt = datetime(*published[:6])
                                else:
                                    published_dt = datetime.now()
                                
                                # Clean title
                                title = entry.title[:100] + "..." if len(entry.title) > 100 else entry.title
                                
                                news_item = {
                                    'title': title,
                                    'link': entry.get('link', ''),
                                    'source': feed.feed.get('title', 'منبع'),
                                    'published': published_dt
                                }
                                news_items.append(news_item)
                                
                            except Exception as e:
                                continue
                        
                        return news_items
                    return []
                        
        except Exception as e:
            logger.error(f"Error fetching feed {feed_url}: {e}")
            return []
