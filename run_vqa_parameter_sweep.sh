#!/bin/bash
# Parameter sweep benchmark: VQE performance vs number of parameters
# Tests parameter counts: 12, 16, 20, 24, 28 (corresponding to 3, 4, 5, 6, 7 layers)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${SCRIPT_DIR}/test_results/parameter_sweep"
mkdir -p "$OUTPUT_DIR"

# Parameter counts: 12, 16, 20, 24, 28 (for 4 qubits: 3, 4, 5, 6, 7 layers)
PARAM_COUNTS=(12 16 20 24 28)
LAYERS=(3 4 5 6 7)

FRAMEWORKS=("logosq" "qiskit" "pennylane" "yao")

echo "=========================================="
echo "VQE Parameter Sweep Benchmark"
echo "Testing parameter counts: ${PARAM_COUNTS[*]}"
echo "=========================================="
echo ""

for framework in "${FRAMEWORKS[@]}"; do
    echo "Running $framework parameter sweep..."
    
    for i in "${!PARAM_COUNTS[@]}"; do
        param_count="${PARAM_COUNTS[$i]}"
        layers="${LAYERS[$i]}"
        
        echo "  - Testing $param_count parameters ($layers layers)..."
        
        output_file="${OUTPUT_DIR}/${framework}_${param_count}params.json"
        
        case $framework in
            logosq)
                if cd "${SCRIPT_DIR}/logosq" && VQA_LAYERS="$layers" VQA_OUTPUT_FILE="$output_file" cargo run --example vqa > /dev/null 2>&1; then
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
                if VQA_LAYERS="$layers" VQA_OUTPUT_FILE="$output_file" python3 "${SCRIPT_DIR}/qiskit/VQA/vqa.py" > /dev/null 2>&1; then
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
                if VQA_LAYERS="$layers" VQA_OUTPUT_FILE="$output_file" python3 "${SCRIPT_DIR}/pennylane/VQA/vqa.py" > /dev/null 2>&1; then
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
                if VQA_LAYERS="$layers" VQA_OUTPUT_FILE="$output_file" julia "${SCRIPT_DIR}/yao.jl/VQA/vqa.jl" > /dev/null 2>&1; then
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
combined_file="${SCRIPT_DIR}/vqa_parameter_sweep_results.json"
python3 << PYTHON_SCRIPT
import json
import sys
import os

script_dir = "${SCRIPT_DIR}"
output_dir = "${OUTPUT_DIR}"

frameworks = ["logosq", "qiskit", "pennylane", "yao"]
param_counts = [12, 16, 20, 24, 28]

results = []
for framework in frameworks:
    for param_count in param_counts:
        result_file = os.path.join(output_dir, f"{framework}_{param_count}params.json")
        if os.path.exists(result_file):
            try:
                with open(result_file, 'r') as f:
                    result = json.load(f)
                    results.append(result)
            except Exception as e:
                print(f"Error reading {result_file}: {e}", file=sys.stderr)

if not results:
    print("No parameter sweep results found.", file=sys.stderr)
    sys.exit(1)

output_file = "${combined_file}"
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)

print(f"Combined {len(results)} results into {output_file}")
PYTHON_SCRIPT

echo "✓ Parameter sweep complete!"
echo "Results saved to: $combined_file"
echo "Individual results in: $OUTPUT_DIR"

