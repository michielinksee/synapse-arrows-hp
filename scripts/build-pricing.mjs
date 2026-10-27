#!/usr/bin/env node
/**
 * 値段を 1 か所（pricing.json）から全ページへ流し込む。
 *
 *   node scripts/build-pricing.mjs          # 書き換える
 *   node scripts/build-pricing.mjs --check  # ページが pricing.json と同じか（違えば exit 1）
 *
 * ページ側の印:  <!--p:KEY-->今の表示<!--/p-->
 *   KEY = <plan>.<form>   例: report.man → 5万円 ／ report.yen → 50,000円 ／ report.man_incl → 5.5万円
 *                          form: man / man_incl / yen / yen_incl / jpy / jpy_incl / raw / raw_incl / min_months / name_ja / name_en / label_ja / label_en
 *   KEY = tax_note_ja / tax_note_en / credit_rule_ja / credit_rule_en / min_term_reason_ja / min_term_reason_en / scope_ja / scope_en / decided_on / decided_on_ja / sgd_note_en
 *   KEY = block:<name>    スクリプトが作る大きめの断片。block:ld_pricing_ja／ld_pricing_en＝料金の JSON-LD の <script> まるごと（印は script の外に置く）・block:llms_pricing＝llms.txt の料金の行
 *
 * 印の外の文字はスクリプトが触らないので、文章は HTML に、数字は JSON に置く。
 */
import { readFileSync, writeFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), "..");
const P = JSON.parse(readFileSync(path.join(ROOT, "pricing.json"), "utf-8"));
const TAX = Number(P.tax_rate) || 0;

const num = (n) => n.toLocaleString("en-US");
const incl = (n) => Math.round(n * (1 + TAX));
const man = (n) => {
  const m = n / 10000;
  return (Number.isInteger(m) ? String(m) : m.toFixed(1).replace(/\.0$/, "")) + "万円";
};
const unitJa = (plan) => (plan.billing === "monthly" ? "／月" : "");
const unitEn = (plan) => (plan.billing === "monthly" ? "/month" : "");

function planValue(id, form) {
  const plan = P.plans[id];
  if (!plan) throw new Error(`pricing.json に plan "${id}" が無い`);
  const price = plan.price_jpy;
  switch (form) {
    case "name_ja": return plan.name_ja;
    case "name_en": return plan.name_en;
    case "label_ja": return plan.price_label_ja ?? `${man(price)}${unitJa(plan)}`;
    case "label_en": return plan.price_label_en ?? `JPY ${num(price)}${unitEn(plan)}`;
    case "man": return man(price);
    case "man_incl": return man(incl(price));
    case "yen": return `${num(price)}円`;
    case "yen_incl": return `${num(incl(price))}円`;
    case "jpy": return `JPY ${num(price)}`;
    case "jpy_incl": return `JPY ${num(incl(price))}`;
    case "raw": return String(price);
    case "raw_incl": return String(incl(price));
    case "min_months": return String(plan.min_months ?? "");
    default: throw new Error(`知らない形 "${form}"（${id}.${form}）`);
  }
}

const pct = Math.round(TAX * 100);
const scalars = {
  tax_note_ja: TAX > 0 ? `表示の値段は税別です。税込は消費税 ${pct}% で計算した参考の額です。` : "表示の値段に消費税はかかりません。",
  tax_note_en: TAX > 0 ? `Prices exclude tax. Tax-inclusive figures assume ${pct}% Japanese consumption tax.` : "No consumption tax is added to the prices shown.",
  credit_rule_ja: P.credit_rule_ja,
  credit_rule_en: P.credit_rule_en,
  min_term_reason_ja: P.min_term_reason_ja,
  min_term_reason_en: P.min_term_reason_en,
  scope_ja: P.scope_ja,
  scope_en: P.scope_en,
  sgd_note_en: P.sgd_note_en,
  decided_on: P.decided_on,
  decided_on_ja: P.decided_on.replace(/^(\d{4})-(\d{2})-(\d{2})$/, (m, y, mo, d) => `${y}年${Number(mo)}月${Number(d)}日`),
  implement_fixes_ja: P.implement_monthly_fixes ? `月 ${P.implement_monthly_fixes} 件まで` : "月の件数はご相談の上で決めます",
  implement_fixes_en: P.implement_monthly_fixes ? `up to ${P.implement_monthly_fixes} fixes a month` : "the number of fixes per month is agreed with you",
};

