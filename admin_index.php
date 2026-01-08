<?php
/**
 * FWChecker Admin Panel - With PIN System
 */

require_once '../config.php';

if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

// Database connection for PIN
function getDbConnection() {
    static $pdo = null;
    if ($pdo === null) {
        $pdo = new PDO('mysql:host=localhost;dbname=website;charset=utf8mb4', 'root', 'MySQLroot@La4242la');
        $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    }
    return $pdo;
}

// Admin credentials
$adminPasswords = [
    'fwbebo' => 'FWthebest24$$',
    'moro' => 'morothebest24$$',
    'harlen' => 'HARLENTHEBEST24$$'
];

$error = '';
$success = '';
$step = 'login'; // login, pin_setup, pin_verify

// Handle logout
if (isset($_GET['logout'])) {
    session_destroy();
    header('Location: index.php');
    exit;
}

// Determine current step
if (isset($_SESSION['admin_authenticated']) && $_SESSION['admin_authenticated'] === true) {
    if (!isset($_SESSION['pin_verified']) || $_SESSION['pin_verified'] !== true) {
        // Check if user has PIN set
        $pdo = getDbConnection();
        $stmt = $pdo->prepare('SELECT pin_hash FROM admin_pins WHERE admin_user = ?');
        $stmt->execute([$_SESSION['admin_user']]);
        $pinData = $stmt->fetch(PDO::FETCH_ASSOC);
        
        $step = $pinData ? 'pin_verify' : 'pin_setup';
    } else {
        $step = 'dashboard';
    }
}

// Handle password login
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['password']) && isset($_POST['username'])) {
    $username = strtolower(trim($_POST['username']));
    $password = $_POST['password'];
    
    if (isset($adminPasswords[$username]) && $adminPasswords[$username] === $password) {
        $_SESSION['admin_authenticated'] = true;
        $_SESSION['admin_user'] = $username;
        $_SESSION['admin_login_time'] = time();
        
        // Check if PIN exists
        $pdo = getDbConnection();
        $stmt = $pdo->prepare('SELECT pin_hash FROM admin_pins WHERE admin_user = ?');
        $stmt->execute([$username]);
        $pinData = $stmt->fetch(PDO::FETCH_ASSOC);
        
        $step = $pinData ? 'pin_verify' : 'pin_setup';
    } else {
        $error = 'Invalid username or password!';
    }
}

// Handle PIN setup
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['new_pin']) && isset($_POST['confirm_pin'])) {
    if (!isset($_SESSION['admin_authenticated']) || $_SESSION['admin_authenticated'] !== true) {
        header('Location: index.php');
        exit;
    }
    
    $newPin = $_POST['new_pin'];
    $confirmPin = $_POST['confirm_pin'];
    
    if (strlen($newPin) < 4 || strlen($newPin) > 6) {
        $error = 'PIN must be 4-6 digits!';
        $step = 'pin_setup';
    } elseif (!ctype_digit($newPin)) {
        $error = 'PIN must contain only numbers!';
        $step = 'pin_setup';
    } elseif ($newPin !== $confirmPin) {
        $error = 'PINs do not match!';
        $step = 'pin_setup';
    } else {
        $pdo = getDbConnection();
        $pinHash = password_hash($newPin, PASSWORD_DEFAULT);
        $stmt = $pdo->prepare('INSERT INTO admin_pins (admin_user, pin_hash) VALUES (?, ?) ON DUPLICATE KEY UPDATE pin_hash = ?');
        $stmt->execute([$_SESSION['admin_user'], $pinHash, $pinHash]);
        
        $_SESSION['pin_verified'] = true;
        $success = 'PIN set successfully!';
        $step = 'dashboard';
    }
}

// Handle PIN verification
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['pin']) && !isset($_POST['new_pin'])) {
    if (!isset($_SESSION['admin_authenticated']) || $_SESSION['admin_authenticated'] !== true) {
        header('Location: index.php');
        exit;
    }
    
    $pin = $_POST['pin'];
    
    $pdo = getDbConnection();
    $stmt = $pdo->prepare('SELECT pin_hash FROM admin_pins WHERE admin_user = ?');
    $stmt->execute([$_SESSION['admin_user']]);
    $pinData = $stmt->fetch(PDO::FETCH_ASSOC);
    
    if ($pinData && password_verify($pin, $pinData['pin_hash'])) {
        $_SESSION['pin_verified'] = true;
        $step = 'dashboard';
    } else {
        $error = 'Invalid PIN!';
        $step = 'pin_verify';
    }
}

