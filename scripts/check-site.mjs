#!/usr/bin/env node
/**
 * サイトの壊れを見る（CI と手元で同じ物を走らせる）。
 *   node scripts/check-site.mjs
 * 1. 全ページの <script type="application/ld+json"> が JSON として読めるか（scripts/ の型は除く）
 * 2. 全ページ（google の確認ファイルを除く）に、新しいメニュー・スマホのボタン・解析のタグがあるか
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
  for (const needle of ['nav-cta-ai', "mobile-menu-btn", "/_vercel/insights/script.js"]) {
    if (!s.includes(needle)) { console.error(`missing ${needle}: ${f}`); bad++; }
  }
}
if (bad) { console.error(`${bad} problem(s)`); process.exit(1); }
console.log(`ok: ${files.length} pages (JSON-LD, menu, analytics tag)`);
