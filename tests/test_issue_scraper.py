"""
Comprehensive tests for IEEEScraper class
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from src.issue_scraper import IEEEScraper
from src.browser_manager import BrowserManager
from src.issues_dictionary import IssuesDictionary
from src.issue import Issue
from selenium.webdriver.common.by import By


@pytest.fixture
def mock_browser():
    """Create a mock browser manager"""
    browser = MagicMock(spec=BrowserManager)
    return browser


@pytest.fixture
def mock_driver():
    """Create a mock Selenium driver"""
    driver = MagicMock()
    return driver


@pytest.fixture
def mock_issues_dict(tmp_path):
    """Create a mock issues dictionary"""
    issues_file = tmp_path / "test_issues.json"
    issues_dict = IssuesDictionary(str(issues_file))
    return issues_dict


@pytest.fixture
def scraper(mock_browser):
    """Create a scraper instance with mocked browser"""
    return IEEEScraper(mock_browser)


class TestIEEEScraperInitialization:
    """Test IEEEScraper initialization"""
    
    def test_init_stores_browser(self, mock_browser):
        """Test that __init__ stores browser manager"""
        scraper = IEEEScraper(mock_browser)
        assert scraper.browser == mock_browser


class TestExtractVolumeNumber:
    """Test extract_volume_number method"""
    
    def test_extract_volume_number_success(self, scraper, mock_driver):
        """Test successful volume number extraction"""
        # Mock the DOM structure
        mock_section = MagicMock()
        mock_div = MagicMock()
        mock_div.text = "Volume 34"
        
        mock_driver.find_element.return_value = mock_section
        mock_section.find_element.return_value = mock_div
        
        volume = scraper.extract_volume_number(mock_driver)
        
        assert volume == 34
    
    def test_extract_volume_number_with_extra_text(self, scraper, mock_driver):
        """Test volume extraction with additional text"""
        mock_section = MagicMock()
        mock_div = MagicMock()
        mock_div.text = "  Volume 33 - Issues  "
        
        mock_driver.find_element.return_value = mock_section
        mock_section.find_element.return_value = mock_div
        
        volume = scraper.extract_volume_number(mock_driver)
        
        assert volume == 33
    
    def test_extract_volume_number_case_insensitive(self, scraper, mock_driver):
        """Test that volume extraction is case-insensitive"""
        mock_section = MagicMock()
        mock_div = MagicMock()
        mock_div.text = "VOLUME 35"
        
        mock_driver.find_element.return_value = mock_section
        mock_section.find_element.return_value = mock_div
        
        volume = scraper.extract_volume_number(mock_driver)
        
        assert volume == 35
    
    def test_extract_volume_number_returns_zero_on_no_match(self, scraper, mock_driver):
        """Test that extraction returns 0 when no volume found"""
        mock_section = MagicMock()
        mock_div = MagicMock()
        mock_div.text = "No volume here"
        
        mock_driver.find_element.return_value = mock_section
        mock_section.find_element.return_value = mock_div
        
        volume = scraper.extract_volume_number(mock_driver)
        
        assert volume == 0


class TestExtractIssueLinks:
    """Test extract_issue_links method"""
    
    def test_extract_issue_links_success(self, scraper, mock_driver):
        """Test successful extraction of issue links"""
        # Mock issue elements
        mock_link1 = MagicMock()
        mock_link1.text = "Issue 1"
        mock_link1.get_attribute.return_value = "https://example.com?isnumber=12345"
        
        mock_link2 = MagicMock()
        mock_link2.text = "Issue 2"
        mock_link2.get_attribute.return_value = "https://example.com?isnumber=12346"
        
        mock_element1 = MagicMock()
        mock_element1.find_element.return_value = mock_link1
        
        mock_element2 = MagicMock()
        mock_element2.find_element.return_value = mock_link2
        
        mock_section = MagicMock()
        mock_section.find_elements.return_value = [mock_element1, mock_element2]
        
        mock_driver.find_element.return_value = mock_section
        
        issue_links = scraper.extract_issue_links(mock_driver)
        
        assert len(issue_links) == 2
        assert issue_links[0] == (1, "12345", "https://example.com?isnumber=12345")
        assert issue_links[1] == (2, "12346", "https://example.com?isnumber=12346")
    
    def test_extract_issue_links_empty_list(self, scraper, mock_driver):
        """Test extraction with no issues found"""
        mock_section = MagicMock()
        mock_section.find_elements.return_value = []
        
        mock_driver.find_element.return_value = mock_section
        
        issue_links = scraper.extract_issue_links(mock_driver)
        
        assert issue_links == []
    
    def test_extract_issue_links_handles_parsing_error(self, scraper, mock_driver):
        """Test that parsing errors are raised"""
        mock_element = MagicMock()
        mock_element.find_element.side_effect = Exception("Element not found")
        
        mock_section = MagicMock()
        mock_section.find_elements.return_value = [mock_element]
        
        mock_driver.find_element.return_value = mock_section
        
        with pytest.raises(Exception):
            scraper.extract_issue_links(mock_driver)


class TestExtractIssueDetails:
    """Test extract_issue_details method"""
    
    def test_extract_issue_details_success(self, scraper, mock_driver):
        """Test successful extraction of issue details"""
        mock_element = MagicMock()
        mock_element.text = "Issue 5 • May - 2025"
        
        mock_driver.find_element.return_value = mock_element
        
        details = scraper.extract_issue_details(mock_driver, 5)
        
        assert details is not None
        assert details['month'] == 'May'
        assert details['numerical_month'] == 5
        assert details['year'] == 2025
    
    def test_extract_issue_details_with_abbreviated_month(self, scraper, mock_driver):
        """Test extraction with abbreviated month name"""
        mock_element = MagicMock()
        mock_element.text = "Issue 12 • Dec. - 2026"
        
        mock_driver.find_element.return_value = mock_element
        
        details = scraper.extract_issue_details(mock_driver, 12)
        
        assert details is not None
        assert details['month'] == 'December'
        assert details['numerical_month'] == 12
        assert details['year'] == 2026
    
    def test_extract_issue_details_wrong_issue_number(self, scraper, mock_driver):
        """Test that None is returned if issue number doesn't match"""
        mock_element = MagicMock()
        mock_element.text = "Issue 6 • June - 2025"
        
        mock_driver.find_element.return_value = mock_element
        
        # Looking for issue 5, but page says issue 6
        details = scraper.extract_issue_details(mock_driver, 5)
        
        assert details is None
    
    def test_extract_issue_details_handles_exception(self, scraper, mock_driver):
        """Test that exceptions during extraction are raised"""
        mock_driver.find_element.side_effect = Exception("Element not found")
        
        with pytest.raises(Exception):
            scraper.extract_issue_details(mock_driver, 5)


