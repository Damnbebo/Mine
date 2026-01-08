<?php
/**
 * FWChecker Security Bot - Advanced Fail2Ban Management
 */

$BOT_TOKEN = '8335665121:AAGs-MzdlIxX6vP5lC09v57BlHOI6Bq4UOo';
$ADMIN_IDS = ['533082163'];
$SERVER_NAME = 'FWChecker VPS';

$update = json_decode(file_get_contents('php://input'), true);
if (!$update) exit;

$message = $update['message'] ?? $update['callback_query']['message'] ?? null;
$callback = $update['callback_query'] ?? null;
if (!$message && !$callback) exit;

$chatId = $message['chat']['id'] ?? $callback['message']['chat']['id'];
$userId = (string)($message['from']['id'] ?? $callback['from']['id'] ?? '');
$text = trim($message['text'] ?? '');
$username = $message['from']['username'] ?? 'Unknown';
$messageId = $message['message_id'] ?? null;

// Security
if (!in_array($userId, $ADMIN_IDS)) {
    sendMsg($chatId, "🚫 *Access Denied*\n\nYour ID: `$userId`");
    exit;
}

@file_put_contents('/var/log/security_bot.log', date('Y-m-d H:i:s')." @$username: $text\n", FILE_APPEND);

// Callbacks
if ($callback) {
    $data = $callback['data'];
    file_get_contents("https://api.telegram.org/bot$BOT_TOKEN/answerCallbackQuery?callback_query_id=".$callback['id']);
    switch($data) {
        case 'status': showStatus($chatId); break;
        case 'banned': showBanned($chatId); break;
        case 'attacks': showAttacks($chatId); break;
        case 'health': showHealth($chatId); break;
        case 'jails': showJails($chatId); break;
        case 'report': showReport($chatId); break;
        case 'help': showHelp($chatId); break;
    }
    exit;
}

// Commands
$parts = preg_split('/\s+/', $text);
$cmd = strtolower($parts[0] ?? '');
$arg1 = $parts[1] ?? '';
$arg2 = $parts[2] ?? '';

switch($cmd) {
    case '/start': case '/menu': showMenu($chatId); break;
    case '/help': showHelp($chatId); break;
    case '/status': case '/s': showStatus($chatId); break;
    case '/banned': case '/list': case '/b': showBanned($chatId, $arg1); break;
    case '/ban': doBan($chatId, $arg1, $arg2 ?: 'sshd'); break;
    case '/unban': case '/u': doUnban($chatId, $arg1, $arg2 ?: 'all'); break;
    case '/logs': case '/why': case '/l': showLogs($chatId, $arg1); break;
    case '/attacks': case '/a': showAttacks($chatId, $arg1 ?: 15); break;
    case '/jails': case '/j': showJails($chatId); break;
    case '/whitelist': case '/w': doWhitelist($chatId, $arg1); break;
    case '/restart': doRestart($chatId); break;
    case '/health': case '/h': showHealth($chatId); break;
    case '/report': case '/r': showReport($chatId); break;
    case '/lookup': case '/ip': lookupIP($chatId, $arg1); break;
    case '/config': showConfig($chatId); break;
    default:
        if (!empty($text) && $text[0] === '/') {
            sendMsg($chatId, "Unknown: `$cmd`\n\nUse /help");
        }
}

// === FUNCTIONS ===

function showMenu($chatId) {
    $msg = "🛡️ *FWChecker Security Bot*\n━━━━━━━━━━━━━━━━━━━━━━\n\n";
    $msg .= "Welcome! Manage Fail2Ban from Telegram.\n\n";
    $msg .= "🔐 *Features:*\n";
    $msg .= "├ Monitor banned IPs\n";
    $msg .= "├ Ban/Unban remotely\n";
    $msg .= "├ View attack logs\n";
    $msg .= "├ IP geolocation\n";
    $msg .= "└ Server health\n\n";
    $msg .= "Select below or type /help";
    sendMsg($chatId, $msg, mainKB());
}

