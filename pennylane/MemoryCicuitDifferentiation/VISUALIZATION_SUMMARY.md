# Circuit Visualization Summary

All bug demonstrations in `pennylane_gradient_bugs.py` now include PennyLane's built-in circuit visualization using `qml.draw()`.

## Visualizations Added

### Bug 1: Invalid Generator Operations
- **Visualization**: Shows circuit with CNOT interleaved between parameterized gates
- **Highlights**: The problem of non-generator operations breaking PSR parameter tracking
- **Output**: ASCII circuit diagram showing RX → CNOT → RY → CRY sequence

### Bug 2: No-Cloning Violations
- **Visualization**: Shows entangled Bell state circuit with parameter reuse
- **Highlights**: How state reuse across parameter shifts violates no-cloning principle
- **Output**: Circuit showing H → CNOT → RY → RZ → RX with entangled measurement

### Bug 3: Broadcasting Issues with Batched VQCs
- **Visualization**: Shows VQC with data embedding and parameterized layers
- **Highlights**: Broadcasting problems when data input x is batched
- **Output**: Circuit with RY(x) data embedding followed by parameterized gates

### Bug 4: Silent NaN Errors
- **Visualization**: Shows circuit with potential NaN-producing operations
- **Highlights**: Edge cases that can cause NaN gradients
- **Output**: Circuit with multiple parameterized gates and controlled rotations

### Bug 5: Parameter Reuse and Circular Dependencies
- **Visualization**: Shows circuit with same parameters used multiple times
- **Highlights**: Parameter dependency tracking failures with reuse
- **Output**: Circuit clearly showing θ₀ used 3 times and θ₁ used 2 times

### Bug 6a: Operation Ordering PSR Issues
- **Visualization**: Shows TWO circuits with different operation orders
- **Highlights**: How operation order affects PSR evaluation
- **Output**: Side-by-side comparison of two circuit structures

### Bug 6: Complex VQC Training Failure
- **Visualization**: Shows complex realistic VQC with multiple layers
- **Highlights**: How multiple issues combine in real-world scenarios
- **Output**: Large circuit diagram showing data embedding, multiple parameterized layers, entangling gates, and measurements

## Visualization Features

Each visualization includes:
1. **Circuit Diagram**: PennyLane's `qml.draw()` showing the actual circuit structure
2. **Problem Explanation**: Clear description of what the bug demonstrates
3. **Mathematical Context**: How the circuit structure relates to the PSR computation

## Usage

Visualizations are automatically displayed when running each bug demonstration:

```python
from pennylane_gradient_bugs import PennyLaneGradientBugDemo

demo = PennyLaneGradientBugDemo()
demo.bug_1_invalid_generator_operations()  # Includes visualization
```

Or run all bugs:

```python
demo.run_all_demos()  # All bugs include visualizations
```

## Benefits

The visualizations help:
- **Understand the circuit structure** that causes each bug
- **Identify problematic patterns** (interleaved gates, parameter reuse, etc.)
- **Compare different circuits** to see how structure affects PSR
- **Demonstrate to reviewers** exactly what circuit configurations cause issues

All visualizations use PennyLane's native `qml.draw()` function with appropriate formatting for clarity.


