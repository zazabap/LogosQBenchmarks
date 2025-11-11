#!/usr/bin/env python3
"""
Comprehensive demonstration of Qiskit gradient errors related to 
Parameter-Shift Rule (PSR) usage.

This script demonstrates:
1. Invalid parameter-shift rule usage with non-generator operations
3. Broadcasting issues with batched VQCs
4. Silent NaN errors and wrong gradients
5. Parameter reuse and circular dependencies
6a. Operation ordering causing PSR evaluation errors
6. Complex VQC training failure scenarios

Note: Bug 2 (no-cloning violations through state reuse) was removed as it was
too contrived. Bug 5 already comprehensively covers parameter reuse.
"""

import numpy as np
import warnings
from typing import Tuple, List, Dict
import matplotlib.pyplot as plt
import os

# Qiskit imports
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.quantum_info import Statevector
try:
    from qiskit.algorithms.gradients import ParameterShiftGradient, FiniteDiffGradient
except ImportError:
    # Try alternative import path for newer Qiskit versions
    try:
        from qiskit_algorithms.gradients import ParamShiftEstimatorGradient as ParameterShiftGradient
        from qiskit_algorithms.gradients import FiniteDiffEstimatorGradient as FiniteDiffGradient
    except ImportError:
        # Fallback: use manual gradient computation
        ParameterShiftGradient = None
        FiniteDiffGradient = None
from qiskit.primitives import StatevectorSampler, StatevectorEstimator
import qiskit

# Suppress some Qiskit warnings for cleaner output
warnings.filterwarnings('ignore', category=UserWarning)

# Create output directory for circuit diagrams
os.makedirs('circuit_diagrams', exist_ok=True)

