#!/bin/bash
# XYZ Heisenberg Model Benchmark: Qubit sweep from 4 to 12 qubits
# Tests performance scaling with increasing qubit count

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
RESULTS_BASE_DIR="/app/test_results/xyz_heisenberg"
OUTPUT_DIR="${RESULTS_BASE_DIR}/individual"
mkdir -p "$RESULTS_BASE_DIR" "$OUTPUT_DIR"

# Qubit counts: 4, 5, 6, 7, 8, 9, 10, 11, 12
QUBIT_COUNTS=(4 5 6 7 8 9 10 11 12)

FRAMEWORKS=("logosq" "pennylane" "qiskit" "yao" "qsharp")

echo "=========================================="
echo "XYZ Heisenberg Model Benchmark"
echo "Testing qubit counts: ${QUBIT_COUNTS[*]}"
echo "=========================================="
echo ""

for framework in "${FRAMEWORKS[@]}"; do
    echo "Running $framework qubit sweep..."
    
    for qubits in "${QUBIT_COUNTS[@]}"; do
        echo "  - Testing $qubits qubits..."
        
        output_file="${OUTPUT_DIR}/${framework}_${qubits}qubits.json"
        
        case $framework in
            logosq)
                if cd "${REPO_ROOT}/logosq" && XYZ_QUBITS="$qubits" XYZ_OUTPUT_FILE="$output_file" cargo run --example xyz_heisenberg > /dev/null 2>&1; then
                    if [ -f "$output_file" ]; then
                        echo "    ✓ Completed"
                    else
                        echo "    ✗ JSON file not found"
                    fi
                else
                    echo "    ✗ Failed"
                fi
                ;;
            pennylane)
                if XYZ_QUBITS="$qubits" XYZ_OUTPUT_FILE="$output_file" python3 "${REPO_ROOT}/pennylane/XYZHeisenberg/xyz_h.py" > /dev/null 2>&1; then
                    if [ -f "$output_file" ]; then
                        echo "    ✓ Completed"
                    else
                        echo "    ✗ JSON file not found"
                    fi
                else
                    echo "    ✗ Failed"
                fi
                ;;
            qiskit)
                if XYZ_QUBITS="$qubits" XYZ_OUTPUT_FILE="$output_file" python3 "${REPO_ROOT}/qiskit/XYZHeisenberg/xyz_h.py" > /dev/null 2>&1; then
                    if [ -f "$output_file" ]; then
                        echo "    ✓ Completed"
                    else
                        echo "    ✗ JSON file not found"
                    fi
                else
                    echo "    ✗ Failed"
                fi
                ;;
            yao)
                if XYZ_QUBITS="$qubits" XYZ_OUTPUT_FILE="$output_file" julia --project="${REPO_ROOT}/yao.jl" "${REPO_ROOT}/yao.jl/XYZHeisenberg/xyz_h.jl" > /dev/null 2>&1; then
                    if [ -f "$output_file" ]; then
                        echo "    ✓ Completed"
                    else
                        echo "    ✗ JSON file not found"
                    fi
                else
                    echo "    ✗ Failed"
                fi
                ;;
            qsharp)
                if XYZ_QUBITS="$qubits" XYZ_OUTPUT_FILE="$output_file" dotnet run --project "${REPO_ROOT}/qsharp/XYZHeisenberg/XYZHeisenberg.csproj" --configuration Release > /dev/null 2>&1; then
                    if [ -f "$output_file" ]; then
                        echo "    ✓ Completed"
                    else
                        echo "    ✗ JSON file not found"
                    fi
                else
                    echo "    ✗ Failed"
                fi
                ;;
        esac
    done
    echo ""
done

# Combine all results into a single JSON file
echo "Combining results..."
combined_file="${RESULTS_BASE_DIR}/xyz_heisenberg_results.json"
python3 << PYTHON_SCRIPT
import json
import sys
import os

script_dir = "${SCRIPT_DIR}"
output_dir = "${OUTPUT_DIR}"

frameworks = ["logosq", "pennylane", "qiskit", "yao", "qsharp"]
qubit_counts = [4, 5, 6, 7, 8, 9, 10, 11, 12]

results = []
for framework in frameworks:
    for qubits in qubit_counts:
        result_file = os.path.join(output_dir, f"{framework}_{qubits}qubits.json")
        if os.path.exists(result_file):
            try:
                with open(result_file, 'r') as f:
                    result = json.load(f)
                    results.append(result)
            except Exception as e:
                print(f"Error reading {result_file}: {e}", file=sys.stderr)

if not results:
    print("No XYZ Heisenberg results found.", file=sys.stderr)
    sys.exit(1)

output_file = "${combined_file}"
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)

print(f"Combined {len(results)} results into {output_file}")
PYTHON_SCRIPT

echo "✓ XYZ Heisenberg benchmark complete!"
echo "Results saved to: $combined_file"
echo "Individual results in: $OUTPUT_DIR"
echo ""

# Generate comparison plots
echo "Generating comparison plots..."
if command -v python3 &> /dev/null; then
    if python3 "${SCRIPT_DIR}/plot_xyz_heisenberg_comparison.py" > /tmp/xyz_plot_generation.log 2>&1; then
        echo "✓ Comparison plots generated successfully"
        echo ""
        echo "Generated plots:"
        echo "  • xyz_heisenberg_runtime_comparison.png"
        echo "  • xyz_heisenberg_energy_evolution.png"
        echo "  • xyz_heisenberg_scaling_analysis.png"
        echo "  • xyz_heisenberg_operations_comparison.png"
        echo ""
        echo "Location: ${RESULTS_BASE_DIR}"
    else
        echo "✗ Plot generation failed (check /tmp/xyz_plot_generation.log)"
        cat /tmp/xyz_plot_generation.log | tail -20
    fi
else
    echo "✗ Python3 not available, cannot generate plots"
fi

