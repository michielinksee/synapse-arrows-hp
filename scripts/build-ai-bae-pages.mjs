#!/usr/bin/env node
/**
 * AI映え診断のページを、1 つの型から業種ごとに作る。
 *
 *   node scripts/build-ai-bae-pages.mjs          # 作る（ai-bae-shindan/index.html と業種別の Light 版）
 *   node scripts/build-ai-bae-pages.mjs --check  # 作った物と手元のファイルが同じか（違えば exit 1）
 *
 * 型: scripts/ai-bae/page.template.html ／ ページ: scripts/ai-bae/pages.json
 * 業種の id と表示名: ai-bae-shindan/survey.json の q1（kansei-internal の src/data/ai-bae-survey.json の写し）
 */
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (p) => readFileSync(path.join(ROOT, p), "utf-8");
const template = read("scripts/ai-bae/page.template.html");
const { pages } = JSON.parse(read("scripts/ai-bae/pages.json"));
const survey = JSON.parse(read("ai-bae-shindan/survey.json"));
const INDUSTRIES = survey.questions.q1.options.map((o) => ({ id: o.id, label: o.label }));

const escHtml = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
// JSON inside <script>: keep "</" from closing the tag
const jsonInScript = (v) => JSON.stringify(v).replace(/</g, "\\u003c");

function picker(page) {
  if (page.industry) return `<p class="fixed-ind">${page.fixed_note}</p>`;
  const chips = INDUSTRIES.map((i) => `<button type="button" class="chip" data-ind="${escHtml(i.id)}" aria-pressed="false">${escHtml(i.label)}</button>`).join("");
  return `<fieldset class="inds" id="inds"><legend>1. 業種を選ぶ<small>業種ごとに AI が頼る先が違います</small></legend><div class="chips">${chips}</div><div class="ind-msg" id="ind-msg" role="status"></div></fieldset>`;
}

// 業種別ページへの入口（共通の入口には全部、業種のページにはほかの業種）。pages.json に足せば自動で並ぶ
const navLabel = (p) => p.nav_label || ((INDUSTRIES.find((i) => i.id === p.industry) || {}).label || p.industry) + "向け";
function industryPages(page) {
  const others = pages.filter((p) => p.industry && p !== page);
  if (!others.length) return "";
  return `<p class="ind-pages">業種別の診断: ${others.map((p) => `<a href="${new URL(p.url).pathname}">${escHtml(navLabel(p))} →</a>`).join("・")}</p>`;
}

function build(page) {
  if (page.industry && !INDUSTRIES.some((i) => i.id === page.industry)) throw new Error(`unknown industry ${page.industry} (not in survey q1)`);
  const ld = {
    "@context": "https://schema.org",
    "@type": "WebApplication",
    "@id": page.url + "#webapp",
    name: page.ld_name,
    applicationCategory: "BusinessApplication",
    operatingSystem: "Web",
    offers: { "@type": "Offer", price: "0", priceCurrency: "JPY" },
    provider: { "@type": "Organization", "@id": "https://synapsearrows.com/#organization", name: "Synapse Arrows Pte. Ltd.", url: "https://synapsearrows.com/" },
    url: page.url,
    inLanguage: "ja",
    isAccessibleForFree: true,
    image: "https://synapsearrows.com" + page.og_image,
    description: page.ld_description,
  };
  const vals = {
    TITLE: escHtml(page.title),
    DESCRIPTION: escHtml(page.description),
    URL: page.url,
    OG_TITLE: escHtml(page.og_title),
    OG_DESCRIPTION: escHtml(page.og_description),
    OG_IMAGE: page.og_image,
    LD_JSON: jsonInScript(ld),
    BADGE: page.badge ? `<p class="badge">${escHtml(page.badge)}</p>` : "",
    TAGLINE: escHtml(page.tagline),
    ASK_H2: (page.industry ? "" : "2. ") + escHtml(page.ask_h2),
    INDUSTRY_PICKER: picker(page),
    FIXED_INDUSTRY: page.industry ? JSON.stringify(page.industry) : "null",
    INDUSTRIES_JSON: jsonInScript(INDUSTRIES),
    INDUSTRY_PAGES: industryPages(page),
  };
  const html = template.replace(/\{\{([A-Z0-9_]+)\}\}/g, (m, k) => {
    if (!(k in vals)) throw new Error(`template placeholder ${k} has no value`);
    return vals[k];
  });
  return html;
}

const check = process.argv.includes("--check");
let diff = 0;
for (const page of pages) {
  const html = build(page);
  const out = path.join(ROOT, page.out);
  if (check) {
    const cur = existsSync(out) ? readFileSync(out, "utf-8").replace(/\r\n/g, "\n") : "";
    if (cur !== html) { console.error(`differs: ${page.out}`); diff++; }
  } else {
    mkdirSync(path.dirname(out), { recursive: true });
    writeFileSync(out, html);
    console.log(`wrote ${page.out}`);
  }
}
if (check) { if (diff) process.exit(1); console.log(`ok: ${pages.length} pages match the template`); }