function showHelp($chatId) {
    $msg = "📖 *All Commands*\n━━━━━━━━━━━━━━━━━━━━━━\n\n";
    $msg .= "*📊 STATUS*\n";
    $msg .= "`/status` `/s` - Jail overview\n";
    $msg .= "`/jails` `/j` - Jail details\n";
    $msg .= "`/banned` `/b` - Banned IPs\n";
    $msg .= "`/banned [jail]` - Specific jail\n\n";
    $msg .= "*🚫 BAN/UNBAN*\n";
    $msg .= "`/ban [IP]` - Ban (SSH)\n";
    $msg .= "`/ban [IP] [jail]` - Specific jail\n";
    $msg .= "`/unban [IP]` - Unban all\n";
    $msg .= "`/unban [IP] [jail]` - Specific\n\n";
    $msg .= "*🔍 INVESTIGATE*\n";
    $msg .= "`/logs [IP]` `/why` - Attack details\n";
    $msg .= "`/lookup [IP]` - IP location\n";
    $msg .= "`/attacks [n]` - Recent attacks\n\n";
    $msg .= "*⚙️ MANAGE*\n";
    $msg .= "`/whitelist [IP]` - Never ban\n";
    $msg .= "`/restart` - Restart F2B\n";
    $msg .= "`/config` - View config\n\n";
    $msg .= "*💻 SERVER*\n";
    $msg .= "`/health` `/h` - Resources\n";
    $msg .= "`/report` `/r` - Full report\n\n";
    $msg .= "💡 *Shortcuts:* /s /b /l /a /h /r";
    sendMsg($chatId, $msg);
}

function showStatus($chatId) {
    $output = shell_exec('sudo /usr/bin/fail2ban-client status 2>&1');
    preg_match('/Jail list:\s*(.+)/', $output, $m);
    
    $msg = "📊 *Fail2Ban Status*\n━━━━━━━━━━━━━━━━━━━━━━\n";
    $totalBanned = 0;
    
    if (isset($m[1])) {
        $jails = array_map('trim', explode(',', $m[1]));
        foreach ($jails as $jail) {
            $js = shell_exec("sudo /usr/bin/fail2ban-client status $jail 2>&1");
            preg_match('/Currently banned:\s*(\d+)/', $js, $b);
            preg_match('/Total banned:\s*(\d+)/', $js, $t);
            preg_match('/Currently failed:\s*(\d+)/', $js, $f);
            
            $banned = $b[1] ?? 0;
            $total = $t[1] ?? 0;
            $failed = $f[1] ?? 0;
            $totalBanned += $banned;
            
            $icon = $banned > 0 ? '🔴' : '🟢';
            $msg .= "\n$icon *$jail*\n";
            $msg .= "   ├ Banned: $banned | Total: $total\n";
            $msg .= "   └ Failed attempts: $failed\n";
        }
    }
    
    $msg .= "\n━━━━━━━━━━━━━━━━━━━━━━";
    $msg .= "\n📈 Currently blocking: *$totalBanned* IPs";
    $msg .= "\n⏰ " . date('M d, h:i:s A');
    
    sendMsg($chatId, $msg, statusKB());
}

function showBanned($chatId, $jail = 'all') {
    $jails = ($jail === 'all' || empty($jail)) ? ['sshd', 'nginx-http-auth', 'nginx-botsearch', 'fwchecker-admin'] : [$jail];
    $msg = "📋 *Banned IPs*\n━━━━━━━━━━━━━━━━━━━━━━\n";
    $total = 0;
    
    foreach ($jails as $j) {
        $output = shell_exec("sudo /usr/bin/fail2ban-client status $j 2>&1");
        preg_match('/Banned IP list:\s*(.*)/', $output, $m);
        $ips = trim($m[1] ?? '');
        
        if (!empty($ips)) {
            $ipList = explode(' ', $ips);
            $count = count($ipList);
            $total += $count;
            
            $msg .= "\n🔒 *$j* ($count)\n";
            foreach (array_slice($ipList, 0, 8) as $ip) {
                $msg .= "├ `$ip`\n";
            }
            if ($count > 8) $msg .= "└ _+" . ($count-8) . " more_\n";
        }
    }
    
    $msg .= $total === 0 ? "\n✅ No IPs banned!" : "\n━━━━━━━━━━━━━━━━━━━━━━\n📊 Total: *$total* banned";
    sendMsg($chatId, $msg);
}

