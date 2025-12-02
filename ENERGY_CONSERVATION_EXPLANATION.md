# Energy Conservation in XYZ Heisenberg Model

## Why Energy Change is Close to Zero

### 1. **Energy Conservation is Expected**

Under unitary time evolution with a time-independent Hamiltonian:
- Evolution operator: U(t) = exp(-i*H*t)
- Energy expectation: <ψ(t)|H|ψ(t)> = <ψ(0)|H|ψ(0)>
- This is because [H, U] = 0, so energy is **exactly conserved** for exact evolution

**Energy change ≈ 0 is CORRECT behavior, not a bug!**

### 2. **Trotter Approximation Errors**

With first-order Trotter decomposition:
- Approximation: exp(-i*H*dt) ≈ ∏ᵢ exp(-i*Hᵢ*dt)
- Error per step: O(dt²)
- With dt=0.1, time_steps=10, total_time=1.0
- Expected error: ~10⁻⁵ to 10⁻⁶

This matches the small energy changes observed in:
- **LogosQ (Rust)**: ~7×10⁻⁵ energy change
- **Q# (.NET)**: ~3×10⁻⁶ to 8×10⁻⁶ energy change

### 3. **Why Some Frameworks Show Exact Zero**

Some frameworks show exactly 0 energy change (within machine precision):

- **PennyLane**: Uses `qml.ApproxTimeEvolution` which may use exact matrix exponentiation for small systems
- **Qiskit/Yao.jl**: Use exact statevector simulation with high numerical precision
- **Numerical rounding**: Errors smaller than ~10⁻¹⁰ round to 0 in floating-point arithmetic

### 4. **The State Still Evolves**

Even though energy is conserved, **the quantum state does evolve**:
- Initial state |1111...⟩ mixes with other basis states
- The wavefunction becomes a superposition
- This is normal quantum dynamics

Energy conservation does NOT mean the state is static!

### 5. **Verification**

For a 2-qubit system with J_x=J_y=J_z=1.0:
- Initial state: |11⟩
- Initial energy: E₀ = -J_z = -1.0
- After exact evolution: E₁ = -1.0 (exactly conserved)
- After Trotter evolution: E₁ ≈ -1.0 (small errors ~10⁻⁵)

### Conclusion

**Energy change ≈ 0 is NORMAL and EXPECTED** for unitary time evolution. The small non-zero values in some frameworks are due to Trotter approximation errors, which is the expected behavior for first-order Trotter decomposition.

## Non-Conserved Energy Case

To demonstrate **non-conserved energy**, we can use a **time-dependent Hamiltonian**. 

### Example: Time-Dependent External Field

Add a time-dependent external field: **h(t) = A × sin(ω×t)**

This makes the Hamiltonian explicitly time-dependent:
- **H(t) = H₀ - h(t) × Σᵢ Zᵢ**
- Energy is **NOT conserved** because the Hamiltonian changes over time

### Usage

Run the benchmark with time-dependent field:

```bash
# Set environment variables for time-dependent field
export XYZ_TIME_DEPENDENT=true
export XYZ_FIELD_AMPLITUDE=2.0    # Amplitude A
export XYZ_FIELD_FREQUENCY=1.0    # Frequency ω
export XYZ_QUBITS=4

# Run benchmark
python3 pennylane/XYZHeisenberg/xyz_h.py
```

### Test Script

A test script is available to demonstrate both cases:

```bash
python3 test_non_conserved_energy.py
```

This will show:
1. **Conserved energy** (time-independent): Energy change ≈ 0
2. **Non-conserved energy** (time-dependent): Energy change ≠ 0 (e.g., ~6.73 for the test parameters)

### Why Energy is Not Conserved

For a time-dependent Hamiltonian H(t):
- The evolution operator is: **U(t) = T exp(-i ∫ H(τ) dτ)** (time-ordered exponential)
- Energy expectation: **<ψ(t)|H(t)|ψ(t)> ≠ <ψ(0)|H(0)|ψ(0)>**
- The Hamiltonian itself changes, so energy is not conserved

This is physically meaningful: the time-dependent field can do work on the system, changing its energy.

