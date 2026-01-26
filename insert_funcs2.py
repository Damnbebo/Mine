#!/usr/bin/env python3
import re

# Read the main2.py file
with open("/home/ubuntu/amazon-bot/main2.py", "r") as f:
    content = f.read()

# Read the functions to insert
with open("/tmp/solvecaptcha_funcs.py", "r") as f:
    funcs_code = f.read()

# Check if functions already exist
if "async def solve_funcaptcha_solvecaptcha" in content:
    print("SolveCaptcha functions already exist in main2.py")
else:
    # Find insertion point - after set_current_page function (with exact text)
    marker = '''def set_current_page(page):
    """Set reference to current page for error screenshots"""
    global _current_page_ref
    _current_page_ref = page'''
    
    if marker in content:
        content = content.replace(marker, marker + "\n\n" + funcs_code)
        print("Inserted SolveCaptcha functions after set_current_page")
    else:
        # Try alternate approach - insert after line 896
        print("Using line-based insertion")
        lines = content.split('\n')
        # Find the line with set_current_page
        insert_after = None
        for i, line in enumerate(lines):
            if 'def set_current_page(page):' in line:
                # Find the end of this function (next def or blank line + code)
                for j in range(i+1, len(lines)):
                    if lines[j].strip() and not lines[j].startswith(' ') and not lines[j].startswith('\t'):
                        insert_after = j
                        break
                break
        
        if insert_after:
            lines.insert(insert_after, "\n" + funcs_code + "\n")
            content = '\n'.join(lines)
            print(f"Inserted functions at line {insert_after}")
        else:
            print("Could not find insertion point")

# Write back
with open("/home/ubuntu/amazon-bot/main2.py", "w") as f:
    f.write(content)

print("Done!")
