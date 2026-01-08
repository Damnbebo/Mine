#!/usr/bin/env python3
"""
FWChecker Security Bot - Polling Mode
Manages Fail2Ban via Telegram
"""

import requests
import subprocess
import time
import json
import re
import logging
from datetime import datetime

# Configuration
BOT_TOKEN = '8335665121:AAGs-MzdlIxX6vP5lC09v57BlHOI6Bq4UOo'
ADMIN_IDS = ['533082163']
API_URL = f'https://api.telegram.org/bot{BOT_TOKEN}'

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/security_bot.log'),
        logging.StreamHandler()
    ]
)

def run_cmd(cmd):
    """Run shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {e}"

def send_message(chat_id, text, reply_markup=None):
    """Send message to Telegram"""
    data = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown',
        'disable_web_page_preview': True
    }
    if reply_markup:
        data['reply_markup'] = json.dumps(reply_markup)
    
    try:
        requests.post(f'{API_URL}/sendMessage', data=data, timeout=10)
    except Exception as e:
        logging.error(f"Failed to send message: {e}")

def answer_callback(callback_id):
    """Answer callback query"""
    try:
        requests.post(f'{API_URL}/answerCallbackQuery', data={'callback_query_id': callback_id}, timeout=5)
    except:
        pass

def main_keyboard():
    return {
        'inline_keyboard': [
            [{'text': '📊 Status', 'callback_data': 'status'}, {'text': '📋 Banned', 'callback_data': 'banned'}],
            [{'text': '⚔️ Attacks', 'callback_data': 'attacks'}, {'text': '💻 Health', 'callback_data': 'health'}],
            [{'text': '🔒 Jails', 'callback_data': 'jails'}, {'text': '📊 Report', 'callback_data': 'report'}],
            [{'text': '📖 Help', 'callback_data': 'help'}]
        ]
    }

def status_keyboard():
    return {
        'inline_keyboard': [
            [{'text': '🔄 Refresh', 'callback_data': 'status'}, {'text': '📋 Banned', 'callback_data': 'banned'}],
            [{'text': '⚔️ Attacks', 'callback_data': 'attacks'}, {'text': '📊 Report', 'callback_data': 'report'}]
        ]
    }

# Command handlers
def cmd_start(chat_id):
    msg = """🛡️ *FWChecker Security Bot*
━━━━━━━━━━━━━━━━━━━━━━

Welcome! Manage Fail2Ban from Telegram.

🔐 *Features:*
├ Monitor banned IPs
├ Ban/Unban remotely
├ View attack logs
├ IP geolocation
└ Server health

Select below or type /help"""
    send_message(chat_id, msg, main_keyboard())

def cmd_help(chat_id):
    msg = """📖 *All Commands*
━━━━━━━━━━━━━━━━━━━━━━

*📊 STATUS*
`/status` `/s` - Jail overview
`/jails` `/j` - Jail details
`/banned` `/b` - Banned IPs

*🚫 BAN/UNBAN*
`/ban [IP]` - Ban IP (SSH)
`/ban [IP] [jail]` - Specific jail
`/unban [IP]` - Unban from all

*🔍 INVESTIGATE*
`/logs [IP]` - Attack details
`/lookup [IP]` - IP location
`/attacks` - Recent attacks

*⚙️ MANAGE*
`/whitelist [IP]` - Never ban
`/restart` - Restart Fail2Ban
`/config` - View config

*💻 SERVER*
`/health` `/h` - Resources
`/report` `/r` - Full report

