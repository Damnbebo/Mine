#!/usr/bin/env python3
"""
FWChecker Security Bot v2 - With GeoBlocking & Settings
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

# Country codes
COUNTRY_NAMES = {
    'cn': '🇨🇳 China', 'ru': '🇷🇺 Russia', 'kp': '🇰🇵 North Korea',
    'ir': '🇮🇷 Iran', 'br': '🇧🇷 Brazil', 'in': '🇮🇳 India',
    'vn': '🇻🇳 Vietnam', 'id': '🇮🇩 Indonesia', 'pk': '🇵🇰 Pakistan',
    'bd': '🇧🇩 Bangladesh', 'ng': '🇳🇬 Nigeria', 'ua': '🇺🇦 Ukraine',
    'ro': '🇷🇴 Romania', 'pl': '🇵🇱 Poland', 'tr': '🇹🇷 Turkey',
    'th': '🇹🇭 Thailand', 'ph': '🇵🇭 Philippines', 'mx': '🇲🇽 Mexico',
    'ar': '🇦🇷 Argentina', 'co': '🇨🇴 Colombia', 'kr': '🇰🇷 South Korea',
    'de': '🇩🇪 Germany', 'fr': '🇫🇷 France', 'gb': '🇬🇧 UK',
    'us': '🇺🇸 USA', 'ca': '🇨🇦 Canada', 'au': '🇦🇺 Australia'
}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('/var/log/security_bot.log'), logging.StreamHandler()]
)

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {e}"

def send_message(chat_id, text, reply_markup=None):
    data = {'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown', 'disable_web_page_preview': True}
    if reply_markup:
        data['reply_markup'] = json.dumps(reply_markup)
    try:
        requests.post(f'{API_URL}/sendMessage', data=data, timeout=10)
    except Exception as e:
        logging.error(f"Send failed: {e}")

def answer_callback(callback_id):
    try:
        requests.post(f'{API_URL}/answerCallbackQuery', data={'callback_query_id': callback_id}, timeout=5)
    except:
        pass

def main_keyboard():
    return {'inline_keyboard': [
        [{'text': '📊 Status', 'callback_data': 'status'}, {'text': '📋 Banned', 'callback_data': 'banned'}],
        [{'text': '⚔️ Attacks', 'callback_data': 'attacks'}, {'text': '💻 Health', 'callback_data': 'health'}],
        [{'text': '🌍 GeoBlock', 'callback_data': 'geoblock'}, {'text': '⚙️ Settings', 'callback_data': 'settings'}],
        [{'text': '📖 Help', 'callback_data': 'help'}]
    ]}

def status_keyboard():
    return {'inline_keyboard': [
        [{'text': '🔄 Refresh', 'callback_data': 'status'}, {'text': '📋 Banned', 'callback_data': 'banned'}],
        [{'text': '⚔️ Attacks', 'callback_data': 'attacks'}, {'text': '🌍 GeoBlock', 'callback_data': 'geoblock'}]
    ]}

def geo_keyboard():
    return {'inline_keyboard': [
        [{'text': '🇨🇳 Block China', 'callback_data': 'geo_cn'}, {'text': '🇷🇺 Block Russia', 'callback_data': 'geo_ru'}],
        [{'text': '🇰🇵 Block N.Korea', 'callback_data': 'geo_kp'}, {'text': '🇮🇷 Block Iran', 'callback_data': 'geo_ir'}],
        [{'text': '📋 List Blocked', 'callback_data': 'geo_list'}, {'text': '🔙 Back', 'callback_data': 'status'}]
    ]}

# === COMMAND HANDLERS ===

def cmd_start(chat_id):
    msg = """🛡️ *FWChecker Security Bot v2*
━━━━━━━━━━━━━━━━━━━━━━

Advanced server security management!

🔐 *Features:*
├ Fail2Ban management
├ 🌍 Country blocking
├ ⚙️ Ban time settings
├ IP investigation
└ Server health

