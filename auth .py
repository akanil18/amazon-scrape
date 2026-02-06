"""
Amazon Authentication Module

This script opens a browser for manual login. Once you complete the login
(including any OTP verification), the session is automatically saved to
the Chrome profile directory.

Future scraping sessions will use this saved session - no need to login again.

USAGE:
    python auth.py

WHAT IT DOES:
    1. Opens Chrome with the persistent profile
    2. Navigates to Amazon.in login page
    3. Waits for you to manually complete login
    4. Detects when login is successful
    5. Saves session and closes browser

NOTE: This is a ONE-TIME setup. Run this once, login manually, and then
      use main.py for scraping with your saved session.
"""

import sys
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from driver import create_chrome_driver, close_driver
from config.settings import AMAZON_BASE_URL, LOG_FORMAT, LOG_DATE_FORMAT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt=LOG_DATE_FORMAT,
)

logger = logging.getLogger(__name__)


# Amazon login URL
AMAZON_LOGIN_URL = "https://www.amazon.in/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.amazon.in%2F&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=inflex&openid.mode=checkid_setup&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0"

# Selectors for detecting login state
LOGGED_IN_SELECTORS = [
    "#nav-link-accountList-nav-line-1",  # "Hello, Name" text
    "#nav-item-signout",                  # Sign out link
    "a[data-nav-role='signin']",          # Account link when logged in
]

LOGGED_IN_TEXT_PATTERNS = [
    "Hello,",       # "Hello, Name" in account menu
    "Your Account", # Account page
    "Sign Out",     # Sign out option visible
]


def check_if_logged_in(driver) -> bool:
    """
    Check if user is currently logged in to Amazon.
    
    Args:
        driver: WebDriver instance
        
    Returns:
        bool: True if logged in, False otherwise
    """
    try:
        # Check for account greeting (Hello, Name)
        try:
            account_element = driver.find_element(
                By.CSS_SELECTOR, 
                "#nav-link-accountList-nav-line-1"
            )
            greeting_text = account_element.text.strip()
            
            # If it says "Hello, Sign in" then NOT logged in
            # If it says "Hello, [Name]" then logged in
            if greeting_text and "Sign in" not in greeting_text and "Hello" in greeting_text:
                logger.info(f"Detected logged in user: {greeting_text}")
                return True
        except:
            pass
        
        # Check URL - if we're on a signin page, not logged in
        current_url = driver.current_url.lower()
        if "/ap/signin" in current_url or "/ap/cvf" in current_url:
            return False
        
        # Check for sign out link (only visible when logged in)
        try:
            # Hover over account menu to reveal sign out
            account_list = driver.find_element(By.ID, "nav-link-accountList")
            if account_list:
                # Check page source for sign out
                if "nav-item-signout" in driver.page_source:
                    return True
        except:
            pass
        
        return False
        
    except Exception as e:
        logger.debug(f"Error checking login status: {e}")
        return False


def wait_for_manual_login(driver, timeout_minutes: int = 10) -> bool:
    """
    Wait for user to complete manual login.
    
    Polls every few seconds to check if login was successful.
    
    Args:
        driver: WebDriver instance
        timeout_minutes: Maximum time to wait for login
        
    Returns:
        bool: True if login successful, False if timeout
    """
    logger.info("=" * 60)
    logger.info("MANUAL LOGIN REQUIRED")
    logger.info("=" * 60)
    logger.info("Please complete the login in the browser window.")
    logger.info("This includes:")
    logger.info("  1. Enter your email/phone")
    logger.info("  2. Enter your password")
    logger.info("  3. Complete OTP verification if prompted")
    logger.info("")
    logger.info(f"Waiting up to {timeout_minutes} minutes for login...")
    logger.info("=" * 60)
    
    start_time = time.time()
    timeout_seconds = timeout_minutes * 60
    check_interval = 3  # Check every 3 seconds
    
    while (time.time() - start_time) < timeout_seconds:
        # Check if logged in
        if check_if_logged_in(driver):
            logger.info("Login successful! Session will be saved.")
            return True
        
        # Check if still on login page or moved away
        current_url = driver.current_url.lower()
        
        # If redirected to homepage and logged in
        if "amazon.in" in current_url and "/ap/" not in current_url:
            # Double check login status
            time.sleep(2)  # Wait for page to fully load
            if check_if_logged_in(driver):
                logger.info("Login successful! Session will be saved.")
                return True
        
        time.sleep(check_interval)
        
        # Progress indicator every 30 seconds
        elapsed = int(time.time() - start_time)
        if elapsed % 30 == 0 and elapsed > 0:
            remaining = timeout_seconds - elapsed
            logger.info(f"Still waiting for login... ({remaining}s remaining)")
    
    logger.warning("Login timeout - did not detect successful login")
    return False


