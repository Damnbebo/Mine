
/**
 * Process PyCCN (Dashlane) Gate
 * Uses Python Playwright bot for card checking
 */
function processPyCCNGate($card, $startTime) {
    $responseTime = 0;
    
    try {
        // Parse card details
        $parts = explode('|', $card);
        if (count($parts) < 4) {
            return [
                'card' => $card,
                'result' => 'error',
                'message' => "Error ➔ {$card} ➔ Invalid card format ➔ @FWChecker"
            ];
        }
        
        // Use the runner script
        $runnerScript = __DIR__ . '/pyccn_runner.php';
        $escapedCard = escapeshellarg($card);
        $command = "php " . escapeshellarg($runnerScript) . " " . $escapedCard . " 2>&1";
        
        // Use proc_open for better control
        $descriptorspec = [
            0 => ['pipe', 'r'],
            1 => ['pipe', 'w'],
            2 => ['pipe', 'w']
        ];
        
        $process = proc_open($command, $descriptorspec, $pipes, __DIR__);
        
        if (!is_resource($process)) {
            return [
                'card' => $card,
                'result' => 'error',
                'message' => "Error ➔ {$card} ➔ Failed to start process ➔ @FWChecker"
            ];
        }
        
        // Set timeout (2 minutes max)
        $timeout = 120;
        $startProcTime = time();
        $responseText = '';
        
        stream_set_blocking($pipes[1], false);
        
        while (true) {
            $status = proc_get_status($process);
            
            $chunk = fread($pipes[1], 8192);
            if ($chunk) {
                $responseText .= $chunk;
            }
            
            if (!$status['running']) {
                $remaining = stream_get_contents($pipes[1]);
                if ($remaining) {
                    $responseText .= $remaining;
                }
                break;
            }
            
            if ((time() - $startProcTime) > $timeout) {
                proc_terminate($process);
                return [
                    'card' => $card,
                    'result' => 'error',
                    'message' => "Error ➔ {$card} ➔ Timeout ➔ @FWChecker"
                ];
            }
            
            usleep(50000);
        }
        
        fclose($pipes[0]);
        fclose($pipes[1]);
        fclose($pipes[2]);
        proc_close($process);
        
        $responseTime = round(microtime(true) - $startTime, 2);
        
        if (empty($responseText)) {
            return [
                'card' => $card,
                'result' => 'error',
                'message' => "Error ➔ {$card} ➔ API returned empty response ➔ ({$responseTime}s) ➔ @FWChecker"
            ];
        }
        
        // Parse response
        $originalResponse = $responseText;
        
        // Check for APROVADA (live card)
        $isApproved = (stripos($responseText, 'APROVADA') !== false) || 
                      (stripos($responseText, '✅ LIVE') !== false);
        $isDeclined = (stripos($responseText, 'REPROVADA') !== false) || 
                      (stripos($responseText, '❌ DEAD') !== false);
        $isError = (stripos($responseText, '⚠️ ERROR') !== false);
        
        // Parse JSON result if available
        $jsonData = null;
        if (preg_match('/JSON:(\{.*\})/', $responseText, $jsonMatch)) {
            $jsonData = json_decode($jsonMatch[1], true);
        }
        
        // Extract reason
        $reason = 'Decline';
        if ($jsonData && isset($jsonData['reason'])) {
            $reason = $jsonData['reason'];
        } elseif (preg_match('/➔\s*([^➔]+?)\s*➔/', $responseText, $matches)) {
            $rawReason = trim(strip_tags($matches[1]));
            if (!empty($rawReason) && $rawReason !== 'Unknown') {
                // Normalize common reasons
                if (stripos($rawReason, 'CVV') !== false) {
                    $reason = 'CVV Decline';
                } elseif (stripos($rawReason, 'Insufficient') !== false) {
                    $reason = 'Insufficient Funds';
                } elseif (stripos($rawReason, 'Do Not Honor') !== false) {
                    $reason = 'Do Not Honor';
                } elseif (stripos($rawReason, 'Fraud') !== false) {
                    $reason = 'Fraud';
                } elseif (stripos($rawReason, 'Invalid') !== false) {
                    $reason = 'Invalid Card';
                } elseif (stripos($rawReason, '3DS') !== false || stripos($rawReason, '3D') !== false) {
                    $reason = '3DS Required';
                } elseif (stripos($rawReason, 'Blocked') !== false) {
                    $reason = 'Blocked';
                } else {
                    $reason = $rawReason;
                }
            }
        }
        
        if ($isApproved) {
            if ($reason === 'Decline') {
                $reason = 'CVV Match';
            }
            $message = "APROVADA ➔ {$card} ➔ {$reason} ➔ ({$responseTime}s) ➔ @FWChecker";
            return [
                'card' => $card,
                'result' => 'live',
                'message' => $message,
                'full_response' => trim($originalResponse)
            ];
        } elseif ($isDeclined) {
            $message = "REPROVADA ➔ {$card} ➔ {$reason} ➔ ({$responseTime}s) ➔ @FWChecker";
            return [
                'card' => $card,
                'result' => 'dead',
                'message' => $message
            ];
        } elseif ($isError) {
            return [
                'card' => $card,
                'result' => 'error',
                'message' => "Error ➔ {$card} ➔ {$reason} ➔ ({$responseTime}s) ➔ @FWChecker"
            ];
        }
        
        // Unknown response
        return [
            'card' => $card,
            'result' => 'error',
            'message' => "Unknown Response ➔ {$card} ➔ ({$responseTime}s) ➔ @FWChecker",
            'raw_response' => substr($responseText, 0, 500)
        ];
        
    } catch (Exception $e) {
        $responseTime = round(microtime(true) - $startTime, 2);
        return [
            'card' => $card,
            'result' => 'error',
            'message' => "Error ➔ {$card} ➔ " . $e->getMessage() . " ➔ ({$responseTime}s) ➔ @FWChecker"
        ];
    }
}
