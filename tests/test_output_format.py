import os
import json
from unittest.mock import patch, MagicMock
from src.main import main
from src.issue import Issue

def extract_json(output_text):
    """Helper to extract the JSON string from GitHub output text."""
    import re
    m = re.search(r"new_issues<<EOF\n(.*)\nEOF", output_text, flags=re.DOTALL)
    return m.group(1) if m else None

@patch('src.main.IssuesDictionary')
@patch('src.main.BrowserManager')
@patch('src.main.IEEEScraper')
@patch('sys.argv', ['main.py', '/app/data/previous_issues.json'])
def test_output_is_valid_json(mock_scraper_cls, mock_browser_cls, mock_issues_cls, tmp_path):
    # Prepare mocks
    mock_scraper = MagicMock()
    mock_scraper.get_issues.return_value = [
        Issue(volume=33, issue=6, month='June', numerical_month=6, year=2025, isnumber='11010805')
    ]
    mock_scraper_cls.return_value = mock_scraper

    mock_browser_cls.return_value = MagicMock()

    mock_issues = MagicMock()
    mock_issues.get_latest_issue.return_value = None
    mock_issues_cls.return_value = mock_issues

    output_file = tmp_path / 'out.txt'
    os.environ['GITHUB_OUTPUT'] = str(output_file)
    try:
        main()
    finally:
        os.environ.pop('GITHUB_OUTPUT', None)

    data = output_file.read_text()
    json_str = extract_json(data)
    assert json_str is not None
    parsed = json.loads(json_str)
    assert isinstance(parsed, list)
    assert parsed[0]['volume'] == 33
