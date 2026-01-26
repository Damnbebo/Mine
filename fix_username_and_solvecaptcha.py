#!/usr/bin/env python3
"""
Fix:
1. @username resolution - allow adding users by username before they interact
2. SolveCaptcha API setup - match the exact format from the article
"""

# ==================== FIX 1: Database - Add pending_users table ====================
db_fix = '''
    async def create_pending_user(self, username: str, credits: float, added_by: int) -> bool:
        """Add a pending user by username only (before they interact with bot)"""
        try:
            username = username.lstrip('@').lower()
            await self._connection.execute("""
                INSERT OR REPLACE INTO pending_users (username, credits, added_by, created_at)
                VALUES (?, ?, ?, datetime('now'))
            """, (username, credits, added_by))
            await self._connection.commit()
            await self.log_activity(added_by, None, 'ADD_PENDING_USER', 
                f'Added pending user @{username} with {credits} credits')
            return True
        except Exception as e:
            print(f"Error creating pending user: {e}")
            return False
    
    async def get_pending_user(self, username: str) -> dict:
        """Get pending user by username"""
        try:
            username = username.lstrip('@').lower()
            cursor = await self._connection.execute(
                "SELECT * FROM pending_users WHERE LOWER(username) = ?", (username,))
            row = await cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            print(f"Error getting pending user: {e}")
            return None
    
    async def claim_pending_credits(self, user_id: int, username: str) -> float:
        """Claim pending credits when user starts the bot"""
        try:
            username_lower = username.lstrip('@').lower() if username else ""
            
            # Check for pending entry
            cursor = await self._connection.execute(
                "SELECT credits, added_by FROM pending_users WHERE LOWER(username) = ?",
                (username_lower,))
            row = await cursor.fetchone()
            
            if row:
                credits = row['credits']
                added_by = row['added_by']
                
                # Add user with the pending credits
                await self.add_user(user_id, username, credits, added_by)
                
                # Delete the pending entry
                await self._connection.execute(
                    "DELETE FROM pending_users WHERE LOWER(username) = ?",
                    (username_lower,))
                await self._connection.commit()
                
                await self.log_activity(user_id, username, 'CLAIM_PENDING',
                    f'Claimed {credits} pending credits')
                
                return credits
            return 0.0
        except Exception as e:
            print(f"Error claiming pending credits: {e}")
            return 0.0
'''

# Read database.py
with open('/home/ubuntu/amazon-bot/database.py', 'r') as f:
    db_content = f.read()

# Check if pending_users table exists in init
if 'pending_users' not in db_content:
    # Add pending_users table creation in initialize
    old_init = '''            CREATE TABLE IF NOT EXISTS sessions'''
    new_init = '''            CREATE TABLE IF NOT EXISTS pending_users (
                username TEXT PRIMARY KEY,
                credits REAL DEFAULT 0.0,
                added_by INTEGER,
                created_at TEXT
            );
            
            CREATE TABLE IF NOT EXISTS sessions'''
    
    db_content = db_content.replace(old_init, new_init)
    print("Added pending_users table to database schema")

# Add the new methods to Database class
if 'async def create_pending_user' not in db_content:
    # Find a good place to insert - before get_all_users
    marker = '    async def get_all_users'
    if marker in db_content:
        db_content = db_content.replace(marker, db_fix + '\n' + marker)
        print("Added pending user methods to database")
    else:
        print("WARNING: Could not find insertion point for pending user methods")

# Write database.py
with open('/home/ubuntu/amazon-bot/database.py', 'w') as f:
    f.write(db_content)

print("Database updated!")

# ==================== FIX 2: Telegram Bot - Update allow_command ====================
with open('/home/ubuntu/amazon-bot/telegram_bot.py', 'r') as f:
    bot_content = f.read()

# Fix the allow_command to support adding by username without user_id
old_allow_error = '''            else:
                await update.message.reply_text(
                    f"❌ Cannot resolve `@{user_ref}`\\n\\n"
                    "Please reply to their message, or use their numeric ID:\\n"
                    "`/allow 123456789 30`",
                    parse_mode=ParseMode.MARKDOWN
                )
                return'''

new_allow_logic = '''            else:
                # User provided @username - add as pending user
                target_username = user_ref
                target_user_id = None  # Will be linked when user starts the bot
                
                # Try to find if user already exists in database
                existing_user = await db.get_user_by_username(user_ref)
                if existing_user:
                    target_user_id = existing_user['user_id']
                    target_username = existing_user['username']'''

if old_allow_error in bot_content:
    bot_content = bot_content.replace(old_allow_error, new_allow_logic)
    print("Updated allow_command to support @username")
else:
    print("WARNING: Could not find allow_command error block to replace")

