/**
 * Universal Header — QiMatrix
 * Drop in <script src="header.js" defer></script> on any page.
 * Automatically highlights the active nav link.
 */
(function () {
    if (window.__qimatrixHeaderInitialized) {
        return;
    }
    window.__qimatrixHeaderInitialized = true;

    var pathName = window.location.pathname || '';
    var page = pathName.split('/').pop() || 'index.html';
    var inPagesDir = pathName.indexOf('/pages/') !== -1;
    var basePrefix = inPagesDir ? '../' : '';

    function href(path) {
        return basePrefix + path;
    }

    function active(href) {
        var target = href.split('/').pop().split('#')[0];
        return page === target ? ' hdr-active' : '';
    }

    // Indoor sub-pages all highlight "Indoor Analysis"
    var indoorPages = ['indoor-analysis.html', 'indoor-design.html', 'indoor-upload.html'];
    function indoorActive() {
        return indoorPages.indexOf(page) !== -1 ? ' hdr-active' : '';
    }

    var html = '<header class="top-frame">'
        + '<div class="frame-shell nav-row">'

        + '<a class="brand" href="' + href('index.html') + '" aria-label="QiMatrix Home">'
        + '<span class="brand-glyph" aria-hidden="true"></span>'
        + '<span class="brand-text">QiMatrix</span>'
        + '</a>'

        + '<nav class="hdr-nav" aria-label="Primary">'
        + '<a href="' + href('index.html') + '" class="' + active('index.html').trim() + '" data-i18n="nav.home">Home</a>'
        + '<a href="' + href('outdoor-analysis.html') + '" class="' + active('outdoor-analysis.html').trim() + '" data-i18n="nav.outdoor">Outdoor Analysis</a>'
        + '<a href="' + href('indoor-analysis.html') + '" class="' + indoorActive().trim() + '" data-i18n="nav.indoor">Indoor Analysis</a>'
        + '<a href="' + href('personal-feng-shui.html') + '" class="' + active('personal-feng-shui.html').trim() + '" data-i18n="nav.personal">Personal</a>'
        + '<a href="' + href('weather.html') + '" class="' + active('weather.html').trim() + '" data-i18n="nav.weather">Weather</a>'
        + '<a href="' + href('learn-feng-shui.html') + '" class="' + active('learn-feng-shui.html').trim() + '" data-i18n="nav.learn">Learn</a>'
        + '</nav>'

        + '<div class="nav-ctas">'
        + '<button class="hdr-lang-toggle" aria-label="Toggle language" title="切换语言 / Switch Language"></button>'
        + '<a href="' + href('outdoor-analysis.html') + '" class="hdr-btn hdr-btn-solid" data-i18n="nav.startAnalysis">Start Analysis</a>'
        + '</div>'

        + '<button class="hdr-toggle" aria-label="Toggle menu" aria-expanded="false">'
        + '<span></span><span></span><span></span>'
        + '</button>'

        + '</div>'

        + '<nav class="hdr-mobile-nav" aria-label="Mobile navigation">'
        + '<a href="' + href('index.html') + '" data-i18n="nav.home">Home</a>'
        + '<a href="' + href('outdoor-analysis.html') + '" data-i18n="nav.outdoor">Outdoor Analysis</a>'
        + '<a href="' + href('indoor-analysis.html') + '" data-i18n="nav.indoor">Indoor Analysis</a>'
        + '<a href="' + href('personal-feng-shui.html') + '" data-i18n="nav.personal">Personal</a>'
        + '<a href="' + href('weather.html') + '" data-i18n="nav.weather">Weather</a>'
        + '<a href="' + href('learn-feng-shui.html') + '" data-i18n="nav.learn">Learn</a>'
        + '<button class="hdr-lang-toggle-mobile" aria-label="Toggle language" title="切换语言 / Switch Language"></button>'
        + '<div class="hdr-mobile-ctas">'
        + '<a href="' + href('outdoor-analysis.html') + '" class="hdr-btn hdr-btn-solid" data-i18n="nav.startAnalysis">Start Analysis</a>'
        + '</div>'
        + '</nav>'

        + '</header>';

    function applyLangToHeader() {
        console.log('[QiMatrix Header] applyLangToHeader called, QiLang available:', typeof QiLang !== 'undefined');
        if (typeof QiLang === 'undefined') return;
        // Translate all data-i18n elements inside the header
        document.querySelectorAll('.top-frame [data-i18n], .hdr-mobile-nav [data-i18n]').forEach(function(el) {
            var key = el.getAttribute('data-i18n');
            var translated = QiLang.get(key);
            if (translated && translated !== key) {
                el.textContent = translated;
            }
        });
        // Update language toggle button to show the OPPOSITE language
        var btnText = QiLang.currentLang === 'en' ? '中文' : 'EN';
        var langToggle = document.querySelector('.hdr-lang-toggle');
        var langToggleMobile = document.querySelector('.hdr-lang-toggle-mobile');
        if (langToggle) langToggle.textContent = btnText;
        if (langToggleMobile) langToggleMobile.textContent = btnText;
    }

    function init() {
        console.log('[QiMatrix Header] Initializing...');
        // Prevent duplicate headers when script is loaded twice or when
        // a page still contains a legacy header implementation.
        if (document.querySelector('.top-frame') || document.querySelector('.main-header')) {
            // Header already exists — still apply lang and wire up toggle
            console.log('[QiMatrix Header] Header already exists, skipping injection');
            applyLangToHeader();
            wireToggle();
            return;
        }

        console.log('[QiMatrix Header] Injecting header HTML...');
        document.body.insertAdjacentHTML('afterbegin', html);
        console.log('[QiMatrix Header] Header injected, header element:', document.querySelector('.top-frame'));

        // Apply saved language to the freshly-injected header immediately
        applyLangToHeader();
        console.log('[QiMatrix Header] Language applied, QiLang status:', typeof QiLang);

        var toggle = document.querySelector('.hdr-toggle');
        var mobileNav = document.querySelector('.hdr-mobile-nav');
        if (!toggle || !mobileNav) return;

        toggle.addEventListener('click', function () {
            var isOpen = this.classList.contains('open');
            this.classList.toggle('open');
            this.setAttribute('aria-expanded', String(!isOpen));
            mobileNav.classList.toggle('open');
        });

        mobileNav.querySelectorAll('a').forEach(function (link) {
            link.addEventListener('click', function () {
                toggle.classList.remove('open');
                toggle.setAttribute('aria-expanded', 'false');
                mobileNav.classList.remove('open');
            });
        });

        wireToggle();
    }

    function wireToggle() {
        var langToggle = document.querySelector('.hdr-lang-toggle');
        var langToggleMobile = document.querySelector('.hdr-lang-toggle-mobile');

        if (langToggle && !langToggle.__qiLangBound) {
            langToggle.__qiLangBound = true;
            langToggle.addEventListener('click', function(e) {
                e.preventDefault();
                if (typeof QiLang !== 'undefined') QiLang.toggle();
            });
        }

        if (langToggleMobile && !langToggleMobile.__qiLangBound) {
            langToggleMobile.__qiLangBound = true;
            langToggleMobile.addEventListener('click', function(e) {
                e.preventDefault();
                if (typeof QiLang !== 'undefined') QiLang.toggle();
            });
        }

        // Re-translate header whenever language changes
        window.addEventListener('qilang:changed', function() {
            applyLangToHeader();
        });
    }

    if (document.readyState === 'loading') {
        console.log('[QiMatrix Header] DOM still loading, will initialize on DOMContentLoaded');
        document.addEventListener('DOMContentLoaded', init);
    } else {
        console.log('[QiMatrix Header] DOM ready, initializing immediately');
        init();
    }
})();
