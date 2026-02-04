"""
Amazon Page Scraper
Scrolls the page to load dynamic content and extracts complete HTML.

Anti-Detection Features:
- IP Rotation (proxy support)
- Captcha Detection & Manual Solve
- Throttling Protection
- Browser Fingerprint Spoofing (canvas, webgl, audio, timezone, etc.)
"""

import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Import anti-blocking module (includes fingerprint protection)
from anti_block import (
    ProtectedScraper,
    CaptchaDetector,
    BlockDetector,
    ThrottleManager,
    create_protected_driver
)
from fingerprint import BrowserFingerprint


def create_driver():
    """Create and configure Chrome WebDriver with basic protections."""
    options = ChromeOptions()
    
    # Set the Chrome binary location
    options.binary_location = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    
    # Optional: Run in headless mode (uncomment if you don't want browser window)
    # options.add_argument("--headless=new")
    
    # Disable automation flags to avoid detection
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # Additional options for stability
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    # Set a realistic user agent
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    driver = webdriver.Chrome(options=options)
    return driver


def check_element_exists(driver, xpath):
    """Check if an element exists on the page by XPath."""
    if not xpath:
        return False
    try:
        elements = driver.find_elements(By.XPATH, xpath)
        return len(elements) > 0
    except Exception:
        return False


def is_element_in_viewport(driver, xpath):
    """
    Check if an element is visible in the current viewport.
    Only returns True if the element is scrolled into view.
    """
    if not xpath:
        return False
    try:
        elements = driver.find_elements(By.XPATH, xpath)
        if not elements:
            return False
        
        element = elements[0]
        
        # Check if element is in viewport using JavaScript
        is_visible = driver.execute_script("""
            var elem = arguments[0];
            var rect = elem.getBoundingClientRect();
            var windowHeight = window.innerHeight || document.documentElement.clientHeight;
            var windowWidth = window.innerWidth || document.documentElement.clientWidth;
            
            // Check if element is within the viewport
            var vertInView = (rect.top <= windowHeight) && ((rect.top + rect.height) >= 0);
            var horInView = (rect.left <= windowWidth) && ((rect.left + rect.width) >= 0);
            
            return vertInView && horInView;
        """, element)
        
        return is_visible
    except Exception:
        return False


