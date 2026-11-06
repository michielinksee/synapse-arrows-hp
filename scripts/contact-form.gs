/**
 * Synapse Arrows 資料請求・相談フォームの受け口（Google Apps Script・V8）
 *
 * 何をするか:
 *   synapsearrows.com/contact/ と /en/contact/ のフォームから届いた 1 件を、
 *   Google スプレッドシートの「inquiries」シートに 1 行足し、担当にメールで知らせる。
 *   ページ側の ENDPOINT は scripts/site/contact.json の endpoint 1 か所に書き、python scripts/build-site.py で
 *   contact/index.html・contact/confirm/index.html・en/contact/index.html の 3 枚に入れる（HTML を手で直さない）。
 *   試験: node scripts/test-contact-form-gs.mjs（ページが送る形の見本 3 つで、シートの 1 行を確かめる）
 *   このファイルは .vercelignore の scripts/ にあるので、サイトには公開されない。
 *
 * スクリプト プロパティ（プロジェクトの設定 → スクリプト プロパティ）:
 *   SHEET_ID            必須。記録先スプレッドシートの ID（URL の /d/ と /edit のあいだ）
 *   NOTIFY_TO           任意。知らせる宛先。カンマ区切りで複数可。空なら contact@synapse-arrows.com
 *   TURNSTILE_SECRET    任意。Cloudflare Turnstile のウィジェット kansei-link-checkers のシークレット キー
 *   TURNSTILE_REQUIRED  任意。'true' のとき、確認の券（turnstile_token）が無い送信を断る
 *
 * デプロイ: デプロイ → 新しいデプロイ → 種類「ウェブアプリ」
 *   実行するユーザー: 自分 ／ アクセスできるユーザー: 全員
 *   コードを直したら: デプロイを管理 → 編集（鉛筆）→ バージョン: 新バージョン → デプロイ（URL は変わらない）
 *   スクリプト プロパティの変更は、デプロイし直さなくてもすぐ効く。
 *
 * 手順書: KanseiLINK/founder-ops/research/AiBae_2026-10/STEPS-contact-form-gas-michie.md
 */