# Also need to update the success logic to handle pending users
old_allow_success = '''    if credits <= 0:
        await update.message.reply_text("❌ Credits must be positive.")
        return
    
    success = await db.add_user(target_user_id, target_username, credits, user_id)'''

new_allow_success = '''    if credits <= 0:
        await update.message.reply_text("❌ Credits must be positive.")
        return
    
    # If we have user_id, add directly. Otherwise, add as pending
    if target_user_id:
        success = await db.add_user(target_user_id, target_username, credits, user_id)
    else:
        # Add as pending user - will be activated when user starts the bot
        success = await db.create_pending_user(target_username, credits, user_id)
        if success:
            await update.message.reply_text(
                f"✅ *Pending User Added*\\n\\n"
                f"👤 Username: @{target_username}\\n"
                f"💰 Credits: `{credits:.2f}` (pending)\\n\\n"
                f"ℹ️ Credits will be activated when the user sends /start to the bot.",
                parse_mode=ParseMode.MARKDOWN
            )
            return'''

if old_allow_success in bot_content:
    bot_content = bot_content.replace(old_allow_success, new_allow_success)
    print("Updated allow_command success logic for pending users")
else:
    print("WARNING: Could not find allow_command success block")

# Update start_command to claim pending credits
old_start_logging = '''    await log_activity(user_id, username, "START", "User started the bot")'''

new_start_with_claim = '''    await log_activity(user_id, username, "START", "User started the bot")
    
    # Check for pending credits
    db = await get_database()
    if username:
        pending_credits = await db.claim_pending_credits(user_id, username)
        if pending_credits > 0:
            await update.message.reply_text(
                f"🎉 *Welcome!* Your account has been activated!\\n\\n"
                f"💰 Credits: `{pending_credits:.2f}`\\n\\n"
                f"Use /gen to start generating cookies.",
                parse_mode=ParseMode.MARKDOWN
            )'''

if old_start_logging in bot_content:
    bot_content = bot_content.replace(old_start_logging, new_start_with_claim)
    print("Updated start_command to claim pending credits")
else:
    print("WARNING: Could not find start_command logging line")

# Write telegram_bot.py
with open('/home/ubuntu/amazon-bot/telegram_bot.py', 'w') as f:
    f.write(bot_content)

print("Telegram bot updated!")

# ==================== FIX 3: SolveCaptcha - Match exact API format from article ====================
with open('/home/ubuntu/amazon-bot/main2.py', 'r') as f:
    main2_content = f.read()

# Find and replace the solve_funcaptcha_solvecaptcha function to match article format exactly
old_solvecaptcha = '''async def solve_funcaptcha_solvecaptcha(public_key, page_url, api_subdomain=None, data_blob=None, user_agent=None):
    """Solve FunCaptcha using SolveCaptcha.com API (primary solver)"""
    import requests
    import time
    
    if not SOLVECAPTCHA_API_KEY:
        print("**SolveCaptcha: No API key configured**")
        return None
    
    try:
        print(f"**SolveCaptcha: Sending FunCaptcha request...**")
        
        params = {
            "key": SOLVECAPTCHA_API_KEY,
            "method": "funcaptcha",
            "publickey": public_key,
            "pageurl": page_url,
            "json": "1"
        }
        
        if api_subdomain:
            if not api_subdomain.startswith("http"):
                params["surl"] = f"https://{api_subdomain}"
            else:
                params["surl"] = api_subdomain
        
        if data_blob:
            params["data[blob]"] = data_blob
        
        if user_agent:
            params["userAgent"] = user_agent
        
        surl_display = params.get("surl", "N/A")
        if surl_display and len(surl_display) > 40:
            surl_display = surl_display[:40]
        print(f"**SolveCaptcha params: pk={public_key[:20]}... surl={surl_display}**")
        
        response = requests.post("https://api.solvecaptcha.com/in.php", data=params, timeout=30)
        result = response.json()
        
        if result.get("status") != 1:
            error = result.get("request", "Unknown error")
            print(f"**SolveCaptcha submit error: {error}**")
            return None
        
        captcha_id = result.get("request")
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
                    "https://api.solvecaptcha.com/res.php",
                    params={"key": SOLVECAPTCHA_API_KEY, "action": "get", "id": captcha_id, "json": "1"},
                    timeout=30
                )
                result = res.json()
                
                if result.get("status") == 1:
                    token = result.get("request")
                    print(f"**SolveCaptcha SUCCESS! Token received ({len(token)} chars)**")
                    return token
                
                request_status = result.get("request", "")
                if request_status == "CAPCHA_NOT_READY":
                    poll_interval = min(poll_interval + 2, 10)
                    continue
                elif "ERROR" in str(request_status):
                    print(f"**SolveCaptcha error: {request_status}**")
                    return None
            except Exception as poll_err:
                print(f"**SolveCaptcha poll error: {poll_err}**")
        
        print(f"**SolveCaptcha timeout after {max_wait}s**")
        return None
        
    except Exception as e:
        print(f"**SolveCaptcha exception: {e}**")
        return None'''

