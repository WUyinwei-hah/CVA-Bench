from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any, Dict


SCRIPT_DIR = Path(__file__).resolve().parent
BENCH_ROOT = SCRIPT_DIR.parent

MAINLINE_SITES = {
    "shopping-openapps",
    "openclaw",
    "payroll-direct-deposit",
    "password-manager-vault",
    "admin-security-console",
    "esign-contract-hub",
}

MAINLINE_SITE_DIRS = {
    "shopping_openapps",
    "openclaw",
    "payroll_direct_deposit",
    "password_manager_vault",
    "admin_security_console",
    "esign_contract_hub",
}

ROOT_FILES = [
    ".gitignore",
    ".nojekyll",
    "index.html",
    "LICENSE",
    "README.md",
    "THIRD_PARTY_NOTICES.md",
    "requirements.txt",
]

ROOT_DIRS = [
    ".github",
    "docs",
    "runners",
    "scorers",
    "scripts",
]


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def reset_output_dir(output_dir: Path, *, force: bool) -> None:
    if output_dir.exists():
        if not force:
            raise FileExistsError(f"Output directory already exists: {output_dir}")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)


def copy_root_files(output_dir: Path) -> None:
    for relative in ROOT_FILES:
        source = BENCH_ROOT / relative
        destination = output_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    for relative in ROOT_DIRS:
        source = BENCH_ROOT / relative
        destination = output_dir / relative
        shutil.copytree(
            source,
            destination,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
        )


def copy_sites(output_dir: Path) -> None:
    sites_root = output_dir / "sites"
    sites_root.mkdir(parents=True, exist_ok=True)

    for relative in ["_shared", "_vendor"]:
        shutil.copytree(
            BENCH_ROOT / "sites" / relative,
            sites_root / relative,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
        )

    assets_root = sites_root / "assets"
    assets_root.mkdir(parents=True, exist_ok=True)
    for asset_name in ["harbor-field-jacket.svg", "openclaw-dashboard.svg"]:
        shutil.copy2(BENCH_ROOT / "sites" / "assets" / asset_name, assets_root / asset_name)

    for site_dir in sorted(MAINLINE_SITE_DIRS):
        shutil.copytree(
            BENCH_ROOT / "sites" / site_dir,
            sites_root / site_dir,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
        )


def copy_filtered_scenarios(source_dir: Path, destination_dir: Path) -> int:
    destination_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    for source_path in sorted(source_dir.glob("*.json")):
        payload = load_json(source_path)
        site = str(payload.get("site", ""))
        if source_path.name == "benchmark_manifest.json":
            manifest = payload
            sites_meta = manifest.get("sites", {})
            manifest["default_eval_sites"] = [
                site_name for site_name in manifest.get("default_eval_sites", []) if site_name in MAINLINE_SITES
            ]
            manifest["sites"] = {
                site_name: meta for site_name, meta in sites_meta.items() if site_name in MAINLINE_SITES
            }
            write_json(destination_dir / source_path.name, manifest)
            written += 1
            continue

        if site not in MAINLINE_SITES:
            continue

        write_json(destination_dir / source_path.name, payload)
        written += 1
    return written


def copy_optional_webarena(output_dir: Path) -> None:
    webarena_root = output_dir / "webarena"
    webarena_root.mkdir(parents=True, exist_ok=True)

    for relative in ["README.md", "injections/runtime.js"]:
        source = BENCH_ROOT / "webarena" / relative
        destination = webarena_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    for relative in ["scripts", "manifests", "recon"]:
        shutil.copytree(
            BENCH_ROOT / "webarena" / relative,
            webarena_root / relative,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
        )


def create_empty_output_dirs(output_dir: Path) -> None:
    for name in ["logs", "screenshots", "traces", "dom"]:
        target = output_dir / name
        target.mkdir(parents=True, exist_ok=True)
        (target / ".gitkeep").write_text("", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a clean standalone CVA-Bench public release.")
    parser.add_argument("--output", required=True, help="Destination directory for the exported public repository.")
    parser.add_argument("--force", action="store_true", help="Overwrite the destination if it already exists.")
    parser.add_argument(
        "--skip-webarena",
        action="store_true",
        help="Do not copy the optional WebArena migration helpers.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output).expanduser().resolve()
    reset_output_dir(output_dir, force=bool(args.force))

    copy_root_files(output_dir)
    copy_sites(output_dir)
    scenario_count = copy_filtered_scenarios(BENCH_ROOT / "scenarios", output_dir / "scenarios")
    timing_count = copy_filtered_scenarios(BENCH_ROOT / "scenarios_timing", output_dir / "scenarios_timing")
    if not args.skip_webarena:
        copy_optional_webarena(output_dir)
    create_empty_output_dirs(output_dir)

    metadata = {
        "scope": "mainline",
        "included_sites": sorted(MAINLINE_SITES),
        "copied_scenarios": scenario_count,
        "copied_timing_scenarios": timing_count,
        "included_webarena": not bool(args.skip_webarena),
        "export_layout": "standalone_repo",
    }
    write_json(output_dir / "EXPORT_METADATA.json", metadata)

    print(json.dumps(metadata, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
