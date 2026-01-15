# ui/components/domain_explorer.py

from typing import Dict, Any, List

import streamlit as st
import pandas as pd
import altair as alt

# -------------------------------------------------------------------
#  Shared severity ordering & colours (aligned with v0.4 UI)
# -------------------------------------------------------------------

SEVERITY_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
SEVERITY_COLORS = {
    "LOW": "#00916E",        # green
    "MEDIUM": "#ffb300",     # amber
    "HIGH": "#C62828",       # red
    "CRITICAL": "#8b008b",   # purple
}

# Canonical GNCE regime set (used by Regime Outcome Vector too)
CANONICAL_DOMAINS = [
    {"DomainId": "DSA", "Domain": "EU Digital Services Act (DSA)"},
    {"DomainId": "DMA", "Domain": "EU Digital Markets Act (DMA)"},
    {"DomainId": "EU_AI_ACT_ISO_42001", "Domain": "EU AI Act / ISO 42001"},
    {"DomainId": "GDPR", "Domain": "EU GDPR"},
    {"DomainId": "NIST_AI_RMF", "Domain": "NIST AI RMF"},
]


def _severity_to_score(sev: str) -> int:
    """Numeric score for risk-weighting."""
    mapping = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
    return mapping.get(str(sev).upper(), 0)


def _normalise_severity(raw: Any) -> str:
    """Normalise severity into LOW/MEDIUM/HIGH/CRITICAL/UNKNOWN."""
    num_map = {1: "LOW", 2: "MEDIUM", 3: "HIGH", 4: "CRITICAL"}

    # numeric → map to band
    if isinstance(raw, (int, float)):
        return num_map.get(int(raw), "UNKNOWN")

    # string → clean & map
    if isinstance(raw, str):
        s = raw.strip().upper()
        if not s:
            return "UNKNOWN"
        if s.isdigit():
            return num_map.get(int(s), "UNKNOWN")
        if s in SEVERITY_ORDER:
            return s
        return s  # already some label (fallback)

    return "UNKNOWN"


def _build_l4_df(adra: Dict[str, Any]) -> pd.DataFrame:
    """
    Build a per-policy dataframe for this ADRA.

    Columns:
      - Domain        (human-friendly label, e.g. 'EU Digital Markets Act (DMA)')
      - DomainId      (short code, if present: DSA, DMA, GDPR, ...)
      - Article
      - Severity
      - Status        (SATISFIED / VIOLATED / NOT_APPLICABLE / ...)
    """
    if not isinstance(adra, dict):
        return pd.DataFrame(
            columns=["Domain", "DomainId", "Article", "Severity", "Status"]
        )

    l4 = adra.get("L4_policy_lineage_and_constitution", {}) or {}
    policies = l4.get("policies_triggered", []) or []

    rows: List[Dict[str, Any]] = []
    for p in policies:
        if not isinstance(p, dict):
            continue

        status = str(p.get("status", "")).upper() or "UNKNOWN"

        domain_label = (
            p.get("domain")
            or p.get("regulatory_domain")
            or p.get("regime")
            or "Unknown"
        )
        domain_id = p.get("domain_id") or p.get("regime") or domain_label

        article = p.get("article", "N/A")

        sev_raw = (
            p.get("severity")
            or p.get("severity_level")
            or p.get("severity_score")
            or p.get("criticality")
        )
        sev = _normalise_severity(sev_raw)

        rows.append(
            {
                "Domain": domain_label,
                "DomainId": str(domain_id),
                "Article": article,
                "Severity": sev,
                "Status": status,
            }
        )

    if not rows:
        return pd.DataFrame(
            columns=["Domain", "DomainId", "Article", "Severity", "Status"]
        )

    df = pd.DataFrame(rows)
    df["Severity"] = pd.Categorical(df["Severity"], SEVERITY_ORDER, ordered=True)
    return df


# -------------------------------------------------------------------
#  PUBLIC ENTRYPOINT
# -------------------------------------------------------------------

