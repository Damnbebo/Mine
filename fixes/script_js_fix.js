/**
 * script.js - Fix for BLOCKED results not being counted as errors
 * 
 * ISSUES FIXED:
 * 1. BLOCKED results (Rate Limited) not incrementing error counter
 * 2. Gateway Blocked count display in status
 * 
 * UPDATE the result event listener in /var/www/site/script.js
 */

// === FIX: Update the result event listener in processPyCCNCard ===
// Find the eventSource.addEventListener('result', ...) section and update it:

/*
FIND THIS in your script.js processPyCCNCard function:

eventSource.addEventListener('result', function(e) {
    try {
        resultReceived = true;
        const data = JSON.parse(e.data);
        finalResult = data;
        const resultType = data.result === 'live' ? 'success' : 'error';
        addBrainTreeStatusMessage('📋 Result: ' + (data.message || data.result), resultType);
        ...
    } catch (err) { console.error('Result parse error:', err); }
});

REPLACE WITH:
*/

const RESULT_LISTENER_FIX = `
eventSource.addEventListener('result', function(e) {
    try {
        resultReceived = true;
        const data = JSON.parse(e.data);
        finalResult = data;
        
        // Determine display type based on result
        let resultType = 'info';
        let statusEmoji = '📋';
        
        if (data.result === 'live') {
            resultType = 'success';
            statusEmoji = '✅';
            playLiveSound();
        } else if (data.result === 'dead') {
            resultType = 'error';
            statusEmoji = '❌';
        } else if (data.result === 'error') {
            // This includes BLOCKED status
            resultType = 'error';
            statusEmoji = '⚠️';
        }
        
        // Check for Gateway Blocked with counter
        if (data.status === 'BLOCKED' || (data.reason && data.reason.includes('Rate Limited'))) {
            resultType = 'warning';
            statusEmoji = '🚫';
            addBrainTreeStatusMessage(statusEmoji + ' BLOCKED: ' + (data.reason || 'Rate Limited'), 'warning');
        } else if (data.reason && data.reason.includes('Gateway Blocked')) {
            // Show gateway blocked count
            addBrainTreeStatusMessage('⚠️ ' + data.reason, 'warning');
        } else {
            addBrainTreeStatusMessage(statusEmoji + ' Result: ' + (data.message || data.result), resultType);
        }

        // Batch mode: Update lista and counters
        if (data.index && data.total) {
            addBrainTreeStatusMessage('📊 Progress: ' + data.index + '/' + data.total, 'info');

            // Remove processed card from textarea
            const listaElement = document.getElementById('cardListInput');
            if (listaElement && data.card) {
                const lines = listaElement.value.split('\\n');
                const newLines = lines.filter(l => l.trim() !== data.card.trim());
                listaElement.value = newLines.join('\\n');
            }
            
            // Update dashboard counters correctly
            // BLOCKED and ERROR both count as errors
            if (data.result === 'live') {
                appendResult('live', data.message || data.card);
            } else if (data.result === 'dead') {
                appendResult('dead', data.message || data.card);
            } else {
                // data.result === 'error' (includes BLOCKED)
                appendResult('error', data.message || data.card);
            }
        }
        
        // Show warning if gateway blocked is accumulating
        if (data.gatewayBlockedCount && data.gatewayBlockedCount > 0) {
            addBrainTreeStatusMessage('⚠️ Gateway Blocked: ' + data.gatewayBlockedCount + '/5 - Will refresh after 5', 'warning');
        }
        
    } catch (err) { 
        console.error('Result parse error:', err); 
    }
});
`;

// === FIX 2: Update addBrainTreeStatusMessage to handle 'warning' type ===
/*
Make sure your addBrainTreeStatusMessage function handles the 'warning' type:
*/

const ADD_STATUS_MESSAGE_FIX = `
function addBrainTreeStatusMessage(message, type) {
    type = type || 'info';
    if (!braintreeStatusContent) return;

    // Auto-expand if minimized and important message
    if (isMinimized && (type === 'success' || type === 'error' || type === 'warning')) {
        toggleMinimize();
    }

    const timestamp = new Date().toLocaleTimeString();
    const msgDiv = document.createElement('div');
    
    // Define colors for each type
    let bgColor, borderColor;
    switch(type) {
        case 'success':
            bgColor = 'rgba(74, 222, 128, 0.15)';
            borderColor = '#4ade80';
            break;
        case 'error':
            bgColor = 'rgba(239, 68, 68, 0.15)';
            borderColor = '#ef4444';
            break;
        case 'warning':
            bgColor = 'rgba(251, 191, 36, 0.15)';
            borderColor = '#fbbf24';
            break;
        default: // info
            bgColor = 'rgba(59, 130, 246, 0.15)';
            borderColor = '#3b82f6';
    }
    
    msgDiv.style.cssText = 'padding: 8px 12px; margin-bottom: 8px; background: ' + bgColor + '; border-radius: 8px; border-left: 3px solid ' + borderColor + ';';
    msgDiv.innerHTML = '<span style="color: #94a3b8; font-size: 11px;">[' + timestamp + ']</span> ' + message;
    braintreeStatusContent.appendChild(msgDiv);
    braintreeStatusContent.scrollTop = braintreeStatusContent.scrollHeight;
}
`;

// === FIX 3: Update appendResult function to properly increment counters ===
/*
Make sure the appendResult function exists and increments counters:
*/

const APPEND_RESULT_FIX = `
function appendResult(type, message) {
    // Increment the appropriate counter
    if (type === 'live') {
        // Update live counter
        const liveCounter = document.getElementById('aprovadas') || document.querySelector('.live-count');
        if (liveCounter) {
            let count = parseInt(liveCounter.textContent) || 0;
            liveCounter.textContent = count + 1;
        }
        
        // Add to live results container
        const liveContainer = document.getElementById('liveResults') || document.querySelector('.live-results');
        if (liveContainer) {
            const div = document.createElement('div');
            div.className = 'result-item live';
            div.textContent = message;
            liveContainer.appendChild(div);
        }
    } else if (type === 'dead') {
        // Update dead counter
        const deadCounter = document.getElementById('reprovadas') || document.querySelector('.dead-count');
        if (deadCounter) {
            let count = parseInt(deadCounter.textContent) || 0;
            deadCounter.textContent = count + 1;
        }
        
        // Add to dead results container
        const deadContainer = document.getElementById('deadResults') || document.querySelector('.dead-results');
        if (deadContainer) {
            const div = document.createElement('div');
            div.className = 'result-item dead';
            div.textContent = message;
            deadContainer.appendChild(div);
        }
    } else {
        // type === 'error' - THIS IS THE KEY FIX
        // Update error counter
        const errorCounter = document.getElementById('erros') || document.querySelector('.error-count');
        if (errorCounter) {
            let count = parseInt(errorCounter.textContent) || 0;
            errorCounter.textContent = count + 1;  // INCREMENT ERROR COUNT
        }
        
        // Add to error results container
        const errorContainer = document.getElementById('errorResults') || document.querySelector('.error-results');
        if (errorContainer) {
            const div = document.createElement('div');
            div.className = 'result-item error';
            div.textContent = message;
            errorContainer.appendChild(div);
        }
    }
    
    // Update total processed
    const totalCounter = document.getElementById('total') || document.querySelector('.total-count');
    if (totalCounter) {
        let count = parseInt(totalCounter.textContent) || 0;
        totalCounter.textContent = count + 1;
    }
}
`;

console.log("Script.js fixes created. Apply these changes to /var/www/site/script.js");
