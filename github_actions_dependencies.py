#!/usr/bin/env python3
"""
GitHub Actions Dependency Parser

This script retrieves GitHub Actions runs for a specified repository and date,
then parses dependency information from the build logs.
"""

import argparse
import json
import re
import sys
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

try:
    from github import Github
except ImportError:
    print("Error: PyGitHub module not found. Please install it with: pip install PyGithub")
    sys.exit(1)

class GitHubActionsDependencyParser:
    def __init__(self, github_token: Optional[str] = None):
        """Initialize the parser with GitHub API access."""
        self.github = Github(github_token)
        
    def parse_github_url(self, url: str) -> Tuple[str, str]:
        """Parse GitHub URL to extract owner and repository name."""
        parsed = urlparse(url)
        if parsed.netloc != "github.com":
            raise ValueError("URL must be a GitHub repository URL")
        
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) < 2:
            raise ValueError("Invalid GitHub repository URL")
            
        owner = path_parts[0]
        repo = path_parts[1]
        return owner, repo
    
    def get_successful_jobs(self, owner: str, repo: str, target_date: date, workflow_name: str = "CI") -> List[Dict]:
        """Retrieve successful GitHub Actions jobs for a specific date and workflow."""
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            workflows = repository.get_workflows()
            
            successful_jobs = []
            
            for workflow in workflows:
                # Only process workflows that match the specified name
                if workflow.name != workflow_name:
                    continue
                    
                try:
                    runs = workflow.get_runs()
                    print(f"Found runs for workflow {workflow.name}")
                    run_count = 0
                    for run in runs:
                        run_count += 1
                            
                        # Check if run was created on target date and was successful
                        run_date = run.created_at.date()
                        if run_date == target_date and run.conclusion == "success":
                            # Get all jobs for this successful run
                            try:
                                jobs = list(run.jobs())
                                for job in jobs:
                                    successful_jobs.append({
                                        'run_id': run.id,
                                        'run_name': run.name,
                                        'workflow_name': workflow.name,
                                        'created_at': run.created_at.isoformat(),
                                        'head_branch': run.head_branch,
                                        'job_id': job.id,
                                        'job_name': job.name,
                                        'job_conclusion': job.conclusion
                                    })
                            except Exception as e:
                                print(f"Warning: Could not retrieve jobs for run {run.id}: {e}")
                                continue
                        # Stop if we've gone too far back in time
                        elif run_date < target_date:
                            break
                except Exception as e:
                    print(f"Warning: Could not retrieve runs for workflow {workflow.name}: {e}")
                    continue
            
            return successful_jobs
            
        except Exception as e:
            print(f"Error retrieving runs: {e}")
            return []
    
    def get_build_logs(self, owner: str, repo: str, run_id: int, job_id: Optional[int] = None) -> Optional[str]:
        """Retrieve build logs for a specific job."""
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            run = repository.get_workflow_run(run_id)
            
            # Get the specific job if job_id is provided, otherwise find a build job
            target_job = None
            
            # Try to get jobs from the run using the correct API
            try:
                # Call the jobs method and convert to list
                jobs = list(run.jobs())
                
                if job_id:
                    # Find the specific job by ID
                    for job in jobs:
                        if job.id == job_id:
                            target_job = job
                            break
                else:
                    # Find a build job (usually named "Build" or similar)
                    for job in jobs:
                        if "build" in job.name.lower():
                            target_job = job
                            break
                    
                    if not target_job and jobs:
                        target_job = jobs[0]
            except Exception as e:
                print(f"Could not retrieve jobs for run {run_id}: {e}")
                return None
            
            if target_job:
                # Get the logs using the correct API
                try:
                    # Use the logs_url method and download with requests
                    logs_url = target_job.logs_url()
                    import requests
                    
                    # Make request without authentication (logs are public)
                    response = requests.get(logs_url)
                    if response.status_code == 200:
                        return response.text
                    else:
                        print(f"Failed to retrieve logs for job {target_job.id}: {response.status_code}")
                        return None
                except Exception as e:
                    print(f"Error retrieving logs for job {target_job.id}: {e}")
                    return None
            else:
                print(f"No target job found for run {run_id}")
                return None
                
        except Exception as e:
            print(f"Error retrieving logs for run {run_id}: {e}")
            return None
    
    def parse_dependency_section(self, log_content: str) -> Dict:
        """Parse the dependency report section from build logs."""
        # Pattern to find the dependency report section with timestamps and ANSI codes
        start_pattern = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z -- \x1b\[1;33m=========================================================================\x1b\[m\n\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z -- \x1b\[1;33m= Dependency report\s*=\s*\x1b\[m\n\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z -- \x1b\[1;33m=========================================================================\x1b\[m"
        end_pattern = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z -- \x1b\[1;33m=========================================================================\x1b\[m"
        
        # Find the dependency section
        start_match = re.search(start_pattern, log_content, re.MULTILINE)
        if not start_match:
            return {"error": "Dependency report section not found"}
        
        start_pos = start_match.end()
        end_match = re.search(end_pattern, log_content[start_pos:])
        
        if not end_match:
            return {"error": "End of dependency report section not found"}
        
        end_pos = start_pos + end_match.start()
        dependency_section = log_content[start_pos:end_pos].strip()
        
        return self._parse_dependencies(dependency_section)
    
    def _clean_line(self, line: str) -> str:
        """Clean a line by removing ANSI codes, timestamps, and leading -- characters."""
        # Remove leading/trailing whitespace
        line = line.strip()
        
        # Remove timestamp prefix (format: 2024-12-30T10:30:00.123Z -- )
        line = re.sub(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z -- ', '', line)
        
        # Remove all ANSI escape codes (comprehensive)
        line = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', line)  # Color codes, cursor movement, etc.
        line = re.sub(r'\x1b\[m', '', line)  # Reset codes
        line = re.sub(r'\x1b\[K', '', line)  # Clear line codes
        line = re.sub(r'\x1b\[[0-9]*[ABCD]', '', line)  # Cursor movement codes
        
        # Remove leading -- characters (common in dependency lists)
        line = re.sub(r'^--+\s*', '', line)
        
        return line.strip()
    
    def _parse_dependencies(self, section: str) -> Dict:
        """Parse the dependency section into structured data."""
        dependencies = {
            "dependencies_found_externally": [],
            "dependencies_too_old": [],
            "dependencies_built_locally": [],
            "dependencies_not_found": []
        }
        
        lines = section.split('\n')
        current_section = None
        
        for line in lines:
            # Clean the line first
            clean_line = self._clean_line(line)
            if not clean_line:
                continue
                
            # Detect section headers
            if "the following dependencies found externally:" in clean_line.lower():
                current_section = "dependencies_found_externally"
                continue
            elif "the following dependencies were found but were too old:" in clean_line.lower():
                current_section = "dependencies_too_old"
                continue
            elif "the following dependencies were not found" in clean_line.lower():
                current_section = "dependencies_not_found"
                continue
            
            # Parse package entries (lines that look like package names)
            if current_section and clean_line:
                # Skip if this is a section header (contains "Dependencies")
                if "dependencies" in clean_line.lower():
                    continue
                
                if current_section == "dependencies_found_externally":
                    # Try to extract version if present
                    version_match = re.search(r'(\S+)\s+(\S+)\s*$', clean_line)
                elif current_section == "dependencies_too_old":
                    # Try to extract version too old if present
                    version_match = re.search(r'(\S+) \(([^)]+)\)$', clean_line)
                elif current_section == "dependencies_not_found":
                    # Try to extract version not found if present with optional BUILT LOCALLY
                    version_match = re.search(r'(\S+) (\S+)  \((\S+) BUILT LOCALLY\)$', clean_line)
                    if version_match:
                        current_section = "dependencies_built_locally"
                        version_match = re.search(r'(\S+) (\S+)$', clean_line)

                if version_match:
                    package_name = version_match.group(1)
                    version = version_match.group(2)
                    dependencies[current_section].append({
                        "package": package_name,
                        "version": version
                    })
                else:
                    # No version found, just package name
                    dependencies[current_section].append({
                        "package": clean_line,
                        "version": None
                    })

        return dependencies
    
    def process_repository(self, github_url: str, target_date: date, workflow_name: str = "CI") -> Dict:
        """Main method to process a repository and extract dependency information."""
        try:
            owner, repo = self.parse_github_url(github_url)
            print(f"Processing repository: {owner}/{repo}")
            print(f"Target date: {target_date}")
            print(f"Workflow name: {workflow_name}")
            
            # Get successful jobs
            successful_jobs = self.get_successful_jobs(owner, repo, target_date, workflow_name)
            print(f"Found {len(successful_jobs)} successful jobs")
            
            results = {
                "repository": f"{owner}/{repo}",
                "date": target_date.isoformat(),
                "runs": []
            }
            
            for job in successful_jobs:
                print(f"Processing job {job['job_id']} ({job['job_name']}) from run {job['run_id']}: {job['run_name']}")
                
                # Get build logs for this specific job
                logs = self.get_build_logs(owner, repo, job['run_id'], job['job_id'])
                
                if logs:
                    # Parse dependency section
                    dependencies = self.parse_dependency_section(logs)
                    
                    job_result = {
                        "run_id": job['run_id'],
                        "run_name": job['run_name'],
                        "workflow_name": job['workflow_name'],
                        "created_at": job['created_at'],
                        "head_branch": job['head_branch'],
                        "job_id": job['job_id'],
                        "job_name": job['job_name'],
                        "job_conclusion": job['job_conclusion'],
                        "dependencies": dependencies
                    }
                    
                    results["runs"].append(job_result)
                else:
                    print(f"Could not retrieve logs for job {job['job_id']} from run {job['run_id']}")
            
            return results
            
        except Exception as e:
            print(f"Error processing repository: {e}")
            return {"error": str(e)}


def main():
    """Main function to handle command line arguments and execute the script."""
    parser = argparse.ArgumentParser(
        description="Parse GitHub Actions dependency information from build logs"
    )
    parser.add_argument(
        "--date",
        type=str,
        default=date.today().isoformat(),
        help="Target date in YYYY-MM-DD format (default: today)"
    )
    parser.add_argument(
        "--url",
        type=str,
        default="https://github.com/AcademySoftwareFoundation/OpenImageIO",
        help="GitHub repository URL (default: https://github.com/AcademySoftwareFoundation/OpenImageIO)"
    )
    parser.add_argument(
        "--token",
        type=str,
        help="GitHub API token (optional, but recommended for higher rate limits)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file for JSON results (default: stdout)"
    )
    parser.add_argument(
        "--workflow",
        type=str,
        default="CI",
        help="Workflow name to filter runs (default: CI)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test the script without making API calls (uses sample data)"
    )
    
    args = parser.parse_args()
    
    # Parse date
    try:
        target_date = datetime.fromisoformat(args.date).date()
    except ValueError:
        print(f"Error: Invalid date format '{args.date}'. Use YYYY-MM-DD format.")
        sys.exit(1)
    
    # Initialize parser
    parser_obj = GitHubActionsDependencyParser(args.token)
    
    if args.dry_run:
        # Test with sample data
        print("Running in dry-run mode with sample data...")
        sample_results = {
            "repository": "AcademySoftwareFoundation/OpenImageIO",
            "date": target_date.isoformat(),
            "workflow_name": args.workflow,
            "runs": [
                {
                    "run_id": 123456789,
                    "run_name": "Build",
                    "workflow_name": args.workflow,
                    "created_at": "2024-12-30T10:30:00Z",
                    "head_branch": "main",
                    "job_id": 987654321,
                    "job_name": "build",
                    "job_conclusion": "success",
                    "dependencies": {
                        "dependencies_found_externally": [
                            {"package": "cmake", "version": "3.28.1"},
                            {"package": "boost", "version": "1.84.0"}
                        ],
                        "dependencies_not_found": [
                            {"package": "missing_package", "version": None}
                        ],
                        "dependencies_built_locally": [
                            {"package": "openexr", "version": "3.2.0"}
                        ]
                    }
                }
            ]
        }
        results = sample_results
    else:
        # Process repository
        results = parser_obj.process_repository(args.url, target_date, args.workflow)
    
    # Output results
    json_output = json.dumps(results, indent=2)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(json_output)
        print(f"Results written to {args.output}")
    else:
        print(json_output)


if __name__ == "__main__":
    main() 
