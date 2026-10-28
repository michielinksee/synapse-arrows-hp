# -*- coding: utf-8 -*-
"""日本語の主なページを 1 つの型から作る（Codex の試作 2026-10-27 を静的 HTML に移した物・PR #5）。

  python scripts/build-site.py          # 作る
  python scripts/build-site.py --check  # 作った物と手元のファイルが同じか（違えば exit 1・CI で使う）

作る物: index.html, services/ (+5 詳細), products/, tools/, about/, contact/ (+confirm/), ai-bae-shindan/pricing/, /flow/,
insights/ (+3 テーマ), 英語の /en/ 一式（文言は scripts/site/en.json・policy とシンガポールの記事は本文をそのまま外枠だけ）, site.js, site-chrome.css（site.css から共通部分だけを抜いた物。AI映え診断の本物の入力画面が使う）。
値段は <!--p:KEY--> の印のまま書き、scripts/build-pricing.mjs が pricing.json から流し込む（--check は印の中身を見ない）。
文章・一覧はこのファイルと scripts/site/*.json（JSON-LD の元・Insights の記事一覧・相談フォームの送り先 contact.json）。AI映え診断の本体（ai-bae-shindan/index.html と業種別）は
scripts/build-ai-bae-pages.mjs の受け持ち。業種別ページの一覧は scripts/ai-bae/pages.json から読む（足せばリンクも増える）。
標準ライブラリだけで動く（CI の python3 でそのまま走る）。"""
import io, json, re, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace("\\", "/") + "/"
SITE = "https://synapsearrows.com"
CHECK = "--check" in sys.argv
OUT = {}
def wr(p, s):
    OUT[p] = s
    if CHECK: return
    os.makedirs(os.path.dirname(ROOT + p), exist_ok=True)
    io.open(ROOT + p, "w", encoding="utf-8", newline="\n").write(s)
def rd(p): return io.open(ROOT + p, encoding="utf-8").read()
EN = json.load(io.open(ROOT + "scripts/site/en.json", encoding="utf-8"))  # 英語の文言（/en/）
def P(k, d): return f"<!--p:{k}-->{d}<!--/p-->"
def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
def ldjson(o): return '<script type="application/ld+json">' + json.dumps(o, ensure_ascii=False).replace("</", "<\\/") + "</script>"

# ---------------------------------------------------------------- icons (Phosphor shapes redrawn as plain SVG)
CARET = '<svg viewBox="0 0 256 256" fill="currentColor" aria-hidden="true"><path d="M181.66 133.66l-80 80a8 8 0 0 1-11.32-11.32L164.69 128 90.34 53.66a8 8 0 0 1 11.32-11.32l80 80a8 8 0 0 1 0 11.32z"/></svg>'
CARET_BOLD = '<svg viewBox="0 0 256 256" fill="currentColor" aria-hidden="true"><path d="M184.49 136.49l-80 80a12 12 0 0 1-17-17L159 128 87.51 56.49a12 12 0 1 1 17-17l80 80a12 12 0 0 1 0 17z"/></svg>'
UPRIGHT = '<svg viewBox="0 0 256 256" fill="currentColor" aria-hidden="true"><path d="M200 64v104a8 8 0 0 1-16 0V83.31L69.66 197.66a8 8 0 0 1-11.32-11.32L172.69 72H88a8 8 0 0 1 0-16h104a8 8 0 0 1 8 8z"/></svg>'
ARROW_R = '<svg viewBox="0 0 256 256" fill="currentColor" aria-hidden="true"><path d="M221.66 133.66l-72 72a8 8 0 0 1-11.32-11.32L196.69 136H40a8 8 0 0 1 0-16h156.69l-58.35-58.34a8 8 0 0 1 11.32-11.32l72 72a8 8 0 0 1 0 11.32z"/></svg>'
LIST_I = '<svg viewBox="0 0 256 256" fill="currentColor" aria-hidden="true"><path d="M224 128a8 8 0 0 1-8 8H40a8 8 0 0 1 0-16h176a8 8 0 0 1 8 8zM40 72h176a8 8 0 0 0 0-16H40a8 8 0 0 0 0 16zm176 112H40a8 8 0 0 0 0 16h176a8 8 0 0 0 0-16z"/></svg>'
CHECK_C = '<svg viewBox="0 0 256 256" fill="currentColor" aria-hidden="true"><path d="M173.66 98.34a8 8 0 0 1 0 11.32l-56 56a8 8 0 0 1-11.32 0l-24-24a8 8 0 0 1 11.32-11.32L112 148.69l50.34-50.35a8 8 0 0 1 11.32 0zM232 128A104 104 0 1 1 128 24a104.11 104.11 0 0 1 104 104zm-16 0a88 88 0 1 0-88 88 88.1 88.1 0 0 0 88-88z"/></svg>'
WARN_C = '<svg viewBox="0 0 256 256" fill="currentColor" aria-hidden="true"><path d="M128 24a104 104 0 1 0 104 104A104.11 104.11 0 0 0 128 24zm0 192a88 88 0 1 1 88-88 88.1 88.1 0 0 1-88 88zm-8-80V80a8 8 0 0 1 16 0v56a8 8 0 0 1-16 0zm20 36a12 12 0 1 1-12-12 12 12 0 0 1 12 12z"/></svg>'
SEARCH_I = '<svg viewBox="0 0 256 256" fill="currentColor" aria-hidden="true"><path d="M229.66 218.34l-50.07-50.06a88.11 88.11 0 1 0-11.31 11.31l50.06 50.07a8 8 0 0 0 11.32-11.32zM40 112a72 72 0 1 1 72 72 72.08 72.08 0 0 1-72-72z"/></svg>'
PLAY_C = '<svg viewBox="0 0 256 256" fill="currentColor" aria-hidden="true"><path opacity=".2" d="M224 128a96 96 0 1 1-96-96 96 96 0 0 1 96 96z"/><path d="M128 24a104 104 0 1 0 104 104A104.11 104.11 0 0 0 128 24zm0 192a88 88 0 1 1 88-88 88.1 88.1 0 0 1-88 88zm36.44-94.66l-48-32A8 8 0 0 0 104 96v64a8 8 0 0 0 12.44 6.66l48-32a8 8 0 0 0 0-13.32zM120 145.05V111l25.58 17z"/></svg>'

# ---------------------------------------------------------------- shared chrome
def head(title, desc, path, ld=None, og_image="/og-image.png", extra_css="", noindex=False, lang="ja"):
    url = SITE + path
    ld = ld or []
    pair = alts(path)
    alt = "" if (noindex or not pair) else "".join(f'\n    <link rel="alternate" hreflang="{k}" href="{SITE}{v}">' for k, v in (("ja", pair["ja"]), ("en", pair["en"]), ("x-default", pair["ja"])))
    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{esc(title)}</title>
    <meta name="description" content="{esc(desc)}">
    <link rel="canonical" href="{url}">{alt}
    {'<meta name="robots" content="noindex, follow">' if noindex else ''}
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="Synapse Arrows">
    <meta property="og:title" content="{esc(title)}">
    <meta property="og:description" content="{esc(desc)}">
    <meta property="og:url" content="{url}">
    <meta property="og:image" content="{SITE}{og_image}">
    <meta property="og:locale" content="{"en_US" if lang == "en" else "ja_JP"}">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:site" content="@michielinksee">
    <meta name="twitter:title" content="{esc(title)}">
    <meta name="twitter:description" content="{esc(desc)}">
    <meta name="twitter:image" content="{SITE}{og_image}">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400..900&display=swap" rel="stylesheet">
    <link rel="icon" href="/favicon.png" type="image/png">
    <link rel="manifest" href="/site.webmanifest">
    <link rel="stylesheet" href="/site.css">
{extra_css}    {''.join(ldjson(o) for o in ld)}
    <script>window.va=window.va||function(){{(window.vaq=window.vaq||[]).push(arguments)}};</script>
    <script defer src="/_vercel/insights/script.js"></script>
    <script defer src="/site.js"></script>
