# ui/components/domain_catalog.py
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Any, Set

import streamlit as st
import pandas as pd
import altair as alt



# =========================================================
# GNCE HYBRID CONSTITUTIONAL TAXONOMY (Option D)
# =========================================================
# NOTE:
# - Each leaf node has a stable domain_id.
# - In your policy bundles (YAML/JSON), add a `domain_id`
#   that matches one of these IDs so the catalog can
#   highlight which domains were triggered by an ADRA.
# =========================================================

GNCE_DOMAIN_TAXONOMY: List[Dict[str, Any]] = [
    {
        "id": "safety",
        "label": "Safety & Harm Prevention",
        "description": "Physical, digital and psychological safety safeguards.",
        "children": [
            {
                "id": "safety.child_protection",
                "label": "Child & Minor Safety",
                "regimes": ["DSA", "EU AI Act"],
                "examples": [
                    "CSAM detection and removal",
                    "Protection of minors from harmful content",
                ],
            },
            {
                "id": "safety.high_risk_ai",
                "label": "High-Risk AI Systems (Annex III)",
                "regimes": ["EU AI Act"],
                "examples": [
                    "Biometric identification / categorisation",
                    "Critical infrastructure and health AI systems",
                ],
            },
            {
                "id": "safety.physical_autonomy",
                "label": "Physical Safety & Robotics",
                "regimes": ["EU AI Act", "Product Safety"],
                "examples": [
                    "Autonomous driving & emergency braking",
                    "Robotic arm / industrial robots safety",
                    "Drone navigation & geofencing",
                ],
            },
            {
                "id": "safety.behavioural_harm",
                "label": "Behavioural Harm & Addiction",
                "regimes": ["DSA", "EU AI Act"],
                "examples": [
                    "Addictive recommender loops",
                    "Self-harm content surfacing",
                ],
            },
        ],
    },
    {
        "id": "content_governance",
        "label": "Content & Speech Governance",
        "description": "How content is ranked, amplified, removed or left up.",
        "children": [
            {
                "id": "content.illegal_notice_action",
                "label": "Illegal Content, Notice & Action",
                "regimes": ["DSA"],
                "examples": [
                    "Notice & action workflows",
                    "Handling of terrorist content",
                    "Unlawful hate speech",
                ],
            },
            {
                "id": "content.recommenders",
                "label": "Recommender Systems & Ranking",
                "regimes": ["DSA"],
                "examples": [
                    "News feed ranking",
                    "Video recommendation",
                    "Influence of engagement-based optimisation",
                ],
            },
            {
                "id": "content.political_ads",
                "label": "Political / Issue Ads & Manipulation",
                "regimes": ["DSA", "EU AI Act"],
                "examples": [
                    "Targeting political opinions",
                    "Sensitive attribute micro-targeting",
                ],
            },
            {
                "id": "content.trusted_flaggers",
                "label": "Trusted Flaggers & Complaints",
                "regimes": ["DSA"],
                "examples": [
                    "Trusted flagger queues",
                    "Internal complaints handling",
                ],
            },
        ],
    },
    {
        "id": "user_rights",
        "label": "User Rights, Privacy & Data Protection",
        "description": "GDPR-style rights & lawful processing obligations.",
        "children": [
            {
                "id": "user_rights.lawful_basis",
                "label": "Lawful Basis & Consent",
                "regimes": ["GDPR"],
                "examples": [
                    "Consent for personalised ads",
                    "Legitimate interest vs consent checks",
                ],
            },
            {
                "id": "user_rights.profiling_scoring",
                "label": "Profiling & Scoring",
                "regimes": ["GDPR", "EU AI Act"],
                "examples": [
                    "Credit scoring",
                    "Automated risk / fraud scoring",
                ],
            },
            {
                "id": "user_rights.data_minimisation",
                "label": "Data Minimisation & Purpose Limitation",
                "regimes": ["GDPR"],
                "examples": [
                    "Retention & deletion policies",
                    "Secondary use of platform telemetry",
                ],
            },
            {
                "id": "user_rights.data_subject_rights",
                "label": "Data Subject Rights",
                "regimes": ["GDPR"],
                "examples": [
                    "Access, rectification, erasure",
                    "Portability & restriction of processing",
                ],
            },
            {
                "id": "user_rights.data_transfers",
                "label": "Data Transfers & Third Countries",
                "regimes": ["GDPR"],
                "examples": [
                    "Standard Contractual Clauses checks",
                    "Cross-border data movement controls",
                ],
            },
        ],
    },
    {
        "id": "platform_integrity",
        "label": "Platform Integrity & Abuse",
        "description": "Trust, safety and abuse of platform mechanics.",
        "children": [
            {
                "id": "platform.fake_accounts",
                "label": "Fake Accounts, Bots & Inauthentic Behaviour",
                "regimes": ["DSA"],
                "examples": [
                    "Coordinated inauthentic behaviour",
                    "Botnets for manipulation",
                ],
            },
            {
                "id": "platform.spam_automation",
                "label": "Spam & Automation Abuse",
                "regimes": ["DSA"],
                "examples": [
                    "Mass messaging / scraping",
                    "Abuse of APIs / automation features",
                ],
            },
            {
                "id": "platform.fraud_scams",
                "label": "Fraud, Scams & Financial Abuse",
                "regimes": ["DSA", "Financial"],
                "examples": [
                    "Payment fraud detection",
                    "Crypto / investment scams",
                ],
            },
            {
                "id": "platform.misuse_reporting",
                "label": "Misuse of Reporting & Appeals",
                "regimes": ["DSA"],
                "examples": [
                    "Harassment via abuse reports",
                    "Bad-faith flagging campaigns",
                ],
            },
        ],
    },
    {
        "id": "autonomy_agents",
        "label": "Autonomy, AI Agents & Automation",
        "description": "Agentic systems, autonomy levels and control surfaces.",
        "children": [
            {
                "id": "autonomy.autonomous_mobility",
                "label": "Autonomous Mobility & Drones",
                "regimes": ["EU AI Act"],
                "examples": [
                    "Self-driving vehicles",
                    "Drone routing & no-fly enforcement",
                ],
            },
            {
                "id": "autonomy.ai_agents",
                "label": "AI Agents & Multi-Agent Systems",
                "regimes": ["EU AI Act", "Internal GN"],
                "examples": [
                    "Task execution agents",
                    "Multi-agent orchestration",
                ],
            },
            {
                "id": "autonomy.decision_support",
                "label": "Decision Support & Automated Decisions",
                "regimes": ["GDPR", "EU AI Act"],
                "examples": [
                    "Human-in-the-loop decision making",
                    "Automated rejection/approval flows",
                ],
            },
            {
                "id": "autonomy.safety_overrides",
                "label": "Safety Overrides & Kill-Switch",
                "regimes": ["EU AI Act", "Product Safety"],
                "examples": [
                    "Kill-switch wiring",
                    "Safe-state fallbacks",
                ],
            },
        ],
    },
    {
        "id": "competition_economic",
        "label": "Economic & Competition Governance",
        "description": "Gatekeeper conduct, self-preferencing and lock-in.",
        "children": [
            {
                "id": "competition.gatekeeper_conduct",
                "label": "Gatekeeper Conduct (DMA)",
                "regimes": ["DMA"],
                "examples": [
                    "Ranking own services above rivals",
                    "Restrictive access to core platform services",
                ],
            },
            {
                "id": "competition.self_preferencing",
                "label": "Self-Preferencing & Interoperability",
                "regimes": ["DMA"],
                "examples": [
                    "Preferential surfacing of own products",
                    "Refusal to interoperate",
                ],
            },
            {
                "id": "competition.dark_patterns",
                "label": "Dark Patterns & Lock-In",
                "regimes": ["DMA", "DSA"],
                "examples": [
                    "Obstructing switching / cancelling",
                    "Interface designs that trick users",
                ],
            },
            {
                "id": "competition.data_access_portability",
                "label": "Data Access & Portability (DMA / DSA)",
                "regimes": ["DMA", "DSA"],
                "examples": [
                    "Business user data access",
                    "Multi-homing & portability enforcement",
                ],
            },
        ],
    },
    {
        "id": "cloud_infra",
        "label": "Cloud, Infrastructure & Workload Governance",
        "description": "Where and how workloads run, with what controls.",
        "children": [
            {
                "id": "cloud.workload_placement",
                "label": "Workload Placement & Sovereign Boundaries",
                "regimes": ["Internal GN"],
                "examples": [
                    "Data residency",
                    "Cross-cloud / multi-region placement rules",
                ],
            },
            {
                "id": "cloud.identity_access",
                "label": "Identity & Access Governance",
                "regimes": ["Security", "CIS"],
                "examples": [
                    "IAM roles and policies",
                    "Privileged access workflows",
                ],
            },
            {
                "id": "cloud.logging_evidence",
                "label": "Logging, Monitoring & Evidence",
                "regimes": ["Internal GN", "Audit"],
                "examples": [
                    "Tamper-evident logging",
                    "ADRA / SARS persistence",
                ],
            },
            {
                "id": "cloud.dr_resilience",
                "label": "DR, Failover & Resilience",
                "regimes": ["Internal GN"],
                "examples": [
                    "Failover safety constraints",
                    "DR runbooks and governance",
                ],
            },
        ],
    },
    {
        "id": "governance_process",
        "label": "Governance Process & Auditability",
        "description": "How the organisation proves and maintains compliance.",
        "children": [
            {
                "id": "governance.risk_management",
                "label": "Risk Management & Assessments",
                "regimes": ["DSA", "EU AI Act"],
                "examples": [
                    "Systemic risk assessments (Art. 34 DSA)",
                    "High-risk AI risk management (Art. 9 AI Act)",
                ],
            },
            {
                "id": "governance.documentation",
                "label": "Documentation & Technical Files",
                "regimes": ["EU AI Act"],
                "examples": [
                    "Technical documentation (Art. 11 AI Act)",
                    "Model cards & system cards",
                ],
            },
            {
                "id": "governance.incident_reporting",
                "label": "Incident Reporting & Escalation",
                "regimes": ["DSA", "EU AI Act"],
                "examples": [
                    "Serious incidents notification",
                    "Security breach reporting",
                ],
            },
            {
                "id": "governance.audit_trails",
                "label": "Audit Trails, ADRAs & SARS",
                "regimes": ["Internal GN"],
                "examples": [
                    "ADRA immutability",
                    "SARS ledger traceability",
                ],
            },
        ],
    },
]