class TestGetYears:
    """Test get_years method"""
    
    def test_get_years_success(self, scraper, mock_driver):
        """Test successful extraction of years"""
        mock_elem_2024 = MagicMock()
        mock_elem_2024.text = "2024"
        
        mock_elem_2025 = MagicMock()
        mock_elem_2025.text = "2025"
        
        mock_elem_2026 = MagicMock()
        mock_elem_2026.text = "2026"
        
        mock_driver.find_elements.return_value = [mock_elem_2024, mock_elem_2025, mock_elem_2026]
        
        years = scraper.get_years(mock_driver)
        
        assert years == [2024, 2025, 2026]
    
    def test_get_years_removes_duplicates(self, scraper, mock_driver):
        """Test that duplicate years are removed"""
        elements = [MagicMock(text="2025"), MagicMock(text="2025"), MagicMock(text="2026")]
        mock_driver.find_elements.return_value = elements
        
        years = scraper.get_years(mock_driver)
        
        assert years == [2025, 2026]
    
    def test_get_years_sorted(self, scraper, mock_driver):
        """Test that years are sorted oldest to newest"""
        elements = [MagicMock(text="2026"), MagicMock(text="2024"), MagicMock(text="2025")]
        mock_driver.find_elements.return_value = elements
        
        years = scraper.get_years(mock_driver)
        
        assert years == [2024, 2025, 2026]
    
    def test_get_years_ignores_non_numeric(self, scraper, mock_driver):
        """Test that non-numeric values are ignored"""
        elements = [
            MagicMock(text="2025"),
            MagicMock(text="All Issues"),
            MagicMock(text="2026")
        ]
        mock_driver.find_elements.return_value = elements
        
        years = scraper.get_years(mock_driver)
        
        assert years == [2025, 2026]
    
    def test_get_years_handles_no_elements(self, scraper, mock_driver):
        """Test handling when no year elements found"""
        mock_driver.find_elements.return_value = []
        
        years = scraper.get_years(mock_driver)
        
        assert years == []


