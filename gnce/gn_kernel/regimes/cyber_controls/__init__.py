"""GNCE Cyber Controls Regime.

Executable GNCE regime that evaluates cyber-control constraints at execution time
(access control, data handling, key handling, deployment/config changes, incident actions).

Copy to: gnce/gn_kernel/regimes/cyber_controls/
Then register in your central registry.
"""

from .register import REGIME_ID, get_regime_spec
from .resolver import resolve
from .applicability import is_applicable
