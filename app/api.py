import logging
from fastapi import APIRouter, HTTPException
from app.models.schemas import ScrapeResponse, SearchFiltersRequest
from app.config import LOGIN_USERNAME, LOGIN_PASSWORD
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
def login_and_navigate(search_filters: SearchFiltersRequest):
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
    try:
        # Get credentials from .env
        username = LOGIN_USERNAME
        password = LOGIN_PASSWORD
        
        if not username or not password:
            raise HTTPException(
                status_code=400,
                detail="Login credentials not found in .env file. Please set LOGIN_USERNAME and LOGIN_PASSWORD."
            )
        
        logger.info(f"Starting login and navigation for user: {username}")
        print(f"[API] Starting login and navigation for user: {username}")
        
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
            
            return ScrapeResponse(
                status="success",
                message=f"Successfully completed all steps and extracted {len(mortgage_data)} mortgage history records",
                current_url=final_url,
                success=True,
                data=mortgage_data
            )
            
    except LoginError as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Login failed: {str(e)}")
    except NavigationError as e:
        logger.error(f"Navigation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Navigation failed: {str(e)}")
    except ScraperError as e:
        logger.error(f"Scraper error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Scraping error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    finally:
        # Ensure session is closed even if error occurs
        if session_manager:
            try:
                session_manager.close()
            except:
                pass


@router.post("/scrape")
def scrape(payload: dict):
    """Legacy endpoint - kept for backward compatibility."""
    return {
        "message": "Please use /scrape/login-and-navigate endpoint",
        "payload": payload
    }
