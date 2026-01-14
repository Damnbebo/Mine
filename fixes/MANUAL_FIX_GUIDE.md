# PyCCN Gateway Blocked Counter & Error Counting Fix

## Issues Being Fixed:
1. **Gateway Blocked counter keeps resetting to (1/5)** - Counter should persist and only reset after reaching 5/5 or getting a successful/normal result
2. **BLOCKED results (Rate Limited) not counted as errors** - Dashboard shows 0 errors despite multiple BLOCKED responses

---

## Fix 1: /opt/dashlane/bot_batch.py

### 1.1 Ensure `gateway_blocked_count` is initialized in `__init__`:

```python
def __init__(self):
    self.browser = None
    self.context = None
    self.page = None
    self.session_active = False
    self.gateway_blocked_count = 0  # <-- ADD THIS LINE
```

### 1.2 Update `process_batch` method - Key Changes:

Find the section that handles `RATE_LIMITED` and `GATEWAY_BLOCKED`. The key fixes are:

**A) When RATE_LIMITED occurs:**
```python
if result['status'] == 'RATE_LIMITED':
    # Print as BLOCKED for frontend parsing (IMPORTANT!)
    print(f"! BLOCKED ➔ {card_str} ➔ Rate Limited ➔ {result.get('time', 0):.1f}s")
    
    # Restart browser but DON'T reset gateway_blocked_count
    # (Rate limit is different from gateway blocked)
    print(f"[!] Rate Limited! Restarting browser for new IP...")
    self.session_active = False
    self.close_browser()
    continue  # Retry this card
```

**B) When GATEWAY_BLOCKED occurs:**
```python
if result['status'] == 'GATEWAY_BLOCKED':
    self.gateway_blocked_count += 1
    current_count = self.gateway_blocked_count
    
    # Print with count
    print(f"✗ REPROVADA ➔ {card_str} ➔ Gateway Blocked ({current_count}/5) ➔ {result.get('time', 0):.1f}s")
    
    if current_count >= 5:
        print(f"[!] 5 consecutive Gateway Blocked! Restarting browser...")
        self.gateway_blocked_count = 0  # Only reset AFTER triggering restart
        self.session_active = False
        self.close_browser()
        continue  # Retry this card with new session
    else:
        # Move to next card (don't retry same card)
        result['status'] = 'REPROVADA'
        result['reason'] = f"Gateway Blocked ({current_count}/5)"
        remaining.pop(0)
        results.append(result)
        continue
```

**C) Reset counter on successful/normal results:**
```python
# After processing a normal result (not BLOCKED):
if result['status'] in ['APROVADA', 'REPROVADA', 'ERROR']:
    self.gateway_blocked_count = 0  # Reset on any non-blocked result
```

---

## Fix 2: /var/www/site/stream/PyCCN/stream_batch.php

### 2.1 Update regex to include BLOCKED status:

Find this pattern:
```php
if (preg_match('/([✓✗!]) (APROVADA|REPROVADA|ERROR) ➔/', $line, $m)) {
```

Change to:
```php
if (preg_match('/([✓✗!]) (APROVADA|REPROVADA|ERROR|BLOCKED) ➔/', $line, $m)) {
```

### 2.2 Add BLOCKED handling in result type logic:

Find where `$resultType` is set and add BLOCKED handling:
```php
if ($status === 'APROVADA') {
    $resultType = 'live';
} elseif ($status === 'BLOCKED') {
    $resultType = 'error';  // <-- ADD THIS BLOCK
} elseif ($status === 'REPROVADA') {
    $resultType = 'dead';
} else {
    $resultType = 'error';
}
```

---

## Fix 3: /var/www/site/script.js

### 3.1 Update result event listener to count BLOCKED as errors:

In the `processPyCCNCard` function, find the `result` event listener and ensure BLOCKED results call `appendResult('error', ...)`:

```javascript
eventSource.addEventListener('result', function(e) {
    try {
        const data = JSON.parse(e.data);
        
        // ... existing code ...
        
        // Update dashboard counters - IMPORTANT FIX
        if (data.result === 'live') {
            appendResult('live', data.message || data.card);
        } else if (data.result === 'dead') {
            appendResult('dead', data.message || data.card);
        } else {
            // data.result === 'error' includes BLOCKED status
            appendResult('error', data.message || data.card);  // <-- THIS IS KEY
        }
        
    } catch (err) { console.error('Result parse error:', err); }
});
```

### 3.2 Verify appendResult function increments error counter:

Make sure this function exists and properly handles errors:
```javascript
function appendResult(type, message) {
    if (type === 'live') {
        // Update live counter
        const counter = document.getElementById('aprovadas');
        if (counter) counter.textContent = parseInt(counter.textContent || 0) + 1;
    } else if (type === 'dead') {
        // Update dead counter
        const counter = document.getElementById('reprovadas');
        if (counter) counter.textContent = parseInt(counter.textContent || 0) + 1;
    } else {
        // type === 'error' - INCREMENT ERROR COUNTER!
        const counter = document.getElementById('erros');
        if (counter) counter.textContent = parseInt(counter.textContent || 0) + 1;
    }
    
    // Update total
    const total = document.getElementById('total');
    if (total) total.textContent = parseInt(total.textContent || 0) + 1;
}
```

---

## Testing

After applying fixes:

1. Restart PHP-FPM:
   ```bash
   sudo systemctl restart php8.3-fpm
   ```

2. Clear any cached JavaScript:
   - Hard refresh browser (Ctrl+Shift+R)

3. Test with cards that trigger Gateway Blocked:
   - Counter should increment: (1/5), (2/5), (3/5), (4/5), (5/5)
   - After 5/5, browser should restart
   - Dashboard error counter should increment for BLOCKED results

---

## Expected Output After Fix

```
REPROVADA ➔ 379364015255311|07|2027|4898 ➔ Gateway Blocked (1/5) ➔ (14.7s)
REPROVADA ➔ 379364015251468|07|2027|7873 ➔ Gateway Blocked (2/5) ➔ (14.4s)
REPROVADA ➔ 379364015258620|07|2027|8366 ➔ Gateway Blocked (3/5) ➔ (40.9s)
REPROVADA ➔ 379364015253340|07|2027|4997 ➔ Gateway Blocked (4/5) ➔ (38.0s)
REPROVADA ➔ 379364015257168|07|2027|4857 ➔ Gateway Blocked (5/5) ➔ (14.8s)
[!] 5 consecutive Gateway Blocked! Restarting browser...
[*] Setting up new browser session...
REPROVADA ➔ 379364015252458|07|2027|9731 ➔ Gateway Blocked (1/5) ➔ (17.4s)  <-- Counter starts fresh after restart
```

And when Rate Limited:
```
! BLOCKED ➔ 379364015255311|07|2027|4898 ➔ Rate Limited ➔ (40.9s)
[!] Rate Limited! Restarting browser for new IP...
```

Dashboard should show:
- **Errors: X** (where X = number of BLOCKED results)
