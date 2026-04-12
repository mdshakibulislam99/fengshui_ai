# Quick Translation Template

Use this template to quickly add translations to new pages.

## Step 1: Add Keys to translations.js

```javascript
const TRANSLATIONS = {
  en: {
    // ... existing keys ...
    
    // Page Name Here
    'page.title': 'Page Title',
    'page.description': 'Page description text',
    'page.button.label': 'Button Text',
    'page.form.input.placeholder': 'Enter something',
  },
  
  zh: {
    // ... existing keys ...
    
    // 页面名称这里
    'page.title': '页面标题',
    'page.description': '页面描述文本',
    'page.button.label': '按钮文本',
    'page.form.input.placeholder': '输入某些内容',
  }
};
```

## Step 2: Add to HTML Head

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your Page Title</title>
    
    <!-- CSS files -->
    <link rel="stylesheet" href="header.css">
    <link rel="stylesheet" href="your-page-styles.css">
    
    <!-- Translation system - MUST load first -->
    <script src="translations.js" defer></script>
    <script src="language-manager.js" defer></script>
    <script src="header.js" defer></script>
    
    <!-- Your other scripts -->
    <script src="your-page-script.js" defer></script>
</head>
<body>
    <!-- Header auto-loads here -->
    
    <main>
        <!-- Your content with data-i18n attributes -->
    </main>
</body>
</html>
```

## Step 3: Add data-i18n to Elements

```html
<!-- Headings -->
<h1 data-i18n="page.title">Page Title</h1>
<p data-i18n="page.description">Page description text</p>

<!-- Buttons -->
<button data-i18n="page.button.label">Button Text</button>

<!-- Forms -->
<input type="text" placeholder="Enter something" data-i18n="page.form.input.placeholder">

<!-- Links -->
<a href="other-page.html" data-i18n="page.link">Link Text</a>
```

## Dynamic Content Example

If creating elements in JavaScript:

```javascript
// Get translated text
const buttonText = QiLang.get('page.button.label');
const description = QiLang.get('page.description');

// Create element
const button = document.createElement('button');
button.textContent = buttonText;

// Listen for language changes
window.addEventListener('qilang:changed', function() {
    button.textContent = QiLang.get('page.button.label');
    // Update other elements as needed
});

document.body.appendChild(button);
```

## Common Patterns

### Navigation Items (Already Translated)
```html
<nav>
    <a href="index.html" data-i18n="nav.home">Home</a>
    <a href="outdoor-analysis.html" data-i18n="nav.outdoor">Outdoor Analysis</a>
    <!-- etc -->
</nav>
```

### Feature Cards
```html
<article class="feature-card">
    <h3 data-i18n="feature.name.title">Title</h3>
    <p data-i18n="feature.name.desc">Description</p>
    <button data-i18n="feature.name.btn">Button Text</button>
</article>
```

### Form Inputs
```html
<label data-i18n="form.email.label">Email Address</label>
<input type="email" placeholder="Enter email" data-i18n="form.email.placeholder">

<label data-i18n="form.message.label">Message</label>
<textarea placeholder="Type message" data-i18n="form.message.placeholder"></textarea>
```

## Naming Convention Examples

```
nav.*                   - Navigation items
hero.*                  - Hero/intro seaction
feature.*               - Feature cards
form.*                  - Form fields
button.*                - Buttons and CTAs
error.*                 - Error messages
success.*               - Success messages
modal.*                 - Modal dialogs
sidebar.*               - Sidebar content
footer.*                - Footer content
```

## Testing Checklist

- [ ] Add all text keys to translations.js
- [ ] Add data-i18n to all HTML elements
- [ ] Add script tags to page head (in correct order)
- [ ] Test page in English
- [ ] Click language toggle
- [ ] Test page in Chinese
- [ ] Verify all text translated
- [ ] Refresh page - language preference persists
- [ ] Navigate to another page - language preference maintained
- [ ] Back to this page - still in selected language

## Troubleshooting

**Translation not showing?**
```
1. Check data-i18n attribute spelling
2. Confirm key exists in translations.js for both en and zh
3. Open browser Console (F12) - any errors?
4. Hard refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
```

**Scripts not loading?**
```
1. Verify script paths are correct
2. Check browser Console for 404 errors
3. Verify scripts load in this order:
   - translations.js
   - language-manager.js
   - header.js
   - your other scripts
```

**Can't toggle language?**
```
1. Verify .hdr-lang-toggle element exists
2. Check Console for JavaScript errors
3. Verify QiLang object is defined: console.log(QiLang)
```

## Translation Quality Tips

When translating to Chinese:
- Keep translations natural and idiomatic
- Chinese text often takes more horizontal space - test layout
- Use Simplified Chinese (Simplified rather than Traditional)
- Test both horizontal and vertical text layouts

Common translations:
```
English                    Chinese
Analysis                   分析
Learn                      学习
Personal                   个人
Outdoor                    户外
Indoor                     室内
Submit/Send               提交
Cancel                    取消
Close                     关闭
Settings                  设置
Help                      帮助
About                     关于
Contact                   联系
Save                      保存
Delete                    删除
```