def render_domain_explorer(adra: Dict[str, Any]) -> None:
    """
    📚 L4 domain compliance explorer (this ADRA)

    For the selected regulatory domain, show:
      1) Compliance profile by severity band (articles per severity)
      2) Risk-weighted violation score (severity-weighted)

    v0.4 behaviour:
      - Dropdown always shows the full GNCE regime set:
        DSA, DMA, EU AI Act / ISO 42001, GDPR, NIST AI RMF.
      - If a domain has no L4 policies, we treat it as a pure stub and explain
        that there is no article-level trace for this ADRA.
      - If a domain has only SATISFIED / NOT_APPLICABLE policies, we show that
        it currently has no violations and inherits the GNCE verdict.
    """
    st.markdown("---")
    st.subheader("📚 L4 domain compliance explorer (this ADRA)")
    st.caption(
        "How this ADRA touches L4 policy articles, by regulatory domain and severity band. "
        "This view is ADRA-scoped, not session telemetry."
    )

    df_all = _build_l4_df(adra)

    if df_all.empty:
        # Even if there are no L4 rows at all, we still show the dropdown so the
        # user understands the regime set, but we immediately explain there is
        # no article-level trace for this ADRA.
        st.warning(
            "This ADRA currently has no L4 policy trace. "
            "Regimes are shown for context only."
        )

    # ------------------------------------------------------------------
    # Domain selector: canonical list merged with whatever L4 actually has
    # ------------------------------------------------------------------
    existing = (
        df_all[["DomainId", "Domain"]].drop_duplicates()
        if not df_all.empty
        else pd.DataFrame(columns=["DomainId", "Domain"])
    )

    existing_ids = set(str(x) for x in existing["DomainId"].tolist())

    rows: List[Dict[str, str]] = existing.to_dict(orient="records")

    # Add any canonical domains that are missing
    for c in CANONICAL_DOMAINS:
        cid = c["DomainId"]
        if cid not in existing_ids:
            rows.append({"DomainId": cid, "Domain": c["Domain"]})

    domains_df = pd.DataFrame(rows).drop_duplicates()
    domains_df = domains_df.sort_values(by=["DomainId", "Domain"])

    # Display label: "DSA — EU Digital Services Act (DSA)" style
    def _label(row: pd.Series) -> str:
        did = row.get("DomainId", "")
        lab = row.get("Domain", "")
        if did and lab and did not in lab:
            return f"{did} — {lab}"
        return lab or did or "Unknown"

    options = [_label(r) for _, r in domains_df.iterrows()]
    option_map = {opt: domains_df.iloc[i]["DomainId"] for i, opt in enumerate(options)}

    if not options:
        st.info("No regimes available to display.")
        return

    default_opt = options[0]

    selected_label = st.selectbox(
        "Regulatory domain",
        options=options,
        index=options.index(default_opt),
        key="l4_domain_explorer_domain",
    )
    selected_domain_id = option_map.get(selected_label)

    # ------------------------------------------------------------------
    # Filter L4 rows for this domain
    # ------------------------------------------------------------------
    if df_all.empty:
        st.info(
            f"No L4 policy trace available for **{selected_label}** in this ADRA. "
            "This regime is currently a UI-only stub for this run."
        )
        return

    df_dom_all = df_all[df_all["DomainId"] == selected_domain_id].copy()

    # ----------------------------------------------------
    # Domain "vava voom" header: quick signals
    # ----------------------------------------------------
    total_policies = int(len(df_dom_all))
    total_viol = int((df_dom_all["Status"] == "VIOLATED").sum())
    total_sat = int((df_dom_all["Status"] == "SATISFIED").sum())
    total_na = int((df_dom_all["Status"] == "NOT_APPLICABLE").sum())

    # Severity-weighted risk (violations only)
    tmp = df_dom_all.copy()
    tmp["Score"] = tmp["Severity"].apply(_severity_to_score).astype(float)
    risk_weighted = float(tmp.loc[tmp["Status"] == "VIOLATED", "Score"].sum())

    if total_policies == 0:
        badge = "⚪ No L4 trace"
    elif total_viol == 0:
        badge = "✅ Clean (inherits GNCE verdict)"
    else:
        # escalate emoji by worst violated severity
        worst = (
            df_dom_all.loc[df_dom_all["Status"] == "VIOLATED", "Severity"]
            .dropna()
            .astype(str)
            .tolist()
        )
        worst = worst[0] if worst else "UNKNOWN"
        badge = "🚨 Violations present"

    st.markdown(f"### {selected_label}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📜 Articles (L4)", f"{total_policies}")
    c2.metric("✅ Satisfied", f"{total_sat}")
    c3.metric("❌ Violated", f"{total_viol}")
    c4.metric("⚖️ Risk-weighted", f"{risk_weighted:.0f}")
    st.caption(f"Status: **{badge}**")


    if df_dom_all.empty:
        # ----------------------------------------------------
        # Constitutional Coverage Card (market-ready empty state)
        # ----------------------------------------------------
        with st.container(border=True):
            st.markdown("### 🧭 Constitutional Coverage Active")
            st.markdown(
                f"**{selected_label}** is recognized and governed by GNCE constitutional logic for this decision."
            )

            st.markdown(
                "No article-level (L4) policies were triggered for this ADRA, so the domain **inherits the GNCE verdict** "
                "without article-specific violations or satisfactions."
            )

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("🏛️ Regime", "Catalogued")
            c2.metric("📜 Articles", "Not evaluated")
            c3.metric("⚖️ Outcome", "Inherited")
            c4.metric("🔐 Audit", "Reproducible")

            with st.expander("Why this can happen (expected)"):
                st.markdown(
                    "- The decision did not fall within this regime’s article scope for this run.\n"
                    "- The regime may apply structurally (constitutional), not transactionally (article-triggered).\n"
                    "- No compliance obligation was activated at L4 for this ADRA."
                )

        return


    # For charts, we only look at violations
    df_dom_viol = df_dom_all[df_dom_all["Status"] == "VIOLATED"].copy()

    if df_dom_viol.empty:
        st.success(
            f"✅ **{selected_label}** has **no L4 violations** in this ADRA. "
            "All applicable articles are SATISFIED / NOT_APPLICABLE — this domain inherits the GNCE verdict."
        )

        with st.expander("📄 Show satisfied / N/A L4 articles"):
            df_show = df_dom_all.copy()
            df_show["Severity"] = df_show["Severity"].astype(str)
            st.dataframe(
                df_show[["Article", "Severity", "Status"]].sort_values(["Status", "Severity"]),
                use_container_width=True,
                hide_index=True,
            )
        return

    # ----------------------------------------------------
    # 1) Compliance profile – articles per severity band
    # ----------------------------------------------------
    st.markdown("#### Compliance profile by severity band (this domain)")

    # Distinct articles per severity
    df_articles = (
        df_dom_viol.groupby("Severity", as_index=False)["Article"]
        .nunique()
        .rename(columns={"Article": "Articles"})
    )
    df_articles["Severity"] = pd.Categorical(
        df_articles["Severity"], SEVERITY_ORDER, ordered=True
    )

    chart_articles = (
        alt.Chart(df_articles)
        .mark_bar()
        .encode(
            y=alt.Y("Severity:N", sort=SEVERITY_ORDER, title=None),
            x=alt.X("Articles:Q", title="Articles"),
            color=alt.Color(
                "Severity:N",
                scale=alt.Scale(
                    domain=SEVERITY_ORDER,
                    range=[
                        SEVERITY_COLORS["LOW"],
                        SEVERITY_COLORS["MEDIUM"],
                        SEVERITY_COLORS["HIGH"],
                        SEVERITY_COLORS["CRITICAL"],
                    ],
                ),
                legend=alt.Legend(title="Severity band", orient="right"),
            ),
        )
        .properties(height=180)
    )

    st.altair_chart(chart_articles, use_container_width=True)

    # ----------------------------------------------------
    # 2) Risk-weighted violation score (severity-weighted)
    # ----------------------------------------------------
    st.markdown("#### Risk-weighted violation score (severity-weighted)")

    df_dom_viol["Score"] = df_dom_viol["Severity"].apply(_severity_to_score).astype(
        float
    )

    df_risk = (
        df_dom_viol.groupby("Severity", as_index=False)
        .agg(RiskWeighted=("Score", "sum"))
    )
    df_risk["Severity"] = pd.Categorical(
        df_risk["Severity"], SEVERITY_ORDER, ordered=True
    )

    chart_risk = (
        alt.Chart(df_risk)
        .mark_bar()
        .encode(
            y=alt.Y("Severity:N", sort=SEVERITY_ORDER, axis=None),
            x=alt.X("RiskWeighted:Q", title="Risk-weighted violations"),
            color=alt.Color(
                "Severity:N",
                scale=alt.Scale(
                    domain=SEVERITY_ORDER,
                    range=[
                        SEVERITY_COLORS["LOW"],
                        SEVERITY_COLORS["MEDIUM"],
                        SEVERITY_COLORS["HIGH"],
                        SEVERITY_COLORS["CRITICAL"],
                    ],
                ),
                legend=alt.Legend(title="Severity band", orient="right"),
            ),
        )
        .properties(height=160)
    )

    st.altair_chart(chart_risk, use_container_width=True)

    # ----------------------------------------------------
    # 3) Drill-down: top violated articles (the "vava voom")
    # ----------------------------------------------------
    st.markdown("#### 🔎 Violated articles (drill-down)")

    show_only_critical = st.toggle("🔴 Show only CRITICAL", value=False, key="l4_show_only_critical")
    show_only_high_plus = st.toggle("🟠 Show HIGH+", value=False, key="l4_show_only_highplus")

    df_table = df_dom_viol.copy()
    df_table["Severity"] = df_table["Severity"].astype(str)

    if show_only_critical:
        df_table = df_table[df_table["Severity"] == "CRITICAL"]
    elif show_only_high_plus:
        df_table = df_table[df_table["Severity"].isin(["HIGH", "CRITICAL"])]

    # Emoji severity label
    sev_emoji = {"LOW": "🟢 LOW", "MEDIUM": "🟡 MEDIUM", "HIGH": "🟠 HIGH", "CRITICAL": "🔴 CRITICAL"}
    df_table["Severity"] = df_table["Severity"].apply(lambda s: sev_emoji.get(str(s), f"⚪ {s}"))

    df_table = df_table.sort_values(by=["Severity", "Article"], ascending=[False, True])

    st.dataframe(
        df_table[["Article", "Severity", "Status"]],
        use_container_width=True,
        hide_index=True,
    )

    st.caption("Tip: wire article deep-links later (ADRA section anchors) — this table becomes your compliance cockpit.")

