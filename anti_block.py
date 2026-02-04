"""
Anti-Blocking Module
Handles IP rotation, captcha detection, throttling protection, and fingerprint spoofing.
"""

import time
import random
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Import fingerprint module
from fingerprint import BrowserFingerprint, FingerprintManager


# ============================================================================
# PROXY MANAGEMENT - IP Rotation
# ============================================================================

class ProxyManager:
    """
    Manages proxy rotation to avoid IP blocking.
    Add your proxy list here or load from file/API.
    """
    
    def __init__(self, proxy_list=None):
        """
        Initialize with a list of proxies.
        
        Proxy format: "ip:port" or "ip:port:username:password"
        """
        # Default free proxy list (replace with your own proxies for reliability)
        self.proxy_list = proxy_list or [
            # Add your proxies here in format: "ip:port" or "ip:port:user:pass"
            # Example:
            # "192.168.1.1:8080",
            # "192.168.1.2:8080:username:password",
        ]
        self.current_index = 0
        self.failed_proxies = set()
        
    def get_next_proxy(self):
        """Get the next available proxy from the list."""
        if not self.proxy_list:
            print("No proxies available - using direct connection")
            return None
            
        # Filter out failed proxies
        available = [p for p in self.proxy_list if p not in self.failed_proxies]
        
        if not available:
            print("All proxies failed - resetting and trying again")
            self.failed_proxies.clear()
            available = self.proxy_list
            
        # Random selection for better distribution
        proxy = random.choice(available)
        print(f"Using proxy: {proxy.split(':')[0]}:****")
        return proxy
    
    def mark_failed(self, proxy):
        """Mark a proxy as failed."""
        if proxy:
            self.failed_proxies.add(proxy)
            print(f"Proxy marked as failed: {proxy.split(':')[0]}:****")
    
    def get_proxy_dict(self, proxy):
        """Convert proxy string to dictionary format for requests."""
        if not proxy:
            return None
            
        parts = proxy.split(":")
        if len(parts) == 2:
            # ip:port format
            return {
                "http": f"http://{proxy}",
                "https": f"http://{proxy}"
            }
        elif len(parts) == 4:
            # ip:port:user:pass format
            ip, port, user, password = parts
            return {
                "http": f"http://{user}:{password}@{ip}:{port}",
                "https": f"http://{user}:{password}@{ip}:{port}"
            }
        return None
    
    def get_chrome_proxy_arg(self, proxy):
        """Convert proxy string to Chrome argument format."""
        if not proxy:
            return None
            
        parts = proxy.split(":")
        if len(parts) >= 2:
            return f"--proxy-server={parts[0]}:{parts[1]}"
        return None


# ============================================================================
# CAPTCHA DETECTION
# ============================================================================

