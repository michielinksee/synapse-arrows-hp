# -*- coding: utf-8 -*-
"""業種別「AI が頼る先」調査の記事（insights/ai-sources-*/）を、scripts/site/industry-insights.json から作る（2026-11-02）。

骨組みは insights/tax-accountant-ai-recommendation-2026-09/index.html と同じ（/styles.css・同じ nav と footer・article-wrap）。
数字は PR TIMES の下書き（founder-ops/PRTIMES-Drafts_2026-09-30/city-series/*_下書き.md）と同じ物を JSON に写した。ここでは数字を作らない。
画像は insights/<slug>/img/*.webp（PR TIMES と同じ 7 枚）。

使い方:  python -X utf8 scripts/build-industry-insights.py        → 7 ページを書く
         python -X utf8 scripts/build-industry-insights.py --check → 書かずに差分の有無だけ（CI 用・差分があれば 1）
"""
import io, json, os, sys, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + os.sep
SITE = "https://synapsearrows.com"
DATA = json.load(io.open(ROOT + "scripts/site/industry-insights.json", encoding="utf-8"))

def esc(s): return H.escape(s, quote=True)
def ldjson(o): return '<script type="application/ld+json">\n' + json.dumps(o, ensure_ascii=False, indent=2).replace("</", "<\\/") + "\n</script>"

STYLE = """  <style>
    .article-wrap{max-width:900px;margin:0 auto;padding:56px 24px 88px}.article-wrap h1{font-size:clamp(1.9rem,4.6vw,3rem);line-height:1.3;letter-spacing:-.02em;margin:16px 0}.article-wrap h2{font-size:1.5rem;margin:52px 0 16px}.article-wrap h3{font-size:1.15rem;margin:30px 0 10px}.article-wrap p,.article-wrap li{font-size:1.02rem;line-height:1.9;color:#334155}.article-wrap a{color:var(--primary);text-decoration:underline}.article-meta{color:#64748b;font-size:.9rem;margin-bottom:28px}.eyebrow{color:var(--primary);font-weight:700;letter-spacing:.08em;text-transform:uppercase;font-size:.8rem}
    .disclose{background:#fffbeb;border:1px solid #fde68a;border-radius:14px;padding:18px 22px;margin:24px 0}.disclose p{color:#78350f;font-size:.95rem;margin:0}
    .summary{background:var(--accent);border-radius:16px;padding:22px 26px;margin:24px 0}.summary ul{margin:8px 0 0;padding-left:20px}
    .tbl-wrap{overflow-x:auto;margin:20px 0;border:1px solid var(--border);border-radius:12px}.tbl-wrap table{border-collapse:collapse;width:100%;font-size:.92rem}.tbl-wrap th,.tbl-wrap td{padding:10px 14px;border-bottom:1px solid var(--border);text-align:left;vertical-align:top;line-height:1.6}.tbl-wrap th{background:var(--bg-light);font-weight:700;white-space:nowrap}.tbl-wrap tr:last-child td{border-bottom:0}.tbl-wrap td.num{text-align:right;font-variant-numeric:tabular-nums}
    .bars{margin:20px 0}.bar{display:grid;grid-template-columns:220px 1fr 56px;gap:12px;align-items:center;margin:8px 0;font-size:.95rem}.bar i{display:block;height:18px;border-radius:9px;background:var(--primary)}.bar b{text-align:right}@media(max-width:640px){.bar{grid-template-columns:1fr 56px}.bar i{grid-column:1/-1;order:3}}
    .cta-box{background:linear-gradient(135deg,var(--bg-dark) 0%,#111936 100%);color:#fff;border-radius:16px;padding:28px 30px;margin:36px 0}.cta-box h3{color:#fff;margin:0 0 8px}.cta-box p{color:#cbd5e1;margin:0 0 16px}.cta-box a{color:#fff}
    .note{font-size:.88rem!important;color:#64748b!important}
    .article-wrap figure{margin:24px 0}.article-wrap figure img{width:100%;height:auto;border:1px solid var(--border);border-radius:12px;display:block}.article-wrap figcaption{font-size:.88rem;color:#64748b;margin-top:8px}
    .series-nav{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px;margin:20px 0}.series-nav a{display:block;border:1px solid var(--border);border-radius:12px;padding:14px 16px;text-decoration:none!important;color:inherit}.series-nav a:hover{border-color:var(--primary)}.series-nav a.current{background:var(--bg-light)}.series-nav a span{display:block;color:#64748b;font-size:.82rem;margin-bottom:4px}.series-nav a strong{color:var(--primary)}
    .lead-quote{font-size:1.15rem;font-weight:600;color:#0f172a;border-left:4px solid var(--primary);padding:6px 0 6px 18px;margin:20px 0}
  </style>"""

