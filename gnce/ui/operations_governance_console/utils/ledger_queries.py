# gnce/ui/Operations_Governance_Dashboard/utils/ledger_queries.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json
import hashlib
from datetime import datetime


# -----------------------------
# Helpers
# -----------------------------
def _safe_read_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _safe_read_jsonl(path: Path, max_lines: int = 5000) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= max_lines:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except Exception:
                    # ignore broken lines
                    continue
    except Exception:
        return []
    return out


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _as_dt(x: Any) -> Optional[datetime]:
    """
    Best-effort parse of timestamps found in ledger/ADRA objects.
    Accepts ISO strings or epoch seconds/ms.
    """
    if x is None:
        return None
    if isinstance(x, (int, float)):
        # try ms then s
        try:
            if x > 10_000_000_000:  # likely ms
                return datetime.fromtimestamp(x / 1000.0)
            return datetime.fromtimestamp(float(x))
        except Exception:
            return None
    if isinstance(x, str):
        s = x.strip()
        if not s:
            return None
        # handle 'Z'
        s = s.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(s)
        except Exception:
            return None
    return None


# -----------------------------
# Public API (read-only)
# -----------------------------

def default_ledger_paths(repo_root: Path) -> List[Path]:
    """
    Canonical sovereign evidence path(s) for Block M.

    Block M must read from REPO_ROOT/adra_logs (kernel-written truth).
    """
    path = repo_root / "adra_logs"
    if not (path.exists() and path.is_dir()):
        raise FileNotFoundError(f"Missing canonical ledger directory: {path}")
    return [path]


def discover_ledger_sources(search_dirs: List[Path]) -> List[Path]:
    """
    Discover files that likely contain ADRAs / session ledgers.
    Supports .json and .jsonl.
    """
    files: List[Path] = []
    for d in search_dirs:
        try:
            for ext in ("*.jsonl", "*.json"):
                files.extend(sorted(d.rglob(ext)))
        except Exception:
            continue
    # newest first
    files.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
    return files


def load_ledger_entries(
    sources: List[Path],
    max_files: int = 10,
    max_entries_per_file: int = 5000,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Load ledger/ADRA entries from the newest sources first.
    Returns (entries, meta)
    meta includes: used_sources, discovered_count, errors_count
    """
    entries: List[Dict[str, Any]] = []
    used: List[str] = []
    errors = 0

    for path in sources[:max_files]:
        if not path.exists() or not path.is_file():
            continue

        try:
            if path.suffix.lower() == ".jsonl":
                chunk = _safe_read_jsonl(path, max_lines=max_entries_per_file)
                if chunk:
                    entries.extend(chunk)
                    used.append(str(path))
            elif path.suffix.lower() == ".json":
                obj = _safe_read_json(path)
                if obj is None:
                    errors += 1
                    continue
                # Accept common shapes:
                # - {"entries":[...]}
                # - {"ledger":[...]}
                # - [ ... ]
                if isinstance(obj, list):
                    entries.extend([x for x in obj if isinstance(x, dict)])
                    used.append(str(path))
                elif isinstance(obj, dict):
                    arr = None
                    for k in ("entries", "ledger", "adra", "adras", "runs"):
                        if isinstance(obj.get(k), list):
                            arr = obj.get(k)
                            break
                    if arr:
                        entries.extend([x for x in arr if isinstance(x, dict)])
                        used.append(str(path))
                    else:
                        # treat the dict itself as one entry if it looks like an ADRA
                        entries.append(obj)
                        used.append(str(path))
        except Exception:
            errors += 1

        # stop if we have plenty
        if len(entries) >= max_entries_per_file:
            break

    meta = {
        "used_sources": used,
        "discovered_count": len(sources),
        "errors_count": errors,
        "entries_loaded": len(entries),
    }
    return entries, meta


def normalize_entry(e: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes a raw entry into a minimally consistent shape.
    Supports:
      - envelope rows: {"record": {...}, "written_at_utc": ..., ...}
      - flat rows: {"Decision": "...", "Timestamp (UTC)": "...", ...}
    """
    # 1) unwrap envelope if present
    rec = e.get("record") if isinstance(e, dict) else None
    base = rec if isinstance(rec, dict) else e

    out = dict(base)  # normalized view
    env = e if (isinstance(rec, dict) and isinstance(e, dict)) else {}

    # Timestamp
    ts = (
        base.get("timestamp_utc")
        or base.get("Timestamp (UTC)")
        or base.get("timestamp")
        or base.get("time")
        or base.get("created_at")
        or base.get("ts")
        or env.get("written_at_utc")
        or (base.get("meta", {}).get("timestamp") if isinstance(base.get("meta"), dict) else None)
    )
    dt = _as_dt(ts)
    out["_dt"] = dt

    # Verdict
    verdict = (
        base.get("verdict")
        or base.get("decision")
        or base.get("Decision")
        or (base.get("result", {}).get("verdict") if isinstance(base.get("result"), dict) else None)
    )
    if isinstance(verdict, str):
        verdict = verdict.upper().strip()
    out["_verdict"] = verdict if verdict in ("ALLOW", "DENY") else (verdict or "UNKNOWN")

    # Clause / reason (optional)
    clause = (
        base.get("clause")
        or (base.get("constitutional", {}).get("clause") if isinstance(base.get("constitutional"), dict) else None)
    )
    out["_clause"] = str(clause) if clause else None

    reason = (
        base.get("reason")
        or base.get("explanation")
        or (base.get("constitutional", {}).get("justification") if isinstance(base.get("constitutional"), dict) else None)
    )
    out["_reason"] = str(reason) if reason else None

    # Constitution hash
    const_hash = (
        base.get("constitution_hash")
        or base.get("constitutionHash")
        or (base.get("constitutional", {}).get("constitution_hash") if isinstance(base.get("constitutional"), dict) else None)
        or (base.get("meta", {}).get("constitution_hash") if isinstance(base.get("meta"), dict) else None)
    )
    out["_constitution_hash"] = str(const_hash) if const_hash else None

    return out



def session_constitution_hash(entries: List[Dict[str, Any]]) -> Optional[str]:
    """
    Returns the dominant constitution hash in session entries, if present.
    If absent, returns None.
    """
    counts: Dict[str, int] = {}
    for e in entries:
        h = e.get("_constitution_hash")
        if h:
            counts[h] = counts.get(h, 0) + 1
    if not counts:
        return None
    # most common
    return max(counts.items(), key=lambda kv: kv[1])[0]


def compute_session_fingerprint(entries: List[Dict[str, Any]]) -> str:
    """
    Deterministic hash of the normalized session entries (order-independent).
    Useful for "determinism confidence" in the sovereign loop.
    """
    # We only hash a stable subset to avoid UI-only keys
    stable = []
    for e in entries:
        stable.append({
            "dt": e.get("_dt").isoformat() if e.get("_dt") else None,
            "verdict": e.get("_verdict"),
            "veto_layer": e.get("_veto_layer"),
            "clause": e.get("_clause"),
            "constitution_hash": e.get("_constitution_hash"),
        })
    # order-independent
    stable_sorted = sorted(stable, key=lambda x: json.dumps(x, sort_keys=True))
    payload = json.dumps(stable_sorted, sort_keys=True)
    return _sha256_text(payload)
