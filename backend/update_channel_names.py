#!/usr/bin/env python3
"""
Script to update all channel name references in tests to use the new naming scheme.
"""

import re
import glob

# Mapping from old names to new names
name_mapping = {
    "Test Channel 1": "Alpha Channel",
    "Test Channel 2": "Beta Channel", 
    "Test Channel 3": "Gamma Channel"
}

def update_file(file_path):
    """Update a single file with the new channel names."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Replace all occurrences
    for old_name, new_name in name_mapping.items():
        content = content.replace(f'"{old_name}"', f'"{new_name}"')
        content = content.replace(f"'{old_name}'", f"'{new_name}'")
        content = content.replace(old_name, new_name)
    
    # Only write if content changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {file_path}")
    else:
        print(f"No changes needed in {file_path}")

# Update all Python test files
test_files = glob.glob("tests/*.py")
for file_path in test_files:
    if file_path.endswith('.py'):
        update_file(file_path)

print("Done!")
