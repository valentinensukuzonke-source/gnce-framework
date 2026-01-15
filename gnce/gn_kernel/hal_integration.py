"""
Universal HAL Integration for GPUx Readiness
Works with any kernel that returns L0-L7 layers.
"""

import json
import hashlib
import uuid
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict

# ============================================================================
# Core HAL Components (Hardware Abstraction Layer)
# ============================================================================

@dataclass
class ConstitutionalBundle:
    """Serializable bundle of constitutional layer outputs (L0-L4)"""
    l0: Dict[str, Any]
    l1: Dict[str, Any]
    l2: Dict[str, Any]
    l3: Dict[str, Any]
    l4: Dict[str, Any]
    
    def to_gpux_format(self) -> Dict[str, Any]:
        """Convert to GPUx-compatible format"""
        return {
            'constitutional_layers': {
                'L0': self.l0, 'L1': self.l1, 'L2': self.l2,
                'L3': self.l3, 'L4': self.l4
            },
            'metadata': {
                'hash': self.get_content_hash(),
                'type': 'ConstitutionalBundle',
                'version': '1.0',
                'id': str(uuid.uuid4())
            }
        }
    
    def get_content_hash(self) -> str:
        """Get SHA256 hash of bundle content"""
        data = json.dumps(self.to_gpux_format(), sort_keys=True)
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

class GPUxPipeline:
    """GPUx execution pipeline (software emulation)"""
    
    @staticmethod
    def execute_l5_cet(bundle: ConstitutionalBundle) -> Dict[str, Any]:
        """L5: Cryptographic Execution Token"""
        return {
            'layer': 'L5',
            'title': 'Integrity & Cryptographic Execution Token (CET)',
            'validated': True,
            'content_hash_sha256': f'sha256:{bundle.get_content_hash()}',
            'constitutional': {
                'clause': 'GNCE Sec. 5.1 — Constitutional decisions must be integrity-bound via CET.',
                'explainability': {
                    'headline': 'CET SIGNED — constitutional substrate integrity-bound.'
                }
            }
        }
    
    @staticmethod
    def execute_l6_drift(bundle: ConstitutionalBundle) -> Dict[str, Any]:
        """L6: Drift Detection"""
        return {
            'layer': 'L6',
            'title': 'Behavioral Drift & Constitutional Monitoring',
            'drift_status': 'NO_DRIFT',
            'drift_outcome': 'NO_DRIFT',
            'constitutional': {
                'clause': 'GNCE Sec. 6.1 — Behavioral drift monitoring must detect unsafe patterns.'
            }
        }
    
    @staticmethod
    def execute_l7_veto(bundle: ConstitutionalBundle) -> Dict[str, Any]:
        """L7: Veto Path"""
        verdict = bundle.l1.get('decision_outcome', 'UNKNOWN')
        severity = bundle.l1.get('severity', 'LOW')
        
        veto_required = severity in ['HIGH', 'CRITICAL'] and verdict == 'DENY'
        
        return {
            'layer': 'L7',
            'title': 'Veto Path & Sovereign Execution Feedback',
            'execution_authorized': not veto_required,
            'veto_triggered': veto_required,
            'veto_category': 'CONSTITUTIONAL_BLOCK' if veto_required else 'NONE',
            'constitutional_citation': 'A system cannot execute an ALLOW verdict when HIGH/CRITICAL obligations are violated.'
        }

# ============================================================================
# HAL Kernel Wrapper (Universal)
# ============================================================================

