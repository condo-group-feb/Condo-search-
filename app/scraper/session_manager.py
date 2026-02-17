"""Selenium WebDriver session management."""

import logging
from contextlib import contextmanager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from app.config import (
    SELENIUM_HEADLESS,
    SELENIUM_TIMEOUT,
    SELENIUM_WINDOW_SIZE
)
from app.scraper.exceptions import SessionError

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages Selenium WebDriver sessions."""
    
    def __init__(self):
        self.driver = None
        self.wait = None
    
    # def create_driver(self) -> webdriver.Chrome:
    #     """Create and configure Chrome WebDriver."""
    #     try:
    #         chrome_options = Options()
            
    #         if SELENIUM_HEADLESS:
    #             chrome_options.add_argument("--headless")
            
    #         chrome_options.add_argument("--no-sandbox")
    #         chrome_options.add_argument("--disable-dev-shm-usage")
    #         chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    #         chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    #         chrome_options.add_experimental_option('useAutomationExtension', False)
            
    #         # Set window size
    #         if SELENIUM_WINDOW_SIZE:
    #             chrome_options.add_argument(f"--window-size={SELENIUM_WINDOW_SIZE}")
    #         else:
    #             chrome_options.add_argument("--start-maximized")
            
    #         # User agent to appear more like a real browser
    #         chrome_options.add_argument(
    #             "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    #             "AppleWebKit/537.36 (KHTML, like Gecko) "
    #             "Chrome/120.0.0.0 Safari/537.36"
    #         )
            
    #         # Initialize driver with automatic driver management
    #         service = Service(ChromeDriverManager().install())
    #         driver = webdriver.Chrome(service=service, options=chrome_options)
            
    #         # Set timeouts
    #         driver.implicitly_wait(10)
    #         driver.set_page_load_timeout(SELENIUM_TIMEOUT)
            
    #         self.driver = driver
    #         self.wait = WebDriverWait(driver, SELENIUM_TIMEOUT)
            
    #         logger.info("WebDriver created successfully")
    #         return driver
            
    #     except Exception as e:
    #         logger.error(f"Failed to create WebDriver: {str(e)}")
    #         raise SessionError(f"Failed to create WebDriver: {str(e)}")

    def create_driver(self):
        """Create and configure Chrome WebDriver."""
        try:
            options = Options()
            
            if SELENIUM_HEADLESS:
                options.add_argument("--headless=new")
            
            # REQUIRED for Docker/headless
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Set window size
            if SELENIUM_WINDOW_SIZE:
                options.add_argument(f"--window-size={SELENIUM_WINDOW_SIZE}")
            else:
                options.add_argument("--window-size=1920,1080")
            
            # User agent to appear more like a real browser
            options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
            
            # Try to use system chromium if available (for Docker)
            try:
                import os
                if os.path.exists("/usr/bin/chromium"):
                    options.binary_location = "/usr/bin/chromium"
            except:
                pass
            
            # Use ChromeDriverManager to automatically download and manage driver
            # service = Service(ChromeDriverManager().install())
            service = Service("/usr/bin/chromedriver")
            driver = webdriver.Chrome(service=service, options=options)
            
            # Set timeouts
            driver.implicitly_wait(10)
            driver.set_page_load_timeout(SELENIUM_TIMEOUT)
            
            self.driver = driver
            self.wait = WebDriverWait(driver, SELENIUM_TIMEOUT)
            
            logger.info("WebDriver created successfully")
            return driver
            
        except Exception as e:
            logger.error(f"Failed to create WebDriver: {str(e)}", exc_info=True)
            raise SessionError(f"Failed to create WebDriver: {str(e)}")

    def close(self):
        """Close the WebDriver session."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver session closed")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {str(e)}")
            finally:
                self.driver = None
                self.wait = None
    
    @contextmanager
    def session(self):
        """Context manager for WebDriver session."""
        try:
            self.create_driver()
            yield self
        finally:
            self.close()
    
    def __enter__(self):
        self.create_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()











