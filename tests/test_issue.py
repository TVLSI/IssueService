"""
Comprehensive tests for Issue class
"""
import pytest
from src.issue import Issue


class TestIssueCreation:
    """Test Issue creation and initialization"""
    
    def test_issue_creation_with_all_fields(self):
        """Test that an Issue can be created with expected values"""
        issue = Issue(
            volume=33,
            issue=5,
            month="May",
            numerical_month=5,
            year=2025,
            isnumber="10977652"
        )
        
        assert issue.volume == 33
        assert issue.issue == 5
        assert issue.month == "May"
        assert issue.numerical_month == 5
        assert issue.year == 2025
        assert issue.isnumber == "10977652"
    
    def test_issue_creation_with_different_months(self):
        """Test issue creation with various month values"""
        months = [
            ("January", 1), ("February", 2), ("March", 3),
            ("April", 4), ("May", 5), ("June", 6),
            ("July", 7), ("August", 8), ("September", 9),
            ("October", 10), ("November", 11), ("December", 12)
        ]
        
        for month_name, month_num in months:
            issue = Issue(
                volume=33, issue=month_num, month=month_name,
                numerical_month=month_num, year=2025, isnumber=f"1000{month_num}"
            )
            assert issue.month == month_name
            assert issue.numerical_month == month_num


class TestIssueEquality:
    """Test Issue equality and comparison"""
    
    def test_issue_equality_same_values(self):
        """Test that issues with same volume/issue/year are equal"""
        issue1 = Issue(volume=33, issue=5, month="May", numerical_month=5, year=2025, isnumber="10977652")
        issue2 = Issue(volume=33, issue=5, month="May", numerical_month=5, year=2025, isnumber="10977652")
        
        assert issue1 == issue2
    
    def test_issue_equality_different_isnumber_still_equal(self):
        """Test that equality is based on volume/issue/year, not isnumber"""
        issue1 = Issue(volume=33, issue=5, month="May", numerical_month=5, year=2025, isnumber="10977652")
        issue2 = Issue(volume=33, issue=5, month="May", numerical_month=5, year=2025, isnumber="99999999")
        
        # Issues with same volume/issue/year are equal regardless of isnumber
        assert issue1 == issue2
    
    def test_issue_inequality_different_issue(self):
        """Test that issues with different issue numbers are not equal"""
        issue1 = Issue(volume=33, issue=5, month="May", numerical_month=5, year=2025, isnumber="10977652")
        issue2 = Issue(volume=33, issue=6, month="June", numerical_month=6, year=2025, isnumber="10977653")
        
        assert issue1 != issue2
    
    def test_issue_inequality_different_volume(self):
        """Test that issues with different volumes are not equal"""
        issue1 = Issue(volume=33, issue=5, month="May", numerical_month=5, year=2025, isnumber="10977652")
        issue2 = Issue(volume=34, issue=5, month="May", numerical_month=5, year=2025, isnumber="10977652")
        
        assert issue1 != issue2
    
    def test_issue_inequality_different_year(self):
        """Test that issues with different years are not equal"""
        issue1 = Issue(volume=33, issue=5, month="May", numerical_month=5, year=2025, isnumber="10977652")
        issue2 = Issue(volume=33, issue=5, month="May", numerical_month=5, year=2026, isnumber="10977652")
        
        assert issue1 != issue2
    
    def test_issue_equality_with_non_issue_object(self):
        """Test that comparing with non-Issue object returns False"""
        issue = Issue(volume=33, issue=5, month="May", numerical_month=5, year=2025, isnumber="10977652")
        
        assert issue != "not an issue"
        assert issue != 12345
        assert issue != None
        assert issue != {"volume": 33, "issue": 5}


