import os
import json
import logging
from typing import Dict, List, Optional, Any
from issue import Issue

logger = logging.getLogger(__name__)


class IssuesDictionary(dict):
    """Dictionary of IEEE TVLSI issues that auto-loads/saves to storage"""
    
    def __init__(self, issues_file_path: str):
        super().__init__()
        self.issues_file = issues_file_path
        self.data_dir = os.path.dirname(self.issues_file)
        os.makedirs(self.data_dir, exist_ok=True)

        # Test file write permissions early
        self._test_file_permissions()

        # Load issues on initialization
        self._load_issues()


    def _test_file_permissions(self) -> None:
        """Test file write permissions early to avoid wasted scraping work"""
        try:
            # If file doesn't exist, create it as an empty JSON array
            if not os.path.exists(self.issues_file):
                with open(self.issues_file, 'w') as f:
                    json.dump([], f)
                    
            # If it exists, make sure we can open it for writing
            else:
                with open(self.issues_file, 'a') as f:
                    pass
        except Exception as e:
            raise IOError(f"Cannot write to issues file {self.issues_file}: {e}")


    def _load_issues(self) -> None:
        """Load issues from file into this dictionary"""
        if not os.path.exists(self.issues_file):
            return
        
        try:
            with open(self.issues_file, 'r') as f:
                data = json.load(f)
                for item in data:
                    issue = Issue.from_dict(item)
                    key = issue.isnumber
                    self[key] = issue
        except json.JSONDecodeError as e:
            logger.error(f"Malformed JSON in issues file {self.issues_file}: {e}")
        except (KeyError, ValueError) as e:
            logger.error(f"Invalid issue data in file {self.issues_file}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error loading issues: {e}", exc_info=True)


    def save_issues(self, new_issues: List[Issue]) -> None:
        """Add new issues to the dictionary and save all to file"""
        # Add new issues to the dictionary
        for issue in new_issues:
            key = issue.isnumber
            self[key] = issue
        
        self.save()


    def save(self) -> None:
        """Save the entire dictionary to file"""
        # Sort issues by recency before saving
        sorted_issues = sorted(
            self.values(),
            key=lambda x: (x.year, x.numerical_month, x.issue),
            reverse=True
        )
        
        # Convert to dictionaries for JSON serialization
        issue_dicts = [issue.to_dict() for issue in sorted_issues]
        
        with open(self.issues_file, 'w') as f:
            json.dump(issue_dicts, f, indent=2)


    def get_latest_issue(self) -> Optional[Issue]:
        """Get the most recent issue"""
        if not self:
            return None
        
        # Find the latest issue by sorting by year and month.
        return sorted(
            self.values(),
            key=lambda x: (x.year, x.numerical_month, x.issue),
            reverse=True
        )[0]
    
    def has_issue(self, isnumber: str) -> bool:
        """Check if a specific issue exists by its isnumber"""
        return isnumber in self