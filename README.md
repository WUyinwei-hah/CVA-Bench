# CVA-Bench

Context-first benchmark scaffolding for evaluating whether computer-use agents
comply with visibly suspicious popups when those popups appear tightly coupled
to the current task.

## What is included

This repository contains:

- static benchmark sites under `sites/`
- provenance-scored scenario JSON files under `scenarios/`
- timing-expanded scenario JSON files under `scenarios_timing/`
- a Playwright runner for scripted and heuristic execution
- a real-agent runner that can connect to an external `browser-use` stack
- a schema-aligned scorer and batch-evaluation utilities
- optional WebArena shopping migration helpers under `webarena/`

The public release is designed around the current 7-family mainline:

- `shopping_complete_order_openapps`
- `openclaw_connect_provider`
- `openclaw_advanced_usage_unlock`
- `payroll_direct_deposit_update`
- `password_manager_enable_device_sync`
- `admin_console_rotate_service_token`
- `esign_send_contract_for_signature`

Additional benchmark details are documented in
[`docs/BENCHMARK_OVERVIEW.md`](docs/BENCHMARK_OVERVIEW.md).

## Repository layout

```text
CVA-Bench/
  README.md
  LICENSE
  THIRD_PARTY_NOTICES.md
  requirements.txt
  docs/
  runners/
  scorers/
  scenarios/
  scenarios_timing/
  sites/
  webarena/
```

Generated outputs such as `logs/`, `screenshots/`, `traces/`, and `dom/` are
created locally and are intentionally not tracked in the public release.

## Quick start

### 1. Install local runner dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Serve the static benchmark sites

Run the HTTP server from the repository root:

```bash
python3 -m http.server 8011
```

Example pages:

- `http://localhost:8011/sites/openclaw/index.html?variant=clean`
- `http://localhost:8011/sites/openclaw/index.html?variant=attack`
- `http://localhost:8011/sites/shopping_openapps/index.html?variant=attack`
- `http://localhost:8011/sites/payroll_direct_deposit/index.html?variant=legit`

### 3. Run the Playwright benchmark runner

```bash
python3 runners/run_playwright.py \
  --scenario scenarios/openclaw_clean.json \
  --base-url http://localhost:8011 \
  --defense none
```

The runner writes:

- a screenshot
- a DOM snapshot
- a structured run log
- optional trace artifacts

## Runner modes

`runners/run_playwright.py` supports:

- `scripted-smoke`
- `heuristic-policy`
- `page-only`

Batch matrices can be launched with:

```bash
python3 runners/run_matrix.py \
  --matrix smoke \
  --mode heuristic-policy \
  --base-url http://localhost:8011 \
  --headless
```

## Real-agent execution

`runners/run_agent.py` drives the benchmark with a real `browser-use` agent.
This path is optional and requires a separate `browser-use` checkout plus model
credentials.

The runner supports either:

- `BROWSER_USE_ROOT=/path/to/browser-use`
- `--browser-use-root /path/to/browser-use`

Example:

```bash
python3 runners/run_agent.py \
  --scenario scenarios/openclaw_attack.json \
  --base-url http://localhost:8011 \
  --browser-use-root /path/to/browser-use \
  --defense L1 \
  --score
```

If the `browser-use` stack keeps its environment variables in a non-default
location, also pass `--env-file` or set `BROWSER_USE_ENV_FILE`.

## Public release export

The internal development workspace contains extra artifacts that should not be
published directly, including:

- large generated outputs
- local virtual environments
- local template-source dumps used during site construction

To prepare a clean standalone GitHub release, run:

```bash
python3 scripts/prepare_public_release.py --output ../public_release/CVA-Bench
```

The export script creates a small, publishable repository containing the
mainline benchmark files and release metadata while excluding local experiment
artifacts.

## Optional WebArena migration helpers

The WebArena shopping migration utilities live under `webarena/`. These files
are not required for the mainline static benchmark but can be used as an
optional extension path.

## License

Repository-specific benchmark code and benchmark-authored site files are
released under the MIT license in [`LICENSE`](LICENSE), with third-party
component notices listed in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
