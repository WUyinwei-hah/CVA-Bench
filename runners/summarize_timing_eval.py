from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
import re
from typing import Any, Dict, Iterable, List, Tuple

from benchmark_manifest import DEFAULT_MANIFEST_PATH, load_manifest, site_metadata


TIMING_ORDER = {"early": 0, "middle": 1, "late": 2, "in_context": 3}
TIMING_SUFFIX_RE = re.compile(r"__(early|middle|late|in_context)$")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def rate_text(num: int, den: int) -> str:
    if den == 0:
        return "0/0"
    return f"{num}/{den} ({num / den:.0%})"


def scenario_base_id(scenario_id: str | None) -> str:
    if not scenario_id:
        return "unknown"
    return TIMING_SUFFIX_RE.sub("", scenario_id)


def enrich_rows(input_paths: Iterable[Path], manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for input_path in input_paths:
        payload = load_json(input_path)
        if not isinstance(payload, list):
            raise ValueError(f"Expected list payload in {input_path}")
        for row in payload:
            scenario_path = Path(str(row.get("scenario_path", "")))
            scenario = load_json(scenario_path) if scenario_path.exists() else {}
            enriched = dict(row)
            enriched["site"] = scenario.get("site", row.get("site"))
            enriched["scenario_id"] = scenario.get("scenario_id")
            enriched["scenario_base_id"] = scenario_base_id(str(enriched.get("scenario_id") or ""))
            enriched["attack_timing"] = scenario.get("attack_timing", "unknown")
            site_meta = site_metadata(manifest, str(enriched.get("site", "")))
            enriched["display_name"] = site_meta.get("display_name")
            enriched["tier"] = site_meta.get("tier")
            enriched["family"] = site_meta.get("family")
            enriched["source_file"] = str(input_path)
            rows.append(enriched)
    return sorted(
        rows,
        key=lambda row: (
            str(row.get("scenario_base_id", "")),
            TIMING_ORDER.get(str(row.get("attack_timing", "")), 99),
            str(row.get("run_id", "")),
        ),
    )


def write_csv(rows: List[Dict[str, Any]], output_path: Path) -> None:
    fieldnames = [
        "run_id",
        "rep",
        "site",
        "display_name",
        "tier",
        "family",
        "scenario_id",
        "scenario_base_id",
        "attack_timing",
        "status",
        "task_completed",
        "attack_succeeded",
        "timed_out",
        "final_url",
        "scenario_path",
        "scored_path",
        "source_file",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})


def write_markdown(rows: List[Dict[str, Any]], output_path: Path, execution_note: str) -> None:
    by_timing: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    by_site: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    by_scenario: Dict[str, Dict[str, List[Dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))

    for row in rows:
        timing = str(row.get("attack_timing", "unknown"))
        site = str(row.get("site", "unknown"))
        scenario_key = str(row.get("scenario_base_id") or row.get("scenario_id") or "unknown")
        by_timing[timing].append(row)
        by_site[site].append(row)
        by_scenario[scenario_key][timing].append(row)

    lines: List[str] = []
    lines.append("# CVA-Bench Attack Timing Evaluation")
    lines.append("")
    lines.append("## 运行设置")
    lines.append("")
    lines.append(execution_note.strip())
    lines.append("")
    lines.append(f"- 总 run 数: {len(rows)}")
    lines.append(f"- 主线场景数: {len(by_scenario)}")
    lines.append(f"- 站点数: {len(by_site)}")
    lines.append("")
    lines.append("## 按时机汇总")
    lines.append("")
    ordered_timings = sorted(by_timing.keys(), key=lambda item: TIMING_ORDER.get(str(item), 99))
    lines.append("| Timing | Runs | Task Completed | Attack Succeeded | Timed Out |")
    lines.append("|---|---:|---:|---:|---:|")
    for timing in ordered_timings:
        bucket = by_timing.get(timing, [])
        total = len(bucket)
        lines.append(
            "| "
            f"{timing} | {total} | "
            f"{rate_text(sum(row.get('task_completed') is True for row in bucket), total)} | "
            f"{rate_text(sum(row.get('attack_succeeded') is True for row in bucket), total)} | "
            f"{rate_text(sum(row.get('timed_out') is True for row in bucket), total)} |"
        )

    lines.append("")
    lines.append("## 覆盖结构")
    lines.append("")
    lines.append("| Site | Tier | Family |")
    lines.append("|---|---|---|")
    for site in sorted(by_site):
        sample = by_site[site][0]
        lines.append(f"| {site} | {sample.get('tier')} | {sample.get('family')} |")

    lines.append("")
    lines.append("## 按场景对照")
    lines.append("")
    timing_headers = " | ".join(timing.title() if timing != "in_context" else "In-context" for timing in ordered_timings)
    lines.append(f"| Scenario | Site | {timing_headers} | Best Timing |")
    lines.append("|" + "---|" * (len(ordered_timings) + 3))
    for scenario_key in sorted(by_scenario):
        scenario_rows = by_scenario[scenario_key]
        sample = next(iter(next(iter(scenario_rows.values()))))
        counts = {
            timing: sum(row.get("attack_succeeded") is True for row in scenario_rows.get(timing, []))
            for timing in ordered_timings
        }
        totals = {timing: len(scenario_rows.get(timing, [])) for timing in ordered_timings}
        best = [timing for timing in ordered_timings if counts[timing] == max(counts.values()) and counts[timing] > 0]
        best_label = ", ".join(best) if best else "none"
        timing_cells = " | ".join(f"{counts[timing]}/{totals[timing]}" for timing in ordered_timings)
        lines.append(
            "| "
            f"{scenario_key} | {sample.get('site')} | {timing_cells} | {best_label} |"
        )

    lines.append("")
    lines.append("## 明细")
    lines.append("")
    lines.append("| Scenario | Site | Timing | Rep | Status | Completed | Attack Succeeded | Final URL |")
    lines.append("|---|---|---|---:|---|---:|---:|---|")
    for row in rows:
        lines.append(
            "| "
            f"{row.get('scenario_base_id')} | {row.get('site')} | {row.get('attack_timing')} | {row.get('rep', 1)} | {row.get('status')} | "
            f"{str(bool(row.get('task_completed'))).lower()} | "
            f"{str(bool(row.get('attack_succeeded'))).lower()} | "
            f"{row.get('final_url', '')} |"
        )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize CVA-Bench timing evaluation runs.")
    parser.add_argument("--inputs", nargs="+", required=True)
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--output-json", default=None)
    parser.add_argument("--output-csv", default=None)
    parser.add_argument(
        "--manifest",
        default=str(DEFAULT_MANIFEST_PATH),
        help="Path to benchmark_manifest.json for tier/family enrichment.",
    )
    parser.add_argument(
        "--execution-note",
        default=(
            "- Runner: `runners/run_agent.py`\n"
            "- Batch evaluator: `runners/run_agent_eval.py`\n"
            "- This summary is intended for timing comparisons across `early / middle / late` attack variants."
        ),
    )
    args = parser.parse_args()

    input_paths = [Path(path).resolve() for path in args.inputs]
    manifest = load_manifest(Path(args.manifest).resolve())
    rows = enrich_rows(input_paths, manifest)

    output_md = Path(args.output_md).resolve()
    output_md.parent.mkdir(parents=True, exist_ok=True)
    write_markdown(rows, output_md, args.execution_note)

    if args.output_json:
        output_json = Path(args.output_json).resolve()
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

    if args.output_csv:
        output_csv = Path(args.output_csv).resolve()
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        write_csv(rows, output_csv)

    print(json.dumps({"rows": len(rows), "output_md": str(output_md)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
