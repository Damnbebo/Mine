#!/usr/bin/env python3
"""Add enhanced stealth/anti-detection measures"""

with open("/home/ubuntu/amazon-bot/main2.py", "r") as f:
    content = f.read()

# ============================================
# PART 1: Add more Chrome args for stealth
# ============================================

old_chrome_args_end = '''    "--no-pings"
]'''

new_chrome_args_end = '''    "--no-pings",
    
    # ADVANCED STEALTH ARGS 2025
    "--disable-site-isolation-trials",
    "--disable-features=IsolateOrigins,site-per-process,SitePerProcess",
    "--disable-features=BlockInsecurePrivateNetworkRequests",
    "--disable-features=AutofillServerCommunication",
    "--disable-webrtc-hw-encoding",
    "--disable-webrtc-hw-decoding",
    "--force-webrtc-ip-handling-policy=disable_non_proxied_udp",
    "--disable-webgl2-compute-context",
    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "--lang=en-US,en",
    "--disable-remote-fonts",
    "--enable-features=NetworkService,NetworkServiceInProcess"
]'''

if old_chrome_args_end in content:
    content = content.replace(old_chrome_args_end, new_chrome_args_end)
    print("✅ Added additional Chrome stealth args")
else:
    print("ℹ️ Chrome args end marker not found, may already be enhanced")

# ============================================
# PART 2: Enhanced STEALTH_SCRIPT
# ============================================

old_section = """    console.log('%c[STEALTH] All protections active - Unique device fingerprint generated', 'color: #00ff00;');
})();
'''"""

