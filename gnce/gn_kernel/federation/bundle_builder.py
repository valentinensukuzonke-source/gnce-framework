from __future__ import annotations

from typing import Any, Dict, Tuple
from datetime import datetime, timezone
import io
import json
import hashlib
import zipfile


def build_bundle(payload: Dict[str, Any], adra: Dict[str, Any], mode: str) -> bytes:
    """
    Build the exported bundle.

    For REDACTED/FULL -> returns ZIP bytes (Regulator Evidence Bundle).
    For HASH_ONLY -> returns UTF-8 JSON bytes (no ZIP).
    """
    mode = (mode or "OFF").upper().strip()

    if mode == "HASH_ONLY":
        return _json_bytes(payload)

    if mode in ("REDACTED", "FULL"):
        return _build_regulator_zip(payload, adra, mode)

    return _json_bytes({"mode": "OFF"})


# ----------------------------
# Regulator Bundle (ZIP)
# ----------------------------

def _build_regulator_zip(payload: Dict[str, Any], adra: Dict[str, Any], mode: str) -> bytes:
    ts = _now_utc_compact()
    adra_id = (adra.get("adra_id") or "UNKNOWN").strip()

    manifest, ledger_row, regime_outcomes = _derive_bundle_artifacts(adra, payload, mode)

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("README.txt", _readme_text())
        z.writestr("manifest.json", _json_str(manifest))
        z.writestr("adra.json", _json_str(payload))
        z.writestr("ledger.json", _json_str(ledger_row))
        z.writestr("regime_outcomes.json", _json_str(regime_outcomes))

    return zip_buf.getvalue()


def _derive_bundle_artifacts(adra: Dict[str, Any], payload: Dict[str, Any], mode: str) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    l1 = _l1(adra)
    l6 = adra.get("L6_behavioral_drift_and_monitoring") or adra.get("L6_drift_monitoring") or {}
    l7 = adra.get("L7_veto_and_execution_feedback") or {}
    l5 = adra.get("L5_integrity_and_tokenization") or {}
    l4 = adra.get("L4_policy_lineage_and_constitution") or {}

    decision = l1.get("decision_outcome") or l1.get("decision") or "N/A"
    severity = str(l1.get("severity", "UNKNOWN")).upper()

    drift = l6.get("drift_outcome") or l6.get("drift_status") or "NO_DRIFT"
    veto = bool(l7.get("veto_path_triggered") or l7.get("veto_triggered") or decision == "DENY")

    ledger_row = {
        "adra_id": adra.get("adra_id"),
        "created_at_utc": adra.get("created_at_utc"),
        "decision_outcome": decision,
        "severity": severity,
        "drift": str(drift).upper(),
        "veto_triggered": veto,
        "human_oversight_required": bool(l1.get("human_oversight_required", decision == "DENY")),
        "safe_state_triggered": bool(l1.get("safe_state_triggered", decision == "DENY")),
        "adra_hash": adra.get("adra_hash"),
        "contract_version": adra.get("gnce_contract_version"),
        "gnce_version": adra.get("GNCE_version"),
    }

    regime_outcomes = _build_regime_outcomes(l4)

    manifest = {
        "bundle_type": "GNCE_REGULATOR_EVIDENCE_BUNDLE",
        "generated_at_utc": _now_utc_iso(),
        "mode": mode,
        "adra_id": adra.get("adra_id"),
        "adra_hash": adra.get("adra_hash"),
        "gnce_contract_version": adra.get("gnce_contract_version"),
        "adra_version": adra.get("adra_version"),
        "GNCE_version": adra.get("GNCE_version"),
        "files": {
            "adra.json": _sha256_of_json(payload),
            "ledger.json": _sha256_of_json(ledger_row),
            "regime_outcomes.json": _sha256_of_json(regime_outcomes),
        },
        "integrity": l5,
    }

    return manifest, ledger_row, regime_outcomes


def _build_regime_outcomes(l4: Dict[str, Any]) -> Dict[str, Any]:
    """
    Minimal, regulator-friendly regime outcome vector derived from L4.
    Works even if policy objects vary, as long as we have a list of triggered policies.
    """
    policies = (l4.get("policies_triggered") or []) if isinstance(l4, dict) else []
    out: Dict[str, Any] = {"by_domain": {}, "by_regime": {}, "by_article": {}}

    for p in policies:
        if not isinstance(p, dict):
            continue

        domain = str(p.get("domain") or "UNKNOWN")
        regime = str(p.get("regime") or p.get("domain_id") or "UNKNOWN")
        article = str(p.get("article") or "N/A")
        status = str(p.get("status") or "UNKNOWN").upper()
        sev = p.get("severity")

        # by_domain
        out["by_domain"].setdefault(domain, {"counts": {}})
        out["by_domain"][domain]["counts"][status] = out["by_domain"][domain]["counts"].get(status, 0) + 1

        # by_regime
        out["by_regime"].setdefault(regime, {"counts": {}})
        out["by_regime"][regime]["counts"][status] = out["by_regime"][regime]["counts"].get(status, 0) + 1

        # by_article
        if article and article != "N/A":
            key = f"{regime}:{article}"
            out["by_article"].setdefault(key, {"status": status, "severity": sev, "domain": domain})

    return out


# ----------------------------
# Helpers
# ----------------------------

def _l1(adra: Dict[str, Any]) -> Dict[str, Any]:
    return (
        adra.get("L1_the_verdict_and_constitutional_outcome")
        or adra.get("L1_meta_verdict")
        or {}
    )


def _json_str(obj: Any) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False)


def _json_bytes(obj: Any) -> bytes:
    return _json_str(obj).encode("utf-8")


def _sha256_of_json(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _now_utc_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _readme_text() -> str:
    # Regulator-facing tone. No demos. No hype. Just verifiable facts.
    return (
        "GNCE Regulator Evidence Bundle\n"
        "=============================\n\n"
        "Purpose\n"
        "-------\n"
        "This bundle contains a governance decision artifact (ADRA) produced by the Gordian Nexus Constitutional Engine (GNCE),\n"
        "along with supporting integrity and outcome summaries to support audit, supervisory review, or regulatory assessment.\n\n"
        "Contents\n"
        "--------\n"
        "- adra.json: The Auditable Decision Rationale Artifact (ADRA). Depending on the configured export mode, this may be redacted.\n"
        "- ledger.json: A compact decision summary derived from the ADRA (decision, severity, drift, veto flags, and integrity anchors).\n"
        "- regime_outcomes.json: A regime/domain/article outcome vector derived from L4 policy lineage.\n"
        "- manifest.json: Bundle metadata and SHA-256 digests for included JSON files.\n\n"
        "Verification\n"
        "------------\n"
        "1) Confirm manifest.json 'files' digests match a SHA-256 computed over each corresponding JSON file.\n"
        "2) Confirm adra.json includes 'gnce_contract_version' and the required L0–L7 layers.\n"
        "3) Confirm the ADRA hash referenced in ledger.json matches the ADRA hash in adra.json.\n\n"
        "Interpretation (High Level)\n"
        "---------------------------\n"
        "L0: Pre-execution validation\n"
        "L1: Verdict & constitutional outcome\n"
        "L2: Input snapshot & integrity anchors\n"
        "L3: Rule-level trace\n"
        "L4: Policy lineage & regime grounding\n"
        "L5: Integrity & cryptographic binding (CET)\n"
        "L6: Drift evaluation\n"
        "L7: Veto / execution feedback\n"
    )
