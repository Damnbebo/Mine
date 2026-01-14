#!/bin/bash
# Quick Fix for Slow Website
# Run as root on your VPS: bash quick_fix_slow_site.sh

echo "=== Quick Fix for Slow Website ==="
echo ""

# 1. Kill stuck chromium/playwright processes (MOST COMMON CAUSE)
echo "[1/6] Killing stuck browser processes..."
pkill -9 -f "chromium" 2>/dev/null
pkill -9 -f "chrome" 2>/dev/null
pkill -9 -f "playwright" 2>/dev/null
# Kill any python bot processes stuck for too long
pkill -9 -f "bot_batch.py" 2>/dev/null
pkill -9 -f "bot.py" 2>/dev/null
echo "   ✓ Browser processes cleaned"

# 2. Clear PHP-FPM stuck workers
echo "[2/6] Restarting PHP-FPM..."
systemctl restart php8.3-fpm
echo "   ✓ PHP-FPM restarted"

# 3. Clear Nginx cache and restart
echo "[3/6] Restarting Nginx..."
rm -rf /var/cache/nginx/* 2>/dev/null
systemctl restart nginx
echo "   ✓ Nginx restarted"

# 4. Clear system cache (frees RAM)
echo "[4/6] Clearing system cache..."
sync
echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true
echo "   ✓ System cache cleared"

# 5. Kill any runaway MySQL queries
echo "[5/6] Checking MySQL..."
# Kill queries running longer than 60 seconds
mysql -e "SELECT CONCAT('KILL ', id, ';') FROM information_schema.processlist WHERE time > 60 AND command != 'Sleep';" 2>/dev/null | grep -v CONCAT | mysql 2>/dev/null
systemctl restart mysql
echo "   ✓ MySQL restarted"

# 6. Add cron to prevent future buildup (if not already added)
echo "[6/6] Checking cleanup cron..."
if ! crontab -l 2>/dev/null | grep -q "kill_stuck_chrome"; then
    (crontab -l 2>/dev/null; echo "*/5 * * * * pgrep -f 'chrom' | xargs -r ps -o pid,etimes 2>/dev/null | awk '\$2 > 300 {print \$1}' | xargs -r kill -9 2>/dev/null # kill_stuck_chrome") | crontab -
    echo "   ✓ Added cleanup cron job"
else
    echo "   ✓ Cleanup cron already exists"
fi

echo ""
echo "=== Quick Fix Complete ==="
echo ""
echo "Current Status:"
echo "---------------"
echo "Memory:"
free -h | grep Mem
echo ""
echo "PHP-FPM:"
systemctl status php8.3-fpm --no-pager | grep Active
echo ""
echo "Nginx:"
systemctl status nginx --no-pager | grep Active
echo ""
echo "MySQL:"
systemctl status mysql --no-pager | grep Active
echo ""
echo "Browser processes:"
pgrep -c -f "chrom" 2>/dev/null || echo "0"
echo ""
echo "Your website should be faster now!"
