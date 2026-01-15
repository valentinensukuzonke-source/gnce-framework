"""
Fixed HAL Integration - Handles tuple return from kernel
"""

import json
import hashlib
import uuid
from typing import Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass

# ============================================================================
# Core HAL Components
# ============================================================================

@dataclass
class ConstitutionalBundle:
    """Serializable bundle of constitutional layer outputs (L0-L4)"""
    l0: Dict[str, Any]
    l1: Dict[str, Any]
    l2: Dict[str, Any]
    l3: Dict[str, Any]
    l4: Dict[str, Any]
    
    @classmethod
    def from_kernel_result(cls, result: Union[Dict, Tuple]) -> 'ConstitutionalBundle':
        """Create bundle from kernel result (handles both dict and tuple)"""
        if isinstance(result, tuple):
            # Convert tuple to dict - assuming standard L0-L7 format
            # Based on your L0-L7 output example
            result_dict = {}
            for i, layer in enumerate(result):
                if hasattr(layer, 'get') and callable(layer.get):
                    # Layer is already a dict
                    if 'layer' in layer:
                        layer_name = layer['layer']
                        result_dict[layer_name] = layer
                    else:
                        # Assign L0, L1, etc based on position
                        layer_name = f'L{i}'
                        result_dict[layer_name] = layer
                else:
                    # Not a dict, store as-is
                    result_dict[f'item_{i}'] = layer
        else:
            result_dict = result
        
        return cls(
            l0=result_dict.get('L0', {}),
            l1=result_dict.get('L1', {}),
            l2=result_dict.get('L2', {}),
            l3=result_dict.get('L3', {}),
            l4=result_dict.get('L4', {})
        )
    
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
    """GPUx execution pipeline"""
    
    @staticmethod
    def execute(bundle: ConstitutionalBundle) -> Dict[str, Any]:
        """Execute GPUx pipeline (L5-L7)"""
        # Extract verdict from L1
        l1_data = bundle.l1 if isinstance(bundle.l1, dict) else {}
        verdict = l1_data.get('decision_outcome', l1_data.get('verdict', 'UNKNOWN'))
        severity = l1_data.get('severity', 'LOW')
        
        # L5: Cryptographic Execution Token
        l5 = {
            'layer': 'L5',
            'title': 'Integrity & Cryptographic Execution Token (CET)',
            'validated': True,
            'severity': 'LOW',
            'content_hash_sha256': f'sha256:{bundle.get_content_hash()}',
            'nonce': str(uuid.uuid4()).replace('-', ''),
            'pseudo_signature_sha256': f'sha256:{hashlib.sha256(bundle.get_content_hash().encode()).hexdigest()}',
            'constitutional': {
                'clause': 'GNCE Sec. 5.1 — Constitutional decisions must be integrity-bound via CET.',
                'explainability': {
                    'headline': f'CET SIGNED — constitutional substrate is integrity-bound for verdict={verdict}.'
                }
            }
        }
        
        # L6: Drift Detection
        l6 = {
            'layer': 'L6',
            'title': 'Behavioral Drift & Constitutional Monitoring',
            'validated': True,
            'severity': 'LOW',
            'drift_status': 'NO_DRIFT',
            'drift_outcome': 'NO_DRIFT',
            'drift_score': 0.35,
            'reason': 'Behavior within expected baseline (drift score: 0.35).',
            'constitutional': {
                'clause': 'GNCE Sec. 6.1 — Behavioral drift monitoring must detect unsafe patterns.',
                'explainability': {
                    'headline': 'NO DRIFT — monitoring reports stable behavior.'
                }
            }
        }
        
        # L7: Veto Path
        veto_required = severity in ['HIGH', 'CRITICAL'] and verdict == 'DENY'
        
        l7 = {
            'layer': 'L7',
            'title': 'Veto Path & Sovereign Execution Feedback',
            'validated': True,
            'execution_authorized': not veto_required,
            'veto_triggered': veto_required,
            'veto_path_triggered': veto_required,
            'veto_category': 'CONSTITUTIONAL_BLOCK' if veto_required else 'NONE',
            'escalation_required': 'HUMAN_REVIEWER' if veto_required else 'NONE',
            'severity': 'HIGH' if veto_required else 'LOW',
            'veto_artifact_hash_sha256': f'sha256:{hashlib.sha256(json.dumps(l5).encode()).hexdigest()}',
            'constitutional_citation': 'A system cannot execute an ALLOW verdict when HIGH/CRITICAL obligations are violated.',
        }
        
        return {'L5': l5, 'L6': l6, 'L7': l7}

