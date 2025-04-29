# IEEE TVLSI Issue Scraper GitHub Action

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A GitHub Action that automatically scrapes IEEE Transactions on Very Large Scale Integration (TVLSI) for new issues and keeps an updated json file of all issues.

## Overview

This action monitors the IEEE TVLSI journal website for newly published issues and updates a JSON file with structured metadata about each issue, including:
- Volume number
- Issue number
- Month
- Year
- IEEE isnumber

## Usage

```yaml
- name: Scrape IEEE TVLSI Issues
    uses: TVLSI/IssueService@v1
    with:
        issues_file: 'data/issues.json'
```

### Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `issues_file` | Path to the JSON file that will be updated with issue data | Yes | `issues.json` |

### Outputs

| Output | Description |
|--------|-------------|
| `new_issues_count` | Number of new issues found during this run |
| `new_issues` | JSON array of all new issues found |
| `has_new_issues` | Boolean indicating whether new issues were found |

## Example Workflows

### Basic Usage

```yaml
name: Update TVLSI Issues

on:
    schedule:
        - cron: '0 0 * * 1'  # Run every Monday at midnight
    workflow_dispatch:      # Allow manual triggers

jobs:
    update-issues:
        runs-on: ubuntu-latest
        steps:
            - name: Checkout repository
                uses: actions/checkout@v3
                
            - name: Scrape IEEE TVLSI Issues
                id: scrape
                uses: TVLSI/IssueService@v1
                with:
                    issues_file: 'data/issues.json'
                    
            - name: Commit changes if new issues found
                if: steps.scrape.outputs.has_new_issues == 'true'
                run: |
                    git config --local user.email "action@github.com"
                    git config --local user.name "GitHub Action"
                    git add data/issues.json
                    git commit -m "Update issues: Added ${{ steps.scrape.outputs.new_issues_count }} new issues"
                    git push

## Development

This action uses a Docker container to scrape the IEEE website and update the issues database. It's built with Python and uses web scraping techniques to extract the data.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.