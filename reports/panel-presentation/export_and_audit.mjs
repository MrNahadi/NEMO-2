import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(HERE, "../..");
const AUDIT_DIR = path.join(HERE, "audit");
const SHOTS_DIR = path.join(AUDIT_DIR, "screenshots");
fs.mkdirSync(SHOTS_DIR, { recursive: true });

const CHROME_CANDIDATES = [
  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
];
const CHROME_PATH = CHROME_CANDIDATES.find((p) => fs.existsSync(p));
if (!CHROME_PATH) {
  throw new Error("Neither Chrome nor Edge found on host.");
}

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".woff2": "font/woff2",
};

function startStaticServer() {
  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      const cleanUrl = (req.url || "/").split("?")[0];
      const rel = decodeURIComponent(cleanUrl).replace(/^\/+/, "");
      const filePath = path.resolve(REPO_ROOT, rel);
      if (!filePath.startsWith(REPO_ROOT) || !fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
        res.writeHead(404);
        res.end("Not found");
        return;
      }
      const ext = path.extname(filePath).toLowerCase();
      res.writeHead(200, { "Content-Type": MIME[ext] || "application/octet-stream" });
      fs.createReadStream(filePath).pipe(res);
    });
    server.listen(0, "127.0.0.1", () => {
      resolve({ server, port: server.address().port });
    });
  });
}

function launchChrome() {
  return new Promise((resolve, reject) => {
    const userDataDir = path.join(AUDIT_DIR, "chrome-profile");
    fs.mkdirSync(userDataDir, { recursive: true });
    const proc = spawn(
      CHROME_PATH,
      [
        "--headless=new",
        "--remote-debugging-port=0",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-extensions",
        "--disable-background-networking",
        `--user-data-dir=${userDataDir}`,
        "about:blank",
      ],
      { stdio: ["ignore", "pipe", "pipe"] }
    );
    let stderr = "";
    const timer = setTimeout(() => reject(new Error("Chrome startup timeout: " + stderr)), 15000);
    proc.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
      const m = stderr.match(/DevTools listening on (ws:\/\/[^\s]+)/);
      if (m) {
        clearTimeout(timer);
        resolve({ proc, browserWsUrl: m[1] });
      }
    });
    proc.on("exit", (code) => {
      clearTimeout(timer);
      reject(new Error(`Chrome exited early (${code}): ${stderr}`));
    });
  });
}

class CDPClient {
  constructor(ws) {
    this.ws = ws;
    this.seq = 0;
    this.pending = new Map();
    this.listeners = new Map();
    ws.addEventListener("message", (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.id && this.pending.has(msg.id)) {
        const { resolve, reject } = this.pending.get(msg.id);
        this.pending.delete(msg.id);
        if (msg.error) reject(new Error(JSON.stringify(msg.error)));
        else resolve(msg.result);
      } else if (msg.method && this.listeners.has(msg.method)) {
        for (const fn of this.listeners.get(msg.method)) fn(msg.params);
      }
    });
  }
  send(method, params = {}) {
    const id = ++this.seq;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }
  once(method) {
    return new Promise((resolve) => {
      const arr = this.listeners.get(method) || [];
      const wrap = (p) => {
        this.listeners.set(method, (this.listeners.get(method) || []).filter((f) => f !== wrap));
        resolve(p);
      };
      arr.push(wrap);
      this.listeners.set(method, arr);
    });
  }
  close() {
    this.ws.close();
  }
}

async function connectTarget(browserWsUrl) {
  const port = new URL(browserWsUrl).port;
  const targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  let pageTarget = targets.find((t) => t.type === "page");
  if (!pageTarget) {
    pageTarget = await (await fetch(`http://127.0.0.1:${port}/json/new`, { method: "PUT" })).json();
  }
  const ws = new WebSocket(pageTarget.webSocketDebuggerUrl);
  await new Promise((res, rej) => {
    ws.addEventListener("open", res);
    ws.addEventListener("error", rej);
  });
  const cdp = new CDPClient(ws);
  await cdp.send("Page.enable");
  await cdp.send("Runtime.enable");
  return cdp;
}

async function navigateAndWait(cdp, url) {
  const loaded = cdp.once("Page.loadEventFired");
  await cdp.send("Page.navigate", { url });
  await loaded;
  await cdp.send("Runtime.evaluate", {
    expression: `document.fonts.ready.then(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))))`,
    awaitPromise: true,
  });
}

async function setViewport(cdp, width, height) {
  await cdp.send("Emulation.setDeviceMetricsOverride", {
    width,
    height,
    deviceScaleFactor: 1,
    mobile: false,
  });
}

