#!/usr/bin/env python3
"""Simplify progress messages to show only key steps"""

with open("/home/ubuntu/amazon-bot/telegram_bot.py", "r") as f:
    content = f.read()

# Find and update the progress message handling section
old_progress_handler = '''                if msg_type == "progress":
                    progress_lines.append(msg_data)
                    if len(progress_lines) > 10:
                        progress_lines = progress_lines[-10:]
                    
                    # Rate limit progress updates to avoid Telegram flood control
                    import time
                    current_time = time.time()
                    if current_time - last_update_time[0] < MIN_UPDATE_INTERVAL:
                        continue  # Skip this update, too soon
                    last_update_time[0] = current_time
                    
                    progress_text = "\\n".join(progress_lines)
                    try:
                        await status_message.edit_text('''

new_progress_handler = '''                if msg_type == "progress":
                    # Simplify progress messages - only show key steps
                    raw_msg = msg_data.lower()
                    simple_msg = None
                    
                    # Map detailed messages to simple steps
                    if "obteniendo número" in raw_msg or "comprando número" in raw_msg:
                        simple_msg = "📱 Getting phone number..."
                    elif "número comprado" in raw_msg or "teléfono:" in raw_msg:
                        simple_msg = "✅ Phone number ready"
                    elif "usando navegador" in raw_msg or "stealth" in raw_msg:
                        simple_msg = "🌐 Opening browser..."
                    elif "cargando página" in raw_msg or "loading" in raw_msg:
                        simple_msg = "🌐 Loading Amazon..."
                    elif "ingresando número" in raw_msg or "teléfono ingresado" in raw_msg:
                        simple_msg = "📝 Entering phone number..."
                    elif "clickeando continue" in raw_msg:
                        simple_msg = "➡️ Continuing..."
                    elif "create your amazon" in raw_msg or "crear cuenta" in raw_msg or "new to amazon" in raw_msg:
                        simple_msg = "📝 Creating account..."
                    elif "llenando formulario" in raw_msg or "formulario de registro" in raw_msg:
                        simple_msg = "📝 Filling signup form..."
                    elif "nombre ingresado" in raw_msg:
                        simple_msg = "✅ Name entered"
                    elif "password ingresado" in raw_msg:
                        simple_msg = "✅ Password set"
                    elif "verify" in raw_msg or "submit" in raw_msg:
                        simple_msg = "🔄 Submitting..."
                    elif "captcha" in raw_msg or "robot" in raw_msg or "puzzle" in raw_msg:
                        if "resuelto" in raw_msg or "solved" in raw_msg or "✅" in msg_data:
                            simple_msg = "✅ Captcha solved!"
                        else:
                            simple_msg = "🔐 Solving captcha..."
                    elif "solvecaptcha" in raw_msg or "2captcha" in raw_msg or "anticaptcha" in raw_msg:
                        simple_msg = "🔐 Solving captcha..."
                    elif "esperando" in raw_msg and "sms" in raw_msg:
                        simple_msg = "📲 Waiting for SMS code..."
                    elif "código" in raw_msg and ("recibido" in raw_msg or "otp" in raw_msg):
                        simple_msg = "✅ SMS code received!"
                    elif "cuenta creada" in raw_msg or "account created" in raw_msg:
                        simple_msg = "🎉 Account created!"
                    elif "agregando dirección" in raw_msg or "adding address" in raw_msg:
                        simple_msg = "🏠 Adding address..."
                    elif "extrayendo cookies" in raw_msg or "extracting" in raw_msg:
                        simple_msg = "🍪 Extracting cookies..."
                    elif "navegando" in raw_msg and "wallet" in raw_msg:
                        simple_msg = "💳 Getting payment cookies..."
                    elif "login" in raw_msg and "us" in raw_msg:
                        simple_msg = "🇺🇸 Logging into US Amazon..."
                    elif "cookies guardadas" in raw_msg or "cookies saved" in raw_msg:
                        simple_msg = "✅ Cookies saved!"
                    
                    # Only update if we have a simple message and it's different from last
                    if simple_msg:
                        if not progress_lines or progress_lines[-1] != simple_msg:
                            progress_lines.append(simple_msg)
                            if len(progress_lines) > 6:
                                progress_lines = progress_lines[-6:]
                    
                    # Rate limit progress updates to avoid Telegram flood control
                    import time
                    current_time = time.time()
                    if current_time - last_update_time[0] < MIN_UPDATE_INTERVAL:
                        continue  # Skip this update, too soon
                    last_update_time[0] = current_time
                    
                    progress_text = "\\n".join(progress_lines)
                    try:
                        await status_message.edit_text('''

if old_progress_handler in content:
    content = content.replace(old_progress_handler, new_progress_handler)
    print("Simplified progress messages")
else:
    print("Could not find progress handler - trying alternate approach")
    # Try to find a simpler pattern
    if "progress_lines.append(msg_data)" in content:
        print("Found append - will need manual update")

# Also update the progress display format to be cleaner
old_format = '''f"🔄 *Generation in Progress*\\n\\n📍 Region: {get_supported_countries()[country_code]}\\n{credit_info}\\n```\\n{progress_text}\\n```"'''

new_format = '''f"🔄 *Generation in Progress*\\n\\n📍 Region: {get_supported_countries()[country_code]}\\n{credit_info}\\n\\n{progress_text}"'''

if old_format in content:
    content = content.replace(old_format, new_format)
    print("Updated progress display format")

with open("/home/ubuntu/amazon-bot/telegram_bot.py", "w") as f:
    f.write(content)

print("Done!")
