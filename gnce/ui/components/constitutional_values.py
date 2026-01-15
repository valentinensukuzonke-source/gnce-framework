from __future__ import annotations

"""
ui/components/constitutional_values.py

Static, always-on Constitutional Values panel for GNCE.

Design goals:
- Must never disappear on refresh
- Must be fast (no per-ADRA dependency)
- Must be safe (no f-string brace issues inside CSS)
- Optional: subtle "activation glow" when last decision was DENY/VETO
"""

from typing import Any, Dict
import hashlib

import streamlit as st


# -----------------------------
# Public API
# -----------------------------
def render_constitutional_values_panel(
    *,
    contract_version: str = "1.1",
    constitution_version: str = "v0.7.0-RC",
    last_decision: str | None = None,
) -> None:
    """
    Render the GNCE constitutional values panel.

    Parameters
    ----------
    contract_version:
        The public contract version your UI/kernel guarantees.
    constitution_version:
        A human version label for the constitution surface.
    last_decision:
        If provided and equals DENY/VETO, panel shows a subtle activation glow.
    """

    # Decide if the constitution should "activate" visually
    d = str(last_decision or "").upper().strip()
    activated = d in {"DENY", "VETO"}

    # Stable constitutional hash derived from the panel's canonical text
    canonical = _canonical_constitution_text().encode("utf-8")
    const_hash = hashlib.sha256(canonical).hexdigest()[:12]

    # Inject CSS once
    _inject_css()

    # Add activation class conditionally
    cls = "gnce-constitution gnce-constitution--active" if activated else "gnce-constitution"

    # IMPORTANT:
    # - We do NOT use an f-string for the big HTML/CSS blocks that contain braces.
    # - We only format the small tokens using str.format(), where braces are controlled.
    html = """
<div class="{cls}">
  <div class="gnce-constitution__head">
    <h2>📜 Constitutional Values of the GNCE</h2>
    <div class="cap">These values constrain all GNCE decisions and cannot be bypassed.</div>
  </div>

  <div class="gnce-grid">
    <div class="gnce-card"><b>🏛 Sovereign Supremacy</b><span>External law always overrides internal code.</span></div>
    <div class="gnce-card"><b>⚖ Deterministic Neutrality</b><span>Same input, same result — no bias, no mood.</span></div>
    <div class="gnce-card"><b>📜 Auditability</b><span>Every verdict leaves a trail (ADRA + CET).</span></div>
    <div class="gnce-card"><b>🛟 Safe Failure</b><span>Risk defaults to containment, not collapse.</span></div>
    <div class="gnce-card"><b>👤 Human Authority</b><span>Humans govern the constitution, not machines.</span></div>
    <div class="gnce-card"><b>🧭 Minimal Intrusion</b><span>Enforce only when needed — explain when done.</span></div>
  </div>

  <div class="gnce-sep"></div>

  <div class="gnce-meta">
    <div><b>Execution Scope</b><br/>Values constrain:<br/>• DRE logic<br/>• policy space<br/>• veto boundaries</div>
    <div><b>Governance Scope</b><br/>Values governed by:<br/>• regulators<br/>• policy authorities<br/>• statutory mandates</div>
    <div><b>Legal Character</b><br/>slow · sovereign · binding · auditable</div>
  </div>

  <div class="gnce-notice">
    <b>Constitutional Constraint Notice</b><br/>
    This panel defines what GNCE is <b>bound by</b>.<br/>
    It does not change this decision — it constrains all decisions.
  </div>

  <div class="gnce-hash">Contract {contract} · {version} · CONST_HASH <code>{h}</code></div>
</div>
""".format(
        cls=cls,
        contract=contract_version,
        version=constitution_version,
        h=const_hash,
    )

    st.markdown(html, unsafe_allow_html=True)


# -----------------------------
# Internals
# -----------------------------
def _canonical_constitution_text() -> str:
    # Keep this stable unless you intentionally change the constitution surface.
    return "\n".join(
        [
            "GNCE Constitutional Values",
            "Sovereign Supremacy",
            "Deterministic Neutrality",
            "Auditability",
            "Safe Failure",
            "Human Authority",
            "Minimal Intrusion",
            "Execution Scope: DRE logic, policy space, veto boundaries",
            "Governance Scope: regulators, policy authorities, statutory mandates",
            "Legal Character: slow, sovereign, binding, auditable",
        ]
    )


def _inject_css() -> None:
    # Use a raw triple-quoted string to avoid f-string brace problems.
    st.markdown(
        r"""
<style>
/* Panel container */
.gnce-constitution{
  margin-top: 10px;
  border-radius: 16px;
  padding: 14px 14px 12px 14px;
  border: 1px solid rgba(148,163,184,0.40);
  background: rgba(15,23,42,0.86);
  box-shadow: 0 10px 30px rgba(0,0,0,0.22);
  position: relative;
}

/* Activation glow when DENY/VETO */
.gnce-constitution--active{
  animation: gnceGlow 1.6s ease-in-out infinite;
  border-color: rgba(248,113,113,0.65);
}

@keyframes gnceGlow {
  0%   { box-shadow: 0 10px 30px rgba(0,0,0,0.22); }
  50%  { box-shadow: 0 12px 36px rgba(248,113,113,0.18); }
  100% { box-shadow: 0 10px 30px rgba(0,0,0,0.22); }
}

.gnce-constitution__head h2{
  margin: 0;
  font-size: 1.15rem;
}

.gnce-constitution .cap{
  margin-top: 2px;
  font-size: 0.82rem;
  opacity: 0.85;
}

/* Grid cards */
.gnce-grid{
  margin-top: 10px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.gnce-card{
  padding: 12px;
  border-radius: 12px;
  background: rgba(2,6,23,0.45);
  border: 1px solid rgba(148,163,184,0.25);
}

.gnce-card b{
  display: block;
  font-size: 0.92rem;
  margin-bottom: 3px;
}

.gnce-card span{
  display: block;
  font-size: 0.78rem;
  opacity: 0.82;
  line-height: 1.2rem;
}

/* Separator */
.gnce-sep{
  margin-top: 12px;
  opacity: 0.25;
  border-top: 1px solid rgba(148,163,184,0.35);
}

/* Meta row */
.gnce-meta{
  margin-top: 10px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  font-size: 0.78rem;
  opacity: 0.85;
}

.gnce-notice{
  margin-top: 10px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(30,64,175,0.22);
  border: 1px solid rgba(129,140,248,0.45);
  font-size: 0.80rem;
}

.gnce-hash{
  position: absolute;
  right: 12px;
  bottom: 10px;
  font-size: 0.72rem;
  opacity: 0.75;
}

.gnce-hash code{
  font-size: 0.72rem;
}

/* Responsive */
@media (max-width: 1100px){
  .gnce-grid{ grid-template-columns: 1fr; }
  .gnce-meta{ grid-template-columns: 1fr; }
  .gnce-hash{ position: static; margin-top: 8px; }
}
</style>
""",
        unsafe_allow_html=True,
    )
