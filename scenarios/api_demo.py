#!/usr/bin/env python3
"""Exercise the MergeMind FastAPI backend with the demo project.

Start the backend first (from your MergeMind checkout):

    cd backend
    uvicorn main:app --reload

then, from this repo's root (after create_scenarios.py):

    python scenarios/api_demo.py
    python scenarios/api_demo.py --url http://127.0.0.1:8000

Uses only the standard library. It calls:
  GET  /        health check
  POST /parse   AST + dependency graph for every file in shop/
  POST /merge   three-way analysis of the file both developers edited
"""

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# scenario -> the single file both developers edited
MERGE_CASES = {
    "function-conflict": "shop/pricing.py",
    "dependency-conflict": "shop/pricing.py",
    "class-conflict": "shop/cart.py",
    "safe-merge": "shop/pricing.py",
}


def call(url, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def git_show(ref, path):
    out = subprocess.run(
        ["git", "show", f"{ref}:{path}"], cwd=ROOT, text=True, capture_output=True
    )
    if out.returncode:
        sys.exit(f"git show {ref}:{path} failed. Did you run create_scenarios.py?")
    return out.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--url", default="http://127.0.0.1:5000")
    args = parser.parse_args()
    base_url = args.url.rstrip("/")

    try:
        print("GET /", "->", call(f"{base_url}/"))
    except (urllib.error.URLError, ConnectionError) as error:
        sys.exit(f"Cannot reach the backend at {base_url}: {error}\n"
                 "Start it with: cd backend && uvicorn main:app --reload")

    print("\nPOST /parse")
    for path in sorted((ROOT / "shop").glob("*.py")):
        rel = path.relative_to(ROOT).as_posix()
        reply = call(f"{base_url}/parse", {"filename": rel, "code": path.read_text()})
        graph = reply.get("dependency_graph", {})
        print(f"  {rel:<24} success={reply.get('success')}  "
              f"nodes={len(graph.get('nodes', []))}  edges={len(graph.get('edges', []))}")

    print("\nPOST /merge")
    for scenario, path in MERGE_CASES.items():
        a, b = f"scenario/{scenario}/dev-a", f"scenario/{scenario}/dev-b"
        reply = call(f"{base_url}/merge", {
            "base_code": git_show("main", path),
            "developer_a_code": git_show(a, path),
            "developer_b_code": git_show(b, path),
            "base_filename": path,
        })
        analysis = reply.get("merge_analysis", {})
        conflicts = analysis.get("conflicts", [])
        print(f"  {scenario:<22} {len(conflicts)} conflict(s)")
        for c in conflicts:
            print(f"      [{c.get('severity')}] {c.get('type')}: {c.get('description')}")


if __name__ == "__main__":
    main()
