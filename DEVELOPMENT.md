# IssueService Development Guide

**Version:** 1.0  
**Last Updated:** January 6, 2026

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Running Locally](#running-locally)
4. [Testing](#testing)
5. [Debugging](#debugging)
6. [Code Structure](#code-structure)
7. [Common Development Tasks](#common-development-tasks)
8. [Contributing](#contributing)

---

## Prerequisites

Before you begin, ensure you have the following installed:

### Required
- **Python 3.9+** ([Download](https://www.python.org/downloads/))
- **Google Chrome** (for Selenium automation)
- **Git** ([Download](https://git-scm.com/downloads))

### Recommended
- **Visual Studio Code** with Python extension
- **Python virtual environment** (venv or conda)

### System Requirements
- **OS**: Windows, macOS, or Linux
- **RAM**: 2GB minimum (4GB recommended for Chrome)
- **Disk**: 500MB for dependencies

---

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/TVLSI/IssueService.git
cd IssueService
```

### 2. Create Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Expected packages:**
- `selenium>=4.9.0` - Browser automation
- `webdriver-manager>=3.8.6` - Automatic ChromeDriver management
- `pytest==8.3.5` - Testing framework
- `pytest-cov>=4.1.0` - Test coverage reporting
- `pytest-timeout>=2.2.0` - Test timeouts
- `pytest-mock>=3.12.0` - Mocking utilities

### 4. Verify Installation

```bash
python --version  # Should show 3.9+
pytest --version  # Should show 8.3.5
```

### 5. Create Data Directory

```bash
mkdir data
```

---

## Running Locally

### Basic Execution

Run the scraper locally without Docker:

```bash
python src/main.py data/issues.json
```

**What happens:**
1. Loads existing `data/issues.json` (or creates if missing)
2. Launches Chrome in headless mode
3. Scrapes IEEE TVLSI website for issues
4. Saves updated `data/issues.json`
5. Prints new issues to console

### With Logging

```bash
# Default INFO level
python src/main.py data/issues.json

# Debug level (more verbose)
python -c "import logging; logging.basicConfig(level=logging.DEBUG)" && python src/main.py data/issues.json
```

### First Run (Empty Database)

```bash
# Create empty JSON file
echo "[]" > data/issues.json

# Run scraper (will process all years)
python src/main.py data/issues.json
```

**Expected output:**
```
2026-01-06 10:30:15 - __main__ - INFO - Starting IssueService...
2026-01-06 10:30:15 - __main__ - INFO - No previous issues found. Processing all years...
2026-01-06 10:30:20 - issue_scraper - INFO - Processing year: 2024
2026-01-06 10:30:25 - issue_scraper - INFO - Found 3 issues for year 2024
...
```

### Subsequent Runs (Incremental)

```bash
# Will only process recent years
python src/main.py data/issues.json
```

---

## Testing

### Run All Tests

```bash
pytest
```

**Expected output:**
```
============================= test session starts =============================
...
tests/test_issue.py ............................ [ 37%]
tests/test_issues_dictionary.py ........... [ 70%]
tests/test_browser_manager.py .......... [ 85%]
tests/test_issue_scraper.py .......... [ 95%]
tests/test_integration.py ....... [100%]

======================== 103 passed in 45.23s =========================
```

### Run Specific Test File

```bash
pytest tests/test_issue.py
pytest tests/test_issue_scraper.py -v  # Verbose output
```

### Run Tests with Coverage

```bash
pytest --cov=src --cov-report=html
```

**View coverage report:**
```bash
# Windows
start htmlcov/index.html

# macOS
open htmlcov/index.html

# Linux
xdg-open htmlcov/index.html
```

### Run Tests with Markers

```bash
# Only unit tests
pytest -m unit

# Only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

### Test Configuration

**File:** `pytest.ini`
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow-running tests
```

---

## Debugging

### Debug in VS Code

**Create `.vscode/launch.json`:**
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Main Script",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/src/main.py",
      "args": ["data/issues.json"],
      "console": "integratedTerminal",
      "justMyCode": true
    },
    {
      "name": "Python: Current Test File",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["${file}", "-v"],
      "console": "integratedTerminal",
      "justMyCode": false
    }
  ]
}
```

**Usage:**
1. Set breakpoints in code
2. Press `F5` to start debugging
3. Use Debug Console for inspection

### Common Debug Scenarios

**1. Inspect Chrome Browser (Non-Headless)**

Edit `src/main.py`:
```python
# Change this line:
browser = BrowserManager(headless=True)

# To:
browser = BrowserManager(headless=False)
```

Run and watch browser automation in real-time.

**2. Logging Level Control**

```python
# In src/main.py, change:
logging.basicConfig(level=logging.INFO, ...)

# To:
logging.basicConfig(level=logging.DEBUG, ...)
```

**3. Breakpoint in Scraper**

```python
# In src/issue_scraper.py
import pdb

def extract_volume_number(self, driver):
    pdb.set_trace()  # Debugger stops here
    # ...
```

**4. Print WebDriver HTML**

```python
# In src/issue_scraper.py
print(driver.page_source)  # Print entire page HTML
```

---

## Code Structure

```
IssueService/
├── .github/
│   └── workflows/
│       └── publish-image.yml    # Docker image build/publish
├── data/
│   ├── issues.json              # Production data (not in repo)
│   └── previous_issues.json     # Sample data for testing
├── src/
│   ├── __init__.py
│   ├── main.py                  # Entry point
│   ├── issue.py                 # Issue data model
│   ├── issues_dictionary.py     # JSON persistence
│   ├── browser_manager.py       # Selenium WebDriver
│   └── issue_scraper.py         # Scraping logic
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures
│   ├── test_issue.py            # Issue class tests (39)
│   ├── test_issues_dictionary.py # Dictionary tests (33)
│   ├── test_browser_manager.py  # Browser tests (21)
│   ├── test_issue_scraper.py    # Scraper tests (30+)
│   ├── test_integration.py      # Integration tests (12)
│   ├── test_main.py             # Main script tests
│   └── test_output_format.py    # Output validation
├── action.yml                   # GitHub Action definition
├── Dockerfile                   # Docker image
├── entrypoint.sh                # Docker entrypoint
├── requirements.txt             # Python dependencies
├── pytest.ini                   # Test configuration
├── README.md                    # User documentation
├── DEVELOPMENT.md               # This file
├── ARCHITECTURE.md              # Technical architecture
├── TESTING.md                   # Test documentation
└── LICENSE                      # MIT License
```

### Module Responsibilities

| Module | Responsibility | Lines of Code |
|--------|----------------|---------------|
| `main.py` | CLI entry, orchestration, outputs | ~110 |
| `issue.py` | Data model (Issue dataclass) | ~50 |
| `issues_dictionary.py` | JSON file I/O, queries | ~100 |
| `browser_manager.py` | WebDriver lifecycle | ~80 |
| `issue_scraper.py` | Web scraping logic | ~250 |

---

## Common Development Tasks

### Task 1: Update CSS Selectors (IEEE Site Change)

**Problem:** Scraper returns 0 issues or crashes with `NoSuchElementException`

**Solution:**
1. Visit https://ieeexplore.ieee.org/xpl/issues?punumber=92
2. Open browser DevTools (F12)
3. Inspect elements (year dropdown, issue links, etc.)
4. Update selectors in `src/issue_scraper.py`:

```python
# Example: If year dropdown ID changes
YEAR_SELECT = "select[name='new-year-id']"  # Update this
```

5. Test locally:
```bash
python src/main.py data/issues.json
```

6. Run tests:
```bash
pytest tests/test_issue_scraper.py
```

7. Commit and push (triggers new Docker image build)

### Task 2: Add New Test

**Example:** Test for missing month in TOC page

1. Create test in `tests/test_issue_scraper.py`:
```python
def test_extract_issue_missing_month(mock_scraper):
    """Test handling of missing month in TOC page"""
    # Setup mock driver with missing month
    # Assert error handling
```

2. Run test:
```bash
pytest tests/test_issue_scraper.py::test_extract_issue_missing_month -v
```

3. If fails, fix code in `src/issue_scraper.py`

### Task 3: Change Wait Times

**Problem:** Scraper too slow or timing out

**Solution:**
1. Edit `src/issue_scraper.py`:
```python
# Reduce waits for faster scraping (risky)
time.sleep(1)  # Was 2

# Or increase for stability
time.sleep(5)  # Was 3
```

2. Test thoroughly to avoid race conditions

### Task 4: Add New Issue Field

**Example:** Add DOI (Digital Object Identifier)

1. Update `src/issue.py`:
```python
@dataclass
class Issue:
    # ... existing fields
    doi: Optional[str] = None  # New field
```

2. Update scraper in `src/issue_scraper.py`:
```python
def extract_issue_from_toc_page(self, ...):
    # ... existing code
    doi = self._extract_doi(driver)  # New method
    
    return Issue(
        # ... existing fields
        doi=doi
    )
```

3. Update tests in `tests/test_issue.py`

4. Update JSON serialization (`to_dict`, `from_dict`)

### Task 5: Run Against Staging/Test Site

**Problem:** Want to test scraper without hitting production IEEE site

**Solution:**
1. Edit `src/main.py`:
```python
# Change constant
ISSUES_URL = "https://test-ieee-site.com/issues"  # Test URL
```

2. Or use environment variable:
```python
ISSUES_URL = os.getenv('IEEE_URL', 'https://ieeexplore.ieee.org/...')
```

3. Run:
```bash
IEEE_URL="https://test-site.com" python src/main.py data/issues.json
```

---

## Building and Testing Docker Image Locally

### Build Image

```bash
docker build -t issueservice:local .
```

### Run Image Locally

```bash
# Create test data directory
mkdir -p test-data
echo "[]" > test-data/issues.json

# Run container
docker run --rm \
  -v "$(pwd)/test-data:/workspace" \
  issueservice:local \
  /workspace/issues.json
```

**Windows (PowerShell):**
```powershell
docker run --rm `
  -v "${PWD}/test-data:/workspace" `
  issueservice:local `
  /workspace/issues.json
```

### Debug Inside Container

```bash
# Start interactive shell
docker run --rm -it issueservice:local /bin/bash

# Inside container:
python src/main.py /tmp/test.json
```

---

## Contributing

### Development Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write code
   - Add tests
   - Update documentation

3. **Run Tests Locally**
   ```bash
   pytest
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: Add feature description"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   # Create Pull Request on GitHub
   ```

### Commit Message Convention

```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `test`: Adding tests
- `refactor`: Code restructuring
- `chore`: Maintenance tasks

**Examples:**
```
feat: Add retry logic for network failures

Implements exponential backoff for IEEE site requests.
Retries up to 3 times before failing.

Closes #42
```

### Code Style

- **PEP 8** compliance (Python style guide)
- **Type hints** preferred but not required
- **Docstrings** for public methods
- **Logging** over print statements
- **Specific exceptions** over generic `Exception`

### Testing Requirements

- All new features require tests
- Maintain >80% code coverage
- Tests must pass before merging
- Include both unit and integration tests

---

## Troubleshooting

### Chrome/ChromeDriver Issues

**Problem:** `WebDriverException: unknown error: cannot find Chrome binary`

**Solution:**
```bash
# Ensure Chrome is installed
# Windows: Check C:\Program Files\Google\Chrome\Application\chrome.exe
# macOS: Check /Applications/Google Chrome.app
# Linux: which google-chrome-stable

# Or install chromium-browser
sudo apt-get install chromium-browser  # Linux
```

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'selenium'`

**Solution:**
```bash
# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\Activate.ps1  # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Permission Errors (Windows)

**Problem:** `PowerShell execution policy prevents activation`

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Test Failures

**Problem:** Tests fail with timeout errors

**Solution:**
```bash
# Increase timeout in pytest.ini
[pytest]
timeout = 300  # 5 minutes

# Or run without timeout
pytest --timeout=0
```

---

## Additional Resources

- **GitHub Actions Documentation**: https://docs.github.com/en/actions
- **Selenium Python Docs**: https://selenium-python.readthedocs.io/
- **pytest Documentation**: https://docs.pytest.org/
- **IEEE Xplore**: https://ieeexplore.ieee.org/

---

## Getting Help

- **Issues**: https://github.com/TVLSI/IssueService/issues
- **Discussions**: https://github.com/TVLSI/IssueService/discussions
- **Email**: (maintainer email if applicable)

---

**Document Version:** 1.0  
**Next Review:** April 2026  
**Maintainer:** TVLSI Organization
