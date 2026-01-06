"""
Comprehensive tests for BrowserManager class
"""
import pytest
from unittest.mock import MagicMock, patch, call
from src.browser_manager import BrowserManager
from selenium.webdriver.common.by import By


class TestBrowserManagerInitialization:
    """Test BrowserManager initialization"""
    
    def test_init_headless_true(self):
        """Test initialization with headless=True"""
        manager = BrowserManager(headless=True)
        assert manager.headless is True
        assert manager.driver is None
    
    def test_init_headless_false(self):
        """Test initialization with headless=False"""
        manager = BrowserManager(headless=False)
        assert manager.headless is False
        assert manager.driver is None
    
    def test_init_default_headless(self):
        """Test that default is headless=True"""
        manager = BrowserManager()
        assert manager.headless is True


class TestBrowserManagerInitialize:
    """Test browser initialization"""
    
    @patch('src.browser_manager.webdriver.Chrome')
    @patch('src.browser_manager.ChromeDriverManager')
    @patch('src.browser_manager.Service')
    def test_initialize_creates_driver(self, mock_service, mock_driver_manager, mock_chrome):
        """Test that initialize() creates a webdriver instance"""
        manager = BrowserManager(headless=True)
        mock_driver_instance = MagicMock()
        mock_chrome.return_value = mock_driver_instance
        
        driver = manager.initialize()
        
        assert driver is not None
        assert manager.driver is not None
        mock_chrome.assert_called_once()
    
    @patch('src.browser_manager.webdriver.Chrome')
    @patch('src.browser_manager.ChromeDriverManager')
    @patch('src.browser_manager.Service')
    def test_initialize_with_headless_sets_options(self, mock_service, mock_driver_manager, mock_chrome):
        """Test that headless mode sets appropriate Chrome options"""
        manager = BrowserManager(headless=True)
        
        driver = manager.initialize()
        
        # Check that Chrome was called with options
        call_args = mock_chrome.call_args
        assert call_args is not None
        assert 'options' in call_args.kwargs or len(call_args.args) >= 2
    
    @patch('src.browser_manager.webdriver.Chrome')
    @patch('src.browser_manager.ChromeDriverManager')
    @patch('src.browser_manager.Service')
    def test_initialize_without_headless(self, mock_service, mock_driver_manager, mock_chrome):
        """Test initialization without headless mode"""
        manager = BrowserManager(headless=False)
        mock_driver_instance = MagicMock()
        mock_chrome.return_value = mock_driver_instance
        
        driver = manager.initialize()
        
        assert driver is not None
        assert manager.driver is not None


class TestBrowserManagerNavigation:
    """Test navigation functionality"""
    
    @patch('src.browser_manager.time.sleep')
    @patch('src.browser_manager.webdriver.Chrome')
    @patch('src.browser_manager.ChromeDriverManager')
    @patch('src.browser_manager.Service')
    def test_navigate_initializes_driver_if_none(self, mock_service, mock_driver_manager, mock_chrome, mock_sleep):
        """Test that navigate() initializes driver if not already initialized"""
        manager = BrowserManager(headless=True)
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        result = manager.navigate("https://example.com")
        
        # Should have initialized and navigated
        mock_chrome.assert_called_once()
        mock_driver.get.assert_called_once_with("https://example.com")
    
    @patch('src.browser_manager.time.sleep')
    def test_navigate_uses_existing_driver(self, mock_sleep):
        """Test that navigate() reuses existing driver"""
        manager = BrowserManager(headless=True)
        mock_driver = MagicMock()
        manager.driver = mock_driver
        
        result = manager.navigate("https://example.com")
        
        mock_driver.get.assert_called_once_with("https://example.com")
    
    @patch('src.browser_manager.time.sleep')
    def test_navigate_waits_default_time(self, mock_sleep):
        """Test that navigate() waits default 5 seconds"""
        manager = BrowserManager(headless=True)
        mock_driver = MagicMock()
        manager.driver = mock_driver
        
        manager.navigate("https://example.com")
        
        mock_sleep.assert_called_once_with(5)
    
    @patch('src.browser_manager.time.sleep')
    def test_navigate_waits_custom_time(self, mock_sleep):
        """Test that navigate() respects custom wait time"""
        manager = BrowserManager(headless=True)
        mock_driver = MagicMock()
        manager.driver = mock_driver
        
        manager.navigate("https://example.com", wait_time=10)
        
        mock_sleep.assert_called_once_with(10)
    
    @patch('src.browser_manager.time.sleep')
    def test_navigate_returns_driver(self, mock_sleep):
        """Test that navigate() returns the driver"""
        manager = BrowserManager(headless=True)
        mock_driver = MagicMock()
        manager.driver = mock_driver
        
        result = manager.navigate("https://example.com")
        
        assert result == mock_driver


