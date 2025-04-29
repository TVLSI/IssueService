import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class BrowserManager:
    """Manages browser instances and page navigation"""
    
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
    
    def initialize(self):
        """Initialize the browser with appropriate options"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless=new")  # Updated headless syntax
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            chrome_options.add_argument("--log-level=3")  # Only show fatal errors
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            
        # Use webdriver_manager to handle ChromeDriver installation
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        return self.driver
    
    def navigate(self, url, wait_time=5):
        """Navigate to a URL and wait for page to load"""
        if not self.driver:
            self.initialize()
        self.driver.get(url)
        time.sleep(wait_time)  # Simple wait
        return self.driver
    
    def wait_for_element(self, by, selector, timeout=10):
        """Wait for an element to appear and return it"""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, selector))
        )
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            self.driver = None