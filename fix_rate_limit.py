#!/usr/bin/env python3
"""Fix rate limiting for Telegram progress updates"""

with open("/home/ubuntu/amazon-bot/telegram_bot.py", "r") as f:
    content = f.read()

# Add rate limiting variable at the top of process_queue_messages
old_while = '''        while not generation_done.is_set() or not progress_queue.empty():
            if user_id in active_generations and active_generations[user_id].get("cancelled"):
                return
            
            try:
                msg_type, msg_data = progress_queue.get_nowait()
                
                if msg_type == "progress":
                    progress_lines.append(msg_data)
                    if len(progress_lines) > 10:
                        progress_lines = progress_lines[-10:]
                    
                    progress_text = "\\n".join(progress_lines)
                    try:
                        await status_message.edit_text('''

new_while = '''        last_update_time = [0]  # Track last update time for rate limiting
        MIN_UPDATE_INTERVAL = 2.0  # Minimum seconds between updates
        
        while not generation_done.is_set() or not progress_queue.empty():
            if user_id in active_generations and active_generations[user_id].get("cancelled"):
                return
            
            try:
                msg_type, msg_data = progress_queue.get_nowait()
                
                if msg_type == "progress":
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

if old_while in content:
    content = content.replace(old_while, new_while)
    print("Added rate limiting to progress updates")
else:
    print("Could not find exact while loop match")

# Also add RetryAfter exception handling
old_except = '''                    except Exception as e:
                        if "not modified" not in str(e).lower():
                            logger.error(f"Failed to update progress: {e}")'''

new_except = '''                    except Exception as e:
                        error_str = str(e).lower()
                        if "retry" in error_str or "flood" in error_str:
                            # Rate limited by Telegram - wait and continue
                            await asyncio.sleep(3)
                        elif "not modified" not in error_str:
                            logger.error(f"Failed to update progress: {e}")'''

if old_except in content:
    content = content.replace(old_except, new_except)
    print("Added RetryAfter exception handling")
else:
    print("Could not find except block")

with open("/home/ubuntu/amazon-bot/telegram_bot.py", "w") as f:
    f.write(content)

print("Done!")
