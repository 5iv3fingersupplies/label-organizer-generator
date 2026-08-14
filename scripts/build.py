from __future__ import annotations
import argparse, html, json, os, shutil
from datetime import date
from pathlib import Path
from urllib.parse import quote_plus

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ASSETS = ROOT / "assets"

def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))

def esc(value):
    return html.escape(str(value), quote=True)

def rel(depth, target):
    return "../" * depth + target

def depth(path):
    if path == "index.html":
        return 0
    return len([p for p in path.split("/") if p]) - 1

def absolute(base, path):
    clean = path.replace("index.html", "").strip("/")
    return base.rstrip("/") + ("/" if not clean else "/" + clean + "/")

def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")

def affiliate_href(monetization, query):
    if not monetization.get("amazon_search_links_enabled"):
        return ""
    tag = monetization.get("amazon_associates_tag", "").strip()
    if not tag:
        return ""
    return f"https://www.amazon.com/s?k={quote_plus(query)}&tag={quote_plus(tag)}"

def layout(site, monetization, title, description, path, body, extra_js=False):
    d = depth(path)
    url = absolute(site["base_url"], path)
    schema = {"@context": "https://schema.org", "@type": "WebPage", "name": title, "description": description, "url": url, "publisher": {"@type": "Organization", "name": site["brand"]}}
    tools_js = f'\n<script src="{rel(d, "assets/js/tools.js")}" defer></script>' if extra_js else ""
    return f"""<!doctype html>
<html lang="en-US">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} | {esc(site["name"])}</title><meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(url)}"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:url" content="{esc(url)}"><meta property="og:type" content="website">
<link rel="stylesheet" href="{rel(d, "assets/css/site.css")}"><script type="application/ld+json">{json.dumps(schema)}</script></head>
<body><a class="skip-link" href="#main">Skip to content</a><header class="topbar"><nav class="nav" aria-label="Main navigation"><a class="brand" href="{rel(d, "index.html")}"><span class="brand-mark">AI</span>{esc(site["name"])}</a><div class="nav-links"><a href="{rel(d, "tools/index.html")}">Tools</a><a href="{rel(d, "guides/index.html")}">Guides</a><a href="{rel(d, "monetization/index.html")}">Monetization</a><a href="{rel(d, "privacy/index.html")}">Privacy</a></div></nav></header>
<div class="ribbon"><div class="inner">{monetization["disclosure"]}</div></div><main id="main">{body}</main><footer class="footer"><div class="wrap"><div><strong>{esc(site["name"])}</strong><p class="fineprint">{esc(site["model"])}</p></div><div class="nav-links"><a href="{rel(d, "about/index.html")}">About</a><a href="{rel(d, "sitemap.xml")}">Sitemap</a></div></div></footer>{tools_js}</body></html>"""

def card(title, description, href, tag=""):
    tag_html = f'<span class="tag">{esc(tag)}</span>' if tag else ""
    return f'<article class="card">{tag_html}<h3><a href="{esc(href)}">{esc(title)}</a></h3><p>{esc(description)}</p></article>'

def recommendation_cards(ids, recs, monetization):
    rows = []
    for rec_id in ids:
        rec = recs[rec_id]
        href = affiliate_href(monetization, rec["query"])
        action = f'<a class="button" href="{esc(href)}" rel="sponsored nofollow noopener" data-affiliate="{esc(rec_id)}">Open option search</a>' if href else '<a class="button disabled" href="#" aria-disabled="true">Link inactive</a>'
        rows.append(f'<article class="card"><span class="tag">Fit</span><h3>{esc(rec["label"])}</h3><p>{esc(rec["fit"])}</p>{action}</article>')
    return "".join(rows)

