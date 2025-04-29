import re
from typing import List, Optional, Tuple
from selenium.webdriver.common.by import By
import time

from browser_manager import BrowserManager
from issue import Issue
from issues_dictionary import IssuesDictionary
import calendar
from datetime import datetime

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
                raise
                
        return issue_data
    
    def extract_issue_details(self, driver, issue_num: int) -> Optional[dict]:
        """Extract detailed information from an issue page"""
        try:

            issue_details_element = driver.find_element(By.CSS_SELECTOR, "div.u-m-1.u-mt-1.u-mr-1.text-base-md p b")
            issue_details_text = issue_details_element.text.strip()
            
            month_year_match = re.search(r'•\s+([A-Za-z]+\.?)\s*-\s*(\d{4})', issue_details_text)
            
            if month_year_match and f"Issue {issue_num}" in issue_details_text:
                # Extract month and year
                full_month = month_year_match.group(1).rstrip('.')
                year = int(month_year_match.group(2))
                
                # Try to match the month using calendar module
                month_abbrs = {month.lower(): i for i, month in enumerate(calendar.month_abbr) if month}
                numerical_month = month_abbrs.get(full_month[:3].lower())
                
                if numerical_month:
                    proper_month = calendar.month_name[numerical_month]
                    return {
                        'month': proper_month,
                        'numerical_month': numerical_month,
                        'year': year
                    }
        except Exception as e:
            print(f"Error extracting issue details: {e}")
            raise
        
        return None


    def get_years(self, driver) -> List[int]:
        """Extract all available years from the website"""
        years = []
        try:
            year_elements = driver.find_elements(By.CSS_SELECTOR, 
                "div.issue-details-past-tabs.year ul li a")
            
            for elem in year_elements:
                try:
                    year_text = elem.text.strip()
                    years.append(int(year_text))
                except ValueError:
                    continue
            
            # Sort years from oldest to newest
            years.sort()
        except Exception as e:
            print(f"Error getting years from website: {e}")
        
        return years


    def determine_years_to_process(self, all_years: List[int], previous_issues: IssuesDictionary) -> List[int]:
        """Determine which years need to be processed based on previous issues"""
        if not previous_issues:
            # Process all years if no previous issues
            print("No previous issues found. Processing all years...")
            return all_years
        
        # Get the most recent issue we have
        most_recent_issue = previous_issues.get_latest_issue()
        last_year = most_recent_issue.year
        last_month = most_recent_issue.numerical_month
        
        years_to_process = []
        
        # Add years newer than our most recent issue
        for year in all_years:
            if year > last_year:
                years_to_process.append(year)
        
        # Add the year of our last issue unless it was December (already complete)
        if last_month < 12 and last_year in all_years:
            years_to_process.append(last_year)
        
        print(f"Processing years newer than {last_year}-{last_month}: {years_to_process}")
        return years_to_process


    def select_year(self, driver, year: int) -> bool:
        """Select the tab for a specific year and return success status"""
        year_selector = f"//div[contains(@class, 'issue-details-past-tabs')]/ul/li/a[text()='{year}']"
        try:
            year_element = driver.find_element(By.XPATH, year_selector)
            parent_li = year_element.find_element(By.XPATH, "..")
            
            # Check if this year tab is already active
            is_active = 'active' in parent_li.get_attribute('class')
            
            # Only click if it's not already active
            if not is_active:
                year_element.click()
                time.sleep(1)  # Wait for the page to load
            return True
        except Exception as e:
            print(f"Year {year} not found or not clickable: {e}")
            return False


    def process_issue(self, issue_num: int, isnumber: str, href: str, volume_number: int) -> Optional[Issue]:
        """Process a single issue and return an Issue object if successful"""

        # Navigate to the issue page
        issue_driver = self.browser.navigate(href)
        details = self.extract_issue_details(issue_driver, issue_num)
            
        if details:
            return Issue(
                volume=volume_number,
                issue=issue_num,
                month=details['month'],
                numerical_month=details['numerical_month'],
                year=details['year'],
                isnumber=isnumber
            )
        
        return None


    def process_year(self, driver, url: str, year: int, previous_issues: IssuesDictionary) -> List[Issue]:
        """Process all issues for a single year"""
        year_issues = []
        try:
            # Make sure we're on the main page
            driver = self.browser.navigate(url)
            
            # Click on the year tab
            if not self.select_year(driver, year):
                return []
            
            # Extract volume and issue data
            volume_number = self.extract_volume_number(driver)
            issue_links = self.extract_issue_links(driver)

            count = 0
            # Process each issue
            for issue_num, isnumber, href in issue_links:
                # Skip if already in previous issues
                if previous_issues.has_issue(isnumber):
                    continue
                
                # Process this issue
                new_issue = self.process_issue(issue_num, isnumber, href, volume_number)
                if new_issue:
                    year_issues.append(new_issue)
                    count += 1
            
            print(f" -- Found {count} new issues out of {len(issue_links)}.")
            return year_issues
        except Exception as e:
            print(f"Error processing year {year}: {e}")
            raise


    def get_issues(self, url: str, previous_issues: IssuesDictionary) -> List[Issue]:
        """
        Get issues from the IEEE TVLSI page using smart year selection:
        - If previous_issues is empty, get all issues
        - Otherwise, only process years newer than our most recent stored issue
        - Handle the December/January edge case automatically
        """
        all_new_issues = []
        driver = None
        
        try:
            driver = self.browser.navigate(url)
            
            # Get all available years from the website
            all_years = self.get_years(driver)
            
            # Determine which years to process
            years_to_process = self.determine_years_to_process(all_years, previous_issues)
            
            # Process each year
            for year in years_to_process:
                print(f"Processing year {year}", end="")
                year_issues = self.process_year(driver, url, year, previous_issues)
                
                # Add to all new issues
                all_new_issues.extend(year_issues)
                
                # Save progress after each year
                if year_issues:
                    print(f"Saving {len(year_issues)} issues for year {year}...")
                    previous_issues.save_issues(year_issues)
                    
            return all_new_issues
        except Exception as e:
            print(f"Error getting issues: {e}")
            raise
        finally:
            if driver:
                self.browser.close()