const AUDIT_FN = `(() => {
  const slides = Array.from(document.querySelectorAll('.deck-print-page'));
  const fonts = Array.from(document.fonts).map(f => ({ family: f.family.replace(/['"]/g, ''), status: f.status, weight: f.weight }));
  const bannedWords = [
    'additionally','crucial','delve','enduring','enhance','fostering','garner',
    'interplay','intricate','landscape','pivotal','showcase','tapestry','testament',
    'underscore','vibrant','leverage','utilize','facilitate','robust','seamless',
    'comprehensive','paradigm','holistic','cutting-edge','game-changing',
    'serves as','stands as','boasts','nemo 2'
  ];

  function parseRgb(str) {
    const m = str && str.match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)(?:,\\s*([\\d.]+))?\\)/);
    if (!m) return null;
    return { r: +m[1], g: +m[2], b: +m[3], a: m[4] == null ? 1 : +m[4] };
  }
  function lum({ r, g, b }) {
    const s = [r, g, b].map(v => {
      v /= 255;
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * s[0] + 0.7152 * s[1] + 0.0722 * s[2];
  }
  function contrast(c1, c2) {
    const l1 = lum(c1), l2 = lum(c2);
    return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
  }
  function effectiveBg(el) {
    let cur = el;
    while (cur && cur.nodeType === 1) {
      const bg = parseRgb(getComputedStyle(cur).backgroundColor);
      if (bg && bg.a > 0.9) return bg;
      cur = cur.parentElement;
    }
    return { r: 27, g: 33, b: 31, a: 1 };
  }

  const results = [];
  const sectionTones = [];
  const renderedTexts = {};

  for (const page of slides) {
    const id = page.dataset.slideId;
    const layout = page.dataset.layout;
    const tone = page.dataset.tone;
    if (layout === 'section') sectionTones.push({ id, tone });

    const slide = page.querySelector('.bf-slide');
    const sRect = slide.getBoundingClientRect();
    const issues = [];

    // Collect visible text (excluding aria-hidden decorative code texture on section slabs)
    const walker = document.createTreeWalker(slide, NodeFilter.SHOW_TEXT);
    const textChunks = [];
    let node;
    while ((node = walker.nextNode())) {
      const txt = node.nodeValue.trim();
      if (!txt) continue;
      const parent = node.parentElement;
      if (!parent || parent.closest('[aria-hidden="true"]')) continue;
      textChunks.push(txt);
    }
    const fullText = textChunks.join(' ');
    renderedTexts[id] = fullText;

    // Copy lint
    const lower = fullText.toLowerCase();
    for (const bw of bannedWords) {
      const re = new RegExp('\\\\b' + bw.replace(/[-/\\\\^$*+?.()|[\\]{}]/g, '\\\\$&') + '\\\\b', 'i');
      if (re.test(lower)) issues.push('BANNED_WORD: ' + bw);
    }
    if (fullText.includes('!')) issues.push('EXCLAMATION_MARK');
    if (fullText.includes('\\u2014')) issues.push('EM_DASH');
    if (/[\\u{1F300}-\\u{1FAFF}]/u.test(fullText)) issues.push('EMOJI');

    // Display heading rules: weight 400 and <= 3 lines
    const headings = slide.querySelectorAll('h1, h2, h3');
    for (const hd of headings) {
      const cs = getComputedStyle(hd);
      if (Number(cs.fontWeight) !== 400) {
        issues.push('NON_REGULAR_HEADING(' + hd.tagName + '): weight=' + cs.fontWeight);
      }
      const lh = parseFloat(cs.lineHeight);
      const hr = hd.getBoundingClientRect();
      if (lh > 0 && hr.height > 0) {
        const lines = Math.round(hr.height / lh);
        if (lines > 3) issues.push('HEADING_OVER_3_LINES(' + lines + '): ' + hd.textContent.slice(0, 40));
      }
    }

    // Shadows and radii check
    const allEls = slide.querySelectorAll('*');
    for (const el of allEls) {
      if (el instanceof SVGElement) continue;
      const cs = getComputedStyle(el);
      if (cs.boxShadow && cs.boxShadow !== 'none') {
        // CodeBlock marked lines use horizontal box-shadow bleed per bundle.css line 111
        if (!el.classList.contains('is-marked')) {
          issues.push('BOX_SHADOW: ' + el.className);
        }
      }
      const br = parseFloat(cs.borderTopLeftRadius);
      if (br > 0) {
        const allowed = el.classList.contains('bf-tag') || el.classList.contains('bf-btn') ||
          el.classList.contains('bf-ss-ring') || el.classList.contains('bf-sr-ring') ||
          el.closest('.bf-meter__cells');
        if (!allowed) issues.push('BORDER_RADIUS(' + br + 'px): ' + el.className);
      }
    }

    // Overflow and footer collision checks
    const checkBoxes = slide.querySelectorAll('.bf-sc-text, .bf-sc-vis, .nemo-table-panel, .bf-sm-box, .bf-sd-row, .bf-st-words, .bf-scl-words');
    const foot = slide.querySelector('.bf-s-foot');
    const fRect = foot ? foot.getBoundingClientRect() : null;
    for (const box of checkBoxes) {
      const r = box.getBoundingClientRect();
      if (box.scrollHeight > box.clientHeight + 2) {
        issues.push('VERTICAL_OVERFLOW(' + box.className + '): scroll=' + box.scrollHeight + ' client=' + box.clientHeight);
      }
      if (box.scrollWidth > box.clientWidth + 2) {
        issues.push('HORIZONTAL_OVERFLOW(' + box.className + '): scroll=' + box.scrollWidth + ' client=' + box.clientWidth);
      }
      if (r.bottom > sRect.bottom + 2 || r.right > sRect.right + 2 || r.top < sRect.top - 2 || r.left < sRect.left - 2) {
        issues.push('OUT_OF_BOUNDS(' + box.className + ')');
      }
      if (fRect && !box.classList.contains('bf-sc-vis') && r.bottom > fRect.top - 4 && r.left < fRect.right && r.right > fRect.left) {
        issues.push('FOOTER_COLLISION(' + box.className + '): bottom=' + Math.round(r.bottom) + ' footTop=' + Math.round(fRect.top));
      }
    }
    // Check nemo-vis-wrap vs footer specifically
    const visWrap = slide.querySelector('.nemo-vis-wrap');
    if (visWrap && fRect) {
      const vr = visWrap.getBoundingClientRect();
      if (vr.bottom > fRect.top - 2) {
        issues.push('VIS_FOOTER_COLLISION: visBottom=' + Math.round(vr.bottom) + ' footTop=' + Math.round(fRect.top));
      }
    }

    // WCAG 2.1 contrast check on HTML text nodes (excluding aria-hidden)
    let minContrast = 99;
    let worstContrastEl = null;
    const textEls = slide.querySelectorAll('h1, h2, h3, p, li, th, td, span, div');
    for (const el of textEls) {
      if (el.closest('[aria-hidden="true"]')) continue;
      const directText = Array.from(el.childNodes).some(n => n.nodeType === 3 && n.nodeValue.trim().length > 0);
      if (!directText) continue;
      const cs = getComputedStyle(el);
      const fg = parseRgb(cs.color);
      const bg = effectiveBg(el);
      if (!fg || !bg) continue;
      const ratio = contrast(fg, bg);
      const fsPx = parseFloat(cs.fontSize);
      const threshold = fsPx >= 24 ? 3.0 : 4.5;
      if (ratio < minContrast) {
        minContrast = ratio;
        worstContrastEl = { text: el.textContent.trim().slice(0, 30), ratio: +ratio.toFixed(2), fs: Math.round(fsPx), color: cs.color, bg: 'rgb(' + bg.r + ',' + bg.g + ',' + bg.b + ')' };
      }
      if (ratio < threshold - 0.05) {
        issues.push('LOW_CONTRAST(' + ratio.toFixed(2) + '<' + threshold + '): ' + el.textContent.trim().slice(0, 30));
      }
    }

    // Image load check
    for (const img of slide.querySelectorAll('img')) {
      if (!img.complete || img.naturalWidth === 0) {
        issues.push('BROKEN_IMAGE: ' + img.getAttribute('src'));
      }
    }

    results.push({ id, layout, tone, minContrast: +minContrast.toFixed(2), worstContrastEl, issues });
  }

  // Section tone rotation check
  const sectionToneIssues = [];
  for (let i = 1; i < sectionTones.length; i++) {
    if (sectionTones[i].tone === sectionTones[i - 1].tone) {
      sectionToneIssues.push('DUPLICATE_CONSECUTIVE_SECTION_TONE: ' + sectionTones[i - 1].id + ' & ' + sectionTones[i].id + ' (' + sectionTones[i].tone + ')');
    }
  }

  return {
    viewport: { w: window.innerWidth, h: window.innerHeight },
    fonts,
    slideCount: slides.length,
    sectionTones,
    sectionToneIssues,
    results,
    renderedTexts,
  };
})()`;