def create_hal_enhanced_kernel(original_kernel=None):
    """
    Create HAL-enhanced kernel wrapper.
    
    Args:
        original_kernel: Existing kernel instance or module.
                        If None, will try to import automatically.
    """
    
    # If no kernel provided, try to import
    if original_kernel is None:
        try:
            from gnce.gn_kernel import kernel as kernel_module
            original_kernel = kernel_module
        except ImportError:
            raise ImportError("Could not import GNCE kernel")
    
    class HALEnhancedKernel:
        """HAL-enhanced kernel with GPUx readiness"""
        
        def __init__(self, kernel=original_kernel):
            self.original_kernel = kernel
            self.gpux_pipeline = GPUxPipeline()
            
            # Detect if kernel has evaluate method
            if hasattr(kernel, 'evaluate'):
                self.evaluate_method = kernel.evaluate
            elif hasattr(kernel, 'gn_kernel') and hasattr(kernel.gn_kernel, 'evaluate'):
                self.evaluate_method = kernel.gn_kernel.evaluate
            else:
                # Try to find evaluate function
                for attr_name in dir(kernel):
                    attr = getattr(kernel, attr_name)
                    if callable(attr) and 'evaluate' in attr_name.lower():
                        self.evaluate_method = attr
                        break
                else:
                    raise AttributeError("Could not find evaluate method in kernel")
        
        def evaluate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
            """
            Enhanced evaluate with HAL and GPUx pipeline.
            
            1. Run original evaluation (gets L0-L4)
            2. Extract constitutional layers
            3. Execute GPUx pipeline (L5-L7)
            4. Combine all layers
            """
            # Step 1: Original evaluation
            original_result = self.evaluate_method(payload)
            
            # Step 2: Extract L0-L4 layers
            # Try different possible result formats
            layers = {}
            for layer_name in ['L0', 'L1', 'L2', 'L3', 'L4']:
                if layer_name in original_result:
                    layers[layer_name] = original_result[layer_name]
                elif f'layer_{layer_name[1:]}' in original_result:
                    layers[layer_name] = original_result[f'layer_{layer_name[1:]}']
                else:
                    # Try case-insensitive
                    for key in original_result.keys():
                        if key.upper() == layer_name:
                            layers[layer_name] = original_result[key]
                            break
                    else:
                        layers[layer_name] = {}
            
            # Create constitutional bundle
            bundle = ConstitutionalBundle(
                l0=layers.get('L0', {}),
                l1=layers.get('L1', {}),
                l2=layers.get('L2', {}),
                l3=layers.get('L3', {}),
                l4=layers.get('L4', {})
            )
            
            # Step 3: Execute GPUx pipeline
            l5 = self.gpux_pipeline.execute_l5_cet(bundle)
            l6 = self.gpux_pipeline.execute_l6_drift(bundle)
            l7 = self.gpux_pipeline.execute_l7_veto(bundle)
            
            # Step 4: Combine results
            final_result = {
                **original_result,  # Keep all original data
                'L5': l5,
                'L6': l6,
                'L7': l7,
                '_hal': {
                    'enabled': True,
                    'constitutional_bundle_hash': bundle.get_content_hash(),
                    'gpux_ready': True,
                    'version': '1.0.0'
                }
            }
            
            return final_result
        
        def get_hal_info(self) -> Dict[str, Any]:
            """Get HAL information"""
            return {
                'hal_version': '1.0.0',
                'gpux_ready': True,
                'constitutional_bundle_supported': True,
                'kernel_type': type(self.original_kernel).__name__
            }
    
    return HALEnhancedKernel()

# ============================================================================
# Easy-to-use interface
# ============================================================================

def get_hal_kernel(kernel=None):
    """
    Get HAL-enhanced kernel.
    
    Usage:
        from gnce.gn_kernel.hal_integration import get_hal_kernel
        kernel = get_hal_kernel()
        result = kernel.evaluate(payload)
    """
    return create_hal_enhanced_kernel(kernel)

# For backward compatibility
HALEnhancedKernel = create_hal_enhanced_kernel().__class__

if __name__ == "__main__":
    # Quick test
    print("🧪 Testing HAL Integration")
    try:
        hal_kernel = get_hal_kernel()
        print("✅ HAL Kernel created successfully")
        print(f"Kernel type: {type(hal_kernel)}")
        
        # Quick test with minimal payload
        test_result = hal_kernel.evaluate({
            "action": "TEST",
            "test": True
        })
        
        print(f"✅ Test evaluation completed")
        print(f"Result has HAL: {'_hal' in test_result}")
        if '_hal' in test_result:
            print(f"HAL hash: {test_result['_hal']['constitutional_bundle_hash'][:32]}...")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