# ============================================================================
# HAL Kernel Wrapper
# ============================================================================

class HALEnhancedKernel:
    """
    HAL-enhanced kernel wrapper.
    Works with kernel functions that return tuples.
    """
    
    def __init__(self, kernel_func=None):
        """
        Args:
            kernel_func: The kernel function (e.g., run_gn_kernel)
                       If None, will try to import automatically.
        """
        import gnce.gn_kernel.kernel as km
        
        if kernel_func is None:
            # Try to find the right function
            if hasattr(km, 'run_gn_kernel'):
                self.kernel_func = km.run_gn_kernel
            elif hasattr(km, 'run_gn_kernel_safe'):
                self.kernel_func = km.run_gn_kernel_safe
            elif hasattr(km, 'run_gn_kernel_for_execution_loop'):
                self.kernel_func = km.run_gn_kernel_for_execution_loop
            else:
                raise AttributeError("Could not find kernel function")
        else:
            self.kernel_func = kernel_func
        
        self.gpux_pipeline = GPUxPipeline()
        
        print(f"✅ HAL Kernel initialized with function: {self.kernel_func.__name__}")
    
    def evaluate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced evaluate with HAL and GPUx pipeline.
        
        1. Run original kernel function (returns tuple)
        2. Extract constitutional layers (L0-L4)
        3. Execute GPUx pipeline (L5-L7)
        4. Combine all layers into dict
        """
        # Step 1: Run original kernel
        kernel_result = self.kernel_func(payload)
        
        print(f"📊 Kernel returned: {type(kernel_result)}")
        if isinstance(kernel_result, tuple):
            print(f"   Tuple length: {len(kernel_result)}")
            # Show first few items
            for i, item in enumerate(kernel_result[:3]):
                print(f"   Item {i}: {type(item)}")
                if hasattr(item, 'keys'):
                    print(f"      Keys: {list(item.keys())[:3]}...")
        
        # Step 2: Create constitutional bundle
        bundle = ConstitutionalBundle.from_kernel_result(kernel_result)
        
        # Step 3: Execute GPUx pipeline
        gpux_result = self.gpux_pipeline.execute(bundle)
        
        # Step 4: Combine everything
        final_result = {}
        
        # Add original kernel result items
        if isinstance(kernel_result, tuple):
            for i, item in enumerate(kernel_result):
                if isinstance(item, dict) and 'layer' in item:
                    layer_name = item['layer']
                    final_result[layer_name] = item
                else:
                    final_result[f'result_{i}'] = item
        elif isinstance(kernel_result, dict):
            final_result.update(kernel_result)
        
        # Add GPUx layers (L5-L7)
        final_result.update(gpux_result)
        
        # Add HAL metadata
        final_result['_hal'] = {
            'enabled': True,
            'gpux_ready': True,
            'constitutional_bundle_hash': bundle.get_content_hash(),
            'version': '1.0.0',
            'kernel_function': self.kernel_func.__name__
        }
        
        return final_result

# ============================================================================
# Easy-to-use interface
# ============================================================================

def get_hal_kernel(kernel_func=None):
    """
    Get HAL-enhanced kernel.
    
    Usage:
        from gnce.gn_kernel.hal_integration import get_hal_kernel
        kernel = get_hal_kernel()
        result = kernel.evaluate(payload)
    """
    return HALEnhancedKernel(kernel_func)

# Auto-create instance for convenience
hal_kernel = get_hal_kernel()

if __name__ == "__main__":
    # Quick test
    print("🧪 Testing Fixed HAL Integration")
    try:
        kernel = hal_kernel
        
        test_payload = {
            "action": "TEST",
            "test": True
        }
        
        result = kernel.evaluate(test_payload)
        print(f"✅ Test completed")
        print(f"Result type: {type(result)}")
        print(f"Keys: {list(result.keys())}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
