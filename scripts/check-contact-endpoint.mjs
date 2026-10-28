#!/usr/bin/env node
/**
 * 資料請求・相談フォームの送り先（ENDPOINT）が 4 枚とも同じ値で、scripts/site/contact.json の endpoint と同じかを見る。
 *   node scripts/check-contact-endpoint.mjs
 * 4 枚: contact/index.html（入力の段）・contact/confirm/index.html（確認の段）・en/contact/index.html と en/contact/confirm/index.html（英語）
 * 値は contact.json に書いて python scripts/build-site.py で入れる。1 枚だけ手で貼ると、ここで落ちる。
 */
import { readFileSync } from "node:fs";

const PAGES = ["contact/index.html", "contact/confirm/index.html", "en/contact/index.html", "en/contact/confirm/index.html"];
const SHAPE = /^https:\/\/script\.google\.com\/macros\/s\/[A-Za-z0-9_-]+\/exec$/;

const want = String(JSON.parse(readFileSync("scripts/site/contact.json", "utf8")).endpoint ?? "").trim();
let bad = 0;
if (want && !SHAPE.test(want)) { console.error(`contact.json: endpoint の形が違う: ${want}`); bad++; }

for (const f of PAGES) {
  const lines = readFileSync(f, "utf8").match(/^const ENDPOINT = '([^'\r\n]*)';\r?$/gm) || [];
  if (lines.length !== 1) { console.error(`${f}: const ENDPOINT = '…'; の行が ${lines.length} 個（1 個のはず）`); bad++; continue; }
  const got = lines[0].replace(/^const ENDPOINT = '|';\r?$/g, "");
  if (got !== want) { console.error(`${f}: ENDPOINT が contact.json と違う（ページ: '${got}' ／ contact.json: '${want}'）`); bad++; }
}
if (bad) { console.error(`${bad} problem(s)。scripts/site/contact.json を直して python scripts/build-site.py を走らせる`); process.exit(1); }
console.log(`ok: ENDPOINT is the same on ${PAGES.length} pages (${want ? "set" : "empty = email fallback"})`);
