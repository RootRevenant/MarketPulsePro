"""
Configuration Management
"""

import os
import logging
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/marketpulse.log'),
            logging.StreamHandler()
        ]
    )


class Config:
    """Bot configuration"""
    
    def __init__(self):
        # Bot Token (REQUIRED)
        self.BOT_TOKEN = os.getenv("BOT_TOKEN", "")
        
        # Admin IDs (comma separated)
        admin_ids_str = os.getenv("ADMIN_IDS", "")
        self.ADMIN_IDS = [int(x.strip()) for x in admin_ids_str.split(",") if x.strip()]
        
        # Database
        self.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///data/marketpulse.db")
        
        # API URLs
        self.TGJU_API_URL = os.getenv("TGJU_API_URL", "https://api.tgju.org/v1/data/sana.json")
        self.COINGECKO_API_URL = os.getenv("COINGECKO_API_URL", "https://api.coingecko.com/api/v3")
        
        # News RSS Feeds
        self.NEWS_RSS_FEEDS = os.getenv("NEWS_RSS_FEEDS", "").split(";")
        if not self.NEWS_RSS_FEEDS or self.NEWS_RSS_FEEDS == [""]:
            self.NEWS_RSS_FEEDS = [
                "https://www.tasnimnews.com/fa/rss/feed/0/7/اقتصادی",
                "https://www.farsnews.ir/rss/economy"
            ]
        
        # Bot Settings
        self.REQUIRED_CHANNELS_COUNT = int(os.getenv("REQUIRED_CHANNELS_COUNT", "3"))
        self.VIP_PRICE = int(os.getenv("VIP_PRICE", "49000"))
        self.FREE_TRIAL_DAYS = int(os.getenv("FREE_TRIAL_DAYS", "3"))
        
        # Paths
        self.BASE_DIR = Path(__file__).parent.parent.parent
        self.DATA_DIR = self.BASE_DIR / "data"
        self.LOGS_DIR = self.BASE_DIR / "logs"
        
        # Scheduler intervals (seconds)
        self.PRICE_UPDATE_INTERVAL = 30
        self.NEWS_UPDATE_INTERVAL = 3600
        self.CHECK_MEMBERSHIP_INTERVAL = 300
        
        # Validation
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is required in .env file")
        
        # Create directories if they don't exist
        self.DATA_DIR.mkdir(exist_ok=True)
        self.LOGS_DIR.mkdir(exist_ok=True)


# Global config instance
config = Config()
