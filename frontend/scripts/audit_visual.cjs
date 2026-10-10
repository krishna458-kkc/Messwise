const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

const EDGE_PATH = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const SCREENSHOT_DIR = path.resolve(__dirname, '../../docs/screenshots');

function parseRgb(colorStr) {
  const match = colorStr.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/);
  if (!match) return null;
  return {
    r: parseInt(match[1], 10),
    g: parseInt(match[2], 10),
    b: parseInt(match[3], 10),
    a: match[4] !== undefined ? parseFloat(match[4]) : 1,
  };
}

function getLuminance({ r, g, b }) {
  const [rs, gs, bs] = [r, g, b].map(c => {
    c = c / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}

function getContrastRatio(rgb1, rgb2) {
  const l1 = getLuminance(rgb1);
  const l2 = getLuminance(rgb2);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

async function runAudit() {
  console.log('Starting automated visual & contrast audit...');
  const browser = await puppeteer.launch({
    executablePath: EDGE_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu'],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  const auditReport = [];

  async function checkPageContrast(pageName, theme) {
    console.log(`Auditing: ${pageName} (${theme})...`);
    
    // Set theme via html class
    await page.evaluate((th) => {
      if (th === 'dark') {
        document.documentElement.classList.add('dark');
        localStorage.setItem('messwise_theme', 'dark');
      } else {
        document.documentElement.classList.remove('dark');
        localStorage.setItem('messwise_theme', 'light');
      }
    }, theme);

    await new Promise((r) => setTimeout(r, 600));

    // Screenshot
    const filename = `${pageName}_${theme}.png`;
    const filepath = path.join(SCREENSHOT_DIR, filename);
    await page.screenshot({ path: filepath, fullPage: false });

    // Evaluate contrast of visible text elements
    const elementsData = await page.evaluate(() => {
      function getEffectiveBg(el) {
        let cur = el;
        while (cur && cur !== document.documentElement) {
          const style = window.getComputedStyle(cur);
          const bg = style.backgroundColor;
          if (bg && bg !== 'transparent' && !bg.startsWith('rgba(0, 0, 0, 0)')) {
            return bg;
          }
          cur = cur.parentElement;
        }
        return window.getComputedStyle(document.body).backgroundColor || 'rgb(247, 246, 238)';
      }

      const results = [];
      const nodes = document.querySelectorAll('h1, h2, h3, h4, p, span, button, a, label, th, td');
      for (const node of nodes) {
        const text = (node.innerText || '').trim();
        if (!text || text.length < 2 || node.children.length > 3) continue;

        const rect = node.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0 || rect.top > window.innerHeight) continue;

        const style = window.getComputedStyle(node);
        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') continue;

        const color = style.color;
        const bg = getEffectiveBg(node);
        const fontSize = parseFloat(style.fontSize);
        const fontWeight = parseInt(style.fontWeight, 10) || 400;

        results.push({
          tag: node.tagName.toLowerCase(),
          text: text.slice(0, 50),
          color,
          bg,
          fontSize,
          fontWeight,
        });
      }
      return results;
    });

    const issues = [];
    for (const item of elementsData) {
      const fgRgb = parseRgb(item.color);
      const bgRgb = parseRgb(item.bg);
      if (!fgRgb || !bgRgb) continue;

      const ratio = getContrastRatio(fgRgb, bgRgb);
      const isLarge = item.fontSize >= 18 || (item.fontSize >= 14 && item.fontWeight >= 700);
      const minRatio = isLarge ? 3.0 : 4.5;

      if (ratio < minRatio) {
        issues.push({
          text: item.text,
          tag: item.tag,
          color: item.color,
          bg: item.bg,
          ratio: ratio.toFixed(2),
          required: minRatio,
        });
      }
    }

    auditReport.push({
      page: pageName,
      theme,
      elementsChecked: elementsData.length,
      issuesCount: issues.length,
      issues: issues.slice(0, 10),
      screenshot: filename,
    });
  }

  // 1. Landing Page
  await page.goto('http://localhost:3000/', { waitUntil: 'networkidle0' });
  await checkPageContrast('landing', 'light');
  await checkPageContrast('landing', 'dark');

  // 2. Mobile Viewport Landing Page
  await page.setViewport({ width: 390, height: 844 });
  await checkPageContrast('landing_mobile', 'light');
  await page.setViewport({ width: 1440, height: 900 });

  // 3. Enter App
  await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Launch') || b.innerText.includes('Operational'));
    if (btn) btn.click();
  });
  await new Promise(r => setTimeout(r, 1000));

  // Tabs to test
  const tabs = [
    { id: 'dashboard', name: 'command_center' },
    { id: 'forecast', name: 'forecast_lab' },
    { id: 'kitchen', name: 'kitchen_logging' },
    { id: 'planner', name: 'planner' },
    { id: 'intelligence', name: 'waste_intelligence' },
    { id: 'impact', name: 'sustainability' },
    { id: 'surplus', name: 'surplus_routing' },
    { id: 'simulator', name: 'simulator' },
    { id: 'reports', name: 'reports' },
  ];

  for (const tab of tabs) {
    // Click nav item
    await page.evaluate((tabId) => {
      const btn = document.querySelector(`button[data-tab="${tabId}"]`) || Array.from(document.querySelectorAll('button')).find(b => (b.getAttribute('data-tab') === tabId) || (b.innerText && b.innerText.toLowerCase().includes(tabId)));
      if (btn) btn.click();
    }, tab.id);

    await new Promise(r => setTimeout(r, 800));
    await checkPageContrast(tab.name, 'light');
    await checkPageContrast(tab.name, 'dark');
  }

  // Tablet Viewport Command Center
  await page.setViewport({ width: 768, height: 1024 });
  await checkPageContrast('command_center_tablet', 'light');

  await browser.close();

  const reportPath = path.resolve(__dirname, '../../docs/screenshots/audit_results.json');
  fs.writeFileSync(reportPath, JSON.stringify(auditReport, null, 2));
  console.log('Visual audit complete! Results saved to docs/screenshots/audit_results.json');
  console.log(JSON.stringify(auditReport.map(r => ({ page: r.page, theme: r.theme, checked: r.elementsChecked, issues: r.issuesCount })), null, 2));
}

runAudit().catch(err => {
  console.error('Audit script failed:', err);
  process.exit(1);
});