# =========================================================
# HELPERS
# =========================================================

def _normalize_domain_id(domain_id: str) -> str:
    """
    Map regime-style domain ids to taxonomy leaf ids (UI-side safety net).
    Kernel should ideally emit leaf ids directly, but UI can normalize.
    """
    d = str(domain_id or "").strip()
    u = d.upper()

    if u == "DSA":
        return "content.illegal_notice_action"
    if u == "DMA":
        return "competition.gatekeeper_conduct"
    if u in {"GDPR", "POPIA"}:
        return "user_rights.data_minimisation"
    if u in {"EU AI ACT", "EU_AI_ACT", "EU_AI_ACT_ISO_42001"}:
        return "safety.high_risk_ai"

    return d


def _collect_triggered_domain_ids(adra: Dict[str, Any]) -> Set[str]:
    """
    Extracts domain IDs that were triggered by this ADRA.

    EXPECTATION (recommended):
      - In your policy bundles, each policy has a `domain_id`
        matching one of the GNCE_DOMAIN_TAXONOMY leaf IDs.

    Example policy snippet:
      - id: dsa_art_34_systemic_risk
        regime: DSA
        article: 34
        domain_id: governance.risk_management
    """
    triggered: Set[str] = set()

    if not isinstance(adra, dict):
        return triggered

    # Preferred: L4 policy lineage with explicit domain_id
    l4 = adra.get("L4_policy_lineage_and_constitution", {}) or {}
    for pol in l4.get("policies_triggered", []) or []:
        domain_id = pol.get("domain_id") or pol.get("domain")
        if isinstance(domain_id, str) and domain_id.strip():
            triggered.add(domain_id.strip())

    # Optional fallback: top-level list of domains
    for d in adra.get("domains_triggered", []) or []:
        if isinstance(d, str) and d.strip():
            triggered.add(d.strip())

    return triggered