# New SolveCaptcha function matching the article EXACTLY
new_solvecaptcha = '''async def solve_funcaptcha_solvecaptcha(public_key, page_url, api_subdomain=None, data_blob=None, user_agent=None):
    """
    Solve FunCaptcha using SolveCaptcha.com API
    
    Based on: https://solvecaptcha.com/captcha-solver/funcaptcha-solver-bypass
    
    API Flow:
    1. POST to https://api.solvecaptcha.com/in.php with method=funcaptcha
    2. Wait 10-20 seconds
    3. GET https://api.solvecaptcha.com/res.php?key=KEY&action=get&id=CAPTCHA_ID
    """
    import requests
    import time
    
    if not SOLVECAPTCHA_API_KEY:
        print("**SolveCaptcha: No API key configured**")
        return None
    
    try:
        print(f"**🔐 SolveCaptcha: Sending FunCaptcha request...**")
        
        # Build request exactly as shown in the article
        payload = {
            'key': SOLVECAPTCHA_API_KEY,
            'method': 'funcaptcha',
            'publickey': public_key,
            'pageurl': page_url,
            'json': '1'
        }
        
        # Add surl if provided (API subdomain)
        if api_subdomain:
            if api_subdomain.startswith('http'):
                payload['surl'] = api_subdomain
            else:
                payload['surl'] = f'https://{api_subdomain}'
        
        # Add data[blob] if provided
        if data_blob:
            payload['data[blob]'] = data_blob
        
        # Add userAgent if provided
        if user_agent:
            payload['userAgent'] = user_agent
        
        print(f"**📤 SolveCaptcha request:**")
        print(f"   publickey: {public_key[:30]}...")
        print(f"   pageurl: {page_url[:50]}...")
        if 'surl' in payload:
            print(f"   surl: {payload['surl']}")
        if 'data[blob]' in payload:
            print(f"   data[blob]: {payload['data[blob]'][:30]}...")
        
        # Step 1: Submit the captcha
        response = requests.post(
            'https://api.solvecaptcha.com/in.php',
            data=payload,
            timeout=30
        )
        
        print(f"**📥 SolveCaptcha response: {response.text[:100]}**")
        
        result = response.json()
        
        if result.get('status') != 1:
            error = result.get('request', 'Unknown error')
            print(f"**❌ SolveCaptcha submit error: {error}**")
            return None
        
        captcha_id = result.get('request')
        print(f"**✅ SolveCaptcha task created: {captcha_id}**")
        
        # Step 2: Wait 10-20 seconds as per documentation
        print(f"**⏳ Waiting 15 seconds before polling...**")
        await asyncio.sleep(15)
        
        # Step 3: Poll for result
        max_attempts = 24  # 24 * 5s = 120 seconds max
        
        for attempt in range(max_attempts):
            elapsed = 15 + (attempt * 5)
            print(f"**⏳ SolveCaptcha polling attempt {attempt + 1}... ({elapsed}s)**")
            
            try:
                # GET request as shown in article
                res = requests.get(
                    f'https://api.solvecaptcha.com/res.php?key={SOLVECAPTCHA_API_KEY}&action=get&id={captcha_id}&json=1',
                    timeout=30
                )
                
                result = res.json()
                
                if result.get('status') == 1:
                    token = result.get('request')
                    print(f"**✅ SolveCaptcha SUCCESS!**")
                    print(f"**🎫 Token: {token[:80]}...**")
                    return token
                
                request_status = result.get('request', '')
                
                if request_status == 'CAPCHA_NOT_READY':
                    await asyncio.sleep(5)
                    continue
                elif 'ERROR' in str(request_status):
                    print(f"**❌ SolveCaptcha error: {request_status}**")
                    return None
                else:
                    await asyncio.sleep(5)
                    continue
                    
            except Exception as poll_err:
                print(f"**⚠️ SolveCaptcha poll error: {poll_err}**")
                await asyncio.sleep(5)
        
        print(f"**⚠️ SolveCaptcha timeout after {15 + max_attempts * 5}s**")
        return None
        
    except Exception as e:
        print(f"**❌ SolveCaptcha exception: {e}**")
        import traceback
        traceback.print_exc()
        return None'''

if old_solvecaptcha in main2_content:
    main2_content = main2_content.replace(old_solvecaptcha, new_solvecaptcha)
    print("Updated SolveCaptcha function to match article format")
else:
    print("WARNING: Could not find old SolveCaptcha function to replace")

# Write main2.py
with open('/home/ubuntu/amazon-bot/main2.py', 'w') as f:
    f.write(main2_content)

print("main2.py updated!")
print("\n✅ All fixes applied!")
