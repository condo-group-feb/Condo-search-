"""Login automation handler."""

import logging
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from app.config import LOGIN_URL
from app.scraper.exceptions import LoginError, ElementNotFoundError
from app.scraper.session_manager import SessionManager

logger = logging.getLogger(__name__)


class LoginHandler:
    """Handles login automation."""
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        self.driver = session_manager.driver
        self.wait = session_manager.wait
    
    def login(self, username: str, password: str) -> bool:
        """
        Perform login on the website.
        
        Args:
            username: MLS username
            password: Password
            
        Returns:
            True if login successful
            
        Raises:
            LoginError: If login fails
        """
        try:
            logger.info(f"Navigating to login page: {LOGIN_URL}")
            print(f"[LOG] Navigating to login page: {LOGIN_URL}")
            self.driver.get(LOGIN_URL)
            print(f"[LOG] Page loaded, waiting for body element...")
            
            # Wait for page to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            print(f"[LOG] Page body loaded, current URL: {self.driver.current_url}")
            
            # Find username field - using specific selectors from HTML
            username_field = self._find_element_with_fallback([
                (By.NAME, "member_login_id"),  # Primary selector from HTML
                (By.XPATH, "//input[@name='member_login_id']"),
                (By.XPATH, "//input[@aria-label='MLS Username']"),
                (By.XPATH, "//label[contains(text(), 'MLS Username')]/following::input[@type='text']"),
                (By.CSS_SELECTOR, "input[name='member_login_id']"),
                (By.CSS_SELECTOR, "input[aria-label='MLS Username']"),
                # Fallback selectors
                (By.ID, "username"),
                (By.NAME, "username"),
                (By.CSS_SELECTOR, "input[type='text']"),
            ])
            
            logger.info("Found username field, entering username")
            print(f"[LOG] Found username field, entering username: {username}")
            username_field.clear()
            
            # Human-like typing with delays
            for char in username:
                username_field.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))  # Random delay between 0.1-0.3 seconds per character
            
            # Additional delay after typing username (human-like pause)
            delay_after_username = random.uniform(2, 4)  # 2-4 seconds
            print(f"[LOG] Pausing for {delay_after_username:.2f} seconds (human-like behavior)...")
            time.sleep(delay_after_username)
            print(f"[LOG] Username entered successfully")
            
            # Find password field - using specific selectors from HTML
            password_field = self._find_element_with_fallback([
                (By.XPATH, "//input[@type='password' and @aria-label='Password']"),  # Primary selector from HTML
                (By.XPATH, "//label[contains(text(), 'Password')]/following::input[@type='password']"),
                (By.CSS_SELECTOR, "input[type='password'][aria-label='Password']"),
                # Fallback selectors
                (By.ID, "password"),
                (By.NAME, "password"),
                (By.CSS_SELECTOR, "input[type='password']"),
                (By.XPATH, "//input[@type='password']"),
            ])
            
            logger.info("Found password field, entering password")
            print(f"[LOG] Found password field, entering password (hidden)")
            password_field.clear()
            
            # Human-like typing with delays
            for char in password:
                password_field.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))  # Random delay between 0.1-0.3 seconds per character
            
            # Additional delay after typing password (human-like pause)
            delay_after_password = random.uniform(2, 4)  # 2-4 seconds
            print(f"[LOG] Pausing for {delay_after_password:.2f} seconds (human-like behavior)...")
            time.sleep(delay_after_password)
            print(f"[LOG] Password entered successfully")
            
            # Find and click login button - using specific selectors from HTML
            logger.info("Looking for login button...")
            print("[LOG] Searching for login button...")
            login_button = self._find_element_with_fallback([
                # Primary selectors based on provided HTML
                (By.XPATH, "//button[@type='submit' and contains(@class, 'v-btn')]"),
                (By.XPATH, "//button[@type='submit' and contains(@class, 'primary')]"),
                (By.XPATH, "//button[contains(@class, 'v-btn')]//div[contains(text(), 'Log In')]/ancestor::button"),
                (By.XPATH, "//button[.//div[contains(text(), 'Log In')]]"),
                (By.XPATH, "//button[.//div[@class='v-btn__content' and contains(text(), 'Log In')]]"),
                (By.CSS_SELECTOR, "button.v-btn.primary[type='submit']"),
                (By.CSS_SELECTOR, "button[type='submit'].v-btn"),
                # Fallback selectors
                (By.XPATH, "//button[contains(text(), 'LOG IN')]"),
                (By.XPATH, "//button[contains(text(), 'Log In')]"),
                (By.XPATH, "//button[contains(text(), 'Login')]"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.ID, "login-button"),
                (By.CLASS_NAME, "login-button"),
                (By.XPATH, "//input[@type='submit']"),
            ])
            
            logger.info("Found login button, attempting to click")
            print("[LOG] Found login button, attempting to click...")
            print(f"[LOG] Button text: {login_button.text}")
            print(f"[LOG] Button is displayed: {login_button.is_displayed()}")
            print(f"[LOG] Button is enabled: {login_button.is_enabled()}")
            
            # Wait for button to be clickable
            try:
                self.wait.until(EC.element_to_be_clickable(login_button))
                print("[LOG] Button is clickable, clicking...")
            except TimeoutException:
                print("[LOG] Warning: Button may not be clickable, attempting click anyway...")
            
            # Try regular click first
            try:
                login_button.click()
                print("[LOG] Regular click executed")
            except Exception as e:
                print(f"[LOG] Regular click failed: {str(e)}, trying JavaScript click...")
                # If regular click fails, try JavaScript click
                self.driver.execute_script("arguments[0].click();", login_button)
                print("[LOG] JavaScript click executed")
            
            logger.info("Login button clicked, waiting for navigation...")
            print("[LOG] Login button clicked, waiting for navigation...")
            
            # Wait for navigation after login (check for home page or specific element)
            time.sleep(2)  # Give some time for the page to start loading
            
            current_url_before = self.driver.current_url
            print(f"[LOG] Current URL before wait: {current_url_before}")
            logger.info(f"Current URL before wait: {current_url_before}")
            
            # Try to detect successful login by checking for common post-login elements
            try:
                print("[LOG] Waiting for page navigation...")
                # Wait for URL to change or for post-login elements to appear
                self.wait.until(
                    lambda driver: (
                        "authenticate" not in driver.current_url.lower() or
                        len(driver.find_elements(By.XPATH, "//*[contains(text(), 'Resource') or contains(text(), 'Dashboard') or contains(text(), 'Home')]")) > 0
                    )
                )
                current_url_after = self.driver.current_url
                print(f"[LOG] Login successful! Redirected to: {current_url_after}")
                logger.info(f"Login successful, redirected to home page: {current_url_after}")
                return True
            except TimeoutException:
                current_url_after = self.driver.current_url
                print(f"[LOG] Timeout waiting for navigation. Current URL: {current_url_after}")
                logger.warning(f"Timeout waiting for navigation. Current URL: {current_url_after}")
                
                # Check if we're still on login page (login might have failed)
                if "authenticate" in current_url_after.lower():
                    print("[LOG] Still on login page, checking for error messages...")
                    # Check for error messages
                    error_elements = self.driver.find_elements(
                        By.XPATH, 
                        "//*[contains(@class, 'error') or contains(@class, 'alert') or contains(text(), 'invalid') or contains(text(), 'incorrect')]"
                    )
                    if error_elements:
                        error_text = error_elements[0].text
                        print(f"[LOG] Error message found: {error_text}")
                        raise LoginError(f"Login failed: {error_text}")
                    print("[LOG] No error message found, but still on login page")
                    raise LoginError("Login failed: Still on login page after attempt")
                # If we're not on login page, assume success
                print(f"[LOG] Not on login page anymore, assuming login successful. URL: {current_url_after}")
                logger.info(f"Login appears successful (redirected away from login page): {current_url_after}")
                return True
                
        except ElementNotFoundError as e:
            raise LoginError(f"Login failed - element not found: {str(e)}")
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            raise LoginError(f"Login failed: {str(e)}")
    
    def _find_element_with_fallback(self, selectors: list):
        """
        Try multiple selectors to find an element.
        
        Args:
            selectors: List of (By, value) tuples
            
        Returns:
            WebElement if found
            
        Raises:
            ElementNotFoundError: If no selector works
        """
        for by, value in selectors:
            try:
                print(f"[LOG] Trying selector: {by}={value}")
                element = self.wait.until(EC.presence_of_element_located((by, value)))
                print(f"[LOG] ✓ Found element using {by}={value}")
                logger.debug(f"Found element using {by}={value}")
                return element
            except TimeoutException:
                print(f"[LOG] ✗ Selector failed: {by}={value}")
                continue
        
        print(f"[LOG] ✗ All selectors failed: {selectors}")
        raise ElementNotFoundError(f"Could not find element with any of the provided selectors: {selectors}")