class CaptchaDetector:
    """
    Detects various types of captchas on the page.
    Uses smart detection to avoid false positives.
    """
    
    # XPath patterns for captcha elements (most reliable - check first)
    CAPTCHA_XPATHS = [
        "//img[contains(@src, 'captcha')]",
        "//form[contains(@action, 'captcha')]",
        "//*[contains(@id, 'captcha')]",
        "//iframe[contains(@src, 'recaptcha')]",
        "//div[contains(@class, 'g-recaptcha')]",
        "//div[@id='px-captcha']",  # PerimeterX
        "//input[@id='captchacharacters']",  # Amazon captcha input
        "//div[@class='a-box-inner a-padding-extra-large']//img",  # Amazon captcha image
    ]
    
    # Strong captcha indicators - these phrases usually only appear on captcha pages
    STRONG_INDICATORS = [
        "enter the characters you see below",
        "type the characters you see in this image",
        "sorry, we just need to make sure you're not a robot",
        "to continue, please type the characters below",
        "please enable cookies to continue",
        "access to this page has been denied",
    ]
    
    # URL patterns that indicate captcha pages
    CAPTCHA_URL_PATTERNS = [
        "/captcha/",
        "/validatecaptcha",
        "/errors/validatecaptcha",
        "captcha",
    ]
    
    @staticmethod
    def is_captcha_present(driver):
        """
        Check if a captcha is present on the page.
        Uses multiple checks with priority on reliable indicators.
        
        Returns:
            tuple: (is_captcha, captcha_type)
        """
        # 1. Check URL first (very reliable)
        current_url = driver.current_url.lower()
        for pattern in CaptchaDetector.CAPTCHA_URL_PATTERNS:
            if pattern in current_url:
                print(f"Captcha page detected in URL: {pattern}")
                return True, "url"
        
        # 2. Check page title (reliable)
        title = driver.title.lower()
        if "robot" in title or "captcha" in title:
            print(f"Captcha detected in page title: {driver.title}")
            return True, "title"
        
        # 3. Check for captcha elements by XPath (reliable)
        for xpath in CaptchaDetector.CAPTCHA_XPATHS:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                if elements and any(e.is_displayed() for e in elements):
                    print(f"Captcha element detected: {xpath}")
                    return True, "element"
            except Exception:
                pass
        
        # 4. Check for strong text indicators (specific phrases only)
        page_source = driver.page_source.lower()
        for indicator in CaptchaDetector.STRONG_INDICATORS:
            if indicator in page_source:
                print(f"Captcha detected! Strong indicator: '{indicator}'")
                return True, "text_pattern"
        
        # 5. Check if page is suspiciously small (might be a block/captcha page)
        # Normal Amazon product pages are large (>50KB)
        if len(page_source) < 10000:
            # Small page - check for any captcha-related content
            if "captcha" in page_source or "robot check" in page_source:
                print("Captcha detected: Small page with captcha content")
                return True, "small_page"
        
        return False, None
    
    @staticmethod
    def _silent_captcha_check(driver):
        """Check for captcha without printing messages."""
        # Check URL
        current_url = driver.current_url.lower()
        for pattern in CaptchaDetector.CAPTCHA_URL_PATTERNS:
            if pattern in current_url:
                return True
        
        # Check title
        title = driver.title.lower()
        if "robot" in title or "captcha" in title:
            return True
        
        # Check elements
        for xpath in CaptchaDetector.CAPTCHA_XPATHS:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                if elements and any(e.is_displayed() for e in elements):
                    return True
            except Exception:
                pass
        
        # Check strong indicators
        page_source = driver.page_source.lower()
        for indicator in CaptchaDetector.STRONG_INDICATORS:
            if indicator in page_source:
                return True
        
        # Check small page
        if len(page_source) < 10000:
            if "captcha" in page_source or "robot check" in page_source:
                return True
        
        return False
    
    @staticmethod
    def wait_for_manual_solve(driver, timeout=300):
        """
        Wait for user to manually solve captcha.
        
        Args:
            driver: Selenium WebDriver instance
            timeout: Maximum time to wait (seconds)
            
        Returns:
            bool: True if captcha was solved, False if timeout
        """
        print("\n" + "=" * 60)
        print("CAPTCHA DETECTED!")
        print("Please solve the captcha manually in the browser window.")
        print(f"Waiting up to {timeout} seconds...")
        print("=" * 60 + "\n")
        
        start_time = time.time()
        check_count = 0
        
        while time.time() - start_time < timeout:
            # Use silent check to avoid spam
            is_captcha = CaptchaDetector._silent_captcha_check(driver)
            if not is_captcha:
                print("Captcha appears to be solved! Continuing...")
                time.sleep(2)  # Wait a bit after solving
                return True
            
            check_count += 1
            if check_count % 10 == 0:  # Print status every 30 seconds
                elapsed = int(time.time() - start_time)
                print(f"Still waiting for captcha... ({elapsed}s elapsed)")
            
            time.sleep(3)  # Check every 3 seconds
        
        print("Timeout waiting for captcha to be solved!")
        return False


# ============================================================================
# THROTTLING PROTECTION
# ============================================================================

class ThrottleManager:
    """
    Manages request throttling to avoid rate limiting.
    """
    
    def __init__(self, min_delay=2.0, max_delay=5.0, burst_threshold=10):
        """
        Initialize throttle manager.
        
        Args:
            min_delay: Minimum delay between requests (seconds)
            max_delay: Maximum delay between requests (seconds)
            burst_threshold: Number of requests before increasing delay
        """
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.burst_threshold = burst_threshold
        self.request_count = 0
        self.last_request_time = 0
        self.backoff_multiplier = 1.0
        
    def wait(self):
        """Wait appropriate time before next request."""
        self.request_count += 1
        
        # Increase delay after burst threshold
        if self.request_count % self.burst_threshold == 0:
            self.backoff_multiplier = min(self.backoff_multiplier * 1.5, 3.0)
            print(f"Burst threshold reached - increasing delay (multiplier: {self.backoff_multiplier:.1f}x)")
        
        # Calculate delay
        base_delay = random.uniform(self.min_delay, self.max_delay)
        actual_delay = base_delay * self.backoff_multiplier
        
        # Ensure minimum time between requests
        time_since_last = time.time() - self.last_request_time
        if time_since_last < actual_delay:
            sleep_time = actual_delay - time_since_last
            print(f"Throttling: waiting {sleep_time:.1f}s before next action...")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def report_success(self):
        """Report successful request - may reduce backoff."""
        if self.backoff_multiplier > 1.0:
            self.backoff_multiplier = max(1.0, self.backoff_multiplier * 0.9)
    
    def report_error(self, error_type="generic"):
        """Report error - increase backoff."""
        if error_type == "rate_limit":
            self.backoff_multiplier = min(self.backoff_multiplier * 2.0, 5.0)
            print(f"Rate limit detected - backing off (multiplier: {self.backoff_multiplier:.1f}x)")
        elif error_type == "block":
            self.backoff_multiplier = min(self.backoff_multiplier * 3.0, 10.0)
            print(f"Block detected - major backoff (multiplier: {self.backoff_multiplier:.1f}x)")
    
    def reset(self):
        """Reset throttle state."""
        self.request_count = 0
        self.backoff_multiplier = 1.0