def _severity_rank(sev: str) -> int:
    s = str(sev or "").upper().strip()
    return {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}.get(s, 0)

def _is_triggered_policy(pol: Dict[str, Any]) -> bool:
    status = str(pol.get("status") or "").upper().strip()
    if status in {"TRIGGERED", "APPLICABLE", "ENFORCED", "EVALUATED", "MATCHED", "HIT", "VIOLATED"}:
        return True
    # fallback flags
    if pol.get("triggered") is True or pol.get("applies") is True:
        return True
    return False

def _coverage_badge(posture: Dict[str, Any], is_triggered: bool) -> Dict[str, str]:
    """
    Market-ready coverage badge for Domain Catalog.
    No 'stub' language. Clear constitutional semantics.
    """
    total = int(posture.get("total") or 0)
    viol = int(posture.get("violations") or 0)
    max_sev = str(posture.get("max_severity") or "LOW").upper().strip() or "LOW"

    # No L4 lines for this leaf across session/ADRA store -> constitutional coverage only
    if total == 0 and not is_triggered:
        return {"text": "🧭 Constitutional coverage", "color": "#94a3b8"}  # slate

    # Triggered but no policy-line impacts recorded -> still constitutional coverage (seen/recognized)
    if total == 0 and is_triggered:
        return {"text": "🧭 Constitutional coverage (recognized)", "color": "#94a3b8"}

    if viol > 0:
        color = {
            "LOW": "#22c55e",
            "MEDIUM": "#f97316",
            "HIGH": "#ef4444",
            "CRITICAL": "#a855f7",
        }.get(max_sev, "#64748b")
        return {"text": "🚨 Violations present", "color": color}

    return {"text": "✅ Article-evaluated (clean)", "color": "#22c55e"}

def _rollup_icon_for_node(
    node: Dict[str, Any],
    triggered_ids: Set[str],
    posture_map: Dict[str, Dict[str, Any]],
) -> str:
    """
    Roll up child posture into a single icon for parent nodes.
    Priority: 🚨 violations > ✅ evaluated-clean > 🧭 constitutional coverage.
    """

    def _leaf_icon(domain_id: str) -> str:
        is_triggered = domain_id in triggered_ids
        posture = posture_map.get(domain_id, {}) or {}
        cov = _coverage_badge(posture, is_triggered)
        txt = str(cov.get("text") or "")
        if txt.startswith("🚨"):
            return "🚨"
        if txt.startswith("✅"):
            return "✅"
        return "🧭"

    # Recursive walk
    icons: List[str] = []
    children = node.get("children") or []
    if children:
        for ch in children:
            icons.append(_rollup_icon_for_node(ch, triggered_ids, posture_map))
    else:
        # leaf node
        domain_id = str(node.get("id") or "")
        if domain_id:
            icons.append(_leaf_icon(domain_id))

    # Priority roll-up
    if "🚨" in icons:
        return "🚨"
    if "✅" in icons:
        return "✅"
    return "🧭"


def _is_violation_policy(pol: Dict[str, Any]) -> bool:
    status = str(pol.get("status") or "").upper().strip()
    bad_statuses = {
        "VIOLATED", "FAIL", "FAILED", "NON_COMPLIANT", "NONCOMPLIANT",
        "BREACH", "BLOCK", "DENY", "VETO", "REJECT", "REJECTED", "ERROR",
    }
    issues = pol.get("issues") or pol.get("violations") or pol.get("findings") or []
    has_issues = isinstance(issues, list) and len(issues) > 0
    return (status in bad_statuses) or has_issues


def _policy_line_label(pol: Dict[str, Any]) -> str:
    regime = (pol.get("regime") or pol.get("framework") or "").strip()
    article = (pol.get("article") or pol.get("section") or pol.get("clause") or "").strip()
    title = (pol.get("title") or pol.get("name") or pol.get("category") or "").strip()
    pol_id = (pol.get("id") or pol.get("policy_id") or "").strip()

    bits = []
    if regime:
        bits.append(regime)
    if article:
        bits.append(f"Art/§ {article}")
    if title:
        bits.append(title)
    elif pol_id:
        bits.append(pol_id)

    return " · ".join(bits).strip()


