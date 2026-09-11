#!/usr/bin/env python3
"""
Script to fix double-prefixed API URLs in test files
"""

import os
import re
from pathlib import Path

def fix_double_prefix():
    """Fix double-prefixed API URLs."""
    test_dir = Path("tests")
    
    for test_file in test_dir.glob("test_*.py"):
        print(f"Processing {test_file}...")
        
        with open(test_file, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Fix double prefixes
        content = content.replace('/api/v1/api/v1/', '/api/v1/')
        
        # Write back if changed
        if content != original_content:
            with open(test_file, 'w') as f:
                f.write(content)
            print(f"  Fixed {test_file}")
        else:
            print(f"  No changes needed for {test_file}")

if __name__ == "__main__":
    fix_double_prefix()
