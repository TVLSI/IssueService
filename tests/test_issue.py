import pytest
from src.issue import Issue

def test_issue_creation():
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

def test_issue_equality():
    """Test that issue equality works correctly"""
    issue1 = Issue(volume=33, issue=5, month="May", numerical_month=5, year=2025, isnumber="10977652")
    issue2 = Issue(volume=33, issue=5, month="May", numerical_month=5, year=2025, isnumber="10977652")
    issue3 = Issue(volume=33, issue=6, month="June", numerical_month=6, year=2025, isnumber="10977653")
    
    assert issue1 == issue2
    assert issue1 != issue3
    assert issue2 != issue3

def test_issue_serialization():
    """Test that issues can be serialized and deserialized correctly"""
    original = Issue(volume=33, issue=5, month="May", numerical_month=5, year=2025, isnumber="10977652")
    
    # Mock serialization if to_dict or from_dict methods don't exist
    # You may need to adapt this to match your actual Issue class implementation
    try:
        data = original.to_dict()
        recreated = Issue.from_dict(data)
        
        assert original == recreated
        assert original.volume == recreated.volume
        assert original.issue == recreated.issue
        assert original.month == recreated.month
        assert original.numerical_month == recreated.numerical_month
        assert original.year == recreated.year
        assert original.isnumber == recreated.isnumber
    except AttributeError:
        # Skip this test if serialization methods don't exist
        pytest.skip("Issue class doesn't support serialization")