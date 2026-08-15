from __future__ import annotations
import json, subprocess, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class SiteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable,"scripts/build.py","--out","site"],cwd=ROOT,check=True)
    def test_validation(self):
        subprocess.run([sys.executable,"scripts/validate.py","--dist","site"],cwd=ROOT,check=True)
    def test_counts(self):
        accelerator=json.loads((ROOT/"data/accelerator.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(json.loads((ROOT/"data/tools.json").read_text(encoding="utf-8"))),5)
        self.assertGreaterEqual(len(json.loads((ROOT/"data/guides.json").read_text(encoding="utf-8"))),10)
        self.assertGreaterEqual(len(list((ROOT/"site").rglob("*.html"))),accelerator["target_min_pages"])
    def test_accelerator_pages(self):
        for path in ["recommendations/index.html","tool-plans/index.html","checklists/index.html","categories/index.html","start-here/index.html","seasonal/index.html","publisher-standards/index.html","feed.xml","assets/img/hero-v2.png"]:
            self.assertTrue((ROOT/"site"/path).exists(), path)
    def test_editorial_calendar(self):
        editorial=json.loads((ROOT/"data/editorial_calendar.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(editorial["seasonal_pages"]),12)
        self.assertGreaterEqual(len(editorial["traffic_channels"]),3)
        feed=(ROOT/"site/feed.xml").read_text(encoding="utf-8")
        self.assertIn("<feed", feed)

    def test_design_system_polish(self):
        css=(ROOT/"assets/css/site.css").read_text(encoding="utf-8")
        self.assertIn("--font-display", css)
        self.assertIn("repeating-linear-gradient", css)
        self.assertNotIn("vw", css)

    def test_monetized_links(self):
        html="\n".join(p.read_text(encoding="utf-8") for p in (ROOT/"site").rglob("*.html"))
        self.assertIn("tag=fivefingersup-20", html)
        self.assertIn('rel="sponsored nofollow noopener"', html)
        self.assertIn("As an Amazon Associate I earn from qualifying purchases.", html)
    def test_operations_controls(self):
        ops=json.loads((ROOT/"data/operations.json").read_text(encoding="utf-8"))
        self.assertFalse(ops["kill_switch"])
        self.assertEqual(ops["max_incremental_cost_usd"],0)
        self.assertEqual(ops["bad_item_policy"]["retry_limit"],1)
        js=(ROOT/"assets/js/tools.js").read_text(encoding="utf-8")
        self.assertIn("localStorage", js)
        self.assertIn("fff_affiliate_click_counts", js)
        workflows="\n".join(p.read_text(encoding="utf-8") for p in (ROOT/".github/workflows").glob("*.yml"))
        self.assertIn("scripts/preflight.py", workflows)
    def test_optimizer(self):
        subprocess.run([sys.executable,"scripts/optimize.py","--out","reports"],cwd=ROOT,check=True)
        report=json.loads((ROOT/"reports/optimization-report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["status"],"ok")
        self.assertEqual(report["cost"]["incremental_usd"],0)
        self.assertFalse(report["cost"]["paid_apis_used"])
        self.assertIn("accelerator_page_types", report["site"])
        self.assertGreaterEqual(report["site"]["seasonal_pages"],12)
        self.assertIn("source_strategy_actions", report)
        self.assertGreaterEqual(report["site"]["seasonal_pages"],12)
        self.assertIn("source_strategy_actions", report)
        self.assertGreaterEqual(report["site"]["seasonal_pages"],12)
        self.assertIn("source_strategy_actions", report)
        self.assertGreaterEqual(report["site"]["seasonal_pages"],12)
        self.assertIn("source_strategy_actions", report)
if __name__=="__main__": unittest.main()
