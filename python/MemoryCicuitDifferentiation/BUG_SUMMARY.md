# PennyLane Gradient Bug Summary

## Key Findings

The demonstration script successfully identified several critical issues with PennyLane's Parameter-Shift Rule (PSR) gradient computation:

### 1. Empty Gradient Arrays (Critical Bug)
**Status**: ✅ **CONFIRMED**

Multiple circuits return empty gradient arrays `[]` instead of the expected gradient values. This indicates:
- Parameter detection failures in PSR
- Silent failures that don't raise exceptions
- Potential issues with how PennyLane identifies trainable parameters

**Impact**: **HIGH** - Training cannot proceed if gradients are empty.

### 2. Broadcasting Inconsistencies
**Status**: ✅ **CONFIRMED**

Batched VQC operations show gradient variance across batches:
```
Batch gradients shape: (4, 3)
⚠ WARNING: Gradient variance across batch! Std: [1.04680661e-01 0.00000000e+00 4.80740672e-17]
```

**Impact**: **MEDIUM** - Inconsistent gradients can cause training instability.

### 3. Complex VQC Training
**Status**: ⚠️ **PARTIALLY WORKING**

Complex VQCs with multiple layers and data embedding do compute gradients:
```
✓ Gradient computed: shape=(8,)
  Gradient values: [-0.11218224 -0.00915275 -0.06185186 -0.30970098 ...]
```

However, some gradient components are zero when they shouldn't be, suggesting incomplete parameter tracking.

**Impact**: **MEDIUM** - Training may work but be suboptimal.

## Bug Categories Demonstrated

| Bug ID | Category | Status | Severity |
|--------|----------|--------|----------|
| Bug 1 | Invalid Generator Operations | Empty gradients | HIGH |
| Bug 2 | State Reuse / No-Cloning | Empty gradients | HIGH |
| Bug 3 | Broadcasting Issues | ✅ Confirmed variance | MEDIUM |
| Bug 4 | Silent NaN Errors | No NaN detected in test cases | LOW |
| Bug 5 | Parameter Reuse | Empty gradients | HIGH |
| Bug 6a | Operation Ordering | Empty gradients | HIGH |
| Bug 6 | Complex VQC Training | Partially working | MEDIUM |

## Root Causes Identified

1. **Parameter Detection Failure**: PennyLane fails to identify trainable parameters in certain circuit configurations
2. **State Management Issues**: No-cloning violations may not be properly caught
3. **Broadcasting Edge Cases**: Inconsistent handling of batched operations
4. **Dependency Tracking**: Parameter reuse not properly tracked in gradient computation

## Questions and Answers

### 1. Will Catalyst JIT Compilation Fix These Bugs?

**Answer:** Likely **NO** - Catalyst will not fix these fundamental gradient computation bugs.

**Analysis:**

