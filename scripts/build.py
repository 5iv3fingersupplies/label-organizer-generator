from __future__ import annotations
import argparse, html, json, shutil
from datetime import date
from pathlib import Path
from urllib.parse import quote_plus

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ASSETS = ROOT / "assets"

def load(name, default=None):
    path = DATA / name
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))

def esc(value):
    return html.escape(str(value), quote=True)

def slugify(value):
    return "-".join(replace for replace in "".join(c.lower() if c.isalnum() else "-" for c in str(value)).split("-") if replace)

def rel(depth, target):
    return "../" * depth + target

def depth(path):
    if path == "index.html":
        return 0
    return len([p for p in path.split("/") if p]) - 1

def absolute(base, path):
    clean = path.replace("index.html", "").strip("/")
    if not clean:
        return base.rstrip("/") + "/"
    suffix = "" if "." in clean.rsplit("/", 1)[-1] else "/"
    return base.rstrip("/") + "/" + clean + suffix

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

def layout(site, monetization, title, description, path, body, extra_js=False, page_type="WebPage"):
    design = load("design.json", {"short":"FF","accent":"#0f766e","secondary":"#1d4ed8","warm":"#f59e0b","surface":"#f8fbff","soft":"#eaf2ff","primary_cta":"Start","promise":site["tagline"]})
    d = depth(path)
    url = absolute(site["base_url"], path)
    image = absolute(site["base_url"], "assets/img/hero-v2.png")
    schema = {"@context": "https://schema.org", "@type": page_type, "name": title, "description": description, "url": url, "publisher": {"@type": "Organization", "name": site["brand"]}}
    tools_js = f'\n<script src="{rel(d, "assets/js/tools.js")}" defer></script>' if extra_js else ""
    return f'''<!doctype html>
<html lang="en-US">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} | {esc(site["name"])}</title><meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(url)}"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:url" content="{esc(url)}"><meta property="og:image" content="{esc(image)}"><meta property="og:type" content="website">
<meta name="theme-color" content="{esc(design["accent"])}"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{esc(image)}"><link rel="alternate" type="application/atom+xml" title="{esc(site["name"])} updates" href="{rel(d, "feed.xml")}"><link rel="stylesheet" href="{rel(d, "assets/css/site.css")}"><script type="application/ld+json">{json.dumps(schema)}</script></head>
<body style="--accent:{esc(design['accent'])};--secondary:{esc(design['secondary'])};--warm:{esc(design['warm'])};--surface:{esc(design['surface'])};--soft:{esc(design['soft'])}"><a class="skip-link" href="#main">Skip to content</a><header class="topbar"><nav class="nav" aria-label="Main navigation"><a class="brand" href="{rel(d, "index.html")}"><span class="brand-mark">{esc(design["short"])}</span>{esc(site["name"])}</a><div class="nav-links"><a href="{rel(d, "start-here/index.html")}">Start</a><a href="{rel(d, "tools/index.html")}">Tools</a><a href="{rel(d, "seasonal/index.html")}">Seasonal</a><a href="{rel(d, "guides/index.html")}">Guides</a><a href="{rel(d, "recommendations/index.html")}">Fit</a><a class="nav-cta" href="{rel(d, "tools/index.html")}">{esc(design["primary_cta"])}</a></div></nav></header>
<div class="ribbon"><div class="inner">{monetization["disclosure"]}</div></div><main id="main">{body}</main><footer class="footer"><div class="wrap"><div><strong>{esc(site["name"])}</strong><p class="fineprint">{esc(site["model"])}</p></div><div class="nav-links"><a href="{rel(d, "about/index.html")}">About</a><a href="{rel(d, "publisher-standards/index.html")}">Standards</a><a href="{rel(d, "monetization/index.html")}">Monetization</a><a href="{rel(d, "feed.xml")}">RSS</a><a href="{rel(d, "sitemap.xml")}">Sitemap</a></div></div></footer>{tools_js}</body></html>'''

def card(title, description, href, tag=""):
    tag_html = f'<span class="tag">{esc(tag)}</span>' if tag else ""
    return f'<article class="card">{tag_html}<h3><a href="{esc(href)}">{esc(title)}</a></h3><p>{esc(description)}</p></article>'