NAV = '''  <header><nav class="nav"><div class="container nav-inner"><a href="/" class="nav-logo"><img src="/logo.png" alt="Synapse Arrows" width="32" height="32">Synapse Arrows</a><ul class="nav-links"><li><a href="/services/">事業紹介・サービス</a></li><li><a href="/products/">プロダクト</a></li><li><a href="/insights/" class="active">Insights</a></li><li><a href="/about/">会社概要</a></li><li><a href="/ai-bae-shindan/" class="nav-cta nav-cta-ai">AI映え診断</a></li><li><a href="/contact/" class="nav-cta">資料請求・ご相談</a></li></ul><button class="mobile-menu-btn" aria-label="Menu"><span></span><span></span><span></span></button></div></nav></header>'''
FOOT = '''  <footer class="footer"><div class="container footer-inner"><div class="footer-logo">Synapse Arrows Pte. Ltd</div><ul class="footer-links"><li><a href="https://kansei-link.com" target="_blank" rel="noopener">KanseiLINK</a></li><li><a href="/insights/">Insights</a></li><li><a href="/services/ai-aeo/">AI推薦診断・料金</a></li><li><a href="/policy/">Privacy</a></li><li><a href="/terms/">Terms</a></li></ul><div class="footer-copy">&copy; 2026 Synapse Arrows Pte. Ltd. All rights reserved.</div></div></footer>
  <script>document.querySelector('.mobile-menu-btn').addEventListener('click',function(){const n=document.querySelector('.nav-links');n.style.display=n.style.display==='flex'?'none':'flex';n.style.flexDirection='column';n.style.position='absolute';n.style.top='72px';n.style.left='0';n.style.right='0';n.style.background='#fff';n.style.padding='20px';});</script>'''

def md(s):
    """**x** → <strong>x</strong>。それ以外はエスケープ。[text](url) はリンク。"""
    import re
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: f'<a href="{m.group(2)}"{" target=_blank rel=noopener" if m.group(2).startswith("http") and not m.group(2).startswith(SITE) else ""}>{m.group(1)}</a>', s)
    return s

def figure(slug, img, cap, alt):
    return f'<figure><img src="/insights/{slug}/img/{img}.webp" alt="{esc(alt)}" width="1536" height="1024" loading="lazy"><figcaption>{md(cap)}</figcaption></figure>'

def bars(rows, suffix="%"):
    mx = max(v for _, v in rows) or 1
    return '<div class="bars">' + "".join(f'<div class="bar"><span>{md(l)}</span><i style="width:{max(2, round(v / mx * 100))}%"></i><b>{v:g}{suffix}</b></div>' for l, v in rows) + "</div>"

def table(cols, rows, num_from=1):
    th = "".join(f"<th>{md(c)}</th>" for c in cols)
    trs = "".join("<tr>" + "".join(f'<td{" class=num" if i >= num_from and isinstance(v, (int, float)) else ""}>{v if isinstance(v, (int, float)) else md(str(v))}</td>' for i, v in enumerate(r)) + "</tr>" for r in rows)
    return f'<div class="tbl-wrap"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>'

def block(slug, b):
    t = b["type"]
    if t == "p": return f"<p>{md(b['text'])}</p>"
    if t == "note": return f'<p class="note">{md(b["text"])}</p>'
    if t == "quote": return f'<p class="lead-quote">{md(b["text"])}</p>'
    if t == "h2": return f"<h2>{md(b['text'])}</h2>"
    if t == "h3": return f"<h3>{md(b['text'])}</h3>"
    if t == "ul": return "<ul>" + "".join(f"<li>{md(x)}</li>" for x in b["items"]) + "</ul>"
    if t == "ol": return "<ol>" + "".join(f"<li>{md(x)}</li>" for x in b["items"]) + "</ol>"
    if t == "figure": return figure(slug, b["img"], b["caption"], b.get("alt", b["caption"]))
    if t == "bars": return bars([(r[0], r[1]) for r in b["rows"]], b.get("suffix", "%"))
    if t == "table": return table(b["cols"], b["rows"], b.get("num_from", 1))
    if t == "cta":
        return f'<div class="cta-box"><h3>{md(b["title"])}</h3><p>{md(b["text"])}</p><a href="{b["href"]}">{md(b["label"])} →</a></div>'
    raise ValueError(t)

def series_nav(current):
    items = ""
    for a in DATA["articles"]:
        cls = ' class="current"' if a["slug"] == current else ""
        items += f'<a href="/insights/{a["slug"]}/"{cls}><span>{esc(a["series_label"])}</span><strong>{esc(a["nav_title"])}</strong></a>'
    return f'<nav class="series-nav" aria-label="業種別の調査">{items}</nav>'

