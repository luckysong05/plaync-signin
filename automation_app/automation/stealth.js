// Anti-detection stealth patches for Playwright Chromium
// Override browser fingerprinting vectors used by CAPTCHA/anti-bot systems

// --- navigator.webdriver ---
// Headless: true. Real: undefined.
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined,
    configurable: true,
});

// --- navigator.plugins ---
// Headless: empty array. Real: 3-5 entries (PDF, Native Client, etc.)
Object.defineProperty(navigator, 'plugins', {
    get: () => {
        const arr = [
            { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
            { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
            { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' },
        ];
        arr.item = i => arr[i];
        arr.namedItem = name => arr.find(p => p.name === name) || null;
        arr.refresh = () => {};
        return arr;
    },
    configurable: true,
});

// --- navigator.mimeTypes ---
// Headless: empty array. Real: has application/pdf etc.
Object.defineProperty(navigator, 'mimeTypes', {
    get: () => {
        const arr = [
            { type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format' },
        ];
        arr.item = i => arr[i];
        arr.namedItem = type => arr.find(m => m.type === type) || null;
        arr.refresh = () => {};
        return arr;
    },
    configurable: true,
});

// --- navigator.languages ---
// Match Korean locale — PlayNC is a Korean gaming site
Object.defineProperty(navigator, 'languages', {
    get: () => ['ko-KR', 'ko', 'en-US', 'en'],
    configurable: true,
});

// --- navigator.hardwareConcurrency ---
// Headless: often reports 1. Real desktop: 4-16.
Object.defineProperty(navigator, 'hardwareConcurrency', {
    get: () => 8,
    configurable: true,
});

// --- navigator.deviceMemory ---
// Headless: undefined. Real Chrome: reports system RAM in GB.
Object.defineProperty(navigator, 'deviceMemory', {
    get: () => 8,
    configurable: true,
});

// --- screen properties ---
// Headless: often 800x600 or weird dimensions. Real: common 1920x1080.
Object.defineProperty(screen, 'width', { get: () => 1920, configurable: true });
Object.defineProperty(screen, 'height', { get: () => 1080, configurable: true });
Object.defineProperty(screen, 'availWidth', { get: () => 1920, configurable: true });
Object.defineProperty(screen, 'availHeight', { get: () => 1040, configurable: true });
Object.defineProperty(screen, 'colorDepth', { get: () => 24, configurable: true });
Object.defineProperty(screen, 'pixelDepth', { get: () => 24, configurable: true });

// --- window.chrome ---
// Headless: missing or incomplete. Real: has runtime, loadTimes, etc.
if (!window.chrome) {
    window.chrome = { runtime: {} };
}
window.chrome.runtime = window.chrome.runtime || {};

// --- WebGL vendor/renderer ---
// Headless: "Google Inc." / "Google SwiftShader". Real: Intel/NVIDIA/AMD.
try {
    const _getParam1 = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function (p) {
        if (p === 37445) return 'Intel Inc.';       // UNMASKED_VENDOR_WEBGL
        if (p === 37446) return 'Intel(R) Iris(R) Xe Graphics'; // UNMASKED_RENDERER_WEBGL
        return _getParam1.call(this, p);
    };
} catch (e) { /* WebGL1 not available */ }

try {
    const _getParam2 = WebGL2RenderingContext.prototype.getParameter;
    WebGL2RenderingContext.prototype.getParameter = function (p) {
        if (p === 37445) return 'Intel Inc.';
        if (p === 37446) return 'Intel(R) Iris(R) Xe Graphics';
        return _getParam2.call(this, p);
    };
} catch (e) { /* WebGL2 not available */ }

// --- Canvas fingerprint noise ---
// Headless Chrome renders canvas identically every time — easy fingerprint.
// Flip LSB of ~1% of pixels so hash differs from headless baseline.
(function () {
    const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
    CanvasRenderingContext2D.prototype.getImageData = function (x, y, w, h) {
        const imageData = originalGetImageData.call(this, x, y, w, h);
        const data = imageData.data;
        const pxCount = w * h;
        // Modify ~1% of pixels — flip green channel LSB
        const step = Math.max(4, Math.floor(pxCount / 100) * 4);
        for (let i = 1; i < data.length; i += step) {
            if (i % 4 === 1) { // green channel only
                data[i] = data[i] ^ 1; // flip LSB
            }
        }
        return imageData;
    };
})();

// --- WebGL readPixels noise ---
// Same idea: add subtle noise to WebGL canvas readback.
(function () {
    const originalReadPixels =
        WebGLRenderingContext.prototype.readPixels;
    WebGLRenderingContext.prototype.readPixels = function (
        x, y, width, height, format, type, pixels
    ) {
        const result = originalReadPixels.call(
            this, x, y, width, height, format, type, pixels
        );
        if (pixels && pixels.length) {
            const step = Math.max(1, Math.floor(pixels.length / 200));
            for (let i = 0; i < pixels.length; i += step) {
                pixels[i] = pixels[i] ^ 1;
            }
        }
        return result;
    };
})();

(function () {
    const originalReadPixels2 =
        WebGL2RenderingContext.prototype.readPixels;
    WebGL2RenderingContext.prototype.readPixels = function (
        x, y, width, height, format, type, pixels
    ) {
        const result = originalReadPixels2.call(
            this, x, y, width, height, format, type, pixels
        );
        if (pixels && pixels.length) {
            const step = Math.max(1, Math.floor(pixels.length / 200));
            for (let i = 0; i < pixels.length; i += step) {
                pixels[i] = pixels[i] ^ 1;
            }
        }
        return result;
    };
})();