def recommendation_cards(ids, recs, monetization, prefix=""):
    rows = []
    for rec_id in ids:
        rec = recs[rec_id]
        href = affiliate_href(monetization, rec["query"])
        action = f'<a class="button" href="{esc(href)}" rel="sponsored nofollow noopener" data-affiliate="{esc(rec_id)}">Open option search</a>' if href else '<a class="button disabled" href="#" aria-disabled="true">Link inactive</a>'
        rows.append(f'<article class="card"><span class="tag">Fit</span><h3>{esc(rec["label"])}</h3><p>{esc(rec["fit"])}</p><div class="card-actions"><a class="button secondary" href="{esc(prefix)}recommendations/{esc(rec_id)}/index.html">Read fit notes</a>{action}</div></article>')
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

def related_tools_for_rec(tools, rec_id):
    return [t for t in tools if rec_id in t.get("recommendation_ids", [])]

def related_guides(guides, category, limit=4):
    matches = [g for g in guides if g["category"] == category]
    return matches[:limit] if matches else guides[:limit]

def bullet_list(items):
    return "<ul>" + "".join(f"<li>{esc(item)}</li>" for item in items) + "</ul>"

def recommendation_page(site, monetization, rec, tools, guides):
    related = related_tools_for_rec(tools, rec["id"])
    category = related[0]["category"] if related else "Buying"
    guide_links = "".join(card(g["title"], g["description"], f'../../guides/{g["slug"]}/index.html', g["category"]) for g in related_guides(guides, category, 3))
    tool_links = "".join(card(t["title"], t["description"], f'../../tools/{t["slug"]}/index.html', t["category"]) for t in related[:4])
    href = affiliate_href(monetization, rec["query"])
    action = f'<a class="button" href="{esc(href)}" rel="sponsored nofollow noopener" data-affiliate="{esc(rec["id"])}">Open option search</a>' if href else ""
    checks = [
        "Measure the space, count, or capacity the item must support before shopping.",
        "Prefer clear manufacturer dimensions, materials, compatibility notes, and care instructions.",
        "Avoid buying a broad bundle when one focused item solves the job.",
        "Confirm the item fits the tool result or checklist before leaving the page."
    ]
    avoid = [
        "The product page does not explain size, material, included parts, or intended use.",
        "The item adds a maintenance burden that the workflow does not need.",
        "The accessory depends on a different device, format, paper size, voltage, or container size.",
        "You are buying it only because it looks convenient, not because the calculator result calls for it."
    ]
    body = f'''<section class="page-head"><span class="tag">Product fit</span><h1>{esc(rec["label"])}</h1><p>{esc(rec["fit"])}</p></section>
<article class="content"><div class="notice"><strong>Decision rule:</strong> Use this page to decide whether this product type fits the job. It does not use Amazon images, shopper score data, live availability, or live cost data.</div>
<h2>Best fit</h2><p>{esc(rec["label"])} works best when the buying decision is tied to a real measurement, repeatable task, or storage constraint instead of impulse browsing.</p>
<h2>Before buying</h2>{bullet_list(checks)}
<h2>When to skip it</h2>{bullet_list(avoid)}
<h2>Next step</h2><p>Use the related calculator or checklist first, then open the product-fit search only if the result confirms the need.</p>{action}</article>
<section class="band"><div class="wrap"><h2 class="section-title">Related tools</h2><div class="grid">{tool_links or "<p>No related tool yet.</p>"}</div></div></section>
<section class="band"><div class="wrap"><h2 class="section-title">Related guides</h2><div class="grid">{guide_links}</div></div></section>'''
    return body

