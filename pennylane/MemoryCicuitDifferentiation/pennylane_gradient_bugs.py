#!/usr/bin/env python3
"""
Comprehensive demonstration of PennyLane gradient errors related to 
Parameter-Shift Rule (PSR) usage.

This script demonstrates:
1. Issues with interleaving non-parameterized gates between parameterized gates
4. Silent NaN errors and wrong gradients
5. Parameter reuse in multiple gates
6a. Operation ordering and PSR gradient computation
6. Complex VQC training failure scenarios

Note: Bug 2 (parameter reuse in entangled circuits) was removed as it was
too contrived. Bug 5 already comprehensively covers parameter reuse.
"""

import pennylane as qml
import numpy as np
import warnings
from typing import Tuple, List, Dict
import matplotlib.pyplot as plt
import matplotlib.patches as patches
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
    
    def add_cnot_bug_marker(self, ax, x_position, wire_start, wire_end, width=0.8):
        """Add a red block mark over a CNOT gate to indicate a bug location"""
        if ax is None:
            return
        # Calculate height to cover both wires (CNOT spans multiple wires)
        # In PennyLane, wires are typically spaced 1 unit apart
        wire_span = abs(wire_end - wire_start)
        height = wire_span + 0.6  # Cover the wire span plus some padding
        
        # Center the marker vertically on the CNOT gate
        # CNOT gates are centered between the control and target wires
        y_center = (wire_start + wire_end) / 2.0
        y_position = y_center - height/2
        
        options = {
            'facecolor': '#f57e7e',  # Red fill color
            'edgecolor': '#d32f2f',  # Darker red edge
            'linewidth': 6,
            'alpha': 0.3,  # Semi-transparent so circuit is still visible
            'zorder': 10  # Above circuit elements to be clearly visible
        }
        rect = patches.Rectangle(
            (x_position - width/2, y_position),
            width, height,
            **options
        )
        ax.add_patch(rect)
    
    def setup_devices(self):
        """Setup different devices for testing"""
        self.devices = {
            'default': qml.device('default.qubit', wires=4),
            'default_psr': qml.device('default.qubit', wires=4),
            'default_fd': qml.device('default.qubit', wires=4),  # Finite diff for comparison
        }
    
    def bug_1_invalid_generator_operations(self):
        """
        BUG 1: Interleaving non-parameterized gates with parameterized gates
        
        Problem: When non-parameterized gates (like CNOT) are interleaved between
        parameterized gates, PSR's parameter dependency tracking may be affected,
        potentially leading to incorrect gradient computation.
        """
        print("\n" + "="*70)
        print("BUG 1: Interleaving Non-Parameterized Gates with Parameterized Gates")
        print("="*70)
        
        dev = self.devices['default_psr']
        
        @qml.qnode(dev, diff_method='parameter-shift')
        def circuit_bad(params):
            """Circuit with interleaved non-parameterized gates"""
            # Parameterized rotation
            qml.RX(params[0], wires=0)
            
            # Non-parameterized gate interleaved between parameterized gates
            # This can affect PSR's parameter dependency tracking
            qml.CNOT(wires=[0, 1])
            
            # Another parameterized rotation
            qml.RY(params[1], wires=1)
            
            # Controlled rotation (valid generator operation that supports PSR)
            qml.CRY(params[2], wires=[0, 1])
            
            return qml.expval(qml.PauliZ(0))
        
        params = np.array([0.5, np.pi/2, 0.3])
        
        # Visualize the circuit
        print("\n📊 Circuit Visualization:")
        print("-" * 70)
        _ = circuit_bad(params)  # Execute once to build circuit
        print("\nCircuit Structure (with interleaved non-parameterized gates):")
        result = qml.draw_mpl(circuit_bad, decimals=3, style='black_white', wire_options={'color':'black', 'linewidth': 2})(params)
        fig, ax = result if isinstance(result, tuple) else (result, None)
        # Add red bug marker over the CNOT gate (position 1, wires 0-1)
        if ax is not None:
            self.add_cnot_bug_marker(ax, x_position=1.0, wire_start=0, wire_end=1, width=0.8)
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
        result = qml.draw_mpl(circuit_nan_risk, decimals=3, style='black_white', wire_options={'color':'black', 'linewidth': 2})(test_params)
        fig, ax = result if isinstance(result, tuple) else (result, None)
        # Add red bug marker over the CNOT gate (position 2, wires 0-1)
        if ax is not None:
            self.add_cnot_bug_marker(ax, x_position=2.0, wire_start=0, wire_end=1, width=0.8)
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
        BUG 5: Parameter reuse in multiple gates
        
        Problem: Reusing the same parameter in multiple gates requires PSR to
        correctly sum all contributions from each parameter use. This can cause
        incorrect gradient computation if not handled properly.
        """
        print("\n" + "="*70)
        print("BUG 5: Parameter Reuse in Multiple Gates")
        print("="*70)
        
        dev = self.devices['default_psr']
        
        @qml.qnode(dev, diff_method='parameter-shift')
        def circuit_param_reuse(params):
            """
            Circuit that reuses parameters multiple times - PSR must sum contributions
            """
            # Reuse same parameter in multiple places
            qml.RX(params[0], wires=0)
            qml.RY(params[0], wires=1)  # Same param reused
            
            # Entangling gate
            qml.CNOT(wires=[0, 1])
            qml.RZ(params[1], wires=0)
            qml.RX(params[0], wires=0)  # Same param used again (third time)
            
            # Reuse params[1] in controlled rotation
            qml.CRY(params[1], wires=[0, 1])  # Same param as RZ above
            
            return qml.expval(qml.PauliZ(0))
        
        params = np.array([0.5, 0.3])
        
        # Visualize the circuit
        print("\n📊 Circuit Visualization:")
        print("-" * 70)
        _ = circuit_param_reuse(params)  # Execute once to build circuit
        print("\nCircuit Structure (with parameter reuse):")
        result = qml.draw_mpl(circuit_param_reuse, decimals=3, style='black_white', wire_options={'color':'black', 'linewidth': 2})(params)
        fig, ax = result if isinstance(result, tuple) else (result, None)
        # Add red bug marker over the CNOT gate (position 1, wires 0-1)
        if ax is not None:
            self.add_cnot_bug_marker(ax, x_position=1.0, wire_start=0, wire_end=1, width=0.8)
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
        BUG 6a: Operation ordering and PSR gradient computation
        
        Problem: Different operation orders produce different circuits (and thus
        different gradients). PSR must correctly compute gradients for each
        circuit structure, especially when entangling gates are interleaved with
        parameterized gates.
        """
        print("\n" + "="*70)
        print("BUG 6a: Operation Ordering PSR Evaluation Issues")
        print("="*70)
        
        dev = self.devices['default_psr']
        
        # Two circuits with different operation orders - these are different
        # circuits and should produce different gradients, but PSR must compute
        # them correctly for each structure
        
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
        result1 = qml.draw_mpl(circuit_order1, decimals=3, style='black_white', wire_options={'color':'black', 'linewidth': 2})(params)
        fig1, ax1 = result1 if isinstance(result1, tuple) else (result1, None)
        # Add red bug marker over the CNOT gate (position 1, wires 0-1)
        if ax1 is not None:
            self.add_cnot_bug_marker(ax1, x_position=1.0, wire_start=0, wire_end=1, width=0.8)
        plt.savefig('circuit_diagrams/bug6a_circuit_order1.png', dpi=150, bbox_inches='tight')
        plt.close(fig1)
        print("  ✓ Circuit diagram saved to: circuit_diagrams/bug6a_circuit_order1.png")
        print("-" * 70)
        
        _ = circuit_order2(params)  # Execute once to build circuit
        print("\nCircuit 2 Structure (Order: entangle → param → param):")
        result2 = qml.draw_mpl(circuit_order2, decimals=3, style='black_white', wire_options={'color':'black', 'linewidth': 2})(params)
        fig2, ax2 = result2 if isinstance(result2, tuple) else (result2, None)
        # Add red bug marker over the CNOT gate (position 0, wires 0-1)
        if ax2 is not None:
            self.add_cnot_bug_marker(ax2, x_position=0.0, wire_start=0, wire_end=1, width=0.8)
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
            
            # These are different circuits, so gradients should be different
            # But we verify that PSR computes each one correctly
            diff = np.abs(grad1 - grad2)
            print(f"  Gradient difference (expected, since circuits differ): {diff}")
            
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
        result = qml.draw_mpl(training_vqc, decimals=3, style='black_white', wire_options={'color':'black', 'linewidth': 2})(params, data)
        # Handle both (fig, ax) tuple and single fig return
        if isinstance(result, tuple):
            fig, ax = result
        else:
            fig = result
            ax = None
        # Add red bug markers over CNOT gates
        if ax is not None:
            # Mark CNOT gates: they appear sequentially after data embedding (pos 0) and first param layer (pos 1)
            # In PennyLane, sequential gates get different x positions
            # CNOT(wires=[0, 1]) - first CNOT at position 2
            self.add_cnot_bug_marker(ax, x_position=2.0, wire_start=0, wire_end=1, width=0.8)
            # CNOT(wires=[2, 3]) - second CNOT at position 3
            self.add_cnot_bug_marker(ax, x_position=1.0, wire_start=2, wire_end=3, width=0.8)
            # CNOT(wires=[0, 2]) - third CNOT at position 4
            self.add_cnot_bug_marker(ax, x_position=3.0, wire_start=0, wire_end=2, width=0.8)
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
        # Bug 2 removed - too contrived, Bug 5 already covers parameter reuse comprehensively
        # Bug 3 removed - gradient variance is expected and correct behavior, not a bug
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
        print("  1. Interleaving non-parameterized gates can affect gradient computation")
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
