"""
Amazon Cookie Generator Telegram Bot
Advanced bot with user management, session tracking, and real-time progress updates
UPDATED: Fixed concurrent sessions, countdown timer, username support
"""

import asyncio
import logging
import json
import uuid
import io
import requests
import queue
import threading
import concurrent.futures
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InputFile
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from telegram.constants import ParseMode

from database import get_database, close_database, Database
from main2 import CookieGenerator, GenerationResult, get_supported_countries

# Configuration
BOT_TOKEN = "8268269719:AAFx2Dcdcv4itMdTH6lqZRK2dlaq3dvWFbs"
OWNER_ID = 533082163
SESSION_DURATION_MINUTES = 10

# Credit system
GENERATION_COST = 0.35
DEFAULT_CREDITS = 30.0

# 5sim API key
FIVESIM_API_KEY = ""

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("telegram_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Store active generation tasks (for /gen in progress)
active_generations: Dict[int, dict] = {}

# Store active cookie sessions (browser kept open for 10 min)
active_cookie_sessions: Dict[int, dict] = {}

# Thread pool for concurrent generation
generation_executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)


def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


async def check_access(user_id: int) -> bool:
    if is_owner(user_id):
        return True
    db = await get_database()
    return await db.is_user_allowed(user_id)


async def resolve_user(context, args, update) -> tuple:
    """
    Resolve user from @username, user_id, or reply.
    Returns (user_id, username) or (None, None) if not found.
    """
    db = await get_database()
    target_user_id = None
    target_username = None
    
    # Check if replying to a message
    if update.message.reply_to_message and update.message.reply_to_message.from_user:
        replied_user = update.message.reply_to_message.from_user
        if not replied_user.is_bot:
            target_user_id = replied_user.id
            target_username = replied_user.username or replied_user.first_name or str(replied_user.id)
            return target_user_id, target_username
    
    if not args:
        return None, None
    
    user_ref = args[0].lstrip("@")
    
    # Try as numeric ID first
    try:
        target_user_id = int(user_ref)
        user_info = await db.get_user_info(target_user_id)
        if user_info:
            target_username = user_info.get("username", str(target_user_id))
            return target_user_id, target_username
        return target_user_id, user_ref
    except ValueError:
        pass
    
    # Try username lookup
    user_info = await db.get_user_by_username(user_ref)
    if user_info:
        return user_info["user_id"], user_info["username"]
    
    return None, None


async def notify_owner(context: ContextTypes.DEFAULT_TYPE, message: str):
    try:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=f"📋 *Bot Activity*\n\n{message}",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Failed to notify owner: {e}")


async def log_activity(user_id: int, username: str, action: str, details: str = None):
    db = await get_database()
    await db.log_activity(user_id, username, action, details)


# ==================== Session Countdown Task ====================

async def session_countdown_task(user_id: int, chat_id: int, session_id: str, 
                                 context: ContextTypes.DEFAULT_TYPE, 
                                 generator: CookieGenerator):
    """
    Keep browser session alive for 10 minutes with countdown notifications.
    Notifies user every minute.
    """
    try:
        for minutes_left in range(SESSION_DURATION_MINUTES, 0, -1):
            # Check if session was cancelled
            if user_id not in active_cookie_sessions:
                logger.info(f"Session {session_id} was cancelled, stopping countdown")
                return
            
            if minutes_left == SESSION_DURATION_MINUTES:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"🍪 *Session Active*\n\n"
                         f"🆔 Session: `{session_id}`\n"
                         f"⏱️ Time remaining: *{minutes_left} minutes*\n\n"
                         f"Your cookies are active! Use them now.\n"
                         f"Use /cancel to end the session early.",
                    parse_mode=ParseMode.MARKDOWN
                )
            elif minutes_left <= 3:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"⚠️ *Session Ending Soon*\n\n"
                         f"🆔 Session: `{session_id}`\n"
                         f"⏱️ Time remaining: *{minutes_left} minute(s)*",
                    parse_mode=ParseMode.MARKDOWN
                )
            elif minutes_left % 2 == 0:  # Notify every 2 minutes
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"⏱️ Session `{session_id}`: *{minutes_left} minutes* remaining",
                    parse_mode=ParseMode.MARKDOWN
                )
            
            await asyncio.sleep(60)  # Wait 1 minute
        
        # Session ended
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"⏰ *Session Expired*\n\n"
                 f"🆔 Session: `{session_id}`\n"
                 f"Your 10-minute session has ended.\n\n"
                 f"Use /gen to create a new account.",
            parse_mode=ParseMode.MARKDOWN
        )
        
    except asyncio.CancelledError:
        logger.info(f"Session countdown {session_id} cancelled")
    except Exception as e:
        logger.error(f"Session countdown error: {e}")
    finally:
        # Clean up
        if user_id in active_cookie_sessions:
            del active_cookie_sessions[user_id]
        
        # Close browser if still open
        try:
            if generator and hasattr(generator, "close"):
                await generator.close()
        except:
            pass