Select below or type /help"""
    send_message(chat_id, msg, main_keyboard())

def cmd_help(chat_id):
    msg = """📖 *All Commands*
━━━━━━━━━━━━━━━━━━━━━━

*📊 STATUS*
`/status` - Jail overview
`/banned` - Banned IPs
`/attacks` - Recent attacks

*🚫 BAN/UNBAN*
`/ban [IP]` - Ban IP
`/unban [IP]` - Unban IP
`/logs [IP]` - Attack details

*🌍 COUNTRY BLOCKING*
`/geoblock [country]` - Block country
`/geounblock [country]` - Unblock
`/geocountries` - List blocked
`/geowhitelist [IP]` - Always allow IP

*⚙️ SETTINGS*
`/setbantime [jail] [time]` - Set ban duration
`/settings` - View current settings

*💻 SERVER*
`/health` - Server status
`/report` - Security report
`/lookup [IP]` - IP location

*Country codes:* cn, ru, kp, ir, br, in, vn, etc.
*Time formats:* 1h, 6h, 1d, 1w, 1m (month)"""
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
            bantime = run_cmd(f'sudo fail2ban-client get {jail} bantime 2>&1')
            
            b = int(banned.group(1)) if banned else 0
            t = total.group(1) if total else '0'
            total_banned += b
            
            # Convert bantime to readable
            try:
                bt = int(bantime)
                if bt >= 604800:
                    bt_str = f"{bt // 604800}w"
                elif bt >= 86400:
                    bt_str = f"{bt // 86400}d"
                else:
                    bt_str = f"{bt // 3600}h"
            except:
                bt_str = "?"
            
            icon = '🔴' if b > 0 else '🟢'
            msg += f"\n{icon} *{jail}* ({bt_str} ban)\n"
            msg += f"   └ {b} banned | {t} total\n"
    
    # GeoBlock status
    geo_status = run_cmd('/opt/geoblock.sh status 2>&1')
    geo_countries = run_cmd('cat /etc/geoblock/blocked_countries.txt 2>/dev/null | wc -l')
    
    msg += f"\n🌍 *GeoBlock:* {geo_countries} countries blocked"
    msg += "\n━━━━━━━━━━━━━━━━━━━━━━"
    msg += f"\n📈 Total blocked: *{total_banned}* IPs"
    msg += f"\n⏰ {datetime.now().strftime('%b %d, %I:%M:%S %p')}"
    
    send_message(chat_id, msg, status_keyboard())

def cmd_banned(chat_id, jail='all'):
    jails = ['sshd', 'nginx-http-auth', 'nginx-botsearch', 'fwchecker-admin', 'recidive'] if jail == 'all' else [jail]
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
            for ip in ip_list[:6]:
                msg += f"├ `{ip}`\n"
            if count > 6:
                msg += f"└ _+{count-6} more_\n"
    
    msg += f"\n{'✅ No IPs banned!' if total == 0 else f'━━━━━━━━━━━━━━━━━━━━━━\n📊 Total: *{total}* banned'}"
    send_message(chat_id, msg)

def cmd_ban(chat_id, ip, jail='sshd'):
    if not ip:
        send_message(chat_id, "⚠️ *Usage:* `/ban [IP] [jail]`\n\n*Example:* `/ban 1.2.3.4`")
        return
    if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
        send_message(chat_id, f"❌ Invalid IP: `{ip}`")
        return
    
    run_cmd(f'sudo fail2ban-client set {jail} banip {ip} 2>&1')
    send_message(chat_id, f"🚫 *Banned* `{ip}` in *{jail}*")

def cmd_unban(chat_id, ip, jail='all'):
    if not ip:
        send_message(chat_id, "⚠️ *Usage:* `/unban [IP]`")
        return
    if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
        send_message(chat_id, f"❌ Invalid IP: `{ip}`")
        return
    
    if jail == 'all':
        for j in ['sshd', 'nginx-http-auth', 'nginx-botsearch', 'fwchecker-admin', 'recidive']:
            run_cmd(f'sudo fail2ban-client set {j} unbanip {ip} 2>&1')
        send_message(chat_id, f"✅ *Unbanned* `{ip}` from all jails")
    else:
        run_cmd(f'sudo fail2ban-client set {jail} unbanip {ip} 2>&1')
        send_message(chat_id, f"✅ *Unbanned* `{ip}` from *{jail}*")

def cmd_logs(chat_id, ip):
    if not ip:
        send_message(chat_id, "⚠️ *Usage:* `/logs [IP]`")
        return
    
    msg = f"🔍 *Logs for* `{ip}`\n━━━━━━━━━━━━━━━━━━━━━━\n"
    
    # SSH logs
    ssh = run_cmd(f"grep '{ip}' /var/log/auth.log 2>/dev/null | grep -E 'Failed|Invalid' | tail -5")
    if ssh:
        msg += "\n🔑 *SSH:*\n"
        for line in ssh.split('\n')[:5]:
            m = re.search(r'for (invalid user )?(\w+)', line)
            if m:
                msg += f"❌ `{m.group(2)}`\n"
    
    # GeoIP
    geo = run_cmd(f"geoiplookup {ip} 2>/dev/null")
    if geo and 'not found' not in geo.lower():
        country = geo.split(':')[-1].strip() if ':' in geo else geo
        msg += f"\n🌍 *Location:* {country}\n"
    
    if len(msg) < 80:
        msg += "\n📭 No logs found"
    
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
        msg += f"\n📊 {len(seen)} unique"
    else:
        msg += "\n✅ No attacks!"
    
    send_message(chat_id, msg)

def cmd_health(chat_id):
    uptime = run_cmd('uptime -p')
    load = run_cmd("cat /proc/loadavg | awk '{print $1, $2, $3}'")
    disk = run_cmd("df -h / | awk 'NR==2 {print $3\"/\"$2\" (\"$5\")\"}'")
    mem = run_cmd("free -h | awk 'NR==2 {print $3\"/\"$2}'")
    
    services = {'fail2ban': '🟢' if run_cmd('systemctl is-active fail2ban') == 'active' else '🔴',
                'nginx': '🟢' if run_cmd('systemctl is-active nginx') == 'active' else '🔴',
                'mysql': '🟢' if run_cmd('systemctl is-active mysql') == 'active' else '🔴'}
    
    msg = f"""💻 *Server Health*
