# gnce/ui/components/regime_kpi_explorer.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import streamlit as st


def _read_events_jsonl(path: Path, max_rows: int = 5000) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= max_rows:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict):
                        rows.append(obj)
                except Exception:
                    continue
    except Exception:
        return []
    return rows


def render_regime_kpi_explorer(*, run_events_path: Path) -> None:
    st.caption("Per-regime KPI slicing from GNCE run event stream (JSONL).")

    with st.expander("Source (run_events.jsonl)", expanded=False):
        st.code(str(run_events_path), language="text")

    max_rows = st.slider("Max events to read", 200, 20000, 5000, step=200)

    events = _read_events_jsonl(run_events_path, max_rows=max_rows)
    if not events:
        st.info("No run events found yet. Run GNCE at least once (and ensure append_jsonl is writing).")
        return

    df = pd.DataFrame(events)

    # normalize key fields
    if "regime" not in df.columns:
        df["regime"] = "UNKNOWN"
    df["regime"] = df["regime"].fillna("UNKNOWN").astype(str)

    if "decision" not in df.columns:
        df["decision"] = "UNKNOWN"
    df["decision"] = df["decision"].fillna("UNKNOWN").astype(str).str.upper()

    if "violations_count" not in df.columns:
        df["violations_count"] = 0
    df["violations_count"] = pd.to_numeric(df["violations_count"], errors="coerce").fillna(0).astype(int)

    df["is_allow"] = df["decision"].isin(["ALLOW", "APPROVE", "PERMIT"])
    df["is_deny"] = df["decision"].isin(["DENY", "REJECT", "BLOCK"])

    # aggregate KPIs
    agg = (
        df.groupby("regime", dropna=False)
          .agg(
              total_runs=("decision", "count"),
              allow_count=("is_allow", "sum"),
              deny_count=("is_deny", "sum"),
              violations_total=("violations_count", "sum"),
              violations_avg=("violations_count", "mean"),
          )
          .reset_index()
    )

    agg["allow_rate"] = (agg["allow_count"] / agg["total_runs"]).fillna(0.0)
    agg["deny_rate"] = (agg["deny_count"] / agg["total_runs"]).fillna(0.0)

    agg = agg.sort_values(["total_runs", "deny_rate"], ascending=[False, False])

    st.subheader("Regime KPI Table")
    st.dataframe(
        agg,
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Visuals")
    c1, c2 = st.columns(2)
    with c1:
        st.write("Runs by regime")
        st.bar_chart(agg.set_index("regime")["total_runs"])
    with c2:
        st.write("DENY rate by regime")
        st.bar_chart(agg.set_index("regime")["deny_rate"])

    st.markdown("---")
    st.subheader("Drilldown")
    selected = st.selectbox("Select a regime", options=agg["regime"].tolist())
    sub = df[df["regime"] == selected].copy()

    cols = [c for c in ["ts_utc", "adra_id", "decision", "severity", "violations_count", "execution_authorized", "payload_name"] if c in sub.columns]
    st.dataframe(sub[cols].sort_values(cols[0], ascending=False) if cols else sub, use_container_width=True, hide_index=True)