def render_fields(fields):
    rows = []
    for f in fields:
        attrs = f'name="{esc(f["id"])}" id="{esc(f["id"])}"'
        if f["type"] == "select":
            control = f'<select {attrs}>' + "".join(f'<option value="{esc(o)}">{esc(o)}</option>' for o in f["options"]) + '</select>'
        elif f["type"] == "textarea":
            control = f'<textarea {attrs} rows="5">{esc(f.get("value",""))}</textarea>'
        elif f["type"] == "text":
            control = f'<input type="text" {attrs} value="{esc(f.get("value",""))}">'
        else:
            control = f'<input type="number" {attrs} value="{esc(f.get("value",0))}">'
        rows.append(f'<label for="{esc(f["id"])}">{esc(f["label"])}{control}</label>')
    return "".join(rows)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="site")
    args = parser.parse_args()
    out = (ROOT / args.out).resolve()
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    site, monetization = load("site.json"), load("monetization.json")
    tools, guides = load("tools.json"), load("guides.json")
    recs = {r["id"]: r for r in load("recommendations.json")}
    shutil.copytree(ASSETS, out / "assets")
    tool_cards = "".join(card(t["title"], t["description"], f'tools/{t["slug"]}/index.html', t["category"]) for t in tools)
    guide_cards = "".join(card(g["title"], g["description"], f'guides/{g["slug"]}/index.html', g["category"]) for g in guides[:6])
    visual = "".join(f"<div>{esc(c)}</div>" for c in sorted({t["category"] for t in tools}))
    home = f'<section class="hero"><div><span class="tag">Autonomous tool site</span><h1>{esc(site["name"])}</h1><p>{esc(site["tagline"])}</p><div class="hero-actions"><a class="button" href="tools/index.html">Use tools</a><a class="button secondary" href="guides/index.html">Browse guides</a></div></div><div class="visual">{visual}</div></section><section class="band"><div class="wrap"><h2 class="section-title">Tools</h2><div class="grid">{tool_cards}</div></div></section><section class="band"><div class="wrap"><h2 class="section-title">Guides</h2><div class="grid">{guide_cards}</div></div></section>'
    write(out / "index.html", layout(site, monetization, site["name"], site["tagline"], "index.html", home))
    write(out / "tools/index.html", layout(site, monetization, "Tools", "Interactive browser-only tools.", "tools/index.html", f'<section class="page-head"><h1>Tools</h1><p>Use these calculators and generators before buying supplies or templates.</p></section><section class="wrap"><div class="grid">{tool_cards.replace("tools/","")}</div></section>'))
    for t in tools:
        rec_html = recommendation_cards(t["recommendation_ids"], recs, monetization)
        body = f'<section class="page-head"><span class="tag">{esc(t["category"])}</span><h1>{esc(t["title"])}</h1><p>{esc(t["description"])}</p></section><section class="content tool-shell"><div class="tool-panel"><form class="tool-form" data-calculator="{esc(t["kind"])}">{render_fields(t["fields"])}<button type="submit">Generate</button></form></div><div class="result-box" aria-live="polite"><p>Enter your numbers and generate a result.</p></div></section><section class="band"><div class="wrap"><h2 class="section-title">Product-fit links</h2><div class="grid">{rec_html}</div></div></section>'
        write(out / f'tools/{t["slug"]}/index.html', layout(site, monetization, t["title"], t["description"], f'tools/{t["slug"]}/index.html', body, True))
    guide_index_cards = "".join(card(g["title"], g["description"], f'{g["slug"]}/index.html', g["category"]) for g in guides)
    write(out / "guides/index.html", layout(site, monetization, "Guides", "Evergreen supporting pages.", "guides/index.html", f'<section class="page-head"><h1>Guides</h1><p>Evergreen support pages for the tools and monetized link slots.</p></section><section class="wrap"><div class="grid">{guide_index_cards}</div></section>'))
    for g in guides:
        sections = "".join("<h2>{}</h2><p>{}</p><ul>{}</ul>".format(esc(s["heading"]), esc(s["body"]), "".join(f"<li>{esc(b)}</li>" for b in s["bullets"])) for s in g["sections"])
        write(out / f'guides/{g["slug"]}/index.html', layout(site, monetization, g["title"], g["description"], f'guides/{g["slug"]}/index.html', f'<section class="page-head"><span class="tag">{esc(g["category"])}</span><h1>{esc(g["title"])}</h1><p>{esc(g["description"])}</p></section><article class="content">{sections}</article>'))
    static = {
        "about": ("About", f"{site['name']} is a browser-only static tool business with external monetization links."),
        "privacy": ("Privacy", "This site does not use accounts, comments, payment forms, server analytics, or paid tracking. Calculator inputs stay in the browser."),
        "monetization": ("Monetization", monetization["disclosure"] + " The site does not display Amazon reviews, ratings, prices, availability, or images. Checkout links are handled by external no-monthly-fee storefronts when configured."),
    }
    for slug, (title, text) in static.items():
        write(out / f"{slug}/index.html", layout(site, monetization, title, text, f"{slug}/index.html", f'<section class="page-head"><h1>{esc(title)}</h1><p>{esc(text)}</p></section>'))
    paths = [str(p.relative_to(out)).replace("\\", "/") for p in out.rglob("*.html")]
    urls = "\n".join(f"<url><loc>{esc(absolute(site['base_url'], p))}</loc><lastmod>{date.today().isoformat()}</lastmod></url>" for p in sorted(paths))
    write(out / "sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}\n</urlset>\n')
    write(out / "robots.txt", f"User-agent: *\nAllow: /\nSitemap: {site['base_url'].rstrip()}/sitemap.xml\n")
    print(json.dumps({"status": "ok", "html_pages": len(paths), "tools": len(tools), "guides": len(guides)}, indent=2))

if __name__ == "__main__":
    main()