class TestDetermineYearsToProcess:
    """Test determine_years_to_process method"""
    
    def test_determine_years_empty_previous_issues(self, scraper, mock_issues_dict):
        """Test that all years are processed when no previous issues"""
        all_years = [2024, 2025, 2026]
        
        years_to_process = scraper.determine_years_to_process(all_years, mock_issues_dict)
        
        assert years_to_process == [2024, 2025, 2026]
    
    def test_determine_years_only_newer_years(self, scraper, mock_issues_dict):
        """Test that only newer years are processed"""
        # Add an issue from May 2025
        issue = Issue(volume=33, issue=5, month="May", numerical_month=5, year=2025, isnumber="12345")
        mock_issues_dict.save_issues([issue])
        
        all_years = [2024, 2025, 2026, 2027]
        years_to_process = scraper.determine_years_to_process(all_years, mock_issues_dict)
        
        # Should include 2025 (not complete) and newer years
        assert 2025 in years_to_process
        assert 2026 in years_to_process
        assert 2027 in years_to_process
        assert 2024 not in years_to_process
    
    def test_determine_years_excludes_complete_year(self, scraper, mock_issues_dict):
        """Test that December excludes that year from processing"""
        # Add an issue from December 2025 (last month)
        issue = Issue(volume=33, issue=12, month="December", numerical_month=12, year=2025, isnumber="12345")
        mock_issues_dict.save_issues([issue])
        
        all_years = [2024, 2025, 2026]
        years_to_process = scraper.determine_years_to_process(all_years, mock_issues_dict)
        
        # Should only include years after 2025
        assert 2025 not in years_to_process
        assert 2026 in years_to_process


class TestSelectYear:
    """Test select_year method"""
    
    @patch('src.issue_scraper.time.sleep')
    def test_select_year_direct_link(self, mock_sleep, scraper, mock_driver):
        """Test selecting year with direct link"""
        mock_link = MagicMock()
        mock_link.text = "2026"
        mock_link.get_attribute.return_value = "https://example.com?isnumber=12345"
        
        mock_driver.find_elements.return_value = [mock_link]
        
        result = scraper.select_year(mock_driver, 2026)
        
        assert result is True
        mock_driver.get.assert_called_once()
    
    @patch('src.issue_scraper.time.sleep')
    def test_select_year_clickable_tab(self, mock_sleep, scraper, mock_driver):
        """Test selecting year with clickable tab"""
        mock_link = MagicMock()
        mock_link.text = "2025"
        
        mock_parent_li = MagicMock()
        mock_parent_li.get_attribute.return_value = ""  # Not active
        mock_link.find_element.return_value = mock_parent_li
        
        # First attempt (direct link) fails, second attempt (clickable) succeeds
        mock_driver.find_elements.side_effect = [[], ]
        mock_driver.find_element.return_value = mock_link
        
        result = scraper.select_year(mock_driver, 2025)
        
        assert result is True
        mock_link.click.assert_called_once()
    
    def test_select_year_not_found(self, scraper, mock_driver):
        """Test behavior when year is not found"""
        mock_driver.find_elements.return_value = []
        mock_driver.find_element.side_effect = Exception("Element not found")
        
        result = scraper.select_year(mock_driver, 2099)
        
        assert result is False


