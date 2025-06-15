import os
import sys
import json
from browser_manager import BrowserManager
from issues_dictionary import IssuesDictionary
from issue_scraper import IEEEScraper


# Constants
ISSUES_URL = "https://ieeexplore.ieee.org/xpl/issues?punumber=92&isnumber=10937162"
DEFAULT_ISSUES_FILENAME = "previous_issues.json"

def main():
    print(f"sys.argv: {sys.argv}")
    # Parse command line arguments for GitHub Action mode
    if len(sys.argv) > 1:
        # Use the provided file path directly
        issues_file = sys.argv[1]
        print(f"Using command line path: '{issues_file}'")
    else:
        # Default path for local testing
        data_dir = os.path.join(os.getcwd(), "data")
        issues_file = os.path.join(data_dir, DEFAULT_ISSUES_FILENAME)
        print(f"Using default path: '{issues_file}'")

    previous_issues = IssuesDictionary(issues_file)
    browser = BrowserManager(headless=True)
    scraper = IEEEScraper(browser)

    latest_issue = previous_issues.get_latest_issue()

    # Find the newest issue if previous_issues is not empty
    if latest_issue:
        print(f"Last issue loaded: Volume {latest_issue.volume}, "
              f"Issue {latest_issue.issue}, {latest_issue.month} {latest_issue.year}")
    else:
        print("No previous issues found.")

    try:
        # Get new issues
        new_issues = scraper.get_issues(ISSUES_URL, previous_issues)

        # Print new issues
        if new_issues:
            print(f"Found {len(new_issues)} new issue(s):")
            for issue in new_issues:
                print(f"Volume: {issue.volume}, Year: {issue.year}, "
                      f"Month: {issue.month}, isnumber: {issue.isnumber}")
            
            # Set GitHub Action outputs
            if os.environ.get('GITHUB_OUTPUT'):
                with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                    f.write(f"new_issues_count={len(new_issues)}\n")
                    f.write("has_new_issues=true\n")
                    
                    # Convert issues to a list of dictionaries for JSON serialization
                    issues_list = [issue.to_dict() for issue in new_issues]
                    
                    # Write issues as a JSON string
                    f.write(f"new_issues<<EOF\n{json.dumps(issues_list)}\nEOF\n")
        else:
            print("No new issues found.")
            # Set GitHub Action outputs for no new issues
            if os.environ.get('GITHUB_OUTPUT'):
                with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                    f.write("new_issues_count=0\n")
                    f.write("has_new_issues=false\n")
                    f.write(f"new_issues<<EOF\n[]\nEOF\n")
        return

    except Exception as e:
        print(f"Error: {str(e)}")
        # Exit with error code
        sys.exit(1)
        
if __name__ == "__main__":
    main()