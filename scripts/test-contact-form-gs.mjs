#!/usr/bin/env node
/**
 * scripts/contact-form.gs（Google Apps Script の受け口）を Node で動かし、ページが送る形の見本で
 * シートに入る 1 行（配列）が期待どおりかを確かめる。Google の道具（SpreadsheetApp・MailApp・UrlFetchApp など）は偽物。
 *   node scripts/test-contact-form-gs.mjs
 *
 * 見本は 3 つ（ページの送り方をそのまま写した物）:
 *   1. 日本語の資料請求  … contact/index.html の collect() → contact/confirm/index.html が purpose・lang・consent を足して送る
 *   2. 日本語の相談      … 同じ。料金ページから ?service=AI映え診断&plan=report&intent=相談・見積もり で来た時
 *   3. 英語              … en/contact/index.html の collect()（services・plan・intent は送らない）
 * もう 1 つ、ページの送る項目の名前と、contact-form.gs が読む名前が揃っているかも見る（片方だけ名前を変えたら落ちる）。
 */
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import vm from "node:vm";
import assert from "node:assert/strict";

const SRC = readFileSync("scripts/contact-form.gs", "utf8");
const NOW = "2026-10-28 12:34:56";

function makeGas({ props = {}, turnstileOk = true } = {}) {
  const sheets = {};
  const mails = [];
  const fetches = [];
  const cache = new Map();
  const ss = {
    getName: () => "Synapse 資料請求・相談（試験）",
    getUrl: () => "https://docs.google.com/spreadsheets/d/TEST/edit",
    getSheetByName: (n) => sheets[n] || null,
    insertSheet: (n) => {
      const rows = [];
      sheets[n] = { rows, getLastRow: () => rows.length, appendRow: (r) => rows.push(Array.from(r)), setFrozenRows: () => {} };
      return sheets[n];
    }
  };
  const ctx = {
    console: { log() {}, error() {} },
    JSON, Date, Number, String, Array, Object, Error,
    PropertiesService: { getScriptProperties: () => ({ getProperty: (k) => (k in props ? props[k] : null) }) },
    LockService: { getScriptLock: () => ({ waitLock() {}, releaseLock() {} }) },
    CacheService: { getScriptCache: () => ({ get: (k) => cache.get(k) ?? null, put: (k, v) => cache.set(k, v) }) },
    SpreadsheetApp: { openById: (id) => { assert.equal(id, props.SHEET_ID); return ss; } },
    MailApp: { sendEmail: (m) => mails.push(m), getRemainingDailyQuota: () => 1500 },
    UrlFetchApp: {
      fetch: (url, opt) => {
        fetches.push({ url, opt });
        return { getResponseCode: () => 200, getContentText: () => JSON.stringify({ success: turnstileOk }) };
      }
    },
    Utilities: {
      formatDate: (d, tz, fmt) => { assert.equal(tz, "Asia/Tokyo"); assert.equal(fmt, "yyyy-MM-dd HH:mm:ss"); return NOW; },
      DigestAlgorithm: { SHA_256: "sha256" },
      Charset: { UTF_8: "utf8" },
      computeDigest: (alg, s) => Array.from(createHash("sha256").update(s, "utf8").digest()).map((b) => (b > 127 ? b - 256 : b))
    },
    ContentService: {
      MimeType: { JSON: "json" },
      createTextOutput: (t) => ({ text: t, setMimeType() { return this; } })
    }
  };
  vm.createContext(ctx);
  vm.runInContext(SRC, ctx, { filename: "contact-form.gs" });
  const post = (payload) => JSON.parse(ctx.doPost({ postData: { contents: JSON.stringify(payload) } }).text);
  return { ctx, post, sheets, mails, fetches };
}

