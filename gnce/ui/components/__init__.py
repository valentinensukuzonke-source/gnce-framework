# ui/components/__init__.py

"""
Central export hub for GNCE UI components.

Only import symbols that are actually implemented in the component modules.
"""

from .header import render_header

from .severity_legend import (
    inject_severity_css,
    render_severity_legend,
    severity_tag,
)

from .decision_summary import render_decision_summary

from .regime_outcome_vector import render_regime_outcome_vector

from .domain_catalog import render_domain_catalog

#from .l_layers import render_layers_stack as render_constitutional_layers

from .input_editor import input_editor

from .l4_regimes import render_l4_regimes

from .l_layers import render_layers_stack, render_constitutional_layers
