#!/bin/bash
# Server Performance Diagnostic & Optimization Script
# Run this on your VPS as root

echo "=== Server Performance Diagnostic ==="
echo ""

# 1. Check system resources
echo "[1/8] System Resources:"
echo "------------------------"
echo "Load Average:"
uptime
echo ""
echo "Memory:"
free -h
echo ""
echo "Disk:"
df -h / | tail -1
echo ""

# 2. Check for stuck chromium/playwright processes
echo "[2/8] Checking for stuck browser processes..."
CHROME_COUNT=$(pgrep -c -f "chrom" 2>/dev/null || echo "0")
echo "   Chrome/Chromium processes: $CHROME_COUNT"
if [ "$CHROME_COUNT" -gt 5 ]; then
    echo "   ⚠️ Too many browser processes! Killing old ones..."
    # Kill chromium processes older than 5 minutes
    pkill -9 -f "chrome" 2>/dev/null
    echo "   ✓ Killed stuck browser processes"
fi
echo ""

# 3. Check PHP-FPM
echo "[3/8] PHP-FPM Status:"
PHP_FPM_PROCS=$(pgrep -c -f "php-fpm" 2>/dev/null || echo "0")
echo "   PHP-FPM processes: $PHP_FPM_PROCS"

# Check PHP-FPM pool status if available
if [ -S /var/run/php/php8.3-fpm.sock ]; then
    echo "   ✓ PHP-FPM socket exists"
else
    echo "   ⚠️ PHP-FPM socket not found - restarting..."
    systemctl restart php8.3-fpm
fi
echo ""

# 4. Check MySQL
echo "[4/8] MySQL Status:"
MYSQL_PROCS=$(pgrep -c -f "mysql" 2>/dev/null || echo "0")
echo "   MySQL processes: $MYSQL_PROCS"

# Check MySQL connections
MYSQL_CONNS=$(mysql -N -e "SHOW STATUS LIKE 'Threads_connected';" 2>/dev/null | awk '{print $2}' || echo "unknown")
echo "   Active connections: $MYSQL_CONNS"

# Check for slow queries
SLOW_QUERIES=$(mysql -N -e "SHOW STATUS LIKE 'Slow_queries';" 2>/dev/null | awk '{print $2}' || echo "unknown")
echo "   Slow queries: $SLOW_QUERIES"
echo ""

# 5. Check Nginx
echo "[5/8] Nginx Status:"
NGINX_PROCS=$(pgrep -c -f "nginx" 2>/dev/null || echo "0")
echo "   Nginx processes: $NGINX_PROCS"

# Check nginx error log for issues
NGINX_ERRORS=$(tail -100 /var/log/nginx/error.log 2>/dev/null | grep -c "error" || echo "0")
echo "   Recent errors in log: $NGINX_ERRORS"
echo ""

# 6. Top memory consumers
echo "[6/8] Top Memory Consumers:"
ps aux --sort=-%mem | head -8 | tail -7
echo ""

# 7. Top CPU consumers  
echo "[7/8] Top CPU Consumers:"
ps aux --sort=-%cpu | head -8 | tail -7
echo ""

# 8. Apply optimizations
echo "[8/8] Applying Optimizations..."
echo ""

# Kill any zombie processes
echo "   Killing zombie processes..."
ps aux | awk '$8=="Z" {print $2}' | xargs -r kill -9 2>/dev/null

# Clear PHP OPcache
echo "   Clearing PHP OPcache..."
# This works if you have a opcache reset endpoint
curl -s "http://localhost/opcache_reset.php" 2>/dev/null || true

# Restart services if needed
read -p "   Restart PHP-FPM? (y/n): " restart_php
if [ "$restart_php" = "y" ]; then
    systemctl restart php8.3-fpm
    echo "   ✓ PHP-FPM restarted"
fi

read -p "   Restart MySQL? (y/n): " restart_mysql
if [ "$restart_mysql" = "y" ]; then
    systemctl restart mysql
    echo "   ✓ MySQL restarted"
fi

read -p "   Restart Nginx? (y/n): " restart_nginx
if [ "$restart_nginx" = "y" ]; then
    systemctl restart nginx
    echo "   ✓ Nginx restarted"
fi

echo ""
echo "=== Diagnostic Complete ==="
