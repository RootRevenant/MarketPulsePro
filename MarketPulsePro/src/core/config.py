import os
# ... کدهای قبلی ...

class Config(BaseSettings):
    # ... کدهای قبلی ...
    
    @property
    def IS_RENDER(self):
        return os.getenv('RENDER') is not None
    
    @property
    def DATA_DIR(self):
        if self.IS_RENDER:
            return Path("/opt/render/project/src/data")
        return self.BASE_DIR / "data"
    
    # ... بقیه کدها ...