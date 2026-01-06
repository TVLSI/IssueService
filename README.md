# IEEE TVLSI Issue Scraper GitHub Action

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A GitHub Action that automatically scrapes IEEE Transactions on Very Large Scale Integration (TVLSI) for new issues and maintains a comprehensive JSON database of all published issues.

## Overview

This action monitors the [IEEE TVLSI journal website](https://ieeexplore.ieee.org/xpl/RecentIssue.jsp?punumber=92) for newly published issues and updates a JSON file with structured metadata about each issue.

### What It Does
- 🔍 **Scrapes** IEEE TVLSI website for all issues (or just new ones)
- 📊 **Tracks** volume number, issue number, month, year, and IEEE isnumber
- 💾 **Updates** your JSON file with new issues (deduplicates automatically)
- 📤 **Outputs** new issues for downstream workflows to process

### Why Use This?
- **Automated monitoring** - No manual checking for new issues
- **Structured data** - Clean JSON format for easy processing
- **GitHub native** - Integrates seamlessly with GitHub Actions
- **Fast execution** - Pre-built Docker images (~2-3 min per run)

## Quick Start

Add this to your workflow:

```yaml
- name: Scrape IEEE TVLSI Issues
  uses: TVLSI/IssueService@v1
  with:
    issues_file: 'data/issues.json'
```

## Configuration

### Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `issues_file` | Path to the JSON file that will be updated with issue data | Yes | `issues.json` |

**Example:** `data/issues.json`, `issues.json`, `path/to/issues.json`

### Outputs

| Output | Description | Type | Example |
|--------|-------------|------|---------|
| `new_issues_count` | Number of new issues found | String (number) | `"3"` |
| `new_issues` | JSON array of all new issues | String (JSON) | `[{...}]` |
| `has_new_issues` | Whether new issues were found | String (boolean) | `"true"` |

**Note:** All outputs are strings (GitHub Actions limitation). Parse accordingly.

### Output Format

Each issue in the `new_issues` array has this structure:

```json
{
  "volume": 32,
  "issue": 1,
  "month": "January",
  "numerical_month": 1,
  "year": 2024,
  "isnumber": "10379819"
}
```

**Fields:**
- `volume` (int): Volume number
- `issue` (int): Issue number within the volume
- `month` (string): Full month name (e.g., "January", "February")
- `numerical_month` (int): Month as number (1-12)
- `year` (int): Publication year
- `isnumber` (string): IEEE's unique identifier for the issue

## Example Workflows

### Basic Usage - Update and Commit

This is the typical workflow pattern (as used in [TVLSI/website-data](https://github.com/TVLSI/website-data)):

```yaml
name: Update TVLSI Issues

on:
  schedule:
    - cron: '0 0 * * 1'  # Run every Monday at midnight UTC
  workflow_dispatch:      # Allow manual triggers

jobs:
  update-issues:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        
      - name: Scrape IEEE TVLSI Issues
        id: scrape
        uses: TVLSI/IssueService@v1
        with:
          issues_file: 'data/issues.json'
          
      - name: Commit changes if new issues found
        if: steps.scrape.outputs.has_new_issues == 'true'
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add data/issues.json
          git commit -m "Update issues: Added ${{ steps.scrape.outputs.new_issues_count }} new issues"
   How It Works

1. **Loads** existing issues from your JSON file
2. **Determines** which years to scrape (all years if first run, recent years otherwise)
3. **Navigates** IEEE TVLSI website using Selenium WebDriver
4. **Extracts** issue metadata from each Table of Contents page
5. **Deduplicates** and sorts issues chronologically
6. **Saves** updated JSON file back to your repository
7. **Outputs** new issues for downstream processing

**Technical Stack:**
- Python 3.9 + Selenium WebDriver
- Chrome browser (headless)
- Pre-built Docker image (updated monthly)
- ~2-3 minute execution time

## Behavior

### First Run (Empty/Missing JSON)
- Processes **all available years** on IEEE website
- Builds complete issue database from scratch
- May take 5-10 minutes depending on issue count

### Subsequent Runs (Incremental)
- Only processes **recent years** (current year + last year)
- Fast execution (~2-3 minutes)
- Automatically deduplicates existing issues

### Idempotency
- Safe to run multiple times
- Won't create duplicate entries
- Sorting is deterministic (chronological)

## Troubleshooting

### No New Issues Found
- Check if IEEE site is accessible: https://ieeexplore.ieee.org/xpl/RecentIssue.jsp?punumber=92
- Verify your `issues_file` contains valid JSON
- Check action logs for scraping errors

### Action Fails
- View detailed logs in Actions tab
- Look for `ERROR` level messages
- Common issues:
  - Invalid JSON in issues_file
  - IEEE website structure changed (CSS selectors)
  - Network timeout

### Stale Data
- Action runs on schedule you define (e.g., weekly)
- IEEE typically publishes issues monthly
- Trigger manually via `workflow_dispatch` if needed

## Documentation

- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Local development setup, testing, debugging
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical architecture, design decisions
- **[TESTING.md](TESTING.md)** - Test suite documentation (103 tests)
- **[CODE_REVIEW_2026-01-06.md](CODE_REVIEW_2026-01-06.md)** - Comprehensive code review

## Contributing

Contributions are welcome! Please:

1. Read [DEVELOPMENT.md](DEVELOPMENT.md) for setup instructions
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Add tests for new functionality
4. Ensure all tests pass (`pytest`)
5. Commit changes (`git commit -m 'feat: Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Maintainers

**TVLSI Organization** - https://github.com/TVLSI

## Acknowledgments

- IEEE Xplore for providing accessible issue data
- Selenium project for browser automation
- GitHub Actions for CI/CD infrastructure
```yaml
name: Update and Process TVLSI Issues

on:
  schedule:
    - cron: '0 0 * * 1'
  workflow_dispatch:

jobs:
  update-issues:
    runs-on: ubuntu-latest
    outputs:
      has_new: ${{ steps.scrape.outputs.has_new_issues }}
      new_count: ${{ steps.scrape.outputs.new_issues_count }}
      
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        
      - name: Scrape IEEE TVLSI Issues
        id: scrape
        uses: TVLSI/IssueService@v1
        with:
          issues_file: 'data/issues.json'
          
      - name: Upload updated issues as artifact
        uses: actions/upload-artifact@v4
        with:
          name: issues-json
          path: data/issues.json
          
  process-new-issues:
    needs: update-issues
    if: needs.update-issues.outputs.has_new == 'true'
    runs-on: ubuntu-latest
    steps:
      - name: Download issues
        uses: actions/download-artifact@v4
        with:
          name: issues-json
          
      - name: Process new issues
        run: |
          echo "Processing ${{ needs.update-issues.outputs.new_count }} new issues"
          # Add your custom processing here
          # e.g., send notifications, update website, etc.
```

### Simple - Just Scrape

Minimal workflow to just run the scraper:

```yaml
name: Scrape TVLSI Issues

on:
  workflow_dispatch:

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Scrape Issues
        uses: TVLSI/IssueService@v1
        with:
          issues_file: 'issues.json'
```

## Development

This action uses a Docker container to scrape the IEEE website and update the issues database. It's built with Python and uses web scraping techniques to extract the data.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.