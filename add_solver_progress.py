#!/usr/bin/env python3
"""Add progress callbacks to show which captcha solver is being used"""

with open("/home/ubuntu/amazon-bot/main2.py", "r") as f:
    content = f.read()

# Modify solve_funcaptcha_arkose to accept progress_callback
old_func_sig = 'async def solve_funcaptcha_arkose(page):'
new_func_sig = 'async def solve_funcaptcha_arkose(page, progress_callback=None):'

if old_func_sig in content:
    content = content.replace(old_func_sig, new_func_sig)
    print("✅ Added progress_callback parameter to solve_funcaptcha_arkose")

# Add helper function to send progress inside solve_funcaptcha_arkose
old_timeout_check = '''    def check_timeout():
        """Check if we've exceeded the timeout"""
        elapsed = time.time() - start_time
        if elapsed > CAPTCHA_TIMEOUT_SECONDS:
            print(f"**⏱️ CAPTCHA timeout alcanzado ({int(elapsed)}s) - abortando...**")
            return True
        return False'''

new_timeout_check = '''    def check_timeout():
        """Check if we've exceeded the timeout"""
        elapsed = time.time() - start_time
        if elapsed > CAPTCHA_TIMEOUT_SECONDS:
            print(f"**⏱️ CAPTCHA timeout alcanzado ({int(elapsed)}s) - abortando...**")
            return True
        return False
    
    async def report_progress(msg):
        """Send progress to callback if available"""
        print(msg)
        if progress_callback:
            try:
                import asyncio
                if asyncio.iscoroutinefunction(progress_callback):
                    await progress_callback(msg)
                else:
                    progress_callback(msg)
            except:
                pass'''

if old_timeout_check in content:
    content = content.replace(old_timeout_check, new_timeout_check)
    print("✅ Added report_progress helper function")

# Update the print statements to use report_progress for key solver messages
# Priority 1: SolveCaptcha
old_p1 = 'print(f"**🔐 PRIORITY 1: Trying SolveCaptcha for FunCaptcha...**")'
new_p1 = 'await report_progress("🔐 Solving FunCaptcha via SolveCaptcha...")'
content = content.replace(old_p1, new_p1)

old_p1_success = 'print(f"**✅ FunCaptcha SOLVED via SolveCaptcha!**")'
new_p1_success = 'await report_progress("✅ FunCaptcha solved via SolveCaptcha!")'
content = content.replace(old_p1_success, new_p1_success)

# Priority 2: 2Captcha  
old_p2 = 'print(f"**🔐 PRIORITY 2: Trying 2Captcha for FunCaptcha...**")'
new_p2 = 'await report_progress("🔐 Solving FunCaptcha via 2Captcha...")'
content = content.replace(old_p2, new_p2)

old_p2_success = 'print(f"**✅ FunCaptcha SOLVED via 2Captcha!**")'
new_p2_success = 'await report_progress("✅ FunCaptcha solved via 2Captcha!")'
content = content.replace(old_p2_success, new_p2_success)

# Priority 3: AntiCaptcha
old_p3 = 'print(f"**📤 PRIORITY 3: Trying Anti-Captcha (timeout: {CAPTCHA_TIMEOUT_SECONDS}s)...**")'
new_p3 = 'await report_progress("🔐 Solving FunCaptcha via AntiCaptcha...")'
content = content.replace(old_p3, new_p3)

# Also update the initial FunCaptcha message
old_init = 'print(f"**🎮 Intentando resolver FunCaptcha (Arkose Labs)...**")'
new_init = 'await report_progress("🎮 FunCaptcha detected - starting solve...")'
content = content.replace(old_init, new_init)

# Now update the calls to solve_funcaptcha_arkose to pass progress_callback
# Find calls and update them

# Call 1: around line 2440 (in create_us_amazon_account)
old_call1 = 'captcha_solved = await solve_funcaptcha_arkose(us_page)'
new_call1 = 'captcha_solved = await solve_funcaptcha_arkose(us_page, progress_callback=progress_callback)'
content = content.replace(old_call1, new_call1)

# Call 2: around line 3562 
old_call2 = 'result = await solve_funcaptcha_arkose(page)'
new_call2 = 'result = await solve_funcaptcha_arkose(page, progress_callback=progress_callback if "progress_callback" in dir() else None)'
content = content.replace(old_call2, new_call2)

# Call 3: around line 8658 (in create_amazon_account)
old_call3 = 'captcha_solved = await solve_funcaptcha_arkose(page)'
new_call3 = 'captcha_solved = await solve_funcaptcha_arkose(page, progress_callback=progress_callback)'
content = content.replace(old_call3, new_call3)

print("✅ Updated solve_funcaptcha_arkose calls to pass progress_callback")

with open("/home/ubuntu/amazon-bot/main2.py", "w") as f:
    f.write(content)

print("\n✅ Done! Captcha solving will now show which solver is being used.")