def page(a):
    slug, url = a["slug"], f"{SITE}/insights/{a['slug']}/"
    title, desc = a["title"], a["description"]
    og = f"{SITE}/insights/{slug}/img/00_main.webp"
    # 英語版がある記事は hreflang の対を張る（scripts/check-site.mjs が双方向かを見る）
    alt = "".join(f'\n  <link rel="alternate" hreflang="{k}" href="{v}">' for k, v in (("ja", url), ("en", SITE + a["en"]), ("x-default", url))) if a.get("en") else ""
    body = []
    body.append(f'<div class="eyebrow">Insights · {esc(a["eyebrow"])}</div>')
    body.append(f"<h1>{esc(title)}</h1>")
    body.append(f'<div class="article-meta"><time datetime="{a["date"]}">{a["date_ja"]}</time> · Synapse Arrows</div>')
    if a.get("en"): body.append(f'<p class="note">English version: <a href="{a["en"]}" hreflang="en" lang="en">{esc(a["en_title"])}</a></p>')
    body.append(f'<div class="disclose"><p><strong>この調査について：</strong>{md(a["disclose"])}</p></div>')
    for b in a["lead"]: body.append(block(slug, b))
    body.append('<div class="summary"><strong>分かったこと</strong><ul>' + "".join(f"<li>{md(x)}</li>" for x in a["summary"]) + "</ul></div>")
    for b in a["body"]: body.append(block(slug, b))
    body.append("<h2>このシリーズの記事</h2>")
    body.append(series_nav(slug))
    body.append("<h2>よくある質問</h2>")
    for q, ans in a["faq"]: body.append(f"<h3>{md(q)}</h3><p>{md(ans)}</p>")
    body.append("<h2>この調査の限界</h2>")
    for x in a["limits"]: body.append(f"<p>{md(x)}</p>")
    if a.get("prtimes"):
        body.append(f'<p>この調査は <a href="{a["prtimes"]}" target="_blank" rel="noopener">PR TIMES</a> でも配信しています。</p>')
    body.append(f'<p class="note">{md(DATA["common_note"])}</p>')

    faq_ld = {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": ans.replace("**", "")}} for q, ans in a["faq"]]}
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "Organization", "@id": SITE + "/#organization", "name": "Synapse Arrows Pte. Ltd.", "url": SITE, "logo": SITE + "/logo.png"},
        {"@type": "Article", "@id": url + "#article", "headline": title, "description": desc, "image": og, "datePublished": a["date"], "dateModified": a["date"], "inLanguage": "ja", "mainEntityOfPage": url, "author": {"@id": SITE + "/#organization"}, "publisher": {"@id": SITE + "/#organization"}, "about": a["about"]},
        {"@type": "Dataset", "name": a["dataset_name"], "description": a["dataset_desc"], "creator": {"@id": SITE + "/#organization"}, "license": "https://creativecommons.org/licenses/by/4.0/", "datePublished": a["date"], "url": url},
        faq_ld,
        {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "ホーム", "item": SITE + "/"}, {"@type": "ListItem", "position": 2, "name": "Insights・記事", "item": SITE + "/insights/"}, {"@type": "ListItem", "position": 3, "name": title, "item": url}]},
    ]}
    doc = f'''<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(title)} | Synapse Arrows</title>
  <meta name="description" content="{esc(desc)}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{url}">{alt}
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="Synapse Arrows">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(desc)}">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="{og}">
  <meta property="og:image:width" content="1536">
  <meta property="og:image:height" content="1024">
  <meta property="article:published_time" content="{a["date"]}">
  <meta property="article:modified_time" content="{a["date"]}">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+JP:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="icon" href="/favicon.png" type="image/png">
  <link rel="stylesheet" href="/styles.css">
  <script>window.va=window.va||function(){{(window.vaq=window.vaq||[]).push(arguments)}};</script>
  <script defer src="/_vercel/insights/script.js"></script>
  {ldjson(ld)}
{STYLE}
</head>
<body>
{NAV}
  <main class="article-wrap">
    {chr(10).join("    " + x for x in body).strip()}
  </main>
{FOOT}
</body>
</html>
'''
    return doc

def main():
    check = "--check" in sys.argv
    diff = 0
    for a in DATA["articles"]:
        p = ROOT + f"insights/{a['slug']}/index.html"
        doc = page(a)
        old = io.open(p, encoding="utf-8").read() if os.path.exists(p) else None
        if old != doc:
            diff += 1
            if not check:
                os.makedirs(os.path.dirname(p), exist_ok=True)
                io.open(p, "w", encoding="utf-8", newline="\n").write(doc)
                print("wrote", p[len(ROOT):])
    if check:
        print("industry-insights: up to date" if diff == 0 else f"industry-insights: {diff} page(s) differ — run scripts/build-industry-insights.py")
        sys.exit(1 if diff else 0)

if __name__ == "__main__":
    main()
