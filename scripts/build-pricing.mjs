#!/usr/bin/env node
/**
 * 値段を 1 か所（pricing.json）から全ページへ流し込む。
 *
 *   node scripts/build-pricing.mjs          # 書き換える
 *   node scripts/build-pricing.mjs --check  # ページが pricing.json と同じか（違えば exit 1）
 *
 * ページ側の印:  <!--p:KEY-->今の表示<!--/p-->
 *   KEY = <plan>.<form>   例: report.man → 5万円 ／ report.yen → 50,000円 ／ report.man_incl → 5.5万円
 *                          form: man（21万円〜）/ man_num（21〜）/ yen / jpy / raw / min_months / term_total_man / name_ja / name_en / label_ja / label_en（税込の *_incl は廃止）
 *                          renewal_ja / renewal_en（最低期間と、そのあとの決まり）・after_ja / after_en（そのあとの決まりだけ）・content_ja / content_en（オプションの中身）
 *                          p<月数>_<yen|jpy|man|off|off_en>  まとめ払い  例: monitor.p6_yen → 162,000円 ／ monitor.p12_off → 25%引き
 *   <plan> には pricing.json の options のキー（advice など）も使える
 *   KEY = tax_note_ja / tax_note_en / prepay_choose_ja / prepay_choose_en / prepay_tax_note_ja / prepay_tax_note_en / dashboard_note_ja / min_term_reason_ja / min_term_reason_en / scope_ja / scope_en / decided_on / decided_on_ja / sgd_note_en
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
const OPTIONS = P.options ?? {};
// まとめ払いの額は 月額×月数×(1−割引) と同じでなければ止める（JSON の打ち間違いを防ぐ）
for (const [id, plan] of [...Object.entries(P.plans), ...Object.entries(OPTIONS)]) {
  for (const b of plan.prepay ?? []) {
    const want = Math.round(plan.price_jpy * b.months * (1 - b.discount));
    if (want !== b.price_jpy) throw new Error(`pricing.json: ${id} の ${b.months} か月一括は ${want} 円のはず（今 ${b.price_jpy}）`);
  }
}
// オプションのまとめ払いは、付ける先のプランと同じ割引
for (const [id, o] of Object.entries(OPTIONS)) {
  const parent = P.plans[o.for_plan];
  if (!parent) throw new Error(`pricing.json: option ${id} の for_plan "${o.for_plan}" が無い`);
  const key = (l) => (l ?? []).map((b) => `${b.months}:${b.discount}`).join(",");
  if (key(o.prepay) !== key(parent.prepay)) throw new Error(`pricing.json: option ${id} のまとめ払いの割引が ${o.for_plan} と違う`);
}

const num = (n) => n.toLocaleString("en-US");
const incl = (n) => Math.round(n * (1 + TAX));
const man = (n) => {
  const m = n / 10000;
  return (Number.isInteger(m) ? String(m) : m.toFixed(1).replace(/\.0$/, "")) + "万円";
};
const from = (plan, ja = true) => (plan.starting_at ? (ja ? "〜" : "") : "");
const fromEn = (plan) => (plan.starting_at ? "from " : "");
const unitJa = (plan) => (plan.billing === "monthly" ? "／月" : "");
const unitEn = (plan) => (plan.billing === "monthly" ? "/month" : "");

const pct = (d) => `${Math.round(d * 100)}%`;
const termJa = (m) => (m === 12 ? "1 年" : `${m} か月`);
const termEn = (m) => (m === 12 ? "1 year" : `${m} months`);
const afterJa = (plan) => (plan.after_min_term === "monthly" ? "その後は 1 か月ごとに、続けるか止めるかを選べます。" : "");
const afterEn = (plan) => (plan.after_min_term === "monthly" ? "After that, you choose month by month whether to continue or stop." : "");
const renewalJa = (plan) => (plan.after_min_term === "monthly" ? `最低 ${plan.min_months} か月。${afterJa(plan)}` : "");
const renewalEn = (plan) => (plan.after_min_term === "monthly" ? `Minimum ${plan.min_months} months. ${afterEn(plan)}` : "");
function planValue(id, form) {
  const plan = P.plans[id] ?? OPTIONS[id];
  if (!plan) throw new Error(`pricing.json に plan "${id}" が無い`);
  const price = plan.price_jpy;
  const pm = form.match(/^p(\d+)_([a-z_]+)$/);
  if (pm) {
    const b = (plan.prepay ?? []).find((x) => x.months === Number(pm[1]));
    if (!b) throw new Error(`pricing.json: ${id} に ${pm[1]} か月のまとめ払いが無い（${id}.${form}）`);
    switch (pm[2]) {
      case "yen": return `${num(b.price_jpy)}円`;
      case "jpy": return `JPY ${num(b.price_jpy)}`;
      case "man": return man(b.price_jpy);
      case "off": return `${pct(b.discount)}引き`;
      case "off_en": return `${pct(b.discount)} off`;
      default: throw new Error(`知らない形 "${form}"（${id}.${form}）`);
    }
  }
  switch (form) {
    case "renewal_ja": return renewalJa(plan);
    case "renewal_en": return renewalEn(plan);
    case "after_ja": return afterJa(plan);
    case "after_en": return afterEn(plan);
    case "content_ja": return plan.content_ja;
    case "content_en": return plan.content_en;
    case "name_ja": return plan.name_ja;
    case "name_en": return plan.name_en;
    case "label_ja": return plan.price_label_ja ?? `${man(price)}${unitJa(plan)}`;
    case "label_en": return plan.price_label_en ?? `JPY ${num(price)}${unitEn(plan)}`;
    case "man": return man(price) + from(plan);
    case "man_num": return String(price / 10000) + from(plan);
    case "yen": return `${num(price)}円` + from(plan);
    case "jpy": return `${fromEn(plan)}JPY ${num(price)}`;
    case "raw": return String(price);
    case "min_months": return String(plan.min_months ?? "");
    case "term_total_man": return man(price * (plan.min_months || 1)) + from(plan);
    case "man_incl": case "yen_incl": case "jpy_incl": case "raw_incl":
      throw new Error(`税込の表示は出さない決まり（2026-10-27 夜）: ${id}.${form} の印を外す`);
    default: throw new Error(`知らない形 "${form}"（${id}.${form}）`);
  }
}

const scalars = {
  tax_note_ja: P.tax_note_ja,
  tax_note_en: P.tax_note_en,
  dashboard_note_ja: P.dashboard_note_ja,
  min_term_reason_ja: P.min_term_reason_ja,
  min_term_reason_en: P.min_term_reason_en,
  scope_ja: P.scope_ja,
  scope_en: P.scope_en,
  sgd_note_en: P.sgd_note_en,
  prepay_choose_ja: P.prepay_choose_ja,
  prepay_choose_en: P.prepay_choose_en,
  prepay_tax_note_ja: P.prepay_tax_note_ja,
  prepay_tax_note_en: P.prepay_tax_note_en,
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
      ...(plan.starting_at ? { minPrice: String(plan.price_jpy) } : { price: String(plan.price_jpy) }),
      priceCurrency: "JPY",
      valueAddedTaxIncluded: false,
      ...(plan.billing === "monthly" ? { unitText: lang === "ja" ? "月" : "month" } : {}),
    },
    ...(plan.min_months ? { eligibleDuration: { "@type": "QuantitativeValue", minValue: plan.min_months, unitCode: "MON" } } : {}),
    ...(plan.after_min_term ? { description: lang === "ja" ? renewalJa(plan) : renewalEn(plan) } : {}),
    itemOffered: { "@type": "Service", name, ...(plan.billing === "free" ? { url: "https://synapsearrows.com/ai-bae-shindan/" } : {}) },
  };
  return o;
};
// まとめ払い（一括）とオプション。親のプランと同じ形の Offer にする
const prepayOffers = (id, lang) => {
  const plan = P.plans[id] ?? OPTIONS[id];
  const base = lang === "ja" ? plan.name_ja : plan.name_en;
  return (plan.prepay ?? []).map((b) => {
    const name = lang === "ja" ? `${base}（${termJa(b.months)}一括・${pct(b.discount)}引き）` : `${base} (${termEn(b.months)} prepaid, ${pct(b.discount)} off)`;
    const note = b.note === "tax" ? (lang === "ja" ? P.prepay_tax_note_ja : P.prepay_tax_note_en) : "";
    return {
      "@type": "Offer",
      name,
      priceCurrency: "JPY",
      priceSpecification: { "@type": "UnitPriceSpecification", price: String(b.price_jpy), priceCurrency: "JPY", valueAddedTaxIncluded: false, referenceQuantity: { "@type": "QuantitativeValue", value: b.months, unitCode: "MON" } },
      eligibleDuration: { "@type": "QuantitativeValue", value: b.months, unitCode: "MON" },
      ...(note ? { description: note } : {}),
      itemOffered: { "@type": "Service", name: base },
    };
  });
};
const optionOffer = (id, lang) => {
  const o = OPTIONS[id];
  const parent = P.plans[o.for_plan];
  const name = lang === "ja" ? `${o.name_ja}（${parent.name_ja}のオプション）` : `${o.name_en} (for ${parent.name_en})`;
  return {
    "@type": "Offer",
    name,
    priceCurrency: "JPY",
    priceSpecification: { "@type": "UnitPriceSpecification", price: String(o.price_jpy), priceCurrency: "JPY", valueAddedTaxIncluded: false, unitText: lang === "ja" ? "月" : "month" },
    description: lang === "ja" ? o.content_ja : o.content_en,
    itemOffered: { "@type": "Service", name: lang === "ja" ? o.name_ja : o.name_en },
  };
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
      itemListElement: [
        ...[...FREE, ...PAID].map((id) => offer(id, lang)),
        ...PAID.flatMap((id) => prepayOffers(id, lang)),
        ...Object.keys(OPTIONS).flatMap((id) => [optionOffer(id, lang), ...prepayOffers(id, lang)]),
      ],
    },
  };
  return `<script type="application/ld+json">${JSON.stringify(node).replace(/</g, "\u003c")}</script>`;
};
const blocks = {
  ld_pricing_ja: ldScript("ja"),
  ld_pricing_en: ldScript("en"),
  llms_pricing:
    `- Pricing for AI映え診断 (set ${P.decided_on}; JPY, tax excluded, ${P.scope_en}; how consumption tax applies is confirmed at contract time): Light check free with no sign-up; detailed check (four AIs, three fixed questions, once) free with email confirmation; ` +
    `fact-check report JPY ${num(P.plans.report.price_jpy)} one-off; fact-check report + one re-measurement after a month JPY ${num(P.plans.report_remeasure.price_jpy)} one-off; ` +
    `monthly monitoring JPY ${num(P.plans.monitor.price_jpy)}/month (${P.plans.monitor.min_months}-month minimum; monthly report only, no meeting and no fixes; prepaid: ${P.plans.monitor.prepay.map((b) => `${termEn(b.months)} JPY ${num(b.price_jpy)} (${pct(b.discount)} off)`).join(", ")}); ` +
    `${OPTIONS.advice.name_en.toLowerCase()} for monitoring JPY ${num(OPTIONS.advice.price_jpy)}/month (${OPTIONS.advice.content_en}; same prepaid discounts: ${OPTIONS.advice.prepay.map((b) => `JPY ${num(b.price_jpy)} for ${termEn(b.months)}`).join(", ")}); ` +
    `implementation retainer from JPY ${num(P.plans.implement.price_jpy)}/month (${P.plans.implement.min_months}-month minimum; monitoring plus fixes done by us plus a monthly meeting; the price depends on scope; no prepayment discount). Monthly plans: after the minimum term, the client chooses month by month whether to continue or stop; a 3-month prepayment is not discounted. Several shops or a whole company: quote on request. A dashboard is planned, not yet available. ` +
    `Japanese: 照合レポート ${man(P.plans.report.price_jpy)}（単発）、照合レポート＋測り直し ${man(P.plans.report_remeasure.price_jpy)}（単発）、定点観測 月 ${man(P.plans.monitor.price_jpy)}（最低 ${P.plans.monitor.min_months} か月・レポートのみ・${P.plans.monitor.prepay.map((b) => `${termJa(b.months)}一括 ${num(b.price_jpy)}円（${pct(b.discount)}引き）`).join("・")}）、オプション「${OPTIONS.advice.name_ja}」月 ${man(OPTIONS.advice.price_jpy)}（まとめ払いは同じ割引）、実装・伴走 月 ${man(P.plans.implement.price_jpy)}〜（最低 ${P.plans.implement.min_months} か月・まとめ払いの割引なし）。月額プランは最低期間のあと 1 か月ごとに続けるか止めるかを選べる。税別。`,
};

function value(key) {
  if (key.startsWith("block:")) {
    const b = blocks[key.slice(6)];
    if (b === undefined) throw new Error(`知らない block "${key}"`);
    return b;
  }
  if (key in scalars) return scalars[key];
  const m = key.match(/^([a-z_]+)\.([a-z0-9_]+)$/);
  if (!m) throw new Error(`印の名前が読めない "${key}"`);
  return planValue(m[1], m[2]);
}

const RE = /<!--p:([a-z0-9_:.]+)-->([\s\S]*?)<!--\/p-->/g;
const files = execFileSync("git", ["ls-files", "--cached", "--others", "--exclude-standard", "--", "*.html", "llms.txt"], { cwd: ROOT, encoding: "utf-8" }).split(/\r?\n/).filter(Boolean);
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
