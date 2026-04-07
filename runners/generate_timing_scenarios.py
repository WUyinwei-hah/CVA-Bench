from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from repo_paths import BENCH_ROOT

SOURCE_DIR = BENCH_ROOT / "scenarios"
OUTPUT_DIR = BENCH_ROOT / "scenarios_timing"

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

ATTACK_DEFAULT_TIMINGS = ("early", "middle", "late")
ATTACK_SITE_TIMINGS = {
    "shopping-openapps": ("early", "middle", "late", "in_context"),
    "openclaw": ("early", "middle", "late", "in_context"),
    "payroll-direct-deposit": ("early", "middle", "late", "in_context"),
    "password-manager-vault": ("early", "middle", "late", "in_context"),
    "admin-security-console": ("early", "middle", "late", "in_context"),
    "esign-contract-hub": ("early", "middle", "late", "in_context"),
}
LEGIT_SITE_TIMINGS = {
    "openclaw_legit": ("early", "middle", "in_context"),
    "payroll_direct_deposit_legit": ("in_context",),
    "password_manager_vault_legit": ("early", "middle", "in_context"),
    "admin_security_console_legit": ("early", "middle", "in_context"),
    "esign_contract_hub_legit": ("early", "middle", "in_context"),
}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def add_or_replace_query_param(entry_path: str, key: str, value: str) -> str:
    parts = urlsplit(entry_path)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query[key] = value
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    written = 0

    for source_path in sorted(SOURCE_DIR.glob("*.json")):
        if source_path.name.endswith(".template.json"):
            continue

        data = load_json(source_path)
        site = data.get("site")
        variant = data.get("variant")

        if site not in SUPPORTED_SITES:
            continue

        timings = None
        timing_field = None
        if variant == "attack":
            timings = ATTACK_SITE_TIMINGS.get(str(site), ATTACK_DEFAULT_TIMINGS)
            timing_field = "attack_timing"
        elif variant == "legit" and source_path.stem in LEGIT_SITE_TIMINGS:
            timings = LEGIT_SITE_TIMINGS[source_path.stem]
            timing_field = "legit_timing"
        else:
            continue

        for timing in timings:
            clone = deepcopy(data)
            clone["scenario_id"] = f"{data['scenario_id']}__{timing}"
            clone[timing_field] = timing
            clone["entry_path"] = add_or_replace_query_param(str(data["entry_path"]), "timing", timing)
            if clone.get("notes_entry_path"):
                clone["notes_entry_path"] = add_or_replace_query_param(str(clone["notes_entry_path"]), "timing", timing)

            output_path = OUTPUT_DIR / f"{source_path.stem}_{timing}.json"
            output_path.write_text(json.dumps(clone, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            written += 1

    print(json.dumps({"written": written, "output_dir": str(OUTPUT_DIR)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