var SHEET_NAME = 'inquiries';
var HEADERS = [
  '受付日時(JST)', 'ご用件', '会社名・店名', 'お名前', 'メール', '業種 id', '業種', 'サイトの URL', 'ひとこと',
  '選んだサービス', 'プラン',
  '言語', 'ページ', '参照元', 'utm_source', 'utm_medium', 'utm_campaign', 'Turnstile', '状態'
];
var PURPOSES = {
  download: '資料請求',
  consult: '無料相談（20 分・オンライン）',
  quote: '見積もり（複数店舗・会社として）',
  other: 'そのほか'
};
// 日本語の /contact/ は「資料請求」「相談・見積もり」の 2 択（intent）を送る。purpose は download／consult に丸めた物なので、
// ご用件の列には、ページで選ばれた言葉をそのまま入れる（英語のページは intent を送らないので PURPOSES の言葉）
var INTENTS = ['資料請求', '相談・見積もり'];
var DEFAULT_NOTIFY_TO = 'contact@synapse-arrows.com';
var MAX_FIELD = 500;
var MAX_MESSAGE = 2000;
var RATE_MAX = 5;            // 同じメールアドレスから 1 時間に 5 件まで
var RATE_WINDOW_SEC = 3600;
var EMAIL_RE = /^[^\s@<>()",;:\\]+@[^\s@<>()",;:\\]+\.[^\s@<>()",;:\\]+$/;

function doGet() {
  return json_({ ok: true, service: 'synapse-contact-form' });
}

function doPost(e) {
  try {
    return handle_(e);
  } catch (err) {
    console.error('contact-form: ' + (err && err.stack ? err.stack : err));
    return json_({ ok: false, error: 'server_error' });
  }
}

function handle_(e) {
  // 1. 読む・確かめる
  var raw = e && e.postData && typeof e.postData.contents === 'string' ? e.postData.contents : '';
  var p;
  try { p = JSON.parse(raw); } catch (err) { return bad_(); }
  if (!p || typeof p !== 'object' || Array.isArray(p)) return bad_();

  if (str_(p.website_hp) !== '') return bad_();                 // 見えない欄（人は空のまま）
  if (str_(p.message).length > MAX_MESSAGE) return bad_();

  var f = {
    company: cut_(p.company, MAX_FIELD),
    name: cut_(p.name, MAX_FIELD),
    email: cut_(p.email, MAX_FIELD),
    industry: cut_(p.industry, MAX_FIELD),
    industry_label: cut_(p.industry_label, MAX_FIELD),
    site_url: cut_(p.site_url, MAX_FIELD),
    purpose: cut_(p.purpose, MAX_FIELD),
    services: cut_(Array.isArray(p.services) ? p.services.map(function (x) { return str_(x); }).filter(Boolean).join(' ／ ') : p.services, MAX_FIELD),
    plan: cut_(p.plan, MAX_FIELD),
    intent: cut_(p.intent, MAX_FIELD),
    message: cut_(p.message, MAX_MESSAGE),
    lang: cut_(p.lang, MAX_FIELD),
    page: cut_(p.page, MAX_FIELD),
    referrer: cut_(p.referrer, MAX_FIELD),
    utm_source: cut_(p.utm_source, MAX_FIELD),
    utm_medium: cut_(p.utm_medium, MAX_FIELD),
    utm_campaign: cut_(p.utm_campaign, MAX_FIELD),
    turnstile_token: cut_(p.turnstile_token, 4096)
  };
  if (!f.company || !f.name || !f.email || !f.purpose) return bad_();   // 業種は任意（2026-10-27 夜の画面から）
  if (!PURPOSES.hasOwnProperty(f.purpose)) return bad_();
  if (!(p.consent === true || p.consent === 'true' || p.consent === 'on')) return bad_();
  if (f.email.length > 254 || !EMAIL_RE.test(f.email)) return bad_();
  f.purpose_label = INTENTS.indexOf(f.intent) >= 0 ? f.intent : PURPOSES[f.purpose];

  var props = PropertiesService.getScriptProperties();

  // 2. Turnstile（人による操作の確認）
  var turnstile;
  var secret = props.getProperty('TURNSTILE_SECRET');
  if (!secret) {
    turnstile = 'off';
  } else if (f.turnstile_token) {
    if (!verifyTurnstile_(secret, f.turnstile_token)) return json_({ ok: false, error: 'turnstile_failed' });
    turnstile = 'ok';
  } else if (props.getProperty('TURNSTILE_REQUIRED') === 'true') {
    return json_({ ok: false, error: 'turnstile_required' });
  } else {
    turnstile = 'none';
  }

  // 3. 回数の上限（メールアドレスの sha-256 で数える。アドレスそのものはキャッシュに置かない）
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  var ss, row;
  try {
    var cache = CacheService.getScriptCache();
    var key = 'rl_' + sha256Hex_(f.email.toLowerCase());
    var count = Number(cache.get(key) || 0);
    if (count >= RATE_MAX) return json_({ ok: false, error: 'rate_limited' });
    cache.put(key, String(count + 1), RATE_WINDOW_SEC);

    // 4. シートに 1 行足す
    var sheetId = props.getProperty('SHEET_ID');
    if (!sheetId) throw new Error('SHEET_ID is not set');
    ss = SpreadsheetApp.openById(sheetId);
    var sheet = ss.getSheetByName(SHEET_NAME) || ss.insertSheet(SHEET_NAME);
    if (sheet.getLastRow() === 0) {
      sheet.appendRow(HEADERS);
      sheet.setFrozenRows(1);
    }
    row = [
      Utilities.formatDate(new Date(), 'Asia/Tokyo', 'yyyy-MM-dd HH:mm:ss'),
      f.purpose_label,
      f.company, f.name, f.email, f.industry, f.industry_label, f.site_url, f.message,
      f.services, f.plan,
      f.lang, f.page, f.referrer, f.utm_source, f.utm_medium, f.utm_campaign,
      turnstile,
      '' // 状態（Michie が 対応中／済 を書く）
    ];
    sheet.appendRow(row.map(safeCell_));
  } finally {
    lock.releaseLock();
  }

  // 5. 知らせる（失敗しても行は残っているので、受け付けたことにする）
  try {
    notify_(props, ss, f);
  } catch (err) {
    console.error('contact-form notify failed: ' + err);
  }

  // 6. 返す
  return json_({ ok: true });
}

function notify_(props, ss, f) {
  var to = (props.getProperty('NOTIFY_TO') || '').trim() || DEFAULT_NOTIFY_TO;
  var purposeLabel = f.purpose_label;
  var subject = oneLine_('【資料請求・相談】' + purposeLabel + '｜' + f.company).slice(0, 200);
  var lines = [
    'ご用件: ' + purposeLabel,
    '会社名・店名: ' + f.company,
    'お名前: ' + f.name,
    'メール: ' + f.email,
    '業種: ' + (f.industry ? f.industry_label + '（' + f.industry + '）' : '（なし）'),
    'サイトの URL: ' + (f.site_url || '（なし）'),
    '選んだサービス: ' + (f.services || '（なし）'),
    'プラン: ' + (f.plan || '（なし）'),
    'ひとこと:',
    f.message || '（なし）',
    '',
    '言語: ' + f.lang,
    'ページ: ' + f.page,
    '参照元: ' + f.referrer,
    'utm: ' + [f.utm_source, f.utm_medium, f.utm_campaign].join(' / '),
    '',
    'シートを開く: ' + ss.getUrl()
  ];
  MailApp.sendEmail({
    to: to,
    subject: subject,
    body: lines.join('\n'),
    replyTo: f.email,
    name: 'Synapse 資料請求・相談フォーム'
  });
}

function verifyTurnstile_(secret, token) {
  try {
    var res = UrlFetchApp.fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
      method: 'post',
      payload: { secret: secret, response: token },
      muteHttpExceptions: true
    });
    if (res.getResponseCode() !== 200) return false;
    var j = JSON.parse(res.getContentText());
    return j && j.success === true;
  } catch (err) {
    console.error('turnstile verify failed: ' + err);
    return false;
  }
}

