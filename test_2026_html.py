"""Test to see the HTML structure after selecting 2026"""
import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from browser_manager import BrowserManager
from issue_scraper import IEEEScraper

ISSUES_URL = "https://ieeexplore.ieee.org/xpl/issues?punumber=92&isnumber=10937162"

def test_2026_html():
    """Test to see HTML structure for 2026"""
    print("Testing 2026 HTML structure...")
    browser = BrowserManager(headless=False)
    scraper = IEEEScraper(browser)
    
    try:
        # Navigate to the page
        driver = browser.navigate(ISSUES_URL)
        
        # Select year 2026
        if scraper.select_year(driver, 2026):
            print("Successfully selected year 2026")
            print(f"Current URL: {driver.current_url}")
            
            # Wait a bit for page to fully load
            time.sleep(3)
            
            # Save page source
            with open('2026_page.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print("Saved page HTML to 2026_page.html")
            
            # Print first 2000 characters
            print("\nFirst 2000 characters of page:")
            print(driver.page_source[:2000])
            
            input("Press Enter to close browser...")
        else:
            print("Failed to select year 2026")
            return False
            
        return True
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        browser.close()

if __name__ == "__main__":
    test_2026_html()
