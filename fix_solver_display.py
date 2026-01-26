#!/usr/bin/env python3
"""Fix solver display and add /pending command"""

with open("/home/ubuntu/amazon-bot/telegram_bot.py", "r") as f:
    content = f.read()

# Fix the order of captcha message checks - solver specific should come FIRST
old_captcha_section = '''                    elif "captcha" in raw_msg or "robot" in raw_msg or "puzzle" in raw_msg:
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
                            simple_msg = "🔐 Solving captcha..."
                    elif "solvecaptcha" in raw_msg:
                        simple_msg = "🔐 Solving via SolveCaptcha..."
                    elif "2captcha" in raw_msg:
                        simple_msg = "🔐 Solving via 2Captcha..."
                    elif "anticaptcha" in raw_msg or "anti-captcha" in raw_msg:
                        simple_msg = "🔐 Solving via AntiCaptcha..."'''

new_captcha_section = '''                    elif "solvecaptcha" in raw_msg:
                        if "solved" in raw_msg or "✅" in msg_data:
                            simple_msg = "✅ Solved via SolveCaptcha!"
                        else:
                            simple_msg = "🔐 Solving via SolveCaptcha..."
                    elif "2captcha" in raw_msg:
                        if "solved" in raw_msg or "✅" in msg_data:
                            simple_msg = "✅ Solved via 2Captcha!"
                        else:
                            simple_msg = "🔐 Solving via 2Captcha..."
                    elif "anticaptcha" in raw_msg or "anti-captcha" in raw_msg:
                        if "solved" in raw_msg or "✅" in msg_data:
                            simple_msg = "✅ Solved via AntiCaptcha!"
                        else:
                            simple_msg = "🔐 Solving via AntiCaptcha..."
                    elif "captcha" in raw_msg or "robot" in raw_msg or "puzzle" in raw_msg:
                        if "resuelto" in raw_msg or "solved" in raw_msg or "✅" in msg_data:
                            simple_msg = "✅ Captcha solved!"
                        elif "funcaptcha" in raw_msg or "arkose" in raw_msg:
                            simple_msg = "🔐 Solving FunCaptcha..."
                        elif "aws" in raw_msg or "waf" in raw_msg or "grid" in raw_msg:
                            simple_msg = "🔐 Solving AWS WAF..."
                        elif "recaptcha" in raw_msg:
                            simple_msg = "🔐 Solving reCAPTCHA..."
                        elif "image" in raw_msg or "text" in raw_msg:
                            simple_msg = "🔐 Solving Image Captcha..."
                        else:
                            simple_msg = "🔐 Solving captcha..."'''

if old_captcha_section in content:
    content = content.replace(old_captcha_section, new_captcha_section)
    print("✅ Fixed captcha solver display order")
else:
    print("❌ Could not find captcha section to fix")

# =============================================
# Add /pending command to see pending users
# =============================================

# Find where commands are registered (near other command handlers)
# Add after the allow_command handler

pending_command = '''
async def pending_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show pending users who haven't claimed their credits yet - Owner only"""
    user_id = update.effective_user.id
    
    # Check if user is owner
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ This command is only for the owner.")
        return
    
    try:
        async with aiosqlite.connect(DATABASE_PATH) as conn:
            cursor = await conn.execute(
                "SELECT username, credits, created_at FROM pending_users ORDER BY created_at DESC"
            )
            pending = await cursor.fetchall()
        
        if not pending:
            await update.message.reply_text("📋 No pending users.")
            return
        
        msg = "📋 **Pending Users:**\\n\\n"
        for username, credits, created_at in pending:
            msg += f"• @{username} - {credits} credits (added: {created_at[:10]})\\n"
        
        msg += f"\\n_Total: {len(pending)} pending users_"
        
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

'''

# Find where to insert - after allow_command function
if "async def allow_command" in content and "async def pending_command" not in content:
    # Find the end of allow_command function (next async def or similar)
    import re
    
    # Insert after allow_command function
    pattern = r'(async def allow_command\(update: Update, context: ContextTypes\.DEFAULT_TYPE\):.*?)(async def \w+_command|async def \w+_callback|# ===)'
    
    match = re.search(pattern, content, re.DOTALL)
    if match:
        # Find a good insertion point - after allow_command ends
        allow_idx = content.find("async def allow_command")
        next_func_idx = content.find("async def ", allow_idx + 50)
        
        # Insert before the next function
        content = content[:next_func_idx] + pending_command + "\n" + content[next_func_idx:]
        print("✅ Added pending_command function")
    else:
        # Try alternate insertion
        allow_end = content.find("async def ", content.find("async def allow_command") + 30)
        if allow_end > 0:
            content = content[:allow_end] + pending_command + "\n" + content[allow_end:]
            print("✅ Added pending_command function (alternate)")
else:
    if "async def pending_command" in content:
        print("ℹ️ pending_command already exists")
    else:
        print("❌ Could not find insertion point for pending_command")

# Register the /pending command handler
if 'application.add_handler(CommandHandler("pending"' not in content:
    # Find where handlers are added
    handler_pattern = 'application.add_handler(CommandHandler("allow"'
    if handler_pattern in content:
        content = content.replace(
            handler_pattern,
            'application.add_handler(CommandHandler("pending", pending_command))\n    ' + handler_pattern
        )
        print("✅ Registered /pending command handler")
    else:
        print("❌ Could not find handler registration point")

with open("/home/ubuntu/amazon-bot/telegram_bot.py", "w") as f:
    f.write(content)

print("\n✅ Done!")