/** エディタから一度だけ実行する: 権限の承認と、シート・見出しの用意を確かめる（メールは送らない） */
function checkSetup() {
  var props = PropertiesService.getScriptProperties();
  var sheetId = props.getProperty('SHEET_ID');
  if (!sheetId) throw new Error('スクリプト プロパティ SHEET_ID がありません');
  var ss = SpreadsheetApp.openById(sheetId);
  var sheet = ss.getSheetByName(SHEET_NAME) || ss.insertSheet(SHEET_NAME);
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(HEADERS);
    sheet.setFrozenRows(1);
  }
  CacheService.getScriptCache().get('rl_check');
  console.log('シート: ' + ss.getName() + ' / ' + SHEET_NAME + ' / ' + ss.getUrl());
  console.log('通知先: ' + ((props.getProperty('NOTIFY_TO') || '').trim() || DEFAULT_NOTIFY_TO));
  console.log('Turnstile: ' + (props.getProperty('TURNSTILE_SECRET') ? 'シークレットあり' : 'なし（off）') +
    ' / 必須: ' + (props.getProperty('TURNSTILE_REQUIRED') === 'true' ? 'はい' : 'いいえ'));
  console.log('メールの残り（今日）: ' + MailApp.getRemainingDailyQuota());
}

// ---- 小さな道具 ----

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

function bad_() {
  return json_({ ok: false, error: 'bad_request' });
}

function str_(v) {
  return v === null || v === undefined ? '' : String(v).trim();
}

function cut_(v, max) {
  return str_(v).slice(0, max);
}

function oneLine_(s) {
  return String(s).replace(/[\r\n\t]+/g, ' ');
}

/** 「=」「+」「-」「@」で始まる値を、シートが数式として読まないようにする */
function safeCell_(v) {
  if (typeof v !== 'string') return v;
  return /^[=+\-@\t\r]/.test(v) ? "'" + v : v;
}

function sha256Hex_(s) {
  var bytes = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, s, Utilities.Charset.UTF_8);
  return bytes.map(function (b) { return ('0' + (b & 0xff).toString(16)).slice(-2); }).join('');
}
