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
        + '<a href="' + href('index.html') + '" class="' + active('index.html').trim() + '">Home</a>'
        + '<a href="' + href('outdoor-analysis.html') + '" class="' + active('outdoor-analysis.html').trim() + '">Outdoor Analysis</a>'
        + '<a href="' + href('indoor-analysis.html') + '" class="' + indoorActive().trim() + '">Indoor Analysis</a>'
        + '<a href="' + href('personal-feng-shui.html') + '" class="' + active('personal-feng-shui.html').trim() + '">Personal</a>'
        + '<a href="' + href('weather.html') + '" class="' + active('weather.html').trim() + '">Weather</a>'
        + '<a href="' + href('learn-feng-shui.html') + '" class="' + active('learn-feng-shui.html').trim() + '">Learn</a>'
        + '</nav>'

        + '<div class="nav-ctas">'
        + '<a href="' + href('login.html') + '" class="hdr-btn hdr-btn-ghost">Login</a>'
        + '<a href="' + href('outdoor-analysis.html') + '" class="hdr-btn hdr-btn-solid">Start Analysis</a>'
        + '</div>'

        + '<button class="hdr-toggle" aria-label="Toggle menu" aria-expanded="false">'
        + '<span></span><span></span><span></span>'
        + '</button>'

        + '</div>'

        + '<nav class="hdr-mobile-nav" aria-label="Mobile navigation">'
        + '<a href="' + href('index.html') + '">Home</a>'
        + '<a href="' + href('outdoor-analysis.html') + '">Outdoor Analysis</a>'
        + '<a href="' + href('indoor-analysis.html') + '">Indoor Analysis</a>'
        + '<a href="' + href('personal-feng-shui.html') + '">Personal</a>'
        + '<a href="' + href('weather.html') + '">Weather</a>'
        + '<a href="' + href('learn-feng-shui.html') + '">Learn</a>'
        + '<div class="hdr-mobile-ctas">'
        + '<a href="' + href('login.html') + '" class="hdr-btn hdr-btn-ghost">Login</a>'
        + '<a href="' + href('outdoor-analysis.html') + '" class="hdr-btn hdr-btn-solid">Start Analysis</a>'
        + '</div>'
        + '</nav>'

        + '</header>';

    function init() {
        // Prevent duplicate headers when script is loaded twice or when
        // a page still contains a legacy header implementation.
        if (document.querySelector('.top-frame') || document.querySelector('.main-header')) {
            return;
        }

        document.body.insertAdjacentHTML('afterbegin', html);

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
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
