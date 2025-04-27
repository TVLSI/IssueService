import os
import json
from typing import List, Optional
from issue import Issue

# Constants
ISSUES_FILENAME = "previous_issues.json"

# TODO: make this a dictionary by issue number
# TODO: Load the issues on init so we dont load it mulitple times
class IssueStorage:
    """Handles loading and saving issues from/to storage"""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.issues_file = os.path.join(data_dir, ISSUES_FILENAME)
        os.makedirs(data_dir, exist_ok=True)


    def load_issues(self) -> List[Issue]:
        """Load issues from file"""
        if not os.path.exists(self.issues_file):
            return []
        
        with open(self.issues_file, 'r') as f:
            data = json.load(f)
            return [Issue.from_dict(item) for item in data]


    def save_issues(self, issues: List[Issue]) -> None:
        """Save issues to file, sorted by recency"""
        # TODO: This should class be a dictionary and append the new issues to the dictionary and save it.
        issue_list = self.load_issues()

        # TODO: Switch to check for duplicate month / year. 
        # Just be sure we dont have duplicates by issue number.
        for issue in issues:
            if issue not in issue_list:
                issue_list.append(issue)

        # Sort issues by year, volume, month, and issue number in descending order
        sorted_issues = sorted(
            issue_list, 
            key=lambda x: (x.year, x.volume, x.numerical_month, x.issue),
            reverse=True
        )
        
        # Convert to dictionaries for JSON serialization
        issue_dicts = [issue.to_dict() for issue in sorted_issues]
        
        with open(self.issues_file, 'w') as f:
            json.dump(issue_dicts, f, indent=2)


    def get_latest_issue(self) -> Optional[Issue]:
        """Get the most recent issue from storage"""
        issues = self.load_issues()
        if not issues:
            return None
        return issues[0]  # Already sorted, so first is most recent