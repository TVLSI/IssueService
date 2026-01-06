# IssueService Architecture

**Version:** 1.0  
**Last Updated:** January 6, 2026

---

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Data Flow](#data-flow)
4. [Component Details](#component-details)
5. [Docker Image Strategy](#docker-image-strategy)
6. [Scraping Strategy](#scraping-strategy)
7. [Error Handling](#error-handling)
8. [Performance Considerations](#performance-considerations)

---

## Overview

IssueService is a specialized GitHub Action designed to automatically scrape and track IEEE TVLSI (Transactions on Very Large Scale Integration) journal issues. It maintains a persistent JSON database of all issues, enabling downstream workflows to detect and process new publications.

### Design Principles
- **Single Responsibility**: Focused exclusively on IEEE TVLSI journal scraping
- **Idempotency**: Safe to run multiple times without duplicating data
- **Failure Transparency**: Comprehensive logging and error reporting
- **Efficiency**: Pre-built Docker images for fast execution

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Actions Workflow                  │
│                   (Consumer: TVLSI/website-data)            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    IssueService Action                       │
│                  (Docker Container)                          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  main.py (Entry Point)                                │  │
│  │  • Parse CLI arguments                                │  │
│  │  • Initialize components                              │  │
│  │  • Orchestrate scraping                               │  │
│  │  • Write GitHub Action outputs                        │  │
│  └──────────┬──────────────────────────────┬─────────────┘  │
│             │                              │                 │
│             ▼                              ▼                 │
│  ┌─────────────────────┐      ┌──────────────────────────┐  │
│  │ IssuesDictionary    │      │   BrowserManager         │  │
│  │                     │      │                          │  │
│  │ • Load JSON         │      │ • Selenium WebDriver     │  │
│  │ • Query issues      │      │ • Chrome automation      │  │
│  │ • Save JSON         │      │ • Wait strategies        │  │
│  │ • Deduplication     │      │ • Cleanup                │  │
│  └─────────────────────┘      └──────────┬───────────────┘  │
│             ▲                              │                 │
│             │                              ▼                 │
│             │                  ┌──────────────────────────┐  │
│             │                  │   IEEEScraper            │  │
│             │                  │                          │  │
│             │                  │ • Year navigation        │  │
│             │                  │ • Volume extraction      │  │
│             │                  │ • Issue link extraction  │  │
│             │                  │ • TOC page parsing       │  │
│             │                  │ • Issue metadata build   │  │
│             └──────────────────┴──────────────────────────┘  │
│                                                               │
│  Input: issues.json (existing data)                          │
│  Output: issues.json (updated), new_issues (JSON array)      │
└───────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  GitHub Container Registry                   │
│                ghcr.io/tvlsi/issueservice:latest            │
│                                                              │
│  • Pre-built Docker image (monthly updates)                 │
│  • Python 3.9-slim + Chrome + Selenium                      │
│  • ~300MB compressed                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### 1. Initialization Phase
```
GitHub Action Trigger
  ↓
Load action.yml inputs (issues_file path)
  ↓
Pull pre-built Docker image from GHCR
  ↓
Execute entrypoint.sh
  ↓
Run main.py with issues_file argument
```

### 2. Scraping Phase
```
main.py starts
  ↓
IssuesDictionary loads existing issues.json
  ↓
Determine latest issue (year, month)
  ↓
BrowserManager launches Chrome (headless)
  ↓
IEEEScraper navigates to IEEE TVLSI issues page
  ↓
For each year to process:
  ├─ Select year from dropdown
  ├─ Extract volume number
  ├─ Find all issue links
  ├─ For each issue link:
  │   ├─ Navigate to TOC (Table of Contents) page
  │   ├─ Extract metadata (issue #, month, isnumber)
  │   └─ Build Issue object
  └─ Add to new_issues list
  ↓
IssuesDictionary merges new issues (deduplicates)
  ↓
Save updated issues.json
```

### 3. Output Phase
```
Calculate new_issues_count
  ↓
Serialize new_issues to JSON
  ↓
Write GitHub Action outputs:
  • new_issues_count
  • new_issues
  • has_new_issues (boolean)
  ↓
Consumer workflow reads outputs
  ↓
Consumer commits updated issues.json
```

---

## Component Details

### main.py (Entry Point)
**Responsibilities:**
- Command-line argument parsing
- Component initialization
- Error handling and logging setup
- GitHub Action output writing

**Key Functions:**
- `main()`: Orchestrates entire workflow
- Configures logging infrastructure
- Handles file path resolution (GitHub Action vs local mode)

**Exit Codes:**
- `0`: Success
- `1`: Initialization failure, scraping error, or output writing failure

---

### IssuesDictionary (Data Persistence)
**File:** `src/issues_dictionary.py`

**Responsibilities:**
- Load/save JSON file
- Query operations (get all, get latest)
- Deduplication of issues
- Sorting by chronological order

**Key Methods:**
```python
__init__(filename: str)           # Load existing JSON
get_all_issues() -> List[Issue]   # Return all issues
get_latest_issue() -> Optional[Issue]  # Find most recent
add_issue(issue: Issue)           # Add with dedup
save()                            # Persist to disk
```

**Data Format (issues.json):**
```json
[
  {
    "volume": 32,
    "issue": 1,
    "month": "January",
    "numerical_month": 1,
    "year": 2024,
    "isnumber": "10379819"
  }
]
```

**Error Handling:**
- `JSONDecodeError`: Corrupted/invalid JSON
- `IOError`: File read/write failures
- `KeyError`: Missing required fields

---

### BrowserManager (Browser Automation)
**File:** `src/browser_manager.py`

**Responsibilities:**
- Selenium WebDriver lifecycle management
- Chrome browser configuration (headless mode)
- Wait strategies for page loads
- Resource cleanup

**Key Methods:**
```python
__init__(headless: bool = True)   # Create WebDriver
get_driver() -> WebDriver         # Access driver
wait_for_page_load(timeout: int)  # Explicit waits
close()                           # Cleanup
```

**Configuration:**
- Headless mode (no GUI)
- Automatic ChromeDriver management (webdriver-manager)
- Timeouts: 10s default wait

---

### IEEEScraper (Scraping Logic)
**File:** `src/issue_scraper.py`

**Responsibilities:**
- Navigate IEEE TVLSI website
- Extract volume numbers, issue links
- Parse Table of Contents (TOC) pages
- Build Issue objects

**Key Methods:**
```python
get_issues(url: str, previous_issues: IssuesDictionary) -> List[Issue]
  └─ determine_years_to_process() -> List[int]
  └─ process_year(year: int) -> List[Issue]
      ├─ select_year(year: int) -> bool
      ├─ extract_volume_number() -> int
      ├─ extract_issue_links() -> List[str]
      └─ extract_issue_from_toc_page(link: str, volume: int, year: int) -> Issue
```

**Scraping Strategy:**
1. Load main issues page with hardcoded URL
2. Determine which years to process (since last run or all years)
3. For each year:
   - Select year from dropdown menu
   - Extract volume number from page
   - Find all issue links (table rows with .clickable-row)
   - Visit each issue's TOC page
   - Parse metadata from URL parameters and page content
4. Return list of Issue objects

**CSS Selectors (Fragile Points):**
```python
"select[name='year-select']"           # Year dropdown
"section[class*='issue-container']"    # Volume section
"tr.clickable-row"                     # Issue links
```

**Wait Times:**
- 2s after year selection
- 3s after TOC page load
- 5s for initial page load

---

### Issue (Data Model)
**File:** `src/issue.py`

**Schema:**
```python
@dataclass
class Issue:
    volume: int           # Volume number (e.g., 32)
    issue: int            # Issue number (e.g., 1)
    month: str            # Month name (e.g., "January")
    numerical_month: int  # Month as number (1-12)
    year: int             # Publication year (e.g., 2024)
    isnumber: str         # IEEE identifier (e.g., "10379819")
```

**Methods:**
- `from_dict()`: JSON deserialization
- `to_dict()`: JSON serialization
- `__eq__()`: Equality comparison (volume, issue, year)
- `__lt__()`: Chronological sorting

---

## Docker Image Strategy

### Build & Distribution
**Workflow:** `.github/workflows/publish-image.yml`

**Trigger Schedule:**
- **Monthly**: 1st of every month at midnight UTC
- **On Changes**: Dockerfile, requirements.txt, entrypoint.sh
- **Manual**: workflow_dispatch

**Registry:** GitHub Container Registry (GHCR)
- Public repository: `ghcr.io/tvlsi/issueservice:latest`
- Additional tags: `YYYY-MM`, `YYYY-MM-<sha>`

**Benefits:**
- ✅ **Fast action runs**: No 5-10 minute Docker build
- ✅ **Consistent environment**: Same image for all runs
- ✅ **Layer caching**: Efficient rebuilds
- ✅ **Versioning**: Can pin to specific months

### Image Contents
**Base:** `python:3.9-slim`

**Key Components:**
- Google Chrome Stable (for Selenium)
- Python packages: selenium, webdriver-manager, pytest (testing)
- Application code: src/
- Entry point: entrypoint.sh

**Size:** ~300MB compressed

### Action Configuration
**File:** `action.yml`
```yaml
runs:
  using: 'docker'
  image: 'docker://ghcr.io/tvlsi/issueservice:latest'
```

**First-Time Setup:**
1. Trigger publish workflow manually
2. Make package public (if repo is public)
3. Action runs will pull pre-built image

---

## Scraping Strategy

### Year Processing Logic
**Scenario 1: First Run (No Previous Issues)**
```
previous_issues.json is empty or doesn't exist
  ↓
get_latest_issue() returns None
  ↓
Process ALL available years on IEEE site
```

**Scenario 2: Incremental Update**
```
Load last issue: Volume 32, Issue 3, March 2024
  ↓
Calculate years_to_process:
  • If last_month >= 6: [last_year, current_year]
  • Else: [last_year]
  ↓
Process only recent years for efficiency
```

### Issue Detection
**Deduplication:** Uses `Issue.__eq__()` to check if issue already exists
- Compares: volume, issue number, year
- Prevents duplicate entries

**Sorting:** Chronological order
- Primary: year
- Secondary: volume
- Tertiary: numerical_month
- Quaternary: issue number

### Robustness Considerations
**Hard-coded Waits:**
- `time.sleep(2)` after year selection (DOM update)
- `time.sleep(3)` after TOC page load (async content)
- Not ideal but stable for current IEEE site

**Failure Modes:**
- CSS selector changes → Scraping fails, logs error
- Network timeouts → WebDriver exception, logged
- Malformed JSON → JSONDecodeError, exits with code 1

---

## Error Handling

### Logging Infrastructure
**Configuration:**
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
```

**Log Levels:**
- **DEBUG**: Not currently used (reserved for future)
- **INFO**: Normal operations, progress updates
- **WARNING**: Non-critical issues (e.g., year selection fails)
- **ERROR**: Failures requiring attention

**Key Logging Points:**
- 29 logger calls across 3 modules
- Entry point arguments
- File I/O operations
- Scraping progress (per year, per issue)
- Error conditions with stack traces

### Exception Handling

**Specific Exceptions:**
- `IOError`: File operations
- `JSONDecodeError`: JSON parsing
- `KeyError`: Missing data fields
- `ValueError`: Data validation
- `KeyboardInterrupt`: Graceful shutdown

**Stack Trace Preservation:**
```python
except Exception as e:
    logger.error("Unexpected error", exc_info=True)
```

**Exit Strategy:**
- Errors during initialization → `sys.exit(1)`
- Errors during scraping → Log + exit(1)
- Browser cleanup in finally block

---

## Performance Considerations

### Current Performance
**Typical Run Time:** 2-5 minutes
- Docker image pull: 30s (first run on new runner)
- Chrome startup: 5-10s
- Per-year scraping: 30-60s
- Per-issue TOC parsing: 2-5s

**Bottlenecks:**
1. Sequential year processing (not parallelized)
2. Hard-coded sleep times (could use smarter waits)
3. Full page loads for each issue (no caching)

### Optimization Opportunities

**Done:**
- ✅ Pre-built Docker images (saves 5-10 min per run)
- ✅ Incremental year processing (only recent years)

**Future Possibilities:**
- Parallel year processing (threading/async)
- Smart waits instead of `time.sleep()`
- Caching strategies (if IEEE provides ETags)
- Chromium instead of Chrome (smaller image)

### Resource Usage
**Memory:** ~500MB (Chrome browser + Python)  
**CPU:** Low (waiting for network I/O)  
**Network:** ~10-20 MB per run  
**Storage:** issues.json grows ~200 bytes per issue

---

## Security Considerations

### Dependency Management
- **No known vulnerabilities** (as of Jan 2026)
- Removed outdated `requests==2.25.1`
- Selenium and webdriver-manager kept current

### Docker Security
**Current State:**
- Runs as root in container (standard for GitHub Actions)
- Network access required for IEEE website
- Filesystem: Writes only to workspace directory

**Recommendations for Future:**
- Run as non-root user
- Read-only filesystem (except workspace)
- Network egress filtering (IEEE domains only)

### Input Validation
**Current:** Minimal
- `issues_file` path not validated for traversal attacks
- Assumed safe in GitHub Actions context (controlled environment)

**Future Enhancement:**
- Validate `issues_file` doesn't contain `../`
- Check file extension is `.json`

---

## Future Improvements

### High Priority
1. **Smart Waiting**: Replace `time.sleep()` with WebDriverWait conditions
2. **Fallback Selectors**: Multiple CSS selectors for robustness
3. **Schema Validation**: Detect IEEE page structure changes

### Medium Priority
4. **Parallel Processing**: Scrape multiple years concurrently
5. **Smoke Tests**: Weekly test against live IEEE site
6. **Metrics**: Tracking scraping success rate, duration

### Low Priority
7. **Chromium Migration**: Smaller Docker image
8. **Retry Logic**: Exponential backoff for network errors
9. **API Alternative**: Investigate if IEEE provides JSON API

---

## Maintenance Guide

### Monthly Tasks (Automated)
- Docker image rebuild (1st of month)
- Dependency updates via Dependabot (if configured)

### Quarterly Review
- Check for IEEE website changes
- Review error logs in action runs
- Update CSS selectors if needed

### Breaking Change Indicators
- Scraping returns 0 issues for recent year
- `NoSuchElementException` in logs
- Persistent timeout errors

### Updating Selectors
1. Visit IEEE TVLSI issues page manually
2. Inspect DOM structure (browser DevTools)
3. Update selectors in `issue_scraper.py`
4. Run tests: `pytest tests/test_issue_scraper.py`
5. Test locally: `python src/main.py data/issues.json`
6. Commit changes, publish new Docker image

---

**Document Version:** 1.0  
**Next Review:** April 2026  
**Maintainer:** TVLSI Organization
