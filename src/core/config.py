import os
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/marketpulse.log'),
            logging.StreamHandler()
        ]
    )

class Config:
    def __init__(self):
        self.BOT_TOKEN = os.getenv("BOT_TOKEN", "")
        admin_ids_str = os.getenv("ADMIN_IDS", "")
        self.ADMIN_IDS = [int(x.strip()) for x in admin_ids_str.split(",") if x.strip()]
        self.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///data/marketpulse.db")
        self.TGJU_API_URL = "https://api.tgju.org/v1/data/sana.json"
        self.COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
        self.NEWS_RSS_FEEDS = [
            "https://www.tasnimnews.com/fa/rss/feed/0/7/اقتصادی",
            "https://www.farsnews.ir/rss/economy"
        ]
        self.REQUIRED_CHANNELS_COUNT = 3
        self.VIP_PRICE = 49000
        self.FREE_TRIAL_DAYS = 3
        self.BASE_DIR = Path(__file__).parent.parent.parent
        self.DATA_DIR = self.BASE_DIR / "data"
        self.LOGS_DIR = self.BASE_DIR / "logs"
        self.DATA_DIR.mkdir(exist_ok=True)
        self.LOGS_DIR.mkdir(exist_ok=True)

config = Config()