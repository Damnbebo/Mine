function processBrainTreeCCNGate($card, $startTime) {
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
        
        // Use the runner script (handles escaping properly)
        $runnerScript = __DIR__ . '/braintree_runner.php';
        $escapedCard = escapeshellarg($card);
        $command = "php " . escapeshellarg($runnerScript) . " " . $escapedCard . " 2>&1";
        
        // Execute the command
        $responseText = shell_exec($command);
        
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
        $isApproved = (stripos($responseText, 'APROVADA') !== false);
        $isDeclined = (stripos($responseText, 'REPROVADA') !== false);
        
        // Extract reason from response
        $reason = 'Unknown';
        if (preg_match('/(?:APROVADA|REPROVADA).*?➔\s*([^➔]+?)\s*➔/', $responseText, $matches)) {
            $reason = trim(strip_tags($matches[1]));
        } elseif (preg_match('/(?:CVV|Insufficient|Do Not Honor|Fraud|Invalid|Declined)[^<]*/i', $responseText, $matches)) {
            $reason = trim(strip_tags($matches[0]));
        }
        
        if ($isApproved) {
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
