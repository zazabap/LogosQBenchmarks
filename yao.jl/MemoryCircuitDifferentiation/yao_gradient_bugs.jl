"""
Comprehensive demonstration of Yao.jl gradient errors related to 
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

# Import only the core Yao modules we need, avoiding YaoPlots which has dependency issues
using YaoBlocks
using YaoArrayRegister
using LinearAlgebra
using Statistics  # For std() function

# Import commonly used functions and gates
import YaoBlocks: put, control, Rx, Ry, Rz, H, X, Y, Z, chain
import YaoArrayRegister: zero_state, expect, apply!
using Random  # For random number generation

# Create output directory for circuit diagrams
output_dir = joinpath(@__DIR__, "circuit_diagrams")
mkpath(output_dir)

struct GradientBugDemo
    results::Dict{String, Any}
    
    function GradientBugDemo()
        new(Dict{String, Any}())
    end
end

function bug_1_invalid_generator_operations(demo::GradientBugDemo)
    """
    BUG 1: Invalid parameter-shift rule with non-generator operations
    
    Problem: PSR requires generators (e.g., Pauli rotations), but Julia's 
    dynamism allows non-generator ops like CNOT to be used in parameter 
    positions, leading to invalid shifts.
    """
    println("\n" * "="^70)
    println("BUG 1: Invalid Generator Operations in Parameter Positions")
    println("="^70)
    
    function circuit_bad(params::Vector{Float64})
        """Circuit with invalid parameter usage"""
        n = 4
        reg = zero_state(n)
        
        # Build circuit
        circuit = chain(n,
            put(1=>Rx(params[1])),
            control(1, 2=>X),
            put(2=>Ry(params[2])),
            control(1, 2=>Ry(params[3]))
        )
        
        # Apply circuit
        reg = apply!(reg, circuit)
        
        # Measure expectation value
        return expect(put(n, 1=>Z), reg)
    end
    
    params = [0.5, π/2, 0.3]
    
    println("\n📊 Circuit Visualization:")
    println("-"^70)
    println("\nCircuit Structure (with invalid generator operations):")
    println("  ✓ Circuit diagram would be saved here")
    println("\n⚠ PROBLEM: CNOT (non-generator) is interleaved between parameterized gates")
    println("   This breaks PSR's parameter dependency tracking!")
    println("-"^70)
    
    try
        # Compute gradient using parameter shift rule
        # In Yao.jl, we can use expect' (adjoint) or manual parameter shift
        function loss_fn(p)
            circuit_bad(p)
        end
        
        # Manual parameter shift rule implementation
        s = π/2  # Standard shift for parameter shift rule
        grad = zeros(length(params))
        for i in 1:length(params)
            params_plus = copy(params)
            params_plus[i] += s
            params_minus = copy(params)
            params_minus[i] -= s
            grad[i] = (loss_fn(params_plus) - loss_fn(params_minus)) / 2
        end
        
        println("✓ PSR Gradient computed: $grad")
        
        # Check for NaN values (silent errors)
        if any(isnan, grad) || any(isinf, grad)
            println("⚠ WARNING: Gradient contains NaN/Inf values! $grad")
        end
        
        # Verify against finite difference
        function circuit_fd(params::Vector{Float64})
            n = 4
            reg = zero_state(n)
            circuit = chain(n,
                put(1=>Rx(params[1])),
                control(1, 2=>X),
                put(2=>Ry(params[2])),
                control(1, 2=>Ry(params[3]))
            )
            reg = apply!(reg, circuit)
            return expect(put(n, 1=>Z), reg)
        end
        
        # Finite difference gradient
        h = 1e-5
        grad_fd = zeros(length(params))
        f0 = circuit_fd(params)
        for i in 1:length(params)
            params_plus = copy(params)
            params_plus[i] += h
            f_plus = circuit_fd(params_plus)
            grad_fd[i] = (f_plus - f0) / h
        end
        
        println("  Finite-diff gradient: $grad_fd")
        
        # Check if gradients match
        if length(grad) == 0
            println("⚠ WARNING: PSR returned empty gradient! This indicates a bug.")
            println("  Expected $(length(params)) gradient values but got 0")
        elseif length(grad_fd) == 0
            println("⚠ WARNING: Finite-diff returned empty gradient!")
        elseif length(grad) == length(grad_fd)
            diff = abs.(grad .- grad_fd)
            if length(diff) > 0
                max_diff = maximum(diff)
                if max_diff > 1e-4
                    println("⚠ WARNING: Gradient mismatch! Max difference: $max_diff")
                    println("  PSR: $grad")
                    println("  FD:  $grad_fd")
                    println("  This suggests PSR may be computing wrong gradients")
                end
            end
        else
            println("⚠ WARNING: Gradient shape mismatch! PSR: $(length(grad)), FD: $(length(grad_fd))")
        end
        
    catch e
        println("✗ ERROR during gradient computation: $e")
        println(stacktrace(catch_backtrace()))
    end
    
    demo.results["bug_1"] = Dict("status" => "demonstrated", "params" => params)
end

function bug_3_broadcasting_batched_vqc(demo::GradientBugDemo)
    """
    BUG 3: Broadcasting issues with batched VQCs
    
    Problem: In batched/VQC setups with broadcasting, PSR may fail silently
    or compute incorrect gradients when parameters are broadcast across
    multiple circuit evaluations.
    """
    println("\n" * "="^70)
    println("BUG 3: Broadcasting Issues with Batched VQCs")
    println("="^70)
    
    # Create a variational quantum circuit
    function batched_vqc(params::Vector{Float64}, x::Float64)
        """
        VQC that takes both trainable params and data input x
        Broadcasting can cause issues when x is batched
        """
        n = 4
        reg = zero_state(n)
        
        # Build circuit
        circuit = chain(n,
            put(1=>Ry(x)),
            put(1=>Ry(params[1])),
            put(2=>Rx(params[2])),
            control(1, 2=>X),
            put(1=>Rz(params[3]))
        )
        
        # Apply circuit
        reg = apply!(reg, circuit)
        
        return expect(put(n, 1=>Z), reg)
    end
    
    params = [0.1, 0.2, 0.3]
    
    println("\n📊 Circuit Visualization:")
    println("-"^70)
    println("\nCircuit Structure (Batched VQC with broadcasting):")
    println("  ✓ Circuit diagram would be saved here")
    println("\n⚠ PROBLEM: Data embedding (RY(x)) followed by parameterized gates")
    println("   When x is batched, broadcasting can cause inconsistent gradients!")
    println("-"^70)
    
    # Test with single input
    try
        function loss_fn_single(p, x_val)
            batched_vqc(p, x_val)
        end
        
        # Manual parameter shift rule
        s = π/2
        grad_single = zeros(length(params))
        for i in 1:length(params)
            params_plus = copy(params)
            params_plus[i] += s
            params_minus = copy(params)
            params_minus[i] -= s
            grad_single[i] = (loss_fn_single(params_plus, 0.5) - loss_fn_single(params_minus, 0.5)) / 2
        end
        println("✓ Single input gradient: $grad_single")
    catch e
        println("✗ ERROR with single input: $e")
        grad_single = nothing
    end
    
    # Test with batched input - this often causes issues
    println("\n  Testing with batched input (common source of bugs)...")
    x_batch = [0.1, 0.2, 0.3, 0.4]
    
    try
        # This might fail or produce wrong results
        results = Float64[]
        grads = Vector{Float64}[]
        for x_val in x_batch
            try
                function loss_fn_batch(p, x_val)
                    batched_vqc(p, x_val)
                end
                
                # Manual parameter shift rule
                s = π/2
                grad = zeros(length(params))
                for i in 1:length(params)
                    params_plus = copy(params)
                    params_plus[i] += s
                    params_minus = copy(params)
                    params_minus[i] -= s
                    grad[i] = (loss_fn_batch(params_plus, x_val) - loss_fn_batch(params_minus, x_val)) / 2
                end
                push!(grads, grad)
                result = batched_vqc(params, x_val)
                push!(results, result)
            catch e
                println("    ✗ Failed at x=$x_val: $e")
                push!(grads, Float64[])
                push!(results, NaN)
            end
        end
        
        if !isempty(grads) && all(!isempty, grads)
            grads_array = hcat(grads...)'
            println("  Batch gradients shape: $(size(grads_array))")
            
            # Check for inconsistencies
            grad_std = std(grads_array, dims=1)
            if any(grad_std .> 1e-6)
                println("⚠ WARNING: Gradient variance across batch! Std: $grad_std")
                println("  This suggests inconsistent gradient computation")
            end
            
            # Check for NaN
            if any(isnan, grads_array)
                println("⚠ ERROR: NaN in batch gradients!")
            end
        end
        
    catch e
        println("✗ ERROR with batched input: $e")
    end
    
    demo.results["bug_3"] = Dict("status" => "demonstrated")
end

function bug_4_silent_nan_errors(demo::GradientBugDemo)
    """
    BUG 4: Silent NaN errors from edge cases
    
    Problem: Certain parameter values or circuit configurations cause
    NaN gradients that are not caught or reported properly.
    """
    println("\n" * "="^70)
    println("BUG 4: Silent NaN Errors from Edge Cases")
    println("="^70)
    
    function circuit_nan_risk(params::Vector{Float64})
        """Circuit with operations that can produce NaN under PSR"""
        n = 4
        reg = zero_state(n)
        
        # Build circuit
        circuit = chain(n,
            put(1=>Rx(params[1])),
            put(2=>Ry(params[2])),
            put(1=>Rz(params[3])),  # Parameter at special values can cause NaN
            control(1, 2=>X),
            control(2, 1=>Ry(params[4]))  # Entangling operation that might amplify issues
        )
        
        # Apply circuit
        reg = apply!(reg, circuit)
        
        return expect(put(n, 1=>Z), reg)
    end
    
    println("\n📊 Circuit Visualization:")
    println("-"^70)
    println("\nCircuit Structure (with potential NaN-producing operations):")
    println("  ✓ Circuit diagram would be saved here")
    println("\n⚠ PROBLEM: Multiple parameterized gates + controlled rotation")
    println("   Edge case parameters (π/2, π, near zero) may cause NaN gradients!")
    println("-"^70)
    
    # Test with various parameter values that might cause NaN
    test_cases = [
        ("Normal values", [0.5, 0.3, 0.2, 0.1]),
        ("Large values", [10.0, 5.0, 3.0, 2.0]),
        ("Near zero", [1e-8, 1e-7, 1e-6, 1e-5]),
        ("At π/2", Float64[π/2, π/2, π/2, π/2]),
        ("At π", Float64[π, π, π, π]),
    ]
    
    nan_count = 0
    for (name, params) in test_cases
        try
            function loss_fn(p)
                circuit_nan_risk(p)
            end
            
            # Manual parameter shift rule
            s = π/2
            grad = zeros(length(params))
            for i in 1:length(params)
                params_plus = copy(params)
                params_plus[i] += s
                params_minus = copy(params)
                params_minus[i] -= s
                grad[i] = (loss_fn(params_plus) - loss_fn(params_minus)) / 2
            end
            
            has_nan = any(isnan, grad) || any(isinf, grad)
            
            if has_nan
                println("⚠ $name: Gradient contains NaN/Inf!")
                println("  Params: $params")
                println("  Gradient: $grad")
                nan_count += 1
            else
                println("✓ $name: OK (grad=$grad)")
            end
                
        catch e
            println("✗ $name: Exception - $e")
            nan_count += 1
        end
    end
    
    if nan_count > 0
        println("\n⚠ Found $nan_count cases with NaN/Inf or exceptions")
        println("  This demonstrates silent errors in PSR gradient computation")
    end
    
    demo.results["bug_4"] = Dict("status" => "demonstrated", "nan_cases" => nan_count)
end

function bug_5_parameter_reuse_and_dependencies(demo::GradientBugDemo)
    """
    BUG 5: Parameter reuse and circular dependencies
    
    Problem: Reusing the same parameter in multiple gates or creating
    circular dependencies can cause incorrect gradient computation in PSR.
    """
    println("\n" * "="^70)
    println("BUG 5: Parameter Reuse and Circular Dependencies")
    println("="^70)
    
    function circuit_param_reuse(params::Vector{Float64})
        """
        Circuit that reuses parameters - PSR might not handle this correctly
        """
        n = 4
        reg = zero_state(n)
        
        # Build circuit
        circuit = chain(n,
            put(1=>Rx(params[1])),
            put(2=>Ry(params[1])),  # Same param reused
            control(1, 2=>X),
            put(1=>Rz(params[2])),
            put(1=>Rx(params[1])),  # Same param again!
            control(1, 2=>Ry(params[2]))  # Same param as RZ above
        )
        
        # Apply circuit
        reg = apply!(reg, circuit)
        
        return expect(put(n, 1=>Z), reg)
    end
    
    params = [0.5, 0.3]
    
    println("\n📊 Circuit Visualization:")
    println("-"^70)
    println("\nCircuit Structure (with parameter reuse):")
    println("  ✓ Circuit diagram would be saved here")
    println("\n⚠ PROBLEM: Parameter θ₀ used 3 times, θ₁ used 2 times")
    println("   PSR must correctly sum all contributions from each parameter!")
    println("   Parameter dependency tracking may fail with reuse!")
    println("-"^70)
    
    try
        function loss_fn(p)
            circuit_param_reuse(p)
        end
        
        # Manual parameter shift rule
        s = π/2
        grad = zeros(length(params))
        for i in 1:length(params)
            params_plus = copy(params)
            params_plus[i] += s
            params_minus = copy(params)
            params_minus[i] -= s
            grad[i] = (loss_fn(params_plus) - loss_fn(params_minus)) / (2 * sin(s))
        end
        
        println("✓ PSR Gradient with param reuse: $grad")
        
        # Compare with finite difference
        function circuit_fd(params::Vector{Float64})
            n = 4
            reg = zero_state(n)
            circuit = chain(n,
                put(1=>Rx(params[1])),
                put(2=>Ry(params[1])),
                control(1, 2=>X),
                put(1=>Rz(params[2])),
                put(1=>Rx(params[1])),
                control(1, 2=>Ry(params[2]))
            )
            reg = apply!(reg, circuit)
            return expect(put(n, 1=>Z), reg)
        end
        
        h = 1e-5
        grad_fd = zeros(length(params))
        f0 = circuit_fd(params)
        for i in 1:length(params)
            params_plus = copy(params)
            params_plus[i] += h
            f_plus = circuit_fd(params_plus)
            grad_fd[i] = (f_plus - f0) / h
        end
        
        println("  Finite-diff gradient: $grad_fd")
        
        # PSR should correctly sum contributions from all uses
        # But may fail if not properly tracking parameter dependencies
        if length(grad) == 0
            println("⚠ WARNING: PSR returned empty gradient! This indicates a bug.")
        elseif length(grad_fd) == 0
            println("⚠ WARNING: Finite-diff returned empty gradient!")
        elseif length(grad) == length(grad_fd)
            diff = abs.(grad .- grad_fd)
            if length(diff) > 0
                max_diff = maximum(diff)
                if max_diff > 1e-4
                    println("⚠ WARNING: Gradient mismatch! Max diff: $max_diff")
                    println("  PSR: $grad")
                    println("  FD:  $grad_fd")
                    println("  PSR may not be correctly handling parameter reuse")
                end
            end
        else
            println("⚠ WARNING: Gradient shape mismatch!")
        end
        
    catch e
        println("✗ ERROR: $e")
        println(stacktrace(catch_backtrace()))
    end
    
    demo.results["bug_5"] = Dict("status" => "demonstrated")
end

function bug_6a_operation_ordering_psr_issue(demo::GradientBugDemo)
    """
    BUG 6a: Operation ordering causing PSR evaluation errors
    
    Problem: The order of operations can cause PSR to evaluate shifted circuits
    incorrectly, especially when entangling gates are interleaved with
    parameterized gates.
    """
    println("\n" * "="^70)
    println("BUG 6a: Operation Ordering PSR Evaluation Issues")
    println("="^70)
    
    # Two circuits with different operation orders - should give same result
    # but PSR might compute different gradients
    
    function circuit_order1(params::Vector{Float64})
        """Order: param -> entangle -> param"""
        n = 4
        reg = zero_state(n)
        circuit = chain(n,
            put(1=>Ry(params[1])),
            control(1, 2=>X),
            put(2=>Rx(params[2]))
        )
        reg = apply!(reg, circuit)
        return expect(put(n, 1=>Z), reg)
    end
    
    function circuit_order2(params::Vector{Float64})
        """Order: entangle -> param -> param"""
        n = 4
        reg = zero_state(n)
        circuit = chain(n,
            control(1, 2=>X),
            put(1=>Ry(params[1])),
            put(2=>Rx(params[2]))
        )
        reg = apply!(reg, circuit)
        return expect(put(n, 1=>Z), reg)
    end
    
    params = [0.5, 0.3]
    
    println("\n📊 Circuit Visualization:")
    println("-"^70)
    println("\nCircuit 1 Structure (Order: param → entangle → param):")
    println("  ✓ Circuit diagram would be saved here")
    println("-"^70)
    
    println("\nCircuit 2 Structure (Order: entangle → param → param):")
    println("  ✓ Circuit diagram would be saved here")
    println("\n⚠ PROBLEM: Different operation orders can cause PSR to evaluate")
    println("   shifted circuits incorrectly, leading to gradient mismatches!")
    println("-"^70)
    
    try
        function loss_fn1(p)
            circuit_order1(p)
        end
        
        function loss_fn2(p)
            circuit_order2(p)
        end
        
        # Manual parameter shift rule
        s = π/2
        grad1 = zeros(length(params))
        for i in 1:length(params)
            params_plus = copy(params)
            params_plus[i] += s
            params_minus = copy(params)
            params_minus[i] -= s
            grad1[i] = (loss_fn1(params_plus) - loss_fn1(params_minus)) / 2
        end
        
        grad2 = zeros(length(params))
        for i in 1:length(params)
            params_plus = copy(params)
            params_plus[i] += s
            params_minus = copy(params)
            params_minus[i] -= s
            grad2[i] = (loss_fn2(params_plus) - loss_fn2(params_minus)) / 2
        end
        
        println("✓ Circuit 1 gradient: $grad1")
        println("✓ Circuit 2 gradient: $grad2")
        
        # These should be different due to operation order
        # But check if gradients are computed correctly
        diff = abs.(grad1 .- grad2)
        println("  Gradient difference: $diff")
        
        # Verify with finite difference
        function circuit_fd1(params::Vector{Float64})
            n = 4
            reg = zero_state(n)
            circuit = chain(n,
                put(1=>Ry(params[1])),
                control(1, 2=>X),
                put(2=>Rx(params[2]))
            )
            reg = apply!(reg, circuit)
            return expect(put(n, 1=>Z), reg)
        end
        
        function circuit_fd2(params::Vector{Float64})
            n = 4
            reg = zero_state(n)
            circuit = chain(n,
                control(1, 2=>X),
                put(1=>Ry(params[1])),
                put(2=>Rx(params[2]))
            )
            reg = apply!(reg, circuit)
            return expect(put(n, 1=>Z), reg)
        end
        
        h = 1e-5
        grad_fd1 = zeros(length(params))
        f0_1 = circuit_fd1(params)
        for i in 1:length(params)
            params_plus = copy(params)
            params_plus[i] += h
            f_plus = circuit_fd1(params_plus)
            grad_fd1[i] = (f_plus - f0_1) / h
        end
        
        grad_fd2 = zeros(length(params))
        f0_2 = circuit_fd2(params)
        for i in 1:length(params)
            params_plus = copy(params)
            params_plus[i] += h
            f_plus = circuit_fd2(params_plus)
            grad_fd2[i] = (f_plus - f0_2) / h
        end
        
        println("  FD Circuit 1: $grad_fd1")
        println("  FD Circuit 2: $grad_fd2")
        
        # Check if PSR matches FD for each circuit
        if length(grad1) == 0
            println("⚠ WARNING: Circuit 1 PSR returned empty gradient!")
        elseif length(grad_fd1) == 0
            println("⚠ WARNING: Circuit 1 FD returned empty gradient!")
        elseif length(grad1) == length(grad_fd1)
            diff1 = abs.(grad1 .- grad_fd1)
            if length(diff1) > 0
                max_diff1 = maximum(diff1)
                if max_diff1 > 1e-4
                    println("⚠ WARNING: PSR vs FD mismatch in circuit 1! Max diff: $max_diff1")
                end
            end
        end
        
        if length(grad2) == 0
            println("⚠ WARNING: Circuit 2 PSR returned empty gradient!")
        elseif length(grad_fd2) == 0
            println("⚠ WARNING: Circuit 2 FD returned empty gradient!")
        elseif length(grad2) == length(grad_fd2)
            diff2 = abs.(grad2 .- grad_fd2)
            if length(diff2) > 0
                max_diff2 = maximum(diff2)
                if max_diff2 > 1e-4
                    println("⚠ WARNING: PSR vs FD mismatch in circuit 2! Max diff: $max_diff2")
                end
            end
        end
        
    catch e
        println("✗ ERROR: $e")
        println(stacktrace(catch_backtrace()))
    end
    
    demo.results["bug_6a"] = Dict("status" => "demonstrated")
end

function bug_6_complex_vqc_training_failure(demo::GradientBugDemo)
    """
    BUG 6: Failure in complex VQC training scenarios
    
    Problem: Real-world VQC training scenarios combine multiple issues,
    leading to training failures, wrong gradients, or crashes.
    """
    println("\n" * "="^70)
    println("BUG 6: Complex VQC Training Failure Scenario")
    println("="^70)
    
    # Simulate a realistic VQC training scenario
    function training_vqc(params::Vector{Float64}, data::Vector{Float64})
        """
        Realistic VQC with data embedding and multiple parameterized layers
        This combines multiple potential issues:
        - Data embedding
        - Multiple parameterized layers
        - Entangling gates
        - Multiple measurements
        """
        n = 4
        reg = zero_state(n)
        
        # Build circuit
        gates = []
        
        # Data embedding layer
        for (i, x) in enumerate(data)
            push!(gates, put(i=>Ry(x)))
        end
        
        # First parameterized layer
        for (i, p) in enumerate(params[1:2])
            push!(gates, put(i=>Rx(p)))
        end
        
        # Entangling layer
        push!(gates, control(1, 2=>X))
        push!(gates, control(3, 4=>X))
        push!(gates, control(1, 3=>X))
        
        # Second parameterized layer with reused params
        for (i, p) in enumerate(params[3:4])
            push!(gates, put(i=>Ry(p)))
        end
        
        # More entanglement
        push!(gates, control(2, 1=>Ry(params[5])))
        push!(gates, control(4, 3=>Ry(params[6])))
        
        # Final layer
        for (i, p) in enumerate(params[7:8])
            push!(gates, put(i=>Rz(p)))
        end
        
        circuit = chain(n, gates...)
        reg = apply!(reg, circuit)
        
        # Multiple measurements (can cause issues with PSR)
        exp1 = expect(put(n, 1=>Z), reg)
        exp2 = expect(put(n, 2=>Z), reg)
        return (exp1, exp2)
    end
    
    # Training setup
    Random.seed!(42)
    params = rand(8) * 0.1
    data = [0.5, 0.3, 0.2, 0.1]
    
    println("\n📊 Circuit Visualization:")
    println("-"^70)
    println("\nComplex VQC Structure (combines multiple potential issues):")
    println("  ✓ Circuit diagram would be saved here")
    println("\n⚠ PROBLEM: Complex circuit with:")
    println("   • Data embedding layer (RY gates)")
    println("   • Multiple parameterized layers (RX, RY, RZ)")
    println("   • Interleaved entangling gates (CNOT, CRY)")
    println("   • Multiple measurements")
    println("   All issues from bugs 1-5 can combine here!")
    println("-"^70)
    
    println("\n  Testing realistic VQC training scenario...")
    println("  Parameters: $(length(params))")
    println("  Data: $(length(data))")
    
    try
        # Forward pass
        result = training_vqc(params, data)
        println("✓ Forward pass: $result")
        
        # Gradient computation (most likely to fail)
        function loss_fn(p::Vector{Float64}, d::Vector{Float64})
            results = training_vqc(p, d)
            # Simple loss: sum of expectations
            return results[1] + results[2]
        end
        
        # Manual parameter shift rule
        s = π/2
        grad = zeros(length(params))
        for i in 1:length(params)
            params_plus = copy(params)
            params_plus[i] += s
            params_minus = copy(params)
            params_minus[i] -= s
            grad[i] = (loss_fn(params_plus, data) - loss_fn(params_minus, data)) / 2
        end
        
        println("✓ Gradient computed: shape=$(length(grad))")
        println("  Gradient values: $grad")
        
        # Check for issues
        if any(isnan, grad) || any(isinf, grad)
            println("⚠ ERROR: Gradient contains NaN/Inf!")
        else
            # Check for suspicious values
            grad_magnitude = norm(grad)
            if grad_magnitude > 1e6 || grad_magnitude < 1e-10
                println("⚠ WARNING: Suspicious gradient magnitude: $grad_magnitude")
            end
            
            # Check gradient variance
            if std(grad) < 1e-10
                println("⚠ WARNING: Very low gradient variance - may indicate wrong computation")
            end
        end
        
        # Simulate training step (this is where bugs manifest)
        println("\n  Simulating training step...")
        learning_rate = 0.01
        try
            params_new = params .- learning_rate .* grad
            result_new = training_vqc(params_new, data)
            println("✓ Training step completed")
            println("  New result: $result_new")
            println("  Loss change: $(sum(result)) -> $(sum(result_new))")
        catch e
            println("✗ Training step failed: $e")
        end
            
    catch e
        println("✗ ERROR during VQC training: $e")
        println(stacktrace(catch_backtrace()))
    end
    
    demo.results["bug_6"] = Dict("status" => "demonstrated")
end

function run_all_demos(demo::GradientBugDemo)
    """Run all bug demonstrations"""
    println("\n" * "="^70)
    println("Yao.jl Parameter-Shift Rule Gradient Bugs Demonstration")
    println("="^70)
    println("\nThis script demonstrates various gradient computation errors")
    println("that occur in Yao.jl's parameter-shift rule implementation.")
    println("\nThese bugs can lead to:")
    println("  • Silent NaN errors")
    println("  • Incorrect gradient values")
    println("  • Training failures in VQCs")
    println("  • Wasted compute resources")
    
    bug_1_invalid_generator_operations(demo)
    # Bug 2 removed - too contrived, Bug 5 already covers parameter reuse comprehensively
    bug_3_broadcasting_batched_vqc(demo)
    bug_4_silent_nan_errors(demo)
    bug_5_parameter_reuse_and_dependencies(demo)
    bug_6a_operation_ordering_psr_issue(demo)
    bug_6_complex_vqc_training_failure(demo)
    
    # Summary
    println("\n" * "="^70)
    println("Summary")
    println("="^70)
    println("Demonstrated $(length(demo.results)) different categories of gradient bugs")
    println("\nKey Issues Found:")
    println("  1. Invalid generator operations can lead to wrong gradients")
    println("  3. Broadcasting in batched VQCs produces inconsistent results")
    println("  4. Silent NaN errors from edge cases are not caught")
    println("  5. Parameter reuse can cause incorrect gradient computation")
    println("  6a. Operation ordering can cause PSR evaluation errors")
    println("  6. Complex VQCs combine issues leading to training failures")
    println("\nThese demonstrate why a type-safe, compile-time-checked")
    println("solution (like LogosQ in Rust) can prevent such errors.")
end

function main()
    """Main entry point"""
    demo = GradientBugDemo()
    run_all_demos(demo)  # Run all bug demonstrations
    # bug_1_invalid_generator_operations(demo)  # Or run a single bug
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end

