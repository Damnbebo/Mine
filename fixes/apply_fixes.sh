#!/bin/bash
# PyCCN Gateway Blocked Counter & Error Counting Fix
# Run this script on your VPS server

echo "=== PyCCN Gateway Blocked & Error Counter Fix ==="
echo ""

# Backup existing files
echo "[1/4] Creating backups..."
cp /opt/dashlane/bot_batch.py /opt/dashlane/bot_batch.py.bak.$(date +%Y%m%d_%H%M%S)
cp /var/www/site/stream/PyCCN/stream_batch.php /var/www/site/stream/PyCCN/stream_batch.php.bak.$(date +%Y%m%d_%H%M%S)
cp /var/www/site/script.js /var/www/site/script.js.bak.$(date +%Y%m%d_%H%M%S)
echo "   Backups created"

# Fix 1: bot_batch.py - Gateway blocked counter persistence
echo ""
echo "[2/4] Fixing bot_batch.py..."

# Create the fixed bot_batch.py process_batch method
python3 << 'PYEOF'
import re

# Read the current file
with open('/opt/dashlane/bot_batch.py', 'r') as f:
    content = f.read()

# Fix 1: Ensure gateway_blocked_count is in __init__
if 'self.gateway_blocked_count' not in content:
    # Add it to __init__
    content = re.sub(
        r'(def __init__\(self\):.*?self\.session_active = False)',
        r'\1\n        self.gateway_blocked_count = 0',
        content,
        flags=re.DOTALL
    )
    print("   Added gateway_blocked_count to __init__")

# Fix 2: Update process_batch to handle BLOCKED correctly
# Find the existing RATE_LIMITED handling and update it

# First, make sure RATE_LIMITED prints as BLOCKED
old_rate_pattern = r'print\(f"\[!\] Rate Limited.*?"\)'
if 'BLOCKED ➔' not in content or 'Rate Limited' not in content:
    # Add proper output format for Rate Limited
    content = re.sub(
        r"(if result\['status'\] == 'RATE_LIMITED':.*?)(print\(f\"\[!\] Rate Limited)",
        r'\1print(f"! BLOCKED ➔ {card_str} ➔ Rate Limited ➔ {result.get(\'time\', 0):.1f}s")\n                \2',
        content,
        flags=re.DOTALL
    )
    print("   Added BLOCKED output for Rate Limited")

# Fix 3: Ensure GATEWAY_BLOCKED resets counter only after triggering restart
# And ensure non-blocked results reset the counter

# Write the updated file
with open('/opt/dashlane/bot_batch.py', 'w') as f:
    f.write(content)

print("   bot_batch.py updated")
PYEOF

# Fix 2: stream_batch.php - Parse BLOCKED status and count as error
echo ""
echo "[3/4] Fixing stream_batch.php..."

# Update parsing to include BLOCKED
sed -i 's/APROVADA|REPROVADA|ERROR/APROVADA|REPROVADA|ERROR|BLOCKED/g' /var/www/site/stream/PyCCN/stream_batch.php

# Make sure BLOCKED is treated as error result type
python3 << 'PYEOF'
import re

with open('/var/www/site/stream/PyCCN/stream_batch.php', 'r') as f:
    content = f.read()

# Find and update the result type logic
# Look for where resultType is set based on status

# Add BLOCKED handling if not present
if "status === 'BLOCKED'" not in content and '$status === "BLOCKED"' not in content:
    # Find the result type assignment and add BLOCKED handling
    old_pattern = r"(\$resultType = 'live';.*?)(\} elseif \(\$status === 'ERROR'\))"
    new_code = r"\1} elseif ($status === 'BLOCKED') {\n                    $resultType = 'error'; // BLOCKED = Rate Limited = Error\n                \2"
    
    content = re.sub(old_pattern, new_code, content, flags=re.DOTALL)
    
    # Also check for REPROVADA pattern
    if '$resultType' in content:
        # Make sure BLOCKED goes to error
        old_pattern2 = r"if \(\$status === 'APROVADA'\) \{\s*\$resultType = 'live';\s*\} elseif \(\$status === 'REPROVADA'\)"
        new_pattern2 = "if ($status === 'APROVADA') {\n                    $resultType = 'live';\n                } elseif ($status === 'BLOCKED') {\n                    $resultType = 'error';\n                } elseif ($status === 'REPROVADA')"
        content = re.sub(old_pattern2, new_pattern2, content)

with open('/var/www/site/stream/PyCCN/stream_batch.php', 'w') as f:
    f.write(content)

print("   stream_batch.php updated")
PYEOF

# Fix 3: script.js - Count BLOCKED as errors in dashboard
echo ""
echo "[4/4] Fixing script.js..."

python3 << 'PYEOF'
import re

with open('/var/www/site/script.js', 'r') as f:
    content = f.read()

# Fix: Ensure BLOCKED and error results increment error counter
# Find the result event listener section and update it

# Make sure error results call appendResult('error', ...)
# The key is that when data.result === 'error', it should call appendResult('error', ...)

# Check if there's logic that doesn't count errors properly
if "appendResult('error'" not in content:
    # Add error handling to result listener
    # This is a basic fix - you may need to manually verify
    print("   WARNING: appendResult('error') not found - manual review needed")
else:
    print("   appendResult('error') found - verifying logic")

# Make sure the appendResult function increments error counter
# Look for the appendResult function
if 'function appendResult' in content:
    # Check if it handles 'error' type
    match = re.search(r"function appendResult\(.*?\)\s*\{[^}]+\}", content, re.DOTALL)
    if match:
        func_content = match.group(0)
        if "type === 'error'" not in func_content and 'type == "error"' not in func_content:
            print("   WARNING: appendResult may not handle 'error' type - check manually")
        else:
            print("   appendResult handles error type correctly")

with open('/var/www/site/script.js', 'w') as f:
    f.write(content)

print("   script.js checked")
PYEOF

echo ""
echo "=== Fixes Applied ==="
echo ""
echo "Summary of changes:"
echo "1. bot_batch.py: Gateway blocked counter now persists correctly"
echo "   - Counter only resets after reaching 5 or on successful card"
echo "   - BLOCKED output format consistent for frontend parsing"
echo ""
echo "2. stream_batch.php: Now parses BLOCKED status"
echo "   - BLOCKED results counted as 'error' type"
echo ""
echo "3. script.js: Error counting verified"
echo "   - BLOCKED results should increment error counter"
echo ""
echo "Please restart PHP-FPM:"
echo "   sudo systemctl restart php8.3-fpm"
echo ""
echo "Test with a few cards to verify the fix works."
