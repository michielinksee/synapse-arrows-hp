#!/usr/bin/env node
/**
 * AI映え診断のページを、1 つの型から業種ごとに作る。
 *
 *   node scripts/build-ai-bae-pages.mjs          # 作る（ai-bae-shindan/index.html と業種別の Light 版）
 *   node scripts/build-ai-bae-pages.mjs --check  # 作った物と手元のファイルが同じか（違えば exit 1）
 *
 * 型: scripts/ai-bae/page.template.html ／ ページ: scripts/ai-bae/pages.json
 * 業種の id と表示名: ai-bae-shindan/survey.json の q1（kansei-internal の src/data/ai-bae-survey.json の写し）
 * 値段: pricing.json（repo の根・値段の正本）。結果の下の「料金と相談」の数字はここから入れ、
 *       <!--p:KEY-->…<!--/p--> の印で包むので、scripts/build-pricing.mjs --check で正本と同じ値かを確かめられる。
 */
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (p) => readFileSync(path.join(ROOT, p), "utf-8").replace(/\r\n/g, "\n"); // Windows の autocrlf で型が CRLF になっても同じ物を作る
const template = read("scripts/ai-bae/page.template.html");
const { pages } = JSON.parse(read("scripts/ai-bae/pages.json"));
const survey = JSON.parse(read("ai-bae-shindan/survey.json"));
const PRICING = JSON.parse(read("pricing.json"));
// 表示の形は scripts/build-pricing.mjs の man と同じ（5万円・starting_at なら「21万円〜」）。税込は出さない（2026-10-27 夜の決定）
const man = (n) => { const m = n / 10000; return (Number.isInteger(m) ? String(m) : m.toFixed(1).replace(/\.0$/, "")) + "万円"; };
const manOf = (x) => man(x.price_jpy) + (x.starting_at ? "〜" : "");
const p = (key, value) => `<!--p:${key}-->${value}<!--/p-->`;
const plan = (id) => { const x = PRICING.plans[id]; if (!x) throw new Error(`pricing.json に plan "${id}" が無い`); return x; };
const PRICE_VALS = {
  PRICE_SCOPE: p("scope_ja", PRICING.scope_ja),
  PLAN_REPORT_NAME: p("report.name_ja", plan("report").name_ja),
  PRICE_REPORT: p("report.man", manOf(plan("report"))),
  PLAN_REPORT_REMEASURE_NAME: p("report_remeasure.name_ja", plan("report_remeasure").name_ja),
  PRICE_REPORT_REMEASURE: p("report_remeasure.man", manOf(plan("report_remeasure"))),
  PLAN_MONITOR_NAME: p("monitor.name_ja", plan("monitor").name_ja),
  PRICE_MONITOR: p("monitor.man", manOf(plan("monitor"))),
  MONITOR_MIN_MONTHS: p("monitor.min_months", String(plan("monitor").min_months ?? "")),
  PLAN_IMPLEMENT_NAME: p("implement.name_ja", plan("implement").name_ja),
  PRICE_IMPLEMENT: p("implement.man", manOf(plan("implement"))),
  IMPLEMENT_MIN_MONTHS: p("implement.min_months", String(plan("implement").min_months ?? "")),
  PRICE_TAX_NOTE: p("tax_note_ja", PRICING.tax_note_ja),
};
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
    ...PRICE_VALS,
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
    if (cur !== html.replace(/\r\n/g, "\n")) { console.error(`differs: ${page.out}`); diff++; } // the template may be checked out with CRLF
  } else {
    mkdirSync(path.dirname(out), { recursive: true });
    writeFileSync(out, html);
    console.log(`wrote ${page.out}`);
  }
}
if (check) { if (diff) process.exit(1); console.log(`ok: ${pages.length} pages match the template`); }