</head>
<body>
'''

# 日本語と英語の対（hreflang・言語の切り替え）。片方しか無いページは、切り替えで相手の言語のトップへ
PAIRS = [("/", "/en/"), ("/services/", "/en/services/")] + [(f"/services/{x}/", f"/en/services/{x}/") for x in ("overseas-expansion", "overseas-advisory", "new-business", "ai-training", "ai-agents")] + [
    ("/products/", "/en/products/"), ("/about/", "/en/about/"), ("/contact/", "/en/contact/"), ("/contact/confirm/", "/en/contact/confirm/"), ("/insights/", "/en/insights/"), ("/policy/", "/en/policy-2/"), ("/services/ai-aeo/", "/en/services/ai-aeo/")]
EN_OF = dict(PAIRS); JA_OF = {e: j for j, e in PAIRS}
def alts(path):
    if path in EN_OF: return {"ja": path, "en": EN_OF[path]}
    if path in JA_OF: return {"ja": JA_OF[path], "en": path}
    return None
def other_lang(path, lang): return JA_OF.get(path, "/") if lang == "en" else EN_OF.get(path, "/en/")

NAV = [("/services/", "事業紹介", "services"), ("/services/", "サービス", "services2"), ("/products/", "プロダクト", "products"), ("/insights/", "Insights", "insights"), ("/about/", "会社概要", "about")]
MOBILE = [("/services/", "事業紹介・サービス"), ("/products/", "プロダクト"), ("/tools/", "無料ツール"), ("/ai-bae-shindan/", "AI映え診断"), ("/insights/", "Insights・記事"), ("/about/", "会社概要"), ("/contact/", "資料請求・ご相談")]
def header(current="", path="/", lang="ja"):
    sw = other_lang(path, lang)
    if lang == "en":
        t = EN["nav"]; nav = [("/en/services/", t["services"], "services"), ("/en/products/", t["products"], "products"), ("/en/insights/", t["insights"], "insights"), ("/en/about/", t["about"], "about")]
        mobile = EN["mobile"]; home, cta, cta_l = "/en/", "/en/contact/", t["cta"]
        lk = f'<a class="lang-link" href="{sw}" lang="ja" hreflang="ja">{t["lang_switch"]}</a>'
        lkm = lk.replace('class="lang-link"', 'class="lang-link-mobile"')
        lab = dict(skip=t["skip"], home=t["home_label"], main=t["main_nav"], open=t["menu_open"], mob=t["mobile_nav"])
    else:
        nav = NAV; mobile = MOBILE; home, cta, cta_l = "/", "/contact/", "資料請求・ご相談"
        lk = f'<a class="lang-link" href="{sw}" lang="en" hreflang="en">EN</a>'
        lkm = f'<a class="lang-link-mobile" href="{sw}" lang="en" hreflang="en">English</a>'
        lab = dict(skip="本文へスキップ", home="Synapse Arrows トップへ", main="メインナビゲーション", open="メニューを開く", mob="モバイルナビゲーション")
    links = "".join(f'<a href="{h}"{" aria-current=\"page\"" if k.rstrip("2") == current else ""}>{l}</a>' for h, l, k in nav) + lk
    mob = "".join(f'<a href="{h}">{l}</a>' for h, l in mobile) + lkm
    return f"""<a href="#main" class="skip-link">{lab["skip"]}</a>
<header class="site-header" id="top"><div class="container header-inner"><a class="brand" href="{home}" aria-label="{lab["home"]}"><img src="/assets/company-logo.png" alt="" width="48" height="48"><span>Synapse Arrows</span></a><nav class="desktop-nav" aria-label="{lab["main"]}">{links}</nav><a class="button header-cta" href="{cta}" data-va="download_click" data-va-from="header">{cta_l} {CARET_BOLD}</a><button class="menu-toggle" type="button" aria-label="{lab["open"]}" aria-expanded="false" aria-controls="mobile-menu">{LIST_I}</button></div><nav class="mobile-nav" id="mobile-menu" aria-label="{lab["mob"]}" hidden>{mob}</nav></header>
"""
def footer(path="/", lang="ja"):
    sw = other_lang(path, lang)
    if lang == "en":
        links = "".join(f'<a href="{h}">{l}</a>' for h, l in EN["footer"]) + f'<a href="{sw}" lang="ja" hreflang="ja">{EN["nav"]["lang_switch"]}</a>'
        home, lab_home, lab_nav = "/en/", EN["nav"]["home_label"], EN["nav"]["footer_nav"]
    else:
        links = f'<a href="/insights/">Insights・記事</a><a href="/about/">会社概要</a><a href="/contact/">お問い合わせ</a><a href="/policy/">プライバシーポリシー</a><a href="/terms/">利用規約</a><a href="{sw}" lang="en" hreflang="en">English</a>'
        home, lab_home, lab_nav = "/", "Synapse Arrows トップへ", "フッターナビゲーション"
    return f"""<footer class="footer"><div class="container footer-inner"><a class="brand brand-footer" href="{home}" aria-label="{lab_home}"><img src="/assets/company-logo.png" alt="" width="37" height="37"><span>Synapse Arrows</span></a><nav aria-label="{lab_nav}">{links}</nav></div></footer>
</body>
</html>
"""
def eyebrow(t): return f'<p class="eyebrow"><span aria-hidden="true"></span>{t}</p>'
def btn(href, label, secondary=False, outline=False, attrs=""): return f'<a href="{href}" class="button{" secondary" if secondary else ""}{" button-outline" if outline else ""}" {attrs}>{label} {CARET_BOLD}</a>'
def tlink(href, label, attrs=""): return f'<a href="{href}" class="text-link" {attrs}>{label} {CARET_BOLD}</a>'
def xlink(href, label, cls="text-link"): return f'<a href="{href}" class="{cls}" target="_blank" rel="noopener">{label} {UPRIGHT}</a>'
def crumb(label, parent=None, lang="ja"):
    p = f'<a href="{parent[0]}">{parent[1]}</a>{CARET}' if parent else ""
    home, aria, top = (EN["nav"]["home"], EN["nav"]["breadcrumb"], "/en/") if lang == "en" else ("ホーム", "パンくず", "/")
    return f'<nav class="breadcrumb container" aria-label="{aria}"><a href="{top}">{home}</a>{CARET}{p}<span aria-current="page">{label}</span></nav>'
def intro(eye, title, copy="", photo=None):
    img = f'<img src="/assets/{photo}" alt="" width="1852" height="849" loading="eager">' if photo else ""
    return f'<section class="page-intro-new{" with-photo" if photo else ""}"><div class="container intro-layout"><div>{eyebrow(eye)}<h1 tabindex="-1">{title}</h1>{f"<p class=\"intro-copy\">{copy}</p>" if copy else ""}</div>{img}</div></section>'
def req_url(service="", plan="", intent="資料請求"):
    from urllib.parse import urlencode
    q = {}
    if service: q["service"] = service
    if plan: q["plan"] = plan
    q["intent"] = intent
    return "/contact/?" + urlencode(q)
def next_band(title="社内で検討するための資料を。", copy="サービス内容・パッケージ・進め方を、まとめて確認できます。", service="AI映え診断"):
    return f'<section class="next-band-new"><div>{eyebrow("NEXT STEP")}<h2>{title}</h2><p>{copy}</p></div>{btn(req_url(service), "資料請求・ご相談", attrs=f"data-va=\"download_click\" data-va-from=\"next_band\"")}</section>'
def product_feature(light=False):
    h = "まずは無料で、サイトの下地を確認。" if light else "AIに伝わる情報を、事業の力に。"
    p = "URLと業種から、サイトの読み取りやすさや情報の手がかりをチェックします。" if light else f"{AIB_S1}</p><p>{AIB_S2}"
    a1 = btn("/ai-bae-shindan/", "無料診断 Light を試す" if light else "AI映え診断を詳しく見る", attrs='data-va="ai_bae_start" data-va-from="feature"')
    a2 = tlink("/ai-bae-shindan/", "サービス全体を知る") if light else tlink("/ai-bae-shindan/pricing/", "料金・パッケージ")
    note = '<p class="small-note">LightはAIに質問しません。実際の回答や推薦状況は計測しません。</p>' if light else ""
    return f'<section class="product-feature-new"><div>{eyebrow("FREE TOOL" if light else "FEATURED SERVICE")}<img class="feature-logo" src="/assets/diagnosis-logo.webp" alt="AI映え診断 by Synapse Arrows" width="1000" height="270" loading="lazy"><h2>{h}</h2><p>{p}</p><div class="page-actions">{a1}{a2}</div>{industry_links("feature_light" if light else "feature")}</div><div class="feature-characters"><img src="/assets/characters.webp" alt="AI映え診断の4キャラクター" width="640" height="344" loading="lazy">{note}</div></section>'
def page(path, title, desc, current, label, body, parent=None, ld=None, extra_css="", diagnosis_nav=False, og_image="/og-image.png", noindex=False, lang="ja", after_main=""):
    dn = diag_nav(path) if diagnosis_nav else ""
    html = head(title, desc, path, ld, og_image, extra_css, noindex, lang) + header(current, path, lang) + dn + f'<main id="main" class="inner-page">{crumb(label, parent, lang)}{body}</main>\n' + after_main + footer(path, lang)
    wr(path.lstrip("/") + "index.html", html)
    return path
def diag_nav(path):
    items = [("/ai-bae-shindan/", "サービス内容"), ("/ai-bae-shindan/pricing/", "料金・パッケージ"), ("/ai-bae-shindan/flow/", "ご利用の流れ"), ("/ai-bae-shindan/#check", "無料診断 Light")]
    return '<nav class="diagnosis-nav" aria-label="AI映え診断ナビゲーション"><div class="container"><a href="/ai-bae-shindan/" class="diagnosis-nav-brand">AI映え診断</a>' + "".join(f'<a href="{h}"{" aria-current=\"page\"" if h == path else ""}>{l}</a>' for h, l in items) + "</div></nav>"
def breadcrumb_ld(*items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + u} for i, (n, u) in enumerate(items)]}
def webpage_ld(path, name, desc, lang="ja"):
    return {"@context": "https://schema.org", "@type": "WebPage", "@id": SITE + path + "#page", "url": SITE + path, "name": name, "description": desc, "inLanguage": lang, "isPartOf": {"@id": SITE + "/#website"}, "publisher": {"@id": SITE + "/#organization"}}
def faq_ld(pairs): return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in pairs]}

# ---------------------------------------------------------------- data
SERVICES = [
 {"slug": "overseas-expansion", "name": "海外進出支援", "copy": "市場調査から進出計画、\n現地での展開まで。", "image": "singapore.webp", "alt": "", "detail": "海外市場への進出に向けて、事業の可能性と課題を整理。市場調査、進出計画、現地での展開まで、段階に合わせて支援します。", "points": ["市場・競合の調査", "進出計画の策定", "現地展開に向けた実行支援"]},
 {"slug": "overseas-advisory", "name": "海外進出アドバイザリー", "copy": "海外事業の判断と推進に、\n継続して伴走。", "image": "advisory.webp", "alt": "", "detail": "海外事業を進めるなかで生まれる課題や意思決定に、継続して伴走。状況を整理し、次のアクションをともに考えます。", "points": ["事業課題・論点の整理", "進出・展開方針の検討", "継続的な相談・助言"]},
 {"slug": "new-business", "name": "新規事業開発支援", "copy": "事業構想から検証、\n立ち上げまで。", "image": "new-business.webp", "alt": "", "detail": "新しい事業の構想を、検証できる計画へ。顧客や市場の理解を深めながら、仮説検証から立ち上げまで支援します。", "points": ["事業構想・仮説の整理", "顧客・市場の検証", "立ち上げに向けた実行支援"]},
 {"slug": "ai-bae-shindan", "name": "AI映え診断", "detail": "AI検索で、自社はどう伝わっているのか。AEOの視点から、情報発信の課題と改善の方向性を整理します。"},
 {"slug": "ai-training", "name": "AI研修・導入支援", "detail": "事業や業務の課題に合わせて、AI活用の学びと導入を支援します。対象業務や組織の状況から、ともに検討します。"},
 {"slug": "ai-agents", "name": "AIエージェント開発支援", "detail": "業務の目的や運用環境に合わせて、AIエージェントの活用方法と開発の進め方を検討します。"},
]
AIB_S1 = "お客さんがお店やサービスを探す道に、検索や地図に加えて、ChatGPT などの AI が加わりました。"
AIB_S2 = "お店や会社のサイトの URL を入れるだけで、ChatGPT・Gemini・Claude・Perplexity の 4 つの AI がサイトを読めているか、その場で分かります。"
_Q1 = {o["id"]: o["label"] for o in json.load(io.open(ROOT + "ai-bae-shindan/survey.json", encoding="utf-8"))["questions"]["q1"]["options"]}
INDUSTRY_PAGES = [(p["url"].replace(SITE, ""), p.get("nav_label") or (_Q1.get(p["industry"], p["industry"]) + "向け"))
                  for p in json.load(io.open(ROOT + "scripts/ai-bae/pages.json", encoding="utf-8"))["pages"] if p.get("industry")]
def industry_links(frm):
    """業種別の診断（Light）への入口。scripts/ai-bae/pages.json に業種のページを足すと、ここにも並ぶ。"""
    if not INDUSTRY_PAGES: return ""
    return '<p class="industry-links">業種別の診断: ' + "・".join(f'<a href="{u}" data-va="ai_bae_start" data-va-from="{frm}_industry">{l} {CARET_BOLD}</a>' for u, l in INDUSTRY_PAGES) + "</p>"
def svc_href(s): return "/ai-bae-shindan/" if s["slug"] == "ai-bae-shindan" else f"/services/{s['slug']}/"
PLANS = [
 {"id": "report", "label": "まず、課題を知りたい", "title": "照合レポート", "description": "AIの説明のどこが違い、何を直すべきかを整理します。", "delivery": "回答と公式情報の照合レポート・優先順位付き修正リスト", "frequency": "1回", "fix": "お客様・制作会社で対応", "features": ["20〜30問 × 4つのAI × 3回を調査", "調査範囲内の誤り・引用元を整理", "修正の優先順位を提示"], "after": "レポートを受け取り、自社や制作会社で修正。継続契約は必須ではありません。", "meeting": "標準内容に含みません", "monthly": False},
 {"id": "report_remeasure", "label": "修正後の変化も知りたい", "title": "照合＋測り直し", "description": "照合レポートに、1か月後の再測定を追加します。", "delivery": "照合レポート・優先順位付き修正リスト・再測定の比較結果", "frequency": "初回＋1か月後に1回", "fix": "お客様・制作会社で対応", "features": ["照合レポートの全内容", "お客様側で情報を修正", "1か月後に同条件で測り直し"], "after": "初回レポートをもとにお客様側で修正。1か月後に再測定し、回答の変化を比較します。", "meeting": "標準内容に含みません", "monthly": False},
 {"id": "monitor", "label": "変化を毎月把握したい", "title": "定点観測", "description": "同じ条件でAIの回答を追い、月次レポートで変化を確認します。", "delivery": "毎月の測定結果・前回からの変化をまとめたレポート", "frequency": "毎月", "fix": "お客様・制作会社で対応", "features": ["毎月の測定・レポート提供", "オンライン面談は含みません", "情報の修正・実装作業は含みません"], "after": "毎月レポートをお届けします。内容を確認し、必要な修正はお客様側で行います。", "meeting": "含みません", "monthly": True},
 {"id": "implement", "label": "改善の実行も任せたい", "title": "実装・伴走", "description": "定点観測に加え、改善の優先順位づけから合意した範囲の修正まで支援します。", "delivery": "月次レポート・改善計画・合意範囲の修正内容", "frequency": "毎月の観測＋改善支援", "fix": "Synapse Arrowsが合意範囲を支援", "features": ["定点観測の内容を含みます", "掲載情報・文章・構造化データの修正支援", "月1回の面談。作業範囲・件数に応じてお見積もり"], "after": "優先順位と作業範囲を合意し、修正・実装を進めます。月次の観測で変化を確認し、次の改善につなげます。", "meeting": "月1回。実施内容は見積もり時に合意", "monthly": True},
]
PRICE_LABEL = {"report": P("report.man", "5万円"), "report_remeasure": P("report_remeasure.man", "8万円"), "monitor": "月" + P("monitor.man", "3万円"), "implement": "月" + P("implement.man", "21万円〜")}
MIN = P("monitor.min_months", "6")
DASH = P("dashboard_note_ja", "ダッシュボードでの閲覧・管理機能は今後提供予定です。現在はご利用いただけません。")
TAX = P("tax_note_ja", "料金はすべて税別です。消費税の扱いはご契約の時にご案内します。")
AFTER_JA = P("monitor.after_ja", "その後は 1 か月ごとに、続けるか止めるかを選べます。")
ADV_JA = {"name": P("advice.name_ja", "アドバイスあり"), "man": P("advice.man", "2万円"), "content": P("advice.content_ja", "")}
# まとめ払いの表（定点観測とオプション）。行＝払い方、列＝プラン。値段は印のまま
PREPAY_CSS = '    <style>.diagnosis-comparison.prepay-table{min-width:0;max-width:820px;table-layout:auto}.prepay-table th:first-child{width:38%}.prepay-table td{font-size:16px;font-weight:650;white-space:nowrap}.prepay-table td.prepay-tax{white-space:normal}.prepay-scroll{margin-top:22px}.prepay-table sup{font-size:11px;margin-left:2px}.prepay-table td.prepay-tax{font-size:12px;line-height:1.7;font-weight:400;color:#52637d;padding:10px 16px;background:#fff}.plan .term-total a{color:var(--blue);text-decoration:underline;text-underline-offset:3px}@media(max-width:600px){.prepay-table th,.prepay-table td{padding:12px 10px}.prepay-table td{font-size:14px}}</style>\n'
def prepay_table(caption, cols, rows, tax_note, lang="ja"):
    ja = lang == "ja"
    def cell(pid, m):
        if m == 0: return f'月 {P(pid + ".man", "")}' if ja else f'{P(pid + ".jpy", "")}/month'
        return P(f"{pid}.p{m}_yen" if ja else f"{pid}.p{m}_jpy", "")
    head = "".join(f'<th scope="col">{c}</th>' for c in cols)
    body = ""
    for (label, m) in rows:
        off = f'<span>{P(f"monitor.p{m}_off" if ja else f"monitor.p{m}_off_en", "")}</span>' if m else ""
        mark = "<sup>※</sup>" if m == 12 else ""
        body += f'<tr><th scope="row">{label}{mark}{off}</th><td>{cell("monitor", m)}</td><td>{cell("advice", m)}</td></tr>'
    # 1 年一括の注記（※）は表の最後の行に小さく。狭い画面で 1 列に詰まらないように 3 列をまたぐ
    foot = f'<tfoot><tr><td colspan="3" class="prepay-tax">※{tax_note}</td></tr></tfoot>'
    return f'<div class="comparison-scroll prepay-scroll" tabindex="0" role="region" aria-label="{caption}"><table class="diagnosis-comparison prepay-table"><caption>{caption}</caption><thead><tr>{head}</tr></thead><tbody>{body}</tbody>{foot}</table></div>'
ORG_MIN = {"@context": "https://schema.org", "@type": "Organization", "@id": SITE + "/#organization", "name": "Synapse Arrows Pte. Ltd.", "url": SITE + "/", "logo": SITE + "/assets/company-logo.png"}

# ================================================================= TOP
def build_top():
    keep = json.load(io.open(ROOT + "scripts/site/ld-top.json", encoding="utf-8"))  # Organization / Person / WebSite（元は旧トップの JSON-LD）
    assert any(o["@type"] == "Organization" for o in keep)
    org = next(o for o in keep if o["@type"] == "Organization")
    org["slogan"] = "AI 時代の判断力を、デザインする。"
    org["description"] = "シンガポールと東京を拠点に、AI が自社をどう説明しているかを測り、海外進出・新規事業・AI 活用の判断と実行を支えるコンサルティング会社。海外進出支援・海外進出アドバイザリー・新規事業開発支援・AI映え診断・AI研修・導入支援・AIエージェント開発支援。AI エージェント向けの第三者の計器 KanseiLINK と、記憶 MCP サーバー Linksee Memory を運営。"
    org["logo"] = SITE + "/assets/company-logo.png"
    org["knowsAbout"] = ["Southeast Asia Market Entry", "New Business Development", "AI Visibility", "AI Engine Optimization", "AEO", "LLMO", "Corporate AI Training", "AI Agent Development", "Model Context Protocol", "MCP"]
    org["makesOffer"] = [{"@type": "Offer", "itemOffered": {"@type": "Service", "name": s["name"], "url": SITE + svc_href(s)}} for s in SERVICES]
    svc_cards = ""
    for i, s in enumerate(SERVICES[:3]):
        svc_cards += f'<a class="service-item" href="/services/{s["slug"]}/"><span class="service-number">0{i+1}<span></span></span><h3>{s["name"]}</h3><p>{s["copy"]}</p><div class="service-photo"><img src="/assets/{s["image"]}" alt="" width="600" height="275" loading="lazy"><span class="photo-arrow">{CARET_BOLD}</span></div></a>'
    checks = "".join(f'<label class="service-checkbox"><input type="checkbox" name="service" value="{s["name"]}"><span>{s["name"]}</span></label>' for s in SERVICES)
    TITLE = "Synapse Arrows | AI 時代の判断力を、デザインする。"
    DESC = "AI が自社をどう説明しているかを測り、海外進出・新規事業・AI 活用の判断と実行を支えます。海外進出支援・海外進出アドバイザリー・新規事業開発支援・AI映え診断・AI研修・導入支援・AIエージェント開発支援。Synapse Arrows Pte. Ltd.（シンガポール・東京）。"
    extra = '    <link rel="preload" as="image" href="/assets/hero.webp" fetchpriority="high">\n    <style>.service-item{display:block;color:inherit}.service-item h3{margin:8px 0 0}.request-action .button[aria-disabled=true]{opacity:.55;cursor:not-allowed}</style>\n'
    body = f'''{header("", "/")}<main id="main">
      <section class="hero" aria-labelledby="hero-title"><img class="hero-image" src="/assets/hero.webp" alt="" width="1920" height="819" fetchpriority="high"><div class="hero-shade"></div>
        <div class="container hero-inner"><p class="location"><span aria-hidden="true"></span>Singapore / Tokyo</p><h1 id="hero-title">AI 時代の判断力を、<br>デザインする。</h1><p class="hero-subtitle"><span>AI が自社をどう説明しているかを測り、</span><wbr><span>海外進出・新規事業・AI 活用の判断と実行を支えます。</span></p><p class="hero-copy">Synapse Arrowsは、事業の次の一歩を、<br class="desktop-break">ともに考え、ともにつくるコンサルティングパートナーです。</p><div class="hero-actions"><a href="/ai-bae-shindan/" class="button" data-va="ai_bae_start" data-va-from="hero">無料の AI映え診断を試す {CARET_BOLD}</a><a href="/contact/" class="button button-outline" data-va="download_click" data-va-from="hero">資料請求・ご相談 {CARET_BOLD}</a></div></div>
      </section>
      <section class="services section" id="services" aria-labelledby="services-title"><div class="container">{eyebrow("OUR SERVICES")}<h2 id="services-title"><span>事業の可能性を、</span><wbr><span>実行につなぐ。</span></h2><p class="section-intro">海外での成長と新たな事業の創出に向けて、戦略立案から実行まで一気通貫で支援します。</p><div class="service-grid">{svc_cards}</div></div></section>
      <section class="product section" id="product" aria-labelledby="product-title"><div class="container">{eyebrow("PRODUCT &amp; SERVICE")}<div class="product-grid"><div class="product-copy"><h2 id="product-title">事業成長の支援から生まれた、<br>AI映え診断。</h2><img class="diagnosis-logo" src="/assets/diagnosis-logo.webp" alt="AI映え診断 by Synapse Arrows" width="1000" height="270" loading="lazy"><p>{AIB_S1}</p><p>{AIB_S2}</p></div><img class="characters" src="/assets/characters.webp" alt="コーヒーを持つAI映え診断の4人のキャラクター" width="640" height="344" loading="lazy"></div><div class="product-actions"><a class="button" href="/ai-bae-shindan/" data-va="ai_bae_start" data-va-from="product">AI映え診断を詳しく見る {CARET_BOLD}</a><a class="text-link" href="/ai-bae-shindan/">サービス内容 {CARET_BOLD}</a><a class="text-link" href="/ai-bae-shindan/pricing/">料金・パッケージ {CARET_BOLD}</a><a class="text-link" href="/ai-bae-shindan/flow/">導入の流れ {CARET_BOLD}</a></div>{industry_links("product")}<div class="related"><span>関連サービス</span><a href="/services/ai-training/">AI研修・導入支援</a><span class="slash" aria-hidden="true">／</span><a href="/services/ai-agents/">AIエージェント開発支援</a></div></div></section>
      <section class="request section" id="request" aria-labelledby="request-title"><div class="container">{eyebrow("DOWNLOAD")}<h2 id="request-title"><span>必要なサービスの資料を、</span><wbr><span>まとめて。</span></h2><form id="request-form" action="/contact/" method="get"><fieldset><legend>関心のあるサービスをお選びください（複数選択可）</legend><div class="selection-grid">{checks}</div></fieldset><input type="hidden" name="intent" value="資料請求"><p class="form-error" id="request-error" role="alert" hidden>資料をご希望のサービスを1つ以上お選びください。</p><div class="request-action"><button class="button" type="submit" data-va="download_click" data-va-from="top_request">選んだサービスの資料を請求する {CARET_BOLD}</button><span class="selection-count" id="selection-count" aria-live="polite"></span></div></form></div></section>
    </main>