💡 *Shortcuts:* /s /b /l /a /h /r"""
    send_message(chat_id, msg)

def cmd_status(chat_id):
    output = run_cmd('sudo fail2ban-client status 2>&1')
    match = re.search(r'Jail list:\s*(.+)', output)
    
    msg = "📊 *Fail2Ban Status*\n━━━━━━━━━━━━━━━━━━━━━━\n"
    total_banned = 0
    
    if match:
        jails = [j.strip() for j in match.group(1).split(',')]
        for jail in jails:
            js = run_cmd(f'sudo fail2ban-client status {jail} 2>&1')
            banned = re.search(r'Currently banned:\s*(\d+)', js)
            total = re.search(r'Total banned:\s*(\d+)', js)
            failed = re.search(r'Currently failed:\s*(\d+)', js)
            
            b = int(banned.group(1)) if banned else 0
            t = total.group(1) if total else '0'
            f = failed.group(1) if failed else '0'
            total_banned += b
            
            icon = '🔴' if b > 0 else '🟢'
            msg += f"\n{icon} *{jail}*\n"
            msg += f"   ├ Banned: {b} | Total: {t}\n"
            msg += f"   └ Failed: {f}\n"
    
    msg += "\n━━━━━━━━━━━━━━━━━━━━━━"
    msg += f"\n📈 Currently blocking: *{total_banned}* IPs"
    msg += f"\n⏰ {datetime.now().strftime('%b %d, %I:%M:%S %p')}"
    
    send_message(chat_id, msg, status_keyboard())

def cmd_banned(chat_id, jail='all'):
    jails = ['sshd', 'nginx-http-auth', 'nginx-botsearch', 'fwchecker-admin'] if jail == 'all' else [jail]
    msg = "📋 *Banned IPs*\n━━━━━━━━━━━━━━━━━━━━━━\n"
    total = 0
    
    for j in jails:
        output = run_cmd(f'sudo fail2ban-client status {j} 2>&1')
        match = re.search(r'Banned IP list:\s*(.*)', output)
        ips = match.group(1).strip() if match else ''
        
        if ips:
            ip_list = ips.split()
            count = len(ip_list)
            total += count
            msg += f"\n🔒 *{j}* ({count})\n"
            for ip in ip_list[:8]:
                msg += f"├ `{ip}`\n"
            if count > 8:
                msg += f"└ _+{count-8} more_\n"
    
    if total == 0:
        msg += "\n✅ No IPs banned!"
    else:
        msg += f"\n━━━━━━━━━━━━━━━━━━━━━━\n📊 Total: *{total}* banned"
    
    send_message(chat_id, msg)

def cmd_ban(chat_id, ip, jail='sshd'):
    if not ip:
        send_message(chat_id, "⚠️ *Usage:* `/ban [IP] [jail]`\n\n*Example:*\n`/ban 1.2.3.4`\n`/ban 1.2.3.4 nginx-http-auth`")
        return
    
    # Validate IP
    if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
        send_message(chat_id, f"❌ Invalid IP: `{ip}`")
        return
    
    run_cmd(f'sudo fail2ban-client set {jail} banip {ip} 2>&1')
    
    msg = f"""🚫 *IP Banned*
━━━━━━━━━━━━━━━━━━━━━━

🎯 IP: `{ip}`
🔒 Jail: *{jail}*
⏰ {datetime.now().strftime('%b %d, %I:%M:%S %p')}

