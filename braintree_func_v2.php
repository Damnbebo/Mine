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
        
        // Extract and normalize reason from response
        $reason = 'Decline'; // Default for declined
        if (preg_match('/(?:APROVADA|REPROVADA).*?➔\s*([^➔]+?)\s*➔/', $responseText, $matches)) {
            $rawReason = trim(strip_tags($matches[1]));
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
            } elseif (stripos($rawReason, 'Charged') !== false) {
                $reason = 'Charged';
            } elseif (stripos($rawReason, 'payment could not') !== false || stripos($rawReason, 'try again') !== false) {
                $reason = 'Decline';
            } elseif (!empty($rawReason) && $rawReason !== 'Unknown') {
                $reason = $rawReason;
            }
        } elseif (preg_match('/(CVV|Insufficient|Do Not Honor|Fraud|Invalid|Declined|Charged)/i', $responseText, $matches)) {
            $match = $matches[1];
            if (stripos($match, 'CVV') !== false) {
                $reason = 'CVV Decline';
            } else {
                $reason = $match;
            }
        }
        
        // For approved cards, ensure proper reason
        if ($isApproved && $reason === 'Decline') {
            $reason = 'CVV Decline';
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
