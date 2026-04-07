from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

from benchmark_manifest import DEFAULT_MANIFEST_PATH, load_manifest, site_metadata
from repo_paths import BENCH_ROOT

SCENARIO_DIR = BENCH_ROOT / "scenarios"
LOG_DIR = BENCH_ROOT / "logs"
RUN_AGENT_SCRIPT = BENCH_ROOT / "runners" / "run_agent.py"

SUPPORTED_SITES = {
    "shopping-openapps",
    "openclaw",
    "office-openapps",
    "social-tabler-messenger",
    "drive-tabler-download",
    "crm-tabler-export",
    "payroll-direct-deposit",
    "password-manager-vault",
    "admin-security-console",
    "esign-contract-hub",
    "travel-hotel-booking",
    "patient-portal-records",
    "student-portal-documents",
    "learning-certificate-center",
    "government-services-certificate",
    "insurance-claim-summary",
    "invoice-statement-portal",
    "lease-portal-packet",
}


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_run_id(scenario_path: Path, defense: str, suffix: str) -> str:
    return f"{scenario_path.stem}_{defense}_{suffix}"


def discover_scenarios(
    variants: List[str],
    scenario_stems: List[str] | None = None,
    scenario_dir: Path | None = None,
    manifest: Dict[str, Any] | None = None,
    tiers: List[str] | None = None,
    families: List[str] | None = None,
) -> List[Path]:
    root = scenario_dir or SCENARIO_DIR
    allowed_stems = set(scenario_stems or [])
    allowed_tiers = set(tiers or [])
    allowed_families = set(families or [])
    manifest_payload = manifest or {}
    paths: List[Path] = []
    for path in sorted(root.glob("*.json")):
        if path.name.endswith(".template.json"):
            continue
        if allowed_stems and path.stem not in allowed_stems:
            continue
        data = load_json(path)
        site = str(data.get("site", ""))
        site_meta = site_metadata(manifest_payload, site)
        explicit_selection = bool(allowed_stems)
        if allowed_tiers or allowed_families:
            if not site_meta:
                continue
            if allowed_tiers and site_meta.get("tier") not in allowed_tiers:
                continue
            if allowed_families and site_meta.get("family") not in allowed_families:
                continue
        elif not explicit_selection:
            if site_meta:
                if not bool(site_meta.get("default_eval")):
                    continue
            elif site not in SUPPORTED_SITES:
                continue
        if data.get("variant") not in variants:
            continue
        paths.append(path)
    return paths


def run_one(
    scenario_path: Path,
    *,
    base_url: str,
    defense: str,
    conda_env: str,
    suffix: str,
    vision: bool,
    max_steps: int,
    episode_timeout_s: int,
    step_timeout_s: int,
    process_timeout_s: int,
    manifest: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    run_id = build_run_id(scenario_path, defense, suffix)
    scenario = load_json(scenario_path)
    site = str(scenario.get("site", ""))
    site_meta = site_metadata(manifest or {}, site)
    cmd = [
        "conda",
        "run",
        "--no-capture-output",
        "-n",
        conda_env,
        "python",
        str(RUN_AGENT_SCRIPT),
        "--scenario",
        str(scenario_path),
        "--base-url",
        base_url,
        "--defense",
        defense,
        "--score",
        "--headless",
        "--max-steps",
        str(max_steps),
        "--episode-timeout-s",
        str(episode_timeout_s),
        "--step-timeout-s",
        str(step_timeout_s),
        "--run-suffix",
        suffix,
    ]
    if not vision:
        cmd.append("--no-vision")

    started = time.time()
    result: Dict[str, Any] = {
        "run_id": run_id,
        "scenario_path": str(scenario_path),
        "site": site,
        "display_name": site_meta.get("display_name"),
        "tier": site_meta.get("tier"),
        "family": site_meta.get("family"),
        "status": "unknown",
        "stdout": "",
        "stderr": "",
        "elapsed_s": None,
    }

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(BENCH_ROOT),
            capture_output=True,
            text=True,
            timeout=process_timeout_s,
            check=False,
        )
        result["stdout"] = proc.stdout[-6000:]
        result["stderr"] = proc.stderr[-6000:]
        result["returncode"] = proc.returncode
        result["elapsed_s"] = round(time.time() - started, 2)
        result["status"] = "ok" if proc.returncode == 0 else "process_error"
    except subprocess.TimeoutExpired as exc:
        result["stdout"] = (exc.stdout or "")[-6000:]
        result["stderr"] = (exc.stderr or "")[-6000:]
        result["elapsed_s"] = round(time.time() - started, 2)
        result["status"] = "process_timeout"
        result["returncode"] = None

    run_log_path = LOG_DIR / f"{run_id}.json"
    scored_path = LOG_DIR / f"{run_id}.scored.json"
    result["run_log_path"] = str(run_log_path) if run_log_path.exists() else None
    result["scored_path"] = str(scored_path) if scored_path.exists() else None

    if run_log_path.exists():
        run_log = load_json(run_log_path)
        result["timed_out"] = run_log.get("timed_out")
        result["final_url"] = run_log.get("final_url")
    else:
        result["timed_out"] = None
        result["final_url"] = None

    if scored_path.exists():
        scored = load_json(scored_path)
        for key in [
            "task_completed",
            "attack_attempted",
            "attack_succeeded",
            "legit_succeeded",
            "utility_failure",
            "pause_called",
            "filled_sink_ids",
        ]:
            result[key] = scored.get(key)
    else:
        result["task_completed"] = None
        result["attack_attempted"] = None
        result["attack_succeeded"] = None
        result["legit_succeeded"] = None
        result["utility_failure"] = None
        result["pause_called"] = None
        result["filled_sink_ids"] = None

    return result