'''
    html = head(TITLE, DESC, "/", keep, extra_css=extra) + body + footer("/")
    wr("index.html", html)

# ================================================================= SERVICES
def service_columns(items):
    out = '<div class="consulting-columns">'
    for s in items:
        i = SERVICES.index(s); h = svc_href(s)
        img = f'<a href="{h}"><img src="/assets/{s["image"]}" alt="" width="1852" height="849" loading="lazy"></a>' if s.get("image") else ""
        out += f'<article><span class="column-number">0{i+1}</span><h3><a href="{h}">{s["name"]}</a></h3><p>{s.get("copy") or s["detail"]}</p>{img}{tlink(h, "サービス内容を見る")}</article>'
    return out + "</div>"
def build_services():
    body = intro("CONSULTING SERVICES", "事業の課題から、<br>必要な支援を選ぶ。", "海外進出・新規事業開発から、情報発信とAI活用まで。事業の段階に合わせて、必要な支援をご提案します。") + f'''<div class="container page-content">{product_feature()}<section class="page-section">{eyebrow("BUSINESS CONSULTING")}<h2>次の市場へ。次の事業へ。</h2>{service_columns(SERVICES[:3])}</section><section class="page-section">{eyebrow("AI &amp; OPERATIONS")}<h2>組織と業務に、実践的なAI活用を。</h2>{service_columns(SERVICES[4:])}</section>{next_band("必要な支援を、一緒に整理しませんか？", "6つのサービスから、関心のある資料をまとめてお選びいただけます。", "")}</div>'''
    ld = [webpage_ld("/services/", "サービス一覧", "海外進出・新規事業開発から、情報発信とAI活用まで。"), breadcrumb_ld(("ホーム", "/"), ("サービス一覧", "/services/")),
          {"@context": "https://schema.org", "@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": s["name"], "url": SITE + svc_href(s)} for i, s in enumerate(SERVICES)]}, '<!--p:block:ld_pricing_ja--><!--/p-->']
    page("/services/", "サービス一覧 | Synapse Arrows", "海外進出支援・海外進出アドバイザリー・新規事業開発支援・AI映え診断・AI研修・導入支援・AIエージェント開発支援。事業の段階に合わせて、必要な支援をご提案します。", "services", "サービス一覧", body, ld=ld[:3])
    # pricing LD block lives on the diagnosis pricing page; keep the services page lean
    for i, s in enumerate(SERVICES):
        if s["slug"] == "ai-bae-shindan": continue
        pts = s.get("points") or ["課題・対象業務の整理", "活用方法と実施計画の検討", "導入・開発・運用に向けた支援"]
        topic = "overseas-business" if i < 3 else "ai-development"
        body = intro("BUSINESS CONSULTING" if i < 3 else "AI &amp; OPERATIONS", s["name"], s["detail"], s.get("image")) + f'''<div class="container page-content"><section class="page-section detail-split"><div>{eyebrow("SUPPORT SCOPE")}<h2>{"構想を、次のアクションへ。" if i < 3 else "目的から考える、AI活用。"}</h2><p>事業の状況や課題を伺い、対象範囲・進め方・成果物をすり合わせたうえで支援します。料金は内容に合わせて個別にお見積りします。</p></div><ol class="support-list">{"".join(f"<li><span>0{j+1}</span><h3>{t}</h3></li>" for j, t in enumerate(pts))}</ol></section>{next_band(f"{s['name']}について相談する。", "支援内容や進め方を資料で確認したい方も、具体的な課題をお持ちの方も、お気軽にご相談ください。", s["name"])}<div class="page-actions">{tlink(f"/insights/topics/{topic}/", "関連する調査・実践記事を読む")}{tlink("/services/", "サービス一覧に戻る")}</div></div>'''
        ld = [webpage_ld(f"/services/{s['slug']}/", s["name"], s["detail"]), breadcrumb_ld(("ホーム", "/"), ("サービス一覧", "/services/"), (s["name"], f"/services/{s['slug']}/")),
              {"@context": "https://schema.org", "@type": "Service", "name": s["name"], "description": s["detail"], "provider": {"@id": SITE + "/#organization"}, "areaServed": ["JP", "SG"], "url": SITE + f"/services/{s['slug']}/", "offers": {"@type": "Offer", "description": "個別見積もり"}}]
        page(f"/services/{s['slug']}/", f"{s['name']} | Synapse Arrows", s["detail"], "services", s["name"], body, parent=("/services/", "サービス一覧"), ld=ld)

# ================================================================= PRODUCTS / TOOLS / ABOUT
def build_products():
    cat = [("KanseiLINK", "kanseilink.png", "AIエージェント時代のサービス評価・比較を支える仕組み。当社が運営する第三者の計器です。", "https://kansei-link.com/"), ("Linksee Memory", "linksee.png", "AIエージェントが文脈や記憶を共有するための基盤。オープンソース（MIT）。", "https://docs.linksee.app/"), ("ScaNavi", "scanavi.webp", "日本酒の情報と選び方を届けるAIサービス。", "https://scanavi.app/")]
    cards = "".join(f'<article><div class="catalog-image"><img src="/assets/{im}" alt="{n}" loading="lazy"></div><h3>{n}</h3><p>{c}</p>{xlink(u, "公式サイト")}</article>' for n, im, c, u in cat)
    body = intro("PRODUCTS &amp; INITIATIVES", "自社でつくる。<br>だから、具体的に支援できる。", "診断・評価・AI活用を支える、自社プロダクトと取り組み。") + f'''<div class="container page-content">{product_feature()}<section class="page-section"><div class="section-title-row"><div>{eyebrow("OUR PRODUCTS")}<h2>自らつくり、事業に還元する。</h2></div>{tlink("/tools/", "無料ツール一覧")}</div><div class="product-catalog">{cards}</div></section><details class="page-faq"><summary>開発・検証中の取り組み（企画中を含む）</summary><p>Bantou（AI 経理・ベータ）、CardWize（開発中）、ScaNavi-PC・ScaNavi-Kaden（企画中・まだ提供していません）。公開時には各プロダクトの最新の提供状態を確認してご案内します。</p></details>{next_band("プロダクトの知見を、事業の支援へ。", "導入や活用の進め方も、ご相談いただけます。", "")}</div>'''
    ld = [webpage_ld("/products/", "プロダクト", "診断・評価・AI活用を支える、自社プロダクトと取り組み。"), breadcrumb_ld(("ホーム", "/"), ("プロダクト", "/products/"))]
    page("/products/", "プロダクト | Synapse Arrows", "KanseiLINK・Linksee Memory・ScaNavi と AI映え診断。Synapse Arrows が自社で開発・運営するプロダクトと取り組み。企画中の物は分けて載せています。", "products", "プロダクト", body, ld=ld)
def build_tools():
    body = intro("FREE TOOLS", "まず試して、<br>自社の現在地を知る。", "小さく試し、必要な支援を見つけるためのツールをご紹介します。") + f'''<div class="container page-content">{product_feature(light=True)}<section class="page-section">{eyebrow("AFTER THE CHECK")}<h2>診断のあと、何をすればいい？</h2><p>詳しい診断や、情報の照合・改善支援へ進めます。</p><div class="page-actions">{btn("/ai-bae-shindan/pricing/", "支援内容と料金を見る")}{tlink("/ai-bae-shindan/flow/", "ご利用の流れ")}</div></section><section class="tool-row"><div>{eyebrow("BY INDUSTRY")}<h3>AI映え診断 Light｜飲食店</h3><p>飲食店向け。AI が頼る先（食べログ・Retty・一休.com レストラン・ホットペッパーグルメ・ヒトサラ）へサイトからつながっているかを見ます。</p></div>{tlink("/ai-bae-shindan/inshoku/", "飲食店版を開く", 'data-va="ai_bae_start" data-va-from="tools_inshoku"')}</section><section class="tool-row"><div>{eyebrow("BUSINESS TOOL")}<h3>この仕事、運賃いくら足りない？</h3><p>トラックの大きさ・距離・荷待ち・積み降ろしから、国の「標準的な運賃」との差を計算します（運送業向け）。</p></div>{tlink("/tools/unchin/", "ツールを見る")}</section><section class="tool-row"><div>{eyebrow("FOR SAAS &amp; COMPANIES")}<h3>KanseiLINK のサイトチェッカー</h3><p>当社が運営する AI エージェント向けの計器 KanseiLINK の無料チェック。SaaS や会社のサイトを AI が読めるか・何の会社か判別できるかを見ます（登録不要）。</p></div>{xlink("https://kansei-link.com/site-checker/", "チェッカーを開く")}</section></div>'''
    ld = [webpage_ld("/tools/", "無料ツール", "小さく試し、必要な支援を見つけるためのツール。"), breadcrumb_ld(("ホーム", "/"), ("無料ツール", "/tools/"))]
    page("/tools/", "無料ツール | Synapse Arrows", "AI映え診断 Light（無料・登録不要）、飲食店版、運賃の計算、KanseiLINK のサイトチェッカー。まず試して、自社の現在地を知るための無料ツール。", "", "無料ツール", body, ld=ld)
def build_about():
    body = intro("ABOUT SYNAPSE ARROWS", "事業の可能性を、<br>世界へ、その先へ。", "AI が自社をどう説明しているかを測り、海外進出・新規事業・AI 活用の判断と実行を支えます。", "singapore.webp") + f'''<div class="container page-content"><section class="detail-split page-section"><div>{eyebrow("OUR APPROACH")}<h2>ともに考え、<br>ともにつくる。</h2></div><div><p class="about-lead">次の市場への進出、新しい事業の立ち上げ、組織や業務の変化。事業の状況を理解し、必要な判断と実行に伴走します。</p><p>自社プロダクトの開発で得た知見も、支援に還元します。AI映え診断やAI活用は、事業成長を支えるための取り組みのひとつです。</p><div class="page-actions">{btn("/services/", "サービスを見る")}{tlink("/products/", "自社プロダクトを見る")}</div></div></section><section class="company-profile">{eyebrow("COMPANY")}<h2>会社概要</h2><dl><dt>会社名</dt><dd>Synapse Arrows Pte. Ltd.（シナプスアローズ）</dd><dt>拠点</dt><dd>Singapore / Tokyo</dd><dt>所在地</dt><dd>160 Robinson Road, #14-04 SBF Center, Singapore 068914</dd><dt>代表</dt><dd>山口 路恵（Founder &amp; CEO）</dd><dt>設立</dt><dd>2023年3月8日（シンガポール ACRA 登録・UEN 202308737G）</dd><dt>事業領域</dt><dd>海外進出支援・海外進出アドバイザリー・新規事業開発支援<br>AI映え診断・AI研修・導入支援・AIエージェント開発支援</dd><dt>自社の取り組み</dt><dd><a href="https://kansei-link.com" target="_blank" rel="noopener">KanseiLINK</a>（AI エージェント向けの第三者の計器）・<a href="https://linksee.app" target="_blank" rel="noopener">Linksee Memory</a>（記憶 MCP サーバー）・<a href="/products/">そのほかのプロダクト</a></dd><dt>連絡先</dt><dd><a href="mailto:contact@synapse-arrows.com">contact@synapse-arrows.com</a></dd></dl></section>{next_band("次の一歩を、一緒に。", "現在の状況から、お聞かせください。", "")}</div>'''
    ld = json.load(io.open(ROOT + "scripts/site/ld-about.json", encoding="utf-8"))  # Organization（元は旧 About の JSON-LD）
    for x in ld:
        if x.get("@type") == "Organization":
            x["description"] = "AI が自社をどう説明しているかを測り、海外進出・新規事業・AI 活用の判断と実行を支えるコンサルティング会社（シンガポール・東京）。"
            x["slogan"] = "AI 時代の判断力を、デザインする。"
    if not any(x.get("@type") == "Organization" for x in ld):
        ld.append(dict(ORG_MIN, description="AI が自社をどう説明しているかを測り、海外進出・新規事業・AI 活用の判断と実行を支えるコンサルティング会社（シンガポール・東京）。", slogan="AI 時代の判断力を、デザインする。", address={"@type": "PostalAddress", "streetAddress": "160 Robinson Road, #14-04 SBF Center", "postalCode": "068914", "addressCountry": "SG"}, founder={"@type": "Person", "name": "Michie Yamaguchi"}, foundingDate="2023-03-08"))
    ld += [webpage_ld("/about/", "会社概要", "Synapse Arrows Pte. Ltd. の会社概要。"), breadcrumb_ld(("ホーム", "/"), ("会社概要", "/about/"))]
    page("/about/", "会社概要 | Synapse Arrows", "Synapse Arrows Pte. Ltd.（シンガポール・東京）。AI が自社をどう説明しているかを測り、海外進出・新規事業・AI 活用の判断と実行を支えます。会社情報と自社の取り組み。", "about", "会社概要", body, ld=ld)

# ================================================================= CONTACT (+ confirm)
# 送り先は scripts/site/contact.json の endpoint 1 か所。日本語 2 枚は CONTACT_JS から、英語（/en/contact/ と確認）は
# EN_CONTACT_JS から、どちらも contact_endpoint() で入れる。空か https://script.google.com/macros/s/……/exec の形だけ受け付ける
ENDPOINT_RE = re.compile(r"^https://script\.google\.com/macros/s/[A-Za-z0-9_-]+/exec$")
def contact_endpoint():
    ep = json.loads(rd("scripts/site/contact.json")).get("endpoint", "")
    if not isinstance(ep, str): sys.exit("scripts/site/contact.json: endpoint は文字列で")
    ep = ep.strip()
    if ep and not ENDPOINT_RE.match(ep):
        sys.exit("scripts/site/contact.json: endpoint は空か https://script.google.com/macros/s/……/exec の形で（いま: " + ep + "）")
    return "'" + ep + "'"
