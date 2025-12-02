# VQA Parameter Range Recommendations

## Overview

The VQA parameter sweep benchmark tests VQE performance across different numbers of ansatz parameters. Since the benchmark uses a 4-qubit H₂ molecule, the relationship is:

**Parameters = 4 qubits × number of layers**

## Default Range

- **Start**: 12 parameters (3 layers)
- **End**: 28 parameters (7 layers)  
- **Step**: 4 parameters (1 layer increment)

This corresponds to: 12, 16, 20, 24, 28 parameters (3, 4, 5, 6, 7 layers)

## Reasonable Ranges for Benchmarking

### Minimum Recommended Range
- **Start**: 12 parameters (3 layers)
- **End**: 20 parameters (5 layers)
- **Step**: 4 parameters

**Rationale**: Too few parameters (< 12) may not converge well. 3-5 layers is the minimum for meaningful VQE results.

### Standard Research Range
- **Start**: 12 parameters (3 layers)
- **End**: 40 parameters (10 layers)
- **Step**: 4 parameters

**Rationale**: This range (3-10 layers) is commonly used in VQE research papers. It provides a good balance between:
- Convergence quality (more parameters generally help)
- Computational cost (reasonable runtime)
- Expressibility (sufficient to capture ground state)

### Extended Range (Deep Circuits)
- **Start**: 12 parameters (3 layers)
- **End**: 60 parameters (15 layers)
- **Step**: 4 or 8 parameters

**Rationale**: For testing deep circuits and exploring expressibility limits. Note that:
- Runtime increases significantly with more parameters
- Convergence may become more difficult (barren plateaus)
- Useful for stress-testing frameworks

### Quick Test Range
- **Start**: 12 parameters (3 layers)
- **End**: 16 parameters (4 layers)
- **Step**: 4 parameters

**Rationale**: Minimal range for quick validation (2 data points).

## Usage Examples

```bash
# Default range (12-28 params, step 4)
./scripts/run_vqa_parameter_sweep.sh

# Extended range (12-40 params, step 4)
./scripts/run_vqa_parameter_sweep.sh 12 40 4

# Quick test (12-16 params only)
./scripts/run_vqa_parameter_sweep.sh 12 16 4

# Fine-grained sweep (12-28 params, step 2)
# Note: Only multiples of 4 are valid (4 qubits)
./scripts/run_vqa_parameter_sweep.sh 12 28 4  # Step must be 4 or multiple of 4
```

## Important Notes

1. **Parameter counts must be multiples of 4** (since we use 4 qubits)
   - Valid: 12, 16, 20, 24, 28, 32, 36, 40, ...
   - Invalid: 13, 15, 17, 19, ... (will be skipped with warning)

2. **Step size should be a multiple of 4** to ensure all generated counts are valid
   - Recommended: 4 (1 layer increment)
   - Also valid: 8 (2 layers), 12 (3 layers), etc.

3. **Runtime scales roughly linearly** with number of parameters, but:
   - More parameters → more optimization iterations may be needed
   - Convergence behavior can vary significantly

4. **Memory usage** is relatively constant (4-qubit state vector), so parameter count mainly affects:
   - Optimization runtime
   - Convergence quality
   - Number of iterations

## Typical Results

Based on typical VQE benchmarks:

- **12-16 params (3-4 layers)**: Fast, may not converge perfectly
- **20-28 params (5-7 layers)**: Good balance, typically converges well
- **32-40 params (8-10 layers)**: Better convergence, longer runtime
- **44+ params (11+ layers)**: Deep circuits, may hit barren plateaus

## Plotting

The plotting script (`plot_vqa_benchmark.py`) automatically adapts to any parameter range you use. It will:
- Dynamically set x-axis ticks based on your data
- Generate all plots (error, runtime, iterations, energy) for your range
- Handle any number of parameter points

