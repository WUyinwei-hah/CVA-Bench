# Publish CVA-Bench To GitHub

This file assumes you want to publish the already-prepared standalone release
directory:

`cva-bench/public_release/CVA-Bench`

## 1. Go to the release directory

```bash
cd "/Users/yinwei/科研/GUI agent attack/cva-bench/public_release/CVA-Bench"
```

## 2. Optional local smoke check

Start a static server from the release directory:

```bash
python3 -m http.server 8011
```

Open one or two representative pages:

- `http://localhost:8011/sites/openclaw/index.html?variant=attack`
- `http://localhost:8011/sites/shopping_openapps/index.html?variant=attack`

In a second shell, run one local scripted check:

```bash
python3 runners/run_playwright.py \
  --scenario scenarios/openclaw_clean.json \
  --base-url http://localhost:8011 \
  --defense none
```

If that works, stop the local server and continue.

## 3. Initialize the Git repository

```bash
git init -b main
git add .
git status
```

If the staged files look correct:

```bash
git commit -m "Initial public release of CVA-Bench"
```

## 4. Create the GitHub repository

### Option A: Using GitHub CLI

If `gh` is installed and authenticated:

```bash
gh repo create CVA-Bench --public --source=. --remote=origin --push
```

This is the fastest path.

### Option B: Create the repo manually on GitHub

1. Create an empty public repo on GitHub, for example `CVA-Bench`
2. Then run:

```bash
git remote add origin git@github.com:<YOUR_GITHUB_USERNAME>/CVA-Bench.git
git push -u origin main
```

If you prefer HTTPS:

```bash
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/CVA-Bench.git
git push -u origin main
```

## 5. Add the first release tag

After the first push:

```bash
git tag v0.1.0
git push origin v0.1.0
```

## 6. Suggested GitHub repository settings

- Repo name: `CVA-Bench`
- Visibility: `Public`
- Default branch: `main`
- Topics:
  - `benchmark`
  - `computer-use-agents`
  - `gui-agents`
  - `agent-security`
  - `prompt-injection`
  - `browser-automation`

## 7. Suggested first release text

Title:

```text
v0.1.0: Initial public release of CVA-Bench mainline
```

Body:

```text
This release publishes the standalone CVA-Bench public repository.

Included in v0.1.0:
- mainline benchmark sites
- clean / attack / legit scenarios
- timing-expanded scenarios
- Playwright runner
- real-agent runner hooks for browser-use
- scorer and batch-evaluation utilities

This release intentionally excludes local experiment artifacts such as traces,
screenshots, DOM dumps, and internal template-source workspaces.
```

## 8. If you need to rebuild the public export

From the internal workspace root:

```bash
cd "/Users/yinwei/科研/GUI agent attack"
python3 cva-bench/scripts/prepare_public_release.py \
  --output "/Users/yinwei/科研/GUI agent attack/cva-bench/public_release/CVA-Bench" \
  --force
```

## 9. Minimal publish path

If you just want the shortest sequence:

```bash
cd "/Users/yinwei/科研/GUI agent attack/cva-bench/public_release/CVA-Bench"
git init -b main
git add .
git commit -m "Initial public release of CVA-Bench"
gh repo create CVA-Bench --public --source=. --remote=origin --push
git tag v0.1.0
git push origin v0.1.0
```