INDUSTRY_FALLBACK = ["飲食", "美容院", "不動産", "旅行／宿", "IT／Web", "コンサル", "税理士／会計士", "医療（医科・歯科）", "介護／整体", "美容外科／エステ", "小売", "教室・スクール", "士業", "製造・メーカー", "その他"]
CONTACT_JS = r'''
<script src="/ai-bae-shindan/turnstile-guard.js"></script>
<script>
// Google Apps Script のウェブアプリ URL。正本は scripts/site/contact.json の endpoint（build-site.py が入れる。ここは手で直さない）。
// 空のあいだは、確認の段で「送る」の代わりにメールの案内（mailto）を出す。
const ENDPOINT = __ENDPOINT__;
const API_BASE = (location.hostname === 'localhost' || location.hostname === '127.0.0.1') ? 'http://localhost:3000' : 'https://mcp.kansei-link.com';
const SERVICES = __SERVICES__;
const KEY = 'sa_contact_draft';
const PLAN_NAMES = __PLAN_NAMES__;
function q(name){ return new URLSearchParams(location.search).getAll(name); }
function load(){ try { return JSON.parse(sessionStorage.getItem(KEY) || 'null'); } catch (e) { return null; } }
function save(d){ try { sessionStorage.setItem(KEY, JSON.stringify(d)); } catch (e) {} }
</script>
'''
def build_contact():
    svc_checks = "".join(f'<label class="service-checkbox"><input type="checkbox" name="service" value="{s["name"]}">{s["name"]}</label>' for s in SERVICES)
    ind_opts = "".join(f'<option value="{x}">{x}</option>' for x in INDUSTRY_FALLBACK)
    form = f'''<div class="container page-content contact-page-layout"><aside class="contact-guide">{eyebrow("SERVICE GUIDE")}<h2>必要なサービスの資料を、<br>まとめて。</h2><p>選択したサービスの支援内容や進め方を、資料でご確認いただく構成です。</p><img src="/assets/advisory.webp" alt="" width="1852" height="849" loading="lazy"><h3>資料でわかること</h3><ul><li>サービスの内容・支援範囲</li><li>料金・パッケージの考え方</li><li>ご相談から開始までの流れ</li></ul><p class="small-note">資料は担当が確認のうえ、1 営業日以内にメールでお送りします（自動では配信しません）。</p>{tlink("/services/", "サービス一覧を見直す")}</aside>
<form class="contact-form" id="contact-form" action="/contact/confirm/" method="post" novalidate><div class="intent-switch" role="group" aria-label="お問い合わせの種類"><label><input type="radio" name="intent" value="資料請求" checked>資料請求</label><label><input type="radio" name="intent" value="相談・見積もり">相談・見積もり</label></div><fieldset class="contact-service-field"><legend>検討しているサービス <small>複数選択可</small></legend><div class="contact-service-grid">{svc_checks}</div></fieldset><p class="form-error" id="form-error" role="alert" hidden></p><label class="plan-selected" id="plan-row" hidden>検討中のプラン<input name="plan" id="plan" maxlength="120"><span>料金ページで選んだプランを引き継いでいます。</span></label><div class="form-fields"><label>会社名・店舗名 <span>必須</span><input name="company" autocomplete="organization" required maxlength="120"></label><label>お名前 <span>必須</span><input name="name" autocomplete="name" required maxlength="80"></label><label class="full">メールアドレス <span>必須</span><input name="email" type="email" autocomplete="email" required maxlength="160"></label><label>業種 <small>任意</small><select name="industry" id="industry"><option value="">選択してください</option>{ind_opts}</select></label><label>ホームページURL <small>任意</small><input name="site_url" type="url" inputmode="url" placeholder="https://example.com" maxlength="500"></label><label class="full">ご相談・確認したいこと <small>任意</small><textarea name="message" rows="4" maxlength="2000"></textarea></label></div><div class="hp" aria-hidden="true"><label>Website<input type="text" name="website_hp" tabindex="-1" autocomplete="off"></label></div><label class="consent-row"><input type="checkbox" name="consent" required><span>入力情報の取り扱い（<a href="/policy/#contact-form">プライバシーポリシー 1.5</a>）を確認し、同意します。</span></label><button class="button form-submit" type="submit">入力内容を確認する {CARET_BOLD}</button><p class="small-note">次の画面で内容を確認してから送ります。この画面ではまだ送信されません。</p></form></div>'''
    js = CONTACT_JS.replace("__ENDPOINT__", contact_endpoint()).replace("__SERVICES__", json.dumps([s["name"] for s in SERVICES], ensure_ascii=False)).replace("__PLAN_NAMES__", json.dumps({p["id"]: p["title"] for p in PLANS}, ensure_ascii=False)) + r'''
<script>
(function(){
  var form = document.getElementById('contact-form');
  var d = load() || {};
  var qs = new URLSearchParams(location.search);
  // 料金ページ・トップ・サービスの詳細からの引き継ぎ（?service=…&plan=…&intent=…）
  var svc = q('service'); if (svc.length) d.services = Array.from(new Set((d.services || []).concat(svc)));
  if (qs.has('plan')) { var p = qs.get('plan'); d.plan = PLAN_NAMES[p] || p; }
  if (qs.has('intent')) d.intent = qs.get('intent') === '相談・見積もり' ? '相談・見積もり' : '資料請求';
  // 旧 URL の ?topic= と #download
  var topic = qs.get('topic'); if (topic) { d.intent = (topic === 'download') ? '資料請求' : '相談・見積もり'; if (/aeo|ai-bae|consult|quote/.test(topic)) d.services = Array.from(new Set((d.services || []).concat(['AI映え診断']))); }
  if (location.hash === '#download') d.intent = '資料請求';
  // 業種の一覧は AI映え診断の survey.json（q1）に合わせる。読めなければ HTML の一覧のまま
  fetch('/ai-bae-shindan/survey.json').then(function(r){ return r.ok ? r.json() : null; }).then(function(s){
    var opts = s && s.questions && s.questions.q1 && s.questions.q1.options; if (!opts || !opts.length) return;
    var sel = document.getElementById('industry'); var cur = d.industry || '';
    sel.innerHTML = '<option value="">選択してください</option>' + opts.map(function(o){ return '<option value="' + o.id + '" data-label="' + o.label + '">' + o.label + '</option>'; }).join('');
    if (cur) sel.value = cur;
  }).catch(function(){});
  // 下書きを戻す（修正の段から戻ってきた時）
  function fill(){
    form.querySelectorAll('input[name=service]').forEach(function(c){ c.checked = (d.services || []).indexOf(c.value) >= 0; });
    form.querySelectorAll('input[name=intent]').forEach(function(r){ r.checked = r.value === (d.intent || '資料請求'); });
    ['company','name','email','site_url','message','industry'].forEach(function(k){ if (d[k] != null && form.elements[k]) form.elements[k].value = d[k]; });
    if (d.plan) { form.elements.plan.value = d.plan; document.getElementById('plan-row').hidden = false; }
    if (d.consent) form.elements.consent.checked = true;
  }
  fill();
  function collect(){
    var sel = form.elements.industry; var o = sel.options[sel.selectedIndex];
    return {
      intent: form.querySelector('input[name=intent]:checked').value,
      services: Array.from(form.querySelectorAll('input[name=service]:checked')).map(function(c){ return c.value; }),
      plan: form.elements.plan.value.trim(),
      company: form.elements.company.value.trim(), name: form.elements.name.value.trim(), email: form.elements.email.value.trim(),
      industry: sel.value, industry_label: sel.value && o ? (o.getAttribute('data-label') || o.textContent) : '',
      site_url: form.elements.site_url.value.trim(), message: form.elements.message.value.trim(),
      consent: form.elements.consent.checked, website_hp: form.elements.website_hp.value,
      page: location.origin + location.pathname, referrer: document.referrer || '',
      utm_source: qs.get('utm_source') || (d.utm_source || ''), utm_medium: qs.get('utm_medium') || (d.utm_medium || ''), utm_campaign: qs.get('utm_campaign') || (d.utm_campaign || '')
    };
  }
  form.addEventListener('submit', function(ev){
    ev.preventDefault();
    var err = document.getElementById('form-error'); err.hidden = true;
    var u = form.elements.site_url; if (u.value && !/^https?:\/\//i.test(u.value)) u.value = 'https://' + u.value.trim();
    var data = collect();
    if (data.intent === '資料請求' && !data.services.length) { err.textContent = '資料をご希望のサービスを1つ以上お選びください。'; err.hidden = false; err.scrollIntoView({ block: 'center' }); return; }
    if (!form.checkValidity()) { form.reportValidity(); return; }
    if (!data.industry_label && data.industry) data.industry_label = data.industry;
    save(data);
    location.href = '/contact/confirm/';
  });
})();
</script>'''
    body = intro("CONTACT", "資料で知る。<br>相談して確かめる。", "サービスを比較したい方も、具体的な課題をお持ちの方も。") + form + js
    ld = [webpage_ld("/contact/", "資料請求・ご相談", "Synapse Arrows への資料請求・ご相談。"), breadcrumb_ld(("ホーム", "/"), ("資料請求・ご相談", "/contact/")), {"@context": "https://schema.org", "@type": "ContactPage", "url": SITE + "/contact/", "name": "資料請求・ご相談", "mainEntity": {"@id": SITE + "/#organization"}}]
    page("/contact/", "資料請求・ご相談 | Synapse Arrows", "6 つのサービス（海外進出支援・海外進出アドバイザリー・新規事業開発支援・AI映え診断・AI研修・導入支援・AIエージェント開発支援）の資料請求と、無料相談・お見積もりの入口。", "", "資料請求・ご相談", body, ld=ld)
    # confirm step
    cjs = CONTACT_JS.replace("__ENDPOINT__", contact_endpoint()).replace("__SERVICES__", "[]").replace("__PLAN_NAMES__", "{}") + r'''
<script>
(function(){
  var d = load();
  var box = document.getElementById('confirm-box'), empty = document.getElementById('confirm-empty');
  if (!d || !d.name || !d.email) { empty.hidden = false; return; }
  box.hidden = false;
  var rows = [['お問い合わせの種類', d.intent], ['ご希望のサービス', (d.services || []).join(' ／ ') || 'ご相談のみ'], ['検討中のプラン', d.plan], ['会社名・店舗名', d.company], ['お名前', d.name], ['メールアドレス', d.email], ['業種', d.industry_label], ['ホームページURL', d.site_url], ['ご相談内容', d.message]];
  var dl = document.getElementById('confirm-list');
  rows.forEach(function(r){ if (!r[1]) return; var dt = document.createElement('dt'); dt.textContent = r[0]; var dd = document.createElement('dd'); dd.textContent = r[1]; dl.appendChild(dt); dl.appendChild(dd); });
  var sendBtn = document.getElementById('send-btn'), mailBtn = document.getElementById('mail-btn'), status = document.getElementById('send-status');
  var purpose = d.intent === '資料請求' ? 'download' : 'consult';
  function mailto(){
    var body = ['お問い合わせの種類: ' + d.intent, 'ご希望のサービス: ' + ((d.services || []).join(' ／ ') || 'ご相談のみ'), 'プラン: ' + (d.plan || ''), '会社名・店舗名: ' + d.company, 'お名前: ' + d.name, 'メール: ' + d.email, '業種: ' + (d.industry_label || ''), 'サイトの URL: ' + (d.site_url || ''), 'ご相談内容:', (d.message || '').slice(0, 1500)].join('\n');
    return 'mailto:contact@synapse-arrows.com?subject=' + encodeURIComponent('【' + d.intent + '】' + (d.services || []).join('・')) + '&body=' + encodeURIComponent(body + '\n');
  }
  mailBtn.href = mailto();
  if (!ENDPOINT) { sendBtn.hidden = true; mailBtn.hidden = false; status.textContent = 'フォームの送信先は準備中です。お手数ですが、入力内容が入ったメールでお送りください。'; return; }
  mailBtn.hidden = true;
  try { if (window.KLTurnstile) window.KLTurnstile.init(API_BASE, document.getElementById('ts-box')); } catch (e) {}
  var busy = false;
  sendBtn.addEventListener('click', async function(){
    if (busy) return; busy = true; sendBtn.disabled = true; status.className = 'send-status'; status.textContent = '送っています…';
    var p = Object.assign({}, d, { purpose: purpose, lang: 'ja', ts: new Date().toISOString(), consent: true });
    try {
      var tok = null; try { tok = window.KLTurnstile ? await window.KLTurnstile.token() : null; } catch (e) { tok = null; }
      if (tok) p.turnstile_token = tok;
      var r = await fetch(ENDPOINT, { method: 'POST', mode: 'cors', headers: { 'Content-Type': 'text/plain;charset=utf-8' }, body: JSON.stringify(p) });
      var j = null; try { j = await r.json(); } catch (e) { j = null; }
      if (!j || j.ok !== true) throw new Error((j && j.error) || ('http_' + r.status));
      try { sessionStorage.removeItem(KEY); } catch (e) {}
      box.hidden = true; var ok = document.getElementById('confirm-ok'); ok.hidden = false;
      document.getElementById('ok-text').textContent = purpose === 'download' ? '受け付けました。担当から 1 営業日以内に、資料をメールでお送りします。' : '受け付けました。1 営業日以内にメールでご連絡します。';
      if (window.va) window.va('event', { name: 'contact_submit', data: { purpose: purpose, services: (d.services || []).length } });
    } catch (e) {
      var code = e && e.message; var msg = { rate_limited: '短い時間に何度も送られたため、いったん止めています。1 時間ほどおいてからお試しください。', turnstile_failed: '人による操作の確認に失敗しました。ページを読み込み直してお試しください。', turnstile_required: '人による操作の確認が終わりませんでした。ページを読み込み直してお試しください。', bad_request: '入力の内容を受け付けられませんでした。' }[code] || '送れませんでした。';
      status.className = 'send-status error'; status.textContent = msg + ' お手数ですが、下のメールからお送りください。'; mailBtn.hidden = false;
      busy = false; sendBtn.disabled = false;
    }
  });
})();
</script>'''
    cbody = intro("CONTACT / REVIEW", "ご入力内容の確認", "内容をご確認のうえ、「この内容で送る」を押してください。") + f'''<div class="container page-content confirmation-page"><div id="confirm-box" hidden><div class="confirm-intro">{CHECK_C}<span>送信前の確認画面です</span></div><dl class="confirmation" id="confirm-list"></dl><div id="ts-box" class="ts-box"></div><p class="send-status" id="send-status"></p><div class="page-actions">{btn("/contact/", "入力内容を修正する", secondary=True)}<button class="button" type="button" id="send-btn">この内容で送る {CARET_BOLD}</button><a class="button" id="mail-btn" href="#" hidden>この内容をメールで送る {CARET_BOLD}</a></div><p class="small-note">送信後、担当が確認してメールでお返事します。資料請求だけで有料のご契約にはなりません。</p></div><div id="confirm-ok" class="success-panel" hidden tabindex="-1"><h2>送りました</h2><p id="ok-text"></p><div class="page-actions">{btn("/", "トップページへ")}{tlink("/ai-bae-shindan/", "無料の AI映え診断を試す", 'data-va="ai_bae_start" data-va-from="contact_done"')}</div></div><div id="confirm-empty" hidden><p>確認する入力内容がありません。資料請求・ご相談のページからご入力ください。</p>{btn("/contact/", "資料請求・ご相談へ")}</div></div>''' + cjs
    page("/contact/confirm/", "入力内容の確認 | Synapse Arrows", "資料請求・ご相談の入力内容の確認。", "", "入力内容の確認", cbody, parent=("/contact/", "資料請求・ご相談"), ld=[breadcrumb_ld(("ホーム", "/"), ("資料請求・ご相談", "/contact/"), ("入力内容の確認", "/contact/confirm/"))], noindex=True)

# ================================================================= AI BAE: pricing / flow
def plan_card(p, featured=False):
    price = f'<div class="plan-price">{"<small>月</small>" if p["monthly"] else ""}{P(p["id"] + ".man_num", {"report": "5", "report_remeasure": "8", "monitor": "3", "implement": "21〜"}[p["id"]])}<span>万円</span></div><p class="price-unit">税別 / {"月" if p["monthly"] else "1回"}</p>'
    term = f'<p class="term-total">最低契約期間：{MIN}か月<br>{MIN}か月総額：税別 {P(p["id"] + ".term_total_man", {"monitor": "18万円", "implement": "126万円〜"}.get(p["id"], ""))}<br>{P(p["id"] + ".after_ja", "")}{'<br><a href="#prepay">6 か月・1 年のまとめ払い（割引あり）</a>' if p["id"] == "monitor" else ""}</p>' if p["monthly"] else '<p class="term-total">単発のご依頼／継続契約不要</p>'
    cta = btn(req_url("AI映え診断", p["id"], "相談・見積もり"), "このプランを相談", secondary=not featured, attrs=f'data-va="plan_cta" data-plan="{p["id"]}"')
    return f'<article class="plan{" featured-plan" if featured else ""}"><span class="small-label">{p["label"]}</span><h3>{p["title"]}</h3>{price}<p>{p["description"]}</p><ul>{"".join(f"<li>{f}</li>" for f in p["features"])}</ul>{term}{cta}</article>'
def build_pricing():
    rows = [("受け取るもの", lambda p: p["delivery"]), ("測定のタイミング", lambda p: p["frequency"]), ("修正・実装を行う人", lambda p: p["fix"]), ("オンライン面談", lambda p: p["meeting"] + (f'（オプション「{ADV_JA["name"]}」月{ADV_JA["man"]}で付けられます）' if p["id"] == "monitor" else "")), ("契約期間", lambda p: f"最低{MIN}か月。{P(p['id'] + '.after_ja', '')}" if p["monthly"] else "単発")]
    table = '<table class="diagnosis-comparison"><caption>有料プランの成果物と対応範囲</caption><thead><tr><th scope="col">比較項目</th>' + "".join(f'<th scope="col">{p["title"]}<span>{PRICE_LABEL[p["id"]]}（税別）</span></th>' for p in PLANS) + "</tr></thead><tbody>" + "".join(f'<tr><th scope="row">{l}</th>' + "".join(f"<td>{f(p)}</td>" for p in PLANS) + "</tr>" for l, f in rows) + "</tbody></table>"
    faqs = [("月21万円〜の「〜」は、何で変わりますか？", "対象ページ、修正・実装の範囲と件数、必要な支援内容によって変わります。実施する作業、月額費用、納期をお見積もりで明記し、合意してから開始します。件数はご相談の上で決めます。"), ("契約前に確認できることは？", "対象のAI・質問・ページ、測定条件、納期、納品物を確認します。複数店舗・複数社は個別見積もりです。月額プランは最低期間のあと、1 か月ごとに続けるか止めるかを選べます。"), ("まとめ払いはできますか？", "定点観測と、そのオプション「アドバイスあり」は、6 か月一括と 1 年一括のまとめ払いを選べます。どちらも割引があり、最初の 6 か月から選べます。実装・伴走はまとめ払いの割引はありません。1 年以内の前払いの経理上の扱いは、顧問の税理士にご確認ください。"), ("消費税はかかりますか？", "表示はすべて税別です。消費税の扱いは、ご契約の時にご案内します。")]
    body = intro("AI BAE SHINDAN / PRICING", "違いは、調べる範囲と、<br>改善を誰が進めるか。", "まずは単発で課題を知る。必要に応じて、毎月の観測や実行支援へ。") + f'''<div class="container page-content"><p class="pricing-basis">{P("scope_ja", "1 店舗・1 社あたり")}／税別。月額プランは最低{MIN}か月。{AFTER_JA}実装・伴走は作業範囲に応じた個別見積もりです。{TAX}</p>
 <section class="free-plan-row"><article><span class="small-label">サイトの情報が読み取れるかを知る</span><h2>{P("light.name_ja", "Light")} <strong>無料</strong></h2><p>登録不要。サイトへのアクセス、事業情報の手がかり、関連情報へのつながりを確認します。</p><p class="small-note">AIへ質問する診断ではありません。</p>{tlink("/ai-bae-shindan/#check", "無料でサイトをチェック", 'data-va="ai_bae_start" data-va-from="pricing_free"')}</article><article><span class="small-label">AIの回答を少し見てみる</span><h2>{P("detailed.name_ja", "詳しい診断")} <strong>無料</strong></h2><p>メール確認あり。4つのAI（ChatGPT・Claude・Gemini・Perplexity）に固定の3問を1回ずつ質問。誤りの詳細は1件まで確認できます。</p><p class="small-note">広い範囲の照合や修正リストは有料プランで提供します。Light の結果の画面から申し込めます。</p>{tlink("/ai-bae-shindan/#check", "Light から申し込む")}</article></section>
 <section class="page-section">{eyebrow("PAID PLANS")}<h2>課題を知るところから、改善の実行まで。</h2><div class="plan-grid">{"".join(plan_card(p, p["id"] == "report") for p in PLANS)}</div></section>
 <section class="page-section" id="prepay">{eyebrow("PREPAY &amp; OPTION")}<h2>定点観測は、まとめ払いで割安に。</h2><p>オプション「{ADV_JA["name"]}」は、定点観測に{ADV_JA["content"]}を付けるものです（月{ADV_JA["man"]}・税別）。まとめ払いの時は、オプションにも同じ割引が付きます。</p>{prepay_table("定点観測とオプションの払い方（税別）", ["払い方", "定点観測", f'オプション「{ADV_JA["name"]}」'], [("月払い", 0), ("6 か月一括", 6), ("1 年一括", 12)], P("prepay_tax_note_ja", ""))}<p class="small-note">{P("prepay_choose_ja", "")}</p></section>
 <section class="page-section comparison-section">{eyebrow("COMPARE THE DELIVERABLES")}<h2>何が届き、誰が修正する？</h2><p class="small-note compare-hint">表は横にスクロールしてご覧いただけます。</p><div class="comparison-scroll" tabindex="0" role="region" aria-label="有料プランの比較表">{table}</div></section>
 <aside class="monitor-note"><div>{eyebrow("MONTHLY REPORTING")}<h2>月{P("monitor.man", "3万円")}は、<br>レポートで変化を把握するプラン。</h2></div><div><p>毎月の測定結果をお届けし、お客様側で内容の確認と改善を進めていただきます。オンライン面談や、サイトの修正作業は含みません。面談をご希望の時は、オプション「{ADV_JA["name"]}」（月{ADV_JA["man"]}）で{ADV_JA["content"]}を付けられます。</p><p class="future-feature"><strong>今後の予定</strong>{DASH}</p></div></aside>
 {"".join(f'<details class="page-faq"><summary>{q}</summary><p>{a}</p></details>' for q, a in faqs)}{next_band("まずは単発で、課題を整理しませんか？", "プランを決めきれていなくても、ご相談いただけます。")}{tlink("/ai-bae-shindan/flow/", "申し込み後の流れを見る")}<p class="small-note scope-footnote">料金は{P("decided_on_ja", "2026年10月27日")}改定。対象範囲・契約条件は正式なお見積もりでご案内します。</p></div>'''
    ld = [webpage_ld("/ai-bae-shindan/pricing/", "AI映え診断の料金・パッケージ", "照合レポート・照合＋測り直し・定点観測・実装・伴走の料金と範囲。"), breadcrumb_ld(("ホーム", "/"), ("AI映え診断", "/ai-bae-shindan/"), ("料金・パッケージ", "/ai-bae-shindan/pricing/")), faq_ld(faqs)]
    html = head("AI映え診断の料金・パッケージ | Synapse Arrows", "AI映え診断の料金。Light と詳しい診断は無料。照合レポート・照合＋測り直し（単発）、定点観測・実装・伴走（月額・最低6か月、その後は1か月ごと）。定点観測は6か月・1年のまとめ払いで割引。1店舗・1社あたり、税別。何が届き、誰が修正するかの比較表。", "/ai-bae-shindan/pricing/", ld, "/ai-bae-shindan/img/og-ai-bae.png", extra_css=PREPAY_CSS) + header("", "/ai-bae-shindan/pricing/") + diag_nav("/ai-bae-shindan/pricing/") + f'<main id="main" class="inner-page">{crumb("料金・パッケージ", ("/ai-bae-shindan/", "AI映え診断"))}{body}</main>\n<!--p:block:ld_pricing_ja--><!--/p-->\n' + footer("/ai-bae-shindan/pricing/")
    wr("ai-bae-shindan/pricing/index.html", html)
