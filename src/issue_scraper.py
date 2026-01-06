import re
import logging
from typing import List, Optional, Tuple
from selenium.webdriver.common.by import By
import time

from browser_manager import BrowserManager
from issue import Issue
from issues_dictionary import IssuesDictionary
import calendar
from datetime import datetime

logger = logging.getLogger(__name__)

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
                logger.error(f"Error parsing issue link: {e}", exc_info=True)
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
            logger.error(f"Error extracting issue details: {e}", exc_info=True)
            raise
        
        return None


    def get_years(self, driver) -> List[int]:
        """Extract all available years from the website"""
        years = []
        try:
            # Look for year tabs in both past and current year sections
            year_selectors = [
                "div.issue-details-past-tabs.year ul li a",  # Past years
                "div.issue-details-tabs.year ul li a",      # Current year section
                ".issue-details-past-tabs ul li a",         # Alternative past years selector
                ".issue-details-tabs ul li a"               # Alternative current year selector
            ]
            
            for selector in year_selectors:
                try:
                    year_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in year_elements:
                        try:
                            year_text = elem.text.strip()
                            if year_text.isdigit():  # Only process numeric years
                                years.append(int(year_text))
                        except ValueError:
                            continue
                except Exception:
                    continue  # Try next selector if this one fails
            
            # Remove duplicates and sort years from oldest to newest
            years = sorted(list(set(years)))
        except Exception as e:
            logger.error(f"Error getting years from website: {e}", exc_info=True)
        
        return years


    def determine_years_to_process(self, all_years: List[int], previous_issues: IssuesDictionary) -> List[int]:
        """Determine which years need to be processed based on previous issues"""
        if not previous_issues:
            # Process all years if no previous issues
            logger.info("No previous issues found. Processing all years...")
            return all_years
        
        # Get the most recent issue we have
        most_recent_issue = previous_issues.get_latest_issue()
        
        # Fix: Check if most_recent_issue is None before accessing attributes
        if most_recent_issue is None:
            logger.info("No previous issues found. Processing all years...")
            return all_years
        
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
        
        logger.info(f"Processing years newer than {last_year}-{last_month}: {years_to_process}")
        return years_to_process


    def select_year(self, driver, year: int) -> bool:
        """Select the tab for a specific year and return success status"""
        
        # First, try to find the year as a link with href (this is the most current year)
        # The current year shows as: <a href="/xpl/tocresult.jsp?isnumber=...">2026 </a>
        try:
            # More relaxed selector - just look for any anchor with the year text and href attribute
            year_str = str(year)
            year_links = driver.find_elements(By.XPATH, f"//a[@href and contains(text(), '{year_str}')]")
            
            for link in year_links:
                # Check if the text is exactly the year (with possible whitespace)
                if link.text.strip() == year_str:
                    href = link.get_attribute('href')
                    # If it has an href with isnumber, it's a direct link to the year's issues
                    if href and 'isnumber=' in href:
                        logger.debug(f"Year {year} found as current year (direct link)")
                        # Navigate to this page to show the year's issues
                        driver.get(href)
                        time.sleep(2)  # Wait for page to load
                        return True
        except Exception as e:
            logger.debug(f"Error checking for direct year link: {e}")
        # These show as: <a data-analytics_identifier="past_issue_selected_year">2025</a>
        year_selectors = [
            f"//a[normalize-space(text())='{year}' and @data-analytics_identifier='past_issue_selected_year']",  # Past years with analytics ID
            f"//div[contains(@class, 'issue-details-past-tabs')]//a[normalize-space(text())='{year}']",  # Generic past years
            f"//div[contains(@class, 'issue-details-tabs')]//a[normalize-space(text())='{year}']",       # Alternative location
        ]
        
        for selector in year_selectors:
            try:
                year_element = driver.find_element(By.XPATH, selector)
                parent_li = year_element.find_element(By.XPATH, "..")
                
                # Check if this year tab is already active
                is_active = 'active' in parent_li.get_attribute('class')
                
                # Only click if it's not already active
                if not is_active:
                    year_element.click()
                    time.sleep(2)  # Wait for the page to load
                
                logger.debug(f"Year {year} selected via clickable tab")
                return True
            except Exception:
                continue  # Try next selector
        
        logger.warning(f"Year {year} not found with any selector")
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


    def extract_issue_from_toc_page(self, driver) -> Optional[dict]:
        """Extract issue information when on a TOC (table of contents) page
        
        This handles the case where clicking a year takes us directly to an issue's TOC page,
        which happens for the current year or years with only one issue.
        """
        try:
            # Check if we're on a TOC page by looking for the URL pattern
            current_url = driver.current_url
            if 'tocresult.jsp' not in current_url:
                return None
            
            # Extract isnumber from URL
            isnumber_match = re.search(r'isnumber=(\d+)', current_url)
            if not isnumber_match:
                return None
            isnumber = isnumber_match.group(1)
            
            # Wait for the page to fully load - Angular pages take time to render
            time.sleep(3)
            
            # Find any article on the page to extract volume/issue/year info
            # The HTML structure uses nested spans within divs
            # We need to use textContent to get ALL text including from nested elements
            try:
                # Find description div elements (each article has one)
                description_elements = driver.find_elements(By.CSS_SELECTOR, "div.description")
                
                for desc_elem in description_elements:
                    try:
                        # Look for inner divs within this description
                        inner_divs = desc_elem.find_elements(By.CSS_SELECTOR, "div")
                        
                        # The second div (index 1) usually contains Year/Volume/Issue
                        if len(inner_divs) >= 2:
                            info_div = inner_divs[1]
                            # Use textContent instead of .text to get all nested text
                            text = info_div.get_attribute('textContent').strip()
                            
                            # Skip empty divs
                            if not text:
                                continue
                            
                            # The text should be like "Year: 2026 | Volume: 34 | Issue: 1"
                            year_match = re.search(r'Year:\s*(\d{4})', text)
                            volume_match = re.search(r'Volume:\s*(\d+)', text)
                            issue_match = re.search(r'Issue:\s*(\d+)', text)
                            
                            if year_match and volume_match and issue_match:
                                year = int(year_match.group(1))
                                volume = int(volume_match.group(1))
                                issue = int(issue_match.group(1))
                                
                                # Determine the month based on the issue number
                                # IEEE TVLSI publishes monthly, so Issue 1 = January, Issue 2 = February, etc.
                                if 1 <= issue <= 12:
                                    month_name = calendar.month_name[issue]
                                    
                                    return {
                                        'year': year,
                                        'volume': volume,
                                        'issue': issue,
                                        'month': month_name,
                                        'numerical_month': issue,
                                        'isnumber': isnumber
                                    }
                    except Exception:
                        continue  # Try next description element
                        
            except Exception as e:
                logger.error(f"Error extracting from TOC page elements: {e}", exc_info=True)
                
            return None
        except Exception as e:
            logger.error(f"Error in extract_issue_from_toc_page: {e}", exc_info=True)
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
            
            # Check if we landed on a TOC page (happens for current year with single issue)
            toc_info = self.extract_issue_from_toc_page(driver)
            if toc_info:
                # We found an issue directly from the TOC page
                isnumber = toc_info['isnumber']
                
                # Skip if already in previous issues
                if not previous_issues.has_issue(isnumber):
                    new_issue = Issue(
                        volume=toc_info['volume'],
                        issue=toc_info['issue'],
                        month=toc_info['month'],
                        numerical_month=toc_info['numerical_month'],
                        year=toc_info['year'],
                        isnumber=isnumber
                    )
                    year_issues.append(new_issue)
                    logger.info(f" -- Found 1 new issue: Volume {toc_info['volume']}, Issue {toc_info['issue']}, {toc_info['month']} {toc_info['year']}")
                else:
                    logger.debug(f" -- Issue already in database")
                
                return year_issues
            
            # Otherwise, extract volume and issue data the traditional way
            volume_number = self.extract_volume_number(driver)
            issue_links = self.extract_issue_links(driver)

            count = 0
            possible_new_issues = 0
            # Process each issue
            for issue_num, isnumber, href in issue_links:
                # Skip if already in previous issues
                if previous_issues.has_issue(isnumber):
                    continue
                possible_new_issues += 1
                # Process this issue
                new_issue = self.process_issue(issue_num, isnumber, href, volume_number)
                if new_issue:
                    year_issues.append(new_issue)
                    count += 1
            if possible_new_issues > 0:
                logger.info(f" -- Found {count} new issues out of {len(issue_links)}.")

            return year_issues
        except Exception as e:
            logger.error(f"Error processing year {year}: {e}", exc_info=True)
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
                logger.info(f"Processing year {year}...")
                year_issues = self.process_year(driver, url, year, previous_issues)
                
                # Add to all new issues
                all_new_issues.extend(year_issues)
                
                # Save progress after each year
                if year_issues:
                    logger.info(f"Saving {len(year_issues)} issues for year {year}...")
                    previous_issues.save_issues(year_issues)
                    
            return all_new_issues
        except Exception as e:
            logger.error(f"Error getting issues: {e}", exc_info=True)
            raise
        finally:
            if driver:
                self.browser.close()