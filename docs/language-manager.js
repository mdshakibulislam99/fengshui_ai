/**
 * QiMatrix Language Manager
 * Handles language switching and localStorage persistence.
 * Relies on translations.js being loaded first (script order guarantee from defer).
 */

(function () {
  if (window.__qimatrixLangManagerInitialized) return;
  window.__qimatrixLangManagerInitialized = true;

  window.QiLang = {
    // Default Chinese. User choice is saved to localStorage and always wins.
    currentLang: localStorage.getItem('qimatrix-lang') || 'zh',

    get: function (key) {
      var lang = TRANSLATIONS[this.currentLang];
      return (lang && lang[key]) ? lang[key] : (TRANSLATIONS['en'][key] || key);
    },

    switchLang: function (lang) {
      if (lang !== 'en' && lang !== 'zh') return;
      this.currentLang = lang;
      localStorage.setItem('qimatrix-lang', lang);
      this.applyToPage();
    },

    toggle: function () {
      this.switchLang(this.currentLang === 'en' ? 'zh' : 'en');
    },

    applyToPage: function () {
      // Update HTML lang attribute
      document.documentElement.lang = this.currentLang;
      // Translate every element with a data-i18n attribute
      var self = this;
      document.querySelectorAll('[data-i18n]').forEach(function (el) {
        var key = el.getAttribute('data-i18n');
        var text = self.get(key);
        if (el.tagName === 'INPUT' && el.type !== 'button') {
          el.placeholder = text;
        } else {
          el.textContent = text;
        }
      });
      // Notify listeners (e.g. header.js button text update)
      window.dispatchEvent(new CustomEvent('qilang:changed', { detail: { lang: this.currentLang } }));
    },

    // Legacy alias used by older call sites
    updatePageContent: function () { this.applyToPage(); }
  };

  // Run immediately — defer scripts execute after DOM is parsed
  document.documentElement.lang = QiLang.currentLang;
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { QiLang.applyToPage(); });
  } else {
    QiLang.applyToPage();
  }
})();
