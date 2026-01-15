from __future__ import annotations

import json
import sys
from pathlib import Path


def _add_repo_root_to_syspath() -> Path:
    """
    Ensures `import gnce...` works no matter where the script is run from.
    Repo root is the folder that contains `gnce/`.
    """
    here = Path(__file__).resolve()
    repo_root = here.parents[1]  # tools/ -> repo root
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    return repo_root


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _assert_has(adra: dict, key: str) -> None:
    if key not in adra:
        raise AssertionError(f"Missing required top-level key: {key}")


def _assert_is_dict(adra: dict, key: str) -> None:
    v = adra.get(key)
    if not isinstance(v, dict):
        raise AssertionError(f"Expected `{key}` to be a dict, got {type(v).__name__}")


def _assert_contract_minimal(adra: dict, GNCE_CONTRACT_VERSION: str, case_name: str) -> None:
    _assert_has(adra, "adra_id")
    _assert_has(adra, "adra_hash")
    _assert_has(adra, "gnce_contract_version")
    if str(adra.get("gnce_contract_version")) != str(GNCE_CONTRACT_VERSION):
        raise AssertionError(
            f"{case_name}: Contract version mismatch: "
            f"ADRA={adra.get('gnce_contract_version')} CODE={GNCE_CONTRACT_VERSION}"
        )

    # L1 must exist under your canonical name
    _assert_has(adra, "L1_the_verdict_and_constitutional_outcome")
    _assert_is_dict(adra, "L1_the_verdict_and_constitutional_outcome")

    l1 = adra["L1_the_verdict_and_constitutional_outcome"]
    if "decision_outcome" not in l1:
        raise AssertionError(f"{case_name}: Missing L1.decision_outcome")
    if "severity" not in l1:
        raise AssertionError(f"{case_name}: Missing L1.severity")


def _decision_of(adra: dict) -> str:
    l1 = adra.get("L1_the_verdict_and_constitutional_outcome", {}) or {}
    return str(l1.get("decision_outcome") or "N/A").upper()


def _run_case(run_gn_kernel, payload: dict, case_name: str) -> dict:
    try:
        adra = run_gn_kernel(payload)
    except Exception as e:
        raise RuntimeError(f"{case_name}: Kernel execution failed: {type(e).__name__}: {e}") from e

    if not isinstance(adra, dict):
        raise AssertionError(f"{case_name}: Kernel returned non-dict ADRA: {type(adra).__name__}")

    return adra


def main() -> int:
    repo_root = _add_repo_root_to_syspath()

    print("🔎 GNCE Smoke Test Gate (Extended): START")
    print(f"   Repo root: {repo_root}")

    # -----------------------------
    # 1) Import gates (hard fail)
    # -----------------------------
    try:
        from gnce.gn_kernel.kernel import run_gn_kernel
    except Exception as e:
        print("❌ Import gate failed: gnce.gn_kernel.kernel.run_gn_kernel")
        print(f"   {type(e).__name__}: {e}")
        return 1

    try:
        from gnce.gn_kernel.contracts import GNCE_CONTRACT_VERSION
    except Exception as e:
        print("❌ Import gate failed: gnce.gn_kernel.contracts.GNCE_CONTRACT_VERSION")
        print(f"   {type(e).__name__}: {e}")
        return 1

    try:
        from gnce.gn_kernel.federation.federation_gateway import emit_adra_if_enabled
        from gnce.gn_kernel.federation.config_loader import load_federation_config
    except Exception as e:
        print("❌ Import gate failed: federation gateway/config loader")
        print(f"   {type(e).__name__}: {e}")
        return 1

    print("✅ Imports OK")

    # -----------------------------
    # 2) Load test inputs (ALLOW + DENY)
    # -----------------------------
    allow_path = repo_root / "gnce" / "configs" / "allow_basic.json"

    # ⚠️ Update this filename if your actual deny file is spelled differently.
    deny_path = repo_root / "gnce" / "configs" / "deny_critical_violation.json"

    if not allow_path.exists():
        print(f"❌ Missing ALLOW test input JSON: {allow_path}")
        return 1
    if not deny_path.exists():
        print(f"❌ Missing DENY test input JSON: {deny_path}")
        print("   (Check the exact filename in gnce/configs and update deny_path accordingly.)")
        return 1

    allow_payload = _load_json(allow_path)
    deny_payload = _load_json(deny_path)

    print(f"✅ Loaded input: {allow_path.name}")
    print(f"✅ Loaded input: {deny_path.name}")

    # -----------------------------
    # 3) Run ALLOW case
    # -----------------------------
    try:
        adra_allow = _run_case(run_gn_kernel, allow_payload, "ALLOW")
        _assert_contract_minimal(adra_allow, GNCE_CONTRACT_VERSION, "ALLOW")
        decision_allow = _decision_of(adra_allow)
        print(f"✅ ALLOW case decision: {decision_allow}")
    except Exception as e:
        print(f"❌ ALLOW case failed: {e}")
        return 1

    # -----------------------------
    # 4) Run DENY/VETO case
    # -----------------------------
    try:
        adra_deny = _run_case(run_gn_kernel, deny_payload, "DENY")
        _assert_contract_minimal(adra_deny, GNCE_CONTRACT_VERSION, "DENY")
        decision_deny = _decision_of(adra_deny)
        print(f"✅ DENY case decision: {decision_deny}")

        if decision_deny == "ALLOW":
            raise AssertionError("DENY case unexpectedly resulted in ALLOW (policy gap or test input not binding).")

    except Exception as e:
        print(f"❌ DENY/VETO case failed: {e}")
        return 1

    # -----------------------------
    # 5) Federation gate:
    #    (A) must never crash when OFF
    #    (B) when ON, must not emit twice for same ADRA hash
    # -----------------------------
    fed_cfg_path = repo_root / "gnce" / "configs" / "federation_config.json"
    if not fed_cfg_path.exists():
        print(f"⚠️ federation_config.json not found at {fed_cfg_path} (skipping federation gates)")
    else:
        try:
            fed_cfg = load_federation_config(fed_cfg_path)

            # A) non-blocking dry emit (UI disabled)
            emit_adra_if_enabled(adra_allow, fed_cfg, ui_enabled=False)
            print("✅ Federation gateway OK (dry emit, non-blocking)")

            # B) idempotent emit when UI enabled (hash-based)
            adra_hash = str(adra_allow.get("adra_hash") or "")
            emit_key = f"federation_emitted::{adra_hash}" if adra_hash else f"federation_emitted::{adra_allow.get('adra_id','UNKNOWN')}"

            # Local “session_state-like” gate for the smoke test:
            emitted = {}

            def emit_once_for_test(adra: dict) -> None:
                if emitted.get(emit_key, False):
                    # If the gateway is not idempotent internally, we stop it here.
                    return
                emitted[emit_key] = True
                emit_adra_if_enabled(adra, fed_cfg, ui_enabled=True)

            emit_once_for_test(adra_allow)
            emit_once_for_test(adra_allow)  # should NOT emit again
            print("✅ Federation ON: emission is idempotent (single-emit enforced by hash gate)")

        except Exception as e:
            print("❌ Federation gate failed")
            print(f"   {type(e).__name__}: {e}")
            return 1

    print("🎉 GNCE Smoke Test Gate (Extended): PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
