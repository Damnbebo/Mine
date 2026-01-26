#!/usr/bin/env python3
import re

# Read the main2.py file
with open("/home/ubuntu/amazon-bot/main2.py", "r") as f:
    content = f.read()

# Read the functions to insert
with open("/tmp/solvecaptcha_funcs.py", "r") as f:
    funcs_code = f.read()

# Check if functions already exist
if "async def solve_funcaptcha_solvecaptcha" in content:
    print("SolveCaptcha functions already exist in main2.py")
else:
    # Find insertion point - after set_current_page function
    marker = '''def set_current_page(page):
    """Set the current page reference for error screenshots"""
    global _current_page_ref
    _current_page_ref = page'''
    
    if marker in content:
        content = content.replace(marker, marker + "\n\n" + funcs_code)
        print("Inserted SolveCaptcha functions after set_current_page")
    else:
        print("WARNING: Could not find set_current_page marker")

# Now modify solve_funcaptcha_arkose to use SolveCaptcha first
old_pattern = '''        if ANTICAPTCHA_API_KEY and not check_timeout():
            print(f"**📤 Enviando FunCaptcha a Anti-Captcha (timeout: {CAPTCHA_TIMEOUT_SECONDS}s)...**")'''

new_code = '''        # ============================================
        # PRIORITY 1: Try SolveCaptcha FIRST for FunCaptcha
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
                    
                    captcha_gone = not any(ind in new_content.lower() or ind in new_url.lower() 
                                          for ind in ["arkoselabs", "funcaptcha", "/ap/cvf/"])
                    
                    if captcha_gone:
                        print(f"**✅ FunCaptcha SOLVED via SolveCaptcha!**")
                        return True
                    else:
                        print(f"**⚠️ SolveCaptcha token applied but captcha still showing**")
                except Exception as apply_err:
                    print(f"**⚠️ Error applying SolveCaptcha token: {apply_err}**")
            else:
                print(f"**⚠️ SolveCaptcha failed, trying 2captcha...**")
        
        # ============================================
        # PRIORITY 2: Try 2Captcha as FALLBACK
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
                    
                    captcha_gone = not any(ind in new_content.lower() or ind in new_url.lower() 
                                          for ind in ["arkoselabs", "funcaptcha", "/ap/cvf/"])
                    
                    if captcha_gone:
                        print(f"**✅ FunCaptcha SOLVED via 2Captcha!**")
                        return True
                    else:
                        print(f"**⚠️ 2Captcha token applied but captcha still showing**")
                except Exception as apply_err:
                    print(f"**⚠️ Error applying 2Captcha token: {apply_err}**")
            else:
                print(f"**⚠️ 2Captcha failed, trying AntiCaptcha...**")
        
        # ============================================
        # PRIORITY 3: AntiCaptcha as LAST RESORT
        # ============================================
        if ANTICAPTCHA_API_KEY and not check_timeout():
            print(f"**📤 PRIORITY 3: Trying Anti-Captcha (timeout: {CAPTCHA_TIMEOUT_SECONDS}s)...**")'''

if old_pattern in content:
    content = content.replace(old_pattern, new_code)
    print("Updated FunCaptcha solving order: SolveCaptcha -> 2Captcha -> AntiCaptcha")
else:
    print("WARNING: Could not find Anti-Captcha section to modify")

# Write back
with open("/home/ubuntu/amazon-bot/main2.py", "w") as f:
    f.write(content)

print("Done!")