━━━━━━━━━━━━━━━━━━━━━━

⏱️ {uptime}
📊 Load: `{load}`
💾 Disk: {disk}
🧠 Memory: {mem}

🔧 *Services:*
├ Fail2Ban: {services['fail2ban']}
├ Nginx: {services['nginx']}
└ MySQL: {services['mysql']}"""
    
    send_message(chat_id, msg)

def cmd_report(chat_id):
    ssh_total = run_cmd("sudo fail2ban-client status sshd 2>&1 | grep 'Total banned' | awk '{print $NF}'") or '0'
    attacks = run_cmd("grep -c 'Failed password' /var/log/auth.log 2>/dev/null") or '0'
    geo_blocked = run_cmd("cat /etc/geoblock/blocked_countries.txt 2>/dev/null | wc -l") or '0'
    
    msg = f"""📊 *Security Report*
━━━━━━━━━━━━━━━━━━━━━━

🛡️ *Fail2Ban:*
├ Total blocked: *{ssh_total}*
└ Attack attempts: *{attacks}*

🌍 *GeoBlock:*
└ Countries blocked: *{geo_blocked}*

✅ Protected"""
    send_message(chat_id, msg)

def cmd_lookup(chat_id, ip):
    if not ip or not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
        send_message(chat_id, "⚠️ *Usage:* `/lookup [IP]`")
        return
    
    try:
        resp = requests.get(f'http://ip-api.com/json/{ip}?fields=status,country,countryCode,city,isp,org,proxy,hosting', timeout=10)
        info = resp.json()
        
        if info.get('status') != 'success':
            send_message(chat_id, f"❌ Lookup failed for `{ip}`")
            return
        
        flags = {'US':'🇺🇸','CN':'🇨🇳','RU':'🇷🇺','BR':'🇧🇷','IN':'🇮🇳','DE':'🇩🇪','FR':'🇫🇷','GB':'🇬🇧','NL':'🇳🇱','KR':'🇰🇷','JP':'🇯🇵'}
        flag = flags.get(info.get('countryCode', ''), '🌍')
        
        msg = f"""🌍 *IP Lookup*