def _collect_domain_violation_posture(adra: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    posture[domain_id] = {
        "total": int,
        "triggered": int,
        "violations": int,
        "max_severity": str,
        "impacts": List[Dict[str, Any]],  # <- dynamic per-policy items for UI
    }
    """
    posture: Dict[str, Dict[str, Any]] = {}

    if not isinstance(adra, dict):
        return {}

    # ✅ IMPORTANT: define adra_id once for this ADRA
    adra_id = str(
        adra.get("adra_id")
        or adra.get("ADRA_id")
        or adra.get("id")
        or adra.get("_id")
        or ""
    ).strip() or "unknown"

    # Ensure adra_id is always defined (prevents UnboundLocalError)
    adra_id = str(adra.get("adra_id") or adra.get("id") or "").strip() or "unknown"

    # --- identify ADRA for click-through
    adra_id = str(
        adra.get("adra_id")
        or adra.get("ADRA_ID")
        or adra.get("id")
        or adra.get("_id")
        or ""
    ).strip() or "unknown"

    l4 = adra.get("L4_policy_lineage_and_constitution", {}) or {}
    policies = l4.get("policies_triggered", []) or []

    for pol in policies:
        if not isinstance(pol, dict):
            continue

        domain_id = pol.get("domain_id") or pol.get("domain")
        if not isinstance(domain_id, str) or not domain_id.strip():
            continue
        domain_id = _normalize_domain_id(domain_id.strip())


        sev = str(pol.get("severity") or "LOW").upper().strip() or "LOW"
        status = str(pol.get("status") or "").upper().strip()

        entry = posture.setdefault(
            domain_id,
            {"total": 0, "triggered": 0, "violations": 0, "max_severity": "LOW", "impacts": []},
        )
        entry["total"] += 1

        triggered = _is_triggered_policy(pol)
        violated = _is_violation_policy(pol)

        if triggered:
            entry["triggered"] += 1

        if violated:
            entry["violations"] += 1
            if _severity_rank(sev) > _severity_rank(entry["max_severity"]):
                entry["max_severity"] = sev

        # ---------- dynamic impact line ----------
        label = _policy_line_label(pol)
        detail = (pol.get("violation_detail") or pol.get("finding") or pol.get("notes") or pol.get("impact_on_verdict") or "").strip()
        if not isinstance(detail, str):
            detail = str(detail).strip()

        # Only store lines that are actually triggered/violated (keeps UI clean)
        if triggered or violated:
            key = f"{label}|{sev}|{status}|{detail}"
            # de-dupe
            existing_keys = {x.get("_k") for x in entry["impacts"]}
            if key not in existing_keys:
                policy_id = str(
                    pol.get("policy_id")
                    or pol.get("id")
                    or pol.get("rule_id")
                    or pol.get("code")
                    or ""
                ).strip()

                entry["impacts"].append(
                    {
                        "label": label or domain_id,
                        "severity": sev,
                        "status": status,
                        "detail": detail,
                        "domain_id": domain_id,
                        "adra_id": adra_id,
                        "policy_id": policy_id,
                        "_k": key,
                    }
                )

    # Sort impacts: violations first, then severity desc
    for dom_id, meta in posture.items():
        impacts = meta.get("impacts") or []
        impacts.sort(
            key=lambda x: (
                0 if str(x.get("status", "")).upper() in {"VIOLATED", "DENY", "BLOCK", "FAIL", "FAILED"} else 1,
                -_severity_rank(str(x.get("severity") or "LOW")),
            )
        )
        # keep a sensible cap (avoid 72 lines exploding the page)
        if len(impacts) > 200:
            del impacts[200:]

    return posture

def _find_sars_evidence(
    sars_ledger: List[Dict[str, Any]] | None,
    adra_id: str,
    policy_id: str,
    domain_id: str,
    limit: int = 6,
) -> List[Dict[str, Any]]:
    """
    Best-effort evidence resolver:
    - Prefer exact adra_id match
    - Prefer policy_id match when available
    - Fallback to domain_id match
    """
    if not isinstance(sars_ledger, list) or not sars_ledger:
        return []

    adra_id = (adra_id or "").strip()
    policy_id = (policy_id or "").strip()
    domain_id = (domain_id or "").strip()

    hits: List[Dict[str, Any]] = []

    def _score(e: Dict[str, Any]) -> int:
        s = 0
        if adra_id and str(e.get("adra_id") or e.get("id") or "").strip() == adra_id:
            s += 50
        if policy_id and str(e.get("policy_id") or e.get("rule_id") or e.get("policy") or "").strip() == policy_id:
            s += 25
        if domain_id and str(e.get("domain_id") or e.get("domain") or "").strip() == domain_id:
            s += 10
        # Prefer violated items
        stt = str(e.get("status") or e.get("outcome") or "").upper().strip()
        if stt in {"VIOLATED", "DENY", "BLOCK", "FAIL", "FAILED"}:
            s += 5
        return s

    for e in sars_ledger:
        if not isinstance(e, dict):
            continue
        sc = _score(e)
        if sc > 0:
            hits.append((sc, e))  # type: ignore

    hits.sort(key=lambda x: x[0], reverse=True)
    out = [e for _, e in hits[:limit]]
    return out

def _render_leaf(
    node: Dict[str, Any],
    triggered_ids: Set[str],
    current_triggered_ids: Set[str],
    posture_map: Dict[str, Dict[str, Any]],
    adra_store: Dict[str, Any] | None,
    sars_ledger: List[Dict[str, Any]] | None,
    collapse_by_severity: bool,
    min_severity: str,
) -> None:

    domain_id = node["id"]
    label = node["label"]
    regimes = node.get("regimes", [])
    examples = node.get("examples", [])

    is_triggered = domain_id in triggered_ids
    is_currently_triggered = domain_id in current_triggered_ids

    posture = posture_map.get(domain_id, {}) or {}
    violations = int(posture.get("violations") or 0)
    max_sev = str(posture.get("max_severity") or "LOW").upper().strip() or "LOW"

    # Bullet should match the coverage badge (tree reads instantly)
    cov = _coverage_badge(posture, is_triggered)
    cov_text = str(cov.get("text") or "")

    if cov_text.startswith("🚨"):
        bullet_prefix = "🚨"
    elif cov_text.startswith("✅"):
        bullet_prefix = "✅"
    else:
        bullet_prefix = "🧭"
    
    # Add a special indicator if this domain was triggered in the CURRENT ADRA
    current_indicator = ""
    if is_currently_triggered:
        current_indicator = " 🔥"

    regimes_str = ""
    if regimes:
        regimes_str = " · " + ", ".join(regimes)

    # Coverage badge (always show, market-ready)
    cov_html = (
        f" <span style='display:inline-block; margin-left:8px; padding:2px 8px; "
        f"border-radius:999px; font-size:0.75rem; font-weight:700; "
        f"border:1px solid {cov['color']}; color:{cov['color']}; background:rgba(255,255,255,0.02);'>"
        f"{cov['text']}"
        f"</span>"
    )

    # Severity badge (only when violated)
    sev_html = ""
    if violations > 0:
        color = {
            "LOW": "#22c55e",
            "MEDIUM": "#f97316",
            "HIGH": "#ef4444",
            "CRITICAL": "#a855f7",
        }.get(max_sev, "#64748b")
        sev_html = (
            f" <span style='display:inline-block; margin-left:8px; padding:2px 8px; "
            f"border-radius:999px; font-size:0.75rem; font-weight:700; "
            f"border:1px solid {color}; color:{color}; background:rgba(255,255,255,0.02);'>"
            f"{max_sev} · {violations} violation(s)"
            f"</span>"
        )

    badge_html = cov_html + sev_html

    st.markdown(
        f"{bullet_prefix} **{label}**{current_indicator}{badge_html}  \n"
        f"<span style='font-size:0.8rem; opacity:0.7;'>"
        f"`{domain_id}`{regimes_str}"
        f"</span>",
        unsafe_allow_html=True,
    )

    impacts = posture.get("impacts") or []

    # -----------------------------
    # Leaf-local helpers
    # -----------------------------
    def _severity_rank(s: str) -> int:
        m = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        return m.get(str(s or "").upper().strip(), 0)

    def _sev_color(s: str) -> str:
        return {
            "LOW": "#22c55e",
            "MEDIUM": "#f97316",
            "HIGH": "#ef4444",
            "CRITICAL": "#a855f7",
        }.get(str(s or "").upper().strip(), "#64748b")

    def _remediation_text(it: Dict[str, Any]) -> str:
        label_txt = str(it.get("label") or "").lower()
        if "systemic risk" in label_txt or "art. 34" in label_txt:
            return "Create/refresh a systemic risk assessment, document mitigations, assign owners, and attach evidence pack."
        if "independent audit" in label_txt or "art. 35" in label_txt:
            return "Schedule an independent audit, define audit scope, capture audit artifacts, and link evidence to the ADRA."
        if "crisis" in label_txt or "incident" in label_txt or "art. 36" in label_txt:
            return "Define crisis protocol + escalation runbook, test it, and attach incident drill evidence."
        if "minors" in label_txt or "art. 39" in label_txt:
            return "Implement/verify child protection controls, enforce hard blocks where required, and maintain audit trail."
        return "Assign control owner, define remediation task, implement safeguard, and attach evidence proving closure."

    # -----------------------------
    # Severity filter (passed-in min_severity)
    # -----------------------------
    impacts = [
        it for it in impacts
        if _severity_rank(str(it.get("severity") or "LOW")) >= _severity_rank(min_severity)
    ]

    # ✅ If we have triggered/violated impacts, show them dynamically
    if isinstance(impacts, list) and impacts:

        def _render_one_impact(it: Dict[str, Any]) -> None:
            sev = str(it.get("severity") or "LOW").upper().strip() or "LOW"
            stt = str(it.get("status") or "").upper().strip()
            label_txt = str(it.get("label") or "").strip()
            detail = str(it.get("detail") or "").strip()

            color = _sev_color(sev)
            pill = (
                f"<span style='display:inline-block;margin-left:8px;padding:2px 8px;"
                f"border-radius:999px;font-size:0.72rem;font-weight:700;"
                f"border:1px solid {color};color:{color};background:rgba(255,255,255,0.02);'>"
                f"{sev}{(' · ' + stt) if stt else ''}</span>"
            )

            st.markdown(f"• {label_txt}{pill}", unsafe_allow_html=True)
            if detail:
                st.caption(detail)

            # --- Actions: click-through + remediation + evidence
            adra_id = str(it.get("adra_id") or "").strip()
            policy_id = str(it.get("policy_id") or "").strip()
            dom_id = str(it.get("domain_id") or domain_id).strip()
            k = str(it.get("_k") or f"{dom_id}:{policy_id}:{label_txt}")  # stable widget key

            a1, a2, a3 = st.columns([1, 1, 2])

            with a1:
                if st.button("📌 Open ADRA", key=f"open_adra_{domain_id}_{k}"):
                    if not adra_id:
                        st.warning("No ADRA ID found for this impact yet.")
                    else:
                        st.session_state["adara_browser_target"] = adra_id
                        st.toast("📌 ADRA target set — open the ADRA Browser tab to view it.")
                        st.rerun()

            with a2:
                if st.button("🛠 Remediation", key=f"remed_{domain_id}_{k}"):
                    st.session_state[f"remed_show_{domain_id}_{k}"] = True

            with a3:
                if st.button("🧾 Evidence", key=f"evid_{domain_id}_{k}"):
                    st.session_state[f"evid_show_{domain_id}_{k}"] = True

                # -------------------------
                # Inline ADRA viewer (so "Open ADRA" visibly works)
                # -------------------------
                if st.session_state.get(f"show_adra_inline_{domain_id}_{k}"):
                    with st.expander("📚 ADRA (inline view)", expanded=True):
                        a = None
                        if isinstance(adra_store, dict) and adra_id:
                            a = adra_store.get(adra_id)

                        if not isinstance(a, dict):
                            st.info("ADRA not found in adra_store yet. Open the ADRA Browser tab to load from disk exports.")
                        else:
                            st.markdown(f"**ADRA ID:** `{a.get('adra_id','')}`")
                            st.json(a)

            if st.session_state.get(f"remed_show_{domain_id}_{k}"):
                with st.expander("🛠 Suggested remediation", expanded=True):
                    st.write(_remediation_text(it))

            if st.session_state.get(f"evid_show_{domain_id}_{k}"):
                with st.expander("🧾 SARS evidence (best match)", expanded=True):
                    ev = _find_sars_evidence(sars_ledger, adra_id, policy_id, dom_id, limit=6)
                    if not ev:
                        st.info("No matching SARS entries found for this impact yet.")
                    else:
                        for e in ev:
                            title = str(e.get("title") or e.get("event") or e.get("id") or "SARS Entry")
                            st.markdown(f"**{title}**")
                            st.caption(str(e.get("detail") or e.get("summary") or e.get("why") or "")[:400])

        # collapse-by-severity grouping (passed-in collapse_by_severity)
        if collapse_by_severity:
            buckets = {"CRITICAL": [], "HIGH": [], "MEDIUM": [], "LOW": []}
            for it in impacts:
                buckets[str(it.get("severity") or "LOW").upper().strip() or "LOW"].append(it)

            for sev_band in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
                items = buckets.get(sev_band) or []
                if not items:
                    continue
                with st.expander(
                    f"{sev_band} obligations ({len(items)})",
                    expanded=(sev_band in {"CRITICAL", "HIGH"}),
                ):
                    for it in items:
                        _render_one_impact(it)
    
        else:
            # ----------------------------------------------------
            # Usability: compact + paginated impacts to prevent scroll walls
            # ----------------------------------------------------
            compact = bool(st.session_state.get("domain_compact_mode", True))
            page_size = int(st.session_state.get("domain_leaf_page_size", 10))

            # stable per-leaf key
            leaf_key = f"leaf_page::{domain_id}"
            page = int(st.session_state.get(leaf_key, 0))

            total = len(impacts)
            max_page = max(0, (total - 1) // page_size)
            page = max(0, min(page, max_page))
            st.session_state[leaf_key] = page

            start = page * page_size
            end = min(total, start + page_size)
            page_items = impacts[start:end]

            # Pager controls
            p1, p2, p3 = st.columns([1, 2, 1])
            with p1:
                if st.button("⬅️ Prev", key=f"{leaf_key}_prev", disabled=(page == 0)):
                    st.session_state[leaf_key] = page - 1
                    st.rerun()
            with p2:
                st.caption(f"Showing **{start+1}-{end}** of **{total}** obligations")
            with p3:
                if st.button("Next ➡️", key=f"{leaf_key}_next", disabled=(page >= max_page)):
                    st.session_state[leaf_key] = page + 1
                    st.rerun()

            if compact:
                # Compact list: only show headline + severity pill; expand for actions/details
                for it in page_items:
                    sev = str(it.get("severity") or "LOW").upper().strip() or "LOW"
                    stt = str(it.get("status") or "").upper().strip()
                    label_txt = str(it.get("label") or "").strip()
                    detail = str(it.get("detail") or "").strip()

                    color = _sev_color(sev)
                    pill = (
                        f"<span style='display:inline-block;margin-left:8px;padding:2px 8px;"
                        f"border-radius:999px;font-size:0.72rem;font-weight:700;"
                        f"border:1px solid {color};color:{color};background:rgba(255,255,255,0.02);'>"
                        f"{sev}{(' · ' + stt) if stt else ''}</span>"
                    )

                    with st.expander(f"• {label_txt}  [{sev}{(' · ' + stt) if stt else ''}]", expanded=False):
                        st.markdown(f"{pill}", unsafe_allow_html=True)
                        if detail:
                            st.caption(detail)
                        # Render details/actions only when the user opts in
                        show_actions = st.toggle("Show actions (ADRA / remediation / evidence)", value=False, key=f"actions_{leaf_key}_{it.get('_k')}")
                        if show_actions:
                            _render_one_impact(it)
                        else:
                            st.caption("Actions hidden in compact mode. Toggle on to view.")

            else:
                # Full mode: render actions directly for each item on the page
                for it in page_items:
                    _render_one_impact(it)

    # fallback to static taxonomy examples only when nothing has triggered
    elif examples:
        ex = "; ".join(examples[:2])
        st.caption(f"e.g. {ex}")

def _render_node(
    node: Dict[str, Any],
    triggered_ids: Set[str],
    current_triggered_ids: Set[str],
    posture_map: Dict[str, Dict[str, Any]],
    adra_store: Dict[str, Any] | None,
    sars_ledger: List[Dict[str, Any]] | None,
    collapse_by_severity: bool,
    min_severity: str,
) -> None:

    children = node.get("children")

    if children:
        icon = _rollup_icon_for_node(node, triggered_ids, posture_map)
        child_count = len(children)
        
        # Check if any child is currently triggered
        has_currently_triggered = False
        if current_triggered_ids:
            def _check_current_triggered(n: Dict[str, Any]) -> bool:
                if "children" in n:
                    for child in n["children"]:
                        if _check_current_triggered(child):
                            return True
                else:
                    return n.get("id") in current_triggered_ids
                return False
            
            has_currently_triggered = _check_current_triggered(node)

        with st.expander(f"{icon} {node['label']}  ·  {child_count} items{' 🔥' if has_currently_triggered else ''}", expanded=has_currently_triggered):
            if node.get("description"):
                st.caption(node["description"])

            # Keep your emoji captions (unchanged)
            if icon == "🚨":
                st.caption("🚨 Descendant violations present in this branch.")
            elif icon == "✅":
                st.caption("✅ Descendants are article-evaluated with no violations in this branch.")
            else:
                st.caption("🧭 Constitutional coverage only (no L4 article trace in this branch).")

            # Scalable rendering: show first N children, expand the rest
            max_preview = 12  # tune this number anytime
            head = children[:max_preview]
            tail = children[max_preview:]

            for child in head:
                _render_node(
                    child,
                    triggered_ids,
                    current_triggered_ids,
                    posture_map,
                    adra_store,
                    sars_ledger,
                    collapse_by_severity,
                    min_severity,
                )

            if tail:
                with st.expander(f"Show {len(tail)} more…", expanded=False):
                    for child in tail:
                        _render_node(
                            child,
                            triggered_ids,
                            current_triggered_ids,
                            posture_map,
                            adra_store,
                            sars_ledger,
                            collapse_by_severity,
                            min_severity,
                        )

    else:
        _render_leaf(node, triggered_ids, current_triggered_ids, posture_map, adra_store, sars_ledger, collapse_by_severity, min_severity)

def _render_domain_severity_heatmap() -> None:
    """
    Session-wide domain × severity heatmap, driven by L4 policy severities
    across all ADRAs in this session.
    """
    adra_store = st.session_state.get("gn_adra_store", {}) or {}
    if not adra_store:
        st.info("No ADRAs in this session yet — run Gordian Nexus to populate the domain heatmap.")
        return

    # ---- helper: normalise severity band ----------------------------------
    from typing import Any as _Any

    def _severity_bucket(_raw: _Any) -> str:
        num_map = {1: "LOW", 2: "MEDIUM", 3: "HIGH", 4: "CRITICAL"}
        if isinstance(_raw, (int, float)):
            return num_map.get(int(_raw), "UNKNOWN")
        if isinstance(_raw, str):
            s = _raw.strip().upper()
            if s.isdigit():
                return num_map.get(int(s), "UNKNOWN")
            return s or "UNKNOWN"
        return "UNKNOWN"

    # ---- simple regime/domain registry ------------------------------------
    _DOMAIN_REGISTRY = [
        {"id": "DSA",        "label": "EU DSA",        "tokens": ["DSA", "DIGITAL SERVICES ACT"]},
        {"id": "DMA",        "label": "EU DMA",        "tokens": ["DMA", "DIGITAL MARKETS ACT"]},
        {"id": "EU_AI_ACT",  "label": "EU AI Act",     "tokens": ["EU AI ACT", "EUAIA"]},
        {"id": "ISO_42001",  "label": "ISO 42001",     "tokens": ["ISO 42001", "IEC 42001"]},
        {"id": "NIST_AIRM",  "label": "NIST AI RMF",   "tokens": ["NIST AI RMF", "US AI EO"]},
        {"id": "DATA_PRIV",  "label": "Data protection","tokens": ["GDPR", "POPIA", "CCPA"]},
        {"id": "CYBER_SOV",  "label": "Cyber / NIS2",  "tokens": ["NIS2", "CRITICAL INFRASTRUCTURE"]},
    ]

    def _classify_domain(policy: dict) -> str:
        txt = " ".join(
            str(policy.get(k, ""))
            for k in ["domain", "framework", "regime", "article", "category", "notes"]
        ).upper()
        for dom in _DOMAIN_REGISTRY:
            if any(tok in txt for tok in dom["tokens"]):
                return dom["label"]
        return "Other / Unmapped"

    # ---- aggregate L4 policies across all ADRAs ---------------------------
    score_map = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
    agg = defaultdict(lambda: {"count": 0, "risk_score": 0.0})

    for _adra in adra_store.values():
        l4a = (
            _adra.get("L4_policy_lineage_and_constitution", {})
            or _adra.get("L4_policy_evaluation", {})
            or {}
        )
        policies = l4a.get("policies_triggered", []) or []
        for p in policies:
            domain_label = _classify_domain(p)
            sev_band = _severity_bucket(
                p.get("severity")
                or p.get("severity_level")
                or p.get("severity_score")
                or p.get("criticality")
            )
            status = (p.get("status") or "UNKNOWN").upper()

            key = (domain_label, sev_band)
            agg[key]["count"] += 1
            if status == "VIOLATED" and sev_band in score_map:
                agg[key]["risk_score"] += score_map[sev_band]

    heat_rows = []
    for (dom_label, sev_band), vals in agg.items():
        heat_rows.append(
            {
                "Domain": dom_label,
                "Severity band": sev_band,
                "Policies": vals["count"],
                "Risk score": vals["risk_score"],
            }
        )

    if not heat_rows:
        st.info("No violated L4 policies recorded yet, so the domain heatmap is empty.")
        return

    df_heat = pd.DataFrame(heat_rows)

    severity_order = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    df_heat["Severity band"] = pd.Categorical(
        df_heat["Severity band"],
        categories=severity_order,
        ordered=True,
    )
    df_heat = df_heat.sort_values(["Domain", "Severity band"])

    # GNCE palette: LOW = green, MEDIUM = orange, HIGH = red, CRITICAL = purple
    severity_gradient = [
        "#22c55e",  # LOW
        "#f97316",  # MEDIUM
        "#ef4444",  # HIGH
        "#a855f7",  # CRITICAL
    ]

    min_risk = float(df_heat["Risk score"].min())
    max_risk = float(df_heat["Risk score"].max())
    if min_risk == max_risk:
        max_risk = min_risk + 1.0

    chart_heat = (
        alt.Chart(df_heat)
        .mark_rect()
        .encode(
            x=alt.X(
                "Severity band:N",
                sort=severity_order,
                title="Severity band",
                axis=alt.Axis(labelAngle=0),
            ),
            y=alt.Y("Domain:N", title="Regulatory domain"),
            color=alt.Color(
                "Severity band:N",
                title="Severity band",
                scale=alt.Scale(
                    domain=severity_order,
                    range=severity_gradient,
                ),
                legend=alt.Legend(title="Severity band"),
            ),
            tooltip=[
                alt.Tooltip("Domain:N", title="Domain"),
                alt.Tooltip("Severity band:N", title="Severity"),
                alt.Tooltip("Policies:Q", title="Policies"),
                alt.Tooltip("Risk score:Q", title="Risk score (violations-weighted)"),
            ],
        )
        .properties(
            title="Domain × severity heatmap — L4 policy violations (session)",
            height=260,
        )
    )

    st.altair_chart(chart_heat, use_container_width=True)

    # Clarify this is GNCE constitutional telemetry, not the SARS ledger
    st.caption("GNCE constitutional telemetry; SARS ledger is session-scoped below.")


# =========================================================
# PUBLIC ENTRYPOINT
# =========================================================

def render_domain_catalog(
    adra: Dict[str, Any] | None,
    adra_store: Dict[str, Any] | None = None,
    sars_ledger: List[Dict[str, Any]] | None = None,
) -> None:
    """
    Render the GNCE Constitutional Domain Catalog (Hybrid Taxonomy).
    Shows the full tree and highlights domains that were actually
    triggered for this ADRA (and optionally across the session).
    """
    st.markdown("### 🏛 Constitutional Domain Catalog")

    if not isinstance(adra, dict):
        st.info("No ADRA available yet. Run GNCE to see triggered domains.")
        return 

    # ✅ Always define adra_id BEFORE we build any impacts (prevents UnboundLocalError)
    adra_id = str(
        adra.get("adra_id")
        or adra.get("ADRA ID")
        or adra.get("adraId")
        or ""
    ).strip()
    
    # --------------------------------------------------
    # Get domains triggered in CURRENT ADRA (for highlighting)
    # --------------------------------------------------
    current_triggered_ids = _collect_triggered_domain_ids(adra)
    
    # --------------------------------------------------
    # Aggregate triggered domains across the session
    # --------------------------------------------------
    triggered_ids: Set[str] = set()

    if isinstance(adra_store, dict) and adra_store:
        for _a in adra_store.values():
            if isinstance(_a, dict):
                triggered_ids |= _collect_triggered_domain_ids(_a)
    else:
        triggered_ids = current_triggered_ids

    # Show clear indicators for what's happening in this execution
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Current Run", f"{len(current_triggered_ids)} domains")
    
    with col2:
        total_violations = 0
        if isinstance(adra, dict):
            l1 = adra.get("L1_the_verdict_and_constitutional_outcome", {})
            if l1.get("decision_outcome") == "DENY":
                total_violations = 1
            elif l1.get("severity") in ["HIGH", "CRITICAL"]:
                total_violations = 1
        st.metric("Violations", total_violations)
    
    with col3:
        st.metric("Session Total", f"{len(triggered_ids)} domains")

    # Show which domains were triggered in current run
    if current_triggered_ids:
        domain_labels = []
        for domain_id in current_triggered_ids:
            # Find the label for this domain
            for category in GNCE_DOMAIN_TAXONOMY:
                for child in category.get("children", []):
                    if child.get("id") == domain_id:
                        domain_labels.append(child.get("label", domain_id))
                        break
        
        if domain_labels:
            st.success(f"**Current run triggered:** {', '.join(domain_labels[:3])}")
            if len(domain_labels) > 3:
                st.caption(f"...and {len(domain_labels) - 3} more")
    else:
        st.info("This ADRA did not trigger any domain-specific policies.")

    st.markdown("---")
    
    # --------------------------------------------------
    # Aggregate violation posture across the session
    # --------------------------------------------------
    posture_map: Dict[str, Dict[str, Any]] = {}

    if isinstance(adra_store, dict) and adra_store:
        for _a in adra_store.values():
            if isinstance(_a, dict):
                for dom_id, meta in _collect_domain_violation_posture(_a).items():
                    cur = posture_map.setdefault(
                        dom_id,
                        {
                            "total": 0,
                            "triggered": 0,
                            "violations": 0,
                            "max_severity": "LOW",
                            "impacts": [],
                        },
                    )
                    cur["total"] += int(meta.get("total") or 0)
                    cur["violations"] += int(meta.get("violations") or 0)

                    if _severity_rank(str(meta.get("max_severity") or "LOW")) > _severity_rank(cur["max_severity"]):
                        cur["max_severity"] = str(meta.get("max_severity") or "LOW").upper().strip() or "LOW"

                    # --------------------------------------------------
                    # Merge dynamic per-article impacts
                    # --------------------------------------------------
                    incoming_impacts = meta.get("impacts") or []
                    if isinstance(incoming_impacts, list):
                        cur_keys = {x.get("_k") for x in cur["impacts"]}
                        for it in incoming_impacts:
                            if isinstance(it, dict) and it.get("_k") not in cur_keys:
                                cur["impacts"].append(it)
                                cur_keys.add(it.get("_k"))

                        # deterministic ordering: violations first, highest severity first
                        cur["impacts"].sort(
                            key=lambda x: (
                                0 if str(x.get("status", "")).upper() in {"VIOLATED", "DENY", "BLOCK", "FAIL", "FAILED"} else 1,
                                -_severity_rank(str(x.get("severity") or "LOW")),
                            )
                        )

                        # cap to avoid UI explosion
                        if len(cur["impacts"]) > 200:
                            del cur["impacts"][200:]

    else:
        posture_map = _collect_domain_violation_posture(adra)

    # Display controls
    c1, c2 = st.columns([1, 1])

    with c1:
        collapse_by_severity = st.toggle("🧩 Collapse obligations by severity", value=False)

    with c2:
        min_severity = st.selectbox(
            "Filter: minimum severity",
            ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
            index=0,
        )
        st.session_state["domain_compact_mode"] = st.toggle(
            "🗂 Compact leaf mode (reduce scroll)",
            value=st.session_state.get("domain_compact_mode", True),
        )
        st.session_state["domain_leaf_page_size"] = st.slider(
            "Leaf page size",
            min_value=5,
            max_value=30,
            value=int(st.session_state.get("domain_leaf_page_size", 10)),
            step=5,
        )

    # Legend for indicators
    st.caption("🔥 = Triggered in current run | 🚨 = Violations present | ✅ = Clean | 🧭 = Constitutional coverage")

    # Render the domain catalog with current run highlighting
    for bucket in GNCE_DOMAIN_TAXONOMY:
        _render_node(
            bucket, 
            triggered_ids, 
            current_triggered_ids,
            posture_map, 
            adra_store, 
            sars_ledger, 
            collapse_by_severity, 
            min_severity
        )

    # --------------------------------------------------
    # Optional but powerful: heatmap
    # --------------------------------------------------
    st.markdown("---")
    with st.expander("📊 Domain × Severity Posture (Session-wide)", expanded=False):
        _render_domain_severity_heatmap()