// Show login form
if ($step === 'login') {
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Login - FWChecker</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-box {
            background: rgba(30, 30, 60, 0.9);
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
            width: 100%;
            max-width: 400px;
            border: 1px solid rgba(139,92,246,0.3);
        }
        .login-box h1 {
            color: #fff;
            text-align: center;
            margin-bottom: 30px;
            font-size: 1.8em;
        }
        .form-group { margin-bottom: 20px; }
        .form-group label {
            display: block;
            color: #a78bfa;
            margin-bottom: 8px;
            font-size: 14px;
        }
        .form-group input {
            width: 100%;
            padding: 15px;
            border: 2px solid rgba(139,92,246,0.3);
            border-radius: 10px;
            background: rgba(15,15,35,0.8);
            color: #fff;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        .form-group input:focus {
            outline: none;
            border-color: #8b5cf6;
        }
        .btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #8b5cf6, #7c3aed);
            border: none;
            border-radius: 10px;
            color: #fff;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(139,92,246,0.4);
        }
        .error {
            background: rgba(239,68,68,0.2);
            border: 1px solid #ef4444;
            color: #fca5a5;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
        }
        .icon { font-size: 3em; text-align: center; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="login-box">
        <div class="icon">🔐</div>
        <h1>Admin Login</h1>
        <?php if ($error): ?>
            <div class="error"><?php echo htmlspecialchars($error); ?></div>
        <?php endif; ?>
        <form method="POST">
            <div class="form-group">
                <label>Username</label>
                <input type="text" name="username" placeholder="Enter username" required autofocus>
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="password" placeholder="Enter password" required>
            </div>
            <button type="submit" class="btn">🚀 Login</button>
        </form>
    </div>
</body>
</html>
<?php
    exit;
}

