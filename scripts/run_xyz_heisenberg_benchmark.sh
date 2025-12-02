#!/bin/bash
# XYZ Heisenberg Model Benchmark: Qubit sweep from 4 to 12 qubits
# Tests performance scaling with increasing qubit count

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
RESULTS_BASE_DIR="/app/test_results/xyz_heisenberg"
OUTPUT_DIR="${RESULTS_BASE_DIR}/individual"
mkdir -p "$RESULTS_BASE_DIR" "$OUTPUT_DIR"

# Prompt user for qubit range and step
echo "Configure XYZ Heisenberg qubit sweep:"
read -p "  Enter starting qubit count [4]: " START_QUBITS
read -p "  Enter ending qubit count   [24]: " END_QUBITS
read -p "  Enter qubit step interval  [2]: " STEP_QUBITS

# Apply defaults if user presses Enter
START_QUBITS=${START_QUBITS:-4}
END_QUBITS=${END_QUBITS:-24}
STEP_QUBITS=${STEP_QUBITS:-2}

# Basic validation
if ! [[ "$START_QUBITS" =~ ^[0-9]+$ && "$END_QUBITS" =~ ^[0-9]+$ && "$STEP_QUBITS" =~ ^[0-9]+$ ]]; then
    echo "Error: qubit values must be positive integers."
    exit 1
fi

if [ "$START_QUBITS" -le 0 ] || [ "$END_QUBITS" -lt "$START_QUBITS" ] || [ "$STEP_QUBITS" -le 0 ]; then
    echo "Error: ensure END >= START, START > 0, and STEP > 0."
    exit 1
fi

# Build qubit count array from user input
QUBIT_COUNTS=()
for ((q = START_QUBITS; q <= END_QUBITS; q += STEP_QUBITS)); do
    QUBIT_COUNTS+=("$q")
done

if [ "${#QUBIT_COUNTS[@]}" -eq 0 ]; then
    echo "Error: no valid qubit counts generated."
    exit 1
fi

export XYZ_START_QUBITS="$START_QUBITS"
export XYZ_END_QUBITS="$END_QUBITS"
export XYZ_STEP_QUBITS="$STEP_QUBITS"

# Enable time-dependent field for non-conserved energy case
export XYZ_TIME_DEPENDENT="true"
export XYZ_FIELD_AMPLITUDE="2.0"
export XYZ_FIELD_FREQUENCY="1.0"

