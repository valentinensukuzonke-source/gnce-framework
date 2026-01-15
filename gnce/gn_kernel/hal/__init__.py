"""
Hardware Abstraction Layer (HAL) for GPUx compatibility.
Provides interfaces between constitutional logic and hardware enforcement.
"""

from .gpux_interface import (
    GPUxInstructionSet,
    ConstitutionalBundle,
    GPUxEngine
)

__all__ = [
    'GPUxInstructionSet',
    'ConstitutionalBundle', 
    'GPUxEngine'
]
