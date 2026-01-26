#!/usr/bin/env python3
"""Restore code block style and show captcha types"""

with open("/home/ubuntu/amazon-bot/telegram_bot.py", "r") as f:
    content = f.read()

# Restore the code block format
old_format = 'f"🔄 *Generation in Progress*\\n\\n📍 Region: {get_supported_countries()[country_code]}\\n{credit_info}\\n\\n{progress_text}"'

new_format = 'f"🔄 *Generation in Progress*\\n\\n📍 Region: {get_supported_countries()[country_code]}\\n{credit_info}\\n```\\n{progress_text}\\n```"'

if old_format in content:
    content = content.replace(old_format, new_format)
    print("Restored code block style")
else:
    print("Could not find format to restore")

# Update captcha messages to show type
old_captcha_check = '''                    elif "captcha" in raw_msg or "robot" in raw_msg or "puzzle" in raw_msg:
                        if "resuelto" in raw_msg or "solved" in raw_msg or "✅" in msg_data:
                            simple_msg = "✅ Captcha solved!"
                        else:
                            simple_msg = "🔐 Solving captcha..."'''

new_captcha_check = '''                    elif "captcha" in raw_msg or "robot" in raw_msg or "puzzle" in raw_msg:
                        if "resuelto" in raw_msg or "solved" in raw_msg or "✅" in msg_data:
                            simple_msg = "✅ Captcha solved!"
                        elif "funcaptcha" in raw_msg or "arkose" in raw_msg:
                            simple_msg = "🔐 Solving FunCaptcha..."
                        elif "aws" in raw_msg or "waf" in raw_msg or "grid" in raw_msg:
                            simple_msg = "🔐 Solving AWS WAF Captcha..."
                        elif "recaptcha" in raw_msg:
                            simple_msg = "🔐 Solving reCAPTCHA..."
                        elif "image" in raw_msg or "text" in raw_msg:
                            simple_msg = "🔐 Solving Image Captcha..."
                        else:
                            simple_msg = "🔐 Solving captcha..."'''

if old_captcha_check in content:
    content = content.replace(old_captcha_check, new_captcha_check)
    print("Added captcha type info")
else:
    print("Could not find captcha check")

# Also update the solvecaptcha/2captcha line to show which service
old_solver_check = '''                    elif "solvecaptcha" in raw_msg or "2captcha" in raw_msg or "anticaptcha" in raw_msg:
                        simple_msg = "🔐 Solving captcha..."'''

new_solver_check = '''                    elif "solvecaptcha" in raw_msg:
                        simple_msg = "🔐 Solving via SolveCaptcha..."
                    elif "2captcha" in raw_msg:
                        simple_msg = "🔐 Solving via 2Captcha..."
                    elif "anticaptcha" in raw_msg or "anti-captcha" in raw_msg:
                        simple_msg = "🔐 Solving via AntiCaptcha..."'''

if old_solver_check in content:
    content = content.replace(old_solver_check, new_solver_check)
    print("Added solver service info")
else:
    print("Could not find solver check")

with open("/home/ubuntu/amazon-bot/telegram_bot.py", "w") as f:
    f.write(content)

print("Done!")
