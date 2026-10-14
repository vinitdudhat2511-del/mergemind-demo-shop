#!/usr/bin/env python3
"""Run MergeMind on every scenario and compare it with what really happens.

For each scenario the script reports:

  Git merge   does `git merge` succeed without a textual conflict?
  Tests       do the project's tests pass after the merge?
  MergeMind   what does `mergemind check` say?
  Result      did MergeMind agree with reality?

Usage (from the repo root, after create_scenarios.py):

    python scenarios/run_checks.py
    python scenarios/run_checks.py --only dependency-conflict --verbose
    python scenarios/run_checks.py --cmd "python -m mergemind.cli"

`--cmd` lets you point at a local development copy of MergeMind instead of
the installed `mergemind` command.
"""

import argparse
import json
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# scenario -> does MergeMind (as of v0.1.0) have a detector for it?
#   "flag"  MergeMind should report a conflict
#   "clean" MergeMind should report no conflict
#   "gap"   a real breakage MergeMind is not expected to catch yet
EXPECTED = {
    "function-conflict": "flag",
    "dependency-conflict": "flag",
    "class-conflict": "flag",
    "safe-merge": "clean",
    "cross-file-signature": "gap",
    "import-conflict": "gap",
}


def run(cmd, cwd=ROOT):
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def branches(scenario):
    return f"scenario/{scenario}/dev-a", f"scenario/{scenario}/dev-b"


def ground_truth(scenario):
    """Merge dev-b into dev-a in a throwaway worktree and run the tests."""
    a, b = branches(scenario)
    tmp = Path(tempfile.mkdtemp(prefix="mm-demo-"))
    work = tmp / "wt"
    try:
        add = run(["git", "worktree", "add", "--detach", str(work), a])
        if add.returncode:
            return "error", "error", add.stderr.strip()
        merge = run(["git", "merge", "--no-edit", "-m", "demo merge", b], cwd=work)
        if merge.returncode:
            return "CONFLICT", "n/a", ""
        tests = run([sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider"], cwd=work)
        return "clean", "pass" if tests.returncode == 0 else "FAIL", tests.stdout[-600:]
    finally:
        run(["git", "worktree", "remove", "--force", str(work)])
        shutil.rmtree(tmp, ignore_errors=True)


def mergemind(scenario, cmd):
    a, b = branches(scenario)
    proc = run([*cmd, "check", "--base", a, "--head", b])
    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None, f"could not parse output: {(proc.stderr or proc.stdout)[:300]}"
    return report, ""


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", help="run a single scenario by name")
    parser.add_argument("--verbose", action="store_true", help="print conflict details")
    parser.add_argument("--cmd", default="mergemind", help="MergeMind command (default: mergemind)")
    args = parser.parse_args()
    cmd = shlex.split(args.cmd)

    if shutil.which(cmd[0]) is None:
        sys.exit(f"'{cmd[0]}' not found. Install MergeMind first (see README) or pass --cmd.")

    names = [args.only] if args.only else list(EXPECTED)
    rows, matches = [], 0
    for name in names:
        if name not in EXPECTED:
            sys.exit(f"Unknown scenario '{name}'. Choices: {', '.join(EXPECTED)}")
        git_merge, tests, detail = ground_truth(name)
        report, err = mergemind(name, cmd)
        if report is None:
            verdict, found = "ERROR", []
            print(f"[{name}] {err}")
        else:
            found = report.get("conflicts", [])
            verdict = f"{len(found)} conflict(s)" if found else "no conflicts"
            if report.get("errors"):
                verdict += " + errors"

        flagged = bool(found)
        expect = EXPECTED[name]
        really_broken = tests == "FAIL" or git_merge == "CONFLICT"
        if expect == "flag":
            result = "OK" if flagged else "MISSED"
        elif expect == "clean":
            result = "OK" if not flagged and not really_broken else "UNEXPECTED"
        else:  # gap
            result = "KNOWN GAP" if not flagged else "NOW DETECTED"
        matches += result in ("OK", "KNOWN GAP", "NOW DETECTED")
        rows.append((name, git_merge, tests, verdict, result))

        if args.verbose:
            print(f"\n--- {name}")
            for c in found:
                print(f"    [{c.get('severity')}] {c.get('type')}: {c.get('description')}")
            if tests == "FAIL":
                print("    pytest after merge:\n      " + detail.strip().replace("\n", "\n      "))

    header = ("Scenario", "Git merge", "Tests", "MergeMind", "Result")
    widths = [max(len(str(r[i])) for r in [header, *rows]) for i in range(5)]
    line = "  ".join("{:<%d}" % w for w in widths)
    print("\n" + line.format(*header))
    print(line.format(*("-" * w for w in widths)))
    for row in rows:
        print(line.format(*row))
    print(
        "\nOK = detected/clean as expected | MISSED = detector regression | "
        "KNOWN GAP = real breakage MergeMind cannot see yet (roadmap)"
    )


if __name__ == "__main__":
    main()