function doBan($chatId, $ip, $jail) {
    if (empty($ip)) {
        sendMsg($chatId, "⚠️ *Usage:* `/ban [IP] [jail]`\n\n*Example:*\n`/ban 1.2.3.4`\n`/ban 1.2.3.4 nginx-http-auth`");
        return;
    }
    if (!filter_var($ip, FILTER_VALIDATE_IP)) {
        sendMsg($chatId, "❌ Invalid IP: `$ip`");
        return;
    }
    
    shell_exec("sudo /usr/bin/fail2ban-client set $jail banip $ip 2>&1");
    
    $msg = "🚫 *IP Banned*\n━━━━━━━━━━━━━━━━━━━━━━\n";
    $msg .= "\n🎯 IP: `$ip`";
    $msg .= "\n🔒 Jail: *$jail*";
    $msg .= "\n⏰ " . date('M d, h:i:s A');
    $msg .= "\n\n✅ Blocked from server!";
    
    sendMsg($chatId, $msg);
}

function doUnban($chatId, $ip, $jail) {
    if (empty($ip)) {
        sendMsg($chatId, "⚠️ *Usage:* `/unban [IP]`\n\n*Example:* `/unban 1.2.3.4`");
        return;
    }
    if (!filter_var($ip, FILTER_VALIDATE_IP)) {
        sendMsg($chatId, "❌ Invalid IP: `$ip`");
        return;
    }
    
    if ($jail === 'all') {
        $jails = ['sshd', 'nginx-http-auth', 'nginx-botsearch', 'fwchecker-admin'];
        foreach ($jails as $j) {
            shell_exec("sudo /usr/bin/fail2ban-client set $j unbanip $ip 2>&1");
        }
        sendMsg($chatId, "✅ *Unbanned* `$ip` from all jails");
    } else {
        shell_exec("sudo /usr/bin/fail2ban-client set $jail unbanip $ip 2>&1");
        sendMsg($chatId, "✅ *Unbanned* `$ip` from *$jail*");
    }
}

function showLogs($chatId, $ip) {
    if (empty($ip)) {
        sendMsg($chatId, "⚠️ *Usage:* `/logs [IP]`\n\nShows why an IP was banned.");
        return;
    }
    if (!filter_var($ip, FILTER_VALIDATE_IP)) {
        sendMsg($chatId, "❌ Invalid IP: `$ip`");
        return;
    }
    
    $msg = "🔍 *Attack Logs*\n━━━━━━━━━━━━━━━━━━━━━━\n🎯 IP: `$ip`\n";
    
    // SSH
    $ssh = shell_exec("grep '$ip' /var/log/auth.log 2>/dev/null | grep -E 'Failed|Invalid' | tail -8");
    if (!empty(trim($ssh))) {
        $msg .= "\n🔑 *SSH Attempts:*\n";
        foreach (explode("\n", trim($ssh)) as $line) {
            if (preg_match('/Failed password for (invalid user )?(\w+)/', $line, $m)) {
                $msg .= "❌ Failed: `" . $m[2] . "`\n";
            } elseif (preg_match('/Invalid user (\w+)/', $line, $m)) {
                $msg .= "⚠️ Invalid: `" . $m[1] . "`\n";
            }
        }
    }
    
    // Nginx
    $nginx = shell_exec("grep '$ip' /var/log/nginx/access.log 2>/dev/null | tail -5");
    if (!empty(trim($nginx))) {
        $msg .= "\n🌐 *Web Requests:*\n";
        foreach (array_slice(explode("\n", trim($nginx)), 0, 5) as $line) {
            if (preg_match('/"(GET|POST) ([^"]{1,40}).*" (\d{3})/', $line, $m)) {
                $icon = $m[3] >= 400 ? '❌' : '✅';
                $msg .= "$icon `" . $m[1] . " " . substr($m[2],0,30) . "` (" . $m[3] . ")\n";
            }
        }
    }
    
    // F2B
    $f2b = shell_exec("grep '$ip' /var/log/fail2ban.log 2>/dev/null | tail -3");
    if (!empty(trim($f2b))) {
        $msg .= "\n🛡️ *Fail2Ban:*\n";
        foreach (explode("\n", trim($f2b)) as $line) {
            if (preg_match('/\[(\w+)\]\s+(Ban|Unban)/', $line, $m)) {
                $icon = $m[2] === 'Ban' ? '🚫' : '✅';
                $msg .= "$icon " . $m[2] . " in *" . $m[1] . "*\n";
            }
        }
    }
    
    if (strlen($msg) < 100) $msg .= "\n📭 No logs found";
    $msg .= "\n\n💡 `/lookup $ip` for location";
    
    sendMsg($chatId, $msg);
}

