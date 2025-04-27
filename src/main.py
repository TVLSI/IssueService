import os
from browser_manager import BrowserManager
from issue_storage import IssueStorage
from issue_scraper import IEEEScraper


def main():
    # URL for IEEE Transactions on VLSI Systems issues
    url = "https://ieeexplore.ieee.org/xpl/issues?punumber=92&isnumber=10937162"
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

    storage = IssueStorage(data_dir)
    browser = BrowserManager(headless=True)
    scraper = IEEEScraper(browser)

    previous_issues = storage.load_issues()
    latest_issue = storage.get_latest_issue() 


    # Find the newest issue if previous_issues is not empty
    if latest_issue:
        print(f"Last issue loaded: Volume {latest_issue.volume}, "
              f"Issue {latest_issue.issue}, {latest_issue.month} {latest_issue.year}")
    else:
        print("No previous issues found.")

    try:
        # Get current issues
        new_issues = scraper.get_issues(url, previous_issues)
        
        if not new_issues:
            print("No new issues found.")
            return

        # Print new issues
        if new_issues:
            print(f"Found {len(new_issues)} new issue(s):")
            for issue in new_issues:
                print(f"Volume: {issue.volume}, Year: {issue.year}, "
                      f"Month: {issue.month}, isnumber: {issue.isnumber}")
        else:
            print("No new issues found.")
        
        #all_issues = previous_issues + new_issues

        storage.save_issues(new_issues)
        # Save current issues for next run
        #save_issues(all_issues, issues_file)

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()