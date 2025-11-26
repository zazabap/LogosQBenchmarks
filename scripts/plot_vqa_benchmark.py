"""
Plot VQE parameter sweep results across LogosQ (Rust), PennyLane (Python),
Qiskit (Python), and Yao.jl (Julia).
Generates performance plots vs number of ansatz parameters.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Dict, List

# Configure matplotlib for high-quality plots
plt.rcParams.update({
    'font.size': 11,
    'font.family': 'sans-serif',
    'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica', 'Liberation Sans'],
    'axes.labelsize': 13,
    'axes.titlesize': 15,
    'axes.titleweight': 'bold',
    'axes.labelweight': 'bold',
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'legend.fontsize': 11,
    'legend.framealpha': 0.95,
    'legend.fancybox': True,
    'legend.shadow': True,
    'figure.titlesize': 16,
    'figure.titleweight': 'bold',
    'grid.alpha': 0.3,
    'grid.linewidth': 0.8,
    'lines.linewidth': 2.5,
    'lines.markersize': 10,
    'patch.linewidth': 1.5,
    'axes.linewidth': 1.2,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.axisbelow': True,
    'figure.facecolor': 'white',
    'axes.facecolor': '#FAFAFA',
    'savefig.facecolor': 'white',
    'savefig.edgecolor': 'none',
    'savefig.dpi': 300,
    'savefig.bbox': 'tight'
})

# Color scheme for frameworks
FRAMEWORK_COLORS = {
    'LogosQ (Rust)': '#E63946',
    'Qiskit (Python)': '#457B9D',
    'PennyLane (Python)': '#F77F00',
    'Yao.jl (Julia)': '#2A9D8F',
}

FRAMEWORK_MARKERS = {
    'LogosQ (Rust)': 'o',
    'Qiskit (Python)': 's',
    'PennyLane (Python)': '^',
    'Yao.jl (Julia)': 'D',
}

RESULTS_DIR = Path("/app/test_results/vqa_parameter_sweep")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_JSON = RESULTS_DIR / "vqa_parameter_sweep_results.json"

def load_results(json_path: Path) -> List[Dict]:
    """Load benchmark results from JSON file."""
    with open(json_path, 'r') as f:
        return json.load(f)


def plot_parameter_sweep(results: List[Dict], output_dir: Path):
    """Plot VQE performance vs number of parameters."""
    # Group results by framework
    frameworks = {}
    for r in results:
        fw = r['framework']
        if fw not in frameworks:
            frameworks[fw] = []
        frameworks[fw].append(r)
    
    # Sort by parameter count for each framework
    for fw in frameworks:
        frameworks[fw].sort(key=lambda x: x['parameters'])
    
    # Plot 1: Energy Error vs Parameters
    plt.figure(figsize=(8, 6))
    for fw, fw_results in frameworks.items():
        params = [r['parameters'] for r in fw_results]
        errors = [r['energy_error'] for r in fw_results]
        color = FRAMEWORK_COLORS.get(fw, '#666666')
        marker = FRAMEWORK_MARKERS.get(fw, 'o')
        plt.plot(params, errors, marker=marker, linewidth=2.5, markersize=10, 
                label=fw, color=color, alpha=0.8)
    
    plt.xlabel('Number of Parameters', fontweight='bold')
    plt.ylabel('Energy Error |E - E_exact| (Ha)', fontweight='bold')
    plt.title('Energy Error vs Number of Parameters', fontweight='bold', fontsize=14)
    plt.yscale('log')
    plt.grid(True, alpha=0.3, linestyle='--', which='both')
    plt.legend(loc='best', framealpha=0.95)
    plt.xticks([12, 16, 20, 24, 28])
    plt.tight_layout()
    output_path = output_dir / 'vqa_parameter_sweep_error.png'
    plt.savefig(output_path)
    print(f"Saved energy error plot to: {output_path}")
    plt.close()
    
    # Plot 2: Runtime vs Parameters
    plt.figure(figsize=(8, 6))
    for fw, fw_results in frameworks.items():
        params = [r['parameters'] for r in fw_results]
        runtimes = [r['runtime_ms'] for r in fw_results]
        color = FRAMEWORK_COLORS.get(fw, '#666666')
        marker = FRAMEWORK_MARKERS.get(fw, 'o')
        plt.plot(params, runtimes, marker=marker, linewidth=2.5, markersize=10,
                label=fw, color=color, alpha=0.8)
    
    plt.xlabel('Number of Parameters', fontweight='bold')
    plt.ylabel('Runtime (ms)', fontweight='bold')
    plt.title('Runtime vs Number of Parameters', fontweight='bold', fontsize=14)
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.legend(loc='best', framealpha=0.95)
    plt.xticks([12, 16, 20, 24, 28])
    plt.tight_layout()
    output_path = output_dir / 'vqa_parameter_sweep_runtime.png'
    plt.savefig(output_path)
    print(f"Saved runtime plot to: {output_path}")
    plt.close()
    
    # Plot 3: Iterations vs Parameters
    plt.figure(figsize=(8, 6))
    for fw, fw_results in frameworks.items():
        params = [r['parameters'] for r in fw_results]
        iterations = [r['iterations'] for r in fw_results]
        color = FRAMEWORK_COLORS.get(fw, '#666666')
        marker = FRAMEWORK_MARKERS.get(fw, 'o')
        plt.plot(params, iterations, marker=marker, linewidth=2.5, markersize=10,
                label=fw, color=color, alpha=0.8)
    
    plt.xlabel('Number of Parameters', fontweight='bold')
    plt.ylabel('Number of Iterations', fontweight='bold')
    plt.title('Convergence Iterations vs Number of Parameters', fontweight='bold', fontsize=14)
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.legend(loc='best', framealpha=0.95)
    plt.xticks([12, 16, 20, 24, 28])
    plt.tight_layout()
    output_path = output_dir / 'vqa_parameter_sweep_iterations.png'
    plt.savefig(output_path)
    print(f"Saved iterations plot to: {output_path}")
    plt.close()
    
    # Plot 4: VQE Energy vs Parameters
    plt.figure(figsize=(8, 6))
    exact_energy = results[0]['exact_energy'] if results else 0
    for fw, fw_results in frameworks.items():
        params = [r['parameters'] for r in fw_results]
        energies = [r['vqe_energy'] for r in fw_results]
        color = FRAMEWORK_COLORS.get(fw, '#666666')
        marker = FRAMEWORK_MARKERS.get(fw, 'o')
        plt.plot(params, energies, marker=marker, linewidth=2.5, markersize=10,
                label=fw, color=color, alpha=0.8)
    
    plt.axhline(y=exact_energy, color='red', linestyle='--', linewidth=2,
               label=f'Exact Energy (Ha)')
    plt.xlabel('Number of Parameters', fontweight='bold')
    plt.ylabel('VQE Energy (Ha)', fontweight='bold')
    plt.title('VQE Energy vs Number of Parameters', fontweight='bold', fontsize=14)
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.legend(loc='best', framealpha=0.95)
    plt.xticks([12, 16, 20, 24, 28])
    plt.tight_layout()
    output_path = output_dir / 'vqa_parameter_sweep_energy.png'
    plt.savefig(output_path)
    print(f"Saved VQE energy plot to: {output_path}")
    plt.close()


def main():
    output_dir = RESULTS_DIR

    if not RESULTS_JSON.exists():
        print(f"Error: Parameter sweep results not found: {RESULTS_JSON}")
        print("Please run ./run_vqa_parameter_sweep.sh first to generate results.")
        return

    print("Loading parameter sweep results...")
    param_results = load_results(RESULTS_JSON)

    if not param_results:
        print("No parameter sweep entries found in the results file.")
        return

    print(f"Found {len(param_results)} parameter sweep entries:")
    for r in param_results:
        print(
            f"  - {r['framework']}: params={r['parameters']}, "
            f"energy={r['vqe_energy']:.6f} Ha, runtime={r['runtime_ms']:.2f} ms, "
            f"iterations={r['iterations']}"
        )

    print("\nGenerating parameter sweep plot...")
    plot_parameter_sweep(param_results, output_dir)

    print("\nParameter sweep plot generated successfully!")


if __name__ == "__main__":
    main()