function showAttacks($chatId, $count = 15) {
    $count = min(max((int)$count, 5), 30);
    $msg = "⚔️ *Recent Attacks*\n━━━━━━━━━━━━━━━━━━━━━━\n";
    
    $attacks = shell_exec("grep -E 'Failed password|Invalid user' /var/log/auth.log 2>/dev/null | tail -$count");
    
    if (!empty(trim($attacks))) {
        $seen = [];
        foreach (explode("\n", trim($attacks)) as $line) {
            if (preg_match('/from ([\d.]+)/', $line, $ipM)) {
                $ip = $ipM[1];
                $user = 'unknown';
                if (preg_match('/for (invalid user )?(\w+)/', $line, $uM)) $user = $uM[2];
                $key = "$ip:$user";
                if (!isset($seen[$key])) {
                    $msg .= "❌ `$ip` → `$user`\n";
                    $seen[$key] = true;
                }
            }
        }
        $msg .= "\n📊 " . count($seen) . " unique attempts";
    } else {
        $msg .= "\n✅ No recent attacks!";
    }
    
    sendMsg($chatId, $msg);
}

function showJails($chatId) {
    $info = [
        'sshd' => ['🔑 SSH', '24h ban', '3 tries'],
        'nginx-http-auth' => ['🔐 Web Auth', '2h ban', '5 tries'],
        'nginx-botsearch' => ['🤖 Bots', '4h ban', '2 tries'],
        'fwchecker-admin' => ['👤 Admin', '6h ban', '5 tries']
    ];
    
    $msg = "🔒 *Jail Details*\n━━━━━━━━━━━━━━━━━━━━━━\n";
    
    foreach ($info as $jail => $i) {
        $status = shell_exec("sudo /usr/bin/fail2ban-client status $jail 2>&1");
        preg_match('/Currently banned:\s*(\d+)/', $status, $b);
        $icon = strpos($status, 'Currently') !== false ? '✅' : '❌';
        
        $msg .= "\n$icon *$jail*\n";
        $msg .= "   " . $i[0] . " | " . $i[1] . " | " . $i[2] . "\n";
        $msg .= "   Banned: *" . ($b[1] ?? 0) . "*\n";
    }
    
    sendMsg($chatId, $msg);
}

function doWhitelist($chatId, $ip) {
    if (empty($ip)) {
        sendMsg($chatId, "⚠️ *Usage:* `/whitelist [IP]`\n\nNever ban this IP.");
        return;
    }
    if (!filter_var($ip, FILTER_VALIDATE_IP)) {
        sendMsg($chatId, "❌ Invalid IP: `$ip`");
        return;
    }
    
    $config = @file_get_contents('/etc/fail2ban/jail.local');
    if (strpos($config, $ip) !== false) {
        sendMsg($chatId, "⚠️ `$ip` already whitelisted");
        return;
    }
    
    $config = preg_replace('/(ignoreip\s*=\s*[^\n]+)/', '$1 ' . $ip, $config);
    @file_put_contents('/etc/fail2ban/jail.local', $config);
    shell_exec("sudo /usr/bin/fail2ban-client unban $ip 2>&1");
    shell_exec('sudo /bin/systemctl reload fail2ban 2>&1');
    
    sendMsg($chatId, "✅ *Whitelisted* `$ip`\n\nThis IP will never be banned.");
}