✅ Blocked from server!"""
    send_message(chat_id, msg)

def cmd_unban(chat_id, ip, jail='all'):
    if not ip:
        send_message(chat_id, "⚠️ *Usage:* `/unban [IP]`\n\n*Example:* `/unban 1.2.3.4`")
        return
    
    if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
        send_message(chat_id, f"❌ Invalid IP: `{ip}`")
        return
    
    if jail == 'all':
        jails = ['sshd', 'nginx-http-auth', 'nginx-botsearch', 'fwchecker-admin']
        for j in jails:
            run_cmd(f'sudo fail2ban-client set {j} unbanip {ip} 2>&1')
        send_message(chat_id, f"✅ *Unbanned* `{ip}` from all jails")
    else:
        run_cmd(f'sudo fail2ban-client set {jail} unbanip {ip} 2>&1')
        send_message(chat_id, f"✅ *Unbanned* `{ip}` from *{jail}*")

def cmd_logs(chat_id, ip):
    if not ip:
        send_message(chat_id, "⚠️ *Usage:* `/logs [IP]`\n\nShows why an IP was banned.")
        return
    
    if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
        send_message(chat_id, f"❌ Invalid IP: `{ip}`")
        return
    
    msg = f"🔍 *Attack Logs*\n━━━━━━━━━━━━━━━━━━━━━━\n🎯 IP: `{ip}`\n"
    
    # SSH logs
    ssh = run_cmd(f"grep '{ip}' /var/log/auth.log 2>/dev/null | grep -E 'Failed|Invalid' | tail -8")
    if ssh:
        msg += "\n🔑 *SSH Attempts:*\n"
        for line in ssh.split('\n')[:8]:
            m = re.search(r'Failed password for (invalid user )?(\w+)', line)
            if m:
                msg += f"❌ Failed: `{m.group(2)}`\n"
            else:
                m = re.search(r'Invalid user (\w+)', line)
                if m:
                    msg += f"⚠️ Invalid: `{m.group(1)}`\n"
    
    # Nginx logs
    nginx = run_cmd(f"grep '{ip}' /var/log/nginx/access.log 2>/dev/null | tail -5")
    if nginx:
        msg += "\n🌐 *Web Requests:*\n"
        for line in nginx.split('\n')[:5]:
            m = re.search(r'"(GET|POST) ([^"]{1,40}).*" (\d{3})', line)
            if m:
                icon = '❌' if int(m.group(3)) >= 400 else '✅'
                msg += f"{icon} `{m.group(1)} {m.group(2)[:30]}` ({m.group(3)})\n"
    
    # F2B logs
    f2b = run_cmd(f"grep '{ip}' /var/log/fail2ban.log 2>/dev/null | tail -3")
    if f2b:
        msg += "\n🛡️ *Fail2Ban:*\n"
        for line in f2b.split('\n')[:3]:
            m = re.search(r'\[(\w+)\]\s+(Ban|Unban)', line)
            if m:
                icon = '🚫' if m.group(2) == 'Ban' else '✅'
                msg += f"{icon} {m.group(2)} in *{m.group(1)}*\n"
    
    if len(msg) < 100:
        msg += "\n📭 No logs found"
    
    msg += f"\n\n💡 `/lookup {ip}` for location"
    send_message(chat_id, msg)

def cmd_attacks(chat_id, count=15):
    msg = "⚔️ *Recent Attacks*\n━━━━━━━━━━━━━━━━━━━━━━\n"
    
    attacks = run_cmd(f"grep -E 'Failed password|Invalid user' /var/log/auth.log 2>/dev/null | tail -{count}")
    
    if attacks:
        seen = {}
        for line in attacks.split('\n'):
            ip_m = re.search(r'from ([\d.]+)', line)
            if ip_m:
                ip = ip_m.group(1)
                user = 'unknown'
                user_m = re.search(r'for (invalid user )?(\w+)', line)
                if user_m:
                    user = user_m.group(2)
                key = f"{ip}:{user}"
                if key not in seen:
                    msg += f"❌ `{ip}` → `{user}`\n"
                    seen[key] = True
        msg += f"\n📊 {len(seen)} unique attempts"
    else:
        msg += "\n✅ No recent attacks!"
    
    send_message(chat_id, msg)

def cmd_jails(chat_id):
    info = {
        'sshd': ['🔑 SSH', '24h ban', '3 tries'],
        'nginx-http-auth': ['🔐 Web Auth', '2h ban', '5 tries'],
        'nginx-botsearch': ['🤖 Bots', '4h ban', '2 tries'],
        'fwchecker-admin': ['👤 Admin', '6h ban', '5 tries']
    }
    
    msg = "🔒 *Jail Details*\n━━━━━━━━━━━━━━━━━━━━━━\n"
    
    for jail, i in info.items():
        status = run_cmd(f'sudo fail2ban-client status {jail} 2>&1')
        banned = re.search(r'Currently banned:\s*(\d+)', status)
        icon = '✅' if 'Currently' in status else '❌'
        
        msg += f"\n{icon} *{jail}*\n"
        msg += f"   {i[0]} | {i[1]} | {i[2]}\n"
        msg += f"   Banned: *{banned.group(1) if banned else 0}*\n"
    
    send_message(chat_id, msg)

def cmd_whitelist(chat_id, ip):
    if not ip:
        send_message(chat_id, "⚠️ *Usage:* `/whitelist [IP]`\n\nNever ban this IP.")
        return
    
    if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
        send_message(chat_id, f"❌ Invalid IP: `{ip}`")
        return
    
    # Check if already whitelisted
    config = run_cmd('cat /etc/fail2ban/jail.local')
    if ip in config:
        send_message(chat_id, f"⚠️ `{ip}` already whitelisted")
        return
    
    # Add to whitelist
    run_cmd(f"sed -i 's/\\(ignoreip.*\\)/\\1 {ip}/' /etc/fail2ban/jail.local")
    run_cmd(f'sudo fail2ban-client unban {ip} 2>&1')
    run_cmd('sudo systemctl reload fail2ban')
    
    send_message(chat_id, f"✅ *Whitelisted* `{ip}`\n\nThis IP will never be banned.")

def cmd_restart(chat_id):
    send_message(chat_id, "🔄 Restarting Fail2Ban...")
    run_cmd('sudo systemctl restart fail2ban')
    time.sleep(2)
    status = run_cmd('systemctl is-active fail2ban')
    
    if status == 'active':
        send_message(chat_id, "✅ *Restarted!*\n\nFail2Ban is active.")
    else:
        send_message(chat_id, f"❌ *Failed!*\n\nStatus: {status}")

def cmd_health(chat_id):
    uptime = run_cmd('uptime -p')
    load = run_cmd("cat /proc/loadavg | awk '{print $1, $2, $3}'")
    disk = run_cmd("df -h / | awk 'NR==2 {print $3\"/\"$2\" (\"$5\")\"}'")
    mem = run_cmd("free -h | awk 'NR==2 {print $3\"/\"$2}'")
    
    f2b = run_cmd('systemctl is-active fail2ban')
    nginx = run_cmd('systemctl is-active nginx')
    mysql = run_cmd('systemctl is-active mysql')
    
    msg = f"""💻 *Server Health*
