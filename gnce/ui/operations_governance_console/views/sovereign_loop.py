# gnce/ui/operations_governance_console/views/sovereign_loop.py
from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st
import pandas as pd

from ..utils.viz import entries_to_df
from ..models.integrity import sovereign_integrity


def render_sovereign_loop(
    entries: List[Dict[str, Any]],
    session_fingerprint: str,
    constitution_hash: str | None,
    depth: str = "Standard",
) -> None:
    """
    depth: "Summary" | "Standard" | "Deep"
    - Summary: core assurance metrics only
    - Standard: + notes + verdict counts + completeness KPIs (default)
    - Deep: + raw evidence excerpt + expanded evidence statement
    """
    st.markdown("## 🏛 Loop 2 — Constitutional Integrity & Determinism Assurance (CIDA)")
    st.caption("Assesses integrity, determinism confidence, traceability, and constitution anchoring. Read-only.")

    # Normalize depth defensively
    depth = (depth or "Standard").strip().title()
    if depth not in ("Summary", "Standard", "Deep"):
        depth = "Standard"

    s = sovereign_integrity(entries, session_fingerprint=session_fingerprint, constitution_hash=constitution_hash)

    cols = st.columns(3)
    cols[0].metric("Integrity", s["integrity"])
    cols[1].metric("Determinism Confidence", f"{s['determinism_confidence']}%")
    cols[2].metric("Session Fingerprint", s["session_fingerprint"][:12] + "…")

    st.markdown("**Constitution hash (dominant in loaded scope):**")
    st.code(s["constitution_hash"] or "None (missing in entries)", language="text")

    # Summary ends here
    if depth == "Summary":
        st.divider()
        return

    st.markdown("**Verdict counts:**")
    st.json(s.get("verdict_counts", {}))

    st.markdown("**Notes / Findings:**")
    for note in s["notes"]:
        st.write(f"- {note}")

    # -----------------------------
    # Regulator-grade traceability KPIs
    # (Standard + Deep)
    # -----------------------------
    df = entries_to_df(entries)

    if df is None or df.empty:
        total = 0
        has_ts = 0
        has_const = 0
    else:
        total = len(df)
        has_ts = int(df["time"].notna().sum()) if "time" in df.columns else 0
        # consider missing/placeholder values as not present
        if "constitution_hash" in df.columns:
            has_const = int(df["constitution_hash"].notna().sum())
            # If your df uses "—" as placeholder, subtract those
            has_const = int((df["constitution_hash"] != "—").sum())
        else:
            has_const = 0

    c2 = st.columns(3)
    c2[0].metric("Timestamp Coverage", f"{(has_ts/total*100):.1f}%" if total else "—")
    c2[1].metric("Constitution Hash Coverage", f"{(has_const/total*100):.1f}%" if total else "—")

    if not total:
        completeness = "—"
    else:
        completeness = "HIGH" if (has_ts / total > 0.8 and has_const / total > 0.6) else "MEDIUM"
    c2[2].metric("Evidence Completeness", completeness)

    # Deep mode: show an evidence excerpt + expand statement by default
    deep_expand = True if depth == "Deep" else False

    with st.expander("📌 Sovereign Evidence Statement (copy/paste)", expanded=deep_expand):
        if total:
            st.write(
                f"- Session fingerprint: `{session_fingerprint}`\n"
                f"- Dominant constitution hash: `{constitution_hash or 'None'}`\n"
                f"- Entries observed: `{total}`\n"
                f"- Timestamp coverage: `{(has_ts/total*100):.1f}%`\n"
                f"- Constitution hash coverage: `{(has_const/total*100):.1f}%`"
            )
        else:
            st.write("No entries loaded — evidence statement unavailable.")

    if depth == "Deep":
        with st.expander("🔎 Deep evidence (raw last entry)", expanded=False):
            st.json(entries[-1] if entries else {})

    st.divider()