class TestProcessIssue:
    """Test process_issue method"""
    
    def test_process_issue_success(self, scraper, mock_browser, mock_driver):
        """Test successful issue processing"""
        mock_browser.navigate.return_value = mock_driver
        
        # Mock extract_issue_details
        with patch.object(scraper, 'extract_issue_details') as mock_extract:
            mock_extract.return_value = {
                'month': 'May',
                'numerical_month': 5,
                'year': 2025
            }
            
            issue = scraper.process_issue(5, "12345", "https://example.com", 33)
            
            assert issue is not None
            assert issue.volume == 33
            assert issue.issue == 5
            assert issue.month == 'May'
            assert issue.numerical_month == 5
            assert issue.year == 2025
            assert issue.isnumber == "12345"
    
    def test_process_issue_no_details(self, scraper, mock_browser, mock_driver):
        """Test issue processing when details extraction fails"""
        mock_browser.navigate.return_value = mock_driver
        
        with patch.object(scraper, 'extract_issue_details') as mock_extract:
            mock_extract.return_value = None
            
            issue = scraper.process_issue(5, "12345", "https://example.com", 33)
            
            assert issue is None


class TestExtractIssueFromTocPage:
    """Test extract_issue_from_toc_page method"""
    
    @patch('src.issue_scraper.time.sleep')
    def test_extract_from_toc_page_success(self, mock_sleep, scraper, mock_driver):
        """Test successful extraction from TOC page"""
        # Mock URL
        type(mock_driver).current_url = PropertyMock(
            return_value="https://example.com/tocresult.jsp?isnumber=12345"
        )
        
        # Mock description elements
        mock_div = MagicMock()
        mock_div.get_attribute.return_value = "Year: 2026 | Volume: 34 | Issue: 1"
        
        mock_desc = MagicMock()
        mock_desc.find_elements.return_value = [MagicMock(), mock_div]
        
        mock_driver.find_elements.return_value = [mock_desc]
        
        result = scraper.extract_issue_from_toc_page(mock_driver)
        
        assert result is not None
        assert result['year'] == 2026
        assert result['volume'] == 34
        assert result['issue'] == 1
        assert result['month'] == 'January'
        assert result['numerical_month'] == 1
        assert result['isnumber'] == '12345'
    
    def test_extract_from_toc_page_not_toc_url(self, scraper, mock_driver):
        """Test that None is returned for non-TOC URLs"""
        type(mock_driver).current_url = PropertyMock(
            return_value="https://example.com/other-page"
        )
        
        result = scraper.extract_issue_from_toc_page(mock_driver)
        
        assert result is None
    
    def test_extract_from_toc_page_no_isnumber(self, scraper, mock_driver):
        """Test that None is returned when no isnumber in URL"""
        type(mock_driver).current_url = PropertyMock(
            return_value="https://example.com/tocresult.jsp"
        )
        
        result = scraper.extract_issue_from_toc_page(mock_driver)
        
        assert result is None


class TestIntegrationScenarios:
    """Test integration scenarios"""
    
    @patch('src.issue_scraper.time.sleep')
    def test_process_year_with_toc_page(self, mock_sleep, scraper, mock_browser, mock_driver, mock_issues_dict):
        """Test processing a year that redirects to TOC page"""
        mock_browser.navigate.return_value = mock_driver
        
        with patch.object(scraper, 'select_year') as mock_select, \
             patch.object(scraper, 'extract_issue_from_toc_page') as mock_toc:
            
            mock_select.return_value = True
            mock_toc.return_value = {
                'year': 2026,
                'volume': 34,
                'issue': 1,
                'month': 'January',
                'numerical_month': 1,
                'isnumber': '12345'
            }
            
            issues = scraper.process_year(mock_driver, "https://example.com", 2026, mock_issues_dict)
            
            assert len(issues) == 1
            assert issues[0].year == 2026
            assert issues[0].volume == 34
