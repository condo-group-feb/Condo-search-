"""Navigation automation handler."""

import logging
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from app.scraper.exceptions import NavigationError, ElementNotFoundError
from app.scraper.session_manager import SessionManager

logger = logging.getLogger(__name__)


class Navigator:
    """Handles navigation automation."""
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        self.driver = session_manager.driver
        self.wait = session_manager.wait
    
    def click_corelogic_matrix(self) -> str:
        """
        Click on the CoreLogic Matrix icon/button on the home page.
        
        Returns:
            Current URL after clicking (the new page URL)
            
        Raises:
            NavigationError: If navigation fails
        """
        try:
            # Wait for page to be fully loaded
            logger.info("Waiting for home page to load")
            print("[NAV] Waiting for home page to load...")
            current_url = self.driver.current_url
            print(f"[NAV] Current URL: {current_url}")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)  # Give page time to fully render
            print("[NAV] Home page loaded, searching for CoreLogic Matrix element...")
            
            # Try multiple strategies to find the CoreLogic Matrix element
            corelogic_element = self._find_corelogic_element()
            
            logger.info("Found CoreLogic Matrix element, clicking")
            print("[NAV] ✓ Found CoreLogic Matrix element")
            print(f"[NAV] Element text: {corelogic_element.text}")
            print(f"[NAV] Element is displayed: {corelogic_element.is_displayed()}")
            print(f"[NAV] Element is enabled: {corelogic_element.is_enabled()}")
            
            # Scroll element into view if needed
            print("[NAV] Scrolling element into view...")
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", corelogic_element)
            time.sleep(1)  # Wait for scroll
            
            # Click the element
            print("[NAV] Attempting to click CoreLogic Matrix element...")
            try:
                corelogic_element.click()
                print("[NAV] ✓ Regular click executed")
            except Exception as e:
                # If regular click fails, try JavaScript click
                print(f"[NAV] Regular click failed: {str(e)}, trying JavaScript click...")
                logger.info("Regular click failed, trying JavaScript click")
                self.driver.execute_script("arguments[0].click();", corelogic_element)
                print("[NAV] ✓ JavaScript click executed")
            
            # Wait for navigation to new page
            logger.info("Waiting for navigation to CoreLogic Matrix page")
            print("[NAV] Waiting for navigation to CoreLogic Matrix page...")
            time.sleep(3)  # Wait for page transition
            
            # Wait for page to load (body element should be present)
            try:
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                print("[NAV] New page body loaded")
            except TimeoutException:
                print("[NAV] Warning: Timeout waiting for page body, continuing...")
                pass  # Continue even if timeout
            
            current_url = self.driver.current_url
            print(f"[NAV] ✓ Successfully navigated to: {current_url}")
            logger.info(f"Successfully navigated to: {current_url}")
            
            return current_url
            
        except ElementNotFoundError as e:
            raise NavigationError(f"Could not find CoreLogic Matrix element: {str(e)}")
        except Exception as e:
            logger.error(f"Navigation error: {str(e)}")
            raise NavigationError(f"Failed to navigate to CoreLogic Matrix: {str(e)}")
    
    def _find_corelogic_element(self):
        """
        Find the CoreLogic Matrix element using multiple strategies.
        Based on actual HTML: <a href="https://sef.mlsmatrix.com" target="_blank" title="Matrix MLS" class="resource-card">
        
        Returns:
            WebElement for CoreLogic Matrix
            
        Raises:
            ElementNotFoundError: If element not found
        """
        # Try multiple selectors to find CoreLogic Matrix based on actual HTML structure
        selectors = [
            # Primary selectors based on provided HTML
            (By.XPATH, "//a[@href='https://sef.mlsmatrix.com' and @title='Matrix MLS']"),
            (By.XPATH, "//a[@href='https://sef.mlsmatrix.com']"),
            (By.XPATH, "//a[@title='Matrix MLS' and contains(@href, 'mlsmatrix.com')]"),
            (By.XPATH, "//a[contains(@class, 'resource-card') and @href='https://sef.mlsmatrix.com']"),
            (By.XPATH, "//a[@target='_blank' and @href='https://sef.mlsmatrix.com']"),
            
            # CSS selectors
            (By.CSS_SELECTOR, "a.resource-card[href='https://sef.mlsmatrix.com']"),
            (By.CSS_SELECTOR, "a[title='Matrix MLS'][href*='mlsmatrix.com']"),
            (By.CSS_SELECTOR, "a[href='https://sef.mlsmatrix.com']"),
            
            # By partial href
            (By.XPATH, "//a[contains(@href, 'sef.mlsmatrix.com')]"),
            (By.XPATH, "//a[contains(@href, 'mlsmatrix.com')]"),
            
            # Fallback: By title attribute
            (By.XPATH, "//a[@title='Matrix MLS']"),
            (By.XPATH, "//*[@title='Matrix MLS']"),
            
            # Fallback: By class
            (By.XPATH, "//a[contains(@class, 'resource-card') and contains(@href, 'matrix')]"),
            
            # Legacy selectors (in case page structure changes)
            (By.XPATH, "//*[contains(text(), 'CoreLogic Matrix')]"),
            (By.XPATH, "//*[contains(text(), 'CoreLogic Matrix™')]"),
            (By.XPATH, "//*[contains(text(), 'CoreLogic') and contains(text(), 'Matrix')]"),
            (By.PARTIAL_LINK_TEXT, "CoreLogic Matrix"),
            (By.PARTIAL_LINK_TEXT, "CoreLogic"),
            (By.PARTIAL_LINK_TEXT, "Matrix"),
        ]
        
        for by, value in selectors:
            try:
                print(f"[NAV] Trying selector: {by}={value}")
                element = self.wait.until(EC.element_to_be_clickable((by, value)))
                print(f"[NAV] ✓ Found CoreLogic Matrix element using {by}={value}")
                logger.debug(f"Found CoreLogic Matrix element using {by}={value}")
                return element
            except TimeoutException:
                print(f"[NAV] ✗ Selector failed: {by}={value}")
                continue
        
        # If all selectors fail, try to find by looking at all anchor tags with mlsmatrix.com
        try:
            print("[NAV] Trying fallback: searching for all anchor tags with mlsmatrix.com...")
            all_elements = self.driver.find_elements(By.XPATH, "//a[contains(@href, 'mlsmatrix.com')]")
            for element in all_elements:
                try:
                    if element.is_displayed() and element.is_enabled():
                        href = element.get_attribute('href')
                        title = element.get_attribute('title')
                        print(f"[NAV] Found anchor with href={href}, title={title}")
                        logger.debug(f"Found Matrix element by searching all anchors: href={href}, title={title}")
                        return element
                except Exception as e:
                    print(f"[NAV] Error checking element: {str(e)}")
                    continue
        except Exception as e:
            print(f"[NAV] Error in fallback search: {str(e)}")
            pass
        
        raise ElementNotFoundError("Could not find CoreLogic Matrix element with any selector strategy")
    
    def click_matrix_anchor(self) -> str:
        """
        Click on the Matrix anchor tag that redirects to sef.mlsmatrix.com.
        
        Returns:
            Current URL after clicking (the new page URL)
            
        Raises:
            NavigationError: If navigation fails
        """
        try:
            logger.info("Waiting for Matrix anchor tag to be available")
            print("[NAV] Waiting for Matrix anchor tag to be available...")
            time.sleep(2)  # Give page time to fully render
            
            # Find the Matrix anchor tag using the provided HTML structure
            matrix_anchor = self._find_element_with_fallback([
                (By.XPATH, "//a[@href='https://sef.mlsmatrix.com' and @target='_blank']"),
                (By.XPATH, "//a[contains(@href, 'sef.mlsmatrix.com')]"),
                (By.XPATH, "//a[@title='Matrix MLS']"),
                (By.XPATH, "//a[contains(@class, 'resource-card') and contains(@href, 'mlsmatrix.com')]"),
                (By.CSS_SELECTOR, "a[href='https://sef.mlsmatrix.com']"),
                (By.CSS_SELECTOR, "a.resource-card[href*='mlsmatrix.com']"),
                (By.PARTIAL_LINK_TEXT, "Matrix"),
            ])
            
            logger.info("Found Matrix anchor tag, clicking")
            print("[NAV] ✓ Found Matrix anchor tag")
            print(f"[NAV] Anchor href: {matrix_anchor.get_attribute('href')}")
            
            # Scroll element into view if needed
            print("[NAV] Scrolling anchor into view...")
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", matrix_anchor)
            time.sleep(1)
            
            # Click the anchor
            print("[NAV] Clicking Matrix anchor tag...")
            try:
                matrix_anchor.click()
                print("[NAV] ✓ Regular click executed")
            except Exception as e:
                print(f"[NAV] Regular click failed: {str(e)}, trying JavaScript click...")
                self.driver.execute_script("arguments[0].click();", matrix_anchor)
                print("[NAV] ✓ JavaScript click executed")
            
            # Wait for navigation to new page
            logger.info("Waiting for navigation to Matrix page")
            print("[NAV] Waiting for navigation to Matrix page...")
            time.sleep(5)  # Wait for page transition (new tab/window might open)
            
            # Handle new tab/window if opened
            if len(self.driver.window_handles) > 1:
                print("[NAV] New tab/window detected, switching to it...")
                self.driver.switch_to.window(self.driver.window_handles[-1])
                print("[NAV] Switched to new tab/window")
            
            # Wait for page to load
            try:
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                print("[NAV] New page body loaded")
            except TimeoutException:
                print("[NAV] Warning: Timeout waiting for page body, continuing...")
            
            current_url = self.driver.current_url
            print(f"[NAV] Current URL after navigation: {current_url}")
            
            # Handle "User Identity Conflict" warning if present
            # Wait a bit for the page to fully load (might be SAML redirect first)
            time.sleep(3)
            current_url = self.driver.current_url
            print(f"[NAV] Current URL after initial wait: {current_url}")
            
            # Wait for redirect chain to complete (SAML -> LoginIntermediateMLD)
            if "saml" in current_url.lower() or "LoginIntermediateMLD" not in current_url:
                print("[NAV] Waiting for redirect to LoginIntermediateMLD page...")
                try:
                    # Wait for URL to contain LoginIntermediateMLD or for Continue button to appear
                    self.wait.until(
                        lambda driver: (
                            "LoginIntermediateMLD" in driver.current_url or
                            len(driver.find_elements(By.ID, "btnContinue")) > 0
                        )
                    )
                    current_url = self.driver.current_url
                    print(f"[NAV] Redirected to: {current_url}")
                except TimeoutException:
                    print("[NAV] Warning: Timeout waiting for redirect, continuing...")
            
            # Check for User Identity Conflict warning
            try:
                print("[NAV] Checking for User Identity Conflict warning...")
                # Look for the Continue button using the correct selectors based on HTML
                continue_button = self._find_element_with_fallback([
                    (By.ID, "btnContinue"),  # Primary selector - most reliable
                    (By.XPATH, "//a[@id='btnContinue']"),
                    (By.XPATH, "//a[contains(@href, 'doPostBack') and contains(@href, 'btnContinue')]"),
                    (By.XPATH, "//a[span[contains(text(), 'Continue')]]"),
                    (By.XPATH, "//a[span[@class='linkIcon icon_ok']]"),
                    (By.XPATH, "//td[@class='link important barleft']//a"),
                    (By.XPATH, "//a[contains(text(), 'Continue')]"),  # Fallback
                    (By.PARTIAL_LINK_TEXT, "Continue"),
                ], timeout=5)  # Give it a bit more time
                
                print("[NAV] User Identity Conflict warning detected, clicking Continue...")
                print(f"[NAV] Continue button found: {continue_button.get_attribute('id')}")
                
                # Scroll into view and click
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", continue_button)
                time.sleep(0.5)
                
                try:
                    continue_button.click()
                    print("[NAV] ✓ Continue button clicked (regular click)")
                except Exception as e:
                    print(f"[NAV] Regular click failed: {str(e)}, trying JavaScript click...")
                    self.driver.execute_script("arguments[0].click();", continue_button)
                    print("[NAV] ✓ Continue button clicked (JavaScript click)")
                
                # Wait for page to redirect after clicking Continue
                print("[NAV] Waiting for page to process after clicking Continue...")
                time.sleep(3)
                
                # Wait for redirect away from LoginIntermediateMLD
                try:
                    self.wait.until(
                        lambda driver: "LoginIntermediateMLD" not in driver.current_url
                    )
                    current_url = self.driver.current_url
                    print(f"[NAV] ✓ Redirected after Continue. New URL: {current_url}")
                except TimeoutException:
                    current_url = self.driver.current_url
                    print(f"[NAV] Still on same page after timeout. Current URL: {current_url}")
                
            except (ElementNotFoundError, TimeoutException) as e:
                print(f"[NAV] No User Identity Conflict warning found: {str(e)}")
                print("[NAV] Continuing without clicking Continue...")
                pass  # No warning, continue normally
            
            current_url = self.driver.current_url
            print(f"[NAV] ✓ Successfully navigated to Matrix page: {current_url}")
            logger.info(f"Successfully navigated to Matrix page: {current_url}")
            
            return current_url
            
        except ElementNotFoundError as e:
            raise NavigationError(f"Could not find Matrix anchor tag: {str(e)}")
        except Exception as e:
            logger.error(f"Navigation error: {str(e)}")
            raise NavigationError(f"Failed to navigate to Matrix page: {str(e)}")
    
    def click_search_menu_item(self) -> str:
        """
        Hover over Search menu and click on "RE1/RE2 Single Family/Condo".
        
        Returns:
            Current URL after clicking (the new page URL)
            
        Raises:
            NavigationError: If navigation fails
        """
        try:
            logger.info("Waiting for Search menu to be available")
            print("[NAV] Waiting for Search menu to be available...")
            
            # Wait for the page to fully load - check if we're on LoginIntermediateMLD page
            current_url = self.driver.current_url
            print(f"[NAV] Current URL: {current_url}")
            
            # If we're on the intermediate page, wait for redirect to main Matrix page
            if "LoginIntermediateMLD" in current_url:
                print("[NAV] On intermediate login page, waiting for redirect...")
                try:
                    # Wait for URL to change away from LoginIntermediateMLD
                    self.wait.until(
                        lambda driver: "LoginIntermediateMLD" not in driver.current_url
                    )
                    current_url = self.driver.current_url
                    print(f"[NAV] Redirected to: {current_url}")
                except TimeoutException:
                    print("[NAV] Warning: Still on intermediate page after timeout")
            
            time.sleep(3)  # Give page time to fully render
            
            # Check for and dismiss any modals that might block interaction
            try:
                print("[NAV] Checking for modals that might block interaction...")
                
                # Look for "Submit Your 2025 Comp Sales" modal or similar modals
                # Try to find modal by common patterns
                modal_selectors = [
                    (By.XPATH, "//div[contains(@class, 'modal') and contains(., 'Comp Sales')]"),
                    (By.XPATH, "//div[contains(@class, 'popup') and contains(., 'Comp Sales')]"),
                    (By.XPATH, "//div[contains(., 'Submit Your') and contains(., 'Comp Sales')]"),
                    (By.XPATH, "//*[contains(text(), 'Submit Your 2025 Comp Sales')]"),
                ]
                
                modal_found = False
                for by, selector in modal_selectors:
                    try:
                        modal = WebDriverWait(self.driver, 3).until(
                            EC.presence_of_element_located((by, selector))
                        )
                        if modal and modal.is_displayed():
                            print("[NAV] Modal detected, looking for dismiss button...")
                            modal_found = True
                            break
                    except TimeoutException:
                        continue
                
                if modal_found:
                    # Try to find and click "I've Read This" or "Read Later" button
                    dismiss_buttons = [
                        (By.XPATH, "//button[contains(text(), \"I've Read This\")]"),
                        (By.XPATH, "//button[contains(text(), 'Read Later')]"),
                        (By.XPATH, "//a[contains(text(), \"I've Read This\")]"),
                        (By.XPATH, "//a[contains(text(), 'Read Later')]"),
                        (By.XPATH, "//*[contains(@class, 'button') and contains(text(), \"I've Read This\")]"),
                        (By.XPATH, "//*[contains(@class, 'button') and contains(text(), 'Read Later')]"),
                    ]
                    
                    button_clicked = False
                    for by, selector in dismiss_buttons:
                        try:
                            button = self.driver.find_element(by, selector)
                            if button and button.is_displayed():
                                print(f"[NAV] Found dismiss button, clicking...")
                                try:
                                    button.click()
                                    print("[NAV] ✓ Modal dismissed (regular click)")
                                    button_clicked = True
                                    break
                                except Exception:
                                    self.driver.execute_script("arguments[0].click();", button)
                                    print("[NAV] ✓ Modal dismissed (JavaScript click)")
                                    button_clicked = True
                                    break
                        except Exception:
                            continue
                    
                    if button_clicked:
                        time.sleep(2)  # Wait for modal to close
                    else:
                        print("[NAV] ⚠ Modal found but couldn't find dismiss button, trying to close with ESC...")
                        self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                        time.sleep(1)
                        
            except Exception as e:
                print(f"[NAV] Error handling modal: {str(e)}, continuing...")
                pass  # Continue even if modal handling fails
            
            # Additional wait to ensure page is ready after modal dismissal
            time.sleep(1)
            
            # Find the Search menu item (the parent li with class "sf-top")
            search_menu = self._find_element_with_fallback([
                (By.XPATH, "//li[@class='sf-top']//a[contains(@href, '/Matrix/Search') and contains(span, 'Search')]"),
                (By.XPATH, "//li[contains(@class, 'sf-top')]//a[contains(span/text(), 'Search')]"),
                (By.XPATH, "//a[@data-mtx-track and contains(span, 'Search')]"),
                (By.XPATH, "//a[contains(@href, '/Matrix/Search') and span[contains(text(), 'Search')]]"),
                (By.PARTIAL_LINK_TEXT, "Search"),
            ])
            
            logger.info("Found Search menu, hovering over it")
            print("[NAV] ✓ Found Search menu item")
            
            # Scroll into view first
            print("[NAV] Scrolling Search menu into view...")
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", search_menu)
            time.sleep(1)
            
            # Hover over the Search menu to reveal dropdown
            print("[NAV] Hovering over Search menu to reveal dropdown...")
            try:
                actions = ActionChains(self.driver)
                actions.move_to_element(search_menu).perform()
                time.sleep(2)  # Wait for dropdown to appear
            except Exception as e:
                print(f"[NAV] Regular hover failed: {str(e)}, trying JavaScript hover...")
                # Try JavaScript hover as fallback
                self.driver.execute_script(
                    "var evt = document.createEvent('MouseEvents');"
                    "evt.initEvent('mouseover', true, true);"
                    "arguments[0].dispatchEvent(evt);",
                    search_menu
                )
                time.sleep(2)  # Wait for dropdown to appear
            
            # Now find and click on "RE1/RE2 Single Family/Condo" link
            logger.info("Looking for RE1/RE2 Single Family/Condo link")
            print("[NAV] Looking for 'RE1/RE2 Single Family/Condo' link in dropdown...")
            
            re1_re2_link = self._find_element_with_fallback([
                (By.XPATH, "//a[@href='/Matrix/Search/RE1RE2SingleFamilyCondo']"),
                (By.XPATH, "//a[contains(@href, 'RE1RE2SingleFamilyCondo')]"),
                (By.XPATH, "//a[contains(span, 'RE1/RE2 Single Family/Condo')]"),
                (By.XPATH, "//a[span[contains(text(), 'RE1/RE2')]]"),
                (By.XPATH, "//li//a[contains(span, 'RE1/RE2')]"),
                (By.PARTIAL_LINK_TEXT, "RE1/RE2"),
            ])
            
            logger.info("Found RE1/RE2 link, clicking")
            print("[NAV] ✓ Found 'RE1/RE2 Single Family/Condo' link")
            print(f"[NAV] Link href: {re1_re2_link.get_attribute('href')}")
            
            # Scroll into view and click
            print("[NAV] Scrolling link into view...")
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", re1_re2_link)
            time.sleep(1)
            
            print("[NAV] Clicking RE1/RE2 Single Family/Condo link...")
            try:
                re1_re2_link.click()
                print("[NAV] ✓ Regular click executed")
            except Exception as e:
                print(f"[NAV] Regular click failed: {str(e)}, trying JavaScript click...")
                self.driver.execute_script("arguments[0].click();", re1_re2_link)
                print("[NAV] ✓ JavaScript click executed")
            
            # Wait for navigation to new page
            logger.info("Waiting for navigation to RE1/RE2 page")
            print("[NAV] Waiting for navigation to RE1/RE2 page...")
            time.sleep(5)  # Wait for page transition
            
            # Wait for page to load
            try:
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                print("[NAV] New page body loaded")
            except TimeoutException:
                print("[NAV] Warning: Timeout waiting for page body, continuing...")
            
            current_url = self.driver.current_url
            print(f"[NAV] ✓ Successfully navigated to RE1/RE2 page: {current_url}")
            logger.info(f"Successfully navigated to RE1/RE2 page: {current_url}")
            
            return current_url
            
        except ElementNotFoundError as e:
            raise NavigationError(f"Could not find Search menu or RE1/RE2 link: {str(e)}")
        except Exception as e:
            logger.error(f"Navigation error: {str(e)}")
            raise NavigationError(f"Failed to navigate to RE1/RE2 page: {str(e)}")
    
    def configure_search_filters(
        self, 
        street_number: str, 
        street_direction: str, 
        street_name: str
    ) -> str:
        """
        Configure search filters on the RE1/RE2 page:
        1. Uncheck Active, Coming Soon, Active With Contract
        2. Check Closed
        3. Fill address fields with provided parameters
        4. Click Results button
        
        Args:
            street_number: Street number (e.g., "30", "90")
            street_direction: Street direction (N, NE, E, SE, S, SW, W, NW)
            street_name: Street name (e.g., "3", "3rd")
        
        Returns:
            Current URL after clicking Results button
            
        Raises:
            NavigationError: If any step fails
        """
        # Street direction mapping: direction name -> numeric value
        STREET_DIRECTION_MAP = {
            "N": "121",
            "NE": "122",
            "E": "123",
            "SE": "124",
            "S": "125",
            "SW": "126",
            "W": "127",
            "NW": "128"
        }
        
        # Validate and map street direction
        street_direction_upper = street_direction.upper().strip()
        if street_direction_upper not in STREET_DIRECTION_MAP:
            raise NavigationError(
                f"Invalid street direction: {street_direction}. "
                f"Must be one of: {', '.join(STREET_DIRECTION_MAP.keys())}"
            )
        
        direction_value = STREET_DIRECTION_MAP[street_direction_upper]
        try:
            logger.info("Configuring search filters")
            print("[NAV] Configuring search filters...")
            time.sleep(2)  # Wait for page to fully load
            
            # Step 1: Uncheck Active, Coming Soon, Active With Contract
            print("[NAV] Step 1: Unchecking Active, Coming Soon, Active With Contract...")
            
            # Uncheck Active (value="101")
            active_checkbox = self._find_element_with_fallback([
                (By.XPATH, "//input[@type='checkbox' and @value='101' and @name='Fm11_Ctrl27_LB']"),
                (By.XPATH, "//input[@type='checkbox' and @value='101' and contains(@data-mtx-track, 'Active')]"),
                (By.CSS_SELECTOR, "input[value='101'][name='Fm11_Ctrl27_LB']"),
            ])
            if active_checkbox.is_selected():
                print("[NAV] Unchecking Active checkbox...")
                active_checkbox.click()
                time.sleep(0.5)
                print("[NAV] ✓ Active unchecked")
            
            # Uncheck Coming Soon (value="30647")
            coming_soon_checkbox = self._find_element_with_fallback([
                (By.XPATH, "//input[@type='checkbox' and @value='30647' and @name='Fm11_Ctrl27_LB']"),
                (By.XPATH, "//input[@type='checkbox' and @value='30647' and contains(@data-mtx-track, 'Coming Soon')]"),
                (By.CSS_SELECTOR, "input[value='30647'][name='Fm11_Ctrl27_LB']"),
            ])
            if coming_soon_checkbox.is_selected():
                print("[NAV] Unchecking Coming Soon checkbox...")
                coming_soon_checkbox.click()
                time.sleep(0.5)
                print("[NAV] ✓ Coming Soon unchecked")
            
            # Uncheck Active With Contract (value="21505")
            active_with_contract_checkbox = self._find_element_with_fallback([
                (By.XPATH, "//input[@type='checkbox' and @value='21505' and @name='Fm11_Ctrl27_LB']"),
                (By.XPATH, "//input[@type='checkbox' and @value='21505' and contains(@data-mtx-track, 'Active With Contract')]"),
                (By.CSS_SELECTOR, "input[value='21505'][name='Fm11_Ctrl27_LB']"),
            ])
            if active_with_contract_checkbox.is_selected():
                print("[NAV] Unchecking Active With Contract checkbox...")
                active_with_contract_checkbox.click()
                time.sleep(0.5)
                print("[NAV] ✓ Active With Contract unchecked")
            
            # Step 2: Check Closed (value="21507")
            print("[NAV] Step 2: Checking Closed checkbox...")
            closed_checkbox = self._find_element_with_fallback([
                (By.XPATH, "//input[@type='checkbox' and @value='21507' and @name='Fm11_Ctrl27_LB']"),
                (By.XPATH, "//input[@type='checkbox' and @value='21507' and contains(@data-mtx-track, 'Closed')]"),
                (By.CSS_SELECTOR, "input[value='21507'][name='Fm11_Ctrl27_LB']"),
            ])
            if not closed_checkbox.is_selected():
                print("[NAV] Checking Closed checkbox...")
                closed_checkbox.click()
                time.sleep(0.5)
                print("[NAV] ✓ Closed checked")
            else:
                print("[NAV] ✓ Closed already checked")
            
            # Step 3: Fill address fields
            print("[NAV] Step 3: Filling address fields...")
            time.sleep(1)
            
            # Fill first input (Street #) - id="Fm11_Ctrl15_0_145"
            street_number_input = self._find_element_with_fallback([
                (By.ID, "Fm11_Ctrl15_0_145"),
                (By.XPATH, "//input[@name='Fm11_Ctrl15_0_145']"),
                (By.CSS_SELECTOR, "input#Fm11_Ctrl15_0_145"),
            ])
            print(f"[NAV] Filling Street Number field with '{street_number}'...")
            street_number_input.clear()
            street_number_input.send_keys(street_number)
            time.sleep(0.5)
            print("[NAV] ✓ Street Number filled")
            
            # Select dropdown (Street Direction) - name="Fm11_Ctrl15_0_142"
            street_direction_select = self._find_element_with_fallback([
                (By.NAME, "Fm11_Ctrl15_0_142"),
                (By.XPATH, "//select[@name='Fm11_Ctrl15_0_142']"),
                (By.CSS_SELECTOR, "select[name='Fm11_Ctrl15_0_142']"),
            ])
            print(f"[NAV] Selecting Street Direction '{street_direction_upper}' (value={direction_value})...")
            select = Select(street_direction_select)
            select.select_by_value(direction_value)
            time.sleep(0.5)
            print("[NAV] ✓ Street Direction selected")
            
            # Fill second input (Street Name) - id="Fm11_Ctrl15_0_144"
            street_name_input = self._find_element_with_fallback([
                (By.ID, "Fm11_Ctrl15_0_144"),
                (By.XPATH, "//input[@name='Fm11_Ctrl15_0_144']"),
                (By.CSS_SELECTOR, "input#Fm11_Ctrl15_0_144"),
            ])
            print(f"[NAV] Filling Street Name field with '{street_name}'...")
            street_name_input.clear()
            street_name_input.send_keys(street_name)
            time.sleep(0.5)
            print("[NAV] ✓ Street Name filled")
            
            # Step 4: Select Type of Property - Condo
            print("[NAV] Step 4: Selecting 'Condo' from Type of Property dropdown...")
            time.sleep(1)
            try:
                type_of_property_select = self._find_element_with_fallback([
                    (By.NAME, "Fm11_Ctrl588_LB"),
                    (By.ID, "Fm11_Ctrl588_LB"),
                    (By.XPATH, "//select[@name='Fm11_Ctrl588_LB']"),
                ])
                
                select_type = Select(type_of_property_select)
                # First deselect all options (in case something is already selected)
                try:
                    select_type.deselect_all()
                except:
                    pass  # If nothing is selected, this will fail, but that's okay
                # Select Condo (value="25535")
                select_type.select_by_value("25535")
                print("[NAV] ✓ Selected 'Condo' from Type of Property")
                time.sleep(0.5)
            except Exception as e:
                print(f"[NAV] ⚠ Error selecting Type of Property: {str(e)}, continuing...")
            
            # Step 5: Select Sold Financing Type - Conventional
            print("[NAV] Step 5: Selecting 'Conventional' from Sold Financing Type dropdown...")
            time.sleep(0.5)
            try:
                financing_type_select = self._find_element_with_fallback([
                    (By.NAME, "Fm11_Ctrl491_LB"),
                    (By.ID, "Fm11_Ctrl491_LB"),
                    (By.XPATH, "//select[@name='Fm11_Ctrl491_LB']"),
                ])
                
                select_financing = Select(financing_type_select)
                # First deselect all options (in case something is already selected)
                try:
                    select_financing.deselect_all()
                except:
                    pass  # If nothing is selected, this will fail, but that's okay
                # Select Conventional (value="24512")
                select_financing.select_by_value("24512")
                print("[NAV] ✓ Selected 'Conventional' from Sold Financing Type")
                time.sleep(0.5)
            except Exception as e:
                print(f"[NAV] ⚠ Error selecting Sold Financing Type: {str(e)}, continuing...")
            
            # Step 6: Click Results button
            print("[NAV] Step 6: Clicking Results button...")
            time.sleep(1)
            results_button = self._find_element_with_fallback([
                (By.ID, "m_ucSearchButtons_m_lbSearch"),
                (By.XPATH, "//a[@id='m_ucSearchButtons_m_lbSearch']"),
                (By.XPATH, "//a[contains(@href, 'doPostBack') and contains(., 'Results')]"),
                (By.XPATH, "//a[span[contains(text(), 'Results')]]"),
                (By.PARTIAL_LINK_TEXT, "Results"),
            ])
            
            print("[NAV] Scrolling Results button into view...")
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", results_button)
            time.sleep(1)
            
            print("[NAV] Clicking Results button...")
            try:
                results_button.click()
                print("[NAV] ✓ Regular click executed")
            except Exception as e:
                print(f"[NAV] Regular click failed: {str(e)}, trying JavaScript click...")
                self.driver.execute_script("arguments[0].click();", results_button)
                print("[NAV] ✓ JavaScript click executed")
            
            # Wait for page navigation
            logger.info("Waiting for Results page to load")
            print("[NAV] Waiting for Results page to load...")
            time.sleep(5)  # Wait for page transition
            
            # Wait for page to load
            try:
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                print("[NAV] Results page body loaded")
            except TimeoutException:
                print("[NAV] Warning: Timeout waiting for page body, continuing...")
            
            current_url = self.driver.current_url
            print(f"[NAV] ✓ Successfully clicked Results button. Current URL: {current_url}")
            logger.info(f"Successfully configured filters and clicked Results. Current URL: {current_url}")
            
            return current_url
            
        except ElementNotFoundError as e:
            raise NavigationError(f"Could not find form element: {str(e)}")
        except Exception as e:
            logger.error(f"Form configuration error: {str(e)}")
            raise NavigationError(f"Failed to configure search filters: {str(e)}")
    
    def _find_element_with_fallback(self, selectors: list, timeout: int = None):
        """
        Try multiple selectors to find an element.
        
        Args:
            selectors: List of (By, value) tuples
            timeout: Optional timeout in seconds (uses default wait timeout if None)
            
        Returns:
            WebElement if found
            
        Raises:
            ElementNotFoundError: If no selector works
        """
        wait = self.wait if timeout is None else WebDriverWait(self.driver, timeout)
        
        for by, value in selectors:
            try:
                print(f"[NAV] Trying selector: {by}={value}")
                element = wait.until(EC.presence_of_element_located((by, value)))
                print(f"[NAV] ✓ Found element using {by}={value}")
                logger.debug(f"Found element using {by}={value}")
                return element
            except TimeoutException:
                print(f"[NAV] ✗ Selector failed: {by}={value}")
                continue
        
        print(f"[NAV] ✗ All selectors failed: {selectors}")
        raise ElementNotFoundError(f"Could not find element with any of the provided selectors: {selectors}")
    
    def extract_mortgage_history_from_results(self) -> dict:
        """
        Extract mortgage history data from all result pages.
        First collects all ML#s and ikeys from all pages, then processes each one.
        Ensures all ML#s are returned in the response, even if data extraction fails.
        
        Returns:
            Dictionary with ML# as keys and mortgage history data (or None) as values
        """
        all_data = {}
        all_ml_info = []  # List of dicts: [{'ml_number': 'A123', 'ikey': '123', 'page': 1}, ...]
        
        try:
            logger.info("Starting mortgage history extraction from results pages")
            print("[NAV] Starting mortgage history extraction from results pages...")
            time.sleep(3)  # Wait for results page to load
            
            # STEP 1: Collect all ML#s and ikeys from all pages first
            print("[NAV] ===== STEP 1: Collecting all ML#s and ikeys from all pages =====")
            page_number = 1
            
            while True:
                print(f"[NAV] Collecting from page {page_number}...")
                logger.info(f"Collecting ML#s from page {page_number}")
                
                # Find all $ sign links on current page
                dollar_sign_links_xpath = "//span[contains(@class, 'dU')]//a[contains(@href, 'RealistTaxLookup')]"
                dollar_sign_links = self.driver.find_elements(By.XPATH, dollar_sign_links_xpath)
                
                if len(dollar_sign_links) == 0:
                    print("[NAV] No $ sign links found on this page")
                    break
                
                print(f"[NAV] Found {len(dollar_sign_links)} $ sign links on page {page_number}")
                
                # PHASE 1: COLLECTION - Find all rows that contain dollar links and extract ML# and ikey
                # Approach: Find all rows that contain a dollar link, regardless of row class
                # This ensures we get all ML#s even if some rows don't have DisplayRegRow class
                print(f"[NAV] Collecting ML#s and ikeys from all rows containing dollar links...")
                
                # Find all rows that contain a dollar link
                rows_with_dollar_links = self.driver.find_elements(
                    By.XPATH, 
                    "//tr[.//a[contains(@href, 'RealistTaxLookup')]]"
                )
                print(f"[NAV] Found {len(rows_with_dollar_links)} rows containing dollar links on page {page_number}")
                
                for row in rows_with_dollar_links:
                    try:
                        # Find dollar link within this specific row
                        try:
                            dollar_link = row.find_element(By.XPATH, ".//a[contains(@href, 'RealistTaxLookup')]")
                        except:
                            # No dollar link in this row (shouldn't happen, but just in case)
                            continue
                        
                        # Extract ikey from dollar link's href
                        dollar_href = dollar_link.get_attribute('href')
                        ikey = None
                        if dollar_href:
                            normalized_href = dollar_href.replace('&amp;', '&')
                            ikey_match = re.search(r'[&?]ikey=(\d+)', normalized_href)
                            if not ikey_match:
                                ikey_match = re.search(r'ikey=(\d+)', normalized_href)
                            if ikey_match:
                                ikey = ikey_match.group(1)
                        
                        if not ikey:
                            print(f"[NAV] ⚠ Could not extract ikey from dollar link in row, skipping...")
                            continue
                        
                        # Get all cells in this row
                        all_cells = row.find_elements(By.TAG_NAME, "td")
                        print(f"[NAV] Row has {len(all_cells)} cells for ikey {ikey}")
                        
                        # Find ML# in cell with class containing 'm8' (same row as dollar link)
                        ml_number = None
                        for cell in all_cells:
                            try:
                                cell_class = cell.get_attribute('class') or ''
                                if 'm8' in cell_class:
                                    # Get text from the cell (could be in a link or span)
                                    ml_cell_text = cell.text.strip()
                                    if not ml_cell_text:
                                        # Try to get text from link inside cell
                                        try:
                                            link = cell.find_element(By.TAG_NAME, "a")
                                            ml_cell_text = link.text.strip()
                                        except:
                                            pass
                                    
                                    if ml_cell_text:
                                        ml_pattern = r'\b([ARF]\d{8,})\b'
                                        matches = re.findall(ml_pattern, ml_cell_text)
                                        if matches:
                                            ml_number = matches[0]
                                            print(f"[NAV] Found ML# {ml_number} in m8 cell (ikey: {ikey})")
                                            break
                            except Exception as e:
                                continue
                        
                        # Fallback: Try column index 4 (if m8 cell not found)
                        if not ml_number and len(all_cells) > 4:
                            try:
                                ml_cell = all_cells[4]
                                ml_cell_text = ml_cell.text.strip()
                                if not ml_cell_text:
                                    try:
                                        link = ml_cell.find_element(By.TAG_NAME, "a")
                                        ml_cell_text = link.text.strip()
                                    except:
                                        pass
                                
                                if ml_cell_text:
                                    ml_pattern = r'\b([ARF]\d{8,})\b'
                                    matches = re.findall(ml_pattern, ml_cell_text)
                                    if matches:
                                        ml_number = matches[0]
                                        print(f"[NAV] Found ML# {ml_number} in column 4 (ikey: {ikey})")
                            except:
                                pass
                        
                        if ml_number and ikey:
                            # Check if we already collected this combination (avoid duplicates)
                            if not any(ml['ml_number'] == ml_number and ml['ikey'] == ikey for ml in all_ml_info):
                                all_ml_info.append({
                                    'ml_number': ml_number,
                                    'ikey': ikey,
                                    'page': page_number
                                })
                                print(f"[NAV] ✓ Collected: ML# {ml_number}, ikey {ikey} (page {page_number})")
                            else:
                                print(f"[NAV] ⚠ ML# {ml_number} with ikey {ikey} already collected, skipping duplicate...")
                        elif not ml_number:
                            print(f"[NAV] ⚠ Could not extract ML# from row (ikey: {ikey}), skipping...")
                        elif not ikey:
                            print(f"[NAV] ⚠ Could not extract ikey (ML#: {ml_number}), skipping...")
                    except Exception as e:
                        print(f"[NAV] ⚠ Error processing row for collection: {str(e)}, skipping...")
                        continue
                
                # Check for Next button
                try:
                    next_button = self.driver.find_element(
                        By.XPATH,
                        "//span[@class='pagingLinks']//a[contains(text(), 'Next') and not(@disabled)]"
                    )
                    
                    if next_button and next_button.is_enabled():
                        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", next_button)
                        time.sleep(0.5)
                        next_button.click()
                        time.sleep(3)
                        page_number += 1
                    else:
                        break
                except Exception:
                    break
            
            print(f"[NAV] ✓ Collected {len(all_ml_info)} ML#s from all pages")
            
            if not all_ml_info:
                print("[NAV] ⚠ No ML#s collected, returning empty data")
                return all_data
            
            # Initialize all_data with None for all ML#s (ensures all are in response)
            for ml_info in all_ml_info:
                all_data[ml_info['ml_number']] = None
            
            # STEP 2: Process each ML# to extract mortgage history
            print(f"[NAV] ===== STEP 2: Processing {len(all_ml_info)} ML#s to extract mortgage history =====")
            results_window = self.driver.current_window_handle
            
            for idx, ml_info in enumerate(all_ml_info, 1):
                ml_number = ml_info['ml_number']
                ikey = ml_info['ikey']
                
                try:
                    print(f"[NAV] Processing ML# {idx}/{len(all_ml_info)}: {ml_number} (ikey: {ikey})...")
                    
                    # Make sure we're on the results page
                    try:
                        self.driver.switch_to.window(results_window)
                    except:
                        # If window is closed, we can't continue
                        print(f"[NAV] ⚠ Results window closed, cannot continue")
                        break
                    
                    # Re-find the dollar link using ikey
                    try:
                        dollar_link = self.driver.find_element(
                            By.XPATH,
                            f"//a[contains(@href, 'RealistTaxLookup') and contains(@href, 'ikey={ikey}')]"
                        )
                        print(f"[NAV] ✓ Re-found dollar link for ML# {ml_number}")
                    except Exception as e:
                        print(f"[NAV] ⚠ Could not re-find dollar link for ML# {ml_number}: {str(e)}, skipping...")
                        continue
                    
                    # Click $ sign link
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", dollar_link)
                        time.sleep(0.5)
                        
                        windows_before = set(self.driver.window_handles)
                        
                        try:
                            dollar_link.click()
                            print("[NAV] ✓ Dollar link clicked (regular click)")
                        except Exception as e:
                            print(f"[NAV] Regular click failed: {str(e)}, trying JavaScript click...")
                            self.driver.execute_script("arguments[0].click();", dollar_link)
                            print("[NAV] ✓ Dollar link clicked (JavaScript click)")
                        
                        # Wait longer for new tab to open
                        print("[NAV] Waiting for new tab to open...")
                        time.sleep(5)  # Increased wait time
                        
                        windows_after = set(self.driver.window_handles)
                        new_windows = windows_after - windows_before
                        
                        if not new_windows:
                            print(f"[NAV] ⚠ No new tab opened for ML# {ml_number}, waiting more...")
                            time.sleep(3)
                            windows_after = set(self.driver.window_handles)
                            new_windows = windows_after - windows_before
                            if not new_windows:
                                print(f"[NAV] ⚠ Still no new tab opened for ML# {ml_number}, skipping...")
                                continue
                        
                        new_window = new_windows.pop()
                        self.driver.switch_to.window(new_window)
                        print(f"[NAV] Switched to new tab for ML# {ml_number}")
                        
                    except Exception as e:
                        print(f"[NAV] ⚠ Error clicking $ sign for ML# {ml_number}: {str(e)}, skipping...")
                        continue
                    
                    # Wait for page to load and check URL
                    print(f"[NAV] Waiting for property details page to load...")
                    time.sleep(5)  # Initial wait
                    
                    try:
                        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                        print("[NAV] ✓ Page body loaded")
                    except:
                        print("[NAV] ⚠ Warning: Body element wait timeout, continuing anyway...")
                    
                    # Check final URL after waiting
                    time.sleep(3)  # Additional wait for redirects
                    current_url = self.driver.current_url
                    print(f"[NAV] Current URL: {current_url}")
                    
                    # Check for redirects
                    if "no-properties-found" in current_url.lower():
                        print(f"[NAV] ⚠ Warning: Redirected to 'no-properties-found' page for ML# {ml_number}")
                        print(f"[NAV] ⚠ This property may not exist or link is invalid, setting data to None")
                        all_data[ml_number] = None
                        # Close tab and continue
                        self.driver.close()
                        self.driver.switch_to.window(results_window)
                        time.sleep(2)
                        continue
                    
                    if "login" in current_url.lower() or "authenticate" in current_url.lower():
                        print(f"[NAV] ⚠ Warning: Redirected to login page: {current_url}")
                        print(f"[NAV] ⚠ This ML# {ml_number} may require re-authentication, setting data to None")
                        all_data[ml_number] = None
                        # Close tab and continue
                        self.driver.close()
                        self.driver.switch_to.window(results_window)
                        time.sleep(2)
                        continue
                    
                    print(f"[NAV] ✓ Property details page ready (URL: {current_url})")
                    
                    # Extract mortgage history
                    try:
                        print(f"[NAV] Extracting mortgage history for ML# {ml_number}...")
                        mortgage_data = self._extract_mortgage_history()
                        
                        if mortgage_data:
                            all_data[ml_number] = mortgage_data
                            print(f"[NAV] ✓ Successfully extracted data for ML# {ml_number}")
                            print(f"[NAV] Data: {mortgage_data}")
                        else:
                            all_data[ml_number] = None
                            print(f"[NAV] ⚠ No mortgage data found for ML# {ml_number}")
                    except Exception as e:
                        print(f"[NAV] ⚠ Error extracting mortgage history for ML# {ml_number}: {str(e)}")
                        all_data[ml_number] = None
                    
                    # Close tab and switch back
                    try:
                        self.driver.close()
                        print(f"[NAV] Closed tab for ML# {ml_number}")
                        self.driver.switch_to.window(results_window)
                        print(f"[NAV] Switched back to results page")
                        
                        # Wait for results page to be ready
                        print(f"[NAV] Waiting for results page to reload...")
                        time.sleep(3)
                        
                        try:
                            self.wait.until(EC.presence_of_element_located((By.XPATH, "//tr[contains(@class, 'DisplayRegRow')]")))
                            print(f"[NAV] ✓ Results table is ready")
                        except:
                            print(f"[NAV] ⚠ Warning: Results table wait timeout, continuing anyway...")
                        
                        time.sleep(2)
                        
                    except Exception as e:
                        print(f"[NAV] ⚠ Error closing tab for ML# {ml_number}: {str(e)}")
                        try:
                            self.driver.switch_to.window(results_window)
                            time.sleep(2)
                        except:
                            pass
                
                except Exception as e:
                    print(f"[NAV] ⚠ Error processing ML# {ml_number}: {str(e)}, continuing...")
                    all_data[ml_number] = None
                    try:
                        self.driver.switch_to.window(results_window)
                    except:
                        pass
                    continue
            
            print(f"[NAV] ✓ Completed extraction. Total records: {len(all_data)}")
            print(f"[NAV] ML#s with data: {sum(1 for v in all_data.values() if v is not None)}")
            print(f"[NAV] ML#s without data (None): {sum(1 for v in all_data.values() if v is None)}")
            logger.info(f"Completed mortgage history extraction. Total records: {len(all_data)}")
            
            return all_data
            
        except Exception as e:
            logger.error(f"Error in mortgage history extraction: {str(e)}")
            print(f"[NAV] ✗ Error in extraction: {str(e)}")
            # Ensure all collected ML#s are in the response (with None if not processed)
            for ml_info in all_ml_info:
                if ml_info['ml_number'] not in all_data:
                    all_data[ml_info['ml_number']] = None
            return all_data  # Return whatever we collected so far
    
    def _extract_mortgage_history(self) -> dict:
        """
        Extract mortgage history data from the current page (Realist property details page).
        
        Returns:
            Dictionary with mortgage history data (dates, amounts, lenders)
        """
        try:
            # Wait for page to fully load
            print("[NAV] Waiting for page to fully load...")
            time.sleep(4)  # Increased initial wait
            
            # Wait for body element to ensure page is loaded
            try:
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            except:
                pass
            
            # Check for and dismiss survey modal if present
            try:
                print("[NAV] Checking for survey modal...")
                survey_modal = WebDriverWait(self.driver, 8).until(
                    EC.presence_of_element_located((
                        By.CSS_SELECTOR,
                        ".hl-si-survey-container"
                    ))
                )
                
                if survey_modal and survey_modal.is_displayed():
                    print("[NAV] Survey modal detected, clicking 'No' button...")
                    no_button = survey_modal.find_element(
                        By.CSS_SELECTOR,
                        "button.hl-si-btn-no"
                    )
                    
                    if no_button:
                        try:
                            no_button.click()
                            print("[NAV] ✓ Survey modal dismissed")
                            time.sleep(3)  # Wait for modal to close
                        except Exception as e:
                            print(f"[NAV] Regular click failed, trying JavaScript click: {str(e)}")
                            self.driver.execute_script("arguments[0].click();", no_button)
                            print("[NAV] ✓ Survey modal dismissed (JavaScript click)")
                            time.sleep(3)
                            
            except TimeoutException:
                print("[NAV] No survey modal found, continuing...")
                pass  # No modal, continue normally
            except Exception as e:
                print(f"[NAV] Error handling survey modal: {str(e)}, continuing...")
                pass  # Continue even if modal handling fails
            
            # Additional wait for page content to load after modal dismissal
            time.sleep(2)
            
            # Find the mortgage history table with extended timeout
            print("[NAV] Looking for mortgage history table...")
            current_url = self.driver.current_url
            print(f"[NAV] Current URL: {current_url}")
            
            # Try with extended wait time
            extended_wait = WebDriverWait(self.driver, 20)
            
            try:
                mortgage_table = extended_wait.until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        "//*[@id='cdk-accordion-child-11']//table"
                    ))
                )
                print("[NAV] ✓ Found mortgage history table using primary selector")
            except TimeoutException:
                # Try alternative selector
                try:
                    print("[NAV] Trying alternative selector for mortgage table...")
                    mortgage_table = WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((
                            By.XPATH,
                            "//table[.//th[contains(text(), 'Mortgage Date') or contains(text(), 'Mortgage Amount')]]"
                        ))
                    )
                    print("[NAV] ✓ Found mortgage history table using alternative selector")
                except TimeoutException:
                    # Try even more generic selector
                    try:
                        print("[NAV] Trying generic table selector...")
                        mortgage_table = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((
                                By.XPATH,
                                "//table[contains(., 'Mortgage')]"
                            ))
                        )
                        print("[NAV] ✓ Found mortgage history table using generic selector")
                    except TimeoutException:
                        print("[NAV] ⚠ Could not find mortgage history table with any selector")
                        print("[NAV] ⚠ Timeout waiting for mortgage history table")
                        return None
            
            if not mortgage_table:
                print("[NAV] ⚠ Mortgage history table not found")
                return None
            
            print("[NAV] ✓ Found mortgage history table")
            
            # Extract rows
            rows = mortgage_table.find_elements(By.TAG_NAME, "tr")
            
            if len(rows) < 3:
                print("[NAV] ⚠ Not enough rows in mortgage history table")
                return None
            
            # Extract first 3 rows
            mortgage_dates = []
            mortgage_amounts = []
            mortgage_lenders = []
            
            # Row 1: Mortgage Date
            date_row = rows[0]
            date_cells = date_row.find_elements(By.TAG_NAME, "td")
            for cell in date_cells[1:]:  # Skip first cell (header)
                text = cell.text.strip()
                if text and text != "Mortgage Date":
                    mortgage_dates.append(text)
            
            # Row 2: Mortgage Amount
            amount_row = rows[1]
            amount_cells = amount_row.find_elements(By.TAG_NAME, "td")
            for cell in amount_cells[1:]:  # Skip first cell (header)
                text = cell.text.strip()
                if text and text != "Mortgage Amount":
                    mortgage_amounts.append(text)
            
            # Row 3: Mortgage Lender
            lender_row = rows[2]
            lender_cells = lender_row.find_elements(By.TAG_NAME, "td")
            for cell in lender_cells[1:]:  # Skip first cell (header)
                text = cell.text.strip()
                if text and text != "Mortgage Lender":
                    mortgage_lenders.append(text)
            
            # Build result dictionary - ensure we have data
            if not mortgage_dates and not mortgage_amounts and not mortgage_lenders:
                print("[NAV] ⚠ No mortgage data extracted from table")
                return None
            
            result = {
                "mortgage_dates": mortgage_dates,
                "mortgage_amounts": mortgage_amounts,
                "mortgage_lenders": mortgage_lenders
            }
            
            print(f"[NAV] Extracted {len(mortgage_dates)} mortgage records")
            print(f"[NAV] Dates: {mortgage_dates}")
            print(f"[NAV] Amounts: {mortgage_amounts}")
            print(f"[NAV] Lenders: {mortgage_lenders}")
            return result
            
        except TimeoutException:
            print("[NAV] ⚠ Timeout waiting for mortgage history table")
            return None
        except Exception as e:
            print(f"[NAV] ⚠ Error extracting mortgage history: {str(e)}")
            return None

