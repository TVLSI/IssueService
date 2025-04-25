import json
import os
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def get_issues(url):
    """
    Scrape IEEE TVLSI issues page and extract issue information using Selenium.
    """
    # Configure Chrome to run headless
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        driver.get(url)
        
        # Wait for page to load (adjust timeout as needed)
        time.sleep(5)
        
        # I might not need this, but let's keep it for now
        try:
            # Wait for the years element to be present
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='issue-details-past-tabs'][class*='year']"))
            )
            
            years_div = driver.find_element(By.CSS_SELECTOR, "div[class*='issue-details-past-tabs'][class*='year']")
            active_year_element = years_div.find_element(By.CSS_SELECTOR, "li[class*='active'] a")
            active_year = int(active_year_element.text.strip())
            
            print(f"Active year: {active_year}")
        except Exception as e:
            print(f"Error extracting active year: {e}")
        
        # Get children of the section to make it iterable
        volume_elements = driver.find_element(By.CSS_SELECTOR, "section[class*='issue-container']")
        issue_elements = volume_elements.find_elements(By.CSS_SELECTOR, "div[class*='issue-details']")
        
        # Get issues
        issues = []
        try:
            # Find volume elements
            # Find the section containing the issues
            volume_elements = driver.find_element(By.CSS_SELECTOR, "section[class*='issue-container']")
            
            # Extract the first div containing the text "Volume"
            volume_div = volume_elements.find_element(By.XPATH, ".//div[strong[contains(text(), 'Volume')]]")
            volume_text = volume_div.text.strip()
            
            # Extract just the number from the volume text
            volume_number = re.search(r'Volume\s+(\d+)', volume_text, re.IGNORECASE).group(1)
            print(f"Current Volume: {volume_number}")
            issue_elements = volume_elements.find_elements(By.CSS_SELECTOR, "div[class*='issue-details']")
            
            issue_data = []
            for element in issue_elements:
                try:
                    issue_link = element.find_element(By.CSS_SELECTOR, "a[href*='isnumber=']")
                    issue_text = issue_link.text.strip()
                    href = issue_link.get_attribute("href")
                    
                    # Extract issue and isnumber
                    issue_match = re.search(r'Issue\s+(\d+)', issue_text, re.IGNORECASE)
                    isnumber_match = re.search(r'isnumber=(\d+)', href)
                    
                    if issue_match and isnumber_match:
                        issue_num = int(issue_match.group(1))
                        isnumber = isnumber_match.group(1)
                        issue_data.append((issue_num, isnumber, href))
                    else:
                        print(f"Missing issue or isnumber for element: {issue_text}")
                except Exception as e:
                    print(f"Error parsing issue: {e}")
            
            for issue_num, isnumber, href in issue_data:
                try:
                    # Navigate to the issue page to extract additional details
                    driver.get(href)
                    time.sleep(5)  # Allow the page to load
                    
                    try:
                        issue_details_element = driver.find_element(By.CSS_SELECTOR, "div.u-m-1.u-mt-1.u-mr-1.text-base-md p b")
                        issue_details_text = issue_details_element.text.strip()
                        print(f"Extracted issue details: {issue_details_text}")
                        
                        # Validate issue number and extract month/year
                        month_year_match = re.search(r'•\s+(\w+)-(\d{4})', issue_details_text)
                        
                        if month_year_match:
                            month, year = month_year_match.groups()
                            
                            # Extract full month name and numerical month
                            month_to_num = {
                                'January': 1, 'February': 2, 'March': 3, 'April': 4,
                                'May': 5, 'June': 6, 'July': 7, 'August': 8,
                                'September': 9, 'October': 10, 'November': 11, 'December': 12
                            }
                            
                            # Verify issue number matches and extract full month name
                            if f"Issue {issue_num}" in issue_details_text:
                                full_month_match = re.search(r'•\s+([A-Za-z]+)-(\d{4})', issue_details_text)
                                if full_month_match:
                                    full_month = full_month_match.group(1)
                                    numerical_month = month_to_num.get(full_month, 0)
                                    
                                    issues.append({
                                        'volume': int(volume_number),
                                        'issue': issue_num,
                                        'month': full_month,
                                        'numerical_month': numerical_month,
                                        'year': int(year),
                                        'isnumber': isnumber
                                    })
                                else:
                                    print(f"Could not extract full month for issue {issue_num}")
                            else:
                                print(f"Issue number {issue_num} does not match details text: {issue_details_text}")
                    except Exception as e:
                        print(f"Error extracting issue details from issue page: {e}")
                except Exception as e:
                    print(f"Error navigating to issue page: {e}")
        except Exception as e:
            print(f"Error extracting issues: {e}")
        
        return issues
        
    finally:
        driver.quit()

def save_issues(issues, file_path):
    """Save the list of issues to a JSON file."""
    with open(file_path, 'w') as f:
        json.dump(issues, f, indent=2)

def load_issues(file_path):
    """Load the list of previously seen issues from a JSON file."""
    if not os.path.exists(file_path):
        return []
    
    with open(file_path, 'r') as f:
        return json.load(f)

def find_new_issues(current_issues, previous_issues):
    """Find new issues by comparing current issues with previously seen issues."""
    if not previous_issues:
        return current_issues
    
    # Convert previous issues to a set of tuples for easy comparison
    prev_issue_set = {(issue['volume'], issue['year'], issue['month'], issue['isnumber']) 
                     for issue in previous_issues}
    
    new_issues = []
    for issue in current_issues:
        issue_tuple = (issue['volume'], issue['year'], issue['month'], issue['isnumber'])
        if issue_tuple not in prev_issue_set:
            new_issues.append(issue)
    
    return new_issues

def main():
    # URL for IEEE Transactions on VLSI Systems issues
    url = "https://ieeexplore.ieee.org/xpl/issues?punumber=92&isnumber=10937162"
    
    # File path to store previously seen issues
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)
    issues_file = os.path.join(data_dir, "previous_issues.json")
    
    try:
        # Get current issues
        current_issues = get_issues(url)
        
        if not current_issues:
            print("No issues found on the page. Check if the page structure has changed.")
            return
        
        # Sort issues by year (descending), volume (descending)
        current_issues.sort(key=lambda x: (x['year'], x['volume']), reverse=True)
        
        # Load previously seen issues
        previous_issues = load_issues(issues_file)
        
        # Find new issues
        new_issues = find_new_issues(current_issues, previous_issues)
        
        # Print new issues
        if new_issues:
            print(f"Found {len(new_issues)} new issue(s):")
            for issue in new_issues:
                print(f"Volume: {issue['volume']}, Year: {issue['year']}, Month: {issue['month']}, isnumber: {issue['isnumber']}")
        else:
            print("No new issues found.")
        
        # Save current issues for next run
        save_issues(current_issues, issues_file)
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()