from __future__ import annotations
import argparse, json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/"data"
def load(name): return json.loads((DATA/name).read_text(encoding="utf-8"))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--out", default="reports"); args=ap.parse_args()
    out=(ROOT/args.out); out.mkdir(exist_ok=True)
    tools=load("tools.json"); guides=load("guides.json"); recs=load("recommendations.json"); accelerator=load("accelerator.json")
    cats=Counter([t["category"] for t in tools]+[g["category"] for g in guides])
    page_actions=[]
    for t in tools:
        page_actions.append({"score":32+len(t["recommendation_ids"])*3+(4 if cats[t["category"]]<=4 else 0),"title":t["title"],"path":f"tools/{t['slug']}","reason":"interactive monetized tool page"})
        page_actions.append({"score":24+len(t["recommendation_ids"])*2,"title":t["title"]+" buying plan","path":f"tool-plans/{t['slug']}","reason":"calculator to buyer-intent bridge"})
    for rec in recs:
        page_actions.append({"score":22,"title":rec["label"],"path":f"recommendations/{rec['id']}","reason":"high-intent product-fit page"})
    gaps=[]
    for cat,count in cats.items():
        gaps.append({"score":max(1,14-count),"title":f"Add a deeper {cat} support page","category":cat,"reason":"category depth expansion"})
    page_actions.sort(key=lambda x:x["score"], reverse=True); gaps.sort(key=lambda x:x["score"], reverse=True)
    report={"generated_at":datetime.now(timezone.utc).isoformat(),"status":"ok","cost":{"incremental_usd":0,"paid_apis_used":False},"site":{"tools":len(tools),"guides":len(guides),"recommendations":len(recs),"target_min_pages":accelerator["target_min_pages"],"accelerator_page_types":accelerator["page_types"]},"top_page_actions":page_actions,"content_gap_actions":gaps}
    (out/"optimization-report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    (out/"optimization-report.md").write_text("# Optimization Report\n\n"+"Generated: "+report["generated_at"]+"\n\n## Next Page Actions\n"+"\n".join(f"{i+1}. {a['title']} - score {a['score']} - {a['reason']}" for i,a in enumerate(page_actions[:20]))+"\n\n## Content Gaps\n"+"\n".join(f"{i+1}. {g['title']} - score {g['score']}" for i,g in enumerate(gaps))+"\n",encoding="utf-8")
    print(json.dumps({"status":"ok","page_actions":len(page_actions),"content_gaps":len(gaps),"paid_apis_used":False}, indent=2))
if __name__=="__main__": main()