def build_flow():
    steps = [("資料請求・相談を送る", "お客様", "対象の会社・店舗、サイトURL、気になっていることをお知らせください。プランが未定でも構いません。", "この時点で有料契約にはなりません。"), ("対象と調査内容を確認する", "双方で確認", "対象のAI、質問する内容、公式情報、調べたい範囲をすり合わせます。", "気になる回答のスクリーンショットがあれば、ご共有ください。"), ("見積もり・納期に合意する", "双方で確認", "料金、納品物、納期、月額の場合の契約期間を確認してから、ご契約・開始の手続きへ進みます。", "実装・伴走は、作業内容と件数もここで決めます。"), ("診断・レポートを受け取る", "Synapse Arrows", "合意した条件で調査し、AIの回答と公式情報の違い、修正の優先順位をレポートにまとめます。", "納品時期はお見積もりでご案内します。")]
    tl = "".join(f'<li><span>0{i+1}</span><div><small>{o}</small><h2>{t}</h2><p>{p}</p><p class="small-note">{n}</p></div></li>' for i, (t, o, p, n) in enumerate(steps))
    after = "".join(f'<article><span class="small-label">{PRICE_LABEL[p["id"]]}（税別）</span><h3>{p["title"]}</h3><p>{p["after"]}</p></article>' for p in PLANS)
    faqs = [("資料請求だけでも大丈夫ですか？", "はい。まず資料で支援内容や料金をご確認いただけます。有料サービスは内容と見積もりに合意したうえでご契約いただく流れです。"), ("月3万円のプランに打ち合わせはありますか？", "定点観測はレポート提供が基本で、オンライン面談は含みません。改善の実行や継続的な支援まで希望される場合は、実装・伴走プランをご相談ください。"), ("自社で修正できない場合は？", "実装・伴走プラン（月21万円〜・税別）で、合意した範囲の修正を支援します。外部サイトなど、お客様や当社で直接変更できない情報は、対応方法を確認します。")]
    body = intro("AI BAE SHINDAN / HOW IT WORKS", "申し込んだあと、<br>何をすればいい？", "ご相談からレポートのお届け、その後の対応までをご案内します。") + f'''<div class="container page-content"><div class="flow-page-layout"><ol class="page-timeline">{tl}</ol><aside class="quiet-aside">{eyebrow("BEFORE YOU START")}<h2>まず必要なのは、<br>URLと気になること。</h2><ul><li>会社・店舗のサイトURL</li><li>対象の商品・サービス</li><li>気になるAIの回答例（あれば）</li></ul><p>専門知識や、完成した改善計画は不要です。相談前に試したい方は、無料版Lightもご利用いただけます。</p>{btn(req_url("AI映え診断", "", "相談・見積もり"), "プランについて相談する", attrs='data-va="download_click" data-va-from="flow_aside"')}{tlink("/ai-bae-shindan/#check", "無料版Lightを試す", 'data-va="ai_bae_start" data-va-from="flow_aside"')}</aside></div>
 <section class="page-section">{eyebrow("AFTER THE REPORT")}<h2>レポートのあとが、<br>プランによって変わります。</h2><div class="after-report-grid">{after}</div></section><p class="future-feature"><strong>定点観測の提供方法</strong>現在はレポートでのご提供です。{DASH}</p>{"".join(f'<details class="page-faq"><summary>{q}</summary><p>{a}</p></details>' for q, a in faqs)}{next_band()}{tlink("/ai-bae-shindan/pricing/", "料金と支援範囲を比較する")}</div>'''
    ld = [webpage_ld("/ai-bae-shindan/flow/", "AI映え診断 ご利用の流れ", "ご相談からレポートのお届け、その後の対応まで。"), breadcrumb_ld(("ホーム", "/"), ("AI映え診断", "/ai-bae-shindan/"), ("ご利用の流れ", "/ai-bae-shindan/flow/")), faq_ld([(q, a.replace("月21万円〜", "月額（税別・範囲で変わる）")) for q, a in faqs[:2]] + [(faqs[2][0], "実装・伴走プラン（月額・税別）で、合意した範囲の修正を支援します。外部サイトなど、お客様や当社で直接変更できない情報は、対応方法を確認します。")])]
    html = head("AI映え診断 ご利用の流れ | Synapse Arrows", "AI映え診断の申し込み後の流れ。資料請求・相談 → 対象と調査内容の確認 → 見積もり・納期の合意 → 診断・レポート。レポートのあとはプランによって変わります。", "/ai-bae-shindan/flow/", ld, "/ai-bae-shindan/img/og-ai-bae.png") + header("", "/ai-bae-shindan/flow/") + diag_nav("/ai-bae-shindan/flow/") + f'<main id="main" class="inner-page">{crumb("ご利用の流れ", ("/ai-bae-shindan/", "AI映え診断"))}{body}</main>\n' + footer("/ai-bae-shindan/flow/")
    wr("ai-bae-shindan/flow/index.html", html)

# ================================================================= INSIGHTS
ARTICLES = json.load(io.open(ROOT + "scripts/site/insights-data.json", encoding="utf-8"))
TOPICS = [
 {"id": "global", "slug": "overseas-business", "label": "海外進出・新規事業", "eyebrow": "GLOBAL BUSINESS", "title": "次の市場と、事業の可能性を考える。", "intro": "海外展開の検討と、新しい事業を進めるための調査・実践知をまとめました。シンガポールの市場や支援会社、経営の考え方を、事業の判断材料としてご覧ください。", "image": "singapore.webp", "tag": "市場を知り、次の一歩を考える", "questions": [("進出の目的を整理する", "販売先の開拓、拠点づくり、調達など、海外で何を実現したいかを分けて考えます。"), ("市場と実行条件を確かめる", "顧客、販売経路、現地の制度や運営体制を確認し、比較記事から専門家への相談事項を整理します。"), ("小さく検証し、次の判断へ", "事業の前提やボトルネックを見つけ、検証する順番を決めます。記事は個別の進出判断を置き換えるものではありません。")], "services": [("/services/overseas-expansion/", "海外進出支援"), ("/services/overseas-advisory/", "海外進出アドバイザリー"), ("/services/new-business/", "新規事業開発支援")]},
 {"id": "aeo", "slug": "ai-search", "label": "AI検索・AEO", "eyebrow": "AI SEARCH &amp; RESEARCH", "title": "AIに、事業がどう伝わるかを知る。", "intro": "AIの回答や引用元を調べた記録と、情報発信を見直すための記事です。自社の現状把握から、調査・改善支援の比較まで、順を追って確認できます。", "image": "advisory.webp", "tag": "AIの回答と情報発信を確かめる", "questions": [("サイトの下地とAIの回答を分ける", "サイトが読める状態にあることと、AIが正しく説明・推薦することは別です。確認したい対象に合う診断を選びます。"), ("質問・時点・出典を確認する", "実測記事を読むときは、対象AI、質問文、実施時点、参照されたページを合わせて確認します。一度の結果をすべての検索に一般化しないことが大切です。"), ("修正する場所と担当を決める", "公式情報とのズレを整理したうえで、自社サイトの修正、外部掲載先への確認、再測定の順番を決めます。")], "services": [("/ai-bae-shindan/", "AI映え診断の内容"), ("/ai-bae-shindan/pricing/", "診断の料金・パッケージ"), ("/ai-bae-shindan/#check", "無料版Light")]},
 {"id": "technology", "slug": "ai-development", "label": "AI活用・開発", "eyebrow": "AI IN PRACTICE", "title": "つくった経験を、事業の実行へ。", "intro": "KanseiLINKやLinksee Memoryの開発・調査で得た知見を集めました。業務で使うAIを選ぶところから、接続・運用の検討まで、実装の背景をたどれます。", "image": "new-business.webp", "tag": "技術の検証を業務に活かす", "questions": [("業務の目的から選ぶ", "ツールの機能一覧だけでなく、減らしたい手作業や、任せたい判断を明確にして読み進めます。"), ("接続条件と運用を確かめる", "MCP・APIの対応、認証、権限、エラー時の対応など、実運用で必要な条件を確認します。記事時点の仕様と現行仕様は区別します。"), ("評価方法と利用場面を照らし合わせる", "公開情報に基づく評価と、実際の業務環境での検証は目的が異なります。自社の条件に合わせて試す範囲を決めます。")], "services": [("/services/ai-training/", "AI研修・導入支援"), ("/services/ai-agents/", "AIエージェント開発支援"), ("/products/", "自社プロダクト")]},
]
MEDIA = [("Zenn", "https://zenn.dev/kanseilink", "開発の背景と技術の記録"), ("note", "https://note.com/rodan_ai", "事業づくりと日々の実践"), ("YouTube", "https://www.youtube.com/channel/UC0mscauCUi5NGxYMhbRWY3A", "経営・AIのテーマを動画で"), ("Qiita", "https://qiita.com/michie_yamaguchi", "実装・連携の技術記事"), ("KanseiLINK", "https://kansei-link.com/insights/index.html", "評価方法・調査・解説"), ("ScaNavi", "https://scanavi.app/", "日本酒と海外市場の情報")]
def topic_name(i): return next((t["label"] for t in TOPICS if t["id"] == i), "お知らせ")
def article_card(a):
    internal = a["url"].startswith(SITE)
    link = (lambda h, l: f'<a href="{h}">{l}</a>') if internal else (lambda h, l: f'<a href="{h}" target="_blank" rel="noopener">{l} {UPRIGHT}</a>')
    foot = f'<time datetime="{a["date"]}">{a["date"].replace("-", ".")}</time>' if a.get("date") else "<span>記事内の調査時点をご確認ください</span>"
    comp = f'<a href="{a["companion"]}" target="_blank" rel="noopener">解説記事 {UPRIGHT}</a>' if a.get("companion") else ""
    return f'<article class="insight-entry" data-topic="{a["topic"]}" data-source="{a["source"]}" data-text="{esc((a["title"] + " " + a["summary"] + " " + a["source"] + " " + topic_name(a["topic"])).lower())}"><div class="insight-meta"><span>{topic_name(a["topic"])}</span><span>{a["source"]}{" / 動画" if a.get("format") == "動画" else ""}</span></div><h3>{link(a["url"], a["title"])}</h3><p>{a["summary"]}</p><div class="insight-entry-foot">{foot}{comp}</div></article>'
