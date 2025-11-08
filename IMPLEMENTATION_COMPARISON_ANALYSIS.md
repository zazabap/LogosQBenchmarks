# Bug Implementation Comparison Analysis

## Summary of Issues Found

After comparing the bug implementations across all four libraries (PennyLane, Qiskit, LogosQ, Yao.jl), several issues were identified that affect comparability:

---

## Issue 1: Bug Numbering Mismatch in LogosQ

**Problem**: LogosQ's test numbering doesn't match the other libraries.

- **PennyLane/Qiskit/Yao.jl**: `bug_1` = Invalid Generator Operations
- **LogosQ**: `test_1` = Parameter Reuse (which is `bug_5` in others!)

**Impact**: LogosQ is missing a test for "Invalid Generator Operations" (Bug 1), making it impossible to compare this specific bug across all libraries.

**Recommendation**: Add a `test_1_invalid_generator_operations` function to LogosQ that matches the circuit structure from other libraries.

---

## Issue 2: Yao.jl Bug 1 - Parameter Indexing (NOT AN ISSUE)

**Status**: ✅ **CORRECT** - This is not actually a problem.

**Explanation**: Julia uses 1-based indexing, so `params[1]` in Julia is equivalent to `params[0]` in Python.

**Yao.jl Bug 1** (line 55-58):
```julia
put(1=>Rx(params[1])),  # params[1] = 0.5 (first element in Julia)
control(1, 2=>X),
put(2=>Ry(params[2])),  # params[2] = π/2 (second element)
control(1, 2=>Ry(params[3]))  # params[3] = 0.3 (third element)
```

**PennyLane/Qiskit Bug 1**:
```python
RX(params[0], 0)  # params[0] = 0.5 (first element in Python)
CNOT(0, 1)
RY(params[1], 1)  # params[1] = π/2 (second element)
CRY(params[2], 0, 1)  # params[2] = 0.3 (third element)
```

**Analysis**: Both use the same parameter values `[0.5, π/2, 0.3]`, just with language-appropriate indexing. The circuits are **equivalent**.

---

## Issue 3: Parameter Reuse Test - Circuit Differences

**PennyLane/Qiskit Bug 5**:
```python
RX(params[0], 0)
RY(params[0], 1)  # Reuse params[0]
CNOT(0, 1)
RZ(params[1], 0)
RX(params[0], 0)  # Reuse params[0] again
CRY(params[1], 0, 1)  # Reuse params[1]
```

**LogosQ test_1**:
```rust
rx(0, params[0])
ry(1, params[0])  # Reuse params[0] ✓
cnot(0, 1)
rz(0, params[1])
rx(0, params[0])  # Reuse params[0] again ✓
cry(0, 1, params[1])  # Reuse params[1] ✓
```

**Analysis**: These are actually EQUIVALENT! The CRY gate signature is just different:
- PennyLane/Qiskit: `CRY(angle, control, target)` or `CRY(angle, wires=[control, target])`
- LogosQ: `cry(control, target, angle)` - angle is last parameter

So `CRY(params[1], 0, 1)` in Python = `cry(0, 1, params[1])` in Rust. ✓ CORRECT

---

## Issue 4: Bug 2 (State Reuse) - Observable Differences

**PennyLane Bug 2**:
```python
return qml.expval(qml.PauliZ(0) @ qml.PauliZ(1))  # ZZ observable
```

**Qiskit Bug 2**:
```python
zz_observable = SparsePauliOp(['ZZII'], coeffs=[1.0])  # ZZ observable
```

**Yao.jl Bug 2**:
```julia
exp1 = expect(put(n, 1=>Z), reg)
exp2 = expect(put(n, 2=>Z), reg)
return exp1 * exp2  # Product of Z expectations
```

**LogosQ test_2**:
```rust
obs.add_term(PauliTerm::new(1.0, vec![Pauli::Z, Pauli::Z]));  # ZZ observable
```

