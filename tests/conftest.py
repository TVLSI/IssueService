import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Add the src directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Use broader patching to prevent all browser operations
@pytest.fixture(autouse=True)
def mock_all_browsers(monkeypatch):
    """Mock all browser and selenium related components"""
    # Create a completely fake driver that does nothing
    mock_driver = MagicMock()
    mock_driver.find_element.return_value = MagicMock()
    mock_driver.find_elements.return_value = []
    
    # Mock the browser manager
    class MockBrowserManager:
        def __init__(self, *args, **kwargs):
            pass
        
        def navigate(self, *args, **kwargs):
            return mock_driver
            
        def close(self):
            pass
    
    # Apply mocks before any test runs
    monkeypatch.setattr('src.browser_manager.BrowserManager', MockBrowserManager)
    
    # Also mock selenium directly if it's imported elsewhere
    monkeypatch.setattr('selenium.webdriver.Chrome', MagicMock())
    monkeypatch.setattr('selenium.webdriver.edge.service.Service', MagicMock())
    
    # Block any import that might try to load real browser components
    import builtins
    real_import = builtins.__import__
    
    def mock_import(name, *args, **kwargs):
        if name in ['selenium', 'webdriver', 'chrome', 'edge', 'tensorflow']:
            if name == 'selenium':
                mock_module = MagicMock()
                mock_module.webdriver = MagicMock()
                return mock_module
            return MagicMock()
        return real_import(name, *args, **kwargs)
    
    monkeypatch.setattr(builtins, '__import__', mock_import)