INSIGHTS_JS = r'''
<script>
(function(){
  var cards = Array.from(document.querySelectorAll('#article-grid .insight-entry'));
  var topicBtns = Array.from(document.querySelectorAll('.insight-filters button')), srcSel = document.getElementById('source'), q = document.getElementById('q');
  var meta = document.getElementById('results-meta'), more = document.getElementById('more'), clear = document.getElementById('clear'), empty = document.getElementById('empty');
  var topic = 'all', limit = 6;
  function norm(s){ return (s || '').normalize('NFKC').toLowerCase().trim(); }
  function apply(){
    var src = srcSel.value, qq = norm(q.value), shown = 0, matched = 0;
    cards.forEach(function(c){
      var ok = (topic === 'all' || c.dataset.topic === topic) && (src === 'all' || c.dataset.source === src) && (!qq || c.dataset.text.indexOf(qq) >= 0);
      if (ok) { matched++; c.hidden = shown >= limit; if (!c.hidden) shown++; } else c.hidden = true;
    });
    meta.textContent = matched + '件' + (matched > limit ? '中 ' + shown + '件を表示' : '');
    more.hidden = matched <= limit; more.textContent = 'さらに表示する（残り' + Math.max(0, matched - limit) + '件）';
    empty.hidden = matched > 0; clear.hidden = (topic === 'all' && src === 'all' && !qq);
  }
  topicBtns.forEach(function(b){ b.addEventListener('click', function(){ topic = b.dataset.topic; topicBtns.forEach(function(x){ x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); }); limit = 6; apply(); }); });
  srcSel.addEventListener('change', function(){ limit = 6; apply(); }); q.addEventListener('input', function(){ limit = 6; apply(); });
  more.addEventListener('click', function(){ limit += 6; apply(); });
  function reset(){ topic = 'all'; srcSel.value = 'all'; q.value = ''; topicBtns.forEach(function(x){ x.setAttribute('aria-pressed', x.dataset.topic === 'all' ? 'true' : 'false'); }); limit = 6; apply(); }
  clear.addEventListener('click', reset); document.getElementById('empty-reset').addEventListener('click', reset);
  apply();
})();
</script>'''
def build_insights():
    featured = ARTICLES[0]; videos = [a for a in ARTICLES if a.get("format") == "動画"]
    topics_nav = '<nav class="insight-topic-links" aria-label="テーマ別の読み方">' + "".join(f'<a href="/insights/topics/{t["slug"]}/"><span>0{i+1} / {t["eyebrow"]}</span><strong>{t["label"]}{ARROW_R}</strong><p>{t["tag"]}</p></a>' for i, t in enumerate(TOPICS)) + "</nav>"
    filters = "".join(f'<button type="button" data-topic="{i}" aria-pressed="{"true" if i == "all" else "false"}">{l}</button>' for i, l in [("all", "すべて")] + [(t["id"], t["label"]) for t in TOPICS] + [("news", "お知らせ")])
    sources = "".join(f'<option value="{n}">{n}</option>' for n in ["Synapse Arrows"] + [m[0] for m in MEDIA])
    grid = "".join(article_card(a) for a in ARTICLES)
    vids = "".join(f'<article><div class="video-heading">{PLAY_C}<span>YouTube / 経営の考え方</span></div><h3>{v["title"]}</h3><p>{v["summary"]}</p><div class="page-actions">{xlink(v["url"], "YouTubeで見る")}{xlink(v["companion"], "解説記事を読む")}</div></article>' for v in videos)
    media = "".join(f'<a href="{u}" target="_blank" rel="noopener"><div><strong>{n}</strong><span>{c}</span></div>{UPRIGHT}</a>' for n, u, c in MEDIA)
    body = intro("INSIGHTS / RESEARCH &amp; PRACTICE", "調べる。試す。<br>事業の次につなげる。", "海外進出、新規事業、AIの活用。自社の調査とプロダクト開発から得た知見を、記事と動画でお届けします。", "advisory.webp") + f'''<div class="container page-content">{topics_nav}<section class="insight-feature"><div class="insight-feature-label">{eyebrow("FEATURED RESEARCH")}<span>AI検索の実測調査</span><p>12問 × 4つのAI<br><strong>48回答</strong></p><small>2026年9月の調査</small></div><div><div class="insight-meta"><span>Synapse Arrows / 調査記事</span><time datetime="2026-09-30">2026.09.30</time></div><h2><a href="{featured["url"]}">AIは税理士事務所を、<br>何を根拠に推薦しているか。</a></h2><p>回答に挙がった事務所だけでなく、AIが引用した情報源を調査。公式サイトと外部の紹介情報が、どう参照されたかを確認できます。</p><div class="page-actions">{tlink(featured["url"], "調査方法・結果を読む")}{tlink("/insights/topics/ai-search/", "AI検索の記事をまとめて読む")}</div></div></section>
<section class="insight-archive" id="articles"><div class="section-title-row"><div>{eyebrow("ARTICLE &amp; VIDEO INDEX")}<h2>気になるテーマから探す。</h2></div><span class="small-note">記事名を押すと、掲載元が開きます（外部の掲載先は別タブ）。</span></div><div class="insight-filter-top"><div class="insight-filters" role="group" aria-label="記事のテーマ">{filters}</div><div class="insight-search-row"><label>キーワード<div class="insight-search">{SEARCH_I}<input type="search" id="q" placeholder="例：シンガポール、MCP"></div></label><label>掲載先<select id="source"><option value="all">すべての掲載先</option>{sources}</select></label></div></div><div class="insight-results-meta"><p role="status" id="results-meta"></p><button type="button" id="clear" hidden>絞り込みを解除</button></div><div class="insight-article-grid" id="article-grid">{grid}</div><div class="insight-more"><button type="button" class="button secondary" id="more" hidden></button></div><div class="insight-empty" id="empty" hidden><h3>条件に合う記事がありません。</h3><p>キーワードを短くするか、テーマ・掲載先を変更してください。</p><button type="button" class="button secondary" id="empty-reset">すべての記事を表示する</button></div></section>
<section class="insight-video-section"><div class="section-title-row"><div>{eyebrow("WATCH &amp; READ")}<h2>動画でつかみ、記事で深める。</h2></div>{xlink("https://kansei-link.com/insights/videos/", "動画ライブラリ")}</div><div class="insight-video-grid">{vids}</div></section>
<section class="insight-media-section"><div class="section-title-row"><div>{eyebrow("OUR CHANNELS")}<h2>それぞれの場所で、<br>実践と知見を発信しています。</h2></div><p>媒体ごとの記事・動画一覧はこちらから。</p></div><div class="insight-media-grid">{media}</div><p class="small-note">KanseiLINK・ScaNaviはSynapse Arrowsの自社プロダクトです。note・Qiitaは代表者個人の発信を含みます。</p></section>{next_band("読んで気づいた課題を、次の行動へ。", "海外進出、新規事業、AI検索・活用。自社の場合にどう進めるか、ご相談いただけます。", "")}</div>''' + INSIGHTS_JS
    items = [{"@type": "ListItem", "position": i + 1, "url": a["url"], "name": a["title"]} for i, a in enumerate(ARTICLES)]
    ld = [{"@context": "https://schema.org", "@type": "CollectionPage", "@id": SITE + "/insights/#page", "url": SITE + "/insights/", "name": "Insights・記事", "inLanguage": "ja", "isPartOf": {"@id": SITE + "/#website"}, "mainEntity": {"@type": "ItemList", "itemListElement": items}}, breadcrumb_ld(("ホーム", "/"), ("Insights・記事", "/insights/"))]
    page("/insights/", "Insights・記事 | Synapse Arrows", "海外進出・新規事業、AI検索・AEO、AI活用・開発の調査と実践記事。Synapse Arrows、KanseiLINK、Zenn、note、Qiita、YouTubeの発信をテーマ別に探せます。", "insights", "Insights・記事", body, ld=ld)
    for t in TOPICS:
        rel = [a for a in ARTICLES if a["topic"] == t["id"]]
        body = intro(f'INSIGHTS / {t["eyebrow"]}', t["title"], t["intro"], t["image"]) + f'''<div class="container page-content"><section class="page-section">{eyebrow("READING GUIDE")}<h2>このテーマで、確認しておきたいこと。</h2><div class="three-steps">{"".join(f"<article><b>0{i+1}</b><h3>{q}</h3><p>{c}</p></article>" for i, (q, c) in enumerate(t["questions"]))}</div></section><section class="page-section"><div class="section-title-row"><div>{eyebrow("SELECTED READING")}<h2>{t["label"]}の記事・動画</h2></div><p class="small-note">掲載元の全文・出典へ進めます。</p></div><div class="insight-article-grid">{"".join(article_card(a) for a in rel)}</div><p class="small-note scope-footnote">調査結果やサービス仕様は各記事の時点の情報です。個別の判断には、記事内の調査条件とリンク先の最新情報を併せてご確認ください。</p></section><section class="insight-related-services"><div>{eyebrow("FROM INSIGHT TO ACTION")}<h2>自社の課題として、<br>具体的に検討したい方へ。</h2></div><div>{"".join(tlink(u, n) for u, n in t["services"])}</div></section>{tlink("/insights/", "Insights一覧へ戻る")}</div>'''
        ld = [{"@context": "https://schema.org", "@type": "CollectionPage", "url": SITE + f"/insights/topics/{t['slug']}/", "name": t["label"], "description": t["intro"], "inLanguage": "ja", "mainEntity": {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": a["url"], "name": a["title"]} for i, a in enumerate(rel)]}}, breadcrumb_ld(("ホーム", "/"), ("Insights・記事", "/insights/"), (t["label"], f"/insights/topics/{t['slug']}/"))]
        page(f"/insights/topics/{t['slug']}/", f"{t['label']}の読み方・記事 | Synapse Arrows", t["intro"], "insights", t["label"], body, parent=("/insights/", "Insights"), ld=ld)

# ================================================================= ENGLISH (/en/)
# 見た目・型は日本語と同じ。文言は scripts/site/en.json（services は slug、plans は id で日本語と 1 対 1）。
for _s in SERVICES: assert _s["slug"] in EN["services"], f'en.json に services.{_s["slug"]} が無い'
for _p in PLANS: assert _p["id"] in EN["plans"], f'en.json に plans.{_p["id"]} が無い'
ENS = [dict(s, **EN["services"][s["slug"]]) for s in SERVICES]
ENP = [dict(p, **EN["plans"][p["id"]]) for p in PLANS]
def en_svc_href(s): return "/en/services/ai-aeo/" if s["slug"] == "ai-bae-shindan" else f"/en/services/{s['slug']}/"
def en_req_url(service="", plan="", intent="download"):
    from urllib.parse import urlencode
    q = {}
    if service: q["service"] = service
    if plan: q["plan"] = plan
    q["intent"] = intent
    return "/en/contact/?" + urlencode(q)
def en_next_band(title=None, copy=None, service=""):
    t = EN["next_band"]
    return f'<section class="next-band-new"><div>{eyebrow(t["eyebrow"])}<h2>{title or t["h2"]}</h2><p>{copy or t["p"]}</p></div>{btn(en_req_url(service), t["button"], attrs="data-va=\"download_click\" data-va-from=\"next_band\"")}</section>'
def en_feature(anchor=""):
    f = EN["feature"]; t = EN["top"]
    return f'<section class="product-feature-new"{f" id={chr(34)}{anchor}{chr(34)}" if anchor else ""}><div>{eyebrow(f["eyebrow"])}<img class="feature-logo" src="/assets/diagnosis-logo.webp" alt="AI映え診断 by Synapse Arrows" width="1000" height="270" loading="lazy"><h2>{f["h2"]}</h2><p>{t["product_p1"]}</p><p>{t["product_p2"]}</p><div class="page-actions">{btn("/en/services/ai-aeo/", f["cta"], attrs="data-va=\"ai_bae_en\" data-va-from=\"feature\"")}{tlink("/en/services/ai-aeo/#plans", f["cta2"])}</div><p class="small-note">{f["note"]}</p></div><div class="feature-characters"><img src="/assets/characters.webp" alt="{f["characters_alt"]}" width="640" height="344" loading="lazy"></div></section>'
def en_page(path, title, desc, current, label, body, parent=None, ld=None, extra_css="", noindex=False, after_main=""):
    return page(path, title, desc, current, label, body, parent=parent, ld=ld, extra_css=extra_css, noindex=noindex, lang="en", after_main=after_main)
def en_bc(*items): return breadcrumb_ld(*((EN["nav"]["home"], "/en/"),) + items)

def build_en_top():
    t = EN["top"]
    org = dict(ORG_MIN, description=EN["org_description"], slogan=EN["tagline"], address={"@type": "PostalAddress", "streetAddress": "160 Robinson Road, #14-04 SBF Center", "postalCode": "068914", "addressCountry": "SG"},
               makesOffer=[{"@type": "Offer", "itemOffered": {"@type": "Service", "name": s["name"], "url": SITE + en_svc_href(s)}} for s in ENS])
    ld = [org, {"@context": "https://schema.org", "@type": "WebSite", "@id": SITE + "/#website", "name": "Synapse Arrows", "url": SITE + "/", "inLanguage": ["ja", "en"]}, webpage_ld("/en/", t["title"], t["description"], "en")]
    cards = "".join(f'<a class="service-item" href="{en_svc_href(s)}"><span class="service-number">0{i+1}<span></span></span><h3>{s["name"]}</h3><p>{s["copy"]}</p><div class="service-photo"><img src="/assets/{s["image"]}" alt="" width="600" height="275" loading="lazy"><span class="photo-arrow">{CARET_BOLD}</span></div></a>' for i, s in enumerate(ENS[:3]))
    checks = "".join(f'<label class="service-checkbox"><input type="checkbox" name="service" value="{esc(s["name"])}"><span>{s["name"]}</span></label>' for s in ENS)
    plinks = "".join(f'<a class="text-link" href="{h}"{" lang=" + chr(34) + "ja" + chr(34) if h.startswith("/ai-bae") else ""}>{l} {CARET_BOLD}</a>' for h, l in t["product_links"])
    extra = '    <link rel="preload" as="image" href="/assets/hero.webp" fetchpriority="high">\n    <style>.service-item{display:block;color:inherit}.service-item h3{margin:8px 0 0}.request-action .button[aria-disabled=true]{opacity:.55;cursor:not-allowed}</style>\n'
    sub = "".join(f"<span>{x}</span>" + ("<wbr>" if i == 0 else "") for i, x in enumerate(EN["hero_sub"]))
    body = f'''{header("", "/en/", "en")}<main id="main">
      <section class="hero" aria-labelledby="hero-title"><img class="hero-image" src="/assets/hero.webp" alt="" width="1920" height="819" fetchpriority="high"><div class="hero-shade"></div>
        <div class="container hero-inner"><p class="location"><span aria-hidden="true"></span>Singapore / Tokyo</p><h1 id="hero-title">{EN["tagline_html"]}</h1><p class="hero-subtitle">{sub}</p><p class="hero-copy">{EN["hero_copy"]}</p><div class="hero-actions"><a href="/en/services/ai-aeo/" class="button" data-va="ai_bae_en" data-va-from="hero">{t["cta_primary"]} {CARET_BOLD}</a><a href="/en/contact/" class="button button-outline" data-va="download_click" data-va-from="hero">{t["cta_secondary"]} {CARET_BOLD}</a></div></div>
      </section>
      <section class="services section" id="services" aria-labelledby="services-title"><div class="container">{eyebrow("OUR SERVICES")}<h2 id="services-title"><span>{t["services_h2"][0]}</span> <wbr><span>{t["services_h2"][1]}</span></h2><p class="section-intro">{t["services_intro"]}</p><div class="service-grid">{cards}</div></div></section>
      <section class="product section" id="product" aria-labelledby="product-title"><div class="container">{eyebrow("PRODUCT &amp; SERVICE")}<div class="product-grid"><div class="product-copy"><h2 id="product-title">{t["product_h2"]}</h2><img class="diagnosis-logo" src="/assets/diagnosis-logo.webp" alt="AI映え診断 by Synapse Arrows" width="1000" height="270" loading="lazy"><p>{t["product_p1"]}</p><p>{t["product_p2"]}</p><p class="small-note">{t["product_note"]}</p></div><img class="characters" src="/assets/characters.webp" alt="{EN["feature"]["characters_alt"]}" width="640" height="344" loading="lazy"></div><div class="product-actions"><a class="button" href="/en/services/ai-aeo/" data-va="ai_bae_en" data-va-from="product">{t["cta_primary"]} {CARET_BOLD}</a>{plinks}</div><div class="related"><span>{t["related"]}</span><a href="/en/services/ai-training/">{ENS[4]["name"]}</a><span class="slash" aria-hidden="true">/</span><a href="/en/services/ai-agents/">{ENS[5]["name"]}</a></div></div></section>
      <section class="request section" id="request" aria-labelledby="request-title"><div class="container">{eyebrow("DOWNLOAD")}<h2 id="request-title"><span>{t["request_h2"][0]}</span> <wbr><span>{t["request_h2"][1]}</span></h2><form id="request-form" action="/en/contact/" method="get"><fieldset><legend>{t["request_legend"]}</legend><div class="selection-grid">{checks}</div></fieldset><input type="hidden" name="intent" value="download"><p class="form-error" id="request-error" role="alert" hidden>{t["request_error"]}</p><div class="request-action"><button class="button" type="submit" data-va="download_click" data-va-from="top_request">{t["request_button"]} {CARET_BOLD}</button><span class="selection-count" id="selection-count" aria-live="polite"></span></div></form></div></section>
    </main>
'''
    wr("en/index.html", head(t["title"], t["description"], "/en/", ld, extra_css=extra, lang="en") + body + footer("/en/", "en"))

def en_columns(items, see):
    out = '<div class="consulting-columns">'
    for s in items:
        i = ENS.index(s); h = en_svc_href(s)
        img = f'<a href="{h}"><img src="/assets/{s["image"]}" alt="" width="1852" height="849" loading="lazy"></a>' if s.get("image") else ""
        out += f'<article><span class="column-number">0{i+1}</span><h3><a href="{h}">{s["name"]}</a></h3><p>{s.get("copy") or s["detail"]}</p>{img}{tlink(h, see)}</article>'
    return out + "</div>"
def build_en_services():
    t = EN["services_page"]; d = EN["detail"]
    body = intro(t["intro_eyebrow"], t["intro_h1"], t["intro_copy"]) + f'''<div class="container page-content">{en_feature("pricing")}<section class="page-section">{eyebrow("BUSINESS CONSULTING")}<h2>{t["biz_h2"]}</h2>{en_columns(ENS[:3], t["see"])}</section><section class="page-section">{eyebrow("AI &amp; OPERATIONS")}<h2>{t["ai_h2"]}</h2>{en_columns(ENS[4:], t["see"])}</section><p class="small-note">{t["pricing_p"]}</p>{en_next_band(t["next_h2"], t["next_p"])}</div>'''
    ld = [webpage_ld("/en/services/", t["label"], t["intro_copy"], "en"), en_bc((t["label"], "/en/services/")),
          {"@context": "https://schema.org", "@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": s["name"], "url": SITE + en_svc_href(s)} for i, s in enumerate(ENS)]}]
    en_page("/en/services/", t["title"], t["description"], "services", t["label"], body, ld=ld)
    for i, s in enumerate(ENS):
        if s["slug"] == "ai-bae-shindan": continue
        pts = s.get("points") or EN["service_points_default"]
        path = f"/en/services/{s['slug']}/"
        body = intro("BUSINESS CONSULTING" if i < 3 else "AI &amp; OPERATIONS", s["name"], s["detail"], s.get("image")) + f'''<div class="container page-content"><section class="page-section detail-split"><div>{eyebrow(d["eyebrow_scope"])}<h2>{d["h2_biz"] if i < 3 else d["h2_ai"]}</h2><p>{d["p"]}</p></div><ol class="support-list">{"".join(f"<li><span>0{j+1}</span><h3>{x}</h3></li>" for j, x in enumerate(pts))}</ol></section>{en_next_band(d["next_h2"].replace("{name}", s["name"][0].lower() + s["name"][1:] if not s["name"].startswith("AI") else s["name"]), d["next_p"], s["name"])}<div class="page-actions">{tlink("/en/insights/", d["articles"])}{tlink("/en/services/", d["back"])}</div></div>'''
        ld = [webpage_ld(path, s["name"], s["detail"], "en"), en_bc((t["label"], "/en/services/"), (s["name"], path)),
              {"@context": "https://schema.org", "@type": "Service", "name": s["name"], "description": s["detail"], "provider": {"@id": SITE + "/#organization"}, "areaServed": ["JP", "SG"], "availableLanguage": ["ja", "en"], "url": SITE + path, "offers": {"@type": "Offer", "description": d["offer"]}}]
        en_page(path, f"{s['name']} | Synapse Arrows", s["detail"], "services", s["name"], body, parent=("/en/services/", t["label"]), ld=ld)

def en_plan_card(p, featured=False):
    a = EN["aiaeo"]
    price = f'<div class="plan-price price-en">{P(p["id"] + ".jpy", "JPY 0")}{"<span>" + a["per_month"] + "</span>" if p["monthly"] else ""}</div><p class="price-unit">excl. tax</p>'
    term = f'<p class="term-total">{a["min_term"].replace("{n}", P(p["id"] + ".min_months", "6"))}<br>{P(p["id"] + ".after_en", "")}{"<br><a href=" + chr(34) + "#prepay" + chr(34) + ">" + a["prepay_more"] + "</a>" if p["id"] == "monitor" else ""}</p>' if p["monthly"] else f'<p class="term-total">{a["one_off"]}</p>'
    cta = btn(en_req_url(EN["services"]["ai-bae-shindan"]["name"], p["id"], "consult"), a["plan_cta"], secondary=not featured, attrs=f'data-va="plan_cta" data-plan="{p["id"]}"')
    return f'<article class="plan{" featured-plan" if featured else ""}"><span class="small-label">{p["label"]}</span><h3>{p["title"]}</h3>{price}<p>{p["description"]}</p><ul>{"".join(f"<li>{x}</li>" for x in p["features"])}</ul>{term}{cta}</article>'
def build_en_aiaeo():
    a = EN["aiaeo"]; path = "/en/services/ai-aeo/"
    jp = "".join(f'<a class="text-link" href="{h}" lang="ja" hreflang="ja">{l} {CARET_BOLD}</a>' for h, l in a["jp_links"])
    stages = "".join(f"<article><b>0{i+1}</b><h3>{n}</h3><p class=\"small-label\">{w}</p><p>{c}</p></article>" for i, (n, w, c) in enumerate(a["stages"]))
    price_label = {p["id"]: P(p["id"] + ".jpy", "JPY 0") + (a["per_month"] if p["monthly"] else "") for p in ENP}
    adv = {"name": P("advice.name_en", "Advice add-on"), "price": P("advice.jpy", "JPY 0") + a["per_month"], "content": P("advice.content_en", "")}
    vals = [lambda p: p["delivery"], lambda p: p["frequency"], lambda p: p["fix"], lambda p: p["meeting"] + (a["meeting_option"].replace("{name}", adv["name"]).replace("{price}", adv["price"]) if p["id"] == "monitor" else ""), lambda p: a["minimum"].replace("{n}", P(p["id"] + ".min_months", "6")) + ". " + P(p["id"] + ".after_en", "") if p["monthly"] else a["single"]]
    table = f'<table class="diagnosis-comparison"><caption>{a["compare_caption"]}</caption><thead><tr><th scope="col">{a["compare_item"]}</th>' + "".join(f'<th scope="col">{p["title"]}<span>{price_label[p["id"]]} (excl. tax)</span></th>' for p in ENP) + "</tr></thead><tbody>" + "".join(f'<tr><th scope="row">{l}</th>' + "".join(f"<td>{f(p)}</td>" for p in ENP) + "</tr>" for l, f in zip(a["compare_rows"], vals)) + "</tbody></table>"
    notes = f'<p class="pricing-basis">Prices are {P("scope_en", "per shop or company")}.{P("tax_note_en", "All prices exclude tax.")} {P("sgd_note_en", "Prices are in Japanese yen.")} {a["prices_basis"]}</p>'
    body = intro(a["intro_eyebrow"], a["intro_h1"], a["intro_copy"]) + f'''<div class="container page-content">
 <aside class="monitor-note"><div>{eyebrow("PLEASE NOTE")}<h2>{a["honest_h2"]}</h2></div><div><p>{a["honest_p"]}</p><div class="page-actions">{jp}</div></div></aside>
 <section class="page-section">{eyebrow(a["stages_eyebrow"])}<h2>{a["stages_h2"]}</h2><div class="three-steps">{stages}</div></section>
 <section class="page-section" id="plans">{eyebrow(a["plans_eyebrow"])}<h2>{a["plans_h2"]}</h2>{notes}<div class="plan-grid">{"".join(en_plan_card(p, p["id"] == "report") for p in ENP)}</div></section>
 <section class="page-section" id="prepay">{eyebrow(a["prepay_eyebrow"])}<h2>{a["prepay_h2"]}</h2><p>{a["option_p"].replace("{name}", adv["name"]).replace("{content}", adv["content"]).replace("{price}", adv["price"])}</p>{prepay_table(a["prepay_caption"], a["prepay_cols"], list(zip(a["prepay_rows"], [0, 6, 12])), P("prepay_tax_note_en", ""), "en")}<p class="small-note">{P("prepay_choose_en", "")}</p></section>
 <section class="page-section comparison-section">{eyebrow(a["compare_eyebrow"])}<h2>{a["compare_h2"]}</h2><p class="small-note compare-hint">{a["compare_hint"]}</p><div class="comparison-scroll" tabindex="0" role="region" aria-label="{a["compare_region"]}">{table}</div></section>
 <section class="page-section detail-split"><div>{eyebrow("WHAT CHANGES")}<h2>{a["change_h2"]}</h2><p>{a["change_p"]}</p><p><strong>{a["why_min"]}.</strong> {P("min_term_reason_en", "")}</p><p class="future-feature">{a["dashboard"]}</p></div><div><h3>{a["fit_h2"]}</h3><ul>{"".join(f"<li>{x}</li>" for x in a["fit"])}</ul><h3>{a["nofit_h2"]}</h3><ul>{"".join(f"<li>{x}</li>" for x in a["nofit"])}</ul></div></section>
 <section class="page-section">{eyebrow(a["who_eyebrow"])}<h2>{a["who_h2"]}</h2><p>{a["who_p"]}</p></section>
 {en_next_band(a["next_h2"], a["next_p"], EN["services"]["ai-bae-shindan"]["name"])}<p class="small-note scope-footnote">{a["set_on"]} {P("decided_on", "2026-10-27")}.</p></div>'''
    ld = [webpage_ld(path, a["label"], a["intro_copy"], "en"), en_bc((EN["services_page"]["label"], "/en/services/"), (a["label"], path))]
    en_page(path, a["title"], a["description"], "services", a["label"], body, parent=("/en/services/", EN["services_page"]["label"]), ld=ld, extra_css='    <style>.plan-price.price-en{font-size:34px}@media(max-width:600px){.plan-price.price-en{font-size:30px}}</style>\n' + PREPAY_CSS, after_main="<!--p:block:ld_pricing_en--><!--/p-->\n")

def build_en_products():
    t = EN["products"]
    cards = "".join(f'<article><div class="catalog-image"><img src="/assets/{im}" alt="{n}" loading="lazy"></div><h3>{n}</h3><p>{c}</p>{xlink(u, t["official"])}</article>' for n, im, c, u in t["catalog"])
    body = intro(t["intro_eyebrow"], t["intro_h1"], t["intro_copy"]) + f'''<div class="container page-content">{en_feature()}<section class="page-section">{eyebrow(t["eyebrow"])}<h2>{t["h2"]}</h2><div class="product-catalog">{cards}</div></section><details class="page-faq"><summary>{t["pipeline_summary"]}</summary><p>{t["pipeline"]}</p></details>{en_next_band(t["next_h2"], t["next_p"])}</div>'''
    ld = [webpage_ld("/en/products/", t["label"], t["intro_copy"], "en"), en_bc((t["label"], "/en/products/"))]
    en_page("/en/products/", t["title"], t["description"], "products", t["label"], body, ld=ld)

def build_en_about():
    t = EN["about"]
    rows = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in t["rows"])
    body = intro(t["intro_eyebrow"], t["intro_h1"], EN["hero_sub"][0] + " " + EN["hero_sub"][1], "singapore.webp") + f'''<div class="container page-content"><section class="detail-split page-section"><div>{eyebrow(t["approach_eyebrow"])}<h2>{t["approach_h2"]}</h2></div><div><p class="about-lead">{t["lead"]}</p><p>{t["p"]}</p><div class="page-actions">{btn("/en/services/", t["see_services"])}{tlink("/en/products/", t["see_products"])}</div></div></section><section class="company-profile">{eyebrow(t["company_eyebrow"])}<h2>{t["company_h2"]}</h2><dl>{rows}</dl></section>{en_next_band(t["next_h2"], t["next_p"])}</div>'''
    org = dict(ORG_MIN, description=EN["org_description"], slogan=EN["tagline"], address={"@type": "PostalAddress", "streetAddress": "160 Robinson Road, #14-04 SBF Center", "postalCode": "068914", "addressCountry": "SG"}, founder={"@type": "Person", "name": "Michie Yamaguchi"}, foundingDate="2023-03-08", email="contact@synapse-arrows.com")
    ld = [org, webpage_ld("/en/about/", t["label"], t["description"], "en"), en_bc((t["label"], "/en/about/"))]
    en_page("/en/about/", t["title"], t["description"], "about", t["label"], body, ld=ld)