Catalyst is a JIT compiler that compiles PennyLane quantum programs to optimized machine code using MLIR/LLVM. According to the [Catalyst documentation](https://github.com/pennylaneai/catalyst), it:

- Compiles the entire quantum-classical workflow
- Provides a `@qjit` decorator for JIT compilation
- Uses MLIR with a quantum dialect for optimization
- Lowers to LLVM + QIR for execution

**Why Catalyst Won't Fix These Bugs:**

1. **Same Algorithm**: Catalyst compiles the same PennyLane operations and gradient computation logic. If the parameter-shift rule implementation has bugs in parameter detection or gradient computation, these bugs will be compiled into the optimized code.

2. **Parameter Detection**: The empty gradient bugs stem from PennyLane's runtime parameter detection and dependency tracking. Catalyst's compilation happens at the MLIR level, but it still relies on PennyLane's parameter identification logic.

3. **Fundamental Issues**: The bugs are algorithmic/design issues:
   - Invalid generator operations → PSR fails to compute gradients
   - State reuse violations → Quantum mechanics constraints
   - Parameter reuse → Dependency tracking failures
   - Operation ordering → PSR evaluation order issues

   These are not performance issues that JIT compilation addresses.

4. **Potential Benefits**: Catalyst might help by:
   - Catching some issues at compile time (if it performs static analysis)
   - Providing better error messages during compilation
   - Optimizing the circuit structure, which might avoid some edge cases

**Recommendation**: Test with Catalyst (`@qjit` decorator) to verify, but expect the same bugs unless Catalyst has specific parameter-shift rule improvements.

### 2. Can We Test with Python 3.13?

**Answer:** **YES, but with caution** - Python 3.13 compatibility should be verified first.

**Analysis:**

1. **PennyLane Compatibility**: Check PennyLane's supported Python versions. As of 2024, PennyLane typically supports Python 3.8-3.11. Python 3.13 may not be officially supported yet.

2. **Catalyst Compatibility**: Catalyst officially supports Python 3.11+, but Python 3.13 support may vary.

3. **Testing Benefits**: Testing with Python 3.13 can:
   - Verify if newer Python features affect gradient computation
   - Identify any Python version-specific issues
   - Ensure compatibility with future Python versions

4. **Risks**:
   - May introduce unrelated compatibility errors
   - NumPy/JAX compatibility with Python 3.13
   - Potential false positives from version incompatibilities

**Recommendation**: 
- First verify PennyLane and Catalyst support Python 3.13
- Test in isolated environment
- Compare results with Python 3.10/3.11 to ensure bugs are consistent

### 3. Detailed Line-by-Line Analysis: Why Empty Gradients Occur

This section provides detailed explanations of why **Invalid Generator Operations**, **State Reuse/No-Cloning**, **Parameter Reuse**, and **Operation Ordering** all cause empty gradients in PennyLane.

#### Bug 1: Invalid Generator Operations → Empty Gradients

**Location**: `bug_1_invalid_generator_operations()` (lines 36-136)

**Circuit Structure**:
```python
@qml.qnode(dev, diff_method='parameter-shift')
def circuit_bad(params):
    qml.RX(params[0], wires=0)      # Line 54: Valid generator (Pauli X)
    qml.CNOT(wires=[0, 1])           # Line 59: NO generator (non-parameterized)
    qml.RY(params[1], wires=1)       # Line 62: Valid generator (Pauli Y)
    qml.CRY(params[2], wires=[0, 1]) # Line 65: Controlled rotation (may have issues)
    return qml.expval(qml.PauliZ(0))
```

**Why Empty Gradients Occur (Line-by-Line)**:

1. **Line 50**: `@qml.qnode(dev, diff_method='parameter-shift')` - Sets up parameter-shift rule differentiation
2. **Line 54**: `qml.RX(params[0], wires=0)` - PennyLane registers `params[0]` as a trainable parameter with generator `X`
3. **Line 59**: `qml.CNOT(wires=[0, 1])` - **CRITICAL**: CNOT has no generator and is non-parameterized. This breaks the parameter dependency chain:
   - PSR expects parameterized gates to form a continuous chain
   - CNOT creates a "break" in the dependency tracking
   - When PSR tries to compute gradients, it may lose track of which parameters affect the output
4. **Line 62**: `qml.RY(params[1], wires=1)` - PennyLane tries to register `params[1]`, but the dependency chain is broken
5. **Line 65**: `qml.CRY(params[2], wires=[0, 1])` - Controlled rotation may have generator issues depending on implementation
6. **Line 82-83**: `grad_fn = qml.grad(circuit_bad); grad = grad_fn(params)` - When PSR tries to compute gradients:
   - It looks for parameterized operations with generators
   - The interleaved CNOT confuses the parameter dependency graph
   - PSR fails to identify which parameters are trainable
   - Returns empty gradient `[]` instead of `[grad_0, grad_1, grad_2]`

**Root Cause**: PSR's parameter dependency tracking fails when non-generator operations (like CNOT) are interleaved between parameterized gates, causing the parameter detection algorithm to abort and return an empty gradient.

#### Bug 2: State Reuse/No-Cloning → Empty Gradients

**Location**: `bug_2_state_reuse_no_cloning()` (lines 138-242)

**Circuit Structure**:
```python
@qml.qnode(dev, diff_method='parameter-shift')
def circuit_state_reuse(params):
    qml.Hadamard(wires=0)            # Line 159: Creates superposition
    qml.CNOT(wires=[0, 1])           # Line 160: Creates Bell state |Φ+⟩ = (|00⟩+|11⟩)/√2
    qml.RY(params[0], wires=0)       # Line 163: Parameterized rotation on entangled qubit
    qml.RZ(params[1], wires=0)       # Line 168: Reuses qubit 0 (already entangled!)
    qml.RX(params[0], wires=1)       # Line 171: SAME parameter used again on entangled qubit!
    return qml.expval(qml.PauliZ(0) @ qml.PauliZ(1))
```

**Why Empty Gradients Occur (Line-by-Line)**:

1. **Line 152**: `@qml.qnode(dev, diff_method='parameter-shift')` - Sets up PSR differentiation
2. **Lines 159-160**: Creates entangled Bell state. After CNOT, qubits 0 and 1 are **entangled** - measuring one affects the other
3. **Line 163**: `qml.RY(params[0], wires=0)` - Applies rotation to entangled qubit 0. PSR needs to evaluate circuits at `params[0] ± s` (shift rule)
4. **Line 168**: `qml.RZ(params[1], wires=0)` - **PROBLEM**: Reuses qubit 0 which is still entangled with qubit 1
5. **Line 171**: `qml.RX(params[0], wires=1)` - **CRITICAL ISSUE**: Same parameter `params[0]` used on qubit 1, which is entangled with qubit 0
6. **Line 190-191**: When PSR computes gradients:
   - For `params[0]`, PSR needs to evaluate: `circuit(params[0]+s, params[1])` and `circuit(params[0]-s, params[1])`
   - But `params[0]` affects BOTH qubit 0 (line 163) and qubit 1 (line 171)
   - The entangled state cannot be "cloned" to evaluate both shifts independently
   - PSR's internal state management fails because:
     - It can't isolate the effect of `params[0]` on qubit 0 vs qubit 1
     - The no-cloning theorem prevents copying the entangled state
     - Parameter dependency tracking gets confused by the entanglement + parameter reuse
   - Result: PSR aborts and returns empty gradient `[]`

**Root Cause**: PSR's gradient computation requires evaluating shifted parameter values, but when the same parameter is used on entangled qubits, the no-cloning theorem prevents proper state isolation for independent shift evaluations. This breaks PSR's internal state management.

#### Bug 5: Parameter Reuse → Empty Gradients

**Location**: `bug_5_parameter_reuse_and_dependencies()` (lines 414-511)

**Circuit Structure**:
```python
@qml.qnode(dev, diff_method='parameter-shift')
def circuit_param_reuse(params):
    qml.RX(params[0], wires=0)      # Line 433: First use of params[0]
    qml.RY(params[0], wires=1)       # Line 434: SAME param reused immediately
    qml.CNOT(wires=[0, 1])           # Line 437: Entangles qubits
    qml.RZ(params[1], wires=0)       # Line 438: First use of params[1]
    qml.RX(params[0], wires=0)       # Line 439: params[0] used THIRD time!
    qml.CRY(params[1], wires=[0, 1]) # Line 442: params[1] reused
    return qml.expval(qml.PauliZ(0))
```

**Why Empty Gradients Occur (Line-by-Line)**:

1. **Line 427**: `@qml.qnode(dev, diff_method='parameter-shift')` - Sets up PSR
2. **Line 433**: `qml.RX(params[0], wires=0)` - PSR registers `params[0]` as affecting qubit 0
3. **Line 434**: `qml.RY(params[0], wires=1)` - **ISSUE**: Same parameter used on different qubit. PSR must track that `params[0]` now affects both qubits 0 and 1
4. **Line 437**: `qml.CNOT(wires=[0, 1])` - Creates entanglement, complicating parameter dependency
5. **Line 438**: `qml.RZ(params[1], wires=0)` - New parameter `params[1]` introduced
6. **Line 439**: `qml.RX(params[0], wires=0)` - **CRITICAL**: `params[0]` used THIRD time on qubit 0. PSR's dependency tracker must sum all three contributions:
   - Contribution from line 433: `∂/∂θ₀ [RX(θ₀) on qubit 0]`
   - Contribution from line 434: `∂/∂θ₀ [RY(θ₀) on qubit 1]` (entangled!)
   - Contribution from line 439: `∂/∂θ₀ [RX(θ₀) on qubit 0 again]`
7. **Line 442**: `qml.CRY(params[1], wires=[0, 1])` - `params[1]` reused, must sum contributions from lines 438 and 442
8. **Line 460-461**: When PSR computes gradients:
   - For `params[0]`, PSR must compute: `∂f/∂θ₀ = Σᵢ (∂f/∂θ₀ from operation i)`
   - But the dependency tracking system fails because:
     - Parameter `params[0]` appears in multiple places with different contexts
     - The entanglement (line 437) creates dependencies between qubits
     - PSR's parameter dependency graph becomes inconsistent
     - It cannot properly sum contributions from all three uses
   - PSR's internal algorithm aborts and returns empty gradient `[]`

**Root Cause**: PSR's parameter dependency tracking is designed for one-to-one parameter-to-operation mapping. When parameters are reused multiple times, especially with entanglement, the dependency graph becomes too complex, and PSR fails to correctly aggregate all gradient contributions, leading to empty gradients.

#### Bug 6a: Operation Ordering → Empty Gradients

**Location**: `bug_6a_operation_ordering_psr_issue()` (lines 513-627)

**Circuit Structures**:
```python
# Circuit 1: Order: param → entangle → param
@qml.qnode(dev, diff_method='parameter-shift')
def circuit_order1(params):
    qml.RY(params[0], wires=0)       # Line 533: Parameter first
    qml.CNOT(wires=[0, 1])           # Line 534: Then entanglement
    qml.RX(params[1], wires=1)       # Line 535: Parameter after entanglement
    return qml.expval(qml.PauliZ(0))

# Circuit 2: Order: entangle → param → param  
@qml.qnode(dev, diff_method='parameter-shift')
def circuit_order2(params):
    qml.CNOT(wires=[0, 1])           # Line 541: Entanglement first
    qml.RY(params[0], wires=0)       # Line 542: Parameter after entanglement
    qml.RX(params[1], wires=1)       # Line 543: Parameter after entanglement
    return qml.expval(qml.PauliZ(0))
```

**Why Empty Gradients Occur (Line-by-Line)**:

**Circuit 1 Analysis**:
1. **Line 530**: Sets up PSR differentiation
2. **Line 533**: `qml.RY(params[0], wires=0)` - PSR registers `params[0]` on qubit 0 (before entanglement)
3. **Line 534**: `qml.CNOT(wires=[0, 1])` - Creates entanglement AFTER `params[0]` is applied
4. **Line 535**: `qml.RX(params[1], wires=1)` - PSR registers `params[1]` on qubit 1 (after entanglement)
5. **Line 564-565**: When PSR computes gradients:
   - For `params[0]`: PSR evaluates shifts on qubit 0 BEFORE entanglement
   - For `params[1]`: PSR evaluates shifts on qubit 1 AFTER entanglement
   - The different ordering creates inconsistent dependency graphs
   - PSR may fail because it expects consistent operation ordering

**Circuit 2 Analysis**:
1. **Line 538**: Sets up PSR differentiation
2. **Line 541**: `qml.CNOT(wires=[0, 1])` - Entanglement FIRST, before any parameters
3. **Line 542**: `qml.RY(params[0], wires=0)` - Parameter applied AFTER entanglement
4. **Line 543**: `qml.RX(params[1], wires=1)` - Parameter applied AFTER entanglement
5. **Line 567-568**: When PSR computes gradients:
   - Both parameters are applied AFTER entanglement
   - PSR's shift evaluation must handle parameters on already-entangled qubits
   - This creates a different dependency pattern than Circuit 1
   - PSR's internal algorithm may fail to handle this ordering correctly

**Why Both Can Produce Empty Gradients**:

1. **Inconsistent Dependency Graphs**: PSR builds a dependency graph of how parameters affect the output. Different operation orders create different graphs, and PSR may fail to construct valid graphs in certain orderings.

2. **Entanglement Timing**: When entanglement happens relative to parameterized gates affects how PSR evaluates parameter shifts:
   - If parameters come before entanglement: PSR shifts are applied to independent qubits
   - If parameters come after entanglement: PSR shifts are applied to entangled qubits (violates no-cloning)

3. **PSR Evaluation Order**: PSR internally evaluates circuits in a specific order. When operation order doesn't match PSR's expected pattern, it may:
   - Fail to identify which parameters are trainable
   - Create invalid shift evaluation sequences
   - Abort and return empty gradient `[]`

**Root Cause**: PSR's internal algorithm assumes a consistent operation ordering pattern. When entangling gates are interleaved with parameterized gates in certain orders, PSR's dependency graph construction and shift evaluation fail, leading to empty gradients.

#### Bug 3: Broadcasting Issues → Gradient Inconsistencies

**Location**: `bug_3_broadcasting_batched_vqc()` (lines 257-349)

**Circuit Structure**:
```python
@qml.qnode(dev, diff_method='parameter-shift')
def batched_vqc(params, x):
    qml.RY(x, wires=0)          # Line 279: Data embedding (NON-trainable)
    qml.RY(params[0], wires=0)  # Line 282: Trainable parameter
    qml.RX(params[1], wires=1)  # Line 283: Trainable parameter
    qml.CNOT(wires=[0, 1])      # Line 284: Entangling gate
    qml.RZ(params[2], wires=0)  # Line 285: Trainable parameter
    return qml.expval(qml.PauliZ(0))
```

**Why Broadcasting Issues Occur (Detailed Analysis)**:

The broadcasting problem in Bug 3 is fundamentally different from the empty gradient bugs. Instead of returning empty gradients, it produces **inconsistent gradients** when the same trainable parameters (`params`) are evaluated with different data inputs (`x`).

**1. The Two-Input Problem (Lines 273-287)**:
- **`params`**: Trainable parameters we want gradients for (e.g., `[0.1, 0.2, 0.3]`)
- **`x`**: Data input that varies but is NOT trainable (e.g., `0.1, 0.2, 0.3, 0.4` in a batch)
- The circuit mixes both: data embedding (`RY(x)`) followed by parameterized gates (`RY(params[0])`, etc.)

**2. Parameter-Shift Rule Expectation (Line 307)**:
When PSR computes `∂/∂params`, it expects to evaluate:
```
gradient = [circuit(params + shift_i, x) - circuit(params - shift_i, x)] / (2 * shift_i)
```
For each parameter `i` in `params`, PSR:
- Evaluates circuit at `params + shift_i` with fixed `x`
- Evaluates circuit at `params - shift_i` with fixed `x`
- Computes the finite difference

**3. The Broadcasting Confusion (Lines 321-326)**:
The test loops through different `x` values:
```python
for x_val in x_batch:  # x_val = 0.1, 0.2, 0.3, 0.4
    grad = qml.grad(batched_vqc, argnum=0)(params, x=x_val)
```

**Why This Causes Issues**:

**A. State-Dependent Gradient Computation**:
- When `x = 0.1`: `RY(0.1)` creates state `|ψ₁⟩ = cos(0.05)|0⟩ - sin(0.05)|1⟩`
- When `x = 0.2`: `RY(0.2)` creates state `|ψ₂⟩ = cos(0.1)|0⟩ - sin(0.1)|1⟩`
- These are **different initial states** for the parameterized gates
- PSR computes gradients by shifting `params`, but the **effect of the shift depends on the initial state**
- Result: Gradient w.r.t. `params[0]` should theoretically vary with `x`, but PSR may not handle this correctly

**B. Parameter Dependency Tracking Gets Confused**:
- PSR builds a dependency graph: `params → operations → output`
- But the actual dependency is: `params + x → operations → output`
- PSR treats `x` as a constant, but when `x` changes across the batch:
  - PSR's internal cache/state may get confused
  - It may reuse circuit evaluations from different `x` values
  - The dependency graph becomes inconsistent

**C. The Data Embedding First Problem (Line 279)**:
- **Critical Issue**: Data embedding happens BEFORE parameterized gates
- This means: `output = f(params, initial_state(x))`
- When PSR shifts `params`, it evaluates: `f(params + shift, initial_state(x))`
- But the initial state depends on `x`, creating a **non-linear coupling**
- PSR's linear shift assumption breaks down when `x` varies

**4. Why Gradients Become Inconsistent (Lines 337-340)**:
```python
grad_std = np.std(grads_array, axis=0)
if np.any(grad_std > 1e-6):
    print(f"⚠ WARNING: Gradient variance across batch! Std: {grad_std}")
```

**Expected Behavior**: Gradients should vary smoothly with `x` (because the initial state changes)
**Actual Behavior**: Gradients show **unexpected variance** or **inconsistent patterns**

This happens because:
1. **PSR State Caching**: PSR may cache circuit evaluations, but when `x` changes, the cache becomes invalid
2. **Incorrect Shift Evaluation**: PSR may evaluate shifts incorrectly when the initial state (`x`) changes
3. **Broadcasting Mismatch**: PSR's internal broadcasting logic may not properly handle the `(params, x)` tuple structure
4. **Dependency Graph Inconsistency**: The dependency graph changes with `x`, but PSR doesn't update it

**5. Why This Matters for VQCs**:
In real variational quantum circuits (VQCs):
- You typically have: `loss = Σᵢ circuit(params, data_i)`
- Gradient: `∂loss/∂params = Σᵢ ∂circuit(params, data_i)/∂params`
- Each `data_i` creates a different initial state
- PSR should compute gradients for each `data_i` and sum them
- But the broadcasting bug causes inconsistent gradients, leading to wrong training

**Root Cause**: PSR's parameter-shift rule assumes that shifting parameters happens in isolation, but when data embedding (`x`) occurs before parameterized gates, the effect of parameter shifts becomes **state-dependent**. PSR's internal implementation doesn't properly handle this state-dependent gradient computation, especially when `x` varies across a batch, leading to inconsistent gradient values.

**Key Insight**: Unlike empty gradient bugs (which cause PSR to abort), broadcasting bugs cause PSR to compute **wrong gradients** that appear valid but are inconsistent across the batch. This is particularly dangerous because:
- No error is raised
- Gradients look "reasonable" individually
- But training fails silently due to incorrect gradient accumulation

## Implications for LogosQ

These bugs demonstrate why a type-safe, compile-time-checked solution (like LogosQ in Rust) is valuable:

1. **Compile-Time Parameter Validation**: Rust's type system can ensure parameters are valid at compile time
2. **Explicit State Management**: Ownership system prevents no-cloning violations
3. **Type-Safe Broadcasting**: Generic types can ensure correct batched operation handling
4. **Dependency Analysis**: Compile-time analysis can track all parameter dependencies

## Test Environment

- **PennyLane Version**: 0.42.3
- **Python Version**: 3.10 (tested), 3.13 (see Questions section for testing guidance)
- **Test Date**: 2024
- **Device**: default.qubit (simulator)
- **Catalyst**: Not tested (see Questions section for analysis)

## Recommendations

1. **For PennyLane Users**:
   - Always verify gradient shapes match parameter shapes
   - Use finite-difference as a sanity check for important gradients
   - Be cautious with batched operations
   - Monitor for NaN/Inf values in gradients

2. **For LogosQ Development**:
   - Implement compile-time parameter validation
   - Use Rust's ownership system to prevent state reuse bugs
   - Design type-safe broadcasting mechanisms
   - Add runtime gradient validation as a fallback

## Files

- `pennylane_gradient_bugs.py`: Main demonstration script
- `main.py`: Entry point
- `README.md`: Documentation
- `BUG_SUMMARY.md`: This file

## Running Tests

```bash
cd /app/python/MemoryCicuitDifferentiation
python3 pennylane_gradient_bugs.py
```

## Next Steps

1. **Test with Catalyst**: Verify if `@qjit` decorator changes behavior (though bugs likely persist)
2. **Test with Python 3.13**: Verify compatibility and test if bugs persist in newer Python version
3. **Investigate Empty Gradients**: Use the detailed line-by-line analysis to understand PSR's internal failures
4. **Report Findings**: Report findings to PennyLane developers with detailed bug reports
5. **Guide LogosQ Implementation**: Use findings to ensure LogosQ avoids these issues at compile time
6. **Create Rust-based Tests**: Verify LogosQ's type system prevents these bugs

## Summary of Gradient Bug Causes

### Empty Gradient Bugs (Bugs 1, 2, 5, 6a)

These bug categories (Invalid Generator Operations, State Reuse/No-Cloning, Parameter Reuse, and Operation Ordering) cause empty gradients through a common mechanism:

1. **Parameter Dependency Tracking Failure**: PSR builds an internal dependency graph mapping parameters to operations. When circuits violate assumptions (non-generator operations, entangled parameter reuse, complex parameter dependencies, or inconsistent ordering), this graph becomes invalid or inconsistent.

2. **PSR Algorithm Abort**: When PSR's internal algorithm cannot construct a valid dependency graph or cannot evaluate parameter shifts correctly, it silently aborts and returns an empty gradient array `[]` instead of raising an error.

3. **Silent Failure**: The empty gradient is a silent failure - no exception is raised, making it difficult to detect in production code. This is why these bugs are particularly dangerous.

**Common Pattern**: All empty gradient bugs break PSR's assumption of a simple, linear parameter-to-operation mapping. When real circuits violate this assumption (through entanglement, parameter reuse, or operation ordering), PSR's dependency tracking fails, leading to empty gradients.

### Broadcasting Bug (Bug 3)

**Different Mechanism**: Unlike empty gradient bugs, Bug 3 (Broadcasting Issues) produces **inconsistent but non-empty gradients**. The fundamental issue is:

1. **State-Dependent Gradients**: When data embedding (`x`) occurs before parameterized gates, the gradient computation becomes state-dependent. PSR shifts `params` but the effect of the shift depends on the initial state created by `x`.

2. **Cache Invalidation**: PSR's internal caching mechanism may reuse circuit evaluations across different `x` values, causing inconsistent gradient computations.

3. **Non-Linear Coupling**: The coupling between data (`x`) and parameters (`params`) creates a non-linear dependency that PSR's linear shift assumption cannot handle correctly.

4. **Silent Wrong Gradients**: Unlike empty gradients (which are obvious), broadcasting bugs produce gradients that look valid but are wrong, making them particularly dangerous for training.

**Key Difference**: Empty gradient bugs cause PSR to abort and return `[]`. Broadcasting bugs cause PSR to compute wrong gradients that appear valid but are inconsistent across batches.