// Show PIN setup form
if ($step === 'pin_setup') {
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Setup PIN - FWChecker Admin</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .pin-box {
            background: rgba(30, 30, 60, 0.9);
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
            width: 100%;
            max-width: 400px;
            border: 1px solid rgba(139,92,246,0.3);
        }
        .pin-box h1 {
            color: #fff;
            text-align: center;
            margin-bottom: 10px;
            font-size: 1.8em;
        }
        .pin-box p {
            color: #a78bfa;
            text-align: center;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .form-group { margin-bottom: 20px; }
        .form-group label {
            display: block;
            color: #a78bfa;
            margin-bottom: 8px;
            font-size: 14px;
        }
        .form-group input {
            width: 100%;
            padding: 15px;
            border: 2px solid rgba(139,92,246,0.3);
            border-radius: 10px;
            background: rgba(15,15,35,0.8);
            color: #fff;
            font-size: 24px;
            text-align: center;
            letter-spacing: 10px;
            transition: border-color 0.3s;
        }
        .form-group input:focus {
            outline: none;
            border-color: #8b5cf6;
        }
        .btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #4ade80, #22c55e);
            border: none;
            border-radius: 10px;
            color: #000;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .btn:hover { transform: translateY(-2px); }
        .error {
            background: rgba(239,68,68,0.2);
            border: 1px solid #ef4444;
            color: #fca5a5;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
        }
        .icon { font-size: 3em; text-align: center; margin-bottom: 20px; }
        .user-badge {
            text-align: center;
            margin-bottom: 20px;
        }
        .user-badge span {
            background: linear-gradient(135deg, #8b5cf6, #7c3aed);
            color: #fff;
            padding: 8px 20px;
            border-radius: 20px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="pin-box">
        <div class="icon">🔑</div>
        <h1>Setup Your PIN</h1>
        <p>Create a 4-6 digit PIN for secure access</p>
        <div class="user-badge">
            <span>👤 <?php echo htmlspecialchars($_SESSION['admin_user']); ?></span>
        </div>
        <?php if ($error): ?>
            <div class="error"><?php echo htmlspecialchars($error); ?></div>
        <?php endif; ?>
        <form method="POST">
            <div class="form-group">
                <label>New PIN (4-6 digits)</label>
                <input type="password" name="new_pin" maxlength="6" pattern="[0-9]{4,6}" placeholder="••••" required autofocus>
            </div>
            <div class="form-group">
                <label>Confirm PIN</label>
                <input type="password" name="confirm_pin" maxlength="6" pattern="[0-9]{4,6}" placeholder="••••" required>
            </div>
            <button type="submit" class="btn">✅ Set PIN</button>
        </form>
    </div>
</body>
</html>
<?php
    exit;
}

// Show PIN verify form
if ($step === 'pin_verify') {
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enter PIN - FWChecker Admin</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .pin-box {
            background: rgba(30, 30, 60, 0.9);
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
            width: 100%;
            max-width: 400px;
            border: 1px solid rgba(139,92,246,0.3);
        }
        .pin-box h1 {
            color: #fff;
            text-align: center;
            margin-bottom: 30px;
            font-size: 1.8em;
        }
        .form-group { margin-bottom: 20px; }
        .form-group input {
            width: 100%;
            padding: 20px;
            border: 2px solid rgba(139,92,246,0.3);
            border-radius: 10px;
            background: rgba(15,15,35,0.8);
            color: #fff;
            font-size: 32px;
            text-align: center;
            letter-spacing: 15px;
            transition: border-color 0.3s;
        }
        .form-group input:focus {
            outline: none;
            border-color: #8b5cf6;
        }
        .btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #8b5cf6, #7c3aed);
            border: none;
            border-radius: 10px;
            color: #fff;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .btn:hover { transform: translateY(-2px); }
        .error {
            background: rgba(239,68,68,0.2);
            border: 1px solid #ef4444;
            color: #fca5a5;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
        }
        .icon { font-size: 3em; text-align: center; margin-bottom: 20px; }
        .user-badge {
            text-align: center;
            margin-bottom: 30px;
        }
        .user-badge span {
            background: linear-gradient(135deg, #8b5cf6, #7c3aed);
            color: #fff;
            padding: 8px 20px;
            border-radius: 20px;
            font-size: 14px;
        }
        .logout-link {
            display: block;
            text-align: center;
            margin-top: 20px;
            color: #a78bfa;
            text-decoration: none;
            font-size: 14px;
        }
        .logout-link:hover { color: #fff; }
    </style>
</head>
<body>
    <div class="pin-box">
        <div class="icon">🔐</div>
        <h1>Enter PIN</h1>
        <div class="user-badge">
            <span>👤 <?php echo htmlspecialchars($_SESSION['admin_user']); ?></span>
        </div>
        <?php if ($error): ?>
            <div class="error"><?php echo htmlspecialchars($error); ?></div>
        <?php endif; ?>
        <form method="POST">
            <div class="form-group">
                <input type="password" name="pin" maxlength="6" pattern="[0-9]{4,6}" placeholder="••••" required autofocus>
            </div>
            <button type="submit" class="btn">🔓 Unlock</button>
        </form>
        <a href="?logout=1" class="logout-link">← Use different account</a>
    </div>
</body>
</html>
<?php
    exit;
}

// Dashboard - user is fully authenticated
$currentUser = $_SESSION['admin_user'];
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Panel - FWChecker</title>
    <link rel="stylesheet" href="../style.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 100%);
            min-height: 100vh;
            color: #fff;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        
        .header {
            background: linear-gradient(135deg, #1e1e3f 0%, #2d2d5a 100%);
            padding: 20px 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }
        .header h1 { font-size: 1.8em; display: flex; align-items: center; gap: 10px; }
        .header-right { display: flex; gap: 15px; align-items: center; }
        .admin-badge {
            background: linear-gradient(135deg, #8b5cf6, #7c3aed);
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 13px;
        }
        .logout-btn {
            background: linear-gradient(135deg, #ef4444, #dc2626);
            color: #fff;
            padding: 10px 20px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 500;
        }
        .back-link {
            color: #4ade80;
            text-decoration: none;
            font-size: 14px;
        }
        
        .nav-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
        }
        .nav-card {
            background: linear-gradient(135deg, rgba(30,30,60,0.9), rgba(45,45,90,0.9));
            padding: 25px;
            border-radius: 15px;
            text-decoration: none;
            color: #fff;
            transition: transform 0.3s, box-shadow 0.3s;
            border: 1px solid rgba(139,92,246,0.2);
        }
        .nav-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(139,92,246,0.3);
            border-color: rgba(139,92,246,0.5);
        }
        .nav-icon { font-size: 2.5em; margin-bottom: 15px; }
        .nav-title { font-size: 1.2em; font-weight: bold; margin-bottom: 8px; }
        .nav-description { color: #a78bfa; font-size: 13px; }
        
        .success-msg {
            background: rgba(34,197,94,0.2);
            border: 1px solid #22c55e;
            color: #86efac;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚡ FWChecker Admin</h1>
            <div class="header-right">
                <a href="../dashboard.php" class="back-link">← Back to Dashboard</a>
                <span class="admin-badge">👤 <?php echo htmlspecialchars($currentUser); ?></span>
                <a href="?logout=1" class="logout-btn">🚪 Logout</a>
            </div>
        </div>
        
        <?php if ($success): ?>
            <div class="success-msg">✅ <?php echo htmlspecialchars($success); ?></div>
        <?php endif; ?>
        
        <div class="nav-grid">
            <a href="users.php" class="nav-card">
                <div class="nav-icon">👥</div>
                <div class="nav-title">User Management</div>
                <div class="nav-description">View and manage all users</div>
            </a>
            
            <a href="bulk_notification.php" class="nav-card">
                <div class="nav-icon">📢</div>
                <div class="nav-title">Bulk Notifications</div>
                <div class="nav-description">Send messages to multiple users</div>
            </a>
            
            <a href="gates.php" class="nav-card">
                <div class="nav-icon">🚪</div>
                <div class="nav-title">Gate Management</div>
                <div class="nav-description">Configure validation gates</div>
            </a>
            
            <a href="../FWpanel.php" class="nav-card">
                <div class="nav-icon">🎛️</div>
                <div class="nav-title">FW Panel</div>
                <div class="nav-description">Advanced panel controls</div>
            </a>
            
            <a href="themes.php" class="nav-card">
                <div class="nav-icon">🎨</div>
                <div class="nav-title">Themes</div>
                <div class="nav-description">Customize appearance</div>
            </a>
            
            <a href="bin_management.php" class="nav-card">
                <div class="nav-icon">💳</div>
                <div class="nav-title">BIN Management</div>
                <div class="nav-description">Manage BIN database</div>
            </a>
            
            <a href="Memory/" class="nav-card" style="border: 2px solid #8b5cf6;">
                <div class="nav-icon">🧠</div>
                <div class="nav-title">System Memory</div>
                <div class="nav-description">Documentation & system info</div>
            </a>
        </div>
    </div>
</body>
</html>
