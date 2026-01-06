import os
import sys
import json
import logging
from browser_manager import BrowserManager
from issues_dictionary import IssuesDictionary
from issue_scraper import IEEEScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Constants
ISSUES_URL = "https://ieeexplore.ieee.org/xpl/issues?punumber=92&isnumber=10937162"
DEFAULT_ISSUES_FILENAME = "previous_issues.json"

def main():
    logger.info(f"Starting IssueService with arguments: {sys.argv}")
    # Parse command line arguments for GitHub Action mode
    if len(sys.argv) > 1:
        # Use the provided file path directly
        issues_file = sys.argv[1]
        logger.info(f"Using command line path: '{issues_file}'")
    else:
        # Default path for local testing
        data_dir = os.path.join(os.getcwd(), "data")
        issues_file = os.path.join(data_dir, DEFAULT_ISSUES_FILENAME)
        logger.info(f"Using default path: '{issues_file}'")

    try:
        previous_issues = IssuesDictionary(issues_file)
    except IOError as e:
        logger.error(f"Failed to initialize issues dictionary: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error initializing issues dictionary: {e}", exc_info=True)
        sys.exit(1)

    browser = BrowserManager(headless=True)
    scraper = IEEEScraper(browser)

    latest_issue = previous_issues.get_latest_issue()

    # Find the newest issue if previous_issues is not empty
    if latest_issue:
        logger.info(f"Last issue loaded: Volume {latest_issue.volume}, "
                    f"Issue {latest_issue.issue}, {latest_issue.month} {latest_issue.year}")
    else:
        logger.info("No previous issues found. Will process all available issues.")

    try:
        # Get new issues
        new_issues = scraper.get_issues(ISSUES_URL, previous_issues)

        # Log new issues
        if new_issues:
            logger.info(f"Found {len(new_issues)} new issue(s):")
            for issue in new_issues:
                logger.info(f"  Volume: {issue.volume}, Issue: {issue.issue}, "
                           f"Month: {issue.month}, Year: {issue.year}, isnumber: {issue.isnumber}")
            
            # Set GitHub Action outputs
            if os.environ.get('GITHUB_OUTPUT'):
                try:
                    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                        f.write(f"new_issues_count={len(new_issues)}\n")
                        f.write("has_new_issues=true\n")
                        
                        # Convert issues to a list of dictionaries for JSON serialization
                        issues_list = [issue.to_dict() for issue in new_issues]
                        
                        # Serialize issues as a compact JSON string. Using
                        # ``ensure_ascii=False`` keeps the output valid JSON
                        # while avoiding unnecessary character escapes.
                        issues_json = json.dumps(issues_list, ensure_ascii=False)

                        # Write issues to the GitHub output file
                        f.write(f"new_issues<<EOF\n{issues_json}\nEOF\n")
                    logger.info("GitHub Action outputs written successfully")
                except IOError as e:
                    logger.error(f"Failed to write GitHub Action outputs: {e}")
                    sys.exit(1)
        else:
            logger.info("No new issues found.")
            # Set GitHub Action outputs for no new issues
            if os.environ.get('GITHUB_OUTPUT'):
                try:
                    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                        f.write("new_issues_count=0\n")
                        f.write("has_new_issues=false\n")
                        f.write(f"new_issues<<EOF\n[]\nEOF\n")
                    logger.info("GitHub Action outputs written (no new issues)")
                except IOError as e:
                    logger.error(f"Failed to write GitHub Action outputs: {e}")
                    sys.exit(1)
        return

    except KeyboardInterrupt:
        logger.warning("Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error during scraping: {e}", exc_info=True)
        sys.exit(1)
        
if __name__ == "__main__":
    main()