async function main() {
  const { server, port } = await startStaticServer();
  const baseUrl = `http://127.0.0.1:${port}/reports/panel-presentation/index.html`;
  const { proc, browserWsUrl } = await launchChrome();

  try {
    const cdp = await connectTarget(browserWsUrl);

    // 1. Export vector 16:9 PDFs for both themes (all 20 slides: 15 main + 5 backup)
    for (const theme of ["ink", "paper"]) {
      await setViewport(cdp, 1920, 1080);
      await navigateAndWait(cdp, `${baseUrl}?print=1&theme=${theme}`);
      const pdf = await cdp.send("Page.printToPDF", {
        landscape: false,
        printBackground: true,
        preferCSSPageSize: true,
        paperWidth: 13.333333,
        paperHeight: 7.5,
        marginTop: 0,
        marginBottom: 0,
        marginLeft: 0,
        marginRight: 0,
      });
      const pdfPath = path.join(HERE, `nemo-panel-defense-${theme}.pdf`);
      fs.writeFileSync(pdfPath, Buffer.from(pdf.data, "base64"));
      console.log(`Wrote ${pdfPath} (${(fs.statSync(pdfPath).size / 1024).toFixed(1)} KB)`);
    }

    // 2. Run full automated audit at 1920x1080 and 1280x720 for both ink and paper
    const auditSummary = {};
    let renderedTexts = null;

    for (const theme of ["ink", "paper"]) {
      for (const [vw, vh] of [[1920, 1080], [1280, 720]]) {
        await setViewport(cdp, vw, vh);
        await navigateAndWait(cdp, `${baseUrl}?print=1&theme=${theme}`);
        const ev = await cdp.send("Runtime.evaluate", {
          expression: AUDIT_FN,
          returnByValue: true,
        });
        const report = ev.result.value;
        const key = `${theme}_${vw}x${vh}`;
        if (!renderedTexts && theme === "ink" && vw === 1920) {
          renderedTexts = report.renderedTexts;
        }
        delete report.renderedTexts;
        const totalIssues =
          report.sectionToneIssues.length +
          report.results.reduce((acc, r) => acc + r.issues.length, 0);
        auditSummary[key] = { ...report, totalIssues };
        console.log(`[AUDIT ${key}] slides=${report.slideCount} totalIssues=${totalIssues} fonts=${report.fonts.map(f => `${f.family}:${f.status}`).join(", ")}`);
        if (totalIssues > 0) {
          for (const r of report.results) {
            if (r.issues.length) console.log(`  Slide ${r.id} (${r.layout}):`, r.issues);
          }
          if (report.sectionToneIssues.length) console.log("  Section tones:", report.sectionToneIssues);
        }
      }
    }

    fs.writeFileSync(path.join(AUDIT_DIR, "audit-report.json"), JSON.stringify(auditSummary, null, 2));
    fs.writeFileSync(path.join(AUDIT_DIR, "rendered-text.json"), JSON.stringify(renderedTexts, null, 2));

    // 3. Capture 1920x1080 PNG screenshots of every slide in ink + select paper slides for visual inspection
    await setViewport(cdp, 1920, 1080);
    const slideIds = [
      "01","02","03","04","05","06","07","08","09","10","11","12","13","14","15",
      "B1","B2","B3","B4","B5"
    ];
    for (const sid of slideIds) {
      await navigateAndWait(cdp, `${baseUrl}?slide=${sid}&theme=ink`);
      // Hide HUD for clean slide capture? Capture exact .bf-slide clip!
      const clipEv = await cdp.send("Runtime.evaluate", {
        expression: `(() => { const r = document.querySelector('.bf-slide').getBoundingClientRect(); return { x: r.x, y: r.y, width: r.width, height: r.height, scale: 1 }; })()`,
        returnByValue: true,
      });
      const shot = await cdp.send("Page.captureScreenshot", {
        format: "png",
        clip: clipEv.result.value,
      });
      fs.writeFileSync(path.join(SHOTS_DIR, `slide-${sid}-ink.png`), Buffer.from(shot.data, "base64"));
    }
    for (const sid of ["01", "05", "08", "10", "13"]) {
      await navigateAndWait(cdp, `${baseUrl}?slide=${sid}&theme=paper`);
      const clipEv = await cdp.send("Runtime.evaluate", {
        expression: `(() => { const r = document.querySelector('.bf-slide').getBoundingClientRect(); return { x: r.x, y: r.y, width: r.width, height: r.height, scale: 1 }; })()`,
        returnByValue: true,
      });
      const shot = await cdp.send("Page.captureScreenshot", {
        format: "png",
        clip: clipEv.result.value,
      });
      fs.writeFileSync(path.join(SHOTS_DIR, `slide-${sid}-paper.png`), Buffer.from(shot.data, "base64"));
    }
    console.log("Captured 20 ink + 5 paper verification PNGs in", SHOTS_DIR);

    cdp.close();
  } finally {
    proc.kill();
    server.close();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
