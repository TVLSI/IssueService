"""
Integration tests for the IssueService

These tests verify that multiple components work together correctly.
"""
import pytest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.main import main
from src.issue import Issue
from src.issues_dictionary import IssuesDictionary
from src.browser_manager import BrowserManager
from src.issue_scraper import IEEEScraper


@pytest.mark.integration
class TestEndToEndWorkflow:
    """Test complete end-to-end workflows"""
    
    @patch('src.main.IEEEScraper')
    @patch('src.main.BrowserManager')
    @patch('src.main.IssuesDictionary')
    @patch('sys.argv', ['main.py', '/tmp/test_issues.json'])
    def test_main_with_new_issues_found(self, mock_issues_cls, mock_browser_cls, mock_scraper_cls, tmp_path):
        """Test complete main() workflow when new issues are found"""
        # Setup mocks
        mock_issues = MagicMock()
        mock_issues.get_latest_issue.return_value = None
        mock_issues_cls.return_value = mock_issues
        
        mock_browser = MagicMock()
        mock_browser_cls.return_value = mock_browser
        
        new_issues = [
            Issue(volume=34, issue=1, month='January', numerical_month=1, year=2026, isnumber='12345'),
            Issue(volume=34, issue=2, month='February', numerical_month=2, year=2026, isnumber='12346'),
        ]
        
        mock_scraper = MagicMock()
        mock_scraper.get_issues.return_value = new_issues
        mock_scraper_cls.return_value = mock_scraper
        
        # Create temporary output file for GitHub Actions
        output_file = tmp_path / "github_output.txt"
        os.environ['GITHUB_OUTPUT'] = str(output_file)
        
        try:
            # Run main
            main()
            
            # Verify scraper was called
            mock_scraper.get_issues.assert_called_once()
            
            # Verify GitHub output was written
            assert output_file.exists()
            content = output_file.read_text()
            
            assert "new_issues_count=2" in content
            assert "has_new_issues=true" in content
            assert "new_issues<<EOF" in content
            
            # Verify JSON output is valid
            json_match = content.split("new_issues<<EOF\n")[1].split("\nEOF")[0]
            issues_data = json.loads(json_match)
            assert len(issues_data) == 2
            assert issues_data[0]['volume'] == 34
            assert issues_data[0]['issue'] == 1
            
        finally:
            os.environ.pop('GITHUB_OUTPUT', None)
    
    @patch('src.main.IEEEScraper')
    @patch('src.main.BrowserManager')
    @patch('src.main.IssuesDictionary')
    @patch('sys.argv', ['main.py', '/tmp/test_issues.json'])
    def test_main_with_no_new_issues(self, mock_issues_cls, mock_browser_cls, mock_scraper_cls, tmp_path):
        """Test complete main() workflow when no new issues are found"""
        # Setup mocks
        mock_issues = MagicMock()
        mock_issues.get_latest_issue.return_value = Issue(
            volume=33, issue=12, month='December', numerical_month=12, year=2025, isnumber='99999'
        )
        mock_issues_cls.return_value = mock_issues
        
        mock_browser = MagicMock()
        mock_browser_cls.return_value = mock_browser
        
        mock_scraper = MagicMock()
        mock_scraper.get_issues.return_value = []  # No new issues
        mock_scraper_cls.return_value = mock_scraper
        
        # Create temporary output file
        output_file = tmp_path / "github_output.txt"
        os.environ['GITHUB_OUTPUT'] = str(output_file)
        
        try:
            # Run main
            main()
            
            # Verify GitHub output
            content = output_file.read_text()
            assert "new_issues_count=0" in content
            assert "has_new_issues=false" in content
            assert "new_issues<<EOF\n[]\nEOF" in content
            
        finally:
            os.environ.pop('GITHUB_OUTPUT', None)


@pytest.mark.integration
class TestIssuesDictionaryIntegration:
    """Test IssuesDictionary integration with file system"""
    
    def test_save_and_reload_cycle(self, tmp_path):
        """Test saving issues and reloading them in a new instance"""
        issues_file = tmp_path / "issues.json"
        
        # Create and save issues
        dict1 = IssuesDictionary(str(issues_file))
        issues = [
            Issue(volume=33, issue=1, month='January', numerical_month=1, year=2025, isnumber='10001'),
            Issue(volume=33, issue=2, month='February', numerical_month=2, year=2025, isnumber='10002'),
            Issue(volume=33, issue=3, month='March', numerical_month=3, year=2025, isnumber='10003'),
        ]
        dict1.save_issues(issues)
        
        # Verify file was created
        assert issues_file.exists()
        
        # Load in new instance
        dict2 = IssuesDictionary(str(issues_file))
        
        # Verify all issues loaded
        assert len(dict2) == 3
        assert dict2.has_issue('10001')
        assert dict2.has_issue('10002')
        assert dict2.has_issue('10003')
        
        # Verify latest issue
        latest = dict2.get_latest_issue()
        assert latest.numerical_month == 3
    
    def test_incremental_saves(self, tmp_path):
        """Test that multiple saves accumulate issues correctly"""
        issues_file = tmp_path / "issues.json"
        
        # First save
        dict1 = IssuesDictionary(str(issues_file))
        dict1.save_issues([
            Issue(volume=33, issue=1, month='January', numerical_month=1, year=2025, isnumber='10001')
        ])
        
        # Reload and add more
        dict2 = IssuesDictionary(str(issues_file))
        assert len(dict2) == 1
        
        dict2.save_issues([
            Issue(volume=33, issue=2, month='February', numerical_month=2, year=2025, isnumber='10002')
        ])
        
        # Reload and verify
        dict3 = IssuesDictionary(str(issues_file))
        assert len(dict3) == 2
    
    def test_duplicate_prevention_across_saves(self, tmp_path):
        """Test that duplicates are prevented across multiple save operations"""
        issues_file = tmp_path / "issues.json"
        
        same_issue = Issue(volume=33, issue=1, month='January', numerical_month=1, year=2025, isnumber='10001')
        
        # First save
        dict1 = IssuesDictionary(str(issues_file))
        dict1.save_issues([same_issue])
        assert len(dict1) == 1
        
        # Try to save same issue again
        dict1.save_issues([same_issue])
        assert len(dict1) == 1  # Should still be 1
        
        # Reload and verify
        dict2 = IssuesDictionary(str(issues_file))
        assert len(dict2) == 1


