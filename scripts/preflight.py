from __future__ import annotations
import json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ops = json.loads((ROOT / "data" / "operations.json").read_text(encoding="utf-8"))
errors = []
if ops.get("max_incremental_cost_usd") != 0:
    errors.append("incremental cost cap must remain 0")
if ops.get("routine_human_approval_required"):
    errors.append("routine human approval must remain false")
if ops.get("bad_item_policy", {}).get("retry_limit") != 1:
    errors.append("bad item retry limit must remain 1")

halted = bool(ops.get("kill_switch"))
output_path = os.environ.get("GITHUB_OUTPUT")
if output_path:
    with open(output_path, "a", encoding="utf-8") as handle:
        handle.write(f"halted={str(halted).lower()}\n")

if errors:
    for error in errors:
        print(f"ERROR: {error}")
    sys.exit(1)
print(json.dumps({"status": "halted" if halted else "ok", "incremental_cost_usd": 0, "kill_switch": halted}, indent=2))