
// Process card through PyCCN with real-time status (SSE)
async function processPyCCNCard(card, method) {
    return new Promise(function(resolve, reject) {
        // Close any existing EventSource connection
        if (activeEventSource) {
            try { activeEventSource.close(); } catch(e) {}
            activeEventSource = null;
        }
        
        // Show status display with PyCCN title
        showBrainTreeStatus('pyccn');
        clearBrainTreeStatus();
        addBrainTreeStatus('🐍 Connecting to PyCCN...', 'info');
        
        const eventSource = new EventSource('pyccn_stream.php?card=' + encodeURIComponent(card));
        activeEventSource = eventSource;  // Track for cleanup
        let result = null;
        let lastMessageTime = Date.now();
        
        eventSource.onopen = function() {
            lastMessageTime = Date.now();
            console.log('[PyCCN] Connection opened');
            addBrainTreeStatus('├─ ✓ Connected to server', 'progress');
        };
        
        eventSource.addEventListener('status', function(e) {
            lastMessageTime = Date.now();
            console.log('[PyCCN] Status event received:', e.data);
            try {
                const data = JSON.parse(e.data);
                addBrainTreeStatus(data.message, 'progress');
            } catch (err) {
                console.error('[PyCCN] Error parsing status:', err);
            }
        });
        
        eventSource.addEventListener('result', function(e) {
            lastMessageTime = Date.now();
            console.log('[PyCCN] Result event received:', e.data);
            try {
                const data = JSON.parse(e.data);
                result = data;
            
                // Show full result with details
                if (data.result === 'live') {
                    // Play live sound immediately
                    const liveSoundEl = document.getElementById('liveSound');
                    if (liveSoundEl) {
                        liveSoundEl.pause();
                        liveSoundEl.currentTime = 0;
                        liveSoundEl.play().catch(function(e) { console.log("Audio play error:", e); });
                    }
                }
            
                // Display formatted result with full details
                if (braintreeStatusContent) {
                    braintreeStatusContent.innerHTML = formatFWAVSResult(data);
                }
            } catch (err) {
                console.error('[PyCCN] Error parsing result:', err);
            }
        });
        
        eventSource.addEventListener('done', function(e) {
            console.log('[PyCCN] Done event received:', e.data);
            eventSource.close();
            activeEventSource = null;
            
            // Keep result visible
            hideStatusTimeout = setTimeout(function() {
                hideBrainTreeStatus();
            }, 4000);
            
            if (result) {
                resolve(result);
            } else {
                resolve({
                    card: card,
                    result: 'error',
                    reason: 'No Response',
                    message: 'Error ➔ ' + card + ' ➔ No response ➔ @FWChecker'
                });
            }
        });
        
        eventSource.onerror = function(e) {
            console.log('[PyCCN] EventSource error, readyState:', eventSource.readyState);
            // Let done event or timeout handle it
        };
        
        // Timeout after 3 minutes for PyCCN (Playwright is slower)
        setTimeout(function() {
            if (eventSource.readyState !== EventSource.CLOSED && !result) {
                eventSource.close();
                activeEventSource = null;
                hideBrainTreeStatus();
                resolve({
                    card: card,
                    result: 'error',
                    message: 'Error ➔ ' + card + ' ➔ Timeout ➔ @FWChecker'
                });
            }
        }, 180000);
    });
}
