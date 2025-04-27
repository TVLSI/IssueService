import re
from typing import List, Optional, Tuple
from selenium.webdriver.common.by import By
import time

from browser_manager import BrowserManager
from issue import Issue

class IEEEScraper:
    """Handles scraping IEEE TVLSI issues"""
    
    def __init__(self, browser_manager: BrowserManager):
        self.browser = browser_manager
    
    def extract_volume_number(self, driver) -> int:
        """Extract volume number from the page"""
        volume_elements = driver.find_element(By.CSS_SELECTOR, "section[class*='issue-container']")
        volume_div = volume_elements.find_element(By.XPATH, ".//div[strong[contains(text(), 'Volume')]]")
        volume_text = volume_div.text.strip()
        volume_match = re.search(r'Volume\s+(\d+)', volume_text, re.IGNORECASE)
        return int(volume_match.group(1)) if volume_match else 0
    
    def extract_issue_links(self, driver) -> List[Tuple[int, str, str]]:
        """Extract issue links from the main page"""
        issue_data = []
        volume_elements = driver.find_element(By.CSS_SELECTOR, "section[class*='issue-container']")
        issue_elements = volume_elements.find_elements(By.CSS_SELECTOR, "div[class*='issue-details']")
        
        for element in issue_elements:
            try:
                issue_link = element.find_element(By.CSS_SELECTOR, "a[href*='isnumber=']")
                issue_text = issue_link.text.strip()
                href = issue_link.get_attribute("href")
                
                issue_match = re.search(r'Issue\s+(\d+)', issue_text, re.IGNORECASE)
                isnumber_match = re.search(r'isnumber=(\d+)', href)
                
                if issue_match and isnumber_match:
                    issue_num = int(issue_match.group(1))
                    isnumber = isnumber_match.group(1)
                    issue_data.append((issue_num, isnumber, href))
            except Exception as e:
                print(f"Error parsing issue link: {e}")
                
        return issue_data
    
    def extract_issue_details(self, driver, issue_num: int) -> Optional[dict]:
        """Extract detailed information from an issue page"""
        try:
            issue_details_element = driver.find_element(By.CSS_SELECTOR, "div.u-m-1.u-mt-1.u-mr-1.text-base-md p b")
            issue_details_text = issue_details_element.text.strip()
            
            month_year_match = re.search(r'•\s+(\w+)-(\d{4})', issue_details_text)
            
            if month_year_match and f"Issue {issue_num}" in issue_details_text:
                full_month = month_year_match.group(1)
                year = int(month_year_match.group(2))
                
                month_to_num = {
                    'January': 1, 'February': 2, 'March': 3, 'April': 4,
                    'May': 5, 'June': 6, 'July': 7, 'August': 8,
                    'September': 9, 'October': 10, 'November': 11, 'December': 12
                }
                numerical_month = month_to_num.get(full_month, 0)
                
                return {
                    'month': full_month,
                    'numerical_month': numerical_month,
                    'year': year
                }
        except Exception as e:
            print(f"Error extracting issue details: {e}")
        
        return None

    # TODO: switch this to a dictionary by issue number
    def get_issues(self, url: str, previous_issues: List[Issue]) -> List[Issue]:
        """Get all issues from the IEEE TVLSI page"""
        issues = []
        driver = None
        
        try:
            driver = self.browser.navigate(url)
            volume_number = self.extract_volume_number(driver)
            issue_links = self.extract_issue_links(driver)
            
            for issue_num, isnumber, href in issue_links:
                self.browser.navigate(href)
                details = self.extract_issue_details(driver, issue_num)
                
                if details:
                    issues.append(Issue(
                        volume=volume_number,
                        issue=issue_num,
                        month=details['month'],
                        numerical_month=details['numerical_month'],
                        year=details['year'],
                        isnumber=isnumber
                    ))
            
            return issues
        except Exception as e:
            print(f"Error getting issues: {e}")
            return []
        finally:
            if driver:
                self.browser.close()