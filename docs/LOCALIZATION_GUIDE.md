# QiMatrix Language Localization Guide

## Overview
This guide explains how the multi-language system works and how to add translations to other pages.

---

## System Architecture

### Files Involved
1. **translations.js** - Contains all text content in English (en) and Chinese (zh)
2. **language-manager.js** - Handles language switching and localStorage persistence
3. **header.js** - Updated to include language toggle button
4. **header.css** - Styling for language toggle button

### How It Works

1. **Language Detection**: On page load, the system checks `localStorage` for saved preference (`qimatrix-lang`)
2. **Default Language**: Defaults to English if no preference is saved
3. **DOM Update**: All elements with `data-i18n` attribute are updated with translated text
4. **Persistence**: User's choice is saved to `localStorage` and persists across page refreshes and navigation
5. **Real-time Updates**: Language can be switched at any time with immediate UI update

---

## How to Use

### For End Users

**Language Toggle Button**
- Look in the header for a language button (shows "中文" in English mode, "English" in Chinese mode)
- Click to toggle between English and Chinese
- Language preference is automatically remembered across all visits and pages

---

## For Developers: Adding Translations

### Step 1: Add Translation Keys to translations.js

Open `/docs/translations.js` and add your translation keys:

```javascript
const TRANSLATIONS = {
  en: {
    'your.new.key': 'Your English text here',
    // ... other keys
  },
  zh: {
    'your.new.key': '您的中文文本在这里',
    // ... other keys
  }
};
```

### Step 2: Add data-i18n Attributes to HTML

In your HTML file, add the `data-i18n` attribute to elements:

```html
<h1 data-i18n="your.new.key">Your English text here</h1>
<button data-i18n="another.key">English Button Text</button>
<a href="page.html" data-i18n="link.key">Link Text</a>
```

### Step 3: Load Translation Scripts

Add these scripts to your HTML `<head>` BEFORE other scripts:

```html
<script src="translations.js" defer></script>
<script src="language-manager.js" defer></script>
<script src="header.js" defer></script>
<!-- Your other scripts -->
```

### Step 4: Ensure Language Manager Initializes

The language manager automatically initializes when the page loads. All elements with `data-i18n` attributes will be updated.

---

## Advanced: Listening for Language Changes

If your code needs to react to language changes, listen for the custom event:

```javascript
window.addEventListener('qilang:changed', function(e) {
    const newLang = e.detail.lang; // 'en' or 'zh'
    console.log('Language changed to:', newLang);
    
    // Your custom code here
    // Re-render components, update content, etc.
});
```

---

## Dynamic Content in JavaScript

If you're generating content dynamically via JavaScript, use `QiLang.get()`:

```javascript
const buttonText = QiLang.get('feature.outdoor.btn');
const element = document.createElement('button');
element.textContent = buttonText;

// Listen for language changes if displaying this element
window.addEventListener('qilang:changed', function() {
    element.textContent = QiLang.get('feature.outdoor.btn');
});
```

---

## Available Global Objects

### QiLang Object

```javascript
QiLang.currentLang          // Current language ('en' or 'zh')
QiLang.get(key)             // Get translated text for a key
QiLang.switchLang(lang)     // Switch to specific language
QiLang.toggle()             // Toggle between en and zh
QiLang.updatePageContent()  // Manually update all page content
```

---

## Translation Guidelines

### Key Naming Conventions
- Use lowercase with dot notation: `feature.outdoor.title`
- Group related keys: `nav.*`, `hero.*`, `feature.*`
- Be specific: `nav.home` not `navigation.homepage`

### Quality Tips
- Keep translations concise and consistent
- Match tone and style between English and Chinese versions
- Test both languages for UI layout issues (Chinese often takes more space)
- Use context comments in translations.js when needed

### Current Translation Keys

**Navigation**
- `nav.home` - Home
- `nav.outdoor` - Outdoor Analysis
- `nav.indoor` - Indoor Analysis
- `nav.personal` - Personal
- `nav.weather` - Weather
- `nav.learn` - Learn
- `nav.startAnalysis` - Start Analysis Button

**Language**
- `lang.toggle` - Language toggle button text
- `lang.label` - Language label

**Homepage Hero Section**
- `hero.title` - Main heading
- `hero.subtitle` - Subheading text

**Feature Cards**
- `feature.outdoor.title` - Card title
- `feature.outdoor.desc` - Card description
- `feature.outdoor.btn` - Card button text
- (Same pattern for `indoor`, `personal`, `weather`, `learn`)

---

## Troubleshooting

### Translations Not Showing
1. Verify `data-i18n` attribute matches exactly with key in translations.js
2. Check browser console for errors
3. Ensure `translations.js` loads before page content
4. Force page refresh (Cmd+Shift+R on Mac)

### Language Not Persisting
1. Check if localStorage is enabled in browser
2. Verify JavaScript console shows no errors
3. Check if browser is in private/incognito mode (localStorage may not persist)

### Missing Translations
1. Add the key to both `en` and `zh` objects in translations.js
2. Test language toggle to confirm both show up

---

## Example: Adding Translations to outdoor-analysis.html

1. Update **translations.js**:
```javascript
en: {
  'outdoor.title': 'Outdoor Analysis',
  'outdoor.description': 'Analyze your location...',
}
zh: {
  'outdoor.title': '户外分析',
  'outdoor.description': '分析您的位置...',
}
```

2. Update **outdoor-analysis.html**:
```html
<h1 data-i18n="outdoor.title">Outdoor Analysis</h1>
<p data-i18n="outdoor.description">Analyze your location...</p>
```

3. Add script tags to head:
```html
<script src="translations.js" defer></script>
<script src="language-manager.js" defer></script>
<script src="header.js" defer></script>
```

Done! The page now supports both English and Chinese with automatic language switching.

---

## Browser Compatibility

- Works in all modern browsers (Chrome, Firefox, Safari, Edge)
- Uses localStorage for persistence
- Gracefully degrades if JavaScript is disabled (shows English)

---

## Performance Notes

- All translations loaded upfront (good for small to medium sites)
- Language switching is instant (no server calls)
- localStorage is instant (no network latency)
- No performance impact on page load

---

## Future Enhancements

Potential improvements:
- Add more languages (Spanish, French, German, etc.)
- URL parameter for language switching (?lang=zh)
- Server-side language detection based on browser locale
- CDN support for translation files
- Translation management interface