# ============================================================================
# BLOCK DETECTION
# ============================================================================

class BlockDetector:
    """
    Detects if the IP or session has been blocked.
    """
    
    BLOCK_INDICATORS = [
        "access denied",
        "blocked",
        "forbidden",
        "banned",
        "too many requests",
        "rate limit",
        "service unavailable",
        "please try again later",
        "automated access",
        "suspicious activity",
    ]
    
    BLOCK_STATUS_CODES = [403, 429, 503, 504]
    
    @staticmethod
    def is_blocked(driver):
        """
        Check if the current session is blocked.
        
        Returns:
            tuple: (is_blocked, block_reason)
        """
        page_source = driver.page_source.lower()
        title = driver.title.lower()
        
        # Check title
        for indicator in BlockDetector.BLOCK_INDICATORS:
            if indicator in title:
                return True, f"Title contains: {indicator}"
        
        # Check page content (first 5000 chars for speed)
        content_sample = page_source[:5000]
        for indicator in BlockDetector.BLOCK_INDICATORS:
            if indicator in content_sample:
                return True, f"Page contains: {indicator}"
        
        # Check if page is mostly empty (possible soft block)
        if len(page_source) < 1000:
            return True, "Page suspiciously small"
        
        return False, None
    
    @staticmethod
    def check_response_status(response):
        """
        Check if a requests response indicates blocking.
        
        Args:
            response: requests.Response object
            
        Returns:
            tuple: (is_blocked, block_reason)
        """
        if response.status_code in BlockDetector.BLOCK_STATUS_CODES:
            return True, f"HTTP {response.status_code}"
        return False, None


# ============================================================================
# PROTECTED DRIVER FACTORY
# ============================================================================

def create_protected_driver(proxy_manager=None, use_proxy=True, fingerprint=None):
    """
    Create a Chrome WebDriver with anti-blocking protections and fingerprint spoofing.
    
    Args:
        proxy_manager: ProxyManager instance (optional)
        use_proxy: Whether to use proxy (if available)
        fingerprint: BrowserFingerprint instance (optional, will create one if not provided)
        
    Returns:
        tuple: (driver, proxy_used, fingerprint)
    """
    # Create fingerprint if not provided
    if fingerprint is None:
        fingerprint = BrowserFingerprint()
        fingerprint.print_summary()
    
    options = ChromeOptions()
    
    # Set Chrome binary location
    options.binary_location = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    
    # Anti-detection options
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # Stability options
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Apply fingerprint settings to Chrome options
    for arg in fingerprint.get_chrome_options_args():
        options.add_argument(arg)
    
    # Add proxy if available
    proxy_used = None
    if use_proxy and proxy_manager:
        proxy = proxy_manager.get_next_proxy()
        if proxy:
            proxy_arg = proxy_manager.get_chrome_proxy_arg(proxy)
            if proxy_arg:
                options.add_argument(proxy_arg)
                proxy_used = proxy
    
    driver = webdriver.Chrome(options=options)
    
    # Apply fingerprint injection script (spoofs all browser APIs)
    fingerprint.apply_to_driver(driver)
    
    return driver, proxy_used, fingerprint


# ============================================================================
# MAIN PROTECTION WRAPPER
# ============================================================================