class TestIssueComparison:
    """Test Issue less-than comparison for sorting"""
    
    def test_issue_comparison_by_year(self):
        """Test that issues are compared by year first"""
        issue_2024 = Issue(volume=32, issue=1, month="January", numerical_month=1, year=2024, isnumber="10001")
        issue_2025 = Issue(volume=33, issue=1, month="January", numerical_month=1, year=2025, isnumber="10002")
        
        assert issue_2024 < issue_2025
        assert not (issue_2025 < issue_2024)
    
    def test_issue_comparison_by_volume(self):
        """Test that issues are compared by volume when years are equal"""
        issue_vol32 = Issue(volume=32, issue=1, month="January", numerical_month=1, year=2025, isnumber="10001")
        issue_vol33 = Issue(volume=33, issue=1, month="January", numerical_month=1, year=2025, isnumber="10002")
        
        assert issue_vol32 < issue_vol33
    
    def test_issue_comparison_by_month(self):
        """Test that issues are compared by month when year/volume are equal"""
        issue_jan = Issue(volume=33, issue=1, month="January", numerical_month=1, year=2025, isnumber="10001")
        issue_feb = Issue(volume=33, issue=2, month="February", numerical_month=2, year=2025, isnumber="10002")
        
        assert issue_jan < issue_feb
    
    def test_issue_comparison_by_issue_number(self):
        """Test that issues are compared by issue number last"""
        issue1 = Issue(volume=33, issue=1, month="January", numerical_month=1, year=2025, isnumber="10001")
        issue2 = Issue(volume=33, issue=2, month="January", numerical_month=1, year=2025, isnumber="10002")
        
        assert issue1 < issue2
    
    def test_issue_sorting(self):
        """Test that a list of issues can be sorted correctly"""
        issues = [
            Issue(volume=33, issue=6, month="June", numerical_month=6, year=2025, isnumber="10003"),
            Issue(volume=33, issue=1, month="January", numerical_month=1, year=2025, isnumber="10001"),
            Issue(volume=32, issue=12, month="December", numerical_month=12, year=2024, isnumber="10000"),
            Issue(volume=34, issue=1, month="January", numerical_month=1, year=2026, isnumber="10004"),
        ]
        
        sorted_issues = sorted(issues)
        
        assert sorted_issues[0].year == 2024
        assert sorted_issues[1].numerical_month == 1
        assert sorted_issues[2].numerical_month == 6
        assert sorted_issues[3].year == 2026
    
    def test_issue_comparison_with_non_issue_raises_error(self):
        """Test that comparing with non-Issue raises TypeError"""
        issue = Issue(volume=33, issue=5, month="May", numerical_month=5, year=2025, isnumber="10977652")
        
        with pytest.raises(TypeError):
            _ = issue < "not an issue"


class TestIssueSerialization:
    """Test Issue serialization and deserialization"""
    
    def test_to_dict_contains_all_fields(self):
        """Test that to_dict() includes all issue fields"""
        issue = Issue(volume=33, issue=5, month="May", numerical_month=5, year=2025, isnumber="10977652")
        data = issue.to_dict()
        
        assert data['volume'] == 33
        assert data['issue'] == 5
        assert data['month'] == "May"
        assert data['numerical_month'] == 5
        assert data['year'] == 2025
        assert data['isnumber'] == "10977652"
        assert len(data) == 6  # Ensure no extra fields
    
    def test_from_dict_recreates_issue(self):
        """Test that from_dict() correctly recreates an Issue"""
        original = Issue(volume=33, issue=5, month="May", numerical_month=5, year=2025, isnumber="10977652")
        data = original.to_dict()
        recreated = Issue.from_dict(data)
        
        assert recreated == original
        assert recreated.volume == original.volume
        assert recreated.issue == original.issue
        assert recreated.month == original.month
        assert recreated.numerical_month == original.numerical_month
        assert recreated.year == original.year
        assert recreated.isnumber == original.isnumber
    
    def test_serialization_round_trip(self):
        """Test that serialize -> deserialize preserves all data"""
        original = Issue(volume=34, issue=12, month="December", numerical_month=12, year=2026, isnumber="99999999")
        
        # Round trip
        data = original.to_dict()
        recreated = Issue.from_dict(data)
        data_again = recreated.to_dict()
        
        assert data == data_again
    
    def test_from_dict_with_string_numbers(self):
        """Test that from_dict handles string numbers correctly"""
        data = {
            'volume': "33",
            'issue': "5",
            'month': "May",
            'numerical_month': "5",
            'year': "2025",
            'isnumber': "10977652"
        }
        
        issue = Issue.from_dict(data)
        
        assert issue.volume == 33
        assert issue.issue == 5
        assert issue.numerical_month == 5
        assert issue.year == 2025


class TestIssueEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_issue_with_large_numbers(self):
        """Test that large volume/issue/year numbers are handled"""
        issue = Issue(
            volume=999,
            issue=999,
            month="December",
            numerical_month=12,
            year=9999,
            isnumber="99999999999"
        )
        
        assert issue.volume == 999
        assert issue.year == 9999
    
    def test_issue_with_long_month_name(self):
        """Test that month names are stored correctly"""
        issue = Issue(
            volume=33,
            issue=9,
            month="September",
            numerical_month=9,
            year=2025,
            isnumber="10977652"
        )
        
        assert issue.month == "September"
        assert len(issue.month) == 9
    
    def test_issue_isnumber_as_string(self):
        """Test that isnumber is treated as a string"""
        issue = Issue(
            volume=33,
            issue=5,
            month="May",
            numerical_month=5,
            year=2025,
            isnumber="00012345"  # Leading zeros should be preserved
        )
        
        assert issue.isnumber == "00012345"
        assert isinstance(issue.isnumber, str)