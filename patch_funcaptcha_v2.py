#!/usr/bin/env python3
"""
Patch main2.py to:
1. Add SolveCaptcha API support for FunCaptcha (PRIMARY)
2. Fall back to 2captcha for FunCaptcha
3. Keep AntiCaptcha for AWS WAF / other captcha types
"""

import re

# Read the file
with open('/home/ubuntu/amazon-bot/main2.py', 'r', encoding='utf-8') as f:
    content = f.read()

# ============================================
# 1. Add SolveCaptcha API key constant near the top with other API keys
# ============================================
old_api_keys = 'TWOCAPTCHA_API_KEY = "1391eb71164c1c34c710a23676cf48c4"'

new_api_keys = '''TWOCAPTCHA_API_KEY = "1391eb71164c1c34c710a23676cf48c4"
SOLVECAPTCHA_API_KEY = "CAP-AEA04ED2D09FCE924BC35BD1999D2983B820ED369FA901AF851CC2F7C6301681"'''

if old_api_keys in content and 'SOLVECAPTCHA_API_KEY' not in content:
    content = content.replace(old_api_keys, new_api_keys)
    print("Added SolveCaptcha API key")
elif 'SOLVECAPTCHA_API_KEY' in content:
    print("SolveCaptcha API key already exists")
else:
    print("WARNING: Could not find TWOCAPTCHA_API_KEY to add SolveCaptcha key")

