"""
Comprehensive tests for IssuesDictionary class
"""
import pytest
import json
import os
from pathlib import Path
from src.issues_dictionary import IssuesDictionary
from src.issue import Issue


@pytest.fixture
def temp_issues_file(tmp_path):
    """Create a temporary issues file path"""
    return str(tmp_path / "test_issues.json")


@pytest.fixture
def sample_issues():
    """Sample issues for testing"""
    return [
        Issue(volume=33, issue=5, month="May", numerical_month=5, year=2025, isnumber="10977652"),
        Issue(volume=33, issue=6, month="June", numerical_month=6, year=2025, isnumber="10977653"),
        Issue(volume=33, issue=1, month="January", numerical_month=1, year=2025, isnumber="10977641"),
    ]


class TestIssuesDictionaryInitialization:
    """Test initialization and file loading"""
    
    def test_init_creates_directory_if_not_exists(self, tmp_path):
        """Test that initialization creates directory structure"""
        nested_path = tmp_path / "data" / "nested" / "issues.json"
        issues_dict = IssuesDictionary(str(nested_path))
        
        assert nested_path.parent.exists()
        assert nested_path.exists()
    
    def test_init_creates_empty_file_if_not_exists(self, temp_issues_file):
        """Test that initialization creates an empty JSON file"""
        issues_dict = IssuesDictionary(temp_issues_file)
        
        assert os.path.exists(temp_issues_file)
        with open(temp_issues_file, 'r') as f:
            data = json.load(f)
            assert data == []
    
    def test_init_loads_existing_issues(self, temp_issues_file, sample_issues):
        """Test that initialization loads existing issues from file"""
        # Create file with sample data
        with open(temp_issues_file, 'w') as f:
            json.dump([issue.to_dict() for issue in sample_issues], f)
        
        issues_dict = IssuesDictionary(temp_issues_file)
        
        assert len(issues_dict) == 3
        assert issues_dict.has_issue("10977652")
        assert issues_dict.has_issue("10977653")
        assert issues_dict.has_issue("10977641")
    
    def test_init_handles_empty_json_file(self, temp_issues_file):
        """Test that initialization handles empty JSON array"""
        with open(temp_issues_file, 'w') as f:
            json.dump([], f)
        
        issues_dict = IssuesDictionary(temp_issues_file)
        assert len(issues_dict) == 0
    
    def test_init_raises_error_on_readonly_directory(self, tmp_path):
        """Test that initialization fails gracefully on read-only directory"""
        if os.name == 'nt':
            pytest.skip("Read-only testing is complex on Windows")
        
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        readonly_file = readonly_dir / "issues.json"
        
        # Make directory read-only
        readonly_dir.chmod(0o444)
        
        try:
            with pytest.raises(IOError, match="Cannot write to issues file"):
                IssuesDictionary(str(readonly_file))
        finally:
            # Clean up - restore write permissions
            readonly_dir.chmod(0o755)