# ==================== Command Handlers ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name
    
    await log_activity(user_id, username, "START", "User started the bot")
    
    has_access = await check_access(user_id)
    
    if is_owner(user_id):
        status = "👑 *Owner*"
        access_info = "You have unlimited access to all features."
    elif has_access:
        db = await get_database()
        user_info = await db.get_user_info(user_id)
        credits = user_info.get("credits", 0) if user_info else 0
        accounts = user_info.get("accounts_generated", 0) if user_info else 0
        status = "✅ *Authorized User*"
        access_info = f"💰 Credits: `{credits:.2f}` | 📊 Accounts generated: `{accounts}`\n💵 Cost per generation: `{GENERATION_COST}`"
    else:
        status = "🚫 *No Access*"
        access_info = "Contact the owner to request access."
    
    welcome_message = f"""
🍪 *Amazon Cookie Generator Bot*

Welcome, {username}!

{status}
{access_info}

*Available Commands:*
/gen - Generate Amazon account & cookies
/cancel - Cancel generation or end active session
/balance - Check your credit balance
/help - Show all commands
/mysessions - View your active sessions
"""
    
    if is_owner(user_id):
        welcome_message += """
*Owner Commands:*
/allow @user credits - Add user
/addcredits @user amount - Add credits
/remove @user - Revoke access
/users - List all users
/sessions - View all sessions
/logs - View activity logs
"""
    
    await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    commands = f"""
🍪 *Amazon Cookie Generator - Help*

*User Commands:*
• `/gen` - Start cookie generation (interactive)
• `/gen <country>` - Generate for specific country
• `/cancel` - Cancel generation or end active session
• `/balance` - Check your credit balance
• `/mysessions` - View your active sessions
• `/help` - Show this help message

*Supported Countries:*
🇨🇦 CA (Canada) | 🇲🇽 MX (Mexico)
🇺🇸 US (USA) | 🇬🇧 UK (Britain)
🇩🇪 DE (Germany) | 🇫🇷 FR (France)
🇮🇹 IT (Italy) | 🇪🇸 ES (Spain)
🇯🇵 JP (Japan) | 🇦🇺 AU (Australia)
🇮🇳 IN (India)

💰 *Cost:* `{GENERATION_COST}` credits per successful generation
⏱️ *Session Duration:* {SESSION_DURATION_MINUTES} minutes

*Example:* `/gen US` - Generate for USA
"""
    
    if is_owner(user_id):
        commands += """
*Owner Commands:*
• `/allow @user <credits>` - Add user (supports @username or ID)
• `/addcredits @user <amount>` - Add credits (supports @username)
• `/remove @user` - Revoke access
• `/users` - List all users
• `/sessions` - View all active sessions
• `/killsession <#/all>` - Kill session
• `/logs` - View activity logs
"""
    
    await update.message.reply_text(commands, parse_mode=ParseMode.MARKDOWN)