# ============================================
# 2. Add SolveCaptcha FunCaptcha solver function
# ============================================
solvecaptcha_function = '''

# ============================================
# SOLVECAPTCHA FunCaptcha Solver (PRIMARY for FunCaptcha)
# ============================================
async def solve_funcaptcha_solvecaptcha(public_key: str, page_url: str, api_subdomain: str = None, 
                                        data_blob: str = None, user_agent: str = None):
    """
    Solve FunCaptcha using SolveCaptcha.com API (primary solver)
    
    API Documentation: https://solvecaptcha.com/captcha-solver/funcaptcha-solver-bypass
    """
    import requests
    import time
    
    if not SOLVECAPTCHA_API_KEY:
        print("**SolveCaptcha: No API key configured**")
        return None
    
    try:
        print(f"**SolveCaptcha: Sending FunCaptcha request...**")
        
        params = {
            'key': SOLVECAPTCHA_API_KEY,
            'method': 'funcaptcha',
            'publickey': public_key,
            'pageurl': page_url,
            'json': '1'
        }
        
        if api_subdomain:
            if not api_subdomain.startswith('http'):
                params['surl'] = f"https://{api_subdomain}"
            else:
                params['surl'] = api_subdomain
        
        if data_blob:
            params['data[blob]'] = data_blob
        
        if user_agent:
            params['userAgent'] = user_agent
        
        print(f"**SolveCaptcha params: pk={public_key[:20]}... surl={params.get('surl', 'N/A')[:40] if params.get('surl') else 'N/A'}**")
        
        response = requests.post('https://api.solvecaptcha.com/in.php', data=params, timeout=30)
        result = response.json()
        
        if result.get('status') != 1:
            error = result.get('request', 'Unknown error')
            print(f"**SolveCaptcha submit error: {error}**")
            return None
        
        captcha_id = result.get('request')
        print(f"**SolveCaptcha task created: {captcha_id}**")
        
        max_wait = 120
        start_time = time.time()
        poll_interval = 5
        
        while time.time() - start_time < max_wait:
            await asyncio.sleep(poll_interval)
            elapsed = int(time.time() - start_time)
            print(f"**SolveCaptcha polling... ({elapsed}s)**")
            
            try:
                res = requests.get(
                    'https://api.solvecaptcha.com/res.php',
                    params={'key': SOLVECAPTCHA_API_KEY, 'action': 'get', 'id': captcha_id, 'json': '1'},
                    timeout=30
                )
                result = res.json()
                
                if result.get('status') == 1:
                    token = result.get('request')
                    print(f"**SolveCaptcha SUCCESS! Token received ({len(token)} chars)**")
                    return token
                
                request_status = result.get('request', '')
                if request_status == 'CAPCHA_NOT_READY':
                    poll_interval = min(poll_interval + 2, 10)
                    continue
                elif 'ERROR' in str(request_status):
                    print(f"**SolveCaptcha error: {request_status}**")
                    return None
            except Exception as poll_err:
                print(f"**SolveCaptcha poll error: {poll_err}**")
        
        print(f"**SolveCaptcha timeout after {max_wait}s**")
        return None
        
    except Exception as e:
        print(f"**SolveCaptcha exception: {e}**")
        return None


async def solve_funcaptcha_2captcha_direct(public_key: str, page_url: str, api_subdomain: str = None,
                                           data_blob: str = None, user_agent: str = None):
    """
    Solve FunCaptcha using 2Captcha API (fallback solver)
    """
    import requests
    import time
    
    if not TWOCAPTCHA_API_KEY:
        print("**2Captcha: No API key configured**")
        return None
    
    try:
        print(f"**2Captcha: Sending FunCaptcha request...**")
        
        params = {
            'key': TWOCAPTCHA_API_KEY,
            'method': 'funcaptcha',
            'publickey': public_key,
            'pageurl': page_url,
            'json': '1'
        }
        
        if api_subdomain:
            if not api_subdomain.startswith('http'):
                params['surl'] = f"https://{api_subdomain}"
            else:
                params['surl'] = api_subdomain
        
        if data_blob:
            params['data[blob]'] = data_blob
        
        if user_agent:
            params['userAgent'] = user_agent
        
        print(f"**2Captcha params: pk={public_key[:20]}...**")
        
        response = requests.post('https://2captcha.com/in.php', data=params, timeout=30)
        result = response.json()
        
        if result.get('status') != 1:
            error = result.get('request', 'Unknown error')
            print(f"**2Captcha submit error: {error}**")
            return None
        
        captcha_id = result.get('request')
        print(f"**2Captcha task created: {captcha_id}**")
        
        max_wait = 120
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            await asyncio.sleep(10)
            elapsed = int(time.time() - start_time)
            print(f"**2Captcha polling... ({elapsed}s)**")
            
            try:
                res = requests.get(
                    f'https://2captcha.com/res.php?key={TWOCAPTCHA_API_KEY}&action=get&id={captcha_id}&json=1',
                    timeout=30
                )
                result = res.json()
                
                if result.get('status') == 1:
                    token = result.get('request')
                    print(f"**2Captcha SUCCESS! Token received ({len(token)} chars)**")
                    return token
                
                request_status = result.get('request', '')
                if request_status == 'CAPCHA_NOT_READY':
                    continue
                elif 'ERROR' in str(request_status):
                    print(f"**2Captcha error: {request_status}**")
                    return None
            except Exception as poll_err:
                print(f"**2Captcha poll error: {poll_err}**")
        
        print(f"**2Captcha timeout after {max_wait}s**")
        return None
        
    except Exception as e:
        print(f"**2Captcha exception: {e}**")
        return None


async def apply_funcaptcha_token_to_page(page, token: str):
    """Apply FunCaptcha token to the page"""
    try:
        js_code = '''(token) => {
            // Try setting in fc-token input
            let fcToken = document.querySelector('#fc-token, input[name="fc-token"]');
            if (fcToken) {
                fcToken.value = token;
                console.log('Set fc-token input value');
            }
            
            // Try setting in verification-token
            let verifyToken = document.querySelector('#verification-token, input[name="verification_token"]');
            if (verifyToken) {
                verifyToken.value = token;
            }
            
            // Try setting in any hidden token field
            let hiddenTokens = document.querySelectorAll('input[type="hidden"][name*="token"]');
            hiddenTokens.forEach(input => {
                if (input.name.includes('fc') || input.name.includes('captcha') || input.name.includes('arkose')) {
                    input.value = token;
                }
            });
            
            // Try calling callback functions
            if (window.ArkoseEnforcement && window.ArkoseEnforcement.setToken) {
                window.ArkoseEnforcement.setToken(token);
            }
            
            if (window.onArkoseSuccess) {
                window.onArkoseSuccess(token);
            }
            
            // Dispatch custom event
            let event = new CustomEvent('arkose-token-received', { detail: { token: token } });
            document.dispatchEvent(event);
        }'''
        
        await page.evaluate(js_code, token)
        
        # Try to trigger in iframes
        for frame in page.frames:
            if 'arkoselabs' in frame.url or 'funcaptcha' in frame.url:
                try:
                    await frame.evaluate('''(token) => {
                        if (window.parent && window.parent.postMessage) {
                            window.parent.postMessage({ type: 'arkose-complete', token: token }, '*');
                        }
                    }''', token)
                except:
                    pass
        
        await page.wait_for_timeout(500)
        
        try:
            submit_btn = await page.query_selector('input[type="submit"], button[type="submit"], #cvf-submit-button')
            if submit_btn and await submit_btn.is_visible():
                await submit_btn.click()
                print(f"**Clicked submit after token injection**")
        except:
            pass
            
        print(f"**Token injection completed**")
        
    except Exception as e:
        print(f"**Token injection error: {e}**")
        raise

'''

# Find insertion point - after set_current_page function
insertion_marker = '''def set_current_page(page):
    """Set the current page reference for error screenshots"""
    global _current_page_ref
    _current_page_ref = page'''

if insertion_marker in content and 'async def solve_funcaptcha_solvecaptcha' not in content:
    content = content.replace(insertion_marker, insertion_marker + solvecaptcha_function)
    print("Added SolveCaptcha and 2Captcha FunCaptcha solver functions")
