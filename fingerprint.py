"""
Browser Fingerprint Module
Generates and applies consistent browser fingerprints to avoid bot detection.

Session starts → Fingerprint chosen → Same fingerprint used everywhere → Session ends
"""

import random
import hashlib
import json
from datetime import datetime


class BrowserFingerprint:
    """
    Generates a consistent browser fingerprint for a session.
    All fingerprint values stay the same throughout the session.
    """
    
    # Real-world screen resolutions (common ones)
    SCREEN_RESOLUTIONS = [
        (1920, 1080), (1366, 768), (1536, 864), (1440, 900),
        (1280, 720), (1600, 900), (2560, 1440), (1280, 800),
        (1680, 1050), (1360, 768), (1920, 1200), (2560, 1080),
    ]
    
    # Real user agents (Windows Chrome - updated versions)
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]
    
    # Common languages
    LANGUAGES = [
        ["en-US", "en"],
        ["en-GB", "en"],
        ["en-IN", "en"],
    ]
    
    # Timezones (offset in minutes)
    TIMEZONES = [
        {"name": "Asia/Kolkata", "offset": -330},  # India
        {"name": "America/New_York", "offset": 300},  # US East
        {"name": "America/Los_Angeles", "offset": 480},  # US West
        {"name": "Europe/London", "offset": 0},  # UK
    ]
    
    # WebGL vendors and renderers (real GPU combinations)
    WEBGL_CONFIGS = [
        {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 Direct3D11 vs_5_0 ps_5_0, D3D11)"},
        {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)"},
        {"vendor": "Google Inc. (Intel)", "renderer": "ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)"},
        {"vendor": "Google Inc. (AMD)", "renderer": "ANGLE (AMD, AMD Radeon RX 580 Series Direct3D11 vs_5_0 ps_5_0, D3D11)"},
        {"vendor": "Google Inc. (Intel)", "renderer": "ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)"},
        {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 2070 Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    ]
    
    # Hardware concurrency (CPU cores)
    HARDWARE_CONCURRENCY = [4, 6, 8, 12, 16]
    
    # Device memory (GB)
    DEVICE_MEMORY = [4, 8, 16, 32]
    
    # Platform
    PLATFORMS = ["Win32"]
    
    def __init__(self, seed=None):
        """
        Initialize fingerprint with optional seed for reproducibility.
        
        Args:
            seed: Random seed for consistent fingerprint generation
        """
        # Generate seed if not provided
        if seed is None:
            seed = int(datetime.now().timestamp() * 1000)
        
        self.seed = seed
        self._rng = random.Random(seed)
        
        # Generate all fingerprint components once
        self._generate_fingerprint()
        
        print(f"Fingerprint generated with seed: {seed}")
    
    def _generate_fingerprint(self):
        """Generate all fingerprint components."""
        
        # Screen
        self.screen_resolution = self._rng.choice(self.SCREEN_RESOLUTIONS)
        self.screen_width = self.screen_resolution[0]
        self.screen_height = self.screen_resolution[1]
        self.color_depth = self._rng.choice([24, 32])
        self.pixel_ratio = self._rng.choice([1, 1.25, 1.5, 2])
        
        # Window (slightly smaller than screen)
        self.window_width = self.screen_width - self._rng.randint(0, 100)
        self.window_height = self.screen_height - self._rng.randint(60, 150)
        
        # User agent
        self.user_agent = self._rng.choice(self.USER_AGENTS)
        
        # Language
        self.languages = self._rng.choice(self.LANGUAGES)
        
        # Timezone
        self.timezone = self._rng.choice(self.TIMEZONES)
        
        # WebGL
        self.webgl = self._rng.choice(self.WEBGL_CONFIGS)
        
        # Hardware
        self.hardware_concurrency = self._rng.choice(self.HARDWARE_CONCURRENCY)
        self.device_memory = self._rng.choice(self.DEVICE_MEMORY)
        self.platform = self._rng.choice(self.PLATFORMS)
        
        # Canvas noise (unique per session but consistent)
        self.canvas_noise = self._rng.uniform(-0.0001, 0.0001)
        
        # Audio noise
        self.audio_noise = self._rng.uniform(-0.0001, 0.0001)
        
        # Generate unique but consistent IDs
        self._generate_ids()
    
    def _generate_ids(self):
        """Generate unique identifiers for this fingerprint."""
        base = f"{self.seed}-{self.user_agent}-{self.screen_width}"
        
        # Canvas hash (consistent for session)
        self.canvas_hash = hashlib.md5(f"canvas-{base}".encode()).hexdigest()[:16]
        
        # WebGL hash
        self.webgl_hash = hashlib.md5(f"webgl-{base}".encode()).hexdigest()[:16]
        
        # Audio hash
        self.audio_hash = hashlib.md5(f"audio-{base}".encode()).hexdigest()[:16]
    
    def get_chrome_options_args(self):
        """Get Chrome arguments for this fingerprint."""
        return [
            f"--window-size={self.window_width},{self.window_height}",
            f"user-agent={self.user_agent}",
            f"--lang={self.languages[0]}",
        ]
    
    def get_injection_script(self):
        """
        Get JavaScript to inject into page to spoof fingerprint.
        This script overrides browser APIs to return consistent values.
        """
        return f"""
        (function() {{
            'use strict';
            
            // ================================================================
            // STORE ORIGINAL FUNCTIONS
            // ================================================================
            const originalGetContext = HTMLCanvasElement.prototype.getContext;
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            const originalToBlob = HTMLCanvasElement.prototype.toBlob;
            const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
            
            // ================================================================
            // NAVIGATOR PROPERTIES
            // ================================================================
            
            // Webdriver - hide automation
            Object.defineProperty(navigator, 'webdriver', {{
                get: () => undefined
            }});
            
            // Platform
            Object.defineProperty(navigator, 'platform', {{
                get: () => '{self.platform}'
            }});
            
            // Hardware concurrency (CPU cores)
            Object.defineProperty(navigator, 'hardwareConcurrency', {{
                get: () => {self.hardware_concurrency}
            }});
            
            // Device memory
            Object.defineProperty(navigator, 'deviceMemory', {{
                get: () => {self.device_memory}
            }});
            
            // Languages
            Object.defineProperty(navigator, 'languages', {{
                get: () => {json.dumps(self.languages)}
            }});
            
            Object.defineProperty(navigator, 'language', {{
                get: () => '{self.languages[0]}'
            }});
            
            // ================================================================
            // SCREEN PROPERTIES
            // ================================================================
            
            Object.defineProperty(screen, 'width', {{
                get: () => {self.screen_width}
            }});
            
            Object.defineProperty(screen, 'height', {{
                get: () => {self.screen_height}
            }});
            
            Object.defineProperty(screen, 'availWidth', {{
                get: () => {self.screen_width}
            }});
            
            Object.defineProperty(screen, 'availHeight', {{
                get: () => {self.screen_height - 40}
            }});
            
            Object.defineProperty(screen, 'colorDepth', {{
                get: () => {self.color_depth}
            }});
            
            Object.defineProperty(screen, 'pixelDepth', {{
                get: () => {self.color_depth}
            }});
            
            Object.defineProperty(window, 'devicePixelRatio', {{
                get: () => {self.pixel_ratio}
            }});
            
            // ================================================================
            // TIMEZONE
            // ================================================================
            
            const originalDateTimeFormat = Intl.DateTimeFormat;
            Intl.DateTimeFormat = function(locales, options) {{
                options = options || {{}};
                options.timeZone = options.timeZone || '{self.timezone["name"]}';
                return new originalDateTimeFormat(locales, options);
            }};
            Intl.DateTimeFormat.prototype = originalDateTimeFormat.prototype;
            
            // Override getTimezoneOffset
            Date.prototype.getTimezoneOffset = function() {{
                return {self.timezone["offset"]};
            }};
            
            // ================================================================
            // CANVAS FINGERPRINT PROTECTION
            // ================================================================
            
            const canvasNoise = {self.canvas_noise};
            
            // Add subtle noise to canvas data
            function addCanvasNoise(canvas) {{
                const ctx = canvas.getContext('2d');
                if (!ctx) return;
                
                try {{
                    const imageData = originalGetImageData.call(ctx, 0, 0, canvas.width, canvas.height);
                    const data = imageData.data;
                    
                    // Add consistent noise based on session seed
                    for (let i = 0; i < data.length; i += 4) {{
                        // Modify only a few pixels slightly
                        if ((i / 4) % 100 === 0) {{
                            data[i] = Math.max(0, Math.min(255, data[i] + (canvasNoise * 255)));
                        }}
                    }}
                    
                    ctx.putImageData(imageData, 0, 0);
                }} catch(e) {{}}
            }}
            
            HTMLCanvasElement.prototype.toDataURL = function(...args) {{
                addCanvasNoise(this);
                return originalToDataURL.apply(this, args);
            }};
            
            HTMLCanvasElement.prototype.toBlob = function(...args) {{
                addCanvasNoise(this);
                return originalToBlob.apply(this, args);
            }};
            
            // ================================================================
            // WEBGL FINGERPRINT PROTECTION
            // ================================================================
            
            const webglVendor = '{self.webgl["vendor"]}';
            const webglRenderer = '{self.webgl["renderer"]}';
            
            const getParameterProxy = new Proxy(WebGLRenderingContext.prototype.getParameter, {{
                apply: function(target, thisArg, args) {{
                    const param = args[0];
                    
                    // UNMASKED_VENDOR_WEBGL
                    if (param === 37445) {{
                        return webglVendor;
                    }}
                    // UNMASKED_RENDERER_WEBGL
                    if (param === 37446) {{
                        return webglRenderer;
                    }}
                    
                    return Reflect.apply(target, thisArg, args);
                }}
            }});
            
            WebGLRenderingContext.prototype.getParameter = getParameterProxy;
            
            // WebGL2
            if (typeof WebGL2RenderingContext !== 'undefined') {{
                WebGL2RenderingContext.prototype.getParameter = getParameterProxy;
            }}
            
            // ================================================================
            // AUDIO FINGERPRINT PROTECTION
            // ================================================================
            
            const audioNoise = {self.audio_noise};
            
            if (typeof AudioContext !== 'undefined') {{
                const originalCreateAnalyser = AudioContext.prototype.createAnalyser;
                AudioContext.prototype.createAnalyser = function() {{
                    const analyser = originalCreateAnalyser.apply(this, arguments);
                    const originalGetFloatFrequencyData = analyser.getFloatFrequencyData.bind(analyser);
                    
                    analyser.getFloatFrequencyData = function(array) {{
                        originalGetFloatFrequencyData(array);
                        for (let i = 0; i < array.length; i++) {{
                            array[i] += audioNoise;
                        }}
                    }};
                    
                    return analyser;
                }};
            }}
            
            // ================================================================
            // PLUGINS & MIME TYPES
            // ================================================================
            
            // Fake realistic plugins
            Object.defineProperty(navigator, 'plugins', {{
                get: () => {{
                    const plugins = [
                        {{ name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' }},
                        {{ name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' }},
                        {{ name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }}
                    ];
                    plugins.length = 3;
                    return plugins;
                }}
            }});
            
            // ================================================================
            // PERMISSIONS API
            // ================================================================
            
            const originalQuery = navigator.permissions.query;
            navigator.permissions.query = (parameters) => {{
                if (parameters.name === 'notifications') {{
                    return Promise.resolve({{ state: Notification.permission }});
                }}
                return originalQuery(parameters);
            }};
            
            // ================================================================
            // CHROME SPECIFIC
            // ================================================================
            
            // Add chrome object if missing
            window.chrome = window.chrome || {{}};
            window.chrome.runtime = window.chrome.runtime || {{}};
            
            // ================================================================
            // AUTOMATION DETECTION BYPASS
            // ================================================================
            
            // Remove automation indicators
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
            
            // Override toString to hide modifications
            const nativeToString = Function.prototype.toString;
            Function.prototype.toString = function() {{
                if (this === navigator.permissions.query) {{
                    return 'function query() {{ [native code] }}';
                }}
                return nativeToString.call(this);
            }};
            
            console.log('Fingerprint protection active');
        }})();
        """
    
    def apply_to_driver(self, driver):
        """
        Apply fingerprint to an existing WebDriver instance.
        Call this after driver creation but before navigation.
        
        Args:
            driver: Selenium WebDriver instance
        """
        # Inject fingerprint script to run on every page load
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": self.get_injection_script()
        })
        
        print("Fingerprint applied to driver")
    
    def get_summary(self):
        """Get a summary of the fingerprint configuration."""
        return {
            "seed": self.seed,
            "screen": f"{self.screen_width}x{self.screen_height}",
            "user_agent": self.user_agent[:50] + "...",
            "language": self.languages[0],
            "timezone": self.timezone["name"],
            "webgl_vendor": self.webgl["vendor"],
            "hardware_concurrency": self.hardware_concurrency,
            "device_memory": f"{self.device_memory}GB",
            "canvas_hash": self.canvas_hash,
        }
    
    def print_summary(self):
        """Print fingerprint summary."""
        print("\n" + "=" * 60)
        print("BROWSER FINGERPRINT CONFIGURATION")
        print("=" * 60)
        summary = self.get_summary()
        for key, value in summary.items():
            print(f"  {key}: {value}")
        print("=" * 60 + "\n")


# ============================================================================
# FINGERPRINT MANAGER - Manages fingerprints across sessions
# ============================================================================

class FingerprintManager:
    """
    Manages browser fingerprints for consistent anti-detection.
    """
    
    def __init__(self):
        self.current_fingerprint = None
    
    def new_session(self, seed=None):
        """
        Start a new session with a fresh fingerprint.
        
        Args:
            seed: Optional seed for reproducible fingerprint
            
        Returns:
            BrowserFingerprint instance
        """
        self.current_fingerprint = BrowserFingerprint(seed)
        return self.current_fingerprint
    
    def get_fingerprint(self):
        """Get current fingerprint, creating one if needed."""
        if self.current_fingerprint is None:
            self.new_session()
        return self.current_fingerprint
    
    def end_session(self):
        """End current session, clearing fingerprint."""
        self.current_fingerprint = None
        print("Session ended - fingerprint cleared")


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Create a fingerprint
    fp = BrowserFingerprint()
    fp.print_summary()
    
    # Show injection script (first 500 chars)
    script = fp.get_injection_script()
    print("Injection script preview:")
    print(script[:500] + "...")
