<?php
/**
 * stream_batch.php - Fix for BLOCKED status not being counted as errors
 * 
 * ISSUES FIXED:
 * 1. BLOCKED results (Rate Limited) not being counted as errors on dashboard
 * 2. Parse both "BLOCKED" and "REPROVADA" correctly
 * 
 * UPDATE the parsing section in /var/www/site/stream/PyCCN/stream_batch.php
 */

// === FIX: Update the output parsing section ===
// Find the section that parses bot output and update it like this:

/*
FIND THIS PATTERN in your stream_batch.php:
    if (preg_match('/([✓✗!]) (APROVADA|REPROVADA|ERROR) ➔ (.+)/', $line, $m)) {

REPLACE WITH:
*/

// Updated parsing that handles BLOCKED status
$parsing_logic = <<<'PHP'
            // Parse final result line - include BLOCKED status
            if (preg_match('/([✓✗!]) (APROVADA|REPROVADA|ERROR|BLOCKED) ➔ (.+?) ➔ (.+?) ➔ ([\d.]+)s/', $line, $m)) {
                $symbol = $m[1];
                $status = $m[2];
                $card = trim($m[3]);
                $reason = sanitizeError(trim($m[4]));
                $time = floatval($m[5]);
                
                $cardIndex++;
                
                // Determine result type
                // BLOCKED should be counted as ERROR for dashboard
                if ($status === 'APROVADA') {
                    $resultType = 'live';
                } elseif ($status === 'BLOCKED') {
                    // BLOCKED = Rate Limited or Gateway issue = count as error
                    $resultType = 'error';
                } elseif ($status === 'REPROVADA') {
                    $resultType = 'dead';
                } else {
                    $resultType = 'error';
                }
                
                // Handle Gateway Blocked with counter (e.g., "Gateway Blocked (3/5)")
                $gatewayCount = 0;
                if (preg_match('/Gateway Blocked \((\d)\/5\)/', $reason, $gcMatch)) {
                    $gatewayCount = intval($gcMatch[1]);
                }
                
                sendSSE('result', [
                    'card' => $card,
                    'result' => $resultType,
                    'status' => $status,  // Include original status for frontend
                    'reason' => $reason,
                    'time' => $time,
                    'index' => $cardIndex,
                    'total' => $totalCards,
                    'gatewayBlockedCount' => $gatewayCount,
                    'message' => "{$status} ➔ {$card} ➔ {$reason} ➔ ({$time}s) ➔ @FWChecker"
                ]);
                
                $results[] = [
                    'card' => $card,
                    'status' => $status,
                    'result' => $resultType,
                    'reason' => $reason
                ];
                
                // Process credits based on result
                if ($resultType === 'live') {
                    // Deduct 6 credits for live
                    // ... existing credit logic
                } elseif ($resultType === 'dead') {
                    // Deduct 1 credit for dead
                    // ... existing credit logic
                }
                // Note: errors (including BLOCKED) don't deduct credits
                
                continue;
            }
            
            // Also parse simpler format without time
            if (preg_match('/([✓✗!]) (APROVADA|REPROVADA|ERROR|BLOCKED) ➔ (.+?) ➔ (.+)/', $line, $m)) {
                $symbol = $m[1];
                $status = $m[2];
                $card = trim($m[3]);
                $reason = sanitizeError(trim($m[4]));
                
                $cardIndex++;
                
                // Same logic as above
                if ($status === 'APROVADA') {
                    $resultType = 'live';
                } elseif ($status === 'BLOCKED') {
                    $resultType = 'error';
                } elseif ($status === 'REPROVADA') {
                    $resultType = 'dead';
                } else {
                    $resultType = 'error';
                }
                
                // Extract time if present in reason
                $time = 0;
                if (preg_match('/([\d.]+)s$/', $reason, $timeMatch)) {
                    $time = floatval($timeMatch[1]);
                }
                
                sendSSE('result', [
                    'card' => $card,
                    'result' => $resultType,
                    'status' => $status,
                    'reason' => $reason,
                    'time' => $time,
                    'index' => $cardIndex,
                    'total' => $totalCards,
                    'message' => "{$status} ➔ {$card} ➔ {$reason} ➔ @FWChecker"
                ]);
                
                $results[] = [
                    'card' => $card,
                    'status' => $status,
                    'result' => $resultType,
                    'reason' => $reason
                ];
                
                continue;
            }
PHP;

echo "Stream batch fix - update the parsing logic in stream_batch.php\n";
?>