**Problem**: 
- PennyLane/Qiskit/LogosQ: Use proper ZZ correlation observable
- Yao.jl: Uses product of individual Z expectations: `E[Z₁] * E[Z₂]` instead of `E[Z₁ ⊗ Z₂]`

**Impact**: These are NOT equivalent! 
- `E[Z₁ ⊗ Z₂]` measures correlation between qubits
- `E[Z₁] * E[Z₂]` is the product of individual expectations (different!)

**Recommendation**: Fix Yao.jl Bug 2 to use proper ZZ observable: `expect(put(n, (1,2)=>(Z,Z)), reg)` or equivalent.

---

## Issue 5: Missing Tests in LogosQ

**Missing in LogosQ**:
- ❌ Bug 1: Invalid Generator Operations (test_1 is actually Parameter Reuse)
- ❌ Bug 3: Broadcasting Issues with Batched VQCs

**Present in LogosQ but different numbering**:
- test_1 = Parameter Reuse (Bug 5 in others)
- test_2 = Entangled State Handling (Bug 2 in others)
- test_3 = Complex VQC Layers (similar to Bug 6)
- test_4 = Silent NaN Errors (Bug 4 in others)
- test_5 = Operation Ordering (Bug 6a in others)
- test_6 = Multiple Measurements (similar to Bug 6)

**Recommendation**: 
1. Add Bug 1 test (Invalid Generator Operations)
2. Add Bug 3 test (Broadcasting Issues)
3. Renumber tests to match other libraries for consistency

---

## Issue 6: Yao.jl Manual PSR Implementation

**Problem**: Yao.jl uses manual PSR implementation instead of built-in gradient methods.

**Impact**: 
- Not testing Yao.jl's actual gradient capabilities
- Manual implementation may have bugs that aren't in the library
- Makes comparison less fair

**Note**: This was a design choice for direct PSR comparison, but it means we're not testing Yao.jl's built-in `autodiff(:BP)` or `expect'` methods.

---

## Issue 7: Circuit Structure Differences

### Bug 1 Comparison:

**PennyLane/Qiskit**: 
- RX(θ₀, 0) → CNOT(0,1) → RY(θ₁, 1) → CRY(θ₂, 0,1)
- 2 qubits, 3 parameters

**Yao.jl**: 
- Rx(θ₁, 1) → CNOT(1,2) → Ry(θ₂, 2) → CRY(1,2, θ₃)
- 4 qubits (but only uses qubits 1,2), 3 parameters
- Uses qubits 1,2 instead of 0,1 (Julia 1-based indexing)

**Analysis**: The circuit logic is equivalent, just different qubit numbering. This is acceptable.

---

## Recommendations for Fixes

### High Priority:
1. **Fix Yao.jl Bug 2**: Use proper ZZ observable instead of product of expectations
2. **Add LogosQ Bug 1 test**: Invalid Generator Operations
3. **Add LogosQ Bug 3 test**: Broadcasting Issues

### Medium Priority:
4. **Renumber LogosQ tests**: Match numbering with other libraries
5. **Document Yao.jl choice**: Clarify why manual PSR is used instead of built-in methods

### Low Priority:
6. **Standardize qubit numbering**: Consider using 0-based everywhere for consistency (or document 1-based for Julia)

---

## Overall Assessment

**Comparability**: ⚠️ **PARTIALLY COMPARABLE**

**Issues**:
- LogosQ missing Bug 1 and Bug 3 tests
- Yao.jl Bug 2 uses incorrect observable
- Different test numbering makes cross-reference difficult
- Yao.jl uses manual PSR (by design, but limits comparison)

**Strengths**:
- Bug 5 (Parameter Reuse) is well-matched across all libraries
- Bug 4 (NaN Errors) structure is similar
- Bug 6a (Operation Ordering) is comparable
- Overall circuit structures are logically equivalent (accounting for language differences)

**Conclusion**: The implementations are **mostly appropriate** but have **significant gaps** that prevent full comparison. The main issues are missing tests in LogosQ and the incorrect observable in Yao.jl Bug 2.