def tool_plan_page(site, monetization, tool, recs):
    rec_cards = recommendation_cards(tool["recommendation_ids"], recs, monetization, "../../")
    inputs = [f["label"] for f in tool["fields"]]
    body = f'''<section class="page-head"><span class="tag">Tool plan</span><h1>{esc(tool["title"])} buying plan</h1><p>A step-by-step way to use the calculator result before buying supplies.</p></section>
<article class="content"><h2>Use this when</h2><p>{esc(tool["description"])} This planning page turns the calculator result into a smaller, lower-risk shopping list.</p>
<h2>Inputs to confirm</h2>{bullet_list(inputs)}
<h2>Decision sequence</h2>{bullet_list(["Run the calculator with conservative inputs.", "Write down the resulting count, size, or capacity.", "Compare that result with manufacturer dimensions and included-part details.", "Buy the narrowest item category that solves the measured need."])}
<h2>Common overbuying traps</h2>{bullet_list(["Buying multi-packs before the workflow is proven.", "Choosing a larger size because it feels safer.", "Ignoring storage, cleanup, charging, or refill requirements."])}</article>
<section class="band"><div class="wrap"><h2 class="section-title">Product-fit links</h2><div class="grid">{rec_cards}</div></div></section>'''
    return body

def checklist_page(site, guide):
    items = []
    for section in guide["sections"]:
        items.extend(section.get("bullets", []))
    items.extend(["Open the related calculator before buying.", "Save the final measurement or count.", "Recheck the setup after the first use."])
    boxes = "".join(f'<label class="check-row"><input type="checkbox"> <span>{esc(item)}</span></label>' for item in items[:12])
    return f'''<section class="page-head"><span class="tag">Printable checklist</span><h1>{esc(guide["title"])} checklist</h1><p>A print-friendly setup checklist based on the guide.</p></section>
<article class="content checklist"><p>Use this checklist as a quick pre-shopping pass. It is designed to reduce unnecessary purchases and keep the workflow simple.</p>{boxes}<p><a class="button secondary" href="#" onclick="window.print();return false;">Print checklist</a></p></article>'''

def category_page(category, tools, guides, recs, monetization):
    t_matches = [t for t in tools if t["category"] == category]
    g_matches = [g for g in guides if g["category"] == category]
    rec_ids = []
    for t in t_matches:
        rec_ids.extend(t.get("recommendation_ids", []))
    rec_ids = list(dict.fromkeys(rec_ids))[:6]
    tool_cards = "".join(card(t["title"], t["description"], f'../../tools/{t["slug"]}/index.html', t["category"]) for t in t_matches)
    guide_cards = "".join(card(g["title"], g["description"], f'../../guides/{g["slug"]}/index.html', g["category"]) for g in g_matches[:6])
    rec_cards = recommendation_cards(rec_ids, recs, monetization, "../../")
    return f'''<section class="page-head"><span class="tag">Topic hub</span><h1>{esc(category)} tools and checklists</h1><p>Calculator-first pages for this topic cluster.</p></section>
<section class="band"><div class="wrap"><h2 class="section-title">Tools</h2><div class="grid">{tool_cards or "<p>More tools are queued for this topic.</p>"}</div></div></section>
<section class="band"><div class="wrap"><h2 class="section-title">Guides</h2><div class="grid">{guide_cards or "<p>More guides are queued for this topic.</p>"}</div></div></section>
<section class="band"><div class="wrap"><h2 class="section-title">Product-fit links</h2><div class="grid">{rec_cards}</div></div></section>'''


def seasonal_page(entry, tools_by_slug, guides_by_slug, recs, monetization):
    tool_cards = "".join(card(t["title"], t["description"], f'../../tools/{t["slug"]}/index.html', t["category"]) for t in (tools_by_slug[s] for s in entry.get("tool_slugs", []) if s in tools_by_slug))
    guide_cards = "".join(card(g["title"], g["description"], f'../../guides/{g["slug"]}/index.html', g["category"]) for g in (guides_by_slug[s] for s in entry.get("guide_slugs", []) if s in guides_by_slug))
    rec_cards = recommendation_cards([rid for rid in entry.get("recommendation_ids", []) if rid in recs], recs, monetization, "../../")
    return f'''<section class="page-head"><span class="tag">Seasonal intent</span><h1>{esc(entry["title"])}</h1><p>{esc(entry["description"])}</p></section>
<article class="content"><div class="notice"><strong>Why now:</strong> {esc(entry["reason"])}</div>
<h2>Decision prompts</h2>{bullet_list(entry.get("decision_prompts", []))}
<h2>Use this sequence</h2>{bullet_list(["Open the calculator before browsing.", "Use the matching guide or checklist to catch setup details.", "Open a product-fit link only when the need is specific.", "Bookmark or follow the feed for the next seasonal pass."])}
<h2>Skip these traps</h2>{bullet_list(entry.get("avoid_prompts", []))}</article>
<section class="band"><div class="wrap"><h2 class="section-title">Tools for this moment</h2><div class="grid">{tool_cards}</div></div></section>
<section class="band alt"><div class="wrap"><h2 class="section-title">Supporting guides</h2><div class="grid">{guide_cards}</div></div></section>
<section class="band"><div class="wrap"><h2 class="section-title">Product-fit links</h2><div class="grid">{rec_cards}</div></div></section>'''

