#!/usr/bin/env python3
"""Create the merge scenarios as pairs of developer branches off `main`.

Every scenario has two branches that both start from the same `main` commit:

    scenario/<name>/dev-a      Developer A's change
    scenario/<name>/dev-b      Developer B's change

Usage (run from the repo root, with a clean working tree on a repo whose
`main` branch already has the initial commit):

    python scenarios/create_scenarios.py            # create branches locally
    python scenarios/create_scenarios.py --push     # ...and push to origin
    python scenarios/create_scenarios.py --force    # recreate existing ones

See README.md for what each scenario is and what to expect.
"""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "main"


def git(*args, check=True):
    result = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True)
    if check and result.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed:\n{result.stderr or result.stdout}")
    return result


def edit(path, old, new):
    """Replace `old` with `new` in a file; fail loudly if `old` is missing."""
    file = ROOT / path
    text = file.read_text()
    if old not in text:
        sys.exit(f"Scenario edit failed, text not found in {path}:\n{old}")
    file.write_text(text.replace(old, new, 1))


def write(path, text):
    file = ROOT / path
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(text)


# ===========================================================================
# GROUP 1 - things MergeMind should flag today
# ===========================================================================

# ---- function-conflict ----------------------------------------------------
# Both developers change apply_discount() with conflicting business rules.
# They touch different lines, so Git merges it without complaint.

def function_conflict_a():
    edit(
        "shop/pricing.py",
        "    return round(discounted, 2)\n",
        "    return round(max(discounted, price * 0.5), 2)  # never discount over 50%\n",
    )


def function_conflict_b():
    edit(
        "shop/pricing.py",
        '''    if percent < 0:
        raise ValueError("percent must be >= 0")''',
        '''    if percent < 0 or percent > 90:
        raise ValueError("percent must be between 0 and 90")''',
    )


# ---- dependency-conflict --------------------------------------------------
# Developer A adds a required `currency` argument to calculate_price() and
# updates every caller it can see. Developer B, working in the same file,
# adds a new call to calculate_price() with the old two-argument form.
# Each branch passes its tests alone, Git merges them cleanly, and the merged
# code crashes with a TypeError.

def add_currency_argument():
    """Developer A for both the dependency-conflict and cross-file scenarios."""
    edit(
        "shop/pricing.py",
        '''def calculate_price(price, tax):
    """Return the price including tax."""
    return round(price + tax, 2)''',
        '''def calculate_price(price, tax, currency):
    """Return the price including tax, rounded for the given currency."""
    digits = 0 if currency == "JPY" else 2
    return round(price + tax, digits)''',
    )
    edit(
        "shop/pricing.py",
        "    total = calculate_price(discounted, tax)\n",
        '    total = calculate_price(discounted, tax, "USD")\n',
    )
    edit(
        "tests/test_pricing.py",
        "assert calculate_price(100, 18) == 118.0",
        'assert calculate_price(100, 18, "USD") == 118.0',
    )


def dependency_conflict_b():
    edit(
        "shop/pricing.py",
        "def order_total(subtotal, discount_percent=0):",
        "def order_total(subtotal, discount_percent=0, shipping=0.0):",
    )
    edit(
        "shop/pricing.py",
        "    return total\n",
        "    shipping_gross = calculate_price(shipping, calculate_tax(shipping))\n"
        "    return round(total + shipping_gross, 2)\n",
    )


# ---- class-conflict -------------------------------------------------------
# Both developers change the Cart class (in different methods).

def class_conflict_a():
    edit(
        "shop/cart.py",
        '''        """Add an item to the cart."""
        self.items.append((item, quantity))''',
        '''        """Add an item to the cart."""
        if quantity < 1:
            raise ValueError("quantity must be at least 1")
        self.items.append((item, quantity))''',
    )


def class_conflict_b():
    edit(
        "shop/cart.py",
        "        return sum(quantity for _, quantity in self.items)",
        """        total = 0
        for _, quantity in self.items:
            total += quantity
        return total""",
    )


# ---- safe-merge -----------------------------------------------------------
# Two independent changes to unrelated functions. Nothing should be flagged.

def safe_merge_a():
    edit(
        "shop/pricing.py",
        '''    """Return the tax amount for a price."""
''',
        '''    """Return the tax amount for a price."""
    if price <= 0:
        return 0.0
''',
    )


