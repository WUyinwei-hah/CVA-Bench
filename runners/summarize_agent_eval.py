from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from benchmark_manifest import DEFAULT_MANIFEST_PATH, load_manifest, site_metadata


VARIANT_ORDER = {"clean": 0, "attack": 1, "legit": 2}
DEFENSE_ORDER = {"none": 0, "L1": 1, "L3": 2}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def rate_text(num: int, den: int) -> str:
    if den == 0:
        return "0/0"
    return f"{num}/{den} ({num / den:.0%})"


def sort_key(row: Dict[str, Any]) -> Tuple[int, int, str, str]:
    return (
        VARIANT_ORDER.get(str(row.get("variant")), 99),
        DEFENSE_ORDER.get(str(row.get("defense")), 99),
        str(row.get("site", "")),
        str(row.get("run_id", "")),
    )


def enrich_row(row: Dict[str, Any], manifest: Dict[str, Any]) -> Dict[str, Any]:
    enriched = dict(row)

    scenario_path = Path(str(row.get("scenario_path", "")))
    scenario: Dict[str, Any] = {}
    if scenario_path.exists():
        scenario = load_json(scenario_path)

    scored_path = Path(str(row.get("scored_path", ""))) if row.get("scored_path") else None
    scored: Dict[str, Any] = {}
    if scored_path and scored_path.exists():
        scored = load_json(scored_path)

    enriched["site"] = scored.get("site") or scenario.get("site")
    enriched["scenario_id"] = scored.get("scenario_id") or scenario.get("scenario_id")
    enriched["variant"] = scored.get("variant") or scenario.get("variant")
    enriched["defense"] = scored.get("defense") or enriched.get("defense")
    site_meta = site_metadata(manifest, str(enriched.get("site", "")))
    enriched["display_name"] = site_meta.get("display_name")
    enriched["tier"] = site_meta.get("tier")
    enriched["family"] = site_meta.get("family")
    enriched["goal"] = scenario.get("goal", "")
    enriched["entry_path"] = scenario.get("entry_path", "")
    enriched["required_sink_ids"] = scenario.get("required_sink_ids", [])
    return enriched


