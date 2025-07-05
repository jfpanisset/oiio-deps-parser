# OIIO Dependencies Parser

This Python script retrieves GitHub Actions runs for the OpenImageIO repository and parses dependency information from the build logs to track external dependencies, locally built packages, and missing dependencies.

Project mostly authored with Cursor.

## Features

- Retrieves successful GitHub Actions jobs for a specific date
- Filters jobs by workflow name (defaults to "CI")
- Extracts build logs from each individual job
- Parses dependency report sections from the logs
- Outputs structured JSON with dependency categories:
  - `dependencies_found_externally` (with versions)
  - `dependencies_too_old` (dependencies found but version too old)
  - `dependencies_built_locally` (dependencies built from source)
  - `dependencies_not_found` (missing dependencies)

## Installation

This project uses `uv` for dependency management. If you don't have `uv` installed, you can install it on macOS  with:

```bash
brew install uv
```

Then install the dependencies:

```bash
uv sync
```

## Usage

### Basic Usage

```bash
# Use defaults (today's date, OpenImageIO repository)
uv run python github_actions_dependencies.py

# Specify a date
uv run python github_actions_dependencies.py --date 2024-01-15

# Specify a different repository
uv run python github_actions_dependencies.py --url https://github.com/owner/repo

# Filter by specific workflow
uv run python github_actions_dependencies.py --workflow "docs"

# Save output to file
uv run python github_actions_dependencies.py --output results.json
```

### Command Line Options

- `--date`: Target date in YYYY-MM-DD format (default: today)
- `--url`: GitHub repository URL (default: OpenImageIO repository)
- `--token`: GitHub API token (optional, but recommended for higher rate limits)
- `--output`: Output file for JSON results (default: stdout)
- `--workflow`: Workflow name to filter jobs (default: CI)
- `--dry-run`: Test the script without making API calls (uses sample data)

### GitHub API Token

For better rate limits and access to private repositories, you can provide a GitHub API token:

1. Create a personal access token at https://github.com/settings/tokens
2. Use it with the `--token` argument:
```bash
uv run python github_actions_dependencies.py --token YOUR_TOKEN_HERE
```

## Output Format

The script outputs JSON with the following structure:

```json
{
  "repository": "AcademySoftwareFoundation/OpenImageIO",
  "date": "2024-01-15",
  "runs": [
    {
      "run_id": 123456789,
      "run_name": "Build",
      "workflow_name": "CI",
      "created_at": "2024-01-15T10:30:00Z",
      "head_branch": "main",
      "job_id": 987654321,
      "job_name": "build",
      "job_conclusion": "success",
      "dependencies": {
        "dependencies_found_externally": [
          {
            "package": "cmake",
            "version": "3.28.1"
          }
        ],
        "dependencies_too_old": [
          {
            "package": "boost",
            "version": "1.83.0"
          }
        ],
        "dependencies_built_locally": [
          {
            "package": "openexr",
            "version": "3.2.0"
          }
        ],
        "dependencies_not_found": [
          {
            "package": "missing_package",
            "version": null
          }
        ]
      }
    }
  ]
}
```

## Example

```bash
# Get dependencies from OpenImageIO for today
uv run python github_actions_dependencies.py

# Get dependencies from a specific date
uv run python github_actions_dependencies.py --date 2024-01-15 --output oiio_deps.json

# Filter by workflow and date
uv run python github_actions_dependencies.py --workflow "CI" --date 2024-01-15 --output ci_jobs_deps.json

# Test the script without API calls
uv run python github_actions_dependencies.py --dry-run --output test.json
```

## Error Handling

The script handles various error conditions:
- Invalid GitHub URLs
- Missing dependency report sections in logs
- API rate limiting
- Network connectivity issues

Errors are reported in the output JSON and to stderr for debugging.

## Dependencies

- `PyGithub`: GitHub API client library
- Standard Python libraries: `argparse`, `json`, `re`, `sys`, `datetime`, `typing`, `urllib.parse` 