@pytest.mark.integration
class TestScraperIntegration:
    """Test scraper integration with browser and issues dictionary"""
    
    @patch('src.issue_scraper.time.sleep')
    def test_scraper_with_mock_browser_and_issues_dict(self, mock_sleep, tmp_path):
        """Test scraper integration with mocked browser responses"""
        issues_file = tmp_path / "issues.json"
        issues_dict = IssuesDictionary(str(issues_file))
        
        # Add existing issue from November 2025
        existing_issue = Issue(volume=33, issue=11, month='November', numerical_month=11, year=2025, isnumber='10010')
        issues_dict.save_issues([existing_issue])
        
        # Create mock browser
        mock_browser = MagicMock(spec=BrowserManager)
        mock_driver = MagicMock()
        mock_browser.navigate.return_value = mock_driver
        
        # Create scraper
        scraper = IEEEScraper(mock_browser)
        
        # Mock the methods
        with patch.object(scraper, 'get_years') as mock_get_years, \
             patch.object(scraper, 'process_year') as mock_process_year:
            
            mock_get_years.return_value = [2025, 2026]
            
            # Return different issues based on year
            def process_year_side_effect(driver, url, year, issues_dict):
                if year == 2025:
                    # Dec 2025 - completes the year
                    return [Issue(volume=33, issue=12, month='December', numerical_month=12, year=2025, isnumber='10012')]
                elif year == 2026:
                    # New year
                    return [Issue(volume=34, issue=1, month='January', numerical_month=1, year=2026, isnumber='10011')]
                return []
            
            mock_process_year.side_effect = process_year_side_effect
            
            # Run scraper
            found_issues = scraper.get_issues("https://example.com", issues_dict)
            
            # Verify results - should find issues from both 2025 and 2026
            assert len(found_issues) == 2
            assert any(issue.year == 2025 for issue in found_issues)
            assert any(issue.year == 2026 for issue in found_issues)


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling across components"""
    
    def test_malformed_json_recovery(self, tmp_path):
        """Test that system recovers from malformed JSON"""
        issues_file = tmp_path / "issues.json"
        
        # Write malformed JSON
        issues_file.write_text("{ invalid json }")
        
        # Should handle gracefully
        issues_dict = IssuesDictionary(str(issues_file))
        assert len(issues_dict) == 0
        
        # Should be able to save new issues
        new_issue = Issue(volume=33, issue=1, month='January', numerical_month=1, year=2025, isnumber='10001')
        issues_dict.save_issues([new_issue])
        
        # Should have recovered
        assert len(issues_dict) == 1
    
    def test_missing_directory_creation(self, tmp_path):
        """Test that missing directories are created automatically"""
        nested_path = tmp_path / "data" / "nested" / "issues.json"
        
        # Path doesn't exist
        assert not nested_path.parent.exists()
        
        # Create issues dict
        issues_dict = IssuesDictionary(str(nested_path))
        
        # Directory should be created
        assert nested_path.parent.exists()
        assert nested_path.exists()


@pytest.mark.integration
class TestDataConsistency:
    """Test data consistency across operations"""
    
    def test_sorting_consistency(self, tmp_path):
        """Test that issues remain sorted after multiple operations"""
        issues_file = tmp_path / "issues.json"
        issues_dict = IssuesDictionary(str(issues_file))
        
        # Add issues out of order
        issues = [
            Issue(volume=33, issue=6, month='June', numerical_month=6, year=2025, isnumber='10006'),
            Issue(volume=33, issue=1, month='January', numerical_month=1, year=2025, isnumber='10001'),
            Issue(volume=33, issue=3, month='March', numerical_month=3, year=2025, isnumber='10003'),
        ]
        issues_dict.save_issues(issues)
        
        # Load file directly and check order
        with open(issues_file, 'r') as f:
            data = json.load(f)
        
        # Should be sorted newest to oldest
        assert data[0]['numerical_month'] == 6
        assert data[1]['numerical_month'] == 3
        assert data[2]['numerical_month'] == 1
    
    def test_isnumber_uniqueness(self, tmp_path):
        """Test that isnumber remains unique across operations"""
        issues_file = tmp_path / "issues.json"
        issues_dict = IssuesDictionary(str(issues_file))
        
        # Try to add issues with same isnumber
        issue1 = Issue(volume=33, issue=1, month='January', numerical_month=1, year=2025, isnumber='10001')
        issue2 = Issue(volume=33, issue=2, month='February', numerical_month=2, year=2025, isnumber='10001')
        
        issues_dict.save_issues([issue1])
        issues_dict.save_issues([issue2])
        
        # Should only have one issue (latest overwrites)
        assert len(issues_dict) == 1
        
        # Should be the second issue (updated)
        stored_issue = issues_dict['10001']
        assert stored_issue.issue == 2