def safe_merge_b():
    edit(
        "shop/pricing.py",
        '''        raise ValueError("percent must be >= 0")''',
        '''        raise ValueError("percent must be zero or positive")''',
    )


# ===========================================================================
# GROUP 2 - real breakages that MergeMind cannot see yet (roadmap benchmarks)
# The breaking call lives in a different file from the change, which the
# current per-file, function-level detectors do not cover.
# ===========================================================================

# ---- cross-file-signature -------------------------------------------------
# Same developer A as above. Developer B adds a brand-new module that calls
# calculate_price() with the old signature.

def cross_file_signature_b():
    write(
        "shop/loyalty.py",
        '''"""Loyalty pricing."""

from shop.pricing import calculate_price, calculate_tax


def loyalty_price(price, points):
    """Each 100 points gives 5% off (max 20%), then tax is added."""
    percent = min(points // 100 * 5, 20)
    discounted = price * (1 - percent / 100)
    return calculate_price(discounted, calculate_tax(discounted))
''',
    )
    write(
        "tests/test_loyalty.py",
        '''from shop.loyalty import loyalty_price


def test_loyalty_price_with_points():
    assert loyalty_price(100, 200) == 106.2
''',
    )


# ---- import-conflict ------------------------------------------------------
# A renames send_receipt() and updates orders.py. B adds a new module that
# imports the old name.

def import_conflict_a():
    edit(
        "shop/notifications.py",
        "def send_receipt(email, order_id, total):",
        "def send_order_receipt(email, order_id, total):",
    )
    edit(
        "shop/orders.py",
        "from shop.notifications import send_receipt",
        "from shop.notifications import send_order_receipt",
    )
    edit(
        "shop/orders.py",
        "    send_receipt(email, order_id, total)",
        "    send_order_receipt(email, order_id, total)",
    )


def import_conflict_b():
    write(
        "shop/reminders.py",
        '''"""Customer reminders."""

from shop.notifications import send_receipt


def resend_receipt(email, order_id, total):
    """Send a customer their receipt again."""
    return send_receipt(email, order_id, total)
''',
    )
    write(
        "tests/test_reminders.py",
        '''from shop.reminders import resend_receipt


def test_resend_receipt():
    assert "order 7" in resend_receipt("alice@example.com", 7, 10.0)
''',
    )


# name -> (dev A builder, dev B builder, commit subject)
SCENARIOS = {
    "function-conflict": (function_conflict_a, function_conflict_b, "apply_discount rules"),
    "dependency-conflict": (add_currency_argument, dependency_conflict_b, "currency argument vs new call"),
    "class-conflict": (class_conflict_a, class_conflict_b, "Cart changes"),
    "safe-merge": (safe_merge_a, safe_merge_b, "independent edits"),
    "cross-file-signature": (add_currency_argument, cross_file_signature_b, "currency argument vs new module"),
    "import-conflict": (import_conflict_a, import_conflict_b, "rename send_receipt vs new importer"),
}


def branch_exists(name):
    return git("rev-parse", "--verify", "--quiet", name, check=False).returncode == 0


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--push", action="store_true", help="push branches to origin")
    parser.add_argument("--force", action="store_true", help="recreate existing branches")
    args = parser.parse_args()

    if git("status", "--porcelain").stdout.strip():
        sys.exit("Working tree is not clean. Commit or stash your changes first.")
    if not branch_exists(BASE):
        sys.exit(f"Branch '{BASE}' not found. Make the initial commit on {BASE} first.")

    names = []
    print(f"Creating scenario branches from '{BASE}':")
    for scenario, (build_a, build_b, subject) in SCENARIOS.items():
        for dev, build in (("dev-a", build_a), ("dev-b", build_b)):
            name = f"scenario/{scenario}/{dev}"
            names.append(name)
            if branch_exists(name):
                if not args.force:
                    print(f"  skip   {name} (exists; use --force to recreate)")
                    continue
                git("switch", BASE)
                git("branch", "-D", name)
            git("switch", BASE)
            git("switch", "-c", name)
            build()
            git("add", "-A")
            git("commit", "-m", f"{scenario}: {dev.replace('-', ' ')} - {subject}")
            print(f"  create {name}")

    git("switch", BASE)

    if args.push:
        print("Pushing branches to origin...")
        git("push", "-u", "origin", *names)

    print("\nDone. Next: python scenarios/run_checks.py")


if __name__ == "__main__":
    main()
