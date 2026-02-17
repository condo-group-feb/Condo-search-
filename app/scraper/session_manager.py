"""Selenium WebDriver session management."""

import logging
import os
import subprocess
import time
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
            
            # Try to use system chromium if available (for Docker/Railway)
            if os.path.exists("/usr/bin/chromium"):
                options.binary_location = "/usr/bin/chromium"
            
            # Try ChromeDriverManager first, with retries and better error handling
            service = None
            max_retries = 3
            retry_count = 0
            
            # Set environment variables for ChromeDriverManager to use app directory for cache
            # This ensures it works in Railway/Docker environments
            cache_dir = os.path.join(os.getcwd(), ".wdm")
            os.makedirs(cache_dir, exist_ok=True)
            os.environ.setdefault("WDM_LOCAL", "1")  # Use local cache
            
            while retry_count < max_retries and service is None:
                try:
                    # Try ChromeDriverManager (works in local, may need retries on Railway)
                    logger.info(f"Attempting to use ChromeDriverManager (attempt {retry_count + 1}/{max_retries})...")
                    # Use cache_valid_range to avoid frequent downloads, increase timeout
                    manager = ChromeDriverManager(cache_valid_range=30)  # Cache for 30 days
                    driver_path = manager.install()
                    service = Service(driver_path)
                    logger.info(f"ChromeDriverManager installed successfully at: {driver_path}")
                    break
                except Exception as wdm_error:
                    retry_count += 1
                    error_msg = str(wdm_error)
                    if retry_count < max_retries:
                        logger.warning(f"ChromeDriverManager attempt {retry_count} failed: {error_msg}, retrying...")
                        time.sleep(3)  # Wait longer before retry
                    else:
                        logger.error(f"ChromeDriverManager failed after {max_retries} attempts: {error_msg}")
                        # Log more details for debugging
                        if "network" in error_msg.lower() or "connection" in error_msg.lower():
                            logger.error("Network issue detected. ChromeDriverManager needs internet access to download drivers.")
                        elif "permission" in error_msg.lower() or "access" in error_msg.lower():
                            logger.error("Permission issue detected. Check cache directory permissions.")
            
            # If ChromeDriverManager failed, try to use system chromedriver but warn about version mismatch
            if service is None:
                logger.warning("ChromeDriverManager failed, trying system chromedriver (may have version mismatch)...")
                chromedriver_paths = [
                    "/usr/bin/chromedriver",
                    "/usr/local/bin/chromedriver",
                    "/app/.chromedriver/bin/chromedriver"
                ]
                
                chromedriver_path = None
                for path in chromedriver_paths:
                    if os.path.exists(path):
                        chromedriver_path = path
                        logger.info(f"Found system chromedriver at: {chromedriver_path}")
                        break
                
                if chromedriver_path:
                    # Try to get Chromium version to warn about mismatch
                    try:
                        result = subprocess.run(
                            ["chromium", "--version"],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        chromium_version = result.stdout.strip() if result.returncode == 0 else "unknown"
                        logger.warning(f"Using system chromedriver. Chromium version: {chromium_version}")
                        logger.warning("WARNING: System chromedriver may have version mismatch. ChromeDriverManager is preferred.")
                    except Exception:
                        pass
                    
                    # Try to use it, but it may fail due to version mismatch
                    # In that case, we'll catch the error and provide better guidance
                    service = Service(chromedriver_path)
                else:
                    raise SessionError(
                        f"Could not find chromedriver. ChromeDriverManager failed after {max_retries} attempts, "
                        f"and system chromedriver not found in: {chromedriver_paths}. "
                        f"Please ensure ChromeDriverManager can download drivers or install matching chromedriver."
                    )

            try:
                driver = webdriver.Chrome(
                    service=service,
                    options=options
                )
            except Exception as driver_error:
                error_str = str(driver_error)
                # Check if it's a version mismatch error
                if "version" in error_str.lower() and "chromedriver" in error_str.lower():
                    logger.error(f"ChromeDriver version mismatch detected: {driver_error}")
                    raise SessionError(
                        f"ChromeDriver version mismatch. ChromeDriverManager failed to download matching driver. "
                        f"Error: {driver_error}. "
                        f"Please ensure ChromeDriverManager has network access on Railway to download the correct driver version."
                    )
                else:
                    raise
            
            # Set timeouts
            driver.implicitly_wait(10)
            driver.set_page_load_timeout(SELENIUM_TIMEOUT)
            
            self.driver = driver
            self.wait = WebDriverWait(driver, SELENIUM_TIMEOUT)
            
            logger.info("WebDriver created successfully")
            return driver
            
        except SessionError:
            # Re-raise SessionError as-is
            raise
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