━━━━━━━━━━━━━━━━━━━━━━

⏱️ *Uptime:* {uptime}
📊 *Load:* `{load}`
💾 *Disk:* {disk}
🧠 *Memory:* {mem}

🔧 *Services:*
├ Fail2Ban: {'🟢' if f2b == 'active' else '🔴'}
├ Nginx: {'🟢' if nginx == 'active' else '🔴'}
└ MySQL: {'🟢' if mysql == 'active' else '🔴'}

⏰ {datetime.now().strftime('%b %d, %I:%M:%S %p')}"""
    
    send_message(chat_id, msg)

def cmd_report(chat_id):
    ssh_total = run_cmd("sudo fail2ban-client status sshd 2>&1 | grep 'Total banned' | awk '{print $NF}'")
    attacks = run_cmd("grep -c 'Failed password' /var/log/auth.log 2>/dev/null")
    unique = run_cmd("grep 'Failed password' /var/log/auth.log 2>/dev/null | grep -oP 'from \\K[\\d.]+' | sort -u | wc -l")
    
    msg = f"""📊 *Security Report*
━━━━━━━━━━━━━━━━━━━━━━
📅 {datetime.now().strftime('%B %d, %Y')}

🛡️ *Stats:*
├ Total blocked: *{ssh_total or 0}*
├ Attack attempts: *{attacks or 0}*
└ Unique attackers: *{unique or 0}*"""
    
    # Top attackers
    top = run_cmd("grep 'Failed password' /var/log/auth.log 2>/dev/null | grep -oP 'from \\K[\\d.]+' | sort | uniq -c | sort -rn | head -5")
    if top:
        msg += "\n\n🎯 *Top Attackers:*"
        for line in top.strip().split('\n')[:5]:
            m = re.search(r'(\d+)\s+([\d.]+)', line)
            if m:
                msg += f"\n├ `{m.group(2)}` - {m.group(1)}x"
    
    msg += "\n\n✅ Protected by Fail2Ban"
    send_message(chat_id, msg)

def cmd_lookup(chat_id, ip):
    if not ip:
        send_message(chat_id, "⚠️ *Usage:* `/lookup [IP]`")
        return
    
    if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
        send_message(chat_id, f"❌ Invalid IP: `{ip}`")
        return
    
    try:
        resp = requests.get(f'http://ip-api.com/json/{ip}?fields=status,country,countryCode,city,isp,org,proxy,hosting', timeout=10)
        info = resp.json()
        
        if info.get('status') != 'success':
            send_message(chat_id, f"❌ Lookup failed for `{ip}`")
            return
        
        flags = {'US':'🇺🇸','CN':'🇨🇳','RU':'🇷🇺','BR':'🇧🇷','IN':'🇮🇳','DE':'🇩🇪','FR':'🇫🇷','GB':'🇬🇧','NL':'🇳🇱'}
        flag = flags.get(info.get('countryCode', ''), '🌍')
        
        msg = f"""🌍 *IP Lookup*
━━━━━━━━━━━━━━━━━━━━━━

🎯 IP: `{ip}`

📍 *Location:*
├ {info.get('country', 'Unknown')} {flag}
└ {info.get('city', 'Unknown')}

🏢 *Network:*
├ {info.get('isp', 'Unknown')}
└ {info.get('org', 'Unknown')}"""
        
        if info.get('proxy') or info.get('hosting'):
            msg += "\n\n⚠️ *Flags:*"
            if info.get('proxy'):
                msg += "\n🔴 Proxy/VPN"
            if info.get('hosting'):
                msg += "\n🟡 Hosting/DC"
        
        send_message(chat_id, msg)
    except Exception as e:
        send_message(chat_id, f"❌ Lookup error: {e}")

def cmd_config(chat_id):
    config = run_cmd('cat /etc/fail2ban/jail.local')
    ignore = re.search(r'ignoreip\s*=\s*([^\n]+)', config)
    
    msg = f"""⚙️ *Configuration*
