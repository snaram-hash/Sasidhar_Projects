import os
from typing import Set

class Settings:
    def __init__(self):
        self.ENV: str = os.getenv("CUIS_ENV", "Development")
        self.APP_VERSION: str = "1.0.0"
        
        # Base Path configuration
        self.BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Database
        default_db = os.path.join(self.BASE_DIR, "database", "cuis_local.db")
        self.DATABASE_PATH: str = os.getenv("CUIS_DATABASE_PATH", default_db)
        
        # Uploads & Assets
        self.UPLOAD_DIR: str = os.getenv("CUIS_UPLOAD_DIR", os.path.join(self.BASE_DIR, "assets", "uploads"))
        self.CAM_TEMPLATE_PATH: str = os.getenv("CUIS_CAM_TEMPLATE_PATH", os.path.join(self.BASE_DIR, "assets", "templates", "CAM_Template.xlsx"))
        self.MAX_UPLOAD_SIZE_BYTES: int = int(os.getenv("CUIS_MAX_UPLOAD_SIZE", "52428800")) # 50MB default
        self.ALLOWED_EXTENSIONS: Set[str] = {"pdf", "xlsx", "csv"}
        
        # Logging
        self.LOG_DIR: str = os.getenv("CUIS_LOG_DIR", os.path.join(self.BASE_DIR, "logs"))
        self.LOG_FILE_PATH: str = os.path.join(self.LOG_DIR, "cuis_app.log")
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.DATABASE_PATH), exist_ok=True)
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(self.CAM_TEMPLATE_PATH), exist_ok=True)
        os.makedirs(self.LOG_DIR, exist_ok=True)

settings = Settings()
