# gnce/gn_kernel/regimes/glba/register.py
from gnce.gn_kernel.regimes.register import register_regime
from gnce.gn_kernel.regimes.glba.applicability import is_applicable
from gnce.gn_kernel.rules.glba_rules import evaluate_glba_rules


def register() -> None:
    register_regime(
        regime_id="GLBA",
        display_name="Gramm-Leach-Bliley Act (GLBA)",
        domain="Financial Privacy",
        framework="US Federal Law",
        regime_type="REGULATION",
        jurisdiction="US",
        authority="FTC / Federal Banking Agencies",
        enforceable=True,
        l4_executable=True,
        applicability=is_applicable,
        resolver=lambda payload: {
            "policies_triggered": evaluate_glba_rules(payload)[0]
        },
    )
