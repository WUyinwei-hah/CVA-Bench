from __future__ import annotations

import json
from typing import Any, Dict


def build_scenario_bootstrap_payload(scenario: Dict[str, Any]) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "site": str(scenario.get("site", "")),
        "scenario_id": str(scenario.get("scenario_id", "")),
        "variant": str(scenario.get("variant", "clean")),
    }
    if scenario.get("attack_timing"):
        payload["attack_timing"] = str(scenario["attack_timing"])
    if scenario.get("legit_timing"):
        payload["legit_timing"] = str(scenario["legit_timing"])
    return payload


def build_scenario_bootstrap_init_script(scenario: Dict[str, Any]) -> str:
    payload = json.dumps(build_scenario_bootstrap_payload(scenario), ensure_ascii=False)
    return f"""
(() => {{
  const config = {payload};
  const storageKey = "cva_bench_bootstrap_" + config.site;
  window.__CVA_SCENARIO_CONFIG__ = config;
  try {{
    sessionStorage.setItem(storageKey, JSON.stringify(config));
  }} catch (error) {{
    // Ignore storage failures and keep the config on window for this document.
  }}
}})();
""".strip()
