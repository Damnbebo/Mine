<?php
// Fix path - Memory is in /admin/Memory/, config is in /site/
require_once dirname(__DIR__, 2) . '/config.php';

session_start();

// Check admin authentication
if (!isset($_SESSION['admin_authenticated']) || $_SESSION['admin_authenticated'] !== true) {
    header('Location: ../index.php');
    exit;
}

// Check PIN if required
if (!isset($_SESSION['pin_verified']) || $_SESSION['pin_verified'] !== true) {
    header('Location: ../index.php?need_pin=1');
    exit;
}

$currentUser = $_SESSION['admin_user'] ?? 'Admin';

$docFile = __DIR__ . '/SYSTEM_DOCUMENTATION.md';
$aiFile = __DIR__ . '/AI_CONTEXT.txt';
$secFile = __DIR__ . '/SECURITY_REPORT.md';
$docContent = file_exists($docFile) ? file_get_contents($docFile) : 'Documentation not found.';
$aiContent = file_exists($aiFile) ? file_get_contents($aiFile) : 'Context not found.';
$secContent = file_exists($secFile) ? file_get_contents($secFile) : 'Security report not found.';

// Simple Markdown to HTML conversion
function parseMarkdown($text) {
    $text = htmlspecialchars($text);
    $text = preg_replace('/^### (.+)$/m', '<h3>$1</h3>', $text);
    $text = preg_replace('/^## (.+)$/m', '<h2>$1</h2>', $text);
    $text = preg_replace('/^# (.+)$/m', '<h1>$1</h1>', $text);
    $text = preg_replace('/\*\*(.+?)\*\*/', '<strong>$1</strong>', $text);
    $text = preg_replace('/```(\w+)?\n([\s\S]*?)```/', '<pre class="code-block"><code>$2</code></pre>', $text);
    $text = preg_replace('/`([^`]+)`/', '<code class="inline-code">$1</code>', $text);
    $text = preg_replace('/^- (.+)$/m', '<li>$1</li>', $text);
    $text = preg_replace('/^---$/m', '<hr>', $text);
    $text = nl2br($text);
    return $text;
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>System Memory - FWChecker Admin</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 100%);
            color: #e0e0e0;
            min-height: 100vh;
            line-height: 1.6;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        
        .header {
            background: linear-gradient(135deg, #1e1e3f 0%, #2d2d5a 100%);
            padding: 20px 30px;
            border-radius: 15px;
            margin-bottom: 25px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }
        .header h1 { color: #fff; font-size: 1.8em; display: flex; align-items: center; gap: 10px; }
        .header-right { display: flex; gap: 15px; align-items: center; }
        .back-btn {
            background: linear-gradient(135deg, #3b82f6, #2563eb);
            color: #fff;
            padding: 10px 20px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 500;
            transition: transform 0.2s;
        }
        .back-btn:hover { transform: scale(1.05); }
        .admin-badge {
            background: linear-gradient(135deg, #8b5cf6, #7c3aed);
            color: #fff;
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 13px;
        }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .tab {
            padding: 12px 25px;
            background: rgba(255,255,255,0.1);
            border: none;
            border-radius: 10px;
            color: #e0e0e0;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
        }
        .tab:hover { background: rgba(255,255,255,0.15); }
        .tab.active {
            background: linear-gradient(135deg, #8b5cf6, #7c3aed);
            color: #fff;
        }
        
        .content-box {
            display: none;
            background: rgba(30, 30, 60, 0.8);
            padding: 30px;
            border-radius: 15px;
            border: 1px solid rgba(139,92,246,0.3);
            max-height: 70vh;
            overflow-y: auto;
            margin-bottom: 20px;
        }
        .content-box.active {
            display: block;
        }
        .content-box h1 { color: #a78bfa; margin: 20px 0 10px; font-size: 1.5em; }
        .content-box h2 { color: #8b5cf6; margin: 18px 0 8px; font-size: 1.3em; }
        .content-box h3 { color: #7c3aed; margin: 15px 0 8px; font-size: 1.1em; }
        .content-box p { margin-bottom: 10px; }
        .content-box hr { border: none; border-top: 1px solid rgba(139,92,246,0.3); margin: 20px 0; }
        .content-box li { margin-left: 20px; margin-bottom: 5px; }
        
        .code-block {
            background: #1a1a2e;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 10px 0;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            border: 1px solid rgba(139,92,246,0.2);
        }
        .inline-code {
            background: rgba(139,92,246,0.2);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }
        
        .action-btns {
            position: fixed;
            bottom: 20px;
            right: 20px;
            display: flex;
            gap: 10px;
        }
        .action-btn {
            padding: 12px 20px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-weight: bold;
            font-size: 13px;
            transition: transform 0.2s;
            text-decoration: none;
        }
        .action-btn:hover { transform: scale(1.05); }
        .copy-btn { background: linear-gradient(135deg, #4ade80, #22c55e); color: #000; }
        .copy-context-btn { background: linear-gradient(135deg, #f59e0b, #d97706); color: #000; }
        
        .quick-info {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
        }
        .info-card {
            background: linear-gradient(135deg, rgba(99,102,241,0.2), rgba(139,92,246,0.2));
            padding: 15px;
            border-radius: 10px;
            border: 1px solid rgba(139,92,246,0.3);
        }
        .info-card h4 { color: #a78bfa; margin-bottom: 5px; font-size: 11px; text-transform: uppercase; }
        .info-card p { color: #fff; font-size: 13px; font-family: monospace; }
        
        /* Scrollbar */
        .content-box::-webkit-scrollbar { width: 8px; }
        .content-box::-webkit-scrollbar-track { background: rgba(0,0,0,0.2); border-radius: 4px; }
        .content-box::-webkit-scrollbar-thumb { background: #8b5cf6; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 System Memory</h1>
            <div class="header-right">
                <span class="admin-badge">👤 <?php echo htmlspecialchars($currentUser); ?></span>
                <a href="../" class="back-btn">← Back to Admin</a>
            </div>
        </div>
        
        <div class="quick-info">
            <div class="info-card">
                <h4>Server</h4>
                <p>66.94.117.35</p>
            </div>
            <div class="info-card">
                <h4>Database</h4>
                <p>fwbebochecker</p>
            </div>
            <div class="info-card">
                <h4>PHP</h4>
                <p><?php echo phpversion(); ?></p>
            </div>
            <div class="info-card">
                <h4>Updated</h4>
                <p><?php echo file_exists($docFile) ? date('M j, Y', filemtime($docFile)) : 'N/A'; ?></p>
            </div>
        </div>
        
        <div class="tabs">
            <button class="tab active" onclick="showTab('full', this)">📚 Full Documentation</button>
            <button class="tab" onclick="showTab('context', this)">📋 Quick Context</button>
            <button class="tab" onclick="showTab('security', this)">🔒 Security Report</button>
        </div>
        
        <div id="full" class="content-box active">
            <?php echo parseMarkdown($docContent); ?>
        </div>
        
        <div id="context" class="content-box">
            <pre class="code-block" style="font-size: 12px; line-height: 1.5; white-space: pre-wrap;"><?php echo htmlspecialchars($aiContent); ?></pre>
        </div>
        
        <div id="security" class="content-box">
            <?php echo parseMarkdown($secContent); ?>
        </div>
    </div>
    
    <div class="action-btns">
        <button class="action-btn copy-context-btn" onclick="copyContext()">📋 Copy Context</button>
        <button class="action-btn copy-btn" onclick="copyFull()">📄 Copy Full</button>
    </div>
    
    <script>
        const fullDoc = <?php echo json_encode($docContent); ?>;
        const contextDoc = <?php echo json_encode($aiContent); ?>;
        
        function showTab(tab, btn) {
            document.querySelectorAll('.content-box').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
            document.getElementById(tab).classList.add('active');
            btn.classList.add('active');
        }
        
        function copyFull() {
            navigator.clipboard.writeText(fullDoc).then(() => {
                alert('✅ Full documentation copied!');
            });
        }
        
        function copyContext() {
            navigator.clipboard.writeText(contextDoc).then(() => {
                alert('✅ Context copied!');
            });
        }
    </script>
</body>
</html>