class TestIssuesDictionarySaving:
    """Test saving functionality"""
    
    def test_save_issues_adds_new_issues(self, temp_issues_file, sample_issues):
        """Test that save_issues adds new issues to dictionary and file"""
        issues_dict = IssuesDictionary(temp_issues_file)
        issues_dict.save_issues(sample_issues)
        
        assert len(issues_dict) == 3
        
        # Verify file was updated
        with open(temp_issues_file, 'r') as f:
            data = json.load(f)
            assert len(data) == 3
    
    def test_save_issues_prevents_duplicates(self, temp_issues_file, sample_issues):
        """Test that save_issues doesn't create duplicates"""
        issues_dict = IssuesDictionary(temp_issues_file)
        issues_dict.save_issues(sample_issues)
        issues_dict.save_issues(sample_issues)  # Try to add same issues again
        
        assert len(issues_dict) == 3  # Should still be 3, not 6
    
    def test_save_sorts_by_recency(self, temp_issues_file, sample_issues):
        """Test that save() sorts issues by year, month, issue in descending order"""
        issues_dict = IssuesDictionary(temp_issues_file)
        issues_dict.save_issues(sample_issues)
        
        with open(temp_issues_file, 'r') as f:
            data = json.load(f)
            
            # First should be June (month 6)
            assert data[0]['numerical_month'] == 6
            # Second should be May (month 5)
            assert data[1]['numerical_month'] == 5
            # Last should be January (month 1)
            assert data[2]['numerical_month'] == 1
    
    def test_save_preserves_all_fields(self, temp_issues_file):
        """Test that save() preserves all issue fields"""
        issues_dict = IssuesDictionary(temp_issues_file)
        issue = Issue(
            volume=34, 
            issue=12, 
            month="December", 
            numerical_month=12, 
            year=2026, 
            isnumber="99999999"
        )
        issues_dict.save_issues([issue])
        
        # Reload from file
        with open(temp_issues_file, 'r') as f:
            data = json.load(f)
            saved_issue = data[0]
            
            assert saved_issue['volume'] == 34
            assert saved_issue['issue'] == 12
            assert saved_issue['month'] == "December"
            assert saved_issue['numerical_month'] == 12
            assert saved_issue['year'] == 2026
            assert saved_issue['isnumber'] == "99999999"


class TestIssuesDictionaryQuerying:
    """Test query functionality"""
    
    def test_get_latest_issue_returns_most_recent(self, temp_issues_file, sample_issues):
        """Test that get_latest_issue returns the most recent issue"""
        issues_dict = IssuesDictionary(temp_issues_file)
        issues_dict.save_issues(sample_issues)
        
        latest = issues_dict.get_latest_issue()
        
        assert latest is not None
        assert latest.numerical_month == 6  # June is the latest
        assert latest.year == 2025
    
    def test_get_latest_issue_returns_none_when_empty(self, temp_issues_file):
        """Test that get_latest_issue returns None for empty dictionary"""
        issues_dict = IssuesDictionary(temp_issues_file)
        
        latest = issues_dict.get_latest_issue()
        assert latest is None
    
    def test_get_latest_issue_handles_multiple_years(self, temp_issues_file):
        """Test that get_latest_issue correctly handles multiple years"""
        issues_dict = IssuesDictionary(temp_issues_file)
        issues = [
            Issue(volume=32, issue=12, month="December", numerical_month=12, year=2024, isnumber="10001"),
            Issue(volume=33, issue=1, month="January", numerical_month=1, year=2025, isnumber="10002"),
            Issue(volume=34, issue=1, month="January", numerical_month=1, year=2026, isnumber="10003"),
        ]
        issues_dict.save_issues(issues)
        
        latest = issues_dict.get_latest_issue()
        assert latest.year == 2026
    
    def test_has_issue_returns_true_for_existing(self, temp_issues_file, sample_issues):
        """Test that has_issue returns True for existing isnumber"""
        issues_dict = IssuesDictionary(temp_issues_file)
        issues_dict.save_issues(sample_issues)
        
        assert issues_dict.has_issue("10977652") is True
        assert issues_dict.has_issue("10977653") is True
    
    def test_has_issue_returns_false_for_nonexistent(self, temp_issues_file, sample_issues):
        """Test that has_issue returns False for non-existent isnumber"""
        issues_dict = IssuesDictionary(temp_issues_file)
        issues_dict.save_issues(sample_issues)
        
        assert issues_dict.has_issue("99999999") is False
        assert issues_dict.has_issue("") is False


