#!/usr/bin/env python3
"""
Test script to check what dates have successful runs
"""

from datetime import datetime, date
from github_actions_dependencies import GitHubActionsDependencyParser

def test_dates():
    """Test different dates to see which ones have successful runs."""
    
    # Test dates
    test_dates = [
        "2025-07-03",
        "2025-07-04", 
        "2025-07-05",
        "2025-07-06",
        "2025-07-07"
    ]
    
    parser = GitHubActionsDependencyParser()
    
    for date_str in test_dates:
        try:
            target_date = datetime.fromisoformat(date_str).date()
            print(f"\nTesting date: {date_str}")
            
            # Just get the successful jobs count without processing logs
            successful_jobs = parser.get_successful_jobs("AcademySoftwareFoundation", "OpenImageIO", target_date, "CI")
            print(f"Found {len(successful_jobs)} successful jobs")
            
            if successful_jobs:
                # Show first few jobs
                for i, job in enumerate(successful_jobs[:3]):
                    print(f"  Job {i+1}: {job['job_name']} (ID: {job['job_id']})")
                if len(successful_jobs) > 3:
                    print(f"  ... and {len(successful_jobs) - 3} more jobs")
            else:
                print("  No successful jobs found")
                
        except Exception as e:
            print(f"Error testing {date_str}: {e}")

if __name__ == "__main__":
    test_dates() 