function doRestart($chatId) {
    sendMsg($chatId, "🔄 Restarting Fail2Ban...");
    shell_exec('sudo /bin/systemctl restart fail2ban 2>&1');
    sleep(2);
    $status = trim(shell_exec('sudo /bin/systemctl is-active fail2ban 2>&1'));
    
    if ($status === 'active') {
        sendMsg($chatId, "✅ *Restarted!*\n\nFail2Ban is active.");
    } else {
        sendMsg($chatId, "❌ *Failed!*\n\nStatus: $status");
    }
}

function showHealth($chatId) {
    $uptime = trim(shell_exec('uptime -p'));
    $load = trim(shell_exec("cat /proc/loadavg | awk '{print \$1, \$2, \$3}'"));
    $disk = trim(shell_exec("df -h / | awk 'NR==2 {print \$3\"/\"\$2\" (\"\$5\")\"}'"));
    $mem = trim(shell_exec("free -h | awk 'NR==2 {print \$3\"/\"\$2}'"));
    
    $f2b = trim(shell_exec('systemctl is-active fail2ban'));
    $nginx = trim(shell_exec('systemctl is-active nginx'));
    $mysql = trim(shell_exec('systemctl is-active mysql'));
    
    $msg = "💻 *Server Health*\n━━━━━━━━━━━━━━━━━━━━━━\n";
    $msg .= "\n⏱️ *Uptime:* $uptime";
    $msg .= "\n📊 *Load:* `$load`";
    $msg .= "\n💾 *Disk:* $disk";
    $msg .= "\n🧠 *Memory:* $mem";
    $msg .= "\n\n🔧 *Services:*";
    $msg .= "\n├ Fail2Ban: " . ($f2b === 'active' ? '🟢' : '🔴');
    $msg .= "\n├ Nginx: " . ($nginx === 'active' ? '🟢' : '🔴');
    $msg .= "\n└ MySQL: " . ($mysql === 'active' ? '🟢' : '🔴');
    $msg .= "\n\n⏰ " . date('M d, h:i:s A');
    
    sendMsg($chatId, $msg);
}

function showReport($chatId) {
    $sshTotal = trim(shell_exec("sudo /usr/bin/fail2ban-client status sshd 2>&1 | grep 'Total banned' | awk '{print \$NF}'"));
    $attacks = trim(shell_exec("grep -c 'Failed password' /var/log/auth.log 2>/dev/null"));
    $unique = trim(shell_exec("grep 'Failed password' /var/log/auth.log 2>/dev/null | grep -oP 'from \K[\d.]+' | sort -u | wc -l"));
    
    $msg = "📊 *Security Report*\n━━━━━━━━━━━━━━━━━━━━━━\n";
    $msg .= "📅 " . date('F d, Y') . "\n";
    $msg .= "\n🛡️ *Stats:*";
    $msg .= "\n├ Total blocked: *$sshTotal*";
    $msg .= "\n├ Attack attempts: *$attacks*";
    $msg .= "\n└ Unique attackers: *$unique*";
    
    // Top attackers
    $top = shell_exec("grep 'Failed password' /var/log/auth.log 2>/dev/null | grep -oP 'from \K[\d.]+' | sort | uniq -c | sort -rn | head -5");
    if (!empty(trim($top))) {
        $msg .= "\n\n🎯 *Top Attackers:*";
        foreach (explode("\n", trim($top)) as $line) {
            if (preg_match('/(\d+)\s+([\d.]+)/', $line, $m)) {
                $msg .= "\n├ `" . $m[2] . "` - " . $m[1] . "x";
            }
        }
    }
    
    $msg .= "\n\n✅ Protected by Fail2Ban";
    sendMsg($chatId, $msg);
}

