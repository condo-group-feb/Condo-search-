import logging
import json
import httpx 
import uuid
import os
import base64
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException
from app.models.schemas import ScrapeResponse, SearchFiltersRequest
from app.config import LOGIN_USERNAME, LOGIN_PASSWORD, WEBHOOK_URL 
from app.scraper.session_manager import SessionManager
from app.scraper.login_handler import LoginHandler
from app.scraper.navigator import Navigator
from app.scraper.exceptions import ScraperError, LoginError, NavigationError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


@router.post("/scrape/login-and-navigate", response_model=ScrapeResponse)
async def login_and_navigate(search_filters: SearchFiltersRequest):
    """
    Single endpoint that performs:
    1. Login to the website (using credentials from .env)
    2. Navigate to home page
    3. Click on CoreLogic Matrix icon
    4. Configure search filters with provided parameters
    5. Extract mortgage history data
    
    This endpoint handles the complete flow in one request.
    Username and password are read from .env file (LOGIN_USERNAME and LOGIN_PASSWORD).
    
    Args:
        search_filters: Search filter parameters (street_number, street_direction, street_name)
    """
    session_manager = None

    search_id = search_filters.search_id if search_filters.search_id else str(uuid.uuid4())
    webhook_url = search_filters.webhook_url or WEBHOOK_URL
    logger.info(f"Generated search_id: {search_id} for new scrape request")
    
    # Validate webhook_url
    if not webhook_url:
        error_msg = "webhook_url is required (either in request body or .env file)"
        logger.error(error_msg)
        raise HTTPException(status_code=400, detail=error_msg)
    
    try:
        # Get credentials from .env
        username = LOGIN_USERNAME
        password = LOGIN_PASSWORD
        
        if not username or not password:
            error_msg = "Login credentials not found in .env file. Please set LOGIN_USERNAME and LOGIN_PASSWORD."
            logger.error(error_msg)
            # Send failure webhook
            try:
                await send_webhook(webhook_url, search_id, "failed", error_message=error_msg)
            except Exception as webhook_err:
                logger.error(f"Failed to send error webhook: {webhook_err}")
            # Return 200 with error status since webhook has been notified
            return ScrapeResponse(
                status="error",
                message=error_msg,
                current_url=None,
                success=False,
                data={},
                search_id=search_id
            )
        
        logger.info(f"Starting login and navigation for user: {username}, search_id: {search_id}")
        print(f"[API] Starting login and navigation for user: {username}, search_id: {search_id}")
        
        # Create session and perform operations
        with SessionManager() as session_manager:
            # Step 1: Login
            logger.info("Step 1: Performing login")
            print("[API] Step 1: Performing login")
            login_handler = LoginHandler(session_manager)
            login_handler.login(username, password)
            print("[API] ✓ Login completed successfully")
            
            # Step 2: Click on Matrix anchor tag (opens new tab)
            logger.info("Step 2: Clicking on Matrix anchor tag")
            print("[API] Step 2: Clicking on Matrix anchor tag")
            navigator = Navigator(session_manager)
            matrix_url = navigator.click_matrix_anchor()
            print(f"[API] ✓ Matrix anchor clicked. Current URL: {matrix_url}")
            
            # Step 3: Click on Search menu -> RE1/RE2 Single Family/Condo
            logger.info("Step 3: Clicking on Search menu -> RE1/RE2 Single Family/Condo")
            print("[API] Step 3: Clicking on Search menu -> RE1/RE2 Single Family/Condo")
            re1_re2_url = navigator.click_search_menu_item()
            print(f"[API] ✓ RE1/RE2 page opened. Current URL: {re1_re2_url}")
            
            # Step 4: Configure search filters and click Results
            logger.info("Step 4: Configuring search filters and clicking Results")
            print("[API] Step 4: Configuring search filters and clicking Results")
            print(f"[API] Search filters: street_number={search_filters.street_number}, "
                  f"street_direction={search_filters.street_direction}, street_name={search_filters.street_name}")
            final_url = navigator.configure_search_filters(
                street_number=search_filters.street_number,
                street_direction=search_filters.street_direction,
                street_name=search_filters.street_name
            )
            print(f"[API] ✓ Search filters configured and Results clicked. Current URL: {final_url}")
            
            # Step 5: Extract mortgage history from all result pages
            logger.info("Step 5: Extracting mortgage history from all result pages")
            print("[API] Step 5: Extracting mortgage history from all result pages")
            mortgage_data = navigator.extract_mortgage_history_from_results()
            print(f"[API] ✓ Mortgage history extraction completed. Total records: {len(mortgage_data)}")
            
            logger.info(f"Successfully completed all steps. Final URL: {final_url}, Records extracted: {len(mortgage_data)}")
            
            # Take screenshot before closing session
            screenshot_url = None
            try:
                if session_manager and session_manager.driver:
                    screenshot_url = take_screenshot(session_manager.driver, search_id)
                    logger.info(f"Screenshot saved: {screenshot_url}")
            except Exception as screenshot_err:
                logger.warning(f"Failed to take screenshot: {screenshot_err}")
                # Continue even if screenshot fails
            
            # Transform data and send webhook
            try:
                webhook_results = transform_mortgage_data_to_webhook_format(mortgage_data)
                await send_webhook(webhook_url, search_id, "completed", results=webhook_results, screenshot_url=screenshot_url)
            except Exception as webhook_err:
                logger.error(f"Error sending webhook: {webhook_err}", exc_info=True)
                # Don't fail the request if webhook fails
            
            return ScrapeResponse(
                status="success",
                message=f"Successfully completed all steps and extracted {len(mortgage_data)} mortgage history records",
                current_url=final_url,
                success=True,
                data=mortgage_data,
                search_id=search_id
            )
            
    except LoginError as e:
        error_msg = f"Login failed: {str(e)}"
        logger.error(f"Login error: {error_msg}", exc_info=True)
        try:
            await send_webhook(webhook_url, search_id, "failed", error_message=error_msg)
        except Exception as webhook_err:
            logger.error(f"Failed to send error webhook: {webhook_err}")
        # Return 200 with error status since webhook has been notified
        return ScrapeResponse(
            status="error",
            message=error_msg,
            current_url=None,
            success=False,
            data={},
            search_id=search_id
        )
    except NavigationError as e:
        error_msg = f"Navigation failed: {str(e)}"
        logger.error(f"Navigation error: {error_msg}", exc_info=True)
        try:
            await send_webhook(webhook_url, search_id, "failed", error_message=error_msg)
        except Exception as webhook_err:
            logger.error(f"Failed to send error webhook: {webhook_err}")
        # Return 200 with error status since webhook has been notified
        return ScrapeResponse(
            status="error",
            message=error_msg,
            current_url=None,
            success=False,
            data={},
            search_id=search_id
        )
    except ScraperError as e:
        error_msg = f"Scraping error: {str(e)}"
        logger.error(f"Scraper error: {error_msg}", exc_info=True)
        try:
            await send_webhook(webhook_url, search_id, "failed", error_message=error_msg)
        except Exception as webhook_err:
            logger.error(f"Failed to send error webhook: {webhook_err}")
        # Return 200 with error status since webhook has been notified
        return ScrapeResponse(
            status="error",
            message=error_msg,
            current_url=None,
            success=False,
            data={},
            search_id=search_id
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is (for validation errors, etc.)
        raise
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"Unexpected error: {error_msg}", exc_info=True)
        try:
            await send_webhook(webhook_url, search_id, "failed", error_message=error_msg)
        except Exception as webhook_err:
            logger.error(f"Failed to send error webhook: {webhook_err}")
        # Return 200 with error status since webhook has been notified
        return ScrapeResponse(
            status="error",
            message=error_msg,
            current_url=None,
            success=False,
            data={},
            search_id=search_id
        )
    finally:
        # Ensure session is closed even if error occurs
        if session_manager:
            try:
                session_manager.close()
            except Exception as e:
                logger.warning(f"Error closing session: {e}")

