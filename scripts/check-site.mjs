#!/usr/bin/env node
/**
 * サイトの壊れを見る（CI と手元で同じ物を走らせる）。
 *   node scripts/check-site.mjs
 * 1. 全ページの <script type="application/ld+json"> が JSON として読めるか（scripts/ の型は除く）
 * 2. 全ページ（google の確認ファイルを除く）に、メニュー（Codex の型か旧 nav）・解析のタグがあるか
 * 3. 税込・初月・旧 12 万円 の文言が残っていないか
 */
import { readFileSync } from "node:fs";
import { execFileSync } from "node:child_process";

const files = execFileSync("git", ["ls-files", "--", "*.html"], { encoding: "utf8" })
  .split(/\r?\n/)
  .filter((f) => f && !f.startsWith("scripts/") && !/^google|^9c1b/.test(f));
let bad = 0;
for (const f of files) {
  const s = readFileSync(f, "utf8");
  const re = /<script type="application\/ld\+json">([\s\S]*?)<\/script>/g;
  let m;
  while ((m = re.exec(s))) {
    try { JSON.parse(m[1].replace(/<\\\//g, "</")); }
    catch (e) { console.error(`bad JSON-LD: ${f}: ${e.message}`); bad++; }
  }
  // メニュー: Codex の型（site-header＋menu-toggle）か、旧ページの nav（AI映え診断のボタン＋mobile-menu-btn）
  const menuOk = (s.includes('class="site-header"') && s.includes("menu-toggle")) || (s.includes("nav-cta-ai") && s.includes("mobile-menu-btn"));
  if (!menuOk) { console.error(`missing menu: ${f}`); bad++; }
  if (!s.includes("/_vercel/insights/script.js")) { console.error(`missing analytics tag: ${f}`); bad++; }
  // 2026-10-27 夜の決まり: 税込の額・初月の差し引き・旧 12 万円 は出さない（他社の値段を並べた記事と運賃ツールは除く）
  if (!/^insights\/llmo-aeo|^guide\/|^tools\/unchin/.test(f)) {
    for (const bad_ of ["税込", "初月", "12万円", "120,000円", "JPY 120,000"]) {
      if (s.includes(bad_)) { console.error(`forbidden wording "${bad_}": ${f}`); bad++; }
    }
  }
}
// 4. 英語のページ（en/）に日本語が混ざっていないか。HTML のコメントは除き、文字・属性・script の中まで見る。
//    許すのは固有名詞（サービス名「AI映え診断」）と、lang="ja" の印を付けた要素（言語の切り替え・日本語の記事へのリンク）だけ。
const JA_OK = ["AI映え診断"];
const JA = /[぀-ヿ㐀-鿿！-｠]/; // ひらがな・カタカナ・漢字・全角の記号
let enPages = 0;
for (const f of files.filter((f) => f.startsWith("en/"))) {
  enPages++;
  let s = readFileSync(f, "utf8").replace(/<!--[\s\S]*?-->/g, "").replace(/<(\w+)\b[^>]*\slang="ja"[^>]*>[\s\S]*?<\/\1>/g, "");
  for (const w of JA_OK) s = s.split(w).join("");
  s.split("\n").forEach((line, i) => {
    if (JA.test(line)) { console.error(`Japanese text on an English page: ${f}:${i + 1}: ${line.trim().slice(0, 120)}`); bad++; }
  });
}
// 5. hreflang は対になっているか（A が B を指すなら、B も A を指す・指した先のファイルがある）
const toFile = (u) => u.replace("https://synapsearrows.com/", "").replace(/\/?$/, "/") + "index.html";
const alt = {};
for (const f of files) {
  const s = readFileSync(f, "utf8");
  alt[f] = [...s.matchAll(/<link rel="alternate" hreflang="(ja|en)" href="([^"]+)">/g)].map((m) => toFile(m[2]).replace(/^\//, ""));
}
for (const [f, list] of Object.entries(alt)) {
  for (const g of list) {
    if (g === f) continue;
    if (!alt[g]) { console.error(`hreflang points to a page that does not exist: ${f} -> ${g}`); bad++; continue; }
    if (!alt[g].includes(f)) { console.error(`hreflang is one-way: ${f} -> ${g} (no link back)`); bad++; }
  }
}
if (bad) { console.error(`${bad} problem(s)`); process.exit(1); }
console.log(`ok: ${files.length} pages (JSON-LD, menu, analytics tag, hreflang pairs), ${enPages} English pages without Japanese text`);