━━━━━━━━━━━━━━━━━━━━━━

🎯 IP: `{ip}`

📍 {info.get('country', '?')} {flag}
🏙️ {info.get('city', '?')}
🏢 {info.get('isp', '?')}"""
        
        if info.get('proxy'):
            msg += "\n\n⚠️ *Proxy/VPN detected!*"
        if info.get('hosting'):
            msg += "\n⚠️ *Hosting/Datacenter*"
        
        send_message(chat_id, msg)
    except Exception as e:
        send_message(chat_id, f"❌ Error: {e}")

# === GEO BLOCKING ===

def cmd_geoblock(chat_id, country=None):
    if not country:
        msg = """🌍 *Country Blocking*
━━━━━━━━━━━━━━━━━━━━━━

Block entire countries from accessing your server.

*Usage:* `/geoblock [code]`

*Popular codes:*
🇨🇳 `cn` - China
🇷🇺 `ru` - Russia  
🇰🇵 `kp` - North Korea
🇮🇷 `ir` - Iran
🇧🇷 `br` - Brazil
🇮🇳 `in` - India
🇻🇳 `vn` - Vietnam

*Example:* `/geoblock cn`"""
        send_message(chat_id, msg, geo_keyboard())
        return
    
    country = country.lower()
    name = COUNTRY_NAMES.get(country, country.upper())
    
    send_message(chat_id, f"🌍 Blocking {name}... (downloading IP list)")
    result = run_cmd(f'/opt/geoblock.sh block {country} 2>&1')
    
    if 'Downloaded' in result or 'Blocked' in result:
        send_message(chat_id, f"✅ *Blocked* {name}\n\nAll IPs from this country are now blocked.")
    else:
        send_message(chat_id, f"❌ Failed to block {country}\n\n{result}")

def cmd_geounblock(chat_id, country):
    if not country:
        send_message(chat_id, "⚠️ *Usage:* `/geounblock [code]`\n\n*Example:* `/geounblock cn`")
        return
    
    country = country.lower()
    name = COUNTRY_NAMES.get(country, country.upper())
    
    run_cmd(f'/opt/geoblock.sh unblock {country} 2>&1')
    send_message(chat_id, f"✅ *Unblocked* {name}")

def cmd_geocountries(chat_id):
    blocked = run_cmd('cat /etc/geoblock/blocked_countries.txt 2>/dev/null')
    
    msg = "🌍 *Blocked Countries*\n━━━━━━━━━━━━━━━━━━━━━━\n"
    
    if blocked:
        for code in blocked.split('\n'):
            code = code.strip().lower()
            if code:
                name = COUNTRY_NAMES.get(code, code.upper())
                msg += f"\n🚫 {name}"
        
        # Get IP count
        ip_count = run_cmd("ipset list geoblock 2>/dev/null | grep -c '^[0-9]'") or '0'
        msg += f"\n\n━━━━━━━━━━━━━━━━━━━━━━\n📊 Total: *{ip_count}* IP ranges blocked"
    else:
        msg += "\n✅ No countries blocked"
    
    msg += "\n\n_Use /geounblock [code] to remove_"
    send_message(chat_id, msg)

def cmd_geowhitelist(chat_id, ip):
    if not ip:
        # Show current whitelist
        whitelist = run_cmd('cat /etc/geoblock/whitelist.txt 2>/dev/null')
        msg = "🛡️ *Whitelisted IPs*\n━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += "_These IPs bypass country blocks:_\n\n"
        for line in whitelist.split('\n'):
            if line.strip() and not line.startswith(':'):
                msg += f"✅ `{line.strip()}`\n"
        msg += "\n_Use /geowhitelist [IP] to add_"
        send_message(chat_id, msg)
        return
    
    if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
        send_message(chat_id, f"❌ Invalid IP: `{ip}`")
        return
    
    run_cmd(f'/opt/geoblock.sh whitelist {ip} 2>&1')
    send_message(chat_id, f"✅ *Whitelisted* `{ip}`\n\nThis IP will always be allowed, even from blocked countries.")

# === SETTINGS ===

def cmd_setbantime(chat_id, jail, time_str):
    if not jail or not time_str:
        msg = """⚙️ *Set Ban Time*
