import os
from dotenv import load_dotenv

load_dotenv()

# Application settings
APP_NAME = os.getenv("APP_NAME", "Bolt Bot Scraper")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Selenium settings
SELENIUM_HEADLESS = os.getenv("SELENIUM_HEADLESS", "false").lower() == "true"
SELENIUM_BROWSER = os.getenv("SELENIUM_BROWSER", "chrome")
SELENIUM_TIMEOUT = int(os.getenv("SELENIUM_TIMEOUT", "30"))
SELENIUM_IMPLICIT_WAIT = int(os.getenv("SELENIUM_IMPLICIT_WAIT", "10"))
SELENIUM_WINDOW_SIZE = os.getenv("SELENIUM_WINDOW_SIZE", "1920,1080")

# Website URLs
LOGIN_URL = os.getenv("LOGIN_URL", "https://miamirealtors.mysolidearth.com/authenticate")

# Login credentials (from .env)
LOGIN_USERNAME = os.getenv("LOGIN_USERNAME", "")
LOGIN_PASSWORD = os.getenv("LOGIN_PASSWORD", "")

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://zpsvatonxakysnbqnfcc.supabase.co/functions/v1/condo-search-webhook")