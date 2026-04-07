from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Set

from repo_paths import BENCH_ROOT


DEFAULT_MANIFEST_PATH = BENCH_ROOT / "scenarios" / "benchmark_manifest.json"


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_manifest(path: Optional[Path] = None) -> Dict[str, Any]:
    manifest_path = path or DEFAULT_MANIFEST_PATH
    if not manifest_path.exists():
        return {}
    payload = load_json(manifest_path)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected object payload in manifest: {manifest_path}")
    return payload


def supported_sites(manifest: Dict[str, Any]) -> Set[str]:
    sites = manifest.get("sites", {})
    if not isinstance(sites, dict):
        return set()
    return {str(site) for site in sites.keys()}


def site_metadata(manifest: Dict[str, Any], site: str) -> Dict[str, Any]:
    sites = manifest.get("sites", {})
    if not isinstance(sites, dict):
        return {}
    meta = sites.get(site, {})
    return meta if isinstance(meta, dict) else {}
