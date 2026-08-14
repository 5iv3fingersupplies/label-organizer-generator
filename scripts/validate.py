from __future__ import annotations
import argparse, json, re, sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DISCLOSURE = "As an Amazon Associate I earn from qualifying purchases."
FORBIDDEN = [r"\$\s*\d", r"\brating(s)?\b", r"\bcustomer review(s)?\b", r"\bin stock\b", r"\bsale\b", r"\bdiscount\b", r"\bcheapest\b", r"\blowest price\b", r"\bbest seller\b"]
SECRETS = [r"sk-[A-Za-z0-9_-]{20,}", r"sk-proj-[A-Za-z0-9_-]{20,}", "OPENAI" + r"_API_KEY", r"ghp_[A-Za-z0-9_]{20,}", r"github_pat_[A-Za-z0-9_]{20,}"]

class Parser(HTMLParser):
    def __init__(self):
        super().__init__(); self.hrefs=[]; self.scripts=[]
    def handle_starttag(self, tag, attrs):
        data=dict(attrs)
        if "href" in data: self.hrefs.append(data["href"])
        if tag=="script" and "src" in data: self.scripts.append(data["src"])

def load(name): return json.loads((DATA/name).read_text(encoding="utf-8"))
def fail(errors, message): errors.append(message)
def scan(errors, label, text):
    lower=text.lower()
    lower=lower.replace("does not display amazon reviews, ratings, prices, availability, or images.", "")
    for pat in FORBIDDEN:
        if re.search(pat, lower): fail(errors, f"forbidden volatile claim in {label}: {pat}")
    if "m.media-amazon.com" in lower or "images-na.ssl-images-amazon.com" in lower: fail(errors, f"amazon image reference in {label}")
def target_exists(dist, current, href):
    if href.startswith("#") or href.startswith("mailto:"): return True
    parsed=urlparse(href)
    if parsed.scheme in ("http","https"): return True
    clean=unquote(parsed.path)
    if not clean or clean=="#": return True
    target=(current.parent/clean/"index.html").resolve() if clean.endswith("/") else (current.parent/clean).resolve() if "." in Path(clean).name else (current.parent/clean/"index.html").resolve()
    try: target.relative_to(dist.resolve())
    except ValueError: return False
    return target.exists()
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--dist", default="site"); args=ap.parse_args()
    errors=[]; tools=load("tools.json"); guides=load("guides.json"); monetization=load("monetization.json"); recs={r["id"] for r in load("recommendations.json")}
    if monetization.get("cost_cap_usd") != 0: fail(errors, "cost cap is not 0")
    if not monetization.get("amazon_associates_tag"): fail(errors, "missing associates tag")
    slugs=set()
    for name, coll in [("tool", tools), ("guide", guides)]:
        for item in coll:
            if item["slug"] in slugs: fail(errors, f"duplicate slug {item['slug']}")
            slugs.add(item["slug"]); scan(errors, f"{name}:{item['slug']}", json.dumps(item))
            for rec in item.get("recommendation_ids", []):
                if rec not in recs: fail(errors, f"unknown recommendation {rec}")
    if len(tools) < 5: fail(errors, "fewer than 5 tools")
    if len(guides) < 10: fail(errors, "fewer than 10 guides")
    dist=(ROOT/args.dist).resolve()
    html=list(dist.rglob("*.html"))
    if len(html) < 20: fail(errors, "fewer than 20 html pages")
    for file in html:
        text=file.read_text(encoding="utf-8")
        if DISCLOSURE not in text: fail(errors, f"missing affiliate disclosure in {file.relative_to(dist)}")
        if '<link rel="canonical"' not in text: fail(errors, f"missing canonical in {file.relative_to(dist)}")
        if 'application/ld+json' not in text: fail(errors, f"missing structured data in {file.relative_to(dist)}")
        if "click" not in text and "assets/js/tools.js" not in text: pass
        scan(errors, str(file.relative_to(dist)), text)
        parser=Parser(); parser.feed(text)
        for href in parser.hrefs:
            if not target_exists(dist, file, href): fail(errors, f"broken internal link from {file.relative_to(dist)} to {href}")
    for req in ["sitemap.xml","robots.txt","assets/css/site.css","assets/js/tools.js"]:
        if not (dist/req).exists(): fail(errors, f"missing {req}")
    workflow_text="\n".join(p.read_text(encoding="utf-8") for p in (ROOT/".github/workflows").glob("*.yml"))
    for needle in ["cron:", "deploy-pages", "scripts/optimize.py", "scripts/validate.py"]:
        if needle not in workflow_text: fail(errors, f"workflow missing {needle}")
    for path in ROOT.rglob("*"):
        if not path.is_file(): continue
        rel=path.relative_to(ROOT).as_posix()
        if rel.startswith((".git/","site/","reports/","private-inputs/")): continue
        if Path(rel).name.startswith(".env"): fail(errors, f"env file present: {rel}")
        try: text=path.read_text(encoding="utf-8")
        except UnicodeDecodeError: continue
        for pat in SECRETS:
            if re.search(pat, text): fail(errors, f"possible secret in {rel}")
    if errors:
        for e in errors: print("ERROR:", e, file=sys.stderr)
        return 1
    print(json.dumps({"status":"ok","checks":["data","dist","workflows","public-safety"]}, indent=2)); return 0
if __name__ == "__main__": raise SystemExit(main())