const PAID = ["report", "report_remeasure", "monitor", "implement"];
const FREE = ["light", "detailed"];
const offer = (id, lang) => {
  const plan = P.plans[id];
  const name = lang === "ja" ? plan.name_ja : plan.name_en;
  const o = {
    "@type": "Offer",
    name,
    priceCurrency: "JPY",
    priceSpecification: {
      "@type": "UnitPriceSpecification",
      price: String(plan.price_jpy),
      priceCurrency: "JPY",
      valueAddedTaxIncluded: false,
      ...(plan.billing === "monthly" ? { unitText: lang === "ja" ? "月" : "month" } : {}),
    },
    ...(plan.min_months ? { eligibleDuration: { "@type": "QuantitativeValue", minValue: plan.min_months, unitCode: "MON" } } : {}),
    itemOffered: { "@type": "Service", name, ...(plan.billing === "free" ? { url: "https://synapsearrows.com/ai-bae-shindan/" } : {}) },
  };
  return o;
};
// 1 つの <script type="application/ld+json"> をまるごと作る（印の HTML コメントは JSON の中に置けないため）
const ldScript = (lang) => {
  const node = {
    "@context": "https://schema.org",
    "@type": "Service",
    "@id": "https://synapsearrows.com/services/#ai-bae",
    name: lang === "ja" ? "AI映え診断" : "AI映え診断 (AI visibility check for shops and companies)",
    serviceType: ["AI Visibility Audit", "Answer Engine Optimization", "Generative Engine Optimization"],
    provider: { "@type": "Organization", "@id": "https://synapsearrows.com/#organization", "name": "Synapse Arrows Pte. Ltd.", "url": "https://synapsearrows.com/" },
    url: "https://synapsearrows.com/ai-bae-shindan/",
    areaServed: ["JP", "SG"],
    availableLanguage: ["ja", "en"],
    hasOfferCatalog: {
      "@type": "OfferCatalog",
      name: lang === "ja" ? `AI映え診断の料金（${P.decided_on} 改定・税別・${P.scope_ja}）` : `AI映え診断 pricing (as of ${P.decided_on}; JPY, tax excluded, ${P.scope_en})`,
      itemListElement: [...FREE, ...PAID].map((id) => offer(id, lang)),
    },
  };
  return `<script type="application/ld+json">${JSON.stringify(node).replace(/</g, "\u003c")}</script>`;
};
const blocks = {
  ld_pricing_ja: ldScript("ja"),
  ld_pricing_en: ldScript("en"),
  llms_pricing:
    `- Pricing for AI映え診断 (decided ${P.decided_on}; JPY, tax excluded, ${P.scope_en}): Light check free with no sign-up; detailed check (four AIs, three fixed questions, once) free with email confirmation; ` +
    `fact-check report JPY ${num(P.plans.report.price_jpy)} one-off; fact-check report + one re-measurement after a month JPY ${num(P.plans.report_remeasure.price_jpy)} one-off; ` +
    `monthly monitoring JPY ${num(P.plans.monitor.price_jpy)}/month (${P.plans.monitor.min_months}-month minimum, one 30-minute online meeting a month); ` +
    `implementation retainer JPY ${num(P.plans.implement.price_jpy)}/month (${P.plans.implement.min_months}-month minimum). ${P.credit_rule_en} Several shops or a whole company: quote on request. ` +
    `Japanese: 照合レポート ${man(P.plans.report.price_jpy)}（単発）、照合レポート＋測り直し ${man(P.plans.report_remeasure.price_jpy)}（単発）、定点観測 月 ${man(P.plans.monitor.price_jpy)}（最低 ${P.plans.monitor.min_months} か月）、実装・伴走 月 ${man(P.plans.implement.price_jpy)}（最低 ${P.plans.implement.min_months} か月）。税別。`,
};

function value(key) {
  if (key.startsWith("block:")) {
    const b = blocks[key.slice(6)];
    if (b === undefined) throw new Error(`知らない block "${key}"`);
    return b;
  }
  if (key in scalars) return scalars[key];
  const m = key.match(/^([a-z_]+)\.([a-z_]+)$/);
  if (!m) throw new Error(`印の名前が読めない "${key}"`);
  return planValue(m[1], m[2]);
}

const RE = /<!--p:([a-z_:.]+)-->([\s\S]*?)<!--\/p-->/g;
const files = execFileSync("git", ["ls-files", "--", "*.html", "llms.txt"], { cwd: ROOT, encoding: "utf-8" }).split(/\r?\n/).filter(Boolean);
const check = process.argv.includes("--check");
let touched = 0, markers = 0, differs = 0;
for (const f of files) {
  const abs = path.join(ROOT, f);
  const src = readFileSync(abs, "utf-8");
  if (!RE.test(src)) continue;
  RE.lastIndex = 0;
  let n = 0;
  const out = src.replace(RE, (m, key) => { n++; return `<!--p:${key}-->${value(key)}<!--/p-->`; });
  markers += n;
  if (out !== src) {
    if (check) { console.error(`differs: ${f}`); differs++; }
    else { writeFileSync(abs, out); touched++; console.log(`wrote ${f} (${n})`); }
  }
}
if (check) {
  if (differs) { console.error(`${differs} file(s) differ from pricing.json`); process.exit(1); }
  console.log(`ok: ${markers} price marker(s) match pricing.json`);
} else {
  console.log(`done: ${touched} file(s) written, ${markers} marker(s)`);
}
