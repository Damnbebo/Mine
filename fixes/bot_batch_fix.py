#!/usr/bin/env python3
"""
bot_batch.py - Gateway Blocked Counter Fix

ISSUES FIXED:
1. Gateway blocked counter was resetting incorrectly between cards
2. BLOCKED status needs consistent output format for frontend counting

CHANGES TO MAKE IN /opt/dashlane/bot_batch.py:

Find the process_batch method and update the blocking logic:
"""

# === FIX 1: Ensure gateway_blocked_count is initialized in __init__ ===
# In the __init__ method, add:
"""
def __init__(self):
    self.browser = None
    self.context = None
    self.page = None
    self.session_active = False
    self.gateway_blocked_count = 0  # <-- Make sure this exists
"""

# === FIX 2: Update process_batch method blocking logic ===
# The key fix is in how we handle GATEWAY_BLOCKED vs RATE_LIMITED

PROCESS_BATCH_BLOCKING_LOGIC = '''
    def process_batch(self, cards_list):
        """Process multiple cards, reusing session when possible"""
        results = []
        remaining = list(cards_list)
        
        while remaining:
            # Setup browser if needed
            if not self.session_active:
                print("[*] Setting up new browser session...")
                if not self.setup_browser():
                    print("[!] Failed to setup browser")
                    for card in remaining:
                        results.append({
                            'card': card,
                            'status': 'ERROR',
                            'reason': 'Browser setup failed',
                            'time': 0
                        })
                    break
                
                print("[*] Initializing session...")
                if not self.init_session():
                    print("[!] Failed to init session")
                    self.close_browser()
                    for card in remaining:
                        results.append({
                            'card': card,
                            'status': 'ERROR',
                            'reason': 'Session init failed',
                            'time': 0
                        })
                    break
                
                self.session_active = True
                # DO NOT reset gateway_blocked_count here - let it persist across restarts
                # Only reset when we get a non-blocked result
            
            # Process first card in remaining
            card_str = remaining[0]
            card_index = len(cards_list) - len(remaining) + 1
            total_cards = len(cards_list)
            
            print(f"[CARD {card_index}/{total_cards}] Processing: {card_str[:4]}****")
            
            result = self.process_card(card_str)
            result['index'] = card_index
            result['total'] = total_cards
            
            # Handle RATE_LIMITED - immediate restart with new IP
            if result['status'] == 'RATE_LIMITED':
                # Print as BLOCKED for consistent frontend parsing
                print(f"! BLOCKED ➔ {card_str} ➔ Rate Limited ➔ {result.get('time', 0):.1f}s")
                
                # Rate limited = immediate restart, but DON'T reset gateway counter
                # Rate limit is different from gateway blocked
                print(f"[!] Rate Limited! Restarting browser for new IP...")
                self.session_active = False
                self.close_browser()
                
                # Don't add to results yet, retry this card with new session
                continue
            
            # Handle GATEWAY_BLOCKED - count consecutively
            if result['status'] == 'GATEWAY_BLOCKED':
                self.gateway_blocked_count += 1
                current_count = self.gateway_blocked_count
                
                # Print with count for user feedback
                print(f"✗ REPROVADA ➔ {card_str} ➔ Gateway Blocked ({current_count}/5) ➔ {result.get('time', 0):.1f}s")
                
                if current_count >= 5:
                    print(f"[!] 5 consecutive Gateway Blocked! Restarting browser for new IP...")
                    self.gateway_blocked_count = 0  # Reset ONLY after triggering restart
                    self.session_active = False
                    self.close_browser()
                    
                    # Don't add to results yet, retry this card with new session
                    continue
                else:
                    # Convert to REPROVADA for results, but card is processed (move to next)
                    result['status'] = 'REPROVADA'
                    result['reason'] = f"Gateway Blocked ({current_count}/5)"
                    remaining.pop(0)
                    results.append(result)
                    continue
            
            # Handle CHARGED - restart session (success but need fresh session)
            if result['status'] == 'CHARGED':
                print(f"✓ APROVADA ➔ {card_str} ➔ {result.get('reason', 'Charged')} ➔ {result.get('time', 0):.1f}s")
                self.gateway_blocked_count = 0  # Reset on success
                remaining.pop(0)
                results.append(result)
                
                # Charged = need new session
                print("[*] Card charged, starting new session...")
                self.session_active = False
                self.close_browser()
                continue
            
            # Normal result - remove from remaining and reset counter
            remaining.pop(0)
            results.append(result)
            
            # Reset gateway blocked counter on ANY non-blocked result
            if result['status'] in ['APROVADA', 'REPROVADA', 'ERROR']:
                self.gateway_blocked_count = 0
            
            # Print result
            status = result['status']
            reason = result.get('reason', 'Unknown')
            time_taken = result.get('time', 0)
            
            if status == 'APROVADA':
                print(f"✓ APROVADA ➔ {card_str} ➔ {reason} ➔ {time_taken:.1f}s")
            elif status == 'REPROVADA':
                print(f"✗ REPROVADA ➔ {card_str} ➔ {reason} ➔ {time_taken:.1f}s")
            else:
                print(f"! ERROR ➔ {card_str} ➔ {reason} ➔ {time_taken:.1f}s")
        
        # Cleanup
        self.close_browser()
        
        return results
'''