// ---- 見本（ページの送り方を写す） ----
// 日本語: 入力の段の collect() の形
const jaBase = {
  intent: "資料請求",
  services: ["海外進出支援", "AI映え診断"],
  plan: "",
  company: "試験株式会社", name: "山田 太郎", email: "taro@example.com",
  industry: "restaurant", industry_label: "飲食",
  site_url: "https://example.com", message: "資料をお願いします",
  consent: true, website_hp: "",
  page: "https://synapsearrows.com/contact/", referrer: "https://synapsearrows.com/services/",
  utm_source: "prtimes", utm_medium: "release", utm_campaign: "2026-11"
};
// 確認の段: Object.assign({}, d, { purpose, lang: 'ja', ts, consent: true }) ＋ 券があれば turnstile_token
const jaSend = (d) => Object.assign({}, d, { purpose: d.intent === "資料請求" ? "download" : "consult", lang: "ja", ts: "2026-10-28T03:34:56.000Z", consent: true });

const jaDownload = jaSend(jaBase);
const jaConsult = jaSend({
  ...jaBase,
  intent: "相談・見積もり", services: ["AI映え診断"], plan: "照合レポート",
  industry: "", industry_label: "", site_url: "", message: "",
  referrer: "https://synapsearrows.com/ai-bae-shindan/pricing/", utm_source: "test", utm_medium: "", utm_campaign: "",
  turnstile_token: "tok-123"
});
// 英語: en/contact/index.html の collect() の形
const en = {
  company: "Test Pte. Ltd.", name: "Jane Doe", email: "jane@example.com",
  industry: "saas_web", industry_label: "SaaS / web service",
  site_url: "https://example.sg", purpose: "download", message: "=SUM(A1)",
  consent: true, website_hp: "", lang: "en",
  page: "https://synapsearrows.com/en/contact/", referrer: "", utm_source: "", utm_medium: "", utm_campaign: "",
  ts: "2026-10-28T03:34:56.000Z"
};

let n = 0;
function t(name, fn) { fn(); n++; console.log(`ok ${n} - ${name}`); }

// ---- 1. 日本語の資料請求（シークレットなし → Turnstile は off）----
t("日本語の資料請求 → 見出し＋1 行", () => {
  const g = makeGas({ props: { SHEET_ID: "SHEET-TEST" } });
  assert.deepEqual(g.post(jaDownload), { ok: true });
  const rows = g.sheets.inquiries.rows;
  assert.equal(rows.length, 2);
  assert.deepEqual(rows[0], Array.from(g.ctx.HEADERS));
  assert.equal(rows[0].length, 19);
  assert.deepEqual(rows[1], [
    NOW, "資料請求", "試験株式会社", "山田 太郎", "taro@example.com", "restaurant", "飲食", "https://example.com", "資料をお願いします",
    "海外進出支援 ／ AI映え診断", "",
    "ja", "https://synapsearrows.com/contact/", "https://synapsearrows.com/services/", "prtimes", "release", "2026-11", "off", ""
  ]);
  assert.equal(g.mails.length, 1);
  assert.equal(g.mails[0].to, "contact@synapse-arrows.com");
  assert.equal(g.mails[0].subject, "【資料請求・相談】資料請求｜試験株式会社");
  assert.equal(g.mails[0].replyTo, "taro@example.com");
  assert.equal(g.fetches.length, 0);
});

// ---- 2. 日本語の相談（料金ページから・業種なし・券あり → ok）----
t("日本語の相談（プラン・券あり・業種は空）→ 1 行", () => {
  const g = makeGas({ props: { SHEET_ID: "SHEET-TEST", TURNSTILE_SECRET: "s", NOTIFY_TO: "a@example.com, b@example.com" } });
  assert.deepEqual(g.post(jaConsult), { ok: true });
  assert.deepEqual(g.sheets.inquiries.rows[1], [
    NOW, "相談・見積もり", "試験株式会社", "山田 太郎", "taro@example.com", "", "", "", "",
    "AI映え診断", "照合レポート",
    "ja", "https://synapsearrows.com/contact/", "https://synapsearrows.com/ai-bae-shindan/pricing/", "test", "", "", "ok", ""
  ]);
  assert.equal(g.fetches.length, 1);
  assert.equal(g.fetches[0].opt.payload.response, "tok-123");
  assert.equal(g.mails[0].to, "a@example.com, b@example.com");
  assert.equal(g.mails[0].subject, "【資料請求・相談】相談・見積もり｜試験株式会社");
  assert.match(g.mails[0].body, /業種: （なし）/);
  assert.match(g.mails[0].body, /プラン: 照合レポート/);
});