class ProtectedScraper:
    """
    Wrapper class that combines all protection mechanisms.
    """
    
    def __init__(self, proxy_list=None):
        """
        Initialize protected scraper.
        
        Args:
            proxy_list: List of proxy strings (optional)
        """
        self.proxy_manager = ProxyManager(proxy_list)
        self.throttle_manager = ThrottleManager(min_delay=2.0, max_delay=5.0)
        self.fingerprint_manager = FingerprintManager()
        self.driver = None
        self.current_proxy = None
        self.current_fingerprint = None
        self.max_retries = 3
        
    def start_driver(self, new_fingerprint=False):
        """
        Start a new protected driver with fingerprint.
        
        Args:
            new_fingerprint: If True, generate new fingerprint. If False, reuse existing.
        """
        if self.driver:
            self.quit_driver()
        
        # Use existing fingerprint or create new one
        if new_fingerprint or self.current_fingerprint is None:
            self.current_fingerprint = self.fingerprint_manager.new_session()
            print("\n*** NEW FINGERPRINT SESSION STARTED ***")
        else:
            print("\n*** REUSING EXISTING FINGERPRINT ***")
        
        self.driver, self.current_proxy, _ = create_protected_driver(
            self.proxy_manager, 
            use_proxy=True,
            fingerprint=self.current_fingerprint
        )
        return self.driver
    
    def quit_driver(self):
        """Quit the current driver (fingerprint is preserved for session)."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None
    
    def rotate_ip(self, new_fingerprint=False):
        """
        Rotate to a new IP by changing proxy.
        Keeps same fingerprint by default for session consistency.
        
        Args:
            new_fingerprint: If True, also generate new fingerprint
        """
        print("\nRotating IP (keeping same fingerprint)..." if not new_fingerprint else "\nRotating IP with new fingerprint...")
        if self.current_proxy:
            self.proxy_manager.mark_failed(self.current_proxy)
        self.quit_driver()
        time.sleep(random.uniform(2, 5))
        return self.start_driver(new_fingerprint=new_fingerprint)
    
    def new_identity(self):
        """Get completely new identity (new proxy + new fingerprint)."""
        print("\n*** GETTING NEW IDENTITY (NEW PROXY + NEW FINGERPRINT) ***")
        return self.rotate_ip(new_fingerprint=True)
    
    def get_fingerprint_summary(self):
        """Get current fingerprint summary."""
        if self.current_fingerprint:
            return self.current_fingerprint.get_summary()
        return None
    
    def navigate_with_protection(self, url, max_retries=None):
        """
        Navigate to URL with all protections enabled.
        
        Args:
            url: URL to navigate to
            max_retries: Maximum retry attempts
            
        Returns:
            bool: True if successful, False otherwise
        """
        retries = max_retries or self.max_retries
        
        for attempt in range(retries):
            try:
                # Apply throttling
                self.throttle_manager.wait()
                
                # Ensure driver is running
                if not self.driver:
                    self.start_driver()
                
                print(f"\nAttempt {attempt + 1}/{retries}: Navigating to {url[:50]}...")
                self.driver.get(url)
                
                # Wait for page load
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                time.sleep(random.uniform(1, 3))
                
                # Check for blocks
                is_blocked, reason = BlockDetector.is_blocked(self.driver)
                if is_blocked:
                    print(f"Block detected: {reason}")
                    self.throttle_manager.report_error("block")
                    self.rotate_ip()
                    continue
                
                # Check for captcha
                is_captcha, captcha_type = CaptchaDetector.is_captcha_present(self.driver)
                if is_captcha:
                    print(f"Captcha detected: {captcha_type}")
                    solved = CaptchaDetector.wait_for_manual_solve(self.driver)
                    if not solved:
                        self.rotate_ip()
                        continue
                
                # Success!
                self.throttle_manager.report_success()
                print("Navigation successful!")
                return True
                
            except Exception as e:
                print(f"Error during navigation: {e}")
                self.throttle_manager.report_error("generic")
                if attempt < retries - 1:
                    self.rotate_ip()
        
        print("All retry attempts failed!")
        return False
    
    def get_driver(self):
        """Get the current driver instance."""
        if not self.driver:
            self.start_driver()
        return self.driver
    
    def cleanup(self):
        """Clean up resources and end fingerprint session."""
        self.quit_driver()
        self.fingerprint_manager.end_session()
        self.current_fingerprint = None
        print("Session cleaned up - fingerprint discarded")


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Example proxy list (replace with your own)
    proxies = [
        # "123.456.789.0:8080",
        # "123.456.789.1:8080:user:pass",
    ]
    
    # Create protected scraper
    scraper = ProtectedScraper(proxy_list=proxies)
    
    try:
        # Navigate with protection
        url = "https://www.amazon.in"
        success = scraper.navigate_with_protection(url)
        
        if success:
            driver = scraper.get_driver()
            print(f"Page title: {driver.title}")
            print(f"Page length: {len(driver.page_source)} characters")
            
            # Continue with your scraping logic...
            
    finally:
        scraper.cleanup()