def load_rows(input_paths: Iterable[Path], manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for input_path in input_paths:
        payload = load_json(input_path)
        if not isinstance(payload, list):
            raise ValueError(f"Expected list payload in {input_path}")
        for row in payload:
            if not isinstance(row, dict):
                continue
            enriched = enrich_row(row, manifest)
            enriched["source_file"] = str(input_path)
            rows.append(enriched)
    return sorted(rows, key=sort_key)


def build_aggregate(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    buckets: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (str(row.get("variant")), str(row.get("defense")))
        buckets[key].append(row)

    aggregate_rows: List[Dict[str, Any]] = []
    for (variant, defense), bucket in sorted(
        buckets.items(),
        key=lambda item: (
            VARIANT_ORDER.get(item[0][0], 99),
            DEFENSE_ORDER.get(item[0][1], 99),
        ),
    ):
        total = len(bucket)
        aggregate_rows.append(
            {
                "variant": variant,
                "defense": defense,
                "runs": total,
                "ok_runs": sum(1 for row in bucket if row.get("status") == "ok"),
                "task_completed": sum(1 for row in bucket if row.get("task_completed") is True),
                "attack_succeeded": sum(1 for row in bucket if row.get("attack_succeeded") is True),
                "legit_succeeded": sum(1 for row in bucket if row.get("legit_succeeded") is True),
                "utility_failure": sum(1 for row in bucket if row.get("utility_failure") is True),
                "pause_called": sum(1 for row in bucket if row.get("pause_called") is True),
                "timed_out": sum(1 for row in bucket if row.get("timed_out") is True),
            }
        )
    return aggregate_rows


def write_csv(rows: List[Dict[str, Any]], output_path: Path) -> None:
    fieldnames = [
        "run_id",
        "site",
        "display_name",
        "tier",
        "family",
        "scenario_id",
        "variant",
        "defense",
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
        "scenario_path",
        "scored_path",
        "source_file",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})


def write_markdown(
    rows: List[Dict[str, Any]],
    aggregate_rows: List[Dict[str, Any]],
    output_path: Path,
    *,
    title: str,
    execution_note: str,
) -> None:
    lines: List[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append("## 运行设置")
    lines.append("")
    lines.append(execution_note.strip())
    lines.append("")
    lines.append(f"- 总 run 数: {len(rows)}")
    lines.append(f"- 覆盖站点数: {len({str(row.get('site')) for row in rows})}")
    lines.append(f"- 输入结果文件数: {len({str(row.get('source_file')) for row in rows})}")
    lines.append("")
    lines.append("## 汇总结果")
    lines.append("")
    lines.append("| Variant | Defense | Runs | OK | Task Completed | Attack Succeeded | Legit Succeeded | Utility Failure | Pause Called | Timed Out |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for item in aggregate_rows:
        total = int(item["runs"])
        lines.append(
            "| "
            f"{item['variant']} | {item['defense']} | {total} | "
            f"{rate_text(int(item['ok_runs']), total)} | "
            f"{rate_text(int(item['task_completed']), total)} | "
            f"{rate_text(int(item['attack_succeeded']), total)} | "
            f"{rate_text(int(item['legit_succeeded']), total)} | "
            f"{rate_text(int(item['utility_failure']), total)} | "
            f"{rate_text(int(item['pause_called']), total)} | "
            f"{rate_text(int(item['timed_out']), total)} |"
        )

    tier_counts: Dict[str, int] = defaultdict(int)
    family_counts: Dict[str, int] = defaultdict(int)
    for row in rows:
        tier_counts[str(row.get("tier", "unknown"))] += 1
        family_counts[str(row.get("family", "unknown"))] += 1

    lines.append("")
    lines.append("## 覆盖结构")
    lines.append("")
    lines.append("| Tier | Runs |")
    lines.append("|---|---:|")
    for tier, count in sorted(tier_counts.items()):
        lines.append(f"| {tier} | {count} |")
    lines.append("")
    lines.append("| Family | Runs |")
    lines.append("|---|---:|")
    for family, count in sorted(family_counts.items()):
        lines.append(f"| {family} | {count} |")

    for variant in ["clean", "attack", "legit"]:
        variant_rows = [row for row in rows if row.get("variant") == variant]
        if not variant_rows:
            continue
        lines.append("")
        lines.append(f"## 明细: `{variant}`")
        lines.append("")
        lines.append("| Site | Tier | Family | Defense | Status | Completed | Attack | Legit | Utility Fail | Pause | Timeout | Final URL |")
        lines.append("|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|")
        for row in variant_rows:
            lines.append(
                "| "
                f"{row.get('site')} | {row.get('tier')} | {row.get('family')} | {row.get('defense')} | {row.get('status')} | "
                f"{str(bool(row.get('task_completed'))).lower()} | "
                f"{str(bool(row.get('attack_succeeded'))).lower()} | "
                f"{str(bool(row.get('legit_succeeded'))).lower()} | "
                f"{str(bool(row.get('utility_failure'))).lower()} | "
                f"{str(bool(row.get('pause_called'))).lower()} | "
                f"{str(bool(row.get('timed_out'))).lower()} | "
                f"{row.get('final_url', '')} |"
            )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge and summarize CVA-Bench real-agent evaluation outputs.")
    parser.add_argument("--inputs", nargs="+", required=True, help="Input JSON files from run_agent_eval.py.")
    parser.add_argument("--output-md", required=True, help="Output markdown report path.")
    parser.add_argument("--output-json", default=None, help="Optional merged JSON output path.")
    parser.add_argument("--output-csv", default=None, help="Optional merged CSV output path.")
    parser.add_argument(
        "--manifest",
        default=str(DEFAULT_MANIFEST_PATH),
        help="Path to benchmark_manifest.json for tier/family enrichment.",
    )
    parser.add_argument(
        "--title",
        default="CVA-Bench Real-Agent Evaluation Summary",
        help="Markdown report title.",
    )
    parser.add_argument(
        "--execution-note",
        default=(
            "- Agent runner: `browser-use` real agent (`runners/run_agent.py`)\n"
            "- Execution mode: headless, no-vision\n"
            "- Intended use: merge `run_agent_eval.py` batch outputs across variants / defenses"
        ),
        help="Short markdown note block describing the execution setup.",
    )
    args = parser.parse_args()

    input_paths = [Path(path).resolve() for path in args.inputs]
    manifest = load_manifest(Path(args.manifest).resolve())
    rows = load_rows(input_paths, manifest)
    aggregate_rows = build_aggregate(rows)

    output_md = Path(args.output_md).resolve()
    output_md.parent.mkdir(parents=True, exist_ok=True)
    write_markdown(rows, aggregate_rows, output_md, title=args.title, execution_note=args.execution_note)

    if args.output_json:
        output_json = Path(args.output_json).resolve()
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

    if args.output_csv:
        output_csv = Path(args.output_csv).resolve()
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        write_csv(rows, output_csv)

    print(
        json.dumps(
            {
                "rows": len(rows),
                "aggregate_rows": len(aggregate_rows),
                "output_md": str(output_md),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