// ---- 3. 英語（シークレットあり・券なし・必須でない → none。数式に見える値は ' を前に）----
t("英語 → 1 行（services・plan は空、数式は無害化）", () => {
  const g = makeGas({ props: { SHEET_ID: "SHEET-TEST", TURNSTILE_SECRET: "s" } });
  assert.deepEqual(g.post(en), { ok: true });
  assert.deepEqual(g.sheets.inquiries.rows[1], [
    NOW, "資料請求", "Test Pte. Ltd.", "Jane Doe", "jane@example.com", "saas_web", "SaaS / web service", "https://example.sg", "'=SUM(A1)",
    "", "",
    "en", "https://synapsearrows.com/en/contact/", "", "", "", "", "none", ""
  ]);
});

// ---- 断る場合 ----
t("断る: 必須の券が無い・見えない欄・同意なし・用件が不明・回数の上限", () => {
  const g = makeGas({ props: { SHEET_ID: "SHEET-TEST", TURNSTILE_SECRET: "s", TURNSTILE_REQUIRED: "true" } });
  assert.deepEqual(g.post(en), { ok: false, error: "turnstile_required" });
  const g2 = makeGas({ props: { SHEET_ID: "SHEET-TEST", TURNSTILE_SECRET: "s" }, turnstileOk: false });
  assert.deepEqual(g2.post(jaConsult), { ok: false, error: "turnstile_failed" });
  const g3 = makeGas({ props: { SHEET_ID: "SHEET-TEST" } });
  assert.deepEqual(g3.post({ ...jaDownload, website_hp: "x" }), { ok: false, error: "bad_request" });
  assert.deepEqual(g3.post({ ...jaDownload, consent: false }), { ok: false, error: "bad_request" });
  assert.deepEqual(g3.post({ ...jaDownload, purpose: "spam" }), { ok: false, error: "bad_request" });
  for (let i = 0; i < 5; i++) assert.deepEqual(g3.post(jaDownload), { ok: true });
  assert.deepEqual(g3.post(jaDownload), { ok: false, error: "rate_limited" });
  assert.equal(g3.sheets.inquiries.rows.length, 6);
});

// ---- ページの送る名前と、受け口が読む名前が揃っているか ----
t("ページの送る項目の名前 ＝ contact-form.gs が読む名前", () => {
  const reads = new Set([...SRC.matchAll(/\bp\.([a-z_]+)\b/g)].map((m) => m[1]));
  const keysIn = (file) => {
    const s = readFileSync(file, "utf8");
    const js = s.slice(s.lastIndexOf("<script"));
    const prev = s.slice(s.indexOf("const ENDPOINT"));
    return new Set([...(js + prev).matchAll(/\b([a-z_]+)\s*:/g), ...(js + prev).matchAll(/\bp\.([a-z_]+)\s*=/g)].map((m) => m[1]));
  };
  const ja = new Set([...keysIn("contact/index.html"), ...keysIn("contact/confirm/index.html")]);
  // 英語も日本語と同じ 2 段（入力 → 確認で送る）。2 枚を合わせて見る
  const enKeys = new Set([...keysIn("en/contact/index.html"), ...keysIn("en/contact/confirm/index.html")]);
  const missingJa = [...reads].filter((k) => !ja.has(k));
  const missingEn = [...reads].filter((k) => !enKeys.has(k)).sort();
  assert.deepEqual(missingJa, [], `日本語のページが送らない名前: ${missingJa}`);
  assert.deepEqual(missingEn, [], `英語のページが送らない名前: ${missingEn}`);
});

console.log(`ok: ${n} tests (scripts/contact-form.gs)`);