def verify_session_saved(driver) -> bool:
    """
    Verify the session is properly saved by navigating away and back.
    
    Args:
        driver: WebDriver instance
        
    Returns:
        bool: True if session persists
    """
    logger.info("Verifying session is saved...")
    
    try:
        # Navigate to Amazon homepage
        driver.get(AMAZON_BASE_URL)
        time.sleep(5)  # Wait for page load
        
        # Check if still logged in
        if check_if_logged_in(driver):
            logger.info("Session verified - you are logged in!")
            return True
        else:
            logger.warning("Session may not be saved properly")
            return False
            
    except Exception as e:
        logger.error(f"Error verifying session: {e}")
        return False


def run_authentication():
    """
    Main authentication flow.
    
    Opens browser, waits for manual login, saves session.
    """
    driver = None
    
    try:
        logger.info("=" * 60)
        logger.info("AMAZON AUTHENTICATION SETUP")
        logger.info("=" * 60)
        logger.info("")
        logger.info("This will open a browser for you to login to Amazon.")
        logger.info("Your session will be saved for future scraping.")
        logger.info("")
        
        # Create browser with persistent profile
        logger.info("Opening Chrome browser...")
        driver = create_chrome_driver()
        
        # First check if already logged in
        logger.info("Checking existing session...")
        driver.get(AMAZON_BASE_URL)
        time.sleep(5)
        
        if check_if_logged_in(driver):
            logger.info("=" * 60)
            logger.info("ALREADY LOGGED IN!")
            logger.info("=" * 60)
            logger.info("You already have an active session.")
            logger.info("You can proceed with scraping using main.py")
            
            # Verify session
            verify_session_saved(driver)
            return True
        
        # Not logged in - navigate to login page
        logger.info("Not logged in. Navigating to login page...")
        driver.get(AMAZON_LOGIN_URL)
        time.sleep(3)
        
        # Wait for manual login
        login_success = wait_for_manual_login(driver, timeout_minutes=10)
        
        if login_success:
            # Give extra time for cookies to be set
            logger.info("Waiting for session to be fully saved...")
            time.sleep(5)
            
            # Verify session
            session_ok = verify_session_saved(driver)
            
            if session_ok:
                logger.info("=" * 60)
                logger.info("AUTHENTICATION COMPLETE!")
                logger.info("=" * 60)
                logger.info("Your session has been saved to the Chrome profile.")
                logger.info("You can now run the scraper:")
                logger.info("")
                logger.info("    python main.py --asin YOUR_ASIN")
                logger.info("")
                logger.info("The scraper will use your saved session.")
                logger.info("=" * 60)
                return True
            else:
                logger.warning("Session verification failed. You may need to login again.")
                return False
        else:
            logger.error("Login was not completed within the timeout period.")
            return False
            
    except KeyboardInterrupt:
        logger.info("Authentication cancelled by user.")
        return False
    except Exception as e:
        logger.error(f"Authentication error: {e}", exc_info=True)
        return False
    finally:
        if driver:
            logger.info("Closing browser (session is saved in profile)...")
            close_driver(driver)


def main():
    """Entry point."""
    print("")
    print("Amazon Session Authentication")
    print("=" * 40)
    print("")
    
    success = run_authentication()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