elif 'async def solve_funcaptcha_solvecaptcha' in content:
    print("SolveCaptcha function already exists")
else:
    print("WARNING: Could not find insertion point for SolveCaptcha function")

# ============================================
# 3. Modify solve_funcaptcha_arkose to use SolveCaptcha FIRST
# ============================================
old_anticaptcha_start = '''        if ANTICAPTCHA_API_KEY and not check_timeout():
            print(f"**📤 Enviando FunCaptcha a Anti-Captcha (timeout: {CAPTCHA_TIMEOUT_SECONDS}s)...**")'''

new_funcaptcha_solvers = '''        # ============================================
        # PRIORITY 1: Try SolveCaptcha FIRST for FunCaptcha (PRIMARY)
        # ============================================
        if SOLVECAPTCHA_API_KEY and not check_timeout():
            print(f"**🔐 PRIORITY 1: Trying SolveCaptcha for FunCaptcha...**")
            
            solvecaptcha_token = await solve_funcaptcha_solvecaptcha(
                public_key=public_key,
                page_url=current_url,
                api_subdomain=api_subdomain,
                data_blob=data_blob,
                user_agent=user_agent
            )
            
            if solvecaptcha_token:
                print(f"**✅ SolveCaptcha returned token!**")
                try:
                    await apply_funcaptcha_token_to_page(page, solvecaptcha_token)
                    await page.wait_for_timeout(2000)
                    
                    new_url = page.url
                    new_content = await page.content()
                    
                    captcha_still_there = False
                    for indicator in ['arkoselabs', 'funcaptcha', '/ap/cvf/']:
                        if indicator in new_content.lower() or indicator in new_url.lower():
                            captcha_still_there = True
                            break
                    
                    if not captcha_still_there:
                        print(f"**✅ FunCaptcha SOLVED via SolveCaptcha!**")
                        return True
                    else:
                        print(f"**⚠️ SolveCaptcha token applied but captcha still showing**")
                except Exception as apply_err:
                    print(f"**⚠️ Error applying SolveCaptcha token: {apply_err}**")
            else:
                print(f"**⚠️ SolveCaptcha failed, trying 2captcha...**")
        
        # ============================================
        # PRIORITY 2: Try 2Captcha as FALLBACK for FunCaptcha
        # ============================================
        if TWOCAPTCHA_API_KEY and not check_timeout():
            print(f"**🔐 PRIORITY 2: Trying 2Captcha for FunCaptcha...**")
            
            twocaptcha_token = await solve_funcaptcha_2captcha_direct(
                public_key=public_key,
                page_url=current_url,
                api_subdomain=api_subdomain,
                data_blob=data_blob,
                user_agent=user_agent
            )
            
            if twocaptcha_token:
                print(f"**✅ 2Captcha returned token!**")
                try:
                    await apply_funcaptcha_token_to_page(page, twocaptcha_token)
                    await page.wait_for_timeout(2000)
                    
                    new_url = page.url
                    new_content = await page.content()
                    
                    captcha_still_there = False
                    for indicator in ['arkoselabs', 'funcaptcha', '/ap/cvf/']:
                        if indicator in new_content.lower() or indicator in new_url.lower():
                            captcha_still_there = True
                            break
                    
                    if not captcha_still_there:
                        print(f"**✅ FunCaptcha SOLVED via 2Captcha!**")
                        return True
                    else:
                        print(f"**⚠️ 2Captcha token applied but captcha still showing**")
                except Exception as apply_err:
                    print(f"**⚠️ Error applying 2Captcha token: {apply_err}**")
            else:
                print(f"**⚠️ 2Captcha failed, trying AntiCaptcha as last resort...**")
        
        # ============================================
        # PRIORITY 3: AntiCaptcha as LAST RESORT for FunCaptcha
        # ============================================
        if ANTICAPTCHA_API_KEY and not check_timeout():
            print(f"**📤 PRIORITY 3: Trying Anti-Captcha as last resort (timeout: {CAPTCHA_TIMEOUT_SECONDS}s)...**")'''

if old_anticaptcha_start in content:
    content = content.replace(old_anticaptcha_start, new_funcaptcha_solvers)
    print("Updated FunCaptcha solving to use SolveCaptcha -> 2Captcha -> AntiCaptcha")
else:
    print("WARNING: Could not find Anti-Captcha FunCaptcha section to modify")

# Write the modified file
with open('/home/ubuntu/amazon-bot/main2.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✅ Patch completed!")
print("Changes made:")
print("  1. Added SOLVECAPTCHA_API_KEY constant")
print("  2. Added solve_funcaptcha_solvecaptcha() function")  
print("  3. Added solve_funcaptcha_2captcha_direct() function")
print("  4. Added apply_funcaptcha_token_to_page() helper")
print("  5. Modified FunCaptcha solving order: SolveCaptcha -> 2Captcha -> AntiCaptcha")
