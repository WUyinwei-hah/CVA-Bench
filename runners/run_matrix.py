from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List


MATRICES = {
    "smoke": [
        ("openclaw_clean", "none"),
        ("openclaw_attack", "none"),
        ("shopping_clean", "none"),
        ("shopping_attack", "none"),
    ],
    "main": [
        ("openclaw_clean", "none"),
        ("openclaw_attack", "none"),
        ("shopping_clean", "none"),
        ("shopping_attack", "none"),
        ("openclaw_clean", "L1"),
        ("openclaw_attack", "L1"),
        ("shopping_clean", "L1"),
        ("shopping_attack", "L1"),
    ],
    "utility": [
        ("openclaw_legit", "L1"),
        ("shopping_legit", "L1"),
        ("openclaw_legit", "L3"),
        ("shopping_legit", "L3"),
    ],
}


def run_subprocess(cmd: List[str], cwd: Path) -> Dict:
    completed = subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=True,
    )
    payload = completed.stdout.strip()
    return json.loads(payload)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a CVA-Bench scripted matrix.")
    parser.add_argument(
        "--matrix",
        required=True,
        choices=sorted(MATRICES.keys()),
        help="Named condition matrix to execute.",
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000/cva-bench",
        help="Base URL for the cva-bench static files.",
    )
    parser.add_argument(
        "--mode",
        default="scripted-smoke",
        choices=["scripted-smoke", "heuristic-policy"],
        help="Runner mode to use for each matrix row.",
    )
    parser.add_argument("--headless", action="store_true", help="Run headless browser instances.")
    parser.add_argument(
        "--repetitions",
        type=int,
        default=1,
        help="How many times to repeat each matrix condition.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit on the number of condition rows to execute.",
    )
    args = parser.parse_args()

    root_dir = Path(__file__).resolve().parents[1]
    runner_path = root_dir / "runners" / "run_playwright.py"
    scorer_path = root_dir / "scorers" / "score_run.py"
    logs_dir = root_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    matrix_rows = list(MATRICES[args.matrix])
    if args.limit is not None:
        matrix_rows = matrix_rows[: args.limit]

    summary_rows = []
    started_at = int(time.time())

    for scenario_stem, defense in matrix_rows:
        scenario_path = root_dir / "scenarios" / f"{scenario_stem}.json"

        for rep in range(1, args.repetitions + 1):
            run_id = f"{scenario_stem}_{defense}_r{rep}_{started_at}"
            runner_cmd = [
                sys.executable,
                str(runner_path),
                "--scenario",
                str(scenario_path),
                "--base-url",
                args.base_url,
                "--mode",
                args.mode,
                "--defense",
                defense,
                "--run-id",
                run_id,
            ]
            if args.headless:
                runner_cmd.append("--headless")

            runner_result = run_subprocess(runner_cmd, cwd=root_dir.parent)
            run_log_path = runner_result["run_log"]

            scorer_cmd = [
                sys.executable,
                str(scorer_path),
                "--scenario",
                str(scenario_path),
                "--run-log",
                run_log_path,
            ]
            scorer_result = run_subprocess(scorer_cmd, cwd=root_dir.parent)
            scored_path = scorer_result["scored_output"]

            scored = json.loads(Path(scored_path).read_text(encoding="utf-8"))
            summary_rows.append(
                {
                    "scenario": scenario_stem,
                    "defense": defense,
                    "rep": rep,
                    "run_id": run_id,
                    "task_completed": scored["task_completed"],
                    "attack_succeeded": scored["attack_succeeded"],
                    "legit_succeeded": scored["legit_succeeded"],
                    "utility_failure": scored["utility_failure"],
                    "pause_called": scored["pause_called"],
                    "terminated_by_defense": scored["terminated_by_defense"],
                    "scored_output": scored_path,
                }
            )

    summary_path = logs_dir / f"{args.matrix}_matrix_summary_{started_at}.json"
    summary_path.write_text(json.dumps(summary_rows, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "matrix": args.matrix,
                "mode": args.mode,
                "repetitions": args.repetitions,
                "rows": len(summary_rows),
                "summary_path": str(summary_path),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
