// =============================================================
//  Gordian Nexus Constitutional Engine (GNCE) v0.5
//  GN-DSL master constitution
// =============================================================

constitution "GNCE_Universal_Constitution_v0_5" {

  meta {
    version        = "0.5.0"
    jurisdiction   = "EU + Global"
    description    = "Unified deterministic constitution for GNCE v0.5 (agents, platforms, cloud workloads)."
    author         = "Valentine Nsukuzonke + GNCE"
    last_updated   = "2025-12-08"
  }

  // -----------------------------------------------------------
  //  DOMAIN 1 — Safety & Harm Prevention
  // -----------------------------------------------------------
  domain "Safety & Harm Prevention" {
    id          = "SAFETY"
    description = "Online safety, systemic risk, and harm prevention across services and agents."

    // DSA Art. 34 — Systemic risk assessment
    article "DSA Art. 34 — Systemic risk assessment" {
      id          = "DSA_ART_34"
      regime      = "DSA"
      default_severity = "HIGH"
      tags        = ["safety", "systemic-risk", "online-harms"]

      rule "DSA34_HIGH_RISK_BLOCK" {
        label   = "Block harmful systemic risk with prior violations"
        when {
          input.risk_indicators.harmful_content_flag == true
          and input.risk_indicators.previous_violations >= 1
        }
        then {
          status   = "VIOLATED"
          severity = "HIGH"
          impact   = "Systemic risk identified with prior violations; triggers constitutional veto path."
        }
      }

      rule "DSA34_BASELINE_OK" {
        label = "Baseline safe case"
        when {
          input.risk_indicators.harmful_content_flag == false
          and input.risk_indicators.previous_violations == 0
        }
        then {
          status   = "SATISFIED"
          severity = "LOW"
          impact   = "Baseline safe scenario; supports ALLOW decision."
        }
      }

      rule "DSA34_UNKNOWN" {
        label = "Missing safety indicators"
        when {
          missing(input.risk_indicators)
        }
        then {
          status   = "VIOLATED"
          severity = "MEDIUM"
          impact   = "Safety indicators missing; requires human oversight before execution."
        }
      }
    }

    // DSA Art. 35 — Risk mitigation measures
    article "DSA Art. 35 — Mitigation measures" {
      id          = "DSA_ART_35"
      regime      = "DSA"
      default_severity = "MEDIUM"
      tags        = ["safety", "mitigation"]

      rule "DSA35_MITIGATION_REQUIRED" {
        label = "Mitigation required for known risk profile"
        when {
          input.risk_indicators.harm_profile in ["CHILD_SAFETY", "TERRORISM", "EXTREMISM"]
          and not input.controls.mitigation_plan_present
        }
        then {
          status   = "VIOLATED"
          severity = "HIGH"
          impact   = "High-risk harm profile without mitigation plan; execution must be blocked or routed to safety engine."
        }
      }

      rule "DSA35_MITIGATION_PRESENT" {
        label = "Mitigation documented"
        when {
          input.controls.mitigation_plan_present == true
        }
        then {
          status   = "SATISFIED"
          severity = "LOW"
          impact   = "Mitigation plan documented and attached to ADRA."
        }
      }

      rule "DSA35_NOT_APPLICABLE" {
        label = "No safety risk detected"
        when {
          input.risk_indicators.harm_profile == "NONE"
        }
        then {
          status   = "NOT_APPLICABLE"
          severity = "LOW"
          impact   = "No specific harm profile; mitigation controls not applicable."
        }
      }
    }
  }

  // -----------------------------------------------------------
  //  DOMAIN 2 — Content & Speech Governance
  // -----------------------------------------------------------
  domain "Content & Speech Governance" {
    id          = "CONTENT"
    description = "Moderation, notice & action, and speech governance for user-facing systems."

    // DSA Art. 36 — Content moderation & recommender transparency
    article "DSA Art. 36 — Content moderation & transparency" {
      id          = "DSA_ART_36"
      regime      = "DSA"
      default_severity = "HIGH"
      tags        = ["moderation", "transparency"]

      rule "DSA36_UNEXPLAINED_MODERATION" {
        label = "No human-readable rationale for moderation"
        when {
          input.moderation.decision in ["REMOVE", "DOWNRANK", "BAN"]
          and empty(input.moderation.rationale)
        }
        then {
          status   = "VIOLATED"
          severity = "HIGH"
          impact   = "Moderation action taken without a human-readable rationale; fails transparency requirements."
        }
      }

      rule "DSA36_OK_WITH_RATIONALE" {
        label = "Moderation with rationale"
        when {
          input.moderation.decision in ["REMOVE", "DOWNRANK", "BAN"]
          and not empty(input.moderation.rationale)
        }
        then {
          status   = "SATISFIED"
          severity = "MEDIUM"
          impact   = "Moderation action documented with rationale."
        }
      }

      rule "DSA36_NO_ACTION" {
        label = "No moderation action"
        when {
          input.moderation.decision == "NO_ACTION"
        }
        then {
          status   = "NOT_APPLICABLE"
          severity = "LOW"
          impact   = "No content action; moderation transparency not applicable."
        }
      }
    }

    // DSA Art. 40 — Notice & Action (general complaints)
    article "DSA Art. 40 — Notice & Action" {
      id          = "DSA_ART_40"
      regime      = "DSA"
      default_severity = "MEDIUM"
      tags        = ["complaints", "notice-action"]

      rule "DSA40_NOT_PROCESSED" {
        label = "Complaint not processed"
        when {
          input.complaint.notice_received == true
          and input.complaint.reviewed == false
        }
        then {
          status   = "VIOLATED"
          severity = "HIGH"
          impact   = "User complaint not processed; notice & action requirements breached."
        }
      }

      rule "DSA40_PROCESSED_ON_TIME" {
        label = "Complaint processed within SLA"
        when {
          input.complaint.notice_received == true
          and input.complaint.reviewed == true
          and input.complaint.response_time_hours <= 48
        }
        then {
          status   = "SATISFIED"
          severity = "LOW"
          impact   = "Complaint processed within SLA and logged in SARS ledger."
        }
      }

      rule "DSA40_LATE_RESPONSE" {
        label = "Complaint processed but late"
        when {
          input.complaint.notice_received == true
          and input.complaint.reviewed == true
          and input.complaint.response_time_hours > 48
        }
        then {
          status   = "VIOLATED"
          severity = "MEDIUM"
          impact   = "Complaint processed but outside SLA; must be flagged to governance dashboards."
        }
      }
    }
  }

  // -----------------------------------------------------------
  //  DOMAIN 3 — User Rights, Privacy & Data Protection
  // -----------------------------------------------------------
  domain "User Rights, Privacy & Data Protection" {
    id          = "PRIVACY"
    description = "GDPR, privacy, user rights and data minimisation requirements."

    article "GDPR Art. 5 — Data processing principles" {
      id          = "GDPR_ART_5"
      regime      = "GDPR"
      default_severity = "HIGH"
      tags        = ["gdpr", "principles"]

      rule "GDPR5_PERSONAL_DATA_WITHOUT_BASIS" {
        label = "Processing personal data without lawful basis"
        when {
          input.data.personal_data_present == true
          and input.data.lawful_basis in ["NONE", "UNKNOWN", ""]
        }
        then {
          status   = "VIOLATED"
          severity = "CRITICAL"
          impact   = "Personal data processed without lawful basis; absolute constitutional veto."
        }
      }

      rule "GDPR5_MINIMISED_AND_LAWFUL" {
        label = "Personal data minimised with lawful basis"
        when {
          input.data.personal_data_present == true
          and input.data.lawful_basis in ["CONSENT", "CONTRACT", "LEGITIMATE_INTEREST"]
          and input.data.fields_count <= input.data.fields_minimum_allowed
        }
        then {
          status   = "SATISFIED"
          severity = "MEDIUM"
          impact   = "Personal data has a declared lawful basis and is minimised."
        }
      }

      rule "GDPR5_NOT_APPLICABLE" {
        label = "No personal data"
        when {
          input.data.personal_data_present == false
        }
        then {
          status   = "NOT_APPLICABLE"
          severity = "LOW"
          impact   = "No personal data in scope; GDPR principles surface only."
        }
      }
    }

    article "GDPR Art. 17 — Right to erasure" {
      id          = "GDPR_ART_17"
      regime      = "GDPR"
      default_severity = "MEDIUM"
      tags        = ["gdpr", "erasure"]

      rule "GDPR17_ERASURE_REQUEST_IGNORED" {
        label = "Erasure request ignored"
        when {
          input.data_erasure.requested == true
          and input.data_erasure.processed == false
        }
        then {
          status   = "VIOLATED"
          severity = "HIGH"
          impact   = "User erasure request not processed; must be blocked or escalated."
        }
      }

      rule "GDPR17_ERASURE_PROCESSED" {
        label = "Erasure processed"
        when {
          input.data_erasure.requested == true
          and input.data_erasure.processed == true
        }
        then {
          status   = "SATISFIED"
          severity = "LOW"
          impact   = "Erasure request honoured and logged."
        }
      }

      rule "GDPR17_NO_REQUEST" {
        label = "No erasure request"
        when {
          input.data_erasure.requested == false
        }
        then {
          status   = "NOT_APPLICABLE"
          severity = "LOW"
          impact   = "No right-to-erasure request for this ADRA."
        }
      }
    }
  }

  // -----------------------------------------------------------
  //  DOMAIN 4 — Platform Integrity & Abuse
  // -----------------------------------------------------------
  domain "Platform Integrity & Abuse" {
    id          = "INTEGRITY"
    description = "Integrity of the platform, abuse detection, and trusted flagger workflows."

    article "DSA Art. 39 — Trusted flaggers" {
      id          = "DSA_ART_39"
      regime      = "DSA"
      default_severity = "HIGH"
      tags        = ["trusted-flaggers", "abuse"]

      rule "DSA39_TRUSTED_FLAGGER_IGNORED" {
        label = "Trusted flagger signal ignored"
        when {
          input.trusted_flagger.flag_present == true
          and input.trusted_flagger.reviewed == false
        }
        then {
          status   = "VIOLATED"
          severity = "CRITICAL"
          impact   = "Trusted flagger notice ignored; must trigger veto and escalation."
        }
      }

      rule "DSA39_TRUSTED_FLAGGER_PROCESSED" {
        label = "Trusted flagger signal processed"
        when {
          input.trusted_flagger.flag_present == true
          and input.trusted_flagger.reviewed == true
        }
        then {
          status   = "SATISFIED"
          severity = "HIGH"
          impact   = "Trusted flagger signal processed according to policy."
        }
      }

      rule "DSA39_NO_TRUSTED_FLAGGER" {
        label = "No trusted flagger involvement"
        when {
          input.trusted_flagger.flag_present == false
        }
        then {
          status   = "NOT_APPLICABLE"
          severity = "LOW"
          impact   = "No trusted flagger involvement for this ADRA."
        }
      }
    }
  }

  // -----------------------------------------------------------
  //  DOMAIN 5 — Autonomy, AI Agents & Automation
  // -----------------------------------------------------------
  domain "Autonomy, AI Agents & Automation" {
    id          = "AGENTS"
    description = "Constitutional constraints for autonomous agents and automated decision-making."

    article "GNCE Agent Principle — Separation of Reasoning and Action" {
      id          = "GN_AGENT_SEPARATION"
      regime      = "GNCE"
      default_severity = "HIGH"
      tags        = ["agents", "separation-of-powers"]

      rule "GN_AGENT_PLAN_APPLY_MERGED" {
        label = "Agent attempted plan+apply in one opaque step"
        when {
          input.agent.plan_phase_present == false
          and input.agent.apply_phase_present == true
        }
        then {
          status   = "VIOLATED"
          severity = "CRITICAL"
          impact   = "Agent attempted to reason and execute in a single opaque step; violates GNCE separation principle."
        }
      }

      rule "GN_AGENT_PLAN_APPLY_SEPARATE" {
        label = "Agent separated plan and apply"
        when {
          input.agent.plan_phase_present == true
          and input.agent.apply_phase_present == true
        }
        then {
          status   = "SATISFIED"
          severity = "MEDIUM"
          impact   = "Agent workflow honours GNCE separation of reasoning and action."
        }
      }
    }

    article "GNCE L6 — Behavioural drift guardrail" {
      id          = "GN_L6_DRIFT"
      regime      = "GNCE"
      default_severity = "HIGH"
      tags        = ["drift", "monitoring"]

      rule "GN_DRIFT_ALERT_ESCALATION" {
        label = "Drift alert requires escalation"
        when {
          input.drift.drift_outcome == "DRIFT_ALERT"
        }
        then {
          status   = "VIOLATED"
          severity = "HIGH"
          impact   = "Behavioural drift detected; must trigger safety engine or human recalibration."
        }
      }

      rule "GN_NO_DRIFT" {
        label = "No behavioural drift"
        when {
          input.drift.drift_outcome in ["NO_DRIFT", "NONE", ""]
        }
        then {
          status   = "SATISFIED"
          severity = "LOW"
          impact   = "No drift detected for this ADRA."
        }
      }
    }
  }

  // -----------------------------------------------------------
  //  DOMAIN 6 — Economic & Competition Governance
  // -----------------------------------------------------------
  domain "Economic & Competition Governance" {
    id          = "ECON"
    description = "Digital market fairness, anti-gatekeeper constraints, and basic DMA hooks."

    article "DMA Art. 6 — Gatekeeper obligations" {
      id          = "DMA_ART_6"
      regime      = "DMA"
      default_severity = "MEDIUM"
      tags        = ["dma", "gatekeeper"]

      rule "DMA6_SELF_PREFERENCING" {
        label = "Self-preferencing detected"
        when {
          input.econ.gatekeeper == true
          and input.econ.self_preferencing == true
        }
        then {
          status   = "VIOLATED"
          severity = "HIGH"
          impact   = "Gatekeeper self-preferencing behaviour; must be flagged to competition governance."
        }
      }

      rule "DMA6_NEUTRAL_TREATMENT" {
        label = "Neutral treatment of business users"
        when {
          input.econ.gatekeeper == true
          and input.econ.self_preferencing == false
        }
        then {
          status   = "SATISFIED"
          severity = "LOW"
          impact   = "No self-preferencing detected for this ADRA."
        }
      }

      rule "DMA6_NOT_GATEKEEPER" {
        label = "Not a DMA gatekeeper"
        when {
          input.econ.gatekeeper == false
        }
        then {
          status   = "NOT_APPLICABLE"
          severity = "LOW"
          impact   = "DMA gatekeeper obligations not applicable."
        }
      }
    }
  }

  // -----------------------------------------------------------
  //  DOMAIN 7 — Cloud, Infrastructure & Workload Governance
  // -----------------------------------------------------------
  domain "Cloud, Infrastructure & Workload Governance" {
    id          = "CLOUD"
    description = "Placement, resilience, and infrastructure-level constitutional guardrails."

    article "GNCE Cloud Principle — Safe workload placement" {
      id          = "GN_CLOUD_PLACEMENT"
      regime      = "GNCE"
      default_severity = "MEDIUM"
      tags        = ["cloud", "placement"]

      rule "GN_PLACEMENT_OUT_OF_POLICY" {
        label = "Workload placement violates policy"
        when {
          input.cloud.target_zone not_in input.cloud.allowed_zones
        }
        then {
          status   = "VIOLATED"
          severity = "HIGH"
          impact   = "Requested placement outside allowed sovereign locations; veto or remediation required."
        }
      }

      rule "GN_PLACEMENT_IN_POLICY" {
        label = "Workload placement within policy"
        when {
          input.cloud.target_zone in input.cloud.allowed_zones
        }
        then {
          status   = "SATISFIED"
          severity = "LOW"
          impact   = "Workload placement complies with allowed zones."
        }
      }
    }
  }

  // -----------------------------------------------------------
  //  DOMAIN 8 — Governance Process & Auditability
  // -----------------------------------------------------------
  domain "Governance Process & Auditability" {
    id          = "GOVERNANCE"
    description = "Meta-governance, veto principles, audit trails, and GNCE constitutional hooks."

    article "GNCE Sec. 1.1 — No HIGH/CRITICAL violation may yield ALLOW" {
      id          = "GN_SEC_1_1"
      regime      = "GNCE"
      default_severity = "CRITICAL"
      tags        = ["veto", "meta-constitution"]

      rule "GN_META_VETO" {
        label = "Meta veto when HIGH/CRITICAL violation present"
        when {
          any(policies.status == "VIOLATED"
              and policies.severity in ["HIGH", "CRITICAL"])
        }
        then {
          status   = "VIOLATED"
          severity = "CRITICAL"
          impact   = "Meta-constitutional veto must be triggered; execution_authorized = false."
        }
      }
    }

    article "GNCE Sec. 2.3 — Drift alerts may trigger safety veto even when L1 is ALLOW" {
      id          = "GN_SEC_2_3"
      regime      = "GNCE"
      default_severity = "HIGH"
      tags        = ["drift", "safety"]

      rule "GN_DRIFT_META_VETO" {
        label = "Meta veto on unresolved drift"
        when {
          input.drift.drift_outcome == "DRIFT_ALERT"
          and input.drift.resolution_state in ["UNRESOLVED", "UNKNOWN"]
        }
        then {
          status   = "VIOLATED"
          severity = "HIGH"
          impact   = "Unresolved drift alert; safety veto path should be activated."
        }
      }

      rule "GN_DRIFT_RESOLVED" {
        label = "Drift resolved or not present"
        when {
          input.drift.drift_outcome in ["NO_DRIFT", "NONE", ""]
          or input.drift.resolution_state == "RESOLVED"
        }
        then {
          status   = "SATISFIED"
          severity = "LOW"
          impact   = "No unresolved drift; meta-drift guardrail satisfied."
        }
      }
    }
  }
}