EN_CONTACT_JS = r'''
<script src="/ai-bae-shindan/turnstile-guard.js"></script>
<script>
// Same endpoint as the Japanese form (Google Apps Script). Source of truth: scripts/site/contact.json (build-site.py fills it in; do not edit here).
// While it is empty, the review step offers a prefilled email (mailto) instead of "Send".
const ENDPOINT = __ENDPOINT__;
const API_BASE = (location.hostname === 'localhost' || location.hostname === '127.0.0.1') ? 'http://localhost:3000' : 'https://mcp.kansei-link.com';
const T = __T__;
const KEY = 'sa_contact_draft_en';
const PLAN_NAMES = __PLAN_NAMES__;
function q(name){ return new URLSearchParams(location.search).getAll(name); }
function load(){ try { return JSON.parse(sessionStorage.getItem(KEY) || 'null'); } catch (e) { return null; } }
function save(d){ try { sessionStorage.setItem(KEY, JSON.stringify(d)); } catch (e) {} }
</script>
'''
def build_en_contact():
    c = EN["contact"]
    tjs = json.dumps({k: c[k] for k in ("err_choose", "rows", "consult_only", "sending", "ok_download", "ok_consult", "endpoint_pending", "err_rate", "err_ts_failed", "err_ts_required", "err_bad", "err_generic", "err_tail", "mail_labels", "intent_download", "intent_consult")}, ensure_ascii=False)
    svc_checks = "".join(f'<label class="service-checkbox"><input type="checkbox" name="service" value="{esc(s["name"])}">{s["name"]}</label>' for s in ENS)
    ind = "".join(f'<option value="{i}">{l}</option>' for i, l in c["industries"])
    req = f'<span>{c["required"]}</span>'; opt = f'<small>{c["optional"]}</small>'
    form = f'''<div class="container page-content contact-page-layout"><aside class="contact-guide">{eyebrow(c["guide_eyebrow"])}<h2>{c["guide_h2"]}</h2><p>{c["guide_p"]}</p><img src="/assets/advisory.webp" alt="" width="1852" height="849" loading="lazy"><h3>{c["guide_h3"]}</h3><ul>{"".join(f"<li>{x}</li>" for x in c["guide_items"])}</ul><p class="small-note">{c["guide_note"]}</p>{tlink("/en/services/", c["back"])}</aside>
<form class="contact-form" id="contact-form" action="/en/contact/confirm/" method="post" novalidate><div class="intent-switch" role="group" aria-label="{c["intent_group"]}"><label><input type="radio" name="intent" value="download" checked>{c["intent_download"]}</label><label><input type="radio" name="intent" value="consult">{c["intent_consult"]}</label></div><fieldset class="contact-service-field"><legend>{c["services_legend"]} <small>{c["services_small"]}</small></legend><div class="contact-service-grid">{svc_checks}</div></fieldset><p class="form-error" id="form-error" role="alert" hidden></p><label class="plan-selected" id="plan-row" hidden>{c["plan_label"]}<input name="plan" id="plan" maxlength="120"><span>{c["plan_note"]}</span></label><div class="form-fields"><label>{c["company"]} {req}<input name="company" autocomplete="organization" required maxlength="120"></label><label>{c["name"]} {req}<input name="name" autocomplete="name" required maxlength="80"></label><label class="full">{c["email"]} {req}<input name="email" type="email" autocomplete="email" required maxlength="160"></label><label>{c["industry"]} {opt}<select name="industry" id="industry"><option value="">{c["industry_choose"]}</option>{ind}</select></label><label>{c["site_url"]} {opt}<input name="site_url" type="url" inputmode="url" placeholder="https://example.com" maxlength="500"></label><label class="full">{c["message"]} {opt}<textarea name="message" rows="4" maxlength="2000"></textarea></label></div><div class="hp" aria-hidden="true"><label>Website<input type="text" name="website_hp" tabindex="-1" autocomplete="off"></label></div><label class="consent-row"><input type="checkbox" name="consent" required><span>{c["consent"]}</span></label><button class="button form-submit" type="submit">{c["submit"]} {CARET_BOLD}</button><p class="small-note">{c["submit_note"]}</p></form></div>'''
    base_js = EN_CONTACT_JS.replace("__ENDPOINT__", contact_endpoint()).replace("__T__", tjs)
    js = base_js.replace("__PLAN_NAMES__", json.dumps({p["id"]: p["title"] for p in ENP}, ensure_ascii=False)) + r'''
<script>
(function(){
  var form = document.getElementById('contact-form');
  var d = load() || {};
  var qs = new URLSearchParams(location.search);
  // carried over from the prices page, the top page and service pages (?service=…&plan=…&intent=…)
  var svc = q('service'); if (svc.length) d.services = Array.from(new Set((d.services || []).concat(svc)));
  if (qs.has('plan')) { var p = qs.get('plan'); d.plan = PLAN_NAMES[p] || p; }
  if (qs.has('intent')) d.intent = qs.get('intent') === 'consult' ? 'consult' : 'download';
  function fill(){
    form.querySelectorAll('input[name=service]').forEach(function(c){ c.checked = (d.services || []).indexOf(c.value) >= 0; });
    form.querySelectorAll('input[name=intent]').forEach(function(r){ r.checked = r.value === (d.intent || 'download'); });
    ['company','name','email','site_url','message','industry'].forEach(function(k){ if (d[k] != null && form.elements[k]) form.elements[k].value = d[k]; });
    if (d.plan) { form.elements.plan.value = d.plan; document.getElementById('plan-row').hidden = false; }
    if (d.consent) form.elements.consent.checked = true;
  }
  fill();
  function collect(){
    var sel = form.elements.industry; var o = sel.options[sel.selectedIndex];
    return {
      intent: form.querySelector('input[name=intent]:checked').value,
      services: Array.from(form.querySelectorAll('input[name=service]:checked')).map(function(c){ return c.value; }),
      plan: form.elements.plan.value.trim(),
      company: form.elements.company.value.trim(), name: form.elements.name.value.trim(), email: form.elements.email.value.trim(),
      industry: sel.value, industry_label: sel.value && o ? o.textContent : '',
      site_url: form.elements.site_url.value.trim(), message: form.elements.message.value.trim(),
      consent: form.elements.consent.checked, website_hp: form.elements.website_hp.value,
      page: location.origin + location.pathname, referrer: document.referrer || '',
      utm_source: qs.get('utm_source') || (d.utm_source || ''), utm_medium: qs.get('utm_medium') || (d.utm_medium || ''), utm_campaign: qs.get('utm_campaign') || (d.utm_campaign || '')
    };
  }
  form.addEventListener('submit', function(ev){
    ev.preventDefault();
    var err = document.getElementById('form-error'); err.hidden = true;
    var u = form.elements.site_url; if (u.value && !/^https?:\/\//i.test(u.value)) u.value = 'https://' + u.value.trim();
    var data = collect();
    if (data.intent === 'download' && !data.services.length) { err.textContent = T.err_choose; err.hidden = false; err.scrollIntoView({ block: 'center' }); return; }
    if (!form.checkValidity()) { form.reportValidity(); return; }
    save(data);
    location.href = '/en/contact/confirm/';
  });
})();
</script>'''
    body = intro(c["intro_eyebrow"], c["intro_h1"], c["intro_copy"]) + form + js
    ld = [webpage_ld("/en/contact/", c["label"], c["description"], "en"), en_bc((c["label"], "/en/contact/")), {"@context": "https://schema.org", "@type": "ContactPage", "url": SITE + "/en/contact/", "name": c["label"], "inLanguage": "en", "mainEntity": {"@id": SITE + "/#organization"}}]
    en_page("/en/contact/", c["title"], c["description"], "", c["label"], body, ld=ld)
    cjs = base_js.replace("__PLAN_NAMES__", "{}") + r'''
<script>
(function(){
  var d = load();
  var box = document.getElementById('confirm-box'), empty = document.getElementById('confirm-empty');
  if (!d || !d.name || !d.email) { empty.hidden = false; return; }
  box.hidden = false;
  var intent = d.intent === 'consult' ? T.intent_consult : T.intent_download;
  var svcs = (d.services || []).join(' / ') || T.consult_only;
  var vals = [intent, svcs, d.plan, d.company, d.name, d.email, d.industry_label, d.site_url, d.message];
  var dl = document.getElementById('confirm-list');
  T.rows.forEach(function(label, i){ if (!vals[i]) return; var dt = document.createElement('dt'); dt.textContent = label; var dd = document.createElement('dd'); dd.textContent = vals[i]; dl.appendChild(dt); dl.appendChild(dd); });
  var sendBtn = document.getElementById('send-btn'), mailBtn = document.getElementById('mail-btn'), status = document.getElementById('send-status');
  var purpose = d.intent === 'consult' ? 'consult' : 'download';
  function mailto(){
    var L = T.mail_labels;
    var body = [L[0] + ': ' + intent, L[1] + ': ' + svcs, L[2] + ': ' + (d.plan || ''), L[3] + ': ' + d.company, L[4] + ': ' + d.name, L[5] + ': ' + d.email, L[6] + ': ' + (d.industry_label || ''), L[7] + ': ' + (d.site_url || ''), L[8] + ':', (d.message || '').slice(0, 1500)].join('\n');
    return 'mailto:contact@synapse-arrows.com?subject=' + encodeURIComponent('[' + intent + '] ' + (d.services || []).join(', ')) + '&body=' + encodeURIComponent(body + '\n');
  }
  mailBtn.href = mailto();
  if (!ENDPOINT) { sendBtn.hidden = true; mailBtn.hidden = false; status.textContent = T.endpoint_pending; return; }
  mailBtn.hidden = true;
  try { if (window.KLTurnstile) window.KLTurnstile.init(API_BASE, document.getElementById('ts-box')); } catch (e) {}
  var busy = false;
  sendBtn.addEventListener('click', async function(){
    if (busy) return; busy = true; sendBtn.disabled = true; status.className = 'send-status'; status.textContent = T.sending;
    var p = Object.assign({}, d, { purpose: purpose, lang: 'en', ts: new Date().toISOString(), consent: true });
    try {
      var tok = null; try { tok = window.KLTurnstile ? await window.KLTurnstile.token() : null; } catch (e) { tok = null; }
      if (tok) p.turnstile_token = tok;
      var r = await fetch(ENDPOINT, { method: 'POST', mode: 'cors', headers: { 'Content-Type': 'text/plain;charset=utf-8' }, body: JSON.stringify(p) });
      var j = null; try { j = await r.json(); } catch (e) { j = null; }
      if (!j || j.ok !== true) throw new Error((j && j.error) || ('http_' + r.status));
      try { sessionStorage.removeItem(KEY); } catch (e) {}
      box.hidden = true; var ok = document.getElementById('confirm-ok'); ok.hidden = false;
      document.getElementById('ok-text').textContent = purpose === 'download' ? T.ok_download : T.ok_consult;
      if (window.va) window.va('event', { name: 'contact_submit', data: { purpose: purpose, services: (d.services || []).length, lang: 'en' } });
    } catch (e) {
      var code = e && e.message; var msg = { rate_limited: T.err_rate, turnstile_failed: T.err_ts_failed, turnstile_required: T.err_ts_required, bad_request: T.err_bad }[code] || T.err_generic;
      status.className = 'send-status error'; status.textContent = msg + T.err_tail; mailBtn.hidden = false;
      busy = false; sendBtn.disabled = false;
    }
  });
})();
</script>'''
    cbody = intro(c["confirm_eyebrow"], c["confirm_h1"], c["confirm_copy"]) + f'''<div class="container page-content confirmation-page"><div id="confirm-box" hidden><div class="confirm-intro">{CHECK_C}<span>{c["confirm_intro"]}</span></div><dl class="confirmation" id="confirm-list"></dl><div id="ts-box" class="ts-box"></div><p class="send-status" id="send-status"></p><div class="page-actions">{btn("/en/contact/", c["fix"], secondary=True)}<button class="button" type="button" id="send-btn">{c["send"]} {CARET_BOLD}</button><a class="button" id="mail-btn" href="#" hidden>{c["send_mail"]} {CARET_BOLD}</a></div><p class="small-note">{c["confirm_note"]}</p></div><div id="confirm-ok" class="success-panel" hidden tabindex="-1"><h2>{c["sent_h2"]}</h2><p id="ok-text"></p><div class="page-actions">{btn("/en/", c["to_top"])}{tlink("/en/services/ai-aeo/", EN["feature"]["cta"])}</div></div><div id="confirm-empty" hidden><p>{c["empty"]}</p>{btn("/en/contact/", c["to_contact"])}</div></div>''' + cjs
    en_page("/en/contact/confirm/", c["confirm_title"], c["confirm_description"], "", c["confirm_label"], cbody, parent=("/en/contact/", c["label"]), ld=[en_bc((c["label"], "/en/contact/"), (c["confirm_label"], "/en/contact/confirm/"))], noindex=True)