@router.post("/scrape")
def scrape(payload: dict):
    """Legacy endpoint - kept for backward compatibility."""
    return {
        "message": "Please use /scrape/login-and-navigate endpoint",
        "payload": payload
    }


def take_screenshot(driver, search_id: str) -> str:
    """
    Take a screenshot of the current page and save it.
    
    Args:
        driver: Selenium WebDriver instance
        search_id: Unique search ID for filename
        
    Returns:
        URL or path to the screenshot (for now, returns local path)
        TODO: Upload to cloud storage and return public URL
    """
    try:
        # Create screenshots directory if it doesn't exist
        screenshots_dir = Path("screenshots")
        screenshots_dir.mkdir(exist_ok=True)
        
        # Generate filename with search_id
        filename = f"{search_id}.png"
        filepath = screenshots_dir / filename
        
        # Take screenshot
        driver.save_screenshot(str(filepath))
        logger.info(f"Screenshot saved to {filepath}")
        
        # For now, return the local file path
        # TODO: Upload to cloud storage (S3, Supabase Storage, etc.) and return public URL
        # For production, you should upload to a cloud storage service and return the public URL
        return str(filepath)
        
    except Exception as e:
        logger.error(f"Error taking screenshot: {e}", exc_info=True)
        return None


async def send_webhook(webhook_url: str, search_id: str, status: str, results: list = None, error_message: str = None, screenshot_url: str = None):
    """
    Send webhook POST request with scrape results.
    
    Expected format for completed:
    {
        "search_id": "uuid-here",
        "status": "completed",
        "results": [...],
        "screenshot_url": "https://..."
    }
    
    Expected format for failed:
    {
        "search_id": "uuid-here",
        "status": "failed",
        "error_message": "Error description"
    }
    
    Args:
        webhook_url: URL to POST to
        search_id: Unique search ID (must match existing row in condo_searches)
        status: "completed" or "failed"
        results: List of result objects (for successful scrapes)
        error_message: Error description (for failed scrapes)
        screenshot_url: URL to screenshot (for successful scrapes)
    """
    if not webhook_url:
        logger.warning("Webhook URL is empty, skipping webhook")
        return
        
    try:
        payload = {
            "search_id": search_id,
            "status": status
        }
        
        if status == "completed" and results is not None:
            payload["results"] = results
            if screenshot_url:
                payload["screenshot_url"] = screenshot_url
        elif status == "failed" and error_message:
            payload["error_message"] = error_message
        
        # Log the payload being sent for debugging
        logger.info(f"Sending webhook to {webhook_url}")
        logger.debug(f"Webhook payload: {json.dumps(payload, indent=2)}")
        print(f"[API] Sending webhook to {webhook_url}")
        print(f"[API] Payload: search_id={search_id}, status={status}, results_count={len(results) if results else 0}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(webhook_url, json=payload)
            print("PAYLOAD", payload)
            
            # Log response for debugging
            logger.info(f"Webhook response status: {response.status_code}")
            if response.status_code != 200:
                logger.error(f"Webhook response body: {response.text}")
                print(f"[API] ✗ Webhook returned status {response.status_code}: {response.text}")
            
            response.raise_for_status()
            logger.info(f"Webhook sent successfully to {webhook_url} for search_id: {search_id}")
            print(f"[API] ✓ Webhook sent successfully for search_id: {search_id}")
    except httpx.HTTPStatusError as e:
        logger.error(f"Webhook HTTP error: Status {e.response.status_code}, Response: {e.response.text}")
        print(f"[API] ✗ Webhook HTTP error: Status {e.response.status_code}")
        print(f"[API] Response: {e.response.text}")
    except Exception as e:
        logger.error(f"Failed to send webhook to {webhook_url}: {str(e)}", exc_info=True)
        print(f"[API] ✗ Failed to send webhook: {str(e)}")
        # Don't raise exception - webhook failure shouldn't break the main flow

def transform_mortgage_data_to_webhook_format(mortgage_data: dict) -> list:
    """
    Transform mortgage_data dictionary into webhook results format.
    
     Expected format:
    {
        "unit": "101",
        "close_date": "2025-12-15",
        "sold_price": 450000,
        "mortgage_amount": 360000,
        "lender_name": "Chase Bank",
        "loan_type": "Conventional"
    }
    
    Args:
        mortgage_data: Dictionary with ML# as keys and mortgage history as values
        
    Returns:
        List of result objects in webhook format
    """
    results = []
    
    def parse_date(date_str):
        """Parse date string to YYYY-MM-DD format."""
        if not date_str:
            return None
        
        date_str = str(date_str).strip()
        
        # Try common date formats
        date_formats = [
            "%Y-%m-%d",           # Already in correct format
            "%m/%d/%Y",           # MM/DD/YYYY
            "%m-%d-%Y",           # MM-DD-YYYY
            "%d/%m/%Y",           # DD/MM/YYYY
            "%Y/%m/%d",           # YYYY/MM/DD
            "%B %d, %Y",          # January 15, 2025
            "%b %d, %Y",          # Jan 15, 2025
        ]
        
        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        
        # If parsing fails, return None
        logger.warning(f"Could not parse date: {date_str}")
        return None
    
    def parse_amount(amount_str):
        """Parse amount string to integer."""
        if not amount_str:
            return 0
        
        try:
            # Remove currency symbols and commas
            cleaned = str(amount_str).replace("$", "").replace(",", "").replace(" ", "").strip()
            if cleaned:
                return int(float(cleaned))  # Convert to float first to handle decimals, then int
            return 0
        except (ValueError, AttributeError) as e:
            logger.warning(f"Could not parse amount: {amount_str}, error: {e}")
            return 0
    
    for ml_number, data in mortgage_data.items():
        if data is None:
            continue
            
        # Extract arrays from mortgage data
        mortgage_dates = data.get("mortgage_dates", [])
        mortgage_amounts = data.get("mortgage_amounts", [])
        mortgage_lenders = data.get("mortgage_lenders", [])
        
        # Create one result per mortgage record
        max_len = max(
            len(mortgage_dates) if mortgage_dates else 0,
            len(mortgage_amounts) if mortgage_amounts else 0,
            len(mortgage_lenders) if mortgage_lenders else 0
        )
        
        if max_len == 0:
            continue
        
        for i in range(max_len):
            # Parse close_date to YYYY-MM-DD format
            close_date = None
            if i < len(mortgage_dates) and mortgage_dates[i]:
                close_date = parse_date(mortgage_dates[i])
            
            # Parse mortgage_amount to integer
            mortgage_amount = 0
            if i < len(mortgage_amounts) and mortgage_amounts[i]:
                mortgage_amount = parse_amount(mortgage_amounts[i])
            
            # Get lender_name
            lender_name = None
            if i < len(mortgage_lenders) and mortgage_lenders[i]:
                lender_name = str(mortgage_lenders[i]).strip()
            
            # Only create result if we have at least close_date or mortgage_amount
            if close_date or mortgage_amount > 0:
                result = {
                    "unit": str(ml_number),  # ML# used as unit identifier
                    "close_date": close_date if close_date else None,  # Date in YYYY-MM-DD format or None
                    "sold_price": 0,  # Not available in current data - set to 0
                    "mortgage_amount": mortgage_amount,  # Integer, default to 0
                    "lender_name": lender_name if lender_name else None,  # Lender name or None
                    "loan_type": "Conventional"  # Default value - adjust if loan type is available
                }
                
                # Remove None values to keep payload clean
                result = {k: v for k, v in result.items() if v is not None}
                
                results.append(result)
    
    return results