enhanced_section = """    console.log('%c[STEALTH] All protections active - Unique device fingerprint generated', 'color: #00ff00;');
    
    // ========================================
    // ADVANCED STEALTH 2025 - ADDITIONAL PROTECTIONS
    // ========================================
    
    // 1. WebGL Fingerprint Randomization
    (function() {
        const getParameterProxyHandler = {
            apply: function(target, thisArg, args) {
                const param = args[0];
                const result = Reflect.apply(target, thisArg, args);
                if (param === 37445) return 'Google Inc. (NVIDIA)';
                if (param === 37446) {
                    const renderers = [
                        'ANGLE (NVIDIA, NVIDIA GeForce GTX 1080 Direct3D11 vs_5_0 ps_5_0)',
                        'ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 Direct3D11 vs_5_0 ps_5_0)',
                        'ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0)',
                        'ANGLE (AMD, AMD Radeon RX 580 Series Direct3D11 vs_5_0 ps_5_0)'
                    ];
                    return renderers[Math.floor(Math.random() * renderers.length)];
                }
                return result;
            }
        };
        try {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            if (gl) {
                const origGetParam = gl.getParameter.bind(gl);
                gl.getParameter = new Proxy(origGetParam, getParameterProxyHandler);
            }
        } catch(e) {}
    })();
    
    // 2. Canvas Fingerprint Noise
    (function() {
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function(type) {
            if (type === 'image/png' || type === undefined) {
                try {
                    const context = this.getContext('2d');
                    if (context && this.width > 0 && this.height > 0) {
                        const imageData = context.getImageData(0, 0, Math.min(this.width, 16), Math.min(this.height, 16));
                        for (let i = 0; i < imageData.data.length; i += 4) {
                            if (Math.random() < 0.01) imageData.data[i] = imageData.data[i] ^ 1;
                        }
                        context.putImageData(imageData, 0, 0);
                    }
                } catch(e) {}
            }
            return originalToDataURL.apply(this, arguments);
        };
    })();
    
    // 3. AudioContext Fingerprint Protection
    (function() {
        if (window.AudioContext || window.webkitAudioContext) {
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            const origCreateOscillator = AudioCtx.prototype.createOscillator;
            AudioCtx.prototype.createOscillator = function() {
                const osc = origCreateOscillator.apply(this, arguments);
                osc.frequency.value += (Math.random() * 0.0001 - 0.00005);
                return osc;
            };
        }
    })();
    
    // 4. Screen Properties Randomization
    (function() {
        const screens = [
            {w: 1920, h: 1080}, {w: 1366, h: 768}, {w: 1536, h: 864},
            {w: 1440, h: 900}, {w: 2560, h: 1440}
        ];
        const s = screens[Math.floor(Math.random() * screens.length)];
        Object.defineProperty(window.screen, 'width', { get: () => s.w });
        Object.defineProperty(window.screen, 'height', { get: () => s.h });
        Object.defineProperty(window.screen, 'availWidth', { get: () => s.w });
        Object.defineProperty(window.screen, 'availHeight', { get: () => s.h - 40 });
        Object.defineProperty(window, 'outerWidth', { get: () => s.w });
        Object.defineProperty(window, 'outerHeight', { get: () => s.h });
        Object.defineProperty(window, 'innerWidth', { get: () => s.w - 20 });
        Object.defineProperty(window, 'innerHeight', { get: () => s.h - 140 });
    })();
    
    // 5. Timezone Spoofing (US timezones)
    (function() {
        const tzs = ['America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles'];
        const tz = tzs[Math.floor(Math.random() * tzs.length)];
        const origDTF = Intl.DateTimeFormat;
        Intl.DateTimeFormat = function(locales, options) {
            options = options || {};
            options.timeZone = options.timeZone || tz;
            return new origDTF(locales, options);
        };
        Intl.DateTimeFormat.prototype = origDTF.prototype;
    })();
    
    // 6. Client Rects Noise (element fingerprinting)
    (function() {
        const origGetBCR = Element.prototype.getBoundingClientRect;
        Element.prototype.getBoundingClientRect = function() {
            const r = origGetBCR.apply(this, arguments);
            const n = 0.00001;
            return {
                x: r.x + Math.random() * n, y: r.y + Math.random() * n,
                width: r.width + Math.random() * n, height: r.height + Math.random() * n,
                top: r.top + Math.random() * n, right: r.right + Math.random() * n,
                bottom: r.bottom + Math.random() * n, left: r.left + Math.random() * n
            };
        };
    })();
    
    // 7. WebRTC IP Leak Protection
    (function() {
        if (window.RTCPeerConnection) {
            const origRTC = window.RTCPeerConnection;
            window.RTCPeerConnection = function(config) {
                if (config && config.iceServers) {
                    config.iceServers = [];
                }
                return new origRTC(config);
            };
            window.RTCPeerConnection.prototype = origRTC.prototype;
        }
    })();
    
    // 8. Font Fingerprint Protection
    (function() {
        const commonFonts = ['Arial', 'Verdana', 'Times New Roman', 'Georgia', 'Courier New', 'Tahoma'];
        if (document.fonts && document.fonts.check) {
            const origCheck = document.fonts.check.bind(document.fonts);
            document.fonts.check = function(font) {
                const fontName = font.split(' ').pop().replace(/['"]/g, '');
                if (commonFonts.some(f => fontName.toLowerCase().includes(f.toLowerCase()))) return true;
                return origCheck(font);
            };
        }
    })();
    
    // 9. Performance.now() Noise (timing attacks)
    (function() {
        const origPerfNow = performance.now.bind(performance);
        performance.now = function() {
            return origPerfNow() + Math.random() * 0.0001;
        };
    })();
    
    // 10. Date.now() Noise
    (function() {
        const origDateNow = Date.now;
        Date.now = function() {
            return origDateNow() + Math.floor(Math.random() * 2);
        };
    })();
    
    // 11. Chrome Runtime spoofing
    (function() {
        window.chrome = {
            runtime: {
                connect: () => {},
                sendMessage: () => {},
                onMessage: { addListener: () => {} },
                getManifest: () => ({})
            },
            app: { isInstalled: false },
            csi: () => {},
            loadTimes: () => ({})
        };
    })();
    
    // 12. Permission Query Spoofing
    (function() {
        if (navigator.permissions && navigator.permissions.query) {
            const origQuery = navigator.permissions.query.bind(navigator.permissions);
            navigator.permissions.query = async function(permissionDesc) {
                try {
                    const result = await origQuery(permissionDesc);
                    return result;
                } catch(e) {
                    return { state: 'prompt', onchange: null };
                }
            };
        }
    })();
    
    console.log('%c[STEALTH+] Enhanced protections loaded - WebGL, Canvas, Audio, WebRTC, Fonts, Timing protected', 'color: #00ff00; font-weight: bold;');
})();
'''"""

if old_section in content:
    content = content.replace(old_section, enhanced_section)
    print("✅ Added enhanced stealth JS protections successfully!")
else:
    print("❌ Could not find the exact stealth end marker in JS")
    # Debug: show what's around that area
    idx = content.find("console.log('%c[STEALTH] All protections active")
    if idx > 0:
        print(f"Found at position {idx}")
        print(f"Context: {repr(content[idx:idx+200])}")

with open("/home/ubuntu/amazon-bot/main2.py", "w") as f:
    f.write(content)

print("\n✅ Enhanced stealth configuration complete!")