def start_here_page(site, tools, guides, editorial):
    first_tools = "".join(card(t["title"], t["description"], f'../tools/{t["slug"]}/index.html', t["category"]) for t in tools[:3])
    first_guides = "".join(card(g["title"], g["description"], f'../guides/{g["slug"]}/index.html', g["category"]) for g in guides[:3])
    seasonal = editorial.get("seasonal_pages", [])[:3]
    seasonal_cards = "".join(card(e["title"], e["description"], f'../seasonal/{e["slug"]}/index.html', e["month"]) for e in seasonal)
    return f'''<section class="page-head"><span class="tag">Start here</span><h1>Pick the fastest path to a useful decision</h1><p>{esc(site["tagline"])} Start with a calculator, confirm the details, then open only the product-fit links that match the result.</p></section>
<section class="decision-band"><div class="decision-steps"><div class="step"><strong>1. Search intent</strong><span>Choose the page that matches the job.</span></div><div class="step"><strong>2. Calculator proof</strong><span>Use numbers before product browsing.</span></div><div class="step"><strong>3. Lower friction</strong><span>No account, no checkout, and local inputs.</span></div></div></section>
<section class="band"><div class="wrap"><h2 class="section-title">Best first tools</h2><div class="grid">{first_tools}</div></div></section>
<section class="band alt"><div class="wrap"><h2 class="section-title">Seasonal entry points</h2><div class="grid">{seasonal_cards}</div></div></section>
<section class="band"><div class="wrap"><h2 class="section-title">Trust-building guides</h2><div class="grid">{first_guides}</div></div></section>'''

def publisher_standards_page(site, editorial):
    channels = editorial.get("traffic_channels", [])
    rows = "".join(f'<li><strong>{esc(item["channel"])}:</strong> {esc(item["implementation"])}</li>' for item in channels)
    standards = [
        "Every monetized page carries the Amazon Associate disclosure.",
        "Product-fit links use public search destinations instead of rehosted marketplace content.",
        "Calculator inputs stay in the visitor browser.",
        "No paid placement is accepted inside the automated build.",
        "Volatile marketplace details are omitted unless a permitted source can verify them during the build.",
    ]
    return f'''<section class="page-head"><span class="tag">Publisher standards</span><h1>How this site earns trust before clicks</h1><p>{esc(site["name"])} is built as a self-serve publisher property: useful pages first, disclosed affiliate links second.</p></section>
<article class="content"><h2>Operating standards</h2>{bullet_list(standards)}<h2>Traffic approach</h2><ul>{rows}</ul><h2>Partner fit</h2><p>Future direct affiliate programs should match the audience, allow clear disclosure, and support self-serve transactions without creating a customer-support queue for this site.</p></article>'''