def write_summary(results: List[Dict[str, Any]], output_prefix: Path) -> None:
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    json_path = output_prefix.with_suffix(".json")
    csv_path = output_prefix.with_suffix(".csv")

    json_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    fieldnames = [
        "run_id",
        "rep",
        "scenario_path",
        "site",
        "display_name",
        "tier",
        "family",
        "status",
        "elapsed_s",
        "timed_out",
        "task_completed",
        "attack_attempted",
        "attack_succeeded",
        "legit_succeeded",
        "utility_failure",
        "pause_called",
        "final_url",
        "run_log_path",
        "scored_path",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow({key: row.get(key) for key in fieldnames})


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch-run real agent evaluation on CVA-Bench scenarios.")
    parser.add_argument("--base-url", default="http://localhost:8011/cva-bench")
    parser.add_argument("--defense", default="none", choices=["none", "L1", "L3"])
    parser.add_argument("--variants", nargs="+", default=["attack", "legit"])
    parser.add_argument(
        "--scenario-dir",
        default=str(SCENARIO_DIR),
        help="Directory containing scenario JSON files. Defaults to the repository scenarios/ directory.",
    )
    parser.add_argument(
        "--scenario-stems",
        nargs="+",
        default=None,
        help="Optional list of scenario file stems to run, for example shopping_openapps_attack.",
    )
    parser.add_argument(
        "--manifest",
        default=str(DEFAULT_MANIFEST_PATH),
        help="Path to benchmark_manifest.json for tier/family filtering and report enrichment.",
    )
    parser.add_argument(
        "--tier",
        nargs="+",
        default=None,
        help="Optional manifest tier filter, for example anchor_core headline_breadth.",
    )
    parser.add_argument(
        "--family",
        nargs="+",
        default=None,
        help="Optional manifest family filter, for example payment_booking workspace_account_reauth.",
    )
    parser.add_argument("--conda-env", default="webui")
    parser.add_argument("--suffix", default="evalnv1")
    parser.add_argument(
        "--vision",
        action="store_true",
        help="Enable screenshot-based vision input instead of DOM/text-only mode.",
    )
    parser.add_argument("--max-steps", type=int, default=12)
    parser.add_argument("--episode-timeout-s", type=int, default=180)
    parser.add_argument("--step-timeout-s", type=int, default=60)
    parser.add_argument("--process-timeout-s", type=int, default=240)
    parser.add_argument(
        "--repetitions",
        type=int,
        default=1,
        help="How many times to rerun each discovered scenario with unique run suffixes.",
    )
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--output-prefix", default="docs/agent_eval_2026_04_02_none_no_vision")
    args = parser.parse_args()

    scenario_dir = Path(args.scenario_dir).resolve()
    manifest_path = Path(args.manifest).resolve()
    manifest = load_manifest(manifest_path)
    scenarios = discover_scenarios(
        args.variants,
        scenario_stems=args.scenario_stems,
        scenario_dir=scenario_dir,
        manifest=manifest,
        tiers=args.tier,
        families=args.family,
    )
    if args.limit is not None:
        scenarios = scenarios[: args.limit]

    print(f"Discovered {len(scenarios)} scenarios.")
    results: List[Dict[str, Any]] = []

    total_runs = len(scenarios) * max(args.repetitions, 1)
    run_counter = 0
    for index, scenario_path in enumerate(scenarios, start=1):
        for rep in range(1, max(args.repetitions, 1) + 1):
            run_counter += 1
            suffix = args.suffix if args.repetitions == 1 else f"{args.suffix}_r{rep}"
            print(f"[{run_counter}/{total_runs}] {scenario_path.name} (rep {rep}/{args.repetitions})")
            result = run_one(
                scenario_path,
                base_url=args.base_url,
                defense=args.defense,
                conda_env=args.conda_env,
                suffix=suffix,
                vision=args.vision,
                max_steps=args.max_steps,
                episode_timeout_s=args.episode_timeout_s,
                step_timeout_s=args.step_timeout_s,
                process_timeout_s=args.process_timeout_s,
                manifest=manifest,
            )
            result["rep"] = rep
            results.append(result)
            print(
                json.dumps(
                    {
                        "run_id": result["run_id"],
                        "rep": rep,
                        "tier": result.get("tier"),
                        "family": result.get("family"),
                        "status": result["status"],
                        "timed_out": result["timed_out"],
                        "task_completed": result["task_completed"],
                        "attack_succeeded": result["attack_succeeded"],
                        "legit_succeeded": result["legit_succeeded"],
                    },
                    ensure_ascii=False,
                )
            )

    write_summary(results, (BENCH_ROOT.parent / args.output_prefix).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
