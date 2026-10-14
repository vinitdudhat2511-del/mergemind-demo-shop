# mergemind-demo-shop

A tiny Python "shop" app built to **test [MergeMind](https://github.com/SaaranshJohri/Autonomous-Multi-Agent-Merge-Auditor-Execution-Sequence-Verifier)**, a semantic merge-conflict auditor.

The app itself is simple: pricing, inventory, cart, checkout, orders. The interesting part is `scenarios/`, which builds pairs of developer branches where **Git merges cleanly but the code may still break**, then compares MergeMind's verdict with what really happens.

```
shop/                 the demo app (pricing, inventory, cart, checkout, orders ...)
tests/                pytest suite (all green on main)
scenarios/
  create_scenarios.py builds 6 scenarios = 12 branches (dev-a / dev-b per scenario)
  run_checks.py       runs MergeMind on each and compares with Git + pytest ground truth
  api_demo.py         exercises the FastAPI backend (/parse and /merge)
.github/workflows/
  mergemind.yml       runs `mergemind check` on every pull request
  tests.yml           runs pytest
```

## Quick start

```bash
# 1. environment
python -m venv venv
venv\Scripts\activate            # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
pip install "git+https://github.com/SaaranshJohri/Autonomous-Multi-Agent-Merge-Auditor-Execution-Sequence-Verifier.git"

# 2. make this a Git repo with `main` (skip if you cloned it)
git init -b main
git add .
git commit -m "Initial demo shop"

# 3. build the scenario branches
python scenarios/create_scenarios.py

# 4. run MergeMind against all of them
python scenarios/run_checks.py --verbose
```

To publish: create an **empty** repo on GitHub, then

```bash
git remote add origin https://github.com/<you>/mergemind-demo-shop.git
git push -u origin main
python scenarios/create_scenarios.py --push      # pushes all scenario branches
```

## The scenarios

Each scenario has `scenario/<name>/dev-a` and `scenario/<name>/dev-b`, both branched from `main`. **Every branch passes the tests on its own**, so any failure after merging is caused by the merge.

| Scenario | What happens | Git | Tests after merge | MergeMind (v0.1.0) |
|---|---|---|---|---|
| `function-conflict` | A caps discounts at 50%, B allows up to 90%, both inside `apply_discount` | clean | pass | **flags** `function_conflict` |
| `dependency-conflict` | A adds a required `currency` argument to `calculate_price`; B adds a new old-style call to it inside `order_total` | clean | **FAIL** (`TypeError`) | **flags** `function_conflict` + `semantic_dependency_conflict` |
| `class-conflict` | A and B edit different methods of the `Cart` class | clean | pass | **flags** `class_conflict` |
| `safe-merge` | Independent edits to unrelated functions | clean | pass | no conflicts (correct) |
| `cross-file-signature` | Same A as above; B adds a **new module** calling the old signature | clean | **FAIL** (`TypeError`) | no conflicts, **known gap** |
| `import-conflict` | A renames `send_receipt` and fixes its callers; B adds a **new module** importing the old name | clean | **FAIL** (`ImportError`) | no conflicts, **known gap** |

Results were produced with MergeMind 0.1.0 installed from the repo's main branch.

What this tells you about MergeMind today:

- **Works:** same-file conflicts, both for the same function or class and for a caller/callee pair that two developers changed in the same file.
- **Not covered yet:** a break that spans files (new caller in another module, renamed import). `cross-file-signature` and `import-conflict` are benchmarks for that roadmap work, so the `KNOWN GAP` rows are expected. If you implement cross-file analysis, `run_checks.py` will print `NOW DETECTED` for them.
- **Class granularity:** `class-conflict` is flagged even though the two edits are in different, independent methods. Depending on your goals, that could be a false positive worth refining.

## Running MergeMind by hand

```bash
mergemind check --base scenario/dependency-conflict/dev-a \
                --head scenario/dependency-conflict/dev-b \
                --fail-on-conflict
echo $?          # 1 = conflict, 0 = clean   (Windows cmd: echo %errorlevel%)

mergemind analyze shop/pricing.py
```

`run_checks.py --cmd "python -m your.local.module"` lets you test a local development copy instead of the installed one.

## Testing the API backend

```bash
cd <your MergeMind checkout>/backend
uvicorn main:app --reload
```
then, in this repo:
```bash
python scenarios/api_demo.py
```
It checks `GET /`, sends every file in `shop/` to `POST /parse`, and sends the base/A/B versions of the edited file for each scenario to `POST /merge`.

## Testing the dashboard

Start the Streamlit dashboard, then paste the contents of `shop/pricing.py` (or `shop/cart.py`) as the base version, and the same file from a scenario branch as Developer A / B. For example:

```bash
git show scenario/dependency-conflict/dev-a:shop/pricing.py
git show scenario/dependency-conflict/dev-b:shop/pricing.py
```

## Testing the GitHub Action

1. Push `main` and the scenario branches (see above). The workflow must exist on the PR's **base** branch, which it does because every scenario branch starts from `main`.
2. Open a pull request **from `dev-b` into `dev-a`** (change the base branch in the GitHub UI), or with the GitHub CLI:
   ```bash
   gh pr create --base scenario/dependency-conflict/dev-a --head scenario/dependency-conflict/dev-b \
     --title "Test: dependency-conflict" --body "MergeMind demo"
   ```
3. The **MergeMind Conflict Analysis** check should fail for `function-conflict`, `dependency-conflict` and `class-conflict`, and pass for `safe-merge`.

Don't merge these PRs; they exist only to trigger the check. Close them when done.

You can also run the workflow manually from the **Actions** tab (`workflow_dispatch`), which compares the selected branch with `origin/main`.

## Resetting

```bash
git checkout main
python scenarios/create_scenarios.py --force     # recreate all scenario branches
```

The demo credentials in `shop/auth.py` are fake and for illustration only.