class TestIssuesDictionaryEdgeCases:
    """Test edge cases and error handling"""
    
    def test_handles_malformed_json_gracefully(self, temp_issues_file, caplog):
        """Test that malformed JSON is handled gracefully"""
        # Write invalid JSON to file
        with open(temp_issues_file, 'w') as f:
            f.write("{ invalid json }")
        
        issues_dict = IssuesDictionary(temp_issues_file)
        
        # Should create empty dictionary and log error
        assert len(issues_dict) == 0
        assert "Malformed JSON" in caplog.text or "error loading issues" in caplog.text.lower()
    
    def test_handles_missing_fields_in_json(self, temp_issues_file, caplog):
        """Test that JSON with missing fields is handled"""
        # Write JSON with missing fields
        with open(temp_issues_file, 'w') as f:
            json.dump([{"volume": 33, "issue": 5}], f)  # Missing required fields
        
        issues_dict = IssuesDictionary(temp_issues_file)
        
        # Should handle error gracefully
        assert len(issues_dict) == 0
        assert "Invalid issue data" in caplog.text or "error" in caplog.text.lower()
    
    def test_handles_invalid_data_types(self, temp_issues_file, caplog):
        """Test that invalid data types are handled"""
        # Write JSON with wrong types
        with open(temp_issues_file, 'w') as f:
            json.dump([{
                "volume": "not a number",
                "issue": 5,
                "month": "May",
                "numerical_month": 5,
                "year": 2025,
                "isnumber": "10977652"
            }], f)
        
        issues_dict = IssuesDictionary(temp_issues_file)
        
        # Should handle error gracefully
        assert len(issues_dict) == 0
        assert "Invalid issue data" in caplog.text or "error" in caplog.text.lower()
    
    def test_large_dataset_performance(self, temp_issues_file):
        """Test that large datasets are handled efficiently"""
        issues_dict = IssuesDictionary(temp_issues_file)
        
        # Create 1000 issues
        large_dataset = []
        for i in range(1000):
            issue = Issue(
                volume=33 + i // 12,
                issue=i % 12 + 1,
                month="January",
                numerical_month=i % 12 + 1,
                year=2020 + i // 12,
                isnumber=f"1000{i:04d}"
            )
            large_dataset.append(issue)
        
        # This should complete quickly
        issues_dict.save_issues(large_dataset)
        
        assert len(issues_dict) == 1000
        assert issues_dict.has_issue("10000000")
        assert issues_dict.has_issue("10000999")
        
        latest = issues_dict.get_latest_issue()
        assert latest is not None


class TestIssuesDictionaryIntegration:
    """Test integration scenarios"""
    
    def test_multiple_saves_accumulate(self, temp_issues_file):
        """Test that multiple save operations accumulate issues"""
        issues_dict = IssuesDictionary(temp_issues_file)
        
        # Save in batches
        batch1 = [Issue(volume=33, issue=1, month="January", numerical_month=1, year=2025, isnumber="10001")]
        batch2 = [Issue(volume=33, issue=2, month="February", numerical_month=2, year=2025, isnumber="10002")]
        batch3 = [Issue(volume=33, issue=3, month="March", numerical_month=3, year=2025, isnumber="10003")]
        
        issues_dict.save_issues(batch1)
        assert len(issues_dict) == 1
        
        issues_dict.save_issues(batch2)
        assert len(issues_dict) == 2
        
        issues_dict.save_issues(batch3)
        assert len(issues_dict) == 3
    
    def test_reload_from_file(self, temp_issues_file, sample_issues):
        """Test that a new instance can reload saved data"""
        # Save with first instance
        issues_dict1 = IssuesDictionary(temp_issues_file)
        issues_dict1.save_issues(sample_issues)
        
        # Load with second instance
        issues_dict2 = IssuesDictionary(temp_issues_file)
        
        assert len(issues_dict2) == 3
        assert issues_dict2.has_issue("10977652")
        
        latest1 = issues_dict1.get_latest_issue()
        latest2 = issues_dict2.get_latest_issue()
        
        # Compare all fields
        assert latest1.volume == latest2.volume
        assert latest1.issue == latest2.issue
        assert latest1.month == latest2.month
        assert latest1.numerical_month == latest2.numerical_month
        assert latest1.year == latest2.year
        assert latest1.isnumber == latest2.isnumber