def scroll_and_find_element(driver, target_xpath=None, scroll_step=300, min_pause=1.0, max_pause=3.0, protected_scraper=None):
    """
    Scroll down the page slowly while searching for a target element.
    Stops scrolling when element is found and clicks on it.
    Includes captcha and block detection.
    
    Args:
        driver: Selenium WebDriver instance
        target_xpath: XPath of the element to find and click
        scroll_step: Pixels to scroll each step (smaller = slower, more human-like)
        min_pause: Minimum pause time between scrolls (seconds)
        max_pause: Maximum pause time between scrolls (seconds)
        protected_scraper: ProtectedScraper instance for handling blocks/captchas
        
    Returns:
        tuple: (element_found, was_blocked, captcha_detected)
    """
    print("Starting slow human-like scrolling...")
    if target_xpath:
        print(f"Searching for element: {target_xpath}")
    else:
        print("No target element specified - will scroll to end of page")
    
    last_height = driver.execute_script("return document.body.scrollHeight")
    current_position = 0
    scroll_count = 0
    element_found = False
    was_blocked = False
    captcha_detected = False
    
    while True:
        # =====================================================================
        # STEP 1: SCROLL FIRST (before checking for element)
        # =====================================================================
        
        # Random scroll amount (vary the step for more human-like behavior)
        scroll_amount = random.randint(int(scroll_step * 0.7), int(scroll_step * 1.3))
        current_position += scroll_amount
        
        # Smooth scroll to position (more human-like than instant jump)
        driver.execute_script(f"""
            window.scrollTo({{
                top: {current_position},
                behavior: 'smooth'
            }});
        """)
        
        # Random pause between scrolls (mimics human reading/viewing)
        pause_time = random.uniform(min_pause, max_pause)
        time.sleep(pause_time)
        
        scroll_count += 1
        
        # Get current scroll position and page height
        actual_position = driver.execute_script("return window.pageYOffset")
        current_height = driver.execute_script("return document.body.scrollHeight")
        
        status = "Searching for element..." if target_xpath else ""
        print(f"Scroll {scroll_count} - Position: {actual_position}px / {current_height}px {status}")
        
        # =====================================================================
        # STEP 2: CHECK FOR BLOCKS/CAPTCHA (periodic checks)
        # =====================================================================
        
        # Check for blocks every 5 scrolls
        if scroll_count % 5 == 0:
            is_blocked, block_reason = BlockDetector.is_blocked(driver)
            if is_blocked:
                print(f"\n*** BLOCK DETECTED: {block_reason} ***")
                was_blocked = True
                if protected_scraper:
                    print("Attempting to rotate IP...")
                    driver = protected_scraper.rotate_ip()
                break
        
        # Check for captcha every 3 scrolls
        if scroll_count % 3 == 0:
            is_captcha, captcha_type = CaptchaDetector.is_captcha_present(driver)
            if is_captcha:
                print(f"\n*** CAPTCHA DETECTED: {captcha_type} ***")
                captcha_detected = True
                solved = CaptchaDetector.wait_for_manual_solve(driver)
                if not solved:
                    print("Captcha not solved - stopping...")
                    break
                print("Captcha solved - continuing...")
        
        # =====================================================================
        # STEP 3: CHECK IF TARGET ELEMENT IS NOW VISIBLE IN VIEWPORT
        # =====================================================================
        
        # Only check after scrolling - element must be visible in viewport
        if is_element_in_viewport(driver, target_xpath):
            print(f"\n*** ELEMENT NOW VISIBLE IN VIEWPORT after {scroll_count} scrolls! ***")
            element_found = True
            
            # Wait a moment before clicking (human-like pause)
            time.sleep(random.uniform(1.0, 2.0))
            
            try:
                # Find the element
                element = driver.find_element(By.XPATH, target_xpath)
                
                # Small scroll to center the element (smooth)
                driver.execute_script("""
                    arguments[0].scrollIntoView({
                        behavior: 'smooth',
                        block: 'center'
                    });
                """, element)
                
                time.sleep(random.uniform(1.0, 2.0))  # Wait for scroll to complete
                
                # Click the element
                print("Clicking on the element...")
                element.click()
                print("Element clicked successfully!")
                
                # Wait for any page changes after click
                time.sleep(random.uniform(2.0, 3.0))
                
            except Exception as e:
                print(f"Error clicking element: {e}")
                # Try JavaScript click as fallback
                try:
                    element = driver.find_element(By.XPATH, target_xpath)
                    driver.execute_script("arguments[0].click();", element)
                    print("Element clicked using JavaScript!")
                    time.sleep(random.uniform(2.0, 3.0))
                except Exception as e2:
                    print(f"JavaScript click also failed: {e2}")
            
            break
        
        # Check if we've reached the bottom
        if actual_position + driver.execute_script("return window.innerHeight") >= current_height:
            # Wait a bit more for any lazy-loaded content
            time.sleep(random.uniform(2.0, 3.0))
            
            # Final check for element after reaching bottom (use viewport check)
            if is_element_in_viewport(driver, target_xpath):
                continue  # Go back to top of loop to handle element
            
            # Check if new content was loaded
            new_height = driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height:
                print(f"Scrolling stopped: Page height unchanged ({current_height}px)")
                print("Element NOT found - reached end of page!")
                break
            else:
                print(f"New content loaded! Height: {last_height}px -> {new_height}px")
                last_height = new_height
    
    print(f"Scrolling complete after {scroll_count} scroll steps!")
    return element_found, was_blocked, captcha_detected


def extract_html(driver):
    """Extract the complete HTML of the page."""
    return driver.page_source


def save_html(html_content, filename="amazon_page.html"):
    """Save HTML content to a file."""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"HTML saved to: {filename}")