━━━━━━━━━━━━━━━━━━━━━━

*Usage:* `/setbantime [jail] [time]`

*Jails:* sshd, nginx-http-auth, nginx-botsearch, fwchecker-admin, recidive

*Time formats:*
├ `1h` - 1 hour
├ `6h` - 6 hours
├ `1d` - 1 day
├ `1w` - 1 week
├ `1m` - 1 month

*Examples:*
`/setbantime sshd 1w` - SSH bans for 1 week
`/setbantime recidive 1m` - Repeat offenders 1 month"""
        send_message(chat_id, msg)
        return
    
    # Parse time
    time_str = time_str.lower()
    try:
        if time_str.endswith('h'):
            seconds = int(time_str[:-1]) * 3600
        elif time_str.endswith('d'):
            seconds = int(time_str[:-1]) * 86400
        elif time_str.endswith('w'):
            seconds = int(time_str[:-1]) * 604800
        elif time_str.endswith('m'):
            seconds = int(time_str[:-1]) * 2592000
        else:
            seconds = int(time_str)
    except:
        send_message(chat_id, "❌ Invalid time format. Use: 1h, 6h, 1d, 1w, 1m")
        return
    
    # Update jail.local
    run_cmd(f"sudo fail2ban-client set {jail} bantime {seconds} 2>&1")
    
    # Also update the config file for persistence
    run_cmd(f"sed -i '/\\[{jail}\\]/,/\\[/s/bantime = .*/bantime = {seconds}/' /etc/fail2ban/jail.local 2>/dev/null")
    
    send_message(chat_id, f"✅ *{jail}* ban time set to *{time_str}* ({seconds} seconds)")

def cmd_settings(chat_id):
    msg = "⚙️ *Current Settings*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Get ban times for each jail
    jails = ['sshd', 'nginx-http-auth', 'nginx-botsearch', 'fwchecker-admin', 'recidive']
    
    msg += "*Ban Times:*\n"
    for jail in jails:
        bantime = run_cmd(f'sudo fail2ban-client get {jail} bantime 2>&1')
        try:
            bt = int(bantime)
            if bt >= 2592000:
                bt_str = f"{bt // 2592000} month"
            elif bt >= 604800:
                bt_str = f"{bt // 604800} week"
            elif bt >= 86400:
                bt_str = f"{bt // 86400} day"
            else:
                bt_str = f"{bt // 3600} hour"
        except:
            bt_str = "?"
        msg += f"├ *{jail}*: {bt_str}\n"
    
    # Geo blocked
    geo_count = run_cmd("cat /etc/geoblock/blocked_countries.txt 2>/dev/null | wc -l") or '0'
    msg += f"\n*GeoBlock:*\n├ Countries: {geo_count}\n"
    
    # Whitelist count
    wl_count = run_cmd("cat /etc/geoblock/whitelist.txt 2>/dev/null | grep -v '^:' | wc -l") or '0'
    msg += f"└ Whitelisted IPs: {wl_count}\n"
    
    msg += "\n_Use /setbantime to change_"
    send_message(chat_id, msg)

# === MESSAGE HANDLER ===

def handle_message(message):
    chat_id = message['chat']['id']
    user_id = str(message['from']['id'])
    text = message.get('text', '').strip()
    username = message['from'].get('username', 'Unknown')
    
    if user_id not in ADMIN_IDS:
        send_message(chat_id, f"🚫 Access Denied\n\nID: `{user_id}`")
        return
    
    logging.info(f"@{username}: {text}")
    
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
    elif cmd in ['/banned', '/b']:
        cmd_banned(chat_id, arg1 or 'all')
    elif cmd == '/ban':
        cmd_ban(chat_id, arg1, arg2 or 'sshd')
    elif cmd in ['/unban', '/u']:
        cmd_unban(chat_id, arg1, arg2 or 'all')
    elif cmd in ['/logs', '/l']:
        cmd_logs(chat_id, arg1)
    elif cmd in ['/attacks', '/a']:
        cmd_attacks(chat_id, int(arg1) if arg1.isdigit() else 15)
    elif cmd in ['/health', '/h']:
        cmd_health(chat_id)
    elif cmd in ['/report', '/r']:
        cmd_report(chat_id)
    elif cmd in ['/lookup', '/ip']:
        cmd_lookup(chat_id, arg1)
    elif cmd == '/geoblock':
        cmd_geoblock(chat_id, arg1)
    elif cmd == '/geounblock':
        cmd_geounblock(chat_id, arg1)
    elif cmd in ['/geocountries', '/geo']:
        cmd_geocountries(chat_id)
    elif cmd == '/geowhitelist':
        cmd_geowhitelist(chat_id, arg1)
    elif cmd == '/setbantime':
        cmd_setbantime(chat_id, arg1, arg2)
    elif cmd == '/settings':
        cmd_settings(chat_id)
    elif cmd in ['/jails', '/j']:
        cmd_settings(chat_id)
    elif cmd in ['/whitelist', '/w']:
        # Fail2ban whitelist
        if arg1:
            run_cmd(f"sed -i 's/\\(ignoreip.*\\)/\\1 {arg1}/' /etc/fail2ban/jail.local")
            run_cmd(f'sudo fail2ban-client unban {arg1} 2>&1')
            run_cmd('sudo systemctl reload fail2ban')
            send_message(chat_id, f"✅ Whitelisted `{arg1}` in Fail2Ban")
        else:
            send_message(chat_id, "⚠️ Usage: `/whitelist [IP]`")
    elif cmd == '/restart':
        send_message(chat_id, "🔄 Restarting Fail2Ban...")
        run_cmd('sudo systemctl restart fail2ban')
        time.sleep(2)
        status = run_cmd('systemctl is-active fail2ban')
        send_message(chat_id, f"{'✅ Active!' if status == 'active' else '❌ Failed'}")
    elif text.startswith('/'):
        send_message(chat_id, f"Unknown: `{cmd}`\n\nUse /help")

def handle_callback(callback):
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
    elif data == 'geoblock':
        cmd_geoblock(chat_id)
    elif data == 'settings':
        cmd_settings(chat_id)
    elif data == 'help':
        cmd_help(chat_id)
    elif data == 'geo_list':
        cmd_geocountries(chat_id)
    elif data.startswith('geo_'):
        country = data[4:]
        cmd_geoblock(chat_id, country)

def main():
    logging.info("🛡️ Security Bot v2 started")
    
    for admin_id in ADMIN_IDS:
        send_message(admin_id, "🛡️ *Security Bot v2 Online!*\n\n✅ GeoBlocking enabled\n✅ Settings control\n\nType /start")
    
    offset = 0
    while True:
        try:
            resp = requests.get(f'{API_URL}/getUpdates', params={'offset': offset, 'timeout': 30}, timeout=35)
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
