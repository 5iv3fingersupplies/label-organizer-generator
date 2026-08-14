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
        self.assertGreaterEqual(len(json.loads((ROOT/"data/tools.json").read_text())),5)
        self.assertGreaterEqual(len(json.loads((ROOT/"data/guides.json").read_text())),10)
        self.assertGreaterEqual(len(list((ROOT/"site").rglob("*.html"))),20)
    def test_monetized_links(self):
        html="\n".join(p.read_text(encoding="utf-8") for p in (ROOT/"site").rglob("*.html"))
        self.assertIn("tag=fivefingersup-20", html)
        self.assertIn('rel="sponsored nofollow noopener"', html)
        self.assertIn("As an Amazon Associate I earn from qualifying purchases.", html)
    def test_optimizer(self):
        subprocess.run([sys.executable,"scripts/optimize.py","--out","reports"],cwd=ROOT,check=True)
        report=json.loads((ROOT/"reports/optimization-report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["status"],"ok")
        self.assertEqual(report["cost"]["incremental_usd"],0)
        self.assertFalse(report["cost"]["paid_apis_used"])
if __name__=="__main__": unittest.main()
