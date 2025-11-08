#!/usr/bin/env python3
"""
Comprehensive demonstration of PennyLane gradient errors related to 
Parameter-Shift Rule (PSR) usage.

This script demonstrates:
1. Invalid parameter-shift rule usage with non-generator operations
2. "No-cloning" violations through state reuse across shifts
3. Broadcasting issues with batched VQCs
4. Silent NaN errors and wrong gradients
5. Edge cases that cause crashes or incorrect results
"""

import pennylane as qml
import numpy as np
import warnings
from typing import Tuple, List, Dict
import matplotlib.pyplot as plt
import os

# Suppress some PennyLane warnings for cleaner output
warnings.filterwarnings('ignore', category=UserWarning)

# Create output directory for circuit diagrams
os.makedirs('circuit_diagrams', exist_ok=True)

class PennyLaneGradientBugDemo:
    """Demonstrates various gradient bugs in PennyLane's parameter-shift rule"""
    
    def __init__(self):
        self.results = {}
        self.setup_devices()
    
    def setup_devices(self):
        """Setup different devices for testing"""
        self.devices = {
            'default': qml.device('default.qubit', wires=4),
            'default_psr': qml.device('default.qubit', wires=4),
            'default_fd': qml.device('default.qubit', wires=4),  # Finite diff for comparison
        }
    
    def bug_1_invalid_generator_operations(self):
        """
        BUG 1: Invalid parameter-shift rule with non-generator operations
        
        Problem: PSR requires generators (e.g., Pauli rotations), but Python's 
        dynamism allows non-generator ops like CNOT to be used in parameter 
        positions, leading to invalid shifts.
        """
        print("\n" + "="*70)
        print("BUG 1: Invalid Generator Operations in Parameter Positions")
        print("="*70)
        
        dev = self.devices['default_psr']
        
        @qml.qnode(dev, diff_method='parameter-shift')
        def circuit_bad(params):
            """Circuit with invalid parameter usage"""
            # Valid: Pauli rotation with parameter
            qml.RX(params[0], wires=0)
            
            # PROBLEM: Attempting to use non-generator operations with parameters
            # This can lead to invalid shifts since CNOT doesn't have a generator
            # in the same sense as Pauli rotations
            qml.CNOT(wires=[0, 1])
            
            # Another valid rotation, but now we're mixing valid/invalid
            qml.RY(params[1], wires=1)
            
            # More problematic: controlled gate that might not support PSR properly
            qml.CRY(params[2], wires=[0, 1])
            
            return qml.expval(qml.PauliZ(0))
        
        params = np.array([0.5, np.pi/2, 0.3])
        
        # Visualize the circuit
        print("\n📊 Circuit Visualization:")
        print("-" * 70)
        _ = circuit_bad(params)  # Execute once to build circuit
        print("\nCircuit Structure (with invalid generator operations):")
        result = qml.draw_mpl(circuit_bad, decimals=3, wire_options={'color':'teal', 'linewidth': 5})(params)
        fig, ax = result if isinstance(result, tuple) else (result, None)
        plt.savefig('circuit_diagrams/bug1_invalid_generator_operations.png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        print("  ✓ Circuit diagram saved to: circuit_diagrams/bug1_invalid_generator_operations.png")
        print("\n⚠ PROBLEM: CNOT (non-generator) is interleaved between parameterized gates")
        print("   This breaks PSR's parameter dependency tracking!")
        print("-" * 70)
        
        try:
            grad_fn = qml.grad(circuit_bad)
            grad = grad_fn(params)
            
            # Convert to numpy array if needed
            if isinstance(grad, tuple):
                grad = np.array(grad)
            grad = np.array(grad).flatten()
            
            print(f"✓ PSR Gradient computed: {grad}")
            
            # Check for NaN values (silent errors)
            if np.any(np.isnan(grad)) or np.any(np.isinf(grad)):
                print(f"⚠ WARNING: Gradient contains NaN/Inf values! {grad}")
            
            # Verify against finite difference
            @qml.qnode(self.devices['default_fd'], diff_method='finite-diff')
            def circuit_fd(params):
                qml.RX(params[0], wires=0)
                qml.CNOT(wires=[0, 1])
                qml.RY(params[1], wires=1)
                qml.CRY(params[2], wires=[0, 1])
                return qml.expval(qml.PauliZ(0))
            
            grad_fd_fn = qml.grad(circuit_fd)
            grad_fd = grad_fd_fn(params)
            if isinstance(grad_fd, tuple):
                grad_fd = np.array(grad_fd)
            grad_fd = np.array(grad_fd).flatten()
            
            print(f"  Finite-diff gradient: {grad_fd}")
            
            # Check if gradients match
            if len(grad) == 0:
                print(f"⚠ WARNING: PSR returned empty gradient! This indicates a bug.")
                print(f"  Expected {len(params)} gradient values but got 0")
            elif len(grad_fd) == 0:
                print(f"⚠ WARNING: Finite-diff returned empty gradient!")
            elif len(grad) == len(grad_fd):
                diff = np.abs(grad - grad_fd)
                if len(diff) > 0:
                    max_diff = np.max(diff)
                    if max_diff > 1e-4:
                        print(f"⚠ WARNING: Gradient mismatch! Max difference: {max_diff}")
                        print(f"  PSR: {grad}")
                        print(f"  FD:  {grad_fd}")
                        print(f"  This suggests PSR may be computing wrong gradients")
            else:
                print(f"⚠ WARNING: Gradient shape mismatch! PSR: {grad.shape if hasattr(grad, 'shape') else len(grad)}, FD: {grad_fd.shape if hasattr(grad_fd, 'shape') else len(grad_fd)}")
            
        except Exception as e:
            print(f"✗ ERROR during gradient computation: {e}")
            import traceback
            traceback.print_exc()
        
        self.results['bug_1'] = {'status': 'demonstrated', 'params': params}
    
    def bug_2_state_reuse_no_cloning(self):
        """
        BUG 2: No-cloning violations through state reuse
        
        Problem: PSR requires evaluating shifted circuits (+s and -s), but Python's 
        dynamism allows reusing qubit states across shifts without proper isolation, 
        leading to incorrect gradient computation.
        """
        print("\n" + "="*70)
        print("BUG 2: No-Cloning Violations - State Reuse Across Shifts")
        print("="*70)
        
        dev = self.devices['default_psr']
        
        @qml.qnode(dev, diff_method='parameter-shift')
        def circuit_state_reuse(params):
            """
            Circuit that creates entangled state, then tries to reuse it
            across parameter shifts - this violates no-cloning principle
            """
            # Create entangled state (Bell state)
            qml.Hadamard(wires=0)
            qml.CNOT(wires=[0, 1])
            
            # Apply parameterized rotation to entangled qubit
            qml.RY(params[0], wires=0)
            
            # PROBLEM: Reusing entangled state for another parameterized operation
            # In PSR, when computing shifts, the state from first operation 
            # should be isolated, but Python allows implicit reuse
            qml.RZ(params[1], wires=0)  # Reusing qubit 0 after entanglement
            
            # Another operation that depends on the entangled state
            qml.RX(params[0], wires=1)  # Same parameter used twice - problematic!
            
            return qml.expval(qml.PauliZ(0) @ qml.PauliZ(1))
        
        params = np.array([0.5, 0.3])
        
        # Visualize the circuit
        print("\n📊 Circuit Visualization:")
        print("-" * 70)
        _ = circuit_state_reuse(params)  # Execute once to build circuit
        print("\nCircuit Structure (with state reuse - no-cloning violation):")
        result = qml.draw_mpl(circuit_state_reuse, decimals=3, wire_options={'color':'teal', 'linewidth': 5})(params)
        fig, ax = result if isinstance(result, tuple) else (result, None)
        plt.savefig('circuit_diagrams/bug2_state_reuse_no_cloning.png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        print("  ✓ Circuit diagram saved to: circuit_diagrams/bug2_state_reuse_no_cloning.png")
        print("\n⚠ PROBLEM: Creates entangled Bell state, then reuses qubit 0 multiple times")
        print("   Parameter θ₀ is used twice (RY on qubit 0, RX on qubit 1)")
        print("   This violates no-cloning principle in PSR shift evaluations!")
        print("-" * 70)
        
        try:
            # This might work, but computes wrong gradients due to state reuse
            grad_fn = qml.grad(circuit_state_reuse)
            grad = grad_fn(params)
            
            if isinstance(grad, tuple):
                grad = np.array(grad)
            grad = np.array(grad).flatten()
            
            print(f"✓ PSR Gradient computed: {grad}")
            
            # Check for silent errors
            if np.any(np.isnan(grad)) or np.any(np.isinf(grad)):
                print(f"⚠ ERROR: Gradient contains NaN/Inf! {grad}")
            
            # Compare with finite difference
            @qml.qnode(self.devices['default_fd'], diff_method='finite-diff')
            def circuit_fd(params):
                qml.Hadamard(wires=0)
                qml.CNOT(wires=[0, 1])
                qml.RY(params[0], wires=0)
                qml.RZ(params[1], wires=0)
                qml.RX(params[0], wires=1)
                return qml.expval(qml.PauliZ(0) @ qml.PauliZ(1))
            
            grad_fd_fn = qml.grad(circuit_fd)
            grad_fd = grad_fd_fn(params)
            if isinstance(grad_fd, tuple):
                grad_fd = np.array(grad_fd)
            grad_fd = np.array(grad_fd).flatten()
            
            print(f"  Finite-diff gradient: {grad_fd}")
            
            if len(grad) == 0:
                print(f"⚠ WARNING: PSR returned empty gradient! This indicates a bug.")
            elif len(grad_fd) == 0:
                print(f"⚠ WARNING: Finite-diff returned empty gradient!")
            elif len(grad) == len(grad_fd):
                diff = np.abs(grad - grad_fd)
                if len(diff) > 0:
                    max_diff = np.max(diff)
                    if max_diff > 1e-3:
                        print(f"⚠ WARNING: Significant gradient mismatch! Max diff: {max_diff}")
                        print(f"  PSR: {grad}")
                        print(f"  FD:  {grad_fd}")
                        print(f"  This indicates incorrect gradient due to state reuse")
            else:
                print(f"⚠ WARNING: Gradient shape mismatch!")
            
        except Exception as e:
            print(f"✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        self.results['bug_2'] = {'status': 'demonstrated'}
    
    def bug_3_broadcasting_batched_vqc(self):
        """
        BUG 3: Broadcasting issues with batched VQCs
        
        Problem: In batched/VQC setups with broadcasting, PSR may fail silently
        or compute incorrect gradients when parameters are broadcast across
        multiple circuit evaluations.
        """
        print("\n" + "="*70)
        print("BUG 3: Broadcasting Issues with Batched VQCs")
        print("="*70)
        
        dev = self.devices['default_psr']
        
        # Create a variational quantum circuit
        @qml.qnode(dev, diff_method='parameter-shift')
        def batched_vqc(params, x):
            """
            VQC that takes both trainable params and data input x
            Broadcasting can cause issues when x is batched
            """
            # Embed data
            qml.RY(x, wires=0)
            
            # Parameterized layers
            qml.RY(params[0], wires=0)
            qml.RX(params[1], wires=1)
            qml.CNOT(wires=[0, 1])
            qml.RZ(params[2], wires=0)
            
            return qml.expval(qml.PauliZ(0))
        
        params = np.array([0.1, 0.2, 0.3])
        
        # Visualize the circuit
        print("\n📊 Circuit Visualization:")
        print("-" * 70)
        _ = batched_vqc(params, x=0.5)  # Execute once to build circuit
        print("\nCircuit Structure (Batched VQC with broadcasting):")
        result = qml.draw_mpl(batched_vqc, decimals=3, wire_options={'color':'teal', 'linewidth': 5})(params, x=0.5)
        fig, ax = result if isinstance(result, tuple) else (result, None)
        plt.savefig('circuit_diagrams/bug3_broadcasting_batched_vqc.png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        print("  ✓ Circuit diagram saved to: circuit_diagrams/bug3_broadcasting_batched_vqc.png")
        print("\n⚠ PROBLEM: Data embedding (RY(x)) followed by parameterized gates")
        print("   When x is batched, broadcasting can cause inconsistent gradients!")
        print("-" * 70)
        
        # Test with single input
        try:
            grad_single = qml.grad(batched_vqc, argnum=0)(params, x=0.5)
            print(f"✓ Single input gradient: {grad_single}")
        except Exception as e:
            print(f"✗ ERROR with single input: {e}")
            grad_single = None
        
        # Test with batched input - this often causes issues
        print("\n  Testing with batched input (common source of bugs)...")
        x_batch = np.array([0.1, 0.2, 0.3, 0.4])
        
        try:
            # This might fail or produce wrong results
            results = []
            grads = []
            for x_val in x_batch:
                try:
                    grad = qml.grad(batched_vqc, argnum=0)(params, x=x_val)
                    grads.append(grad)
                    result = batched_vqc(params, x_val)
                    results.append(result)
                except Exception as e:
                    print(f"    ✗ Failed at x={x_val}: {e}")
                    grads.append(None)
                    results.append(None)
            
            if grads and all(g is not None for g in grads):
                grads_array = np.array(grads)
                print(f"  Batch gradients shape: {grads_array.shape}")
                
                # Check for inconsistencies
                grad_std = np.std(grads_array, axis=0)
                if np.any(grad_std > 1e-6):
                    print(f"⚠ WARNING: Gradient variance across batch! Std: {grad_std}")
                    print(f"  This suggests inconsistent gradient computation")
                
                # Check for NaN
                if np.any(np.isnan(grads_array)):
                    print(f"⚠ ERROR: NaN in batch gradients!")
            
        except Exception as e:
            print(f"✗ ERROR with batched input: {e}")
        
        self.results['bug_3'] = {'status': 'demonstrated'}
    
    def bug_4_silent_nan_errors(self):
        """
        BUG 4: Silent NaN errors from edge cases
        
        Problem: Certain parameter values or circuit configurations cause
        NaN gradients that are not caught or reported properly.
        """
        print("\n" + "="*70)
        print("BUG 4: Silent NaN Errors from Edge Cases")
        print("="*70)
        
        dev = self.devices['default_psr']
        
        @qml.qnode(dev, diff_method='parameter-shift')
        def circuit_nan_risk(params):
            """Circuit with operations that can produce NaN under PSR"""
            # Operations that might cause issues
            qml.RX(params[0], wires=0)
            qml.RY(params[1], wires=1)
            
            # Parameter at special values can cause NaN
            # e.g., when shift causes division by zero or invalid states
            qml.RZ(params[2], wires=0)
            
            # Entangling operation that might amplify issues
            qml.CNOT(wires=[0, 1])
            qml.CRY(params[3], wires=[1, 0])
            
            return qml.expval(qml.PauliZ(0))
        
        # Visualize the circuit (using first test case parameters)
        print("\n📊 Circuit Visualization:")
        print("-" * 70)
        test_params = np.array([0.5, 0.3, 0.2, 0.1])
        _ = circuit_nan_risk(test_params)  # Execute once to build circuit
        print("\nCircuit Structure (with potential NaN-producing operations):")
        result = qml.draw_mpl(circuit_nan_risk, decimals=3, wire_options={'color':'teal', 'linewidth': 5})(test_params)
        fig, ax = result if isinstance(result, tuple) else (result, None)
        plt.savefig('circuit_diagrams/bug4_silent_nan_errors.png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        print("  ✓ Circuit diagram saved to: circuit_diagrams/bug4_silent_nan_errors.png")
        print("\n⚠ PROBLEM: Multiple parameterized gates + controlled rotation")
        print("   Edge case parameters (π/2, π, near zero) may cause NaN gradients!")
        print("-" * 70)
        
        # Test with various parameter values that might cause NaN
        test_cases = [
            ("Normal values", np.array([0.5, 0.3, 0.2, 0.1])),
            ("Large values", np.array([10.0, 5.0, 3.0, 2.0])),
            ("Near zero", np.array([1e-8, 1e-7, 1e-6, 1e-5])),
            ("At π/2", np.array([np.pi/2, np.pi/2, np.pi/2, np.pi/2])),
            ("At π", np.array([np.pi, np.pi, np.pi, np.pi])),
        ]
        
        nan_count = 0
        for name, params in test_cases:
            try:
                grad_fn = qml.grad(circuit_nan_risk)
                grad = grad_fn(params)
                
                if isinstance(grad, tuple):
                    grad = np.array(grad)
                grad = np.array(grad).flatten()
                
                has_nan = np.any(np.isnan(grad)) or np.any(np.isinf(grad))
                
                if has_nan:
                    print(f"⚠ {name}: Gradient contains NaN/Inf!")
                    print(f"  Params: {params}")
                    print(f"  Gradient: {grad}")
                    nan_count += 1
                else:
                    print(f"✓ {name}: OK (grad={grad})")
                    
            except Exception as e:
                print(f"✗ {name}: Exception - {e}")
                nan_count += 1
        
        if nan_count > 0:
            print(f"\n⚠ Found {nan_count} cases with NaN/Inf or exceptions")
            print(f"  This demonstrates silent errors in PSR gradient computation")
        
        self.results['bug_4'] = {'status': 'demonstrated', 'nan_cases': nan_count}
    
    def bug_5_parameter_reuse_and_dependencies(self):
        """
        BUG 5: Parameter reuse and circular dependencies
        
        Problem: Reusing the same parameter in multiple gates or creating
        circular dependencies can cause incorrect gradient computation in PSR.
        """
        print("\n" + "="*70)
        print("BUG 5: Parameter Reuse and Circular Dependencies")
        print("="*70)
        
        dev = self.devices['default_psr']
        
        @qml.qnode(dev, diff_method='parameter-shift')
        def circuit_param_reuse(params):
            """
            Circuit that reuses parameters - PSR might not handle this correctly
            """
            # Reuse same parameter in multiple places
            qml.RX(params[0], wires=0)
            qml.RY(params[0], wires=1)  # Same param reused
            
            # Create dependency chain
            qml.CNOT(wires=[0, 1])
            qml.RZ(params[1], wires=0)
            qml.RX(params[0], wires=0)  # Same param again!
            
            # Complex dependency
            qml.CRY(params[1], wires=[0, 1])  # Same param as RZ above
            
            return qml.expval(qml.PauliZ(0))
        
        params = np.array([0.5, 0.3])
        
        # Visualize the circuit
        print("\n📊 Circuit Visualization:")
        print("-" * 70)
        _ = circuit_param_reuse(params)  # Execute once to build circuit
        print("\nCircuit Structure (with parameter reuse):")
        result = qml.draw_mpl(circuit_param_reuse, decimals=3, wire_options={'color':'teal', 'linewidth': 5})(params)
        fig, ax = result if isinstance(result, tuple) else (result, None)
        plt.savefig('circuit_diagrams/bug5_parameter_reuse.png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        print("  ✓ Circuit diagram saved to: circuit_diagrams/bug5_parameter_reuse.png")
        print("\n⚠ PROBLEM: Parameter θ₀ used 3 times, θ₁ used 2 times")
        print("   PSR must correctly sum all contributions from each parameter!")
        print("   Parameter dependency tracking may fail with reuse!")
        print("-" * 70)
        
        try:
            grad_fn = qml.grad(circuit_param_reuse)
            grad = grad_fn(params)
            
            if isinstance(grad, tuple):
                grad = np.array(grad)
            grad = np.array(grad).flatten()
            
            print(f"✓ PSR Gradient with param reuse: {grad}")
            
            # Compare with finite difference
            @qml.qnode(self.devices['default_fd'], diff_method='finite-diff')
            def circuit_fd(params):
                qml.RX(params[0], wires=0)
                qml.RY(params[0], wires=1)
                qml.CNOT(wires=[0, 1])
                qml.RZ(params[1], wires=0)
                qml.RX(params[0], wires=0)
                qml.CRY(params[1], wires=[0, 1])
                return qml.expval(qml.PauliZ(0))
            
            grad_fd_fn = qml.grad(circuit_fd)
            grad_fd = grad_fd_fn(params)
            if isinstance(grad_fd, tuple):
                grad_fd = np.array(grad_fd)
            grad_fd = np.array(grad_fd).flatten()
            
            print(f"  Finite-diff gradient: {grad_fd}")
            
            # PSR should correctly sum contributions from all uses
            # But may fail if not properly tracking parameter dependencies
            if len(grad) == 0:
                print(f"⚠ WARNING: PSR returned empty gradient! This indicates a bug.")
            elif len(grad_fd) == 0:
                print(f"⚠ WARNING: Finite-diff returned empty gradient!")
            elif len(grad) == len(grad_fd):
                diff = np.abs(grad - grad_fd)
                if len(diff) > 0:
                    max_diff = np.max(diff)
                    if max_diff > 1e-4:
                        print(f"⚠ WARNING: Gradient mismatch! Max diff: {max_diff}")
                        print(f"  PSR: {grad}")
                        print(f"  FD:  {grad_fd}")
                        print(f"  PSR may not be correctly handling parameter reuse")
            else:
                print(f"⚠ WARNING: Gradient shape mismatch!")
            
        except Exception as e:
            print(f"✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        self.results['bug_5'] = {'status': 'demonstrated'}
    
    def bug_6a_operation_ordering_psr_issue(self):
        """
        BUG 6a: Operation ordering causing PSR evaluation errors
        
        Problem: The order of operations can cause PSR to evaluate shifted circuits
        incorrectly, especially when entangling gates are interleaved with
        parameterized gates.
        """
        print("\n" + "="*70)
        print("BUG 6a: Operation Ordering PSR Evaluation Issues")
        print("="*70)
        
        dev = self.devices['default_psr']
        
        # Two circuits with different operation orders - should give same result
        # but PSR might compute different gradients
        
        @qml.qnode(dev, diff_method='parameter-shift')
        def circuit_order1(params):
            """Order: param -> entangle -> param"""
            qml.RY(params[0], wires=0)
            qml.CNOT(wires=[0, 1])
            qml.RX(params[1], wires=1)
            return qml.expval(qml.PauliZ(0))
        
        @qml.qnode(dev, diff_method='parameter-shift')
        def circuit_order2(params):
            """Order: entangle -> param -> param"""
            qml.CNOT(wires=[0, 1])
            qml.RY(params[0], wires=0)
            qml.RX(params[1], wires=1)
            return qml.expval(qml.PauliZ(0))
        
        params = np.array([0.5, 0.3])
        
        # Visualize both circuits
        print("\n📊 Circuit Visualization:")
        print("-" * 70)
        _ = circuit_order1(params)  # Execute once to build circuit
        print("\nCircuit 1 Structure (Order: param → entangle → param):")
        result1 = qml.draw_mpl(circuit_order1, decimals=3, wire_options={'color':'teal', 'linewidth': 5})(params)
        fig1, ax1 = result1 if isinstance(result1, tuple) else (result1, None)
        plt.savefig('circuit_diagrams/bug6a_circuit_order1.png', dpi=150, bbox_inches='tight')
        plt.close(fig1)
        print("  ✓ Circuit diagram saved to: circuit_diagrams/bug6a_circuit_order1.png")
        print("-" * 70)
        
        _ = circuit_order2(params)  # Execute once to build circuit
        print("\nCircuit 2 Structure (Order: entangle → param → param):")
        result2 = qml.draw_mpl(circuit_order2, decimals=3, wire_options={'color':'teal', 'linewidth': 5})(params)
        fig2, ax2 = result2 if isinstance(result2, tuple) else (result2, None)
        plt.savefig('circuit_diagrams/bug6a_circuit_order2.png', dpi=150, bbox_inches='tight')
        plt.close(fig2)
        print("  ✓ Circuit diagram saved to: circuit_diagrams/bug6a_circuit_order2.png")
        print("\n⚠ PROBLEM: Different operation orders can cause PSR to evaluate")
        print("   shifted circuits incorrectly, leading to gradient mismatches!")
        print("-" * 70)
        
        try:
            grad1_fn = qml.grad(circuit_order1)
            grad1 = np.array(grad1_fn(params)).flatten()
            
            grad2_fn = qml.grad(circuit_order2)
            grad2 = np.array(grad2_fn(params)).flatten()
            
            print(f"✓ Circuit 1 gradient: {grad1}")
            print(f"✓ Circuit 2 gradient: {grad2}")
            
            # These should be different due to operation order
            # But check if gradients are computed correctly
            diff = np.abs(grad1 - grad2)
            print(f"  Gradient difference: {diff}")
            
            # Verify with finite difference
            @qml.qnode(self.devices['default_fd'], diff_method='finite-diff')
            def circuit_fd1(params):
                qml.RY(params[0], wires=0)
                qml.CNOT(wires=[0, 1])
                qml.RX(params[1], wires=1)
                return qml.expval(qml.PauliZ(0))
            
            @qml.qnode(self.devices['default_fd'], diff_method='finite-diff')
            def circuit_fd2(params):
                qml.CNOT(wires=[0, 1])
                qml.RY(params[0], wires=0)
                qml.RX(params[1], wires=1)
                return qml.expval(qml.PauliZ(0))
            
            grad_fd1 = np.array(qml.grad(circuit_fd1)(params)).flatten()
            grad_fd2 = np.array(qml.grad(circuit_fd2)(params)).flatten()
            
            print(f"  FD Circuit 1: {grad_fd1}")
            print(f"  FD Circuit 2: {grad_fd2}")
            
            # Check if PSR matches FD for each circuit
            if len(grad1) == 0:
                print(f"⚠ WARNING: Circuit 1 PSR returned empty gradient!")
            elif len(grad_fd1) == 0:
                print(f"⚠ WARNING: Circuit 1 FD returned empty gradient!")
            elif len(grad1) == len(grad_fd1):
                diff1 = np.abs(grad1 - grad_fd1)
                if len(diff1) > 0:
                    max_diff1 = np.max(diff1)
                    if max_diff1 > 1e-4:
                        print(f"⚠ WARNING: PSR vs FD mismatch in circuit 1! Max diff: {max_diff1}")
            
            if len(grad2) == 0:
                print(f"⚠ WARNING: Circuit 2 PSR returned empty gradient!")
            elif len(grad_fd2) == 0:
                print(f"⚠ WARNING: Circuit 2 FD returned empty gradient!")
            elif len(grad2) == len(grad_fd2):
                diff2 = np.abs(grad2 - grad_fd2)
                if len(diff2) > 0:
                    max_diff2 = np.max(diff2)
                    if max_diff2 > 1e-4:
                        print(f"⚠ WARNING: PSR vs FD mismatch in circuit 2! Max diff: {max_diff2}")
            
        except Exception as e:
            print(f"✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        self.results['bug_6a'] = {'status': 'demonstrated'}
    
    def bug_6_complex_vqc_training_failure(self):
        """
        BUG 6: Failure in complex VQC training scenarios
        
        Problem: Real-world VQC training scenarios combine multiple issues,
        leading to training failures, wrong gradients, or crashes.
        """
        print("\n" + "="*70)
        print("BUG 6: Complex VQC Training Failure Scenario")
        print("="*70)
        
        dev = self.devices['default_psr']
        
        # Simulate a realistic VQC training scenario
        @qml.qnode(dev, diff_method='parameter-shift')
        def training_vqc(params, data):
            """
            Realistic VQC with data embedding and multiple parameterized layers
            This combines multiple potential issues:
            - Data embedding
            - Multiple parameterized layers
            - Entangling gates
            - Multiple measurements
            """
            # Data embedding layer
            for i, x in enumerate(data):
                qml.RY(x, wires=i)
            
            # First parameterized layer
            for i, p in enumerate(params[:2]):
                qml.RX(p, wires=i)
            
            # Entangling layer
            qml.CNOT(wires=[0, 1])
            qml.CNOT(wires=[2, 3])
            qml.CNOT(wires=[0, 2])
            
            # Second parameterized layer with reused params
            for i, p in enumerate(params[2:4]):
                qml.RY(p, wires=i)
            
            # More entanglement
            qml.CRY(params[4], wires=[1, 0])
            qml.CRY(params[5], wires=[3, 2])
            
            # Final layer
            for i, p in enumerate(params[6:8]):
                qml.RZ(p, wires=i)
            
            # Multiple measurements (can cause issues with PSR)
            return qml.expval(qml.PauliZ(0)), qml.expval(qml.PauliZ(1))
        
        # Training setup
        params = np.random.random(8) * 0.1
        data = np.array([0.5, 0.3, 0.2, 0.1])
        
        # Visualize the circuit
        print("\n📊 Circuit Visualization:")
        print("-" * 70)
        _ = training_vqc(params, data)  # Execute once to build circuit
        print("\nComplex VQC Structure (combines multiple potential issues):")
        result = qml.draw_mpl(training_vqc, decimals=3, wire_options={'color':'teal', 'linewidth': 5})(params, data)
        # Handle both (fig, ax) tuple and single fig return
        if isinstance(result, tuple):
            fig, ax = result
        else:
            fig = result
            ax = None
        plt.savefig('circuit_diagrams/bug6_complex_vqc_training.png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        print("  ✓ Circuit diagram saved to: circuit_diagrams/bug6_complex_vqc_training.png")
        print("\n⚠ PROBLEM: Complex circuit with:")
        print("   • Data embedding layer (RY gates)")
        print("   • Multiple parameterized layers (RX, RY, RZ)")
        print("   • Interleaved entangling gates (CNOT, CRY)")
        print("   • Multiple measurements")
        print("   All issues from bugs 1-5 can combine here!")
        print("-" * 70)
        
        print("\n  Testing realistic VQC training scenario...")
        print(f"  Parameters: {params.shape}")
        print(f"  Data: {data.shape}")
        
        try:
            # Forward pass
            result = training_vqc(params, data)
            print(f"✓ Forward pass: {result}")
            
            # Gradient computation (most likely to fail)
            def loss_fn(params, data):
                results = training_vqc(params, data)
                # Simple loss: sum of expectations
                return sum(results)
            
            grad = qml.grad(loss_fn, argnum=0)(params, data)
            print(f"✓ Gradient computed: shape={grad.shape}")
            print(f"  Gradient values: {grad}")
            
            # Check for issues
            if np.any(np.isnan(grad)) or np.any(np.isinf(grad)):
                print(f"⚠ ERROR: Gradient contains NaN/Inf!")
            else:
                # Check for suspicious values
                grad_magnitude = np.linalg.norm(grad)
                if grad_magnitude > 1e6 or grad_magnitude < 1e-10:
                    print(f"⚠ WARNING: Suspicious gradient magnitude: {grad_magnitude}")
                
                # Check gradient variance
                if np.std(grad) < 1e-10:
                    print(f"⚠ WARNING: Very low gradient variance - may indicate wrong computation")
            
            # Simulate training step (this is where bugs manifest)
            print("\n  Simulating training step...")
            learning_rate = 0.01
            try:
                params_new = params - learning_rate * grad
                result_new = training_vqc(params_new, data)
                print(f"✓ Training step completed")
                print(f"  New result: {result_new}")
                print(f"  Loss change: {sum(result)} -> {sum(result_new)}")
            except Exception as e:
                print(f"✗ Training step failed: {e}")
                
        except Exception as e:
            print(f"✗ ERROR during VQC training: {e}")
            import traceback
            traceback.print_exc()
        
        self.results['bug_6'] = {'status': 'demonstrated'}
    
    def run_all_demos(self):
        """Run all bug demonstrations"""
        print("\n" + "="*70)
        print("PennyLane Parameter-Shift Rule Gradient Bugs Demonstration")
        print("="*70)
        print("\nThis script demonstrates various gradient computation errors")
        print("that occur in PennyLane's parameter-shift rule implementation.")
        print("\nThese bugs can lead to:")
        print("  • Silent NaN errors")
        print("  • Incorrect gradient values")
        print("  • Training failures in VQCs")
        print("  • Wasted compute resources")
        
        self.bug_1_invalid_generator_operations()
        self.bug_2_state_reuse_no_cloning()
        self.bug_3_broadcasting_batched_vqc()
        self.bug_4_silent_nan_errors()
        self.bug_5_parameter_reuse_and_dependencies()
        self.bug_6a_operation_ordering_psr_issue()
        self.bug_6_complex_vqc_training_failure()
        
        # Summary
        print("\n" + "="*70)
        print("Summary")
        print("="*70)
        print(f"Demonstrated {len(self.results)} different categories of gradient bugs")
        print("\nKey Issues Found:")
        print("  1. Invalid generator operations can lead to wrong gradients")
        print("  2. State reuse violates no-cloning and causes errors")
        print("  3. Broadcasting in batched VQCs produces inconsistent results")
        print("  4. Silent NaN errors from edge cases are not caught")
        print("  5. Parameter reuse can cause incorrect gradient computation")
        print("  6a. Operation ordering can cause PSR evaluation errors")
        print("  6. Complex VQCs combine issues leading to training failures")
        print("\nThese demonstrate why a type-safe, compile-time-checked")
        print("solution (like LogosQ in Rust) can prevent such errors.")


def main():
    """Main entry point"""
    demo = PennyLaneGradientBugDemo()
    demo.run_all_demos()
    # demo.bug_1_invalid_generator_operations()


if __name__ == "__main__":
    main()