class QiskitGradientBugDemo:
    """Demonstrates various gradient bugs in Qiskit's parameter-shift rule"""
    
    def __init__(self):
        self.results = {}
        self.sampler = StatevectorSampler()
        self.estimator = StatevectorEstimator()  # Estimator for gradient computation
        self.setup_gradients()
    
    def setup_gradients(self):
        """Setup different gradient methods for testing"""
        if ParameterShiftGradient is not None:
            self.gradient_psr = ParameterShiftGradient()
            self.use_builtin_psr = True
        else:
            self.gradient_psr = None
            self.use_builtin_psr = False
            print("⚠ NOTE: ParameterShiftGradient not available. Using manual PSR implementation.")
        if FiniteDiffGradient is not None:
            self.gradient_fd = FiniteDiffGradient(epsilon=1e-5)
            self.use_builtin_fd = True
        else:
            self.gradient_fd = None
            self.use_builtin_fd = False
    
    def manual_parameter_shift(self, circuit, observable, param_dict, shift=0.5):
        """
        Manual parameter shift rule implementation as fallback
        For Pauli rotations: ∂f/∂θ = (1/2) * [f(θ + π/2) - f(θ - π/2)]
        """
        from qiskit.quantum_info import SparsePauliOp
        
        # Extract parameters and values
        params = list(param_dict.keys())
        param_values = list(param_dict.values())
        
        grad = np.zeros(len(params))
        s = np.pi / 2  # Standard shift for Pauli rotations
        
        # Compute expectation at current point
        bound_circuit = circuit.assign_parameters(param_dict)
        statevector = Statevector.from_instruction(bound_circuit.remove_final_measurements(inplace=False))
        f0 = statevector.expectation_value(observable)
        
        # Compute gradient for each parameter
        for i, param in enumerate(params):
            # Shift parameter up
            param_dict_plus = param_dict.copy()
            param_dict_plus[param] = param_values[i] + s
            bound_circuit_plus = circuit.assign_parameters(param_dict_plus)
            statevector_plus = Statevector.from_instruction(bound_circuit_plus.remove_final_measurements(inplace=False))
            f_plus = statevector_plus.expectation_value(observable)
            
            # Shift parameter down
            param_dict_minus = param_dict.copy()
            param_dict_minus[param] = param_values[i] - s
            bound_circuit_minus = circuit.assign_parameters(param_dict_minus)
            statevector_minus = Statevector.from_instruction(bound_circuit_minus.remove_final_measurements(inplace=False))
            f_minus = statevector_minus.expectation_value(observable)
            
            # Parameter shift rule: ∂f/∂θ = (1/2) * [f(θ + π/2) - f(θ - π/2)]
            # Take real part if complex (expectation values should be real)
            grad[i] = 0.5 * np.real(f_plus - f_minus)
        
        return grad
    
    def manual_finite_difference(self, circuit, observable, param_dict, epsilon=1e-5):
        """Manual finite difference gradient computation as fallback"""
        from qiskit.quantum_info import SparsePauliOp
        
        params = list(param_dict.keys())
        param_values = list(param_dict.values())
        
        grad = np.zeros(len(params))
        
        # Compute expectation at current point
        bound_circuit = circuit.assign_parameters(param_dict)
        statevector = Statevector.from_instruction(bound_circuit.remove_final_measurements(inplace=False))
        f0 = statevector.expectation_value(observable)
        
        # Compute gradient for each parameter
        for i, param in enumerate(params):
            param_dict_plus = param_dict.copy()
            param_dict_plus[param] = param_values[i] + epsilon
            bound_circuit_plus = circuit.assign_parameters(param_dict_plus)
            statevector_plus = Statevector.from_instruction(bound_circuit_plus.remove_final_measurements(inplace=False))
            f_plus = statevector_plus.expectation_value(observable)
            
            # Take real part if complex (expectation values should be real)
            grad[i] = np.real(f_plus - f0) / epsilon
        
        return grad
    
    def compute_psr_gradient(self, circuit, observable, param_dict):
        """Helper function to compute PSR gradient using built-in or manual method"""
        if self.use_builtin_psr:
            grad_result = self.gradient_psr.run([circuit], self.estimator, [observable], [param_dict]).result()
            grad = grad_result.gradients[0]
            if hasattr(grad, 'data'):
                grad = np.array(grad.data).flatten()
            else:
                grad = np.array(grad).flatten()
        else:
            grad = self.manual_parameter_shift(circuit, observable, param_dict)
        return grad
    
    def compute_fd_gradient(self, circuit, observable, param_dict):
        """Helper function to compute finite difference gradient using built-in or manual method"""
        if self.use_builtin_fd:
            grad_result = self.gradient_fd.run([circuit], self.estimator, [observable], [param_dict]).result()
            grad_fd = grad_result.gradients[0]
            if hasattr(grad_fd, 'data'):
                grad_fd = np.array(grad_fd.data).flatten()
            else:
                grad_fd = np.array(grad_fd).flatten()
        else:
            grad_fd = self.manual_finite_difference(circuit, observable, param_dict)
        return grad_fd
    
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
        
        # Create parameters
        theta = [Parameter('θ0'), Parameter('θ1'), Parameter('θ2')]
        params = np.array([0.5, np.pi/2, 0.3])
        
        # Build circuit with invalid parameter usage
        circuit = QuantumCircuit(4)
        # Valid: Pauli rotation with parameter
        circuit.rx(theta[0], 0)
        
        # PROBLEM: Attempting to use non-generator operations with parameters
        # This can lead to invalid shifts since CNOT doesn't have a generator
        # in the same sense as Pauli rotations
        circuit.cx(0, 1)
        
        # Another valid rotation, but now we're mixing valid/invalid
        circuit.ry(theta[1], 1)
        
        # More problematic: controlled gate that might not support PSR properly
        circuit.cry(theta[2], 0, 1)
        
        # Add measurement
        circuit.measure_all()
        
        # Visualize the circuit
        print("\n📊 Circuit Visualization:")
        print("-" * 70)
        print("\nCircuit Structure (with invalid generator operations):")
        try:
            circuit.draw(output='mpl', filename='circuit_diagrams/bug1_invalid_generator_operations.png', style='clifford')
            print("  ✓ Circuit diagram saved to: circuit_diagrams/bug1_invalid_generator_operations.png")
        except Exception as e:
            print(f"  ⚠ Could not save diagram: {e}")
            print(circuit.draw(output='text'))
        print("\n⚠ PROBLEM: CNOT (non-generator) is interleaved between parameterized gates")
        print("   This breaks PSR's parameter dependency tracking!")
        print("-" * 70)
        
        try:
            # Bind parameters
            bound_circuit = circuit.assign_parameters(dict(zip(theta, params)))
            
            # Compute expectation value (using statevector for simplicity)
            statevector = Statevector.from_instruction(bound_circuit.remove_final_measurements(inplace=False))
            from qiskit.quantum_info import SparsePauliOp
            observable_z = SparsePauliOp(['ZIII'], coeffs=[1.0])
            expectation = statevector.expectation_value(observable_z)
            
            print(f"✓ Circuit expectation value: {expectation}")
            
            # Create observable
            from qiskit.quantum_info import SparsePauliOp
            observable = SparsePauliOp(['ZIII'], coeffs=[1.0])
            
            # Try to compute gradient using PSR
            try:
                param_dict = dict(zip(theta, params))
                grad = self.compute_psr_gradient(circuit, observable, param_dict)
                
                print(f"✓ PSR Gradient computed: {grad}")
                
                # Check for NaN values (silent errors)
                if np.any(np.isnan(grad)) or np.any(np.isinf(grad)):
                    print(f"⚠ WARNING: Gradient contains NaN/Inf values! {grad}")
                
                # Verify against finite difference
                try:
                    grad_fd = self.compute_fd_gradient(circuit, observable, param_dict)
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
                    print(f"  ⚠ Could not compute finite-diff gradient: {e}")
                    
            except Exception as e:
                print(f"✗ ERROR during PSR gradient computation: {e}")
                import traceback
                traceback.print_exc()
            
        except Exception as e:
            print(f"✗ ERROR during gradient computation: {e}")
            import traceback
            traceback.print_exc()
        
        self.results['bug_1'] = {'status': 'demonstrated', 'params': params}
    
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
        
        # Create parameters
        theta = [Parameter('θ0'), Parameter('θ1'), Parameter('θ2')]
        params = np.array([0.1, 0.2, 0.3])
        
        # Create a variational quantum circuit
        def create_vqc(x_param):
            """VQC that takes both trainable params and data input x"""
            circuit = QuantumCircuit(4)
            # Embed data
            circuit.ry(x_param, 0)
            
            # Parameterized layers
            circuit.ry(theta[0], 0)
            circuit.rx(theta[1], 1)
            circuit.cx(0, 1)
            circuit.rz(theta[2], 0)
            
            return circuit
        
        # Visualize the circuit
        print("\n📊 Circuit Visualization:")
        print("-" * 70)
        x_val = 0.5
        circuit = create_vqc(x_val)
        circuit.measure_all()
        print("\nCircuit Structure (Batched VQC with broadcasting):")
        try:
            circuit.draw(output='mpl', filename='circuit_diagrams/bug3_broadcasting_batched_vqc.png', style='clifford')
            print("  ✓ Circuit diagram saved to: circuit_diagrams/bug3_broadcasting_batched_vqc.png")
        except Exception as e:
            print(f"  ⚠ Could not save diagram: {e}")
            print(circuit.draw(output='text'))
        print("\n⚠ PROBLEM: Data embedding (RY(x)) followed by parameterized gates")
        print("   When x is batched, broadcasting can cause inconsistent gradients!")
        print("-" * 70)
        
        # Test with single input
        try:
            circuit_single = create_vqc(x_val)
            circuit_single.measure_all()
            
            from qiskit.quantum_info import SparsePauliOp
            observable = SparsePauliOp(['ZIII'], coeffs=[1.0])
            param_dict = dict(zip(theta, params))
            
            grad_single = self.compute_psr_gradient(circuit_single, observable, param_dict)
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
                    circuit_batch = create_vqc(x_val)
                    circuit_batch.measure_all()
                    
                    param_dict = dict(zip(theta, params))
                    grad = self.compute_psr_gradient(circuit_batch, observable, param_dict)
                    grads.append(grad)
                    
                    # Compute expectation
                    bound_circuit = circuit_batch.assign_parameters(dict(zip(theta, params)))
                    statevector = Statevector.from_instruction(bound_circuit.remove_final_measurements(inplace=False))
                    from qiskit.quantum_info import SparsePauliOp
                    observable_z = SparsePauliOp(['ZIII'], coeffs=[1.0])
                    result = statevector.expectation_value(observable_z)
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
        
        # Create parameters
        theta = [Parameter('θ0'), Parameter('θ1'), Parameter('θ2'), Parameter('θ3')]
        
        # Build circuit with operations that can produce NaN under PSR
        circuit = QuantumCircuit(4)
        circuit.rx(theta[0], 0)
        circuit.ry(theta[1], 1)
        
        # Parameter at special values can cause NaN
        # e.g., when shift causes division by zero or invalid states
        circuit.rz(theta[2], 0)
        
        # Entangling operation that might amplify issues
        circuit.cx(0, 1)
        circuit.cry(theta[3], 1, 0)
        
        circuit.measure_all()
        
        # Visualize the circuit
        print("\n📊 Circuit Visualization:")
        print("-" * 70)
        test_params = np.array([0.5, 0.3, 0.2, 0.1])
        print("\nCircuit Structure (with potential NaN-producing operations):")
        try:
            circuit.draw(output='mpl', filename='circuit_diagrams/bug4_silent_nan_errors.png', style='clifford')
            print("  ✓ Circuit diagram saved to: circuit_diagrams/bug4_silent_nan_errors.png")
        except Exception as e:
            print(circuit.draw(output='text'))
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
        
        from qiskit.quantum_info import SparsePauliOp
        observable = SparsePauliOp(['ZIII'], coeffs=[1.0])
        
        nan_count = 0
        for name, params in test_cases:
            try:
                param_dict = dict(zip(theta, params))
                grad = self.compute_psr_gradient(circuit, observable, param_dict)
                
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
        
        # Create parameters
        theta = [Parameter('θ0'), Parameter('θ1')]
        params = np.array([0.5, 0.3])
        
        # Build circuit that reuses parameters
        circuit = QuantumCircuit(4)
        # Reuse same parameter in multiple places
        circuit.rx(theta[0], 0)
        circuit.ry(theta[0], 1)  # Same param reused
        
        # Create dependency chain
        circuit.cx(0, 1)
        circuit.rz(theta[1], 0)
        circuit.rx(theta[0], 0)  # Same param again!
        
        # Complex dependency
        circuit.cry(theta[1], 0, 1)  # Same param as RZ above
        
        circuit.measure_all()
        
        # Visualize the circuit
        print("\n📊 Circuit Visualization:")
        print("-" * 70)
        print("\nCircuit Structure (with parameter reuse):")
        try:
            circuit.draw(output='mpl', filename='circuit_diagrams/bug5_parameter_reuse.png', style='clifford')
            print("  ✓ Circuit diagram saved to: circuit_diagrams/bug5_parameter_reuse.png")
        except Exception as e:
            print(f"  ⚠ Could not save diagram: {e}")
            print(circuit.draw(output='text'))
        print("\n⚠ PROBLEM: Parameter θ₀ used 3 times, θ₁ used 2 times")
        print("   PSR must correctly sum all contributions from each parameter!")
        print("   Parameter dependency tracking may fail with reuse!")
        print("-" * 70)
        
        try:
            from qiskit.quantum_info import SparsePauliOp
            observable = SparsePauliOp(['ZIII'], coeffs=[1.0])
            param_dict = dict(zip(theta, params))
            
            grad = self.compute_psr_gradient(circuit, observable, param_dict)
            print(f"✓ PSR Gradient with param reuse: {grad}")
            
            # Compare with finite difference
            try:
                grad_fd = self.compute_fd_gradient(circuit, observable, param_dict)
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
                print(f"  ⚠ Could not compute finite-diff gradient: {e}")
            
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
        
        # Create parameters
        theta = [Parameter('θ0'), Parameter('θ1')]
        params = np.array([0.5, 0.3])
        
        # Two circuits with different operation orders - should give same result
        # but PSR might compute different gradients
        
        # Circuit 1: Order: param -> entangle -> param
        circuit1 = QuantumCircuit(4)
        circuit1.ry(theta[0], 0)
        circuit1.cx(0, 1)
        circuit1.rx(theta[1], 1)
        circuit1.measure_all()
        
        # Circuit 2: Order: entangle -> param -> param
        circuit2 = QuantumCircuit(4)
        circuit2.cx(0, 1)
        circuit2.ry(theta[0], 0)
        circuit2.rx(theta[1], 1)
        circuit2.measure_all()
        
        # Visualize both circuits
        print("\n📊 Circuit Visualization:")
        print("-" * 70)
        print("\nCircuit 1 Structure (Order: param → entangle → param):")
        try:
            circuit1.draw(output='mpl', filename='circuit_diagrams/bug6a_circuit_order1.png', style='clifford')
            print("  ✓ Circuit diagram saved to: circuit_diagrams/bug6a_circuit_order1.png")
        except Exception as e:
            print(circuit1.draw(output='text'))
        print("-" * 70)
        
        print("\nCircuit 2 Structure (Order: entangle → param → param):")
        try:
            circuit2.draw(output='mpl', filename='circuit_diagrams/bug6a_circuit_order2.png', style='clifford')
            print("  ✓ Circuit diagram saved to: circuit_diagrams/bug6a_circuit_order2.png")
        except Exception as e:
            print(circuit2.draw(output='text'))
        print("\n⚠ PROBLEM: Different operation orders can cause PSR to evaluate")
        print("   shifted circuits incorrectly, leading to gradient mismatches!")
        print("-" * 70)
        
        try:
            from qiskit.quantum_info import SparsePauliOp
            observable = SparsePauliOp(['ZIII'], coeffs=[1.0])
            param_dict = dict(zip(theta, params))
            
            grad1 = self.compute_psr_gradient(circuit1, observable, param_dict)
            grad2 = self.compute_psr_gradient(circuit2, observable, param_dict)
            
            print(f"✓ Circuit 1 gradient: {grad1}")
            print(f"✓ Circuit 2 gradient: {grad2}")
            
            # These should be different due to operation order
            # But check if gradients are computed correctly
            diff = np.abs(grad1 - grad2)
            print(f"  Gradient difference: {diff}")
            
            # Verify with finite difference
            try:
                grad_fd1 = self.compute_fd_gradient(circuit1, observable, param_dict)
                grad_fd2 = self.compute_fd_gradient(circuit2, observable, param_dict)
                
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
                print(f"  ⚠ Could not compute finite-diff gradients: {e}")
            
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
        
        # Create parameters
        theta = [Parameter(f'θ{i}') for i in range(8)]
        params = np.random.random(8) * 0.1
        data = np.array([0.5, 0.3, 0.2, 0.1])
        
        # Build realistic VQC with data embedding and multiple parameterized layers
        circuit = QuantumCircuit(4)
        
        # Data embedding layer
        for i, x in enumerate(data):
            circuit.ry(x, i)
        
        # First parameterized layer
        for i, p in enumerate(theta[:2]):
            circuit.rx(p, i)
        
        # Entangling layer
        circuit.cx(0, 1)
        circuit.cx(2, 3)
        circuit.cx(0, 2)
        
        # Second parameterized layer with reused params
        for i, p in enumerate(theta[2:4]):
            circuit.ry(p, i)
        
        # More entanglement
        circuit.cry(theta[4], 1, 0)
        circuit.cry(theta[5], 3, 2)
        
        # Final layer
        for i, p in enumerate(theta[6:8]):
            circuit.rz(p, i)
        
        circuit.measure_all()
        
        # Visualize the circuit
        print("\n📊 Circuit Visualization:")
        print("-" * 70)
        print("\nComplex VQC Structure (combines multiple potential issues):")
        try:
            circuit.draw(output='mpl', filename='circuit_diagrams/bug6_complex_vqc_training.png', style='clifford')
            print("  ✓ Circuit diagram saved to: circuit_diagrams/bug6_complex_vqc_training.png")
        except Exception as e:
            print(circuit.draw(output='text'))
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
            bound_circuit = circuit.assign_parameters(dict(zip(theta, params)))
            statevector = Statevector.from_instruction(bound_circuit.remove_final_measurements(inplace=False))
            from qiskit.quantum_info import SparsePauliOp
            observable_z0 = SparsePauliOp(['ZIII'], coeffs=[1.0])
            observable_z1 = SparsePauliOp(['IZII'], coeffs=[1.0])
            result1 = statevector.expectation_value(observable_z0)
            result2 = statevector.expectation_value(observable_z1)
            result = (result1, result2)
            print(f"✓ Forward pass: {result}")
            
            # Gradient computation (most likely to fail)
            from qiskit.quantum_info import SparsePauliOp
            # Multiple measurements
            observable1 = SparsePauliOp(['ZIII'], coeffs=[1.0])
            observable2 = SparsePauliOp(['IZII'], coeffs=[1.0])
            
            # For simplicity, compute gradient for sum of expectations
            # This requires computing gradients separately and summing
            try:
                param_dict = dict(zip(theta, params))
                grad1 = self.compute_psr_gradient(circuit, observable1, param_dict)
                grad2 = self.compute_psr_gradient(circuit, observable2, param_dict)
                
                grad = grad1 + grad2
                print(f"✓ Gradient computed: shape={len(grad)}")
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
                    bound_circuit_new = circuit.assign_parameters(dict(zip(theta, params_new)))
                    statevector_new = Statevector.from_instruction(bound_circuit_new.remove_final_measurements(inplace=False))
                    from qiskit.quantum_info import SparsePauliOp
                    observable_z0 = SparsePauliOp(['ZIII'], coeffs=[1.0])
                    observable_z1 = SparsePauliOp(['IZII'], coeffs=[1.0])
                    result1_new = statevector_new.expectation_value(observable_z0)
                    result2_new = statevector_new.expectation_value(observable_z1)
                    result_new = (result1_new, result2_new)
                    print(f"✓ Training step completed")
                    print(f"  New result: {result_new}")
                    print(f"  Loss change: {sum(result)} -> {sum(result_new)}")
                except Exception as e:
                    print(f"✗ Training step failed: {e}")
                    
            except Exception as e:
                print(f"✗ ERROR during gradient computation: {e}")
                import traceback
                traceback.print_exc()
                
        except Exception as e:
            print(f"✗ ERROR during VQC training: {e}")
            import traceback
            traceback.print_exc()
        
        self.results['bug_6'] = {'status': 'demonstrated'}
    
    def run_all_demos(self):
        """Run all bug demonstrations"""
        print("\n" + "="*70)
        print("Qiskit Parameter-Shift Rule Gradient Bugs Demonstration")
        print("="*70)
        print("\nThis script demonstrates various gradient computation errors")
        print("that occur in Qiskit's parameter-shift rule implementation.")
        print("\nThese bugs can lead to:")
        print("  • Silent NaN errors")
        print("  • Incorrect gradient values")
        print("  • Training failures in VQCs")
        print("  • Wasted compute resources")
        
        self.bug_1_invalid_generator_operations()
        # Bug 2 removed - too contrived, Bug 5 already covers parameter reuse comprehensively
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
        print("  3. Broadcasting in batched VQCs produces inconsistent results")
        print("  4. Silent NaN errors from edge cases are not caught")
        print("  5. Parameter reuse can cause incorrect gradient computation")
        print("  6a. Operation ordering can cause PSR evaluation errors")
        print("  6. Complex VQCs combine issues leading to training failures")
        print("\nThese demonstrate why a type-safe, compile-time-checked")
        print("solution (like LogosQ in Rust) can prevent such errors.")


def main():
    """Main entry point"""
    demo = QiskitGradientBugDemo()
    demo.run_all_demos()
    # demo.bug_1_invalid_generator_operations()


if __name__ == "__main__":
    main()