━━━━━━━━━━━━━━━━━━━━━━

📋 *Whitelisted IPs:*
`{ignore.group(1).strip() if ignore else 'none'}`

📁 Config: `/etc/fail2ban/jail.local`"""
    
    send_message(chat_id, msg)

def handle_message(message):
    """Process incoming message"""
    chat_id = message['chat']['id']
    user_id = str(message['from']['id'])
    text = message.get('text', '').strip()
    username = message['from'].get('username', 'Unknown')
    
    # Security check
    if user_id not in ADMIN_IDS:
        send_message(chat_id, f"🚫 *Access Denied*\n\nYour ID: `{user_id}`")
        logging.warning(f"Unauthorized access attempt by {username} ({user_id})")
        return
    
    logging.info(f"@{username}: {text}")
    
    # Parse command
    parts = text.split()
    cmd = parts[0].lower() if parts else ''
    arg1 = parts[1] if len(parts) > 1 else ''
    arg2 = parts[2] if len(parts) > 2 else ''
    
    # Route commands
    if cmd in ['/start', '/menu']:
        cmd_start(chat_id)
    elif cmd == '/help':
        cmd_help(chat_id)
    elif cmd in ['/status', '/s']:
        cmd_status(chat_id)
    elif cmd in ['/banned', '/list', '/b']:
        cmd_banned(chat_id, arg1 or 'all')
    elif cmd == '/ban':
        cmd_ban(chat_id, arg1, arg2 or 'sshd')
    elif cmd in ['/unban', '/u']:
        cmd_unban(chat_id, arg1, arg2 or 'all')
    elif cmd in ['/logs', '/why', '/l']:
        cmd_logs(chat_id, arg1)
    elif cmd in ['/attacks', '/a']:
        cmd_attacks(chat_id, int(arg1) if arg1.isdigit() else 15)
    elif cmd in ['/jails', '/j']:
        cmd_jails(chat_id)
    elif cmd in ['/whitelist', '/w']:
        cmd_whitelist(chat_id, arg1)
    elif cmd == '/restart':
        cmd_restart(chat_id)
    elif cmd in ['/health', '/h']:
        cmd_health(chat_id)
    elif cmd in ['/report', '/r']:
        cmd_report(chat_id)
    elif cmd in ['/lookup', '/ip']:
        cmd_lookup(chat_id, arg1)
    elif cmd == '/config':
        cmd_config(chat_id)
    elif text.startswith('/'):
        send_message(chat_id, f"Unknown: `{cmd}`\n\nUse /help")

def handle_callback(callback):
    """Process callback query"""
    chat_id = callback['message']['chat']['id']
    user_id = str(callback['from']['id'])
    data = callback['data']
    
    answer_callback(callback['id'])
    
    if user_id not in ADMIN_IDS:
        return
    
    if data == 'status':
        cmd_status(chat_id)
    elif data == 'banned':
        cmd_banned(chat_id)
    elif data == 'attacks':
        cmd_attacks(chat_id)
    elif data == 'health':
        cmd_health(chat_id)
    elif data == 'jails':
        cmd_jails(chat_id)
    elif data == 'report':
        cmd_report(chat_id)
    elif data == 'help':
        cmd_help(chat_id)

def main():
    """Main polling loop"""
    logging.info("🛡️ Security Bot started (polling mode)")
    
    # Send startup message
    for admin_id in ADMIN_IDS:
        send_message(admin_id, "🛡️ *Security Bot Online!*\n\n✅ Polling mode active\n\nType /start to begin!")
    
    offset = 0
    
    while True:
        try:
            resp = requests.get(
                f'{API_URL}/getUpdates',
                params={'offset': offset, 'timeout': 30},
                timeout=35
            )
            updates = resp.json().get('result', [])
            
            for update in updates:
                offset = update['update_id'] + 1
                
                if 'message' in update:
                    handle_message(update['message'])
                elif 'callback_query' in update:
                    handle_callback(update['callback_query'])
                    
        except requests.exceptions.Timeout:
            continue
        except Exception as e:
            logging.error(f"Error: {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()