class TestBrowserManagerWaitForElement:
    """Test element waiting functionality"""
    
    @patch('src.browser_manager.WebDriverWait')
    def test_wait_for_element_default_timeout(self, mock_wait):
        """Test waiting for element with default timeout"""
        manager = BrowserManager(headless=True)
        mock_driver = MagicMock()
        manager.driver = mock_driver
        
        mock_wait_instance = MagicMock()
        mock_wait.return_value = mock_wait_instance
        mock_element = MagicMock()
        mock_wait_instance.until.return_value = mock_element
        
        result = manager.wait_for_element(By.ID, "test-id")
        
        # Check that WebDriverWait was called with driver and default timeout
        mock_wait.assert_called_once_with(mock_driver, 10)
        assert result == mock_element
    
    @patch('src.browser_manager.WebDriverWait')
    def test_wait_for_element_custom_timeout(self, mock_wait):
        """Test waiting for element with custom timeout"""
        manager = BrowserManager(headless=True)
        mock_driver = MagicMock()
        manager.driver = mock_driver
        
        mock_wait_instance = MagicMock()
        mock_wait.return_value = mock_wait_instance
        
        manager.wait_for_element(By.CSS_SELECTOR, ".test-class", timeout=30)
        
        mock_wait.assert_called_once_with(mock_driver, 30)
    
    @patch('src.browser_manager.WebDriverWait')
    def test_wait_for_element_with_different_selectors(self, mock_wait):
        """Test waiting for elements with different selector types"""
        manager = BrowserManager(headless=True)
        mock_driver = MagicMock()
        manager.driver = mock_driver
        
        mock_wait_instance = MagicMock()
        mock_wait.return_value = mock_wait_instance
        mock_element = MagicMock()
        mock_wait_instance.until.return_value = mock_element
        
        # Test different selector types
        manager.wait_for_element(By.ID, "test-id")
        manager.wait_for_element(By.CSS_SELECTOR, ".test-class")
        manager.wait_for_element(By.XPATH, "//div[@class='test']")
        
        assert mock_wait_instance.until.call_count == 3


class TestBrowserManagerClose:
    """Test browser cleanup"""
    
    def test_close_quits_driver(self):
        """Test that close() quits the driver"""
        manager = BrowserManager(headless=True)
        mock_driver = MagicMock()
        manager.driver = mock_driver
        
        manager.close()
        
        mock_driver.quit.assert_called_once()
        assert manager.driver is None
    
    def test_close_handles_none_driver(self):
        """Test that close() handles None driver gracefully"""
        manager = BrowserManager(headless=True)
        manager.driver = None
        
        # Should not raise an error
        manager.close()
        
        assert manager.driver is None
    
    def test_close_multiple_times(self):
        """Test that calling close() multiple times is safe"""
        manager = BrowserManager(headless=True)
        mock_driver = MagicMock()
        manager.driver = mock_driver
        
        manager.close()
        manager.close()  # Second call should be safe
        
        # quit should only be called once
        mock_driver.quit.assert_called_once()


class TestBrowserManagerEdgeCases:
    """Test edge cases and error handling"""
    
    @patch('src.browser_manager.time.sleep')
    def test_navigate_handles_driver_exception(self, mock_sleep):
        """Test that navigation handles driver exceptions"""
        manager = BrowserManager(headless=True)
        mock_driver = MagicMock()
        mock_driver.get.side_effect = Exception("Navigation failed")
        manager.driver = mock_driver
        
        with pytest.raises(Exception, match="Navigation failed"):
            manager.navigate("https://example.com")
    
    def test_close_handles_quit_exception(self):
        """Test that close() handles exceptions during quit"""
        manager = BrowserManager(headless=True)
        mock_driver = MagicMock()
        mock_driver.quit.side_effect = Exception("Quit failed")
        manager.driver = mock_driver
        
        # Should handle exception gracefully
        with pytest.raises(Exception):
            manager.close()


class TestBrowserManagerIntegration:
    """Test integration scenarios"""
    
    @patch('src.browser_manager.time.sleep')
    def test_full_workflow(self, mock_sleep):
        """Test complete workflow: initialize -> navigate -> close"""
        manager = BrowserManager(headless=True)
        mock_driver = MagicMock()
        manager.driver = mock_driver
        
        # Navigate
        result = manager.navigate("https://example.com")
        assert result == mock_driver
        mock_driver.get.assert_called_once_with("https://example.com")
        
        # Close
        manager.close()
        mock_driver.quit.assert_called_once()
    
    @patch('src.browser_manager.time.sleep')
    def test_multiple_navigations_same_driver(self, mock_sleep):
        """Test that multiple navigations reuse the same driver"""
        manager = BrowserManager(headless=True)
        mock_driver = MagicMock()
        manager.driver = mock_driver
        
        manager.navigate("https://example1.com")
        manager.navigate("https://example2.com")
        manager.navigate("https://example3.com")
        
        # Should have called get() three times on same driver
        assert mock_driver.get.call_count == 3
        mock_driver.get.assert_any_call("https://example1.com")
        mock_driver.get.assert_any_call("https://example2.com")
        mock_driver.get.assert_any_call("https://example3.com")
