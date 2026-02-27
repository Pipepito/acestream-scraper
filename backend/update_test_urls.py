#!/usr/bin/env python3
"""
Script to update all test URLs to include the API prefix /api/v1
"""

import os
import re
from pathlib import Path

def update_test_urls():
    """Update all test URLs to include API prefix."""
    test_dir = Path("tests")
    
    # URL patterns to update
    patterns = [
        (r'client\.get\("(/[^"]*)"', r'client.get("/api/v1\1"'),
        (r'client\.post\("(/[^"]*)"', r'client.post("/api/v1\1"'),
        (r'client\.put\("(/[^"]*)"', r'client.put("/api/v1\1"'),
        (r'client\.delete\("(/[^"]*)"', r'client.delete("/api/v1\1"'),
        (r'client\.patch\("(/[^"]*)"', r'client.patch("/api/v1\1"'),
    ]
    
    for test_file in test_dir.glob("test_*.py"):
        print(f"Processing {test_file}...")
        
        with open(test_file, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Apply all patterns
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        # Write back if changed
        if content != original_content:
            with open(test_file, 'w') as f:
                f.write(content)
            print(f"  Updated {test_file}")
        else:
            print(f"  No changes needed for {test_file}")

if __name__ == "__main__":
    update_test_urls()