def feed_xml(site, items):
    updated = date.today().isoformat()
    entries = []
    for item in items[:40]:
        url = absolute(site["base_url"], item["path"])
        entries.append(f'''<entry><title>{esc(item["title"])}</title><link href="{esc(url)}"/><id>{esc(url)}</id><updated>{updated}</updated><summary>{esc(item["description"])}</summary></entry>''')
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
<title>{esc(site["name"])} updates</title>
<link href="{esc(site["base_url"].rstrip("/") + "/feed.xml")}" rel="self"/>
<link href="{esc(site["base_url"].rstrip("/") + "/")}"/>
<updated>{updated}</updated>
<id>{esc(site["base_url"].rstrip("/") + "/")}</id>
{''.join(entries)}
</feed>
'''

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
    editorial = load("editorial_calendar.json", {"seasonal_pages": [], "traffic_channels": []})
    accelerator = load("accelerator.json", {"target_min_pages": 50})
    recs = {r["id"]: r for r in load("recommendations.json")}
    shutil.copytree(ASSETS, out / "assets")

    tool_cards = "".join(card(t["title"], t["description"], f'tools/{t["slug"]}/index.html', t["category"]) for t in tools)
    guide_cards = "".join(card(g["title"], g["description"], f'guides/{g["slug"]}/index.html', g["category"]) for g in guides[:6])
    rec_cards = "".join(card(r["label"], r["fit"], f'recommendations/{r["id"]}/index.html', "Product fit") for r in recs.values())
    category_names = sorted({t["category"] for t in tools} | {g["category"] for g in guides})
    design = load("design.json", {"hero_title": site["name"], "promise": site["tagline"], "primary_cta": "Use tools"})
    visual = '<div class="hero-frame"><img class="hero-image" src="assets/img/hero-v2.png" alt="' + esc(design.get("image_prompt", site["name"])) + '"></div>'
    cue_row = '<div class="cue-row"><span class="cue">Free tools</span><span class="cue">No account</span><span class="cue">Private inputs</span><span class="cue">Affiliate disclosed</span></div>'
    decision = '<section class="decision-band"><div class="decision-steps"><div class="step"><strong>1. Measure</strong><span>Use the calculator before browsing.</span></div><div class="step"><strong>2. Narrow</strong><span>Match the result to a product category.</span></div><div class="step"><strong>3. Decide</strong><span>Open only the links that fit the job.</span></div></div></section>'
    home = f'<section class="hero"><div><span class="tag">Decision-first tools</span><h1>{esc(design["hero_title"])}</h1><p class="hero-lede">{esc(design["promise"])}</p>{cue_row}<div class="hero-actions"><a class="button" href="tools/index.html">{esc(design["primary_cta"])}</a><a class="button secondary" href="recommendations/index.html">Compare product fit</a></div></div>{visual}</section>{decision}<section class="band"><div class="wrap"><span class="section-kicker">Start here</span><h2 class="section-title">Useful tools with a buying next step</h2><div class="grid">{tool_cards}</div></div></section><section class="band alt"><div class="wrap"><span class="section-kicker">Reduce regret</span><h2 class="section-title">Product-fit pages for high-intent decisions</h2><div class="grid">{rec_cards}</div></div></section><section class="band"><div class="wrap"><span class="section-kicker">Evergreen help</span><h2 class="section-title">Guides and checklists</h2><div class="grid">{guide_cards}</div></div></section>'
    seasonal_preview = editorial.get("seasonal_pages", [])[:3]
    seasonal_cards = "".join(card(e["title"], e["description"], f'seasonal/{e["slug"]}/index.html', e["month"]) for e in seasonal_preview)
    home += f'<section class="band alt"><div class="wrap"><span class="section-kicker">Seasonal intent</span><h2 class="section-title">Timely entry points for search visitors</h2><div class="grid">{seasonal_cards}</div><p class="feed-callout"><a href="feed.xml">Follow the free update feed</a> for new calculator-first pages without an account.</p></div></section>'
    write(out / "index.html", layout(site, monetization, site["name"], site["tagline"], "index.html", home))

    write(out / "tools/index.html", layout(site, monetization, "Tools", "Interactive browser-only tools.", "tools/index.html", f'<section class="page-head"><h1>Tools</h1><p>Use these calculators and generators before buying supplies or templates.</p></section><section class="wrap"><div class="grid">{tool_cards.replace("tools/","")}</div></section>'))
    for t in tools:
        rec_html = recommendation_cards(t["recommendation_ids"], recs, monetization, "../../")
        body = f'<section class="page-head"><span class="tag">{esc(t["category"])}</span><h1>{esc(t["title"])}</h1><p>{esc(t["description"])}</p></section><section class="content tool-shell"><div class="tool-panel"><form class="tool-form" data-calculator="{esc(t["kind"])}">{render_fields(t["fields"])}<button type="submit">Generate</button></form></div><div class="result-box" aria-live="polite"><p>Enter your numbers and generate a result.</p></div></section><section class="band"><div class="wrap"><h2 class="section-title">Next planning step</h2><p><a class="button secondary" href="../../tool-plans/{esc(t["slug"])}/index.html">Open the buying plan</a></p></div></section><section class="band"><div class="wrap"><h2 class="section-title">Product-fit links</h2><div class="grid">{rec_html}</div></div></section>'
        write(out / f'tools/{t["slug"]}/index.html', layout(site, monetization, t["title"], t["description"], f'tools/{t["slug"]}/index.html', body, True, "SoftwareApplication"))

    guide_index_cards = "".join(card(g["title"], g["description"], f'{g["slug"]}/index.html', g["category"]) for g in guides)
    write(out / "guides/index.html", layout(site, monetization, "Guides", "Evergreen supporting pages.", "guides/index.html", f'<section class="page-head"><h1>Guides</h1><p>Evergreen support pages for the tools and monetized link slots.</p></section><section class="wrap"><div class="grid">{guide_index_cards}</div></section>'))
    for g in guides:
        sections = "".join("<h2>{}</h2><p>{}</p><ul>{}</ul>".format(esc(s["heading"]), esc(s["body"]), "".join(f"<li>{esc(b)}</li>" for b in s["bullets"])) for s in g["sections"])
        checklist_link = f'<p><a class="button secondary" href="../../checklists/{esc(g["slug"])}/index.html">Open printable checklist</a></p>'
        write(out / f'guides/{g["slug"]}/index.html', layout(site, monetization, g["title"], g["description"], f'guides/{g["slug"]}/index.html', f'<section class="page-head"><span class="tag">{esc(g["category"])}</span><h1>{esc(g["title"])}</h1><p>{esc(g["description"])}</p></section><article class="content">{sections}{checklist_link}</article>'))

    rec_index_cards = "".join(card(r["label"], r["fit"], f'{r["id"]}/index.html', "Product fit") for r in recs.values())
    write(out / "recommendations/index.html", layout(site, monetization, "Product-Fit Pages", "High-intent product category fit notes tied to the tools.", "recommendations/index.html", f'<section class="page-head"><h1>Product-fit pages</h1><p>Use these pages after a calculator result tells you what category to consider.</p></section><section class="wrap"><div class="grid">{rec_index_cards}</div></section>'))
    for rec in recs.values():
        write(out / f'recommendations/{rec["id"]}/index.html', layout(site, monetization, rec["label"], rec["fit"], f'recommendations/{rec["id"]}/index.html', recommendation_page(site, monetization, rec, tools, guides)))

    plan_cards = "".join(card(t["title"] + " buying plan", "Turn the calculator result into a narrower supply decision.", f'{t["slug"]}/index.html', t["category"]) for t in tools)
    write(out / "tool-plans/index.html", layout(site, monetization, "Tool Buying Plans", "Step-by-step buying plans for every calculator.", "tool-plans/index.html", f'<section class="page-head"><h1>Tool buying plans</h1><p>These pages bridge calculator output to a product-fit decision.</p></section><section class="wrap"><div class="grid">{plan_cards}</div></section>'))
    for t in tools:
        write(out / f'tool-plans/{t["slug"]}/index.html', layout(site, monetization, t["title"] + " Buying Plan", "A measured buying plan for " + t["title"], f'tool-plans/{t["slug"]}/index.html', tool_plan_page(site, monetization, t, recs)))

    checklist_cards = "".join(card(g["title"] + " checklist", "Print-friendly setup checklist.", f'{g["slug"]}/index.html', g["category"]) for g in guides)
    write(out / "checklists/index.html", layout(site, monetization, "Printable Checklists", "Print-friendly checklists for repeatable setup decisions.", "checklists/index.html", f'<section class="page-head"><h1>Printable checklists</h1><p>Simple checklists that help visitors act without creating a support queue.</p></section><section class="wrap"><div class="grid">{checklist_cards}</div></section>'))
    for g in guides:
        write(out / f'checklists/{g["slug"]}/index.html', layout(site, monetization, g["title"] + " Checklist", "A print-friendly checklist for " + g["title"], f'checklists/{g["slug"]}/index.html', checklist_page(site, g)))

    category_cards = "".join(card(c + " hub", "Tools, guides, and product-fit links for this topic.", f'{slugify(c)}/index.html', "Topic") for c in category_names)
    write(out / "categories/index.html", layout(site, monetization, "Topic Hubs", "Topic-level hubs that improve crawl paths and user routing.", "categories/index.html", f'<section class="page-head"><h1>Topic hubs</h1><p>Grouped tools, guides, and product-fit pages.</p></section><section class="wrap"><div class="grid">{category_cards}</div></section>'))
    for c in category_names:
        write(out / f'categories/{slugify(c)}/index.html', layout(site, monetization, c + " Hub", "Tools and checklists for " + c, f'categories/{slugify(c)}/index.html', category_page(c, tools, guides, recs, monetization)))

    tools_by_slug = {t["slug"]: t for t in tools}
    guides_by_slug = {g["slug"]: g for g in guides}
    write(out / "start-here/index.html", layout(site, monetization, "Start Here", "Fast routing to the best tool, guide, or seasonal page.", "start-here/index.html", start_here_page(site, tools, guides, editorial)))
    seasonal_index_cards = "".join(card(e["title"], e["description"], f'{e["slug"]}/index.html', e["month"]) for e in editorial.get("seasonal_pages", []))
    write(out / "seasonal/index.html", layout(site, monetization, "Seasonal Decision Pages", "Timely calculator-first pages for recurring buying moments.", "seasonal/index.html", f'<section class="page-head"><h1>Seasonal decision pages</h1><p>Recurring entry points built around buyer intent, practical timing, and calculator-first decisions.</p></section><section class="wrap"><div class="grid">{seasonal_index_cards}</div></section>'))
    for entry in editorial.get("seasonal_pages", []):
        write(out / f'seasonal/{entry["slug"]}/index.html', layout(site, monetization, entry["title"], entry["description"], f'seasonal/{entry["slug"]}/index.html', seasonal_page(entry, tools_by_slug, guides_by_slug, recs, monetization)))
    write(out / "publisher-standards/index.html", layout(site, monetization, "Publisher Standards", "Affiliate publisher standards, trust cues, and no-cost traffic approach.", "publisher-standards/index.html", publisher_standards_page(site, editorial)))

    static = {
        "about": ("About", f"{site['name']} is a browser-only static tool business with external monetization links."),
        "privacy": ("Privacy", "This site does not use accounts, comments, payment forms, server analytics, or paid tracking. Calculator inputs stay in the browser. Affiliate click counts, when available, stay in the visitor browser local storage."),
        "monetization": ("Monetization", monetization["disclosure"] + " The site does not display Amazon reviews, ratings, prices, availability, or images. Checkout links are handled by external no-monthly-fee storefronts when configured."),
    }
    for slug, (title, text) in static.items():
        write(out / f"{slug}/index.html", layout(site, monetization, title, text, f"{slug}/index.html", f'<section class="page-head"><h1>{esc(title)}</h1><p>{esc(text)}</p></section>'))

    feed_items = [{"title": site["name"], "description": site["tagline"], "path": "index.html"}]
    feed_items += [{"title": t["title"], "description": t["description"], "path": f'tools/{t["slug"]}/index.html'} for t in tools]
    feed_items += [{"title": e["title"], "description": e["description"], "path": f'seasonal/{e["slug"]}/index.html'} for e in editorial.get("seasonal_pages", [])]
    feed_items += [{"title": g["title"], "description": g["description"], "path": f'guides/{g["slug"]}/index.html'} for g in guides[:12]]
    write(out / "feed.xml", feed_xml(site, feed_items))
    paths = [str(p.relative_to(out)).replace("\\", "/") for p in out.rglob("*.html")]
    urls = "\n".join(f"<url><loc>{esc(absolute(site['base_url'], p))}</loc><lastmod>{date.today().isoformat()}</lastmod></url>" for p in sorted(paths))
    write(out / "sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}\n</urlset>\n')
    write(out / "robots.txt", f"User-agent: *\nAllow: /\nSitemap: {site['base_url'].rstrip()}/sitemap.xml\n")
    print(json.dumps({"status": "ok", "html_pages": len(paths), "tools": len(tools), "guides": len(guides), "seasonal_pages": len(editorial.get("seasonal_pages", [])), "target_min_pages": accelerator.get("target_min_pages", 50)}, indent=2))

if __name__ == "__main__":
    main()