# === FIX 3: Update parse_response to distinguish RATE_LIMITED vs GATEWAY_BLOCKED ===
PARSE_RESPONSE_FIX = '''
def parse_response(data):
    """Parse gateway response to determine card status"""
    if not data:
        return {'status': 'ERROR', 'reason': 'No response data'}
    
    # Check for success first
    if data.get('success') == True:
        return {'status': 'CHARGED', 'reason': 'Card Charged'}
    
    error_type = data.get('error_type', '').lower()
    message = data.get('message', '').lower()
    
    # RATE LIMITED - needs immediate browser restart
    if 'rate' in error_type or 'rate limit' in message or 'rate_limit' in message:
        return {'status': 'RATE_LIMITED', 'reason': 'Rate Limited'}
    
    # GATEWAY BLOCKED - count consecutively, restart after 5
    if error_type == 'gateway.blocked' or 'blocked' in message:
        return {'status': 'GATEWAY_BLOCKED', 'reason': 'Gateway Blocked'}
    
    # Risky transaction - treat as gateway blocked
    if 'risky' in message:
        return {'status': 'GATEWAY_BLOCKED', 'reason': 'Transaction Risky'}
    
    # Card declined - normal dead
    if 'declined' in message or 'decline' in message or error_type == 'card.declined':
        return {'status': 'REPROVADA', 'reason': 'Card Declined'}
    
    # Insufficient funds
    if 'insufficient' in message:
        return {'status': 'REPROVADA', 'reason': 'Insufficient Funds'}
    
    # CVV issues
    if 'cvv' in message or 'cvc' in message or 'security code' in message:
        return {'status': 'REPROVADA', 'reason': 'CVV Mismatch'}
    
    # Invalid card
    if 'invalid' in message and 'card' in message:
        return {'status': 'REPROVADA', 'reason': 'Invalid Card'}
    
    # Expired
    if 'expired' in message:
        return {'status': 'REPROVADA', 'reason': 'Card Expired'}
    
    # Do not honor
    if 'do not honor' in message or 'honor' in message:
        return {'status': 'REPROVADA', 'reason': 'Do Not Honor'}
    
    # 3DS required
    if '3ds' in message or '3d secure' in message or 'authentication' in message:
        return {'status': 'REPROVADA', 'reason': '3DS Required'}
    
    # Generic failure with error_type
    if data.get('success') == False and error_type:
        return {'status': 'REPROVADA', 'reason': error_type.replace('.', ' ').title()}
    
    # Unknown
    return {'status': 'ERROR', 'reason': 'Unknown Response'}
'''

print("Bot batch fix file created. Apply these changes to /opt/dashlane/bot_batch.py")
