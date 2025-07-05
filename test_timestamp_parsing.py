#!/usr/bin/env python3
"""
Test script to verify timestamp and ANSI code parsing
"""

import json
from github_actions_dependencies import GitHubActionsDependencyParser

def test_timestamp_parsing():
    """Test the parsing with timestamp and ANSI code sample data."""
    
    # Sample log content with timestamps and ANSI codes
    sample_log = """
Some build output...

2025-07-04T08:10:03.4957678Z -- \x1b[1;33m=========================================================================\x1b[m
2025-07-04T08:10:03.4958488Z -- \x1b[1;33m= Dependency report                                                     =\x1b[m
2025-07-04T08:10:03.4959252Z -- \x1b[1;33m=========================================================================\x1b[m

2025-07-04T08:10:03.4960000Z -- \x1b[1;32mDependencies found externally:\x1b[m
2025-07-04T08:10:03.4961000Z -- \x1b[1;37m  cmake 3.28.1\x1b[m
2025-07-04T08:10:03.4962000Z -- \x1b[1;37m  boost 1.84.0\x1b[m
2025-07-04T08:10:03.4963000Z -- \x1b[1;37m  openexr 3.2.0\x1b[m

2025-07-04T08:10:03.4964000Z -- \x1b[1;31mDependencies not found:\x1b[m
2025-07-04T08:10:03.4965000Z -- \x1b[1;37m  missing_package\x1b[m

2025-07-04T08:10:03.4966000Z -- \x1b[1;33mDependencies not found (BUILT LOCALLY):\x1b[m
2025-07-04T08:10:03.4967000Z -- \x1b[1;37m  boost 1.84.0\x1b[m
2025-07-04T08:10:03.4968000Z -- \x1b[1;37m  openexr 3.2.0\x1b[m

2025-07-04T08:10:03.4969461Z -- \x1b[1;33m=========================================================================\x1b[m

More build output...
"""
    
    parser = GitHubActionsDependencyParser()
    result = parser.parse_dependency_section(sample_log)
    
    print("Test Results:")
    print(json.dumps(result, indent=2))
    
    # Verify the structure
    expected_keys = [
        "dependencies_found_externally",
        "dependencies_not_found", 
        "dependencies_built_locally"
    ]
    
    for key in expected_keys:
        assert key in result, f"Missing key: {key}"
    
    assert len(result["dependencies_found_externally"]) == 3
    assert len(result["dependencies_not_found"]) == 1
    assert len(result["dependencies_built_locally"]) == 2
    
    print("\n✅ Timestamp and ANSI code parsing test passed!")

if __name__ == "__main__":
    test_timestamp_parsing() 