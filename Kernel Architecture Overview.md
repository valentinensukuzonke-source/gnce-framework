# Kernel Architecture Overview (GNCE)

This document gives new engineers a quick, high-signal view of how GNCE governs execution using **three governance loops**. The goal is to make it obvious **what blocks execution**, **what monitors execution**, and **what changes the governance model itself**.

---

## At a glance: the three governance loops

| Loop         | Name                                           | Where it lives                                 | Timing                            | Blocks execution? | Primary artifact/output                                                        |
| ------------ | ---------------------------------------------- | ---------------------------------------------- | --------------------------------- | ----------------- | ------------------------------------------------------------------------------ |
| **Loop 5.3** | **Veto Feedback Path (Non‑Execution Loop)**    | **Kernel L7** (Veto Path & Execution Feedback) | **Pre-execution (synchronous)**   | **YES**           | **Veto Artifact** + **Corrective Signal** → logged to **SARS**                 |
| **Loop 5.1** | **Continuous Drift Detection Agent (DDA)**     | **Kernel L6** (Drift Monitoring)               | **Post-execution (asynchronous)** | **NO**            | **DRIFT_ALERT** + Forced Recalibration Request (policy/model feedback)         |
| **Loop 5.2** | **Sovereign / Constitutional Governance Loop** | **Out-of-band (Block O / Block P)**            | **Slow / periodic**               | **NO**            | Approved governance changes → committed as Governance‑as‑Code + SARS rationale |

---

## Loop 5.3 — Veto Feedback Path (Non‑Execution Loop)

**Purpose:** stop unsafe or non-compliant actions **before** they execute.

**Trigger:** a request is blocked at **Constraint Validation (Block C)** or the **Execution Gate (Block G)** due to a **blocking policy failure** (typically HIGH/CRITICAL violations).

**What happens:**

1. GNCE computes an authoritative veto result in **L7**:

   * `veto_triggered` (true/false)
   * `veto_category` (e.g., `CONSTITUTIONAL_BLOCK`)
   * `execution_authorized` (false if veto triggers)
   * `veto_basis` (which articles/constraints caused the block)
2. GNCE emits a **Veto Artifact** and logs it to **SARS** (proof of prevention).
3. GNCE attaches a **Corrective Signal** back to the agent:

   * what violated
   * why
   * what must change
   * instruction to replan and resubmit

**Key rule:** *This loop is synchronous and blocking.* If it triggers, the request does not execute.

---

## Loop 5.1 — Continuous Drift Detection Agent (DDA)

**Purpose:** keep operational behavior aligned with policy over time by detecting drift **after** execution.

**Trigger:** monitoring detects a divergence between the system’s operational behavior and the intended policy baseline.

**Where:** L6 (Behavioral Drift & Monitoring)

**What happens:**

* L6 emits a drift outcome:

  * `NO_DRIFT` or `DRIFT_ALERT`
* If `DRIFT_ALERT`, GNCE:

  * records the alert in the ADRA
  * triggers a **Forced Recalibration Request** back into policy/model space

**Key rule:** *This loop is asynchronous and non-blocking.* Drift never blocks the current execution.

---

## Loop 5.2 — Sovereign / Constitutional Governance Loop

**Purpose:** govern the governance model itself (policies, constraints, weightings, constitutional updates) with human/regulatory approval.

**Where:**

* **Block O — Sovereign Governance Dashboard:** review GNCE governance posture, SARS audit trails, constitutional performance
* **Block P — Policy Feedback Commit Handler:** commit approved changes back as Governance‑as‑Code

**Characteristics:**

* slow, periodic, intentional
* out-of-band from runtime execution
* changes are auditable and may carry legal/regulatory consequences

**Key rule:** *This loop does not participate in live verdicts.* It changes the system’s constitutional/policy baseline over time.

---

## Practical engineering rules

### What blocks execution?

Only **Loop 5.3 (L7 veto)** blocks execution.

### What monitors execution?

Only **Loop 5.1 (L6 drift)** continuously monitors execution patterns.

### What changes GNCE’s governance model?

Only **Loop 5.2 (sovereign governance)** changes policies/constitution, and it is out-of-band.

---

## Data contract: where to read truth

* **Decision** (ALLOW/DENY), severity, oversight, safe-state → **L1**
* **Drift monitoring** and drift outcome → **L6**
* **Veto** status, basis, authorization, corrective signal → **L7**

**UI guidance:**

* The UI should read veto from `L7.veto_path_triggered` / `L7.veto_triggered` (not inferred from decision strings).
* The UI should read drift from `L6.drift_outcome`.
* Sovereign governance should only be shown as “invoked” when explicitly signaled (it is out-of-band).

---

## Tiny diagram (10-second mental model)

```text
            ┌───────────────────────────────┐
            │           Runtime             │
            │  (per request / per ADRA)     │
            └───────────────┬───────────────┘
                            │
                         Build L1
                            │
                            v
                   ┌─────────────────┐
                   │ L1: Verdict     │  decision/severity/oversight
                   └───────┬─────────┘
                           │
          ┌────────────────┴────────────────┐
          │                                 │
          v                                 v
┌──────────────────────┐          ┌──────────────────────┐
│ L7: Veto (Loop 5.3)  │          │ L6: Drift (Loop 5.1) │
│ PRE-execution        │          │ POST-execution       │
│ SYNC + BLOCKING      │          │ ASYNC + NON-BLOCKING │
│ veto_triggered?      │          │ drift_outcome?       │
└───────┬──────────────┘          └──────────┬───────────┘
        │                                     │
   if veto: STOP                              │
   + Veto Artifact                             │
   + Corrective Signal                         │
        │                                     │
        v                                     v
     SARS Ledger                         DRIFT_ALERT?
                                          -> Recalibrate


Out-of-band (not runtime):

   ┌────────────────────────────────────────────────────┐
   │ Sovereign Governance (Loop 5.2)                    │
   │ Block O (review)  ->  Block P (commit)             │
   │ Updates Governance-as-Code + writes SARS rationale  │
   └────────────────────────────────────────────────────┘
```

## One-sentence summary

> **L7 blocks, L6 watches, Sovereign governance changes the rules.**
