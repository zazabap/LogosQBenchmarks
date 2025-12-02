# Time-Dependent Field: Non-Conserved Energy Case

## Overview

By default, the XYZ Heisenberg benchmark uses a **time-independent Hamiltonian**, which results in **energy conservation** (energy change ≈ 0). 

To demonstrate **non-conserved energy**, you can enable a **time-dependent external field**.

## How It Works

The time-dependent external field is:
```
h(t) = A × sin(ω × t)
```

Where:
- **A** = `XYZ_FIELD_AMPLITUDE` (default: 2.0)
- **ω** = `XYZ_FIELD_FREQUENCY` (default: 1.0)
- **t** = current time step

This makes the Hamiltonian explicitly time-dependent:
```
H(t) = H₀ - h(t) × Σᵢ Zᵢ
```

Since H(t) changes over time, **energy is NOT conserved**.

## Usage

### PennyLane (Python)

```bash
export XYZ_TIME_DEPENDENT=true
export XYZ_FIELD_AMPLITUDE=2.0
export XYZ_FIELD_FREQUENCY=1.0
export XYZ_QUBITS=4
export XYZ_STEPS=10
export XYZ_DT=0.1
export XYZ_OUTPUT_FILE=non_conserved_energy.json

python3 pennylane/XYZHeisenberg/xyz_h.py
```

### Test Script

Run the demonstration script:

```bash
python3 test_non_conserved_energy.py
```

This shows both:
1. **Conserved energy** case (time-independent)
2. **Non-conserved energy** case (time-dependent)

## Expected Results

### Time-Independent (Conserved)
- Initial Energy: ~-3.0 (for 4 qubits)
- Final Energy: ~-3.0
- Energy Change: ~0.0

### Time-Dependent (Non-Conserved)
- Initial Energy: ~-3.0 (for 4 qubits)
- Final Energy: ~3.7 (example with A=2.0, ω=1.0)
- Energy Change: ~6.7 (significant!)

## Parameters

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `XYZ_TIME_DEPENDENT` | Enable time-dependent field | `false` |
| `XYZ_FIELD_AMPLITUDE` | Amplitude A of sin(ωt) | `2.0` |
| `XYZ_FIELD_FREQUENCY` | Frequency ω of sin(ωt) | `1.0` |

## Physics Explanation

**Why energy is not conserved:**

1. **Time-dependent Hamiltonian**: H(t) changes over time
2. **Work done by field**: The oscillating field can do work on the system
3. **Energy transfer**: Energy can flow into/out of the system

This is physically meaningful and represents:
- Driven quantum systems
- AC magnetic fields
- Time-dependent control in quantum computing

## Comparison

| Case | Hamiltonian | Energy Conservation | Physical Meaning |
|------|-------------|---------------------|------------------|
| Time-independent | H = constant | ✓ Conserved | Closed system, no external driving |
| Time-dependent | H(t) = H₀ - h(t)ΣZ | ✗ Not conserved | Open system, external driving field |