async def gen_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /gen command - start cookie generation"""
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name
    
    # Check access
    if not await check_access(user_id):
        await update.message.reply_text(
            "🚫 *Access Denied*\n\nYou don't have permission to use this bot.\nContact the owner to request access.",
            parse_mode=ParseMode.MARKDOWN
        )
        await log_activity(user_id, username, "ACCESS_DENIED", "Tried to use /gen without access")
        await notify_owner(context, f"⚠️ Unauthorized access attempt by @{username} ({user_id})")
        return
    
    # Check if user has active cookie session (1 session per user)
    if user_id in active_cookie_sessions:
        await update.message.reply_text(
            "⏳ *Active Session Exists*\n\n"
            "You already have an active cookie session.\n"
            "Use /cancel to end it before starting a new one.\n\n"
            "Use /mysessions to see your active sessions.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Check if already generating
    if user_id in active_generations:
        await update.message.reply_text(
            "⏳ You already have a generation in progress.\n"
            "Use /cancel to stop it, or wait for it to complete.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Check credits (owner has unlimited)
    db = await get_database()
    credits_before = 0.0
    if not is_owner(user_id):
        has_credits, current_credits = await db.has_sufficient_credits(user_id, GENERATION_COST)
        credits_before = current_credits
        
        if not has_credits:
            await update.message.reply_text(
                f"💸 *Insufficient Credits*\n\n"
                f"💰 Your balance: `{current_credits:.2f}` credits\n"
                f"💵 Required: `{GENERATION_COST}` credits\n\n"
                f"Contact the owner to purchase more credits.",
                parse_mode=ParseMode.MARKDOWN
            )
            await log_activity(user_id, username, "INSUFFICIENT_CREDITS", f"Tried to gen with {current_credits:.2f} credits")
            return
    
    # Check for country argument
    if context.args and len(context.args) > 0:
        country_code = context.args[0].upper()
        countries = get_supported_countries()
        
        if country_code in countries:
            await start_generation(update, context, country_code, credits_before)
            return
        else:
            await update.message.reply_text(
                f"❌ Invalid country code: `{country_code}`\n\nUse /help to see supported countries.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
    
    # Show country selection
    countries = get_supported_countries()
    keyboard = []
    row = []
    
    for i, (code, name) in enumerate(countries.items()):
        row.append(InlineKeyboardButton(name, callback_data=f"gen_{code}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="gen_cancel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🌍 *Select Country*\n\nChoose the Amazon region for account generation:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )


async def country_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle country selection callback"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "gen_cancel":
        await query.edit_message_text("❌ Generation cancelled.")
        return
    
    if data.startswith("gen_"):
        country_code = data.replace("gen_", "")
        await query.edit_message_text(f"🚀 Starting generation for {get_supported_countries()[country_code]}...")
        
        # Get credits before
        user_id = update.effective_user.id
        db = await get_database()
        credits_before = await db.get_credits(user_id) if not is_owner(user_id) else 0.0
        
        await start_generation(update, context, country_code, credits_before, is_callback=True)


async def start_generation(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                          country_code: str, credits_before: float, is_callback: bool = False):
    """Start the cookie generation process - runs in background, doesn't block other users"""
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name
    
    if is_callback:
        message = update.callback_query.message
    else:
        message = update.message
    
    db = await get_database()
    
    # Double-check credits
    if not is_owner(user_id):
        has_credits, current_credits = await db.has_sufficient_credits(user_id, GENERATION_COST)
        credits_before = current_credits
        
        if not has_credits:
            await context.bot.send_message(
                chat_id=message.chat_id,
                text=f"💸 *Insufficient Credits*\n\n"
                     f"💰 Your balance: `{current_credits:.2f}` credits\n"
                     f"💵 Required: `{GENERATION_COST}` credits",
                parse_mode=ParseMode.MARKDOWN
            )
            return
    
    # Send initial status
    if not is_owner(user_id):
        credit_info = f"💰 Balance: `{credits_before:.2f}` (Cost: `{GENERATION_COST}`)"
    else:
        credit_info = "💰 Owner: Unlimited credits"
    
    status_message = await context.bot.send_message(
        chat_id=message.chat_id,
        text=f"🔄 *Starting Generation*\n\n📍 Region: {get_supported_countries()[country_code]}\n{credit_info}\n\nPlease wait...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Create unique session ID
    session_id = str(uuid.uuid4())[:8]
    
    progress_lines = []
    account_created_notified = [False]
    cookies_sent = [False]
    progress_queue = queue.Queue()
    generation_done = threading.Event()
    
    def sync_progress_callback(msg: str):
        progress_queue.put(("progress", msg))
    
    def sync_on_account_created(account_info: dict):
        progress_queue.put(("account_created", account_info))
    
    def sync_on_cookies_ready(cookie_data: dict):
        progress_queue.put(("cookies_ready", cookie_data))
    
    def sync_on_error_screenshot(screenshot_bytes: bytes, error_msg: str):
        progress_queue.put(("error_screenshot", {"screenshot": screenshot_bytes, "error": error_msg}))
    
    async def process_queue_messages():
        nonlocal progress_lines
        
        while not generation_done.is_set() or not progress_queue.empty():
            if user_id in active_generations and active_generations[user_id].get("cancelled"):
                return
            
            try:
                msg_type, msg_data = progress_queue.get_nowait()
                
                if msg_type == "progress":
                    progress_lines.append(msg_data)
                    if len(progress_lines) > 10:
                        progress_lines = progress_lines[-10:]
                    
                    progress_text = "\n".join(progress_lines)
                    try:
                        await status_message.edit_text(
                            f"🔄 *Generation in Progress*\n\n📍 Region: {get_supported_countries()[country_code]}\n{credit_info}\n```\n{progress_text}\n```",
                            parse_mode=ParseMode.MARKDOWN
                        )
                    except Exception as e:
                        if "not modified" not in str(e).lower():
                            logger.error(f"Failed to update progress: {e}")
                
                elif msg_type == "account_created" and not account_created_notified[0]:
                    account_created_notified[0] = True
                    account_info = msg_data
                    phone = account_info.get("phone", "N/A")
                    password = account_info.get("password", "N/A")
                    name = account_info.get("name", "N/A")
                    
                    await context.bot.send_message(
                        chat_id=message.chat_id,
                        text=f"✅ *Account Created!* 🟢\n\n"
                             f"📱 *Phone:* `{phone}`\n"
                             f"🔑 *Password:* `{password}`\n"
                             f"👤 *Name:* {name}\n\n"
                             f"⏳ Extracting cookies...",
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                elif msg_type == "cookies_ready" and not cookies_sent[0]:
                    cookies_sent[0] = True
                    cookie_data = msg_data
                    phone = cookie_data.get("phone", "N/A")
                    password = cookie_data.get("password", "N/A")
                    name = cookie_data.get("name", "N/A")
                    cookie_content = cookie_data.get("cookie_content", "")
                    
                    file_content = f"""🍪 AMAZON ACCOUNT COOKIES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🆔 Session ID: {session_id}
📱 Phone: {phone}
🔑 Password: {password}
👤 Name: {name}
🌍 Domain: {country_code}
📅 Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🍪 COOKIES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{cookie_content}
"""
                    
                    file_bytes = io.BytesIO(file_content.encode("utf-8"))
                    file_bytes.name = f"cookies_{country_code}_{session_id}.txt"
                    
                    await context.bot.send_document(
                        chat_id=message.chat_id,
                        document=InputFile(file_bytes, filename=file_bytes.name),
                        caption=f"🍪 Cookies for {country_code} - Session: {session_id}"
                    )
                
                elif msg_type == "error_screenshot":
                    screenshot_data = msg_data
                    screenshot_bytes = screenshot_data.get("screenshot")
                    error_msg = screenshot_data.get("error", "Unknown error")
                    
                    if screenshot_bytes:
                        screenshot_file = io.BytesIO(screenshot_bytes)
                        screenshot_file.name = f"error_{country_code}_{session_id}.png"
                        await context.bot.send_photo(
                            chat_id=OWNER_ID,
                            photo=InputFile(screenshot_file, filename=screenshot_file.name),
                            caption=f"🚨 *Error*\n\n👤 @{username}\n🌍 {country_code}\n❌ {error_msg}",
                            parse_mode=ParseMode.MARKDOWN
                        )
                
            except queue.Empty:
                await asyncio.sleep(0.2)
    
    # Create generator
    generator = CookieGenerator(
        sync_progress_callback, 
        headless=True,
        on_account_created=sync_on_account_created,
        on_cookies_ready=sync_on_cookies_ready,
        on_error_screenshot=sync_on_error_screenshot
    )
    
    if FIVESIM_API_KEY:
        generator.FIVESIM_API_KEY = FIVESIM_API_KEY
    
    try:
        await log_activity(user_id, username, "GEN_START", f"Started generation for {country_code}")
        await notify_owner(context, f"🚀 @{username} ({user_id}) started generation for {country_code}")
        
        active_generations[user_id] = {
            "generator": generator,
            "task": None,
            "cancelled": False,
            "country": country_code,
            "done_event": generation_done,
            "session_id": session_id
        }
        
        # Run generation in thread pool (non-blocking)
        def run_generation():
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(generator.generate(country_code, SESSION_DURATION_MINUTES))
            finally:
                loop.close()
                generation_done.set()
        
        queue_task = asyncio.create_task(process_queue_messages())
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(generation_executor, run_generation)
        
        generation_done.set()
        await queue_task
        
        if user_id in active_generations and active_generations[user_id].get("cancelled"):
            await status_message.edit_text("❌ *Generation Cancelled*\n\nYou cancelled the generation.", parse_mode=ParseMode.MARKDOWN)
            return
        
        if result.success:
            account_identifier = result.phone or result.email or "Unknown"
            
            # Deduct credits and calculate
            credits_after = credits_before
            if not is_owner(user_id):
                deduct_success, credits_after = await db.deduct_credits(
                    user_id, GENERATION_COST, 
                    f"Account generation: {account_identifier} ({result.domain})"
                )
                
                if not deduct_success:
                    await status_message.edit_text(
                        f"❌ *Credit Deduction Failed*\n\nGeneration succeeded but credits couldn't be deducted.\nPlease contact the owner.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    await notify_owner(context, f"⚠️ CREDIT ERROR: @{username} gen succeeded but deduction failed!")
                    return
            
            # Store session
            cookies_str = result.cookies or ""
            us_cookies_str = result.us_cookies or ""
            
            try:
                await db.create_session(
                    session_id=session_id,
                    user_id=user_id,
                    username=username,
                    domain=result.domain,
                    email=account_identifier,
                    password=result.password,
                    cookies_str=cookies_str,
                    cookies_dict={},
                    session_duration_minutes=SESSION_DURATION_MINUTES
                )
            except Exception as db_err:
                logger.warning(f"Session DB error: {db_err}")
            
            # Build file content with credit info
            file_content = f"""🍪 AMAZON ACCOUNT COOKIES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🆔 Session ID: {session_id}
📱 Phone: {result.phone or "N/A"}
🔑 Password: {result.password or "N/A"}
👤 Name: {result.name or "N/A"}
🌍 Domain: {result.domain}
📅 Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 CREDIT INFO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Credits Before: {credits_before:.2f}
Credits Used: {GENERATION_COST}
Credits After: {credits_after:.2f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🍪 COOKIES ({result.domain}):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{cookies_str or "No cookies extracted"}
"""
            
            if us_cookies_str:
                file_content += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🇺🇸 US COOKIES (amazon.com):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{us_cookies_str}
"""
            
            file_bytes = io.BytesIO(file_content.encode("utf-8"))
            file_bytes.name = f"cookies_{result.domain}_{session_id}.txt"
            
            # Credit display
            if not is_owner(user_id):
                credit_msg = f"💰 Credits: {credits_before:.2f} → -{GENERATION_COST} → {credits_after:.2f}"
            else:
                credit_msg = "💰 Credits: Owner (Unlimited)"
            
            success_message = f"""✅ *Account Generated Successfully!*

👤 Generated By: @{username}
🆔 Session ID: `{session_id}`
{credit_msg}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 *ACCOUNT INFO:*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📱 Phone: `{result.phone or "N/A"}`
🔑 Password: `{result.password or "N/A"}`
👤 Name: {result.name or "N/A"}
🌍 Domain: {result.domain}

🍪 Cookies {"sent above ⬆️" if cookies_sent[0] else "attached below ⬇️"}

⏱️ *Session will stay active for {SESSION_DURATION_MINUTES} minutes!*
Use /cancel to end session early."""
            
            await status_message.edit_text(success_message, parse_mode=ParseMode.MARKDOWN)
            
            if not cookies_sent[0]:
                await context.bot.send_document(
                    chat_id=message.chat_id,
                    document=InputFile(file_bytes, filename=file_bytes.name),
                    caption=f"🍪 Cookies for {result.domain} - Session: {session_id}"
                )
            
            if result.screenshot:
                screenshot_file = io.BytesIO(result.screenshot)
                screenshot_file.name = f"confirmation_{session_id}.png"
                await context.bot.send_photo(
                    chat_id=message.chat_id,
                    photo=InputFile(screenshot_file, filename=screenshot_file.name),
                    caption="📸 Account confirmation screenshot"
                )
            
            await log_activity(user_id, username, "GEN_SUCCESS", f"Generated {account_identifier} for {country_code}, cost: {GENERATION_COST}")
            await notify_owner(context, f"✅ @{username} generated:\n• Phone: {result.phone}\n• Domain: {result.domain}\n• Credits: {credits_before:.2f} → {credits_after:.2f}")
            
            # Start session countdown (keep browser active)
            active_cookie_sessions[user_id] = {
                "session_id": session_id,
                "generator": generator,
                "started_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(minutes=SESSION_DURATION_MINUTES)
            }
            
            countdown_task = asyncio.create_task(
                session_countdown_task(user_id, message.chat_id, session_id, context, generator)
            )
            active_cookie_sessions[user_id]["countdown_task"] = countdown_task
            
        else:
            phone_info = f"📱 Phone used: {result.phone}" if result.phone else ""
            
            error_message = f"""❌ *Generation Failed*

📍 Region: {country_code}
❗ Error: {result.error or "Unknown error"}

{phone_info}

Please try again or contact the owner if the issue persists."""
            
            await status_message.edit_text(error_message, parse_mode=ParseMode.MARKDOWN)
            
            if result.screenshot:
                screenshot_file = io.BytesIO(result.screenshot)
                screenshot_file.name = f"error_{country_code}_{session_id}.png"
                await context.bot.send_photo(
                    chat_id=message.chat_id,
                    photo=InputFile(screenshot_file, filename=screenshot_file.name),
                    caption="📸 Error screenshot"
                )
            
            await log_activity(user_id, username, "GEN_FAILED", f"Failed for {country_code}: {result.error}")
            await notify_owner(context, f"❌ @{username} generation failed for {country_code}: {result.error}")
        
    except asyncio.CancelledError:
        logger.info(f"Generation cancelled by user {user_id}")
        try:
            await status_message.edit_text("❌ *Generation Cancelled*\n\nYou cancelled the generation process.", parse_mode=ParseMode.MARKDOWN)
        except:
            pass
        return
        
    except Exception as e:
        import traceback
        tb_str = traceback.format_exc()
        
        if user_id in active_generations and active_generations[user_id].get("cancelled"):
            logger.info(f"Generation cancelled by user {user_id}")
            return
        
        logger.error(f"Generation error: {e}\n{tb_str}")
        await status_message.edit_text(
            f"❌ *Error*\n\nAn unexpected error occurred:\n`{str(e)}`\n\nThe owner has been notified.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        await log_activity(user_id, username, "GEN_ERROR", f"Error: {str(e)}")
        await notify_owner(context, f"❌ @{username} generation error: {str(e)}")
    
    finally:
        if user_id in active_generations:
            del active_generations[user_id]


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cancel command - cancel generation or end active session"""
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    # Check for active cookie session first
    if user_id in active_cookie_sessions:
        session_info = active_cookie_sessions[user_id]
        session_id = session_info.get("session_id", "Unknown")
        
        # Cancel countdown task
        countdown_task = session_info.get("countdown_task")
        if countdown_task and not countdown_task.done():
            countdown_task.cancel()
        
        # Remove session
        del active_cookie_sessions[user_id]
        
        await update.message.reply_text(
            f"✅ *Session Ended*\n\n"
            f"🆔 Session: `{session_id}`\n"
            f"Your cookie session has been terminated.\n\n"
            f"Use /gen to create a new account.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        await log_activity(user_id, username, "SESSION_CANCELLED", f"Ended session {session_id}")
        await notify_owner(context, f"🛑 @{username} ended session {session_id}")
        return
    
    # Check for active generation
    if user_id not in active_generations:
        await update.message.reply_text(
            "❌ *Nothing to Cancel*\n\n"
            "You don't have any generation or session in progress.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    await update.message.reply_text(
        "🛑 *Cancelling Generation...*\n\n"
        "Stopping the process and closing browser.\n"
        "Please wait...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    country = active_generations[user_id].get("country", "Unknown")
    
    active_generations[user_id]["cancelled"] = True
    
    try:
        task = active_generations[user_id].get("task")
        if task and not task.done():
            task.cancel()
            logger.info(f"Cancelled task for user {user_id}")
    except Exception as e:
        logger.error(f"Error cancelling task: {e}")
    
    try:
        import subprocess
        import os
        os.system("pkill -9 -f chromium 2>/dev/null")
        os.system("pkill -9 -f chrome 2>/dev/null")
        os.system("pkill -9 -f playwright 2>/dev/null")
        logger.info(f"Killed browser processes for user {user_id}")
    except Exception as e:
        logger.error(f"Error killing browser: {e}")
    
    await asyncio.sleep(1)
    
    if user_id in active_generations:
        del active_generations[user_id]
    
    await log_activity(user_id, username, "GEN_CANCELLED", f"Cancelled generation for {country}")
    await notify_owner(context, f"🛑 @{username} cancelled generation for {country}")
    
    await update.message.reply_text(
        "✅ *Generation Cancelled*\n\n"
        "The browser has been closed and process stopped.\n"
        "You can start a new generation with /gen",
        parse_mode=ParseMode.MARKDOWN
    )


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /balance command"""
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name
    
    if is_owner(user_id):
        await update.message.reply_text(
            "👑 *Owner Account*\n\n"
            "💰 Credits: Unlimited\n"
            "You have full access to all features.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    db = await get_database()
    user_info = await db.get_user_info(user_id)
    
    if not user_info:
        await update.message.reply_text(
            "🚫 *No Account Found*\n\n"
            "You don't have an account yet.\n"
            "Contact the owner to get access.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    credits = user_info.get("credits", 0)
    total_spent = user_info.get("total_spent", 0)
    accounts_generated = user_info.get("accounts_generated", 0)
    can_generate = int(credits / GENERATION_COST)
    
    await update.message.reply_text(
        f"💰 *Credit Balance*\n\n"
        f"👤 User: @{username}\n"
        f"💵 Balance: `{credits:.2f}` credits\n"
        f"📊 Accounts generated: `{accounts_generated}`\n"
        f"💸 Total spent: `{total_spent:.2f}`\n\n"
        f"🎯 Can generate: `{can_generate}` more accounts\n"
        f"💵 Cost per generation: `{GENERATION_COST}`",
        parse_mode=ParseMode.MARKDOWN
    )


# ==================== Owner Commands ====================

async def allow_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /allow command - supports @username"""
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await update.message.reply_text("🚫 This command is only available to the owner.")
        return
    
    db = await get_database()
    
    if len(context.args) < 1:
        await update.message.reply_text(
            "❌ *Usage:*\n"
            "`/allow @username credits` - Add by username\n"
            "`/allow 123456789 credits` - Add by ID\n"
            "Or reply to user's message with `/allow credits`\n\n"
            "*Example:* `/allow @john 30`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    target_user_id = None
    target_username = None
    credits = None
    
    # Check if replying to message (1 arg = credits)
    if update.message.reply_to_message and len(context.args) == 1:
        replied_user = update.message.reply_to_message.from_user
        if replied_user and not replied_user.is_bot:
            target_user_id = replied_user.id
            target_username = replied_user.username or replied_user.first_name
            try:
                credits = float(context.args[0])
            except ValueError:
                await update.message.reply_text("❌ Invalid credits amount.")
                return
        else:
            await update.message.reply_text("❌ Cannot add a bot.")
            return
    elif len(context.args) >= 2:
        user_ref = context.args[0].lstrip("@")
        try:
            credits = float(context.args[1])
        except ValueError:
            await update.message.reply_text("❌ Invalid credits amount.")
            return
        
        # Try as ID first
        try:
            target_user_id = int(user_ref)
            target_username = user_ref
        except ValueError:
            # Try username lookup or use reply
            if update.message.reply_to_message:
                replied_user = update.message.reply_to_message.from_user
                if replied_user and not replied_user.is_bot:
                    target_user_id = replied_user.id
                    target_username = replied_user.username or user_ref
                else:
                    await update.message.reply_text(
                        f"❌ Cannot resolve `@{user_ref}`\n\n"
                        "Please have the user message the bot first, or use their numeric ID.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return
            else:
                await update.message.reply_text(
                    f"❌ Cannot resolve `@{user_ref}`\n\n"
                    "Please reply to their message, or use their numeric ID:\n"
                    "`/allow 123456789 30`",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
    else:
        await update.message.reply_text(
            "❌ *Usage:*\n`/allow @username credits`\nor\n`/allow user_id credits`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if credits <= 0:
        await update.message.reply_text("❌ Credits must be positive.")
        return
    
    success = await db.add_user(target_user_id, target_username, credits, user_id)
    
    if success:
        max_gens = int(credits / GENERATION_COST)
        await update.message.reply_text(
            f"✅ *User Added*\n\n"
            f"👤 User: @{target_username} (`{target_user_id}`)\n"
            f"💰 Credits: `{credits:.2f}`\n"
            f"📊 Can generate: `{max_gens}` accounts",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"🎉 *Welcome to Amazon Cookie Generator!*\n\n"
                     f"You have been granted access with:\n"
                     f"💰 Credits: `{credits:.2f}`\n"
                     f"💵 Cost per generation: `{GENERATION_COST}`\n\n"
                     f"Use /gen to start generating cookies.",
                parse_mode=ParseMode.MARKDOWN
            )
        except:
            pass
    else:
        await update.message.reply_text("❌ Failed to add user.")


async def addcredits_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /addcredits command - supports @username"""
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await update.message.reply_text("🚫 This command is only available to the owner.")
        return
    
    db = await get_database()
    
    if len(context.args) < 1:
        await update.message.reply_text(
            "❌ *Usage:*\n"
            "`/addcredits @username amount`\n"
            "`/addcredits user_id amount`\n"
            "Or reply to user + `/addcredits amount`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    target_user_id = None
    target_username = None
    amount = None
    
    # Reply mode
    if update.message.reply_to_message and len(context.args) == 1:
        replied_user = update.message.reply_to_message.from_user
        if replied_user and not replied_user.is_bot:
            target_user_id = replied_user.id
            target_username = replied_user.username or replied_user.first_name
            try:
                amount = float(context.args[0])
            except ValueError:
                await update.message.reply_text("❌ Invalid amount.")
                return
        else:
            await update.message.reply_text("❌ Cannot add credits to a bot.")
            return
    elif len(context.args) >= 2:
        user_ref = context.args[0].lstrip("@")
        try:
            amount = float(context.args[1])
        except ValueError:
            await update.message.reply_text("❌ Invalid amount.")
            return
        
        try:
            target_user_id = int(user_ref)
            user_info = await db.get_user_info(target_user_id)
            target_username = user_info.get("username", str(target_user_id)) if user_info else user_ref
        except ValueError:
            # Username lookup
            user_info = await db.get_user_by_username(user_ref)
            if user_info:
                target_user_id = user_info["user_id"]
                target_username = user_info["username"]
            else:
                await update.message.reply_text(
                    f"❌ User `@{user_ref}` not found.\n"
                    "User must be added first with `/allow`",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
    else:
        await update.message.reply_text("❌ Invalid usage. See /help for examples.")
        return
    
    if amount <= 0:
        await update.message.reply_text("❌ Amount must be positive.")
        return
    
    success, new_balance = await db.add_credits(target_user_id, amount, user_id)
    
    if success:
        await update.message.reply_text(
            f"✅ *Credits Added*\n\n"
            f"👤 User: @{target_username} (`{target_user_id}`)\n"
            f"💵 Added: `+{amount:.2f}`\n"
            f"💰 New Balance: `{new_balance:.2f}`",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"💰 *Credits Added!*\n\n"
                     f"Amount: `+{amount:.2f}`\n"
                     f"New Balance: `{new_balance:.2f}`",
                parse_mode=ParseMode.MARKDOWN
            )
        except:
            pass
    else:
        await update.message.reply_text(
            "❌ Failed to add credits.\n"
            "Make sure the user exists (use `/allow` first).",
            parse_mode=ParseMode.MARKDOWN
        )


async def remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /remove command"""
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await update.message.reply_text("🚫 Owner only.")
        return
    
    target_user_id, target_username = await resolve_user(context, context.args, update)
    
    if not target_user_id:
        await update.message.reply_text(
            "❌ *Usage:* `/remove @username` or `/remove user_id`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    db = await get_database()
    success = await db.remove_user(target_user_id, user_id)
    
    if success:
        await update.message.reply_text(
            f"✅ *User Removed*\n\n"
            f"👤 @{target_username} (`{target_user_id}`) has been removed.",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text("❌ Failed to remove user.")


async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /users command"""
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await update.message.reply_text("🚫 Owner only.")
        return
    
    db = await get_database()
    users = await db.get_all_users()
    
    if not users:
        await update.message.reply_text("📋 No users found.")
        return
    
    message = "👥 *All Users*\n\n"
    
    for i, user in enumerate(users[:20], 1):
        username = user.get("username", "Unknown")
        uid = user.get("user_id")
        credits = user.get("credits", 0)
        accounts = user.get("accounts_generated", 0)
        
        message += f"{i}. @{username} (`{uid}`)\n"
        message += f"   💰 {credits:.2f} | 📊 {accounts} accounts\n\n"
    
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)


async def sessions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /sessions command"""
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await update.message.reply_text("🚫 Owner only.")
        return
    
    db = await get_database()
    await db.cleanup_expired_sessions()
    sessions = await db.get_all_active_sessions()
    
    active_count = len(active_cookie_sessions)
    
    message = f"🔐 *Active Sessions*\n"
    message += f"Memory: {active_count} | Database: {len(sessions)}\n\n"
    
    if active_cookie_sessions:
        message += "*In-Memory Sessions (Browser Active):*\n"
        for uid, sess in active_cookie_sessions.items():
            sid = sess.get("session_id", "?")
            expires = sess.get("expires_at", datetime.now())
            remaining = (expires - datetime.now()).total_seconds() / 60
            message += f"• `{sid}` - User {uid} - {remaining:.1f}min left\n"
        message += "\n"
    
    if sessions:
        message += "*Database Sessions:*\n"
        for s in sessions[:10]:
            message += f"• `{s['session_id'][:8]}` - @{s.get('username', '?')}\n"
    
    if not sessions and not active_cookie_sessions:
        message += "_No active sessions_"
    
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)


async def mysessions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /mysessions command"""
    user_id = update.effective_user.id
    
    if not await check_access(user_id):
        await update.message.reply_text("🚫 No access.")
        return
    
    message = "🔐 *Your Sessions*\n\n"
    
    if user_id in active_cookie_sessions:
        sess = active_cookie_sessions[user_id]
        sid = sess.get("session_id", "?")
        expires = sess.get("expires_at", datetime.now())
        remaining = max(0, (expires - datetime.now()).total_seconds() / 60)
        
        message += f"🟢 *Active Session*\n"
        message += f"🆔 ID: `{sid}`\n"
        message += f"⏱️ Time left: *{remaining:.1f} minutes*\n\n"
        message += "Use /cancel to end this session."
    else:
        message += "_No active sessions_\n\n"
        message += "Use /gen to create a new account."
    
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)


async def killsession_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /killsession command"""
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await update.message.reply_text("🚫 Owner only.")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /killsession <session_id|all>")
        return
    
    if context.args[0].lower() == "all":
        count = len(active_cookie_sessions)
        for uid in list(active_cookie_sessions.keys()):
            sess = active_cookie_sessions[uid]
            task = sess.get("countdown_task")
            if task and not task.done():
                task.cancel()
            del active_cookie_sessions[uid]
        
        db = await get_database()
        db_count = await db.delete_all_sessions()
        
        await update.message.reply_text(f"✅ Killed {count} memory + {db_count} DB sessions.")
    else:
        session_id = context.args[0]
        found = False
        
        for uid, sess in list(active_cookie_sessions.items()):
            if sess.get("session_id", "").startswith(session_id):
                task = sess.get("countdown_task")
                if task and not task.done():
                    task.cancel()
                del active_cookie_sessions[uid]
                found = True
                break
        
        if found:
            await update.message.reply_text(f"✅ Session `{session_id}` killed.")
        else:
            await update.message.reply_text(f"❌ Session `{session_id}` not found.")


async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /logs command"""
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await update.message.reply_text("🚫 Owner only.")
        return
    
    db = await get_database()
    logs = await db.get_recent_logs(20)
    
    if not logs:
        await update.message.reply_text("📋 No logs found.")
        return
    
    message = "📜 *Recent Logs*\n\n"
    
    for log in logs[:15]:
        ts = log.get("timestamp", "?")
        action = log.get("action", "?")
        details = log.get("details", "")[:50]
        message += f"• `{ts}`\n  {action}: {details}\n\n"
    
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)


async def set5sim_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /set5sim command"""
    global FIVESIM_API_KEY
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await update.message.reply_text("🚫 Owner only.")
        return
    
    if not context.args:
        current = FIVESIM_API_KEY[:10] + "..." if FIVESIM_API_KEY else "Not set"
        await update.message.reply_text(f"Current 5sim API: `{current}`\n\nUsage: `/set5sim YOUR_API_KEY`", parse_mode=ParseMode.MARKDOWN)
        return
    
    FIVESIM_API_KEY = context.args[0]
    await update.message.reply_text(f"✅ 5sim API key updated: `{FIVESIM_API_KEY[:10]}...`", parse_mode=ParseMode.MARKDOWN)


# ==================== Error Handler ====================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import traceback
    
    logger.error(f"Error: {context.error}")
    
    user_id = 0
    username = "Unknown"
    if update and update.effective_user:
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
    
    tb_str = "".join(traceback.format_exception(type(context.error), context.error, context.error.__traceback__))
    
    try:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=f"🚨 *ERROR*\n\n👤 @{username} ({user_id})\n❌ {str(context.error)[:200]}\n\n```\n{tb_str[:1000]}\n```",
            parse_mode=ParseMode.MARKDOWN
        )
    except:
        pass
    
    if update and update.effective_message:
        await update.effective_message.reply_text("❌ An error occurred. The owner has been notified.")


# ==================== Main ====================

async def post_init(application):
    await get_database()
    logger.info("Database initialized")
    
    from telegram import BotCommand, BotCommandScopeChat
    
    user_commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("gen", "Generate Amazon account"),
        BotCommand("cancel", "Cancel/end session"),
        BotCommand("balance", "Check credits"),
        BotCommand("mysessions", "View sessions"),
        BotCommand("help", "Show help"),
    ]
    
    owner_commands = user_commands + [
        BotCommand("allow", "Add user"),
        BotCommand("addcredits", "Add credits"),
        BotCommand("remove", "Remove user"),
        BotCommand("users", "List users"),
        BotCommand("sessions", "View sessions"),
        BotCommand("killsession", "Kill session"),
        BotCommand("logs", "View logs"),
    ]
    
    try:
        await application.bot.set_my_commands(user_commands)
        await application.bot.set_my_commands(owner_commands, scope=BotCommandScopeChat(chat_id=OWNER_ID))
    except Exception as e:
        logger.error(f"Failed to set commands: {e}")
    
    try:
        await application.bot.send_message(
            chat_id=OWNER_ID,
            text=f"🟢 *Bot Online!*\n\n"
                 f"⏱️ Session: {SESSION_DURATION_MINUTES} min\n"
                 f"💰 Cost: {GENERATION_COST} credits\n"
                 f"🔧 Concurrent sessions: Enabled\n"
                 f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            parse_mode=ParseMode.MARKDOWN
        )
    except:
        pass


async def post_shutdown(application):
    try:
        await application.bot.send_message(OWNER_ID, "🔴 *Bot Offline*", parse_mode=ParseMode.MARKDOWN)
    except:
        pass
    await close_database()


def main():
    print("🤖 Starting Amazon Cookie Generator Bot...")
    
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .concurrent_updates(True)  # Enable concurrent updates
        .build()
    )
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("gen", gen_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("allow", allow_command))
    application.add_handler(CommandHandler("addcredits", addcredits_command))
    application.add_handler(CommandHandler("set5sim", set5sim_command))
    application.add_handler(CommandHandler("remove", remove_command))
    application.add_handler(CommandHandler("users", users_command))
    application.add_handler(CommandHandler("sessions", sessions_command))
    application.add_handler(CommandHandler("mysessions", mysessions_command))
    application.add_handler(CommandHandler("killsession", killsession_command))
    application.add_handler(CommandHandler("logs", logs_command))
    
    application.add_handler(CallbackQueryHandler(country_callback, pattern="^gen_"))
    
    application.add_error_handler(error_handler)
    
    print(f"✅ Bot started!")
    print(f"👑 Owner: {OWNER_ID}")
    print(f"⏱️ Session: {SESSION_DURATION_MINUTES} min")
    print(f"💰 Cost: {GENERATION_COST} credits")
    print("\nPress Ctrl+C to stop.")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