echo "Qubit sweep will run for: ${QUBIT_COUNTS[*]}"
echo "Time-dependent field enabled: h(t) = ${XYZ_FIELD_AMPLITUDE} * sin(${XYZ_FIELD_FREQUENCY}*t)"

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
                # Check for cargo in multiple ways
                CARGO_CMD=""
                if command -v cargo &> /dev/null; then
                    CARGO_CMD="cargo"
                elif [ -f "${HOME}/.cargo/bin/cargo" ]; then
                    CARGO_CMD="${HOME}/.cargo/bin/cargo"
                elif [ -f "/root/.cargo/bin/cargo" ]; then
                    CARGO_CMD="/root/.cargo/bin/cargo"
                fi
                
                if [ -z "$CARGO_CMD" ]; then
                    echo "    ✗ Cargo not found, skipping LogosQ"
                    continue
                fi
                
                # Redirect stderr to a temp file to capture errors
                error_log="/tmp/logosq_xyz_${qubits}qubits_error.log"
                # Temporarily disable set -e for this command to handle errors gracefully
                set +e
                cd "${REPO_ROOT}/logosq" && \
                    XYZ_QUBITS="$qubits" \
                    XYZ_OUTPUT_FILE="$output_file" \
                    XYZ_TIME_DEPENDENT="${XYZ_TIME_DEPENDENT:-true}" \
                    XYZ_FIELD_AMPLITUDE="${XYZ_FIELD_AMPLITUDE:-2.0}" \
                    XYZ_FIELD_FREQUENCY="${XYZ_FIELD_FREQUENCY:-1.0}" \
                    "$CARGO_CMD" run --example xyz_heisenberg --release > "$error_log" 2>&1
                cargo_exit_code=$?
                set -e
                
                if [ $cargo_exit_code -eq 0 ]; then
                    if [ -f "$output_file" ]; then
                        echo "    ✓ Completed"
                    else
                        echo "    ✗ JSON file not found"
                        cat "$error_log" | tail -5
                    fi
                else
                    echo "    ✗ Failed"
                    cat "$error_log" | tail -10
                fi
                ;;
            pennylane)
                if XYZ_QUBITS="$qubits" \
                   XYZ_OUTPUT_FILE="$output_file" \
                   XYZ_TIME_DEPENDENT="${XYZ_TIME_DEPENDENT:-true}" \
                   XYZ_FIELD_AMPLITUDE="${XYZ_FIELD_AMPLITUDE:-2.0}" \
                   XYZ_FIELD_FREQUENCY="${XYZ_FIELD_FREQUENCY:-1.0}" \
                   python3 "${REPO_ROOT}/pennylane/XYZHeisenberg/xyz_h.py" > /dev/null 2>&1; then
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
                if XYZ_QUBITS="$qubits" \
                   XYZ_OUTPUT_FILE="$output_file" \
                   XYZ_TIME_DEPENDENT="${XYZ_TIME_DEPENDENT:-true}" \
                   XYZ_FIELD_AMPLITUDE="${XYZ_FIELD_AMPLITUDE:-2.0}" \
                   XYZ_FIELD_FREQUENCY="${XYZ_FIELD_FREQUENCY:-1.0}" \
                   python3 "${REPO_ROOT}/qiskit/XYZHeisenberg/xyz_h.py" > /dev/null 2>&1; then
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
                if XYZ_QUBITS="$qubits" \
                   XYZ_OUTPUT_FILE="$output_file" \
                   XYZ_TIME_DEPENDENT="${XYZ_TIME_DEPENDENT:-true}" \
                   XYZ_FIELD_AMPLITUDE="${XYZ_FIELD_AMPLITUDE:-2.0}" \
                   XYZ_FIELD_FREQUENCY="${XYZ_FIELD_FREQUENCY:-1.0}" \
                   julia --project="${REPO_ROOT}/yao.jl" "${REPO_ROOT}/yao.jl/XYZHeisenberg/xyz_h.jl" > /dev/null 2>&1; then
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
                if XYZ_QUBITS="$qubits" \
                   XYZ_OUTPUT_FILE="$output_file" \
                   XYZ_TIME_DEPENDENT="${XYZ_TIME_DEPENDENT:-true}" \
                   XYZ_FIELD_AMPLITUDE="${XYZ_FIELD_AMPLITUDE:-2.0}" \
                   XYZ_FIELD_FREQUENCY="${XYZ_FIELD_FREQUENCY:-1.0}" \
                   dotnet run --project "${REPO_ROOT}/qsharp/XYZHeisenberg/XYZHeisenberg.csproj" --configuration Release > /dev/null 2>&1; then
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

start_qubits = int(os.environ.get("XYZ_START_QUBITS", "4"))
end_qubits = int(os.environ.get("XYZ_END_QUBITS", "24"))
step_qubits = int(os.environ.get("XYZ_STEP_QUBITS", "2"))
if start_qubits <= 0 or end_qubits < start_qubits or step_qubits <= 0:
    print("Invalid qubit sweep configuration from environment; falling back to default [4, 6, ..., 24].", file=sys.stderr)
    qubit_counts = list(range(4, 25, 2))
else:
    qubit_counts = list(range(start_qubits, end_qubits + 1, step_qubits))

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
        echo "Generated plots (non-conserved energy case):"
        echo "  • xyz_heisenberg_runtime_scaling_log.png"
        echo "  • xyz_heisenberg_operations_comparison.png"
        echo "  • xyz_heisenberg_memory_usage.png"
        echo "  • xyz_heisenberg_energy_evolution.png"
        echo ""
        echo "Location: ${RESULTS_BASE_DIR}"
    else
        echo "✗ Plot generation failed (check /tmp/xyz_plot_generation.log)"
        cat /tmp/xyz_plot_generation.log | tail -20
    fi
else
    echo "✗ Python3 not available, cannot generate plots"
fi

