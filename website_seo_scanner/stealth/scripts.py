FINGERPRINT_SPOOFING_SCRIPT = """
() => {
    // Удаление webdriver property
    delete navigator.__proto__.webdriver;
    // Переопределение plugins
    Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5],
        configurable: true
    });
    // Переопределение languages
    Object.defineProperty(navigator, 'languages', {
        get: () => ['%s', '%s'],
        configurable: true
    });
    // Переопределение platform
    Object.defineProperty(navigator, 'platform', {
        get: () => '%s',
        configurable: true
    });
    // Переопределение hardwareConcurrency
    Object.defineProperty(navigator, 'hardwareConcurrency', {
        get: () => %d,
        configurable: true
    });
    // Скрытие automation properties
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
        configurable: true
    });
    // Переопределение permissions
    const originalQuery = navigator.permissions.query;
    navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
        Promise.resolve({ state: Notification.permission }) :
        originalQuery(parameters)
    );
    // Маскировка под обычный браузер
    window.chrome = {
        runtime: {},
        loadTimes: function() { return {}; },
        csi: function() { return {}; },
        app: { isInstalled: false }
    };
}
"""

WEBGL_SPOOFING_SCRIPT = """
() => {
    const getParameter = WebGLRenderingContext.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {
        if (parameter === 37445) {
            return 'Intel Inc.';
        }
        if (parameter === 37446) {
            return 'Intel Iris OpenGL Engine';
        }
            return getParameter(parameter);
    };
}
"""

CANVAS_SPOOFING_SCRIPT = """
() => {
    // Canvas fingerprint spoofing
    const toDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function(type) {
        const context = this.getContext('2d');
        if (context) {
            context.fillText('Modified Canvas Fingerprint', 10, 10);
        }
        return toDataURL.call(this, type);
    };
}
"""