function lookupIP($chatId, $ip) {
    if (empty($ip)) {
        sendMsg($chatId, "⚠️ *Usage:* `/lookup [IP]`");
        return;
    }
    if (!filter_var($ip, FILTER_VALIDATE_IP)) {
        sendMsg($chatId, "❌ Invalid IP: `$ip`");
        return;
    }
    
    $data = @file_get_contents("http://ip-api.com/json/$ip?fields=status,country,countryCode,city,isp,org,proxy,hosting");
    $info = json_decode($data, true);
    
    if (!$info || $info['status'] !== 'success') {
        sendMsg($chatId, "❌ Lookup failed for `$ip`");
        return;
    }
    
    $flags = ['US'=>'🇺🇸','CN'=>'🇨🇳','RU'=>'🇷🇺','BR'=>'🇧🇷','IN'=>'🇮🇳','DE'=>'🇩🇪','FR'=>'🇫🇷','GB'=>'🇬🇧','NL'=>'🇳🇱'];
    $flag = $flags[$info['countryCode']] ?? '🌍';
    
    $msg = "🌍 *IP Lookup*\n━━━━━━━━━━━━━━━━━━━━━━\n";
    $msg .= "\n🎯 IP: `$ip`";
    $msg .= "\n\n📍 *Location:*";
    $msg .= "\n├ " . $info['country'] . " $flag";
    $msg .= "\n└ " . $info['city'];
    $msg .= "\n\n🏢 *Network:*";
    $msg .= "\n├ " . $info['isp'];
    $msg .= "\n└ " . $info['org'];
    
    if ($info['proxy'] || $info['hosting']) {
        $msg .= "\n\n⚠️ *Flags:*";
        if ($info['proxy']) $msg .= "\n🔴 Proxy/VPN";
        if ($info['hosting']) $msg .= "\n🟡 Hosting/DC";
    }
    
    sendMsg($chatId, $msg);
}

function showConfig($chatId) {
    $config = @file_get_contents('/etc/fail2ban/jail.local');
    preg_match('/ignoreip\s*=\s*([^\n]+)/', $config, $ignore);
    
    $msg = "⚙️ *Configuration*\n━━━━━━━━━━━━━━━━━━━━━━\n";
    $msg .= "\n📋 *Whitelisted IPs:*\n`" . trim($ignore[1] ?? 'none') . "`";
    $msg .= "\n\n📁 Config: `/etc/fail2ban/jail.local`";
    
    sendMsg($chatId, $msg);
}

// === KEYBOARDS ===
function mainKB() {
    return json_encode(['inline_keyboard' => [
        [['text' => '📊 Status', 'callback_data' => 'status'], ['text' => '📋 Banned', 'callback_data' => 'banned']],
        [['text' => '⚔️ Attacks', 'callback_data' => 'attacks'], ['text' => '💻 Health', 'callback_data' => 'health']],
        [['text' => '🔒 Jails', 'callback_data' => 'jails'], ['text' => '📊 Report', 'callback_data' => 'report']],
        [['text' => '📖 Help', 'callback_data' => 'help']]
    ]]);
}

function statusKB() {
    return json_encode(['inline_keyboard' => [
        [['text' => '🔄 Refresh', 'callback_data' => 'status'], ['text' => '📋 Banned', 'callback_data' => 'banned']],
        [['text' => '⚔️ Attacks', 'callback_data' => 'attacks'], ['text' => '📊 Report', 'callback_data' => 'report']]
    ]]);
}

// === SEND MESSAGE ===
function sendMsg($chatId, $text, $kb = null) {
    global $BOT_TOKEN;
    $data = ['chat_id' => $chatId, 'text' => $text, 'parse_mode' => 'Markdown', 'disable_web_page_preview' => true];
    if ($kb) $data['reply_markup'] = $kb;
    
    $ch = curl_init("https://api.telegram.org/bot$BOT_TOKEN/sendMessage");
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_exec($ch);
    curl_close($ch);
}