EN_ARTICLE = "/en/insights/geo-aeo-agencies-singapore-2026-09/"
def build_en_insights():
    t = EN["insights"]
    def card(a):
        ja = f' <span class="small-note">({t["japanese"]})</span>' if a.get("ja") else ""
        return f'<article class="insight-entry"><div class="insight-meta"><span>{a["source"]}</span></div><h3><a href="{a["url"]}" target="_blank" rel="noopener"{" hreflang=" + chr(34) + "ja" + chr(34) if a.get("ja") else ""}>{a["title"]} {UPRIGHT}</a>{ja}</h3><p>{a["summary"]}</p></article>'
    grid = "".join(card(a) for a in t["articles"])
    media = "".join(f'<a href="{u}"{"" if u.startswith("/") else " target=" + chr(34) + "_blank" + chr(34) + " rel=" + chr(34) + "noopener" + chr(34)}><div><strong>{n}</strong><span>{c}</span></div>{UPRIGHT}</a>' for n, u, c in t["channels"])
    body = intro(t["intro_eyebrow"], t["intro_h1"], t["intro_copy"], "advisory.webp") + f'''<div class="container page-content"><section class="insight-feature"><div class="insight-feature-label">{eyebrow(t["featured_eyebrow"])}<span>{t["featured_tag"]}</span><p>{t["featured_stat"]}</p><small>{t["featured_time"]}</small></div><div><div class="insight-meta"><span>{t["featured_meta"]}</span><time datetime="2026-10-22">2026.10.22</time></div><h2><a href="{EN_ARTICLE}">AEO and GEO agencies in Singapore (2026):<br>17 compared on pricing and terms.</a></h2><p>{t["featured_p"]}</p><div class="page-actions">{tlink(EN_ARTICLE, t["featured_cta"])}</div></div></section>
<section class="insight-archive" id="articles"><div class="section-title-row"><div>{eyebrow(t["list_eyebrow"])}<h2>{t["list_h2"]}</h2></div><span class="small-note">{t["list_note"]}</span></div><div class="insight-article-grid">{grid}</div></section>
<section class="insight-media-section"><div class="section-title-row"><div>{eyebrow(t["channels_eyebrow"])}<h2>{t["channels_h2"]}</h2></div></div><div class="insight-media-grid">{media}</div></section>{en_next_band(t["next_h2"], t["next_p"])}</div>'''
    items = [{"@type": "ListItem", "position": 1, "url": SITE + EN_ARTICLE, "name": "AEO and GEO agencies in Singapore (2026): 17 compared on pricing and terms"}] + [{"@type": "ListItem", "position": i + 2, "url": a["url"], "name": a["title"]} for i, a in enumerate(t["articles"])]
    ld = [{"@context": "https://schema.org", "@type": "CollectionPage", "@id": SITE + "/en/insights/#page", "url": SITE + "/en/insights/", "name": t["label"], "inLanguage": "en", "isPartOf": {"@id": SITE + "/#website"}, "mainEntity": {"@type": "ItemList", "itemListElement": items}}, en_bc((t["label"], "/en/insights/"))]
    en_page("/en/insights/", t["title"], t["description"], "insights", t["label"], body, ld=ld)

# 本文を HTML のまま持つページ（英語の policy・シンガポールの記事）は、<!--body--> と <!--/body--> の間を一字も変えずに残し、外枠だけ作る
BODY_MARK = re.compile(r"<!--body-->\n([\s\S]*?)<!--/body-->")
def kept_body(f):
    m = BODY_MARK.search(rd(f).replace("\r\n", "\n"))
    assert m, f"{f} に <!--body--> の印が無い"
    return m.group(1)
def build_en_policy():
    t = EN["policy"]; path = "/en/policy-2/"; f = "en/policy-2/index.html"
    ld = [webpage_ld(path, t["title"], t["description"], "en"), en_bc((t["label"], path))]
    html = head(t["title"], t["description"], path, ld, lang="en") + header("", path, "en") + f'<main id="main" class="inner-page">{crumb(t["label"], None, "en")}<div class="container legal-body">\n<!--body-->\n{kept_body(f)}<!--/body-->\n</div></main>\n' + footer(path, "en")
    wr(f, html)
def build_en_article():
    """シンガポールの GEO/AEO の記事。<head> と本文（<main class="article-wrap">）はそのまま。ヘッダー・フッターと site-chrome.css・site.js だけを足す。"""
    f = EN_ARTICLE.lstrip("/") + "index.html"
    src = rd(f).replace("\r\n", "\n")
    pre, rest = src.split("<head>\n", 1)
    head_in = rest.split("</head>", 1)[0]
    head_in = re.sub(r"[ \t]*<[^\n]*\sdata-frame[^\n]*\n", "", head_in)  # 前回この関数が足した行
    css = '<link rel="stylesheet" href="/styles.css">\n'
    assert css in head_in
    head_in = head_in.replace(css, css + '  <link rel="stylesheet" href="/site-chrome.css" data-frame>\n  <style data-frame>.site-header,.footer{line-height:1.5}.footer{margin-top:0}.footer nav a{color:#e0e8f5}</style>\n', 1) + '    <script defer src="/site.js" data-frame></script>\n'
    html = pre + "<head>\n" + head_in + "</head>\n<body>\n" + header("insights", EN_ARTICLE, "en") + f'<div id="main">\n<!--body-->\n{kept_body(f)}<!--/body-->\n</div>\n' + footer(EN_ARTICLE, "en")
    wr(f, html)
def build_en():
    build_en_top(); build_en_services(); build_en_aiaeo(); build_en_products(); build_en_about(); build_en_contact(); build_en_insights(); build_en_policy(); build_en_article()

# ================================================================= site.js
SITE_JS = r'''/* synapsearrows.com — static port of the Codex prototype (2026-10-27): menu, request form, analytics events */
(function () {
  var en = document.documentElement.lang === 'en';
  var t = document.querySelector('.menu-toggle'), m = document.getElementById('mobile-menu');
  if (t && m) t.addEventListener('click', function () { var open = m.hidden; m.hidden = !open; t.setAttribute('aria-expanded', open ? 'true' : 'false'); t.setAttribute('aria-label', open ? (en ? 'Close menu' : 'メニューを閉じる') : (en ? 'Open menu' : 'メニューを開く')); });
  // どこから進んだかを数える（Vercel Web Analytics・Cookie なし）。名前・メール・自由文・URL は送らない
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('[data-va]'); if (!a || !window.va) return;
    var d = {}; if (a.dataset.vaFrom) d.from = a.dataset.vaFrom; if (a.dataset.plan) d.plan = a.dataset.plan;
    window.va('event', { name: a.dataset.va, data: d });
  });
  var rf = document.getElementById('request-form');
  if (rf) {
    var count = document.getElementById('selection-count'), err = document.getElementById('request-error');
    function n() { return rf.querySelectorAll('input[name=service]:checked').length; }
    rf.addEventListener('change', function () { var k = n(); count.textContent = k ? (en ? k + ' selected' : k + '件のサービスを選択中') : ''; if (k) err.hidden = true; });
    rf.addEventListener('submit', function (e) { if (!n()) { e.preventDefault(); err.hidden = false; err.scrollIntoView({ block: 'center' }); } });
  }
})();
'''

# ================================================================= site-chrome.css（site.css の共通部分だけ）
ALLOWED = ("*", "html", "body", "button,input,textarea", "a", "button", "a,button", "button:focus-visible", "img", ".container",
           ".skip-link", ".site-header", ".header-inner", ".brand", ".desktop-nav", ".button", ".header-cta", ".button-outline",
           ".menu-toggle", ".mobile-nav", ".footer", ".brand-footer", ".text-link", ".eyebrow", ".page-actions", ".small-note",
           ".diagnosis-nav", ".diagnosis-page-hero", ".diagnosis-hero-grid", ".diagnosis-brand-art", ".inner-page .button",
           ".inner-page .text-link", ".inner-page .small-note", ".secondary", ".breadcrumb", "[hidden]", ".visually-hidden", ".lang-link", ".lang-link-mobile")
def _keep(sel):
    sel = sel.strip()
    if sel in ("p,h1,h2,h3", "h1", "h2") or sel.startswith("h1") or sel.startswith("h2"):
        return False
    return all(any(x.strip() == a or x.strip().startswith(a + " ") or x.strip().startswith(a + ":") or x.strip().startswith(a + ">") or x.strip().startswith(a + "[") or x.strip().startswith(a + ".") or x.strip().startswith(a + "+") for a in ALLOWED) for x in sel.split(","))
def _parse(block):
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", block):
        yield m.group(1).strip(), m.group(2).strip()
def build_chrome_css():
    """site.css から、ヘッダー・フッター・ボタン・AI映え診断のナビと見出しのルールだけを抜く（@media の中も同じ条件で）。"""
    src = re.sub(r"/\*.*?\*/", "", rd("site.css"), flags=re.S)
    out = []; pos = 0
    while pos < len(src):
        m = re.search(r"@media[^{]*\{", src[pos:])
        flat = src[pos: pos + m.start()] if m else src[pos:]
        for sel, body in _parse(flat):
            if _keep(sel): out.append(f"{sel}{{{body}}}")
        if not m: break
        start = pos + m.end(); depth = 1; i = start
        while depth and i < len(src):
            if src[i] == "{": depth += 1
            elif src[i] == "}": depth -= 1
            i += 1
        kept = [f"{sel}{{{body}}}" for sel, body in _parse(src[start:i - 1]) if _keep(sel)]
        if kept: out.append(m.group(0).rstrip("{").strip() + "{" + "".join(kept) + "}")
        pos = i
    chrome = ("/* Codex の試作の共通部分（ヘッダー・フッター・ボタン・AI映え診断のナビと見出し）だけ。\n   自前の CSS を持つページ（AI映え診断の本物の入力画面）用。全部入りは /site.css。scripts/build-site.py が site.css から作る（手で直さない） */\n"
              ":root{--blue:#0649ef;--navy:#102745;--rule:#bdcde5;--light:#edf7fd;--container:1230px}\n"
              ".site-header,.footer,.diagnosis-nav,.diagnosis-page-hero,.mobile-nav{font-family:'Noto Sans JP','Inter',-apple-system,BlinkMacSystemFont,sans-serif;color:#081b3b}\n"
              ".diagnosis-page-hero h1{font-size:52px;line-height:1.38;letter-spacing:-.04em;font-weight:820;margin:0}.diagnosis-page-hero h1>span{color:var(--blue)}\n"
              ".diagnosis-page-hero p{margin:0}.diagnosis-page-hero .page-actions .button{font-size:16px;min-height:54px;padding:13px 23px}.diagnosis-page-hero .text-link{font-size:16px}\n"
              "@media(max-width:1200px){.diagnosis-page-hero h1{font-size:43px}}@media(max-width:900px){.diagnosis-page-hero h1{font-size:37px}}@media(max-width:600px){.diagnosis-page-hero h1{font-size:33px;line-height:1.45}.diagnosis-page-hero .page-actions>.button{width:100%}}\n"
              + "\n".join(out) + "\n")
    wr("site-chrome.css", chrome)

PRICE_MARK = re.compile(r"<!--p:([^>]*?)-->[\s\S]*?<!--/p-->")
def check():
    """作った物と手元のファイルを比べる。値段の印 <!--p:K-->…<!--/p--> の中身は build-pricing.mjs の受け持ちなので見ない。"""
    bad = 0
    for p, html in OUT.items():
        cur = rd(p).replace("\r\n", "\n") if os.path.exists(ROOT + p) else ""
        if PRICE_MARK.sub(r"<!--p:\1--><!--/p-->", cur) != PRICE_MARK.sub(r"<!--p:\1--><!--/p-->", html):
            print(f"differs: {p}"); bad += 1
    if bad: sys.exit(1)
    print(f"ok: {len(OUT)} files match scripts/build-site.py")

if __name__ == "__main__":
    build_top(); build_services(); build_products(); build_tools(); build_about(); build_contact(); build_pricing(); build_flow(); build_insights()
    build_en()
    wr("site.js", SITE_JS)
    build_chrome_css()
    if CHECK: check()
    else: print(f"built {len(OUT)} files（値段は node scripts/build-pricing.mjs で流し込む）")