def scrape_amazon_page(url, target_xpath=None, use_protection=True, proxy_list=None):
    """
    Main function to scrape Amazon page with anti-blocking protections.
    
    Args:
        url: The Amazon product URL to scrape
        target_xpath: Optional XPath of element to find and click while scrolling
        use_protection: Enable anti-blocking protections (IP rotation, captcha, throttling)
        proxy_list: List of proxy strings for IP rotation
        
    Returns:
        The complete HTML content of the page
    """
    scraper = None
    driver = None
    
    try:
        if use_protection:
            # Use protected scraper with all anti-blocking features
            print("=" * 60)
            print("PROTECTED MODE ENABLED")
            print("Features: IP Rotation | Captcha Detection | Throttling Protection")
            print("=" * 60)
            
            scraper = ProtectedScraper(proxy_list=proxy_list)
            
            # Navigate with protection (handles retries, captcha, blocks)
            success = scraper.navigate_with_protection(url)
            if not success:
                raise Exception("Failed to navigate to URL after multiple attempts")
            
            driver = scraper.get_driver()
        else:
            # Use basic driver without protections
            print("Creating Chrome WebDriver (basic mode)...")
            driver = create_driver()
            
            print(f"Navigating to: {url}")
            driver.get(url)
            
            # Wait for the page to load initially
            print("Waiting for page to load...")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        
        time.sleep(2)  # Additional wait for dynamic content
        
        # Scroll the page and optionally find/click target element
        if target_xpath:
            element_found, was_blocked, captcha_detected = scroll_and_find_element(
                driver, 
                target_xpath,
                protected_scraper=scraper
            )
            
            if was_blocked:
                print("\n*** Session was blocked during scrolling ***")
                if scraper:
                    # Retry with new IP
                    driver = scraper.get_driver()
                    
            if element_found:
                print("Target element was found and clicked!")
                # Wait for page to update after click
                time.sleep(3)
                
                # Check for captcha/block after clicking
                is_captcha, _ = CaptchaDetector.is_captcha_present(driver)
                if is_captcha:
                    CaptchaDetector.wait_for_manual_solve(driver)
        else:
            # Just scroll without looking for element
            scroll_and_find_element(driver, target_xpath=None, protected_scraper=scraper)
        
        # Extract the complete HTML
        print("Extracting HTML...")
        html_content = extract_html(driver)
        
        print(f"HTML extracted successfully! Length: {len(html_content)} characters")
        
        return html_content
        
    except Exception as e:
        print(f"Error occurred: {e}")
        raise
        
    finally:
        if scraper:
            scraper.cleanup()
        elif driver:
            print("Closing browser...")
            driver.quit()


if __name__ == "__main__":
    # Amazon product URL
    url = (
        "https://www.amazon.in/Lymio-Jackets-Lightweight-Outwear-J-06-Green-L/dp/B0FMDKS5JN/"
        "?_encoding=UTF8&ref_=pd_hp_d_atf_dealz_cs_c&psc=1"
    )
    
    # Target element XPath - stop scrolling and click when found
    # "See more reviews" link at the bottom of reviews section
    target_element_xpath = "//a[@data-hook='see-all-reviews-link-foot']"
    
    # =========================================================================
    # PROXY CONFIGURATION (Optional - for IP rotation)
    # =========================================================================
    # Add your proxies here for IP rotation to avoid blocking
    # Format: "ip:port" or "ip:port:username:password"
    proxy_list = [
        # Examples (replace with your own working proxies):
        # "192.168.1.1:8080",
        # "192.168.1.2:3128",
        # "proxy.example.com:8080:user:password",
    ]
    
    # =========================================================================
    # SCRAPING OPTIONS
    # =========================================================================
    USE_PROTECTION = True  # Enable anti-blocking features (recommended)
    
    print("\n" + "=" * 60)
    print("AMAZON PAGE SCRAPER WITH ANTI-BLOCKING + FINGERPRINT")
    print("=" * 60)
    print(f"URL: {url[:60]}...")
    print(f"Protection Mode: {'ENABLED' if USE_PROTECTION else 'DISABLED'}")
    print(f"Proxies Configured: {len(proxy_list)}")
    print("")
    print("Anti-Detection Features:")
    print("  - Browser Fingerprint Spoofing")
    print("  - Canvas/WebGL/Audio Fingerprint Protection")
    print("  - Navigator & Screen Property Spoofing")
    print("  - Timezone Masking")
    print("  - Automation Detection Bypass")
    print("=" * 60 + "\n")
    
    # Scrape the page while searching for target element
    html = scrape_amazon_page(
        url, 
        target_xpath=target_element_xpath,
        use_protection=USE_PROTECTION,
        proxy_list=proxy_list if proxy_list else None
    )
    
    # Save the HTML to a file
    save_html(html, "amazon_page.html")
    
    print("\n" + "=" * 60)
    print("SCRAPING COMPLETE!")
    print("=" * 60)
    print("Check 'amazon_page.html' for the extracted content.")
