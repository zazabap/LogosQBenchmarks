# Backend Options for Quantum Computing Libraries

This document describes the available backend/simulator options for each quantum computing library in the benchmark suite.

## Current Backend Usage in Benchmarks

### LogosQ (Rust)
- **Current Backend**: Dense (default), MPS (auto-switches for qubits > 10)
- **Available Options**:
  - `dense`: Full state vector representation (2^n memory)
  - `mps`: Matrix Product State representation (efficient for low-entanglement systems)
- **Configuration**: Set via `QFT_BACKEND` environment variable
- **MPS Config**: `MPS_MAX_BOND` (default: 64), `MPS_TRUNC_EPS` (default: 1e-8)
- **Status**: ✅ MPS backend implemented and auto-switches for large qubit counts

### PennyLane (Python)
- **Current Backend**: `default.qubit` (dense state vector)
- **Available Options**:
  - `default.qubit`: Standard CPU state vector simulator (current)
  - `default.mixed`: Mixed state simulator
  - `lightning.qubit`: High-performance CPU simulator (C++ backend, faster)
  - `lightning.gpu`: GPU-accelerated simulator (requires CUDA)
- **MPS/Tensor Network**: ❌ Not available in standard PennyLane
- **Configuration**: Change device in benchmark code
- **Status**: ⚠️ Only dense backend used, lightning.qubit available but not used

### Qiskit (Python)
- **Current Backend**: `Statevector` (dense state vector)
- **Available Options**:
  - `Statevector`: Dense state vector simulator (current)
  - `AerSimulator` (requires `qiskit-aer` package) with methods:
    - `statevector`: Dense state vector (default)
    - `matrix_product_state`: MPS simulator (efficient for low-entanglement)
    - `stabilizer`: Stabilizer simulator (Clifford circuits only)
    - `extended_stabilizer`: Extended stabilizer (approximate)
    - `unitary`: Unitary matrix simulator
- **MPS Support**: ✅ Yes, via `AerSimulator(method='matrix_product_state')` (requires qiskit-aer)
- **Configuration**: Change simulator in benchmark code
- **Status**: ⚠️ Only Statevector used, MPS available but not used (requires qiskit-aer package)

### Yao.jl (Julia)
- **Current Backend**: Dense state vector (default `YaoArrayRegister`)
- **Available Options**:
  - Dense state vector: Default `YaoArrayRegister` representation (current)
  - Tensor network support: Available via `YaoToEinsum` package
  - Custom backends: Can be implemented via Yao's extensible architecture
- **MPS Support**: ❌ Not directly available as a built-in backend
- **Configuration**: Uses default dense representation
- **Status**: ⚠️ Only dense backend used

### Q# (.NET)
- **Current Backend**: `QuantumSimulator` (dense state vector)
- **Available Options**:
  - `QuantumSimulator`: Full state vector simulator (current)
  - `SparseSimulator`: Sparse state vector simulator (for sparse states)
  - `ToffoliSimulator`: Classical reversible simulator (limited gates)
- **MPS Support**: ❌ Not available in standard Q# simulators
- **Configuration**: Change simulator type in code
- **Status**: ⚠️ Only QuantumSimulator used, SparseSimulator available but not used

## Backend Comparison Table

| Library | Dense | MPS | GPU | Sparse | Stabilizer | Current |
|---------|-------|-----|-----|--------|-----------|---------|
| LogosQ | ✓ | ✓ | - | - | - | Dense/MPS (auto) |
| PennyLane | ✓ | - | ✓ (lightning.gpu) | - | - | default.qubit |
| Qiskit | ✓ | ✓ (Aer) | ✓ (Aer GPU) | - | ✓ | Statevector |
| Yao.jl | ✓ | - | - | - | - | Dense |
| Q# | ✓ | - | - | ✓ | - | QuantumSimulator |

## Summary

**MPS Backend Availability:**
- ✅ **LogosQ**: Has MPS backend (implemented, auto-switches for qubits > 10)
- ✅ **Qiskit**: Has MPS via `qiskit-aer` package (not currently used in benchmarks)
- ❌ **PennyLane**: No MPS backend
- ❌ **Yao.jl**: No built-in MPS backend
- ❌ **Q#**: No MPS backend

**Current Backend Status:**
- All libraries currently use **dense state vector** simulators
- Only **LogosQ** has MPS backend implemented and actively used (auto-switches)
- **Qiskit** has MPS capability but requires `qiskit-aer` package (not installed)
- **PennyLane** has faster `lightning.qubit` option but not used
- **Q#** has `SparseSimulator` option but not used

## Recommendations

1. **For small qubit counts (≤10)**: Dense backends are typically fastest
2. **For large qubit counts (>10)**: 
   - Use MPS backends where available (LogosQ, Qiskit with qiskit-aer)
   - LogosQ already auto-switches to MPS for qubits > 10
3. **For GPU acceleration**: 
   - PennyLane `lightning.gpu` (requires CUDA)
   - Qiskit Aer GPU (requires qiskit-aer and CUDA)
4. **For specific circuit types**: 
   - Qiskit stabilizer simulator for Clifford circuits
   - Q# ToffoliSimulator for classical reversible circuits

## Adding Backend Options to Benchmarks

To enable backend selection in benchmarks:

1. **PennyLane**: Change `qml.device("default.qubit", ...)` to `qml.device("lightning.qubit", ...)`
2. **Qiskit**: 
   - Install: `pip install qiskit-aer`
   - Use: `AerSimulator(method='matrix_product_state')` for MPS
3. **Yao.jl**: Currently limited to dense, but extensible via custom implementations
4. **Q#**: Use `SparseSimulator()` for sparse states
