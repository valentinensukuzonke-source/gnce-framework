# GNCE Kernel Refactor Checklist

**Purpose**

This checklist exists to prevent regressions during kernel refactors (e.g. undefined variables, duplicated L7 logic, veto/drift confusion, UI desynchronisation). It reflects the *authoritative GNCE governance architecture* and should be followed for **any** change to `run_gn_kernel()` or downstream consumers.

---

## 0. Pre‑Refactor Guardrails

Before touching the kernel:

* [ ] Create a feature branch for the refactor
* [ ] Identify the **single source of truth** for each layer:

  * **L1** – Verdict & constitutional outcome (decision, severity, oversight, safe‑state)
  * **L6** – Continuous Drift Detection (asynchronous, non‑blocking, audit + recalibration)
  * **L7** – Veto Feedback Path (synchronous, blocking, pre‑execution)
* [ ] Decide which **explicit fields** the UI will consume (never infer from strings unless for backward compatibility)

---

## 1. Structural Rule: Explicit Layer Builders

To avoid ordering and scoping failures:

* [ ] Refactor `run_gn_kernel()` into explicit build stages (local functions are acceptable):

  * `build_l1(...)`
  * `build_l6(...)`
  * `build_l7(...)`
  * `assemble_adra(...)`
* [ ] No layer logic may be duplicated outside its builder
* [ ] L7 veto logic must exist **in exactly one place**

---

## 2. Ordering Rules (Python‑Critical)

These are non‑negotiable:

* [ ] Never reference a variable before assignment
* [ ] Dicts must be defined **before** being embedded in other structures

Required ordering examples:

* `verdict_snapshot` → `chain_of_custody` → `governance_context`
* L7 object must exist before:

  * chain of custody
  * verdict snapshot enrichment
  * ADRA assembly

---

## 3. L7 Veto Path — Single Source of Truth

L7 **is the authoritative runtime governance loop**.

Rules:

* [ ] Exactly one block computes:

  * `veto_triggered`
  * `veto_category`
  * `execution_authorized`
  * `veto_basis`
  * `corrective_signal`
* [ ] `veto_triggered` derives **only** from blocking policy failures
* [ ] Drift must **never** influence veto or execution authorization
* [ ] `veto_basis` must always be defined (empty list allowed)
* [ ] `escalation_required` must always be defined (`"NONE"` or `"HUMAN_REVIEWER"`)

---

## 4. Drift Loop (L6) Guardrails

Drift is **observational**, not gating.

* [ ] L6 may emit `DRIFT_ALERT`
* [ ] L6 may trigger forced recalibration
* [ ] L6 must **never**:

  * block execution
  * trigger veto
  * modify `execution_authorized`

---

## 5. Required Architectural Invariants

Keep these assertions in the kernel:

```python
assert not (drift_alert and veto_triggered), "ARCH: drift must never trigger veto"
assert isinstance(l7, dict) and l7.get("layer") == "L7"
assert "execution_authorized" in l7 and "veto_path_triggered" in l7
```

These catch silent regressions early.

---

## 6. UI Contract Rules (Decision Summary / Dashboards)

The UI must reflect **actual loop engagement**, not inferred semantics.

* [ ] Veto state must come from **L7 fields only**:

  * `l7.veto_path_triggered`
  * `l7.veto_triggered`
* [ ] Drift state must come from **L6 only**
* [ ] Do **not** infer veto from `decision == "DENY"`
* [ ] Sovereign / constitutional governance loop is **out‑of‑band** and must only activate when explicitly signaled

---

## 7. Corrective Signal Completion Check

When veto triggers:

* [ ] A Veto Artifact must be generated
* [ ] A corrective signal must be attached to L7
* [ ] `_event("VETO_CORRECTIVE_SIGNAL_EMITTED", ...)` must fire exactly once
* [ ] Violations must enumerate:

  * article
  * severity
  * explanation
  * constitutional clause

---

## 8. Mandatory Smoke Tests (Run After Every Refactor)

Execute at least one payload for each scenario:

* [ ] ALLOW (no drift, no veto)
* [ ] Blocking policy failure (veto triggers)
* [ ] DRIFT_ALERT with ALLOW (drift‑only scenario)

Confirm ADRA always contains:

* [ ] `L1_the_verdict_and_constitutional_outcome`
* [ ] `L6_behavioral_drift_and_monitoring`
* [ ] `L7_veto_and_execution_feedback`
* [ ] `governance_context.chain_of_custody`

---

## 9. Streamlit / Runtime Hygiene

If errors persist after fixes:

* [ ] Hard‑restart Streamlit (Ctrl+C, rerun)
* [ ] Clear `__pycache__` directories
* [ ] Temporarily print `__file__` to confirm correct module is loaded

---

## Final Principle

> **Governance logic must be boring, deterministic, and singular.**

If a refactor introduces ambiguity about *which loop fired* or *why execution was blocked*, it is architecturally incorrect.
