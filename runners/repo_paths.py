from __future__ import annotations

from pathlib import Path


def detect_bench_root(start: Path) -> Path:
    resolved = start.resolve()
    candidates = [resolved, *resolved.parents]
    for candidate in candidates:
        if (candidate / "sites").is_dir() and (candidate / "scenarios").is_dir() and (candidate / "runners").is_dir():
            return candidate

        nested = candidate / "cva-bench"
        if (nested / "sites").is_dir() and (nested / "scenarios").is_dir() and (nested / "runners").is_dir():
            return nested

    raise RuntimeError(f"Could not detect CVA-Bench root from {start}")


BENCH_ROOT = detect_bench_root(Path(__file__).resolve().parent)
WORKSPACE_ROOT = BENCH_ROOT.parent


def resolve_repo_relative(path_value: str, bench_root: Path | None = None) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path

    root = bench_root or BENCH_ROOT
    candidates: list[Path] = []

    if path.parts and path.parts[0] == "cva-bench":
        candidates.append(root / Path(*path.parts[1:]))

    candidates.append(root / path)
    candidates.append(root.parent / path)

    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.exists():
            return candidate

    return candidates[0]
