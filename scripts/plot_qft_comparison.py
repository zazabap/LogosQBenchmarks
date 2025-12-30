"""
Plot comparison between LogosQ (Rust), PennyLane (Python), Qiskit (Python), and Yao.jl (Julia) QFT benchmarks.
Generates plots for execution time and memory usage comparing all available libraries.
"""

import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

# Configure matplotlib for high-quality, stylish plots
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
plt.rcParams['savefig.format'] = 'pdf'

fig_size = (16, 7)

VECTOR_FORMAT = "pdf"

RESULTS_DIR = Path("/app/test_results/qft")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Library configuration with enhanced styling
LIBRARIES = {
    'logosq': {
        'name': 'LogosQ (Rust)',
        'color': '#E63946',  # Red
        'marker': 'o',
        'markeredgecolor': '#B71C1C',
        'markeredgewidth': 1.5,
        'linestyle': '-',
        'linewidth': 2.8,
        'alpha': 0.9,
        'file': str(RESULTS_DIR / 'logosq_qft_benchmark_results.json')
    },
    'pennylane': {
        'name': 'PennyLane (Python)',
        'color': '#F77F00',  # Orange
        'marker': '^',
        'markeredgecolor': '#E65100',
        'markeredgewidth': 1.5,
        'linestyle': '-',
        'linewidth': 2.8,
        'alpha': 0.9,
        'file': str(RESULTS_DIR / 'pennylane_qft_benchmark_results.json')
    },
    'qiskit': {
        'name': 'Qiskit (Python)',
        'color': '#457B9D',  # Blue
        'marker': 's',
        'markeredgecolor': '#1D3557',
        'markeredgewidth': 1.5,
        'linestyle': '-',
        'linewidth': 2.8,
        'alpha': 0.9,
        'file': str(RESULTS_DIR / 'qiskit_qft_benchmark_results.json')
    },
    'yao': {
        'name': 'Yao.jl (Julia)',
        'color': '#2A9D8F',  # Teal
        'marker': 'D',
        'markeredgecolor': '#004D40',
        'markeredgewidth': 1.5,
        'linestyle': '-',
        'linewidth': 2.8,
        'alpha': 0.9,
        'file': str(RESULTS_DIR / 'yao_qft_benchmark_results.json')
    },
    'qsharp': {
        'name': 'Q# (.NET)',
        'color': '#884dff',  # Purple
        'marker': 'X',
        'markeredgecolor': '#5a32a8',
        'markeredgewidth': 1.5,
        'linestyle': '-',
        'linewidth': 2.8,
        'alpha': 0.9,
        'file': str(RESULTS_DIR / 'qsharp_qft_benchmark_results.json')
    }
}

def load_logosq_results(filepath: str) -> List[Dict]:
    """Load LogosQ (Rust) benchmark results"""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            # Rust results are already a list of BenchmarkResult
            return data if isinstance(data, list) else data.get('results', [])
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing LogosQ results: {e}")
        return []

def load_pennylane_results(filepath: str) -> List[Dict]:
    """Load PennyLane (Python) benchmark results"""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            # PennyLane results are nested in results array with qft_only entries
            if isinstance(data, dict) and 'results' in data:
                # Extract qft_only results
                results = []
                for entry in data['results']:
                    if 'qft_only' in entry:
                        results.append(entry['qft_only'])
                return results
            return []
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing PennyLane results: {e}")
        return []

def load_qiskit_results(filepath: str) -> List[Dict]:
    """Load Qiskit (Python) benchmark results"""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            # Qiskit results format: {"library": "Qiskit", "results": [...]}
            if isinstance(data, dict) and 'results' in data:
                # Filter for QFT results only
                results = []
                for entry in data['results']:
                    if entry.get('name', '').startswith('QFT-'):
                        results.append(entry)
                return results
            return []
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing Qiskit results: {e}")
        return []

def load_yao_results(filepath: str) -> List[Dict]:
    """Load Yao.jl (Julia) benchmark results"""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            # Yao results are already a list of BenchmarkResult (same format as Rust)
            return data if isinstance(data, list) else data.get('results', [])
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing Yao results: {e}")
        return []

def load_qsharp_results(filepath: str) -> List[Dict]:
    """Load Q# (.NET) benchmark results"""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            return data if isinstance(data, list) else data.get('results', [])
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing Q# results: {e}")
        return []

def extract_data(results: List[Dict], source: str) -> Tuple[List[int], List[float], List[float], List[float]]:
    """
    Extract qubit counts, execution times, time std dev, and memory usage.
    
    Returns:
        (qubits, times, time_stds, memory)
    """
    qubits = []
    times = []
    time_stds = []
    memory = []
    
    for result in results:
        if source == 'logosq':
            # Rust format
            qubits.append(result['n_qubits'])
            times.append(result['execution_time_ms'])
            time_stds.append(result.get('std_deviation_ms', 0.0))
            memory.append(result.get('memory_mb', 0.0))
        elif source == 'pennylane':
            # PennyLane format
            qubits.append(result['n_qubits'])
            time_data = result.get('execution_time_ms', {})
            if isinstance(time_data, dict):
                times.append(time_data.get('mean', 0.0))
                time_stds.append(time_data.get('std', 0.0))
            else:
                times.append(time_data)
                time_stds.append(0.0)
            
            mem_data = result.get('memory_usage_mb', {})
            if isinstance(mem_data, dict):
                memory.append(mem_data.get('delta_mean', 0.0))
            else:
                memory.append(mem_data)
        elif source == 'qiskit':
            # Qiskit format: {name, num_qubits, execution_time_ms, memory_usage_mb, ...}
            qubits.append(result['num_qubits'])
            times.append(result.get('execution_time_ms', 0.0))
            time_stds.append(0.0)  # Qiskit doesn't provide std dev in current format
            memory.append(result.get('memory_usage_mb', 0.0))
        elif source == 'yao':
            # Yao format (same as Rust): {n_qubits, execution_time_ms, std_deviation_ms, memory_mb, ...}
            qubits.append(result['n_qubits'])
            times.append(result['execution_time_ms'])
            time_stds.append(result.get('std_deviation_ms', 0.0))
            memory.append(result.get('memory_mb', 0.0))
        elif source == 'qsharp':
            # Q# format (similar to Rust/Yao)
            qubits.append(result['n_qubits'])
            times.append(result['execution_time_ms'])
            time_stds.append(result.get('std_deviation_ms', 0.0))
            memory.append(result.get('memory_mb', 0.0))
    
    return qubits, times, time_stds, memory

def plot_execution_time_comparison(
    datasets: Dict[str, Tuple[List[int], List[float], List[float]]],
    output_path: str
):
    """Plot execution time comparison for multiple libraries with log scale"""
    from pathlib import Path
    
    # Create output path for log plot
    output_path_obj = Path(output_path)
    log_path = output_path_obj.parent / f"{output_path_obj.stem}_log{output_path_obj.suffix}"
    
    # Plot: Log scale
    fig, ax = plt.subplots(1, 1, figsize=(12, 7), facecolor='white')
    
    for lib_id, (qubits, times, stds) in datasets.items():
        if qubits and times:
            config = LIBRARIES[lib_id]
            ax.errorbar(
                qubits, times,
                yerr=stds if any(stds) else None,
                label=config['name'],
                marker=config['marker'],
                markersize=11,
                markeredgecolor=config.get('markeredgecolor', config['color']),
                markeredgewidth=config.get('markeredgewidth', 1.5),
                linewidth=config.get('linewidth', 2.8),
                linestyle=config.get('linestyle', '-'),
                capsize=6,
                capthick=2,
                elinewidth=2,
                color=config['color'],
                alpha=config.get('alpha', 0.9),
                zorder=3
            )
    
    ax.set_xlabel('Number of Qubits', fontsize=13, fontweight='bold', labelpad=10)
    ax.set_ylabel('Execution Time (ms, log scale)', fontsize=13, fontweight='bold', labelpad=10)
    ax.set_yscale('log')
    ax.legend(loc='lower right', frameon=True, fancybox=True, shadow=True,
               fontsize=13, framealpha=0.95, edgecolor='gray', facecolor='white')
    ax.grid(True, alpha=0.4, linestyle='--', linewidth=0.8, which='both', zorder=0)
    ax.set_facecolor('#FAFAFA')
    ax.spines['bottom'].set_color('#333333')
    ax.spines['left'].set_color('#333333')
    ax.tick_params(colors='#333333', width=1.2, length=5)
    
    plt.tight_layout()
    plt.savefig(log_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none', format=VECTOR_FORMAT)
    plt.close(fig)
    print(f"✓ Saved execution time comparison plot (log scale) to: {log_path}")

def plot_memory_comparison(
    datasets: Dict[str, Tuple[List[int], List[float]]],
    output_path: str
):
    """Plot memory usage comparison for multiple libraries with symlog scale"""
    from pathlib import Path
    
    # Create output path for full range plot
    output_path_obj = Path(output_path)
    full_path = output_path_obj.parent / f"{output_path_obj.stem}_full{output_path_obj.suffix}"
    
    # Check if we have memory data
    all_memory_values = []
    for lib_id, (qubits, memory) in datasets.items():
        if qubits and memory:
            all_memory_values.extend([m for m in memory if m is not None])
    
    if not all_memory_values:
        print("⚠ No memory data found, skipping memory plot")
        return
    
    # Plot: Full range with symlog scale to handle both small and large values
    fig, ax = plt.subplots(1, 1, figsize=(14, 8), facecolor='white')
    
    for lib_id, (qubits, memory) in datasets.items():
        if qubits and memory:
            config = LIBRARIES[lib_id]
            ax.plot(
                qubits, memory,
                label=config['name'],
                marker=config['marker'],
                markersize=13,
                markeredgecolor=config.get('markeredgecolor', config['color']),
                markeredgewidth=config.get('markeredgewidth', 1.8),
                linewidth=config.get('linewidth', 3.0),
                linestyle=config.get('linestyle', '-'),
                color=config['color'],
                alpha=config.get('alpha', 0.9),
                zorder=3
            )
    
    ax.set_xlabel('Number of Qubits', fontsize=14, fontweight='bold', labelpad=12)
    ax.set_ylabel('Memory Usage (MB, symlog scale)', fontsize=14, fontweight='bold', labelpad=12)
    ax.legend(loc='upper center', frameon=True, fancybox=True, shadow=True,
              fontsize=12, framealpha=0.95, edgecolor='gray', facecolor='white', 
              borderpad=0.8, handlelength=2.0, handletextpad=0.8)
    ax.grid(True, alpha=0.4, linestyle='--', linewidth=0.8, zorder=0, which='both')
    # Use symlog scale: linear near 0, logarithmic for larger values
    # linthresh=0.1 means values between -0.1 and 0.1 are shown on linear scale
    ax.set_yscale('symlog', linthresh=0.1, linscale=0.5)
    ax.set_facecolor('#FAFAFA')
    ax.spines['bottom'].set_color('#333333')
    ax.spines['left'].set_color('#333333')
    ax.tick_params(colors='#333333', width=1.2, length=6, labelsize=12)
    
    plt.tight_layout()
    plt.savefig(full_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none', format=VECTOR_FORMAT)
    plt.close(fig)
    print(f"✓ Saved memory usage comparison plot (symlog scale) to: {full_path}")

def plot_speedup_comparison(
    datasets: Dict[str, Tuple[List[int], List[float]]],
    baseline_lib: str,
    output_path: str
):
    """Plot speedup ratio compared to a baseline library with enhanced styling"""
    if baseline_lib not in datasets:
        print(f"⚠ Baseline library '{baseline_lib}' not found, skipping speedup plot")
        return
    
    baseline_qubits, baseline_times = datasets[baseline_lib]
    if not baseline_qubits or not baseline_times:
        print(f"⚠ No data for baseline library '{baseline_lib}', skipping speedup plot")
        return
    
    # Create a dictionary for quick lookup
    baseline_dict = dict(zip(baseline_qubits, baseline_times))
    
    fig, ax = plt.subplots(1, 1, figsize=(12, 10), facecolor='white')
    baseline_name = LIBRARIES[baseline_lib]['name']
    
    for lib_id, (qubits, times) in datasets.items():
        if lib_id == baseline_lib:
            continue
        
        if not qubits or not times:
            continue
        
        # Find common qubit counts
        speedup_qubits = []
        speedups = []
        
        for q, t in zip(qubits, times):
            if q in baseline_dict and baseline_dict[q] > 0:
                speedup = t / baseline_dict[q]  # Ratio: other_lib_time / baseline_time
                speedups.append(speedup)
                speedup_qubits.append(q)
        
        if speedups:
            config = LIBRARIES[lib_id]
            ax.plot(
                speedup_qubits, speedups,
                marker=config['marker'],
                markersize=12,
                markeredgecolor=config.get('markeredgecolor', config['color']),
                markeredgewidth=config.get('markeredgewidth', 1.5),
                linewidth=config.get('linewidth', 2.8),
                linestyle=config.get('linestyle', '-'),
                color=config['color'],
                alpha=config.get('alpha', 0.9),
                label=f"{config['name']}",
                zorder=3
            )
            
            # Add annotations for significant differences with better styling
            for q, s in zip(speedup_qubits, speedups):
                if s > 2.0 or s < 0.5:  # Highlight significant differences
                    color = '#FF6B6B' if s > 2.0 else '#4ECDC4'
                    ax.annotate(
                        f'{s:.2f}x',
                        (q, s),
                        xytext=(8, 8),
                        textcoords='offset points',
                        fontsize=10,
                        fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.5', facecolor=color, 
                                alpha=0.7, edgecolor='white', linewidth=1.5),
                        color='white',
                        zorder=4
                    )
    
    # Add reference line at 1x with better styling
    ax.axhline(y=1.0, color='#333333', linestyle='--', linewidth=2.5, 
               alpha=0.7, zorder=2, label=f'{baseline_name} (baseline = 1x)')
    
    # Set log scale before getting limits and adding shaded regions
    ax.set_yscale('log')
    
    # Add shaded regions for better/faster performance (after plotting)
    if ax.lines:  # Check if we have any plots
        y_min, y_max = ax.get_ylim()
        # Add shaded regions (use small positive value for log scale)
        ax.axhspan(max(y_min, 0.01), 1, alpha=0.08, color='#4CAF50', zorder=0)
        ax.axhspan(1, y_max, alpha=0.08, color='#F44336', zorder=0)
        ax.set_ylim(y_min, y_max)  # Restore limits
    
    ax.set_xlabel('Number of Qubits', fontsize=13, fontweight='bold', labelpad=10)
    ax.set_ylabel(f'Speedup Ratio (vs {baseline_name}, log scale)', fontsize=13, fontweight='bold', labelpad=10)
    ax.legend(loc='upper center', frameon=True, fancybox=True, shadow=True,
              fontsize=13, framealpha=0.95, edgecolor='gray', facecolor='white')
    ax.grid(True, alpha=0.4, linestyle='--', linewidth=0.8, which='both', zorder=1)
    ax.set_facecolor('#FAFAFA')
    ax.spines['bottom'].set_color('#333333')
    ax.spines['left'].set_color('#333333')
    ax.tick_params(colors='#333333', width=1.2, length=5)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none', format=VECTOR_FORMAT)
    print(f"✓ Saved speedup comparison plot to: {output_path}")

def plot_synthesis_result(
    time_datasets: Dict[str, Tuple[List[int], List[float], List[float]]],
    memory_datasets: Dict[str, Tuple[List[int], List[float]]],
    baseline_lib: str,
    output_path: str
):
    """Create a synthesis plot combining execution time (log), memory (full), and speedup comparison"""
    if not time_datasets:
        print("⚠ No timing data found, skipping synthesis plot")
        return
    
    if baseline_lib not in time_datasets:
        print(f"⚠ Baseline library '{baseline_lib}' not found, skipping synthesis plot")
        return
    
    baseline_qubits, baseline_times, _ = time_datasets[baseline_lib]
    if not baseline_qubits or not baseline_times:
        print(f"⚠ No data for baseline library '{baseline_lib}', skipping synthesis plot")
        return
    
    # Create figure with 3 subplots arranged horizontally
    fig, axes = plt.subplots(1, 3, figsize=(24, 7), facecolor='white')
    ax1, ax2, ax3 = axes
    
    baseline_name = LIBRARIES[baseline_lib]['name']
    baseline_dict = dict(zip(baseline_qubits, baseline_times))
    
    # Plot 1: Execution Time (Log Scale) - Left subplot
    for lib_id, (qubits, times, stds) in time_datasets.items():
        if qubits and times:
            config = LIBRARIES[lib_id]
            ax1.errorbar(
                qubits, times,
                yerr=stds if any(stds) else None,
                label=config['name'],
                marker=config['marker'],
                markersize=10,
                markeredgecolor=config.get('markeredgecolor', config['color']),
                markeredgewidth=config.get('markeredgewidth', 1.5),
                linewidth=config.get('linewidth', 2.5),
                linestyle=config.get('linestyle', '-'),
                capsize=5,
                capthick=1.8,
                elinewidth=1.8,
                color=config['color'],
                alpha=config.get('alpha', 0.9),
                zorder=3
            )
    
    ax1.set_xlabel('Number of Qubits', fontsize=13, fontweight='bold', labelpad=10)
    ax1.set_ylabel('Execution Time (ms, log scale)', fontsize=13, fontweight='bold', labelpad=10)
    ax1.set_yscale('log')
    ax1.legend(loc='lower right', frameon=True, fancybox=True, shadow=True,
               fontsize=10, framealpha=0.95, edgecolor='gray', facecolor='white', ncol=1)
    ax1.grid(True, alpha=0.4, linestyle='--', linewidth=0.8, which='both', zorder=0)
    ax1.set_facecolor('#FAFAFA')
    ax1.spines['bottom'].set_color('#333333')
    ax1.spines['left'].set_color('#333333')
    ax1.tick_params(colors='#333333', width=1.2, length=5, labelsize=11)
    ax1.set_title('(a) Execution Time Comparison', fontsize=14, fontweight='bold', pad=10)
    
    # Plot 2: Memory Usage (Full Range with Symlog) - Middle subplot
    for lib_id, (qubits, memory) in memory_datasets.items():
        if qubits and memory:
            config = LIBRARIES[lib_id]
            ax2.plot(
                qubits, memory,
                label=config['name'],
                marker=config['marker'],
                markersize=10,
                markeredgecolor=config.get('markeredgecolor', config['color']),
                markeredgewidth=config.get('markeredgewidth', 1.5),
                linewidth=config.get('linewidth', 2.5),
                linestyle=config.get('linestyle', '-'),
                color=config['color'],
                alpha=config.get('alpha', 0.9),
                zorder=3
            )
    
    ax2.set_xlabel('Number of Qubits', fontsize=13, fontweight='bold', labelpad=10)
    ax2.set_ylabel('Memory Usage (MB, symlog scale)', fontsize=13, fontweight='bold', labelpad=10)
    ax2.legend(loc='upper center', frameon=True, fancybox=True, shadow=True,
              fontsize=10, framealpha=0.95, edgecolor='gray', facecolor='white', ncol=1)
    ax2.grid(True, alpha=0.4, linestyle='--', linewidth=0.8, zorder=0, which='both')
    ax2.set_yscale('symlog', linthresh=0.1, linscale=0.5)
    ax2.set_facecolor('#FAFAFA')
    ax2.spines['bottom'].set_color('#333333')
    ax2.spines['left'].set_color('#333333')
    ax2.tick_params(colors='#333333', width=1.2, length=5, labelsize=11)
    ax2.set_title('(b) Memory Usage Comparison', fontsize=14, fontweight='bold', pad=10)
    
    # Plot 3: Speedup Comparison - Right subplot
    for lib_id, (qubits, times, _) in time_datasets.items():
        if lib_id == baseline_lib:
            continue
        
        if not qubits or not times:
            continue
        
        # Find common qubit counts
        speedup_qubits = []
        speedups = []
        
        for q, t in zip(qubits, times):
            if q in baseline_dict and baseline_dict[q] > 0:
                speedup = t / baseline_dict[q]  # Ratio: other_lib_time / baseline_time
                speedups.append(speedup)
                speedup_qubits.append(q)
        
        if speedups:
            config = LIBRARIES[lib_id]
            ax3.plot(
                speedup_qubits, speedups,
                marker=config['marker'],
                markersize=10,
                markeredgecolor=config.get('markeredgecolor', config['color']),
                markeredgewidth=config.get('markeredgewidth', 1.5),
                linewidth=config.get('linewidth', 2.5),
                linestyle=config.get('linestyle', '-'),
                color=config['color'],
                alpha=config.get('alpha', 0.9),
                label=f"{config['name']}",
                zorder=3
            )
    
    # Add reference line at 1x
    ax3.axhline(y=1.0, color='#333333', linestyle='--', linewidth=2.5, 
               alpha=0.7, zorder=2, label=f'{baseline_name} (baseline = 1x)')
    
    # Set log scale before getting limits and adding shaded regions
    ax3.set_yscale('log')
    
    # Add shaded regions for better/faster performance
    if ax3.lines:
        y_min, y_max = ax3.get_ylim()
        ax3.axhspan(max(y_min, 0.01), 1, alpha=0.08, color='#4CAF50', zorder=0)
        ax3.axhspan(1, y_max, alpha=0.08, color='#F44336', zorder=0)
        ax3.set_ylim(y_min, y_max)
    
    ax3.set_xlabel('Number of Qubits', fontsize=13, fontweight='bold', labelpad=10)
    ax3.set_ylabel(f'Speedup Ratio (vs {baseline_name}, log scale)', fontsize=13, fontweight='bold', labelpad=10)
    ax3.legend(loc='upper center', frameon=True, fancybox=True, shadow=True,
              fontsize=10, framealpha=0.95, edgecolor='gray', facecolor='white', ncol=1)
    ax3.grid(True, alpha=0.4, linestyle='--', linewidth=0.8, which='both', zorder=1)
    ax3.set_facecolor('#FAFAFA')
    ax3.spines['bottom'].set_color('#333333')
    ax3.spines['left'].set_color('#333333')
    ax3.tick_params(colors='#333333', width=1.2, length=5, labelsize=11)
    ax3.set_title('(c) Speedup Comparison', fontsize=14, fontweight='bold', pad=10)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none', format=VECTOR_FORMAT)
    plt.close(fig)
    print(f"✓ Saved synthesis result plot to: {output_path}")

def main():
    """Main function to generate all comparison plots"""
    print("=" * 70)
    print("QFT Benchmark Comparison: LogosQ vs PennyLane vs Qiskit vs Yao.jl")
    print("=" * 70)
    
    # Output directory
    output_dir = RESULTS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load results from all libraries
    print("\n📂 Loading benchmark results...")
    
    all_results = {}
    loaders = {
        'logosq': load_logosq_results,
        'pennylane': load_pennylane_results,
        'qiskit': load_qiskit_results,
        'yao': load_yao_results,
        'qsharp': load_qsharp_results
    }
    
    for lib_id, loader in loaders.items():
        filepath = LIBRARIES[lib_id]['file']
        results = loader(filepath)
        all_results[lib_id] = results
        print(f"  {LIBRARIES[lib_id]['name']}: {len(results)} data points")
    
    # Check if we have any results
    if not any(all_results.values()):
        print("❌ No benchmark results found! Please run benchmarks first.")
        return
    
    # Extract data for plotting
    time_datasets = {}
    memory_datasets = {}
    
    for lib_id, results in all_results.items():
        if results:
            qubits, times, stds, memory = extract_data(results, lib_id)
            if qubits and times:
                time_datasets[lib_id] = (qubits, times, stds)
            if qubits and memory:
                memory_datasets[lib_id] = (qubits, memory)
    
    if not time_datasets:
        print("❌ No valid timing data found!")
        return
    
    # Generate plots
    print("\n📊 Generating comparison plots...")
    
    # Execution time comparison
    if time_datasets:
        plot_execution_time_comparison(
            time_datasets,
            str(output_dir / "qft_execution_time_comparison.pdf")
        )
    
    # Memory usage comparison
    if memory_datasets:
        plot_memory_comparison(
            memory_datasets,
            str(output_dir / "qft_memory_comparison.pdf")
        )
    
    # Speedup comparison (using LogosQ as baseline)
    if time_datasets and 'logosq' in time_datasets:
        plot_speedup_comparison(
            {k: (q, t) for k, (q, t, _) in time_datasets.items()},
            'logosq',
            str(output_dir / "qft_speedup_comparison.pdf")
        )
    
    # Synthesis result plot (combining execution time log, memory full, and speedup)
    if time_datasets and memory_datasets and 'logosq' in time_datasets:
        plot_synthesis_result(
            time_datasets,
            memory_datasets,
            'logosq',
            str(output_dir / "synthesis_result.pdf")
        )
    
    print("\n✅ All plots generated successfully!")
    print(f"📁 Output directory: {output_dir}")
    
    # Print summary statistics
    print("\n📊 Summary Statistics:")
    print("-" * 70)
    
    for lib_id, results in all_results.items():
        if results:
            qubits, times, _, memory = extract_data(results, lib_id)
            if qubits and times:
                print(f"\n{LIBRARIES[lib_id]['name']}:")
                print(f"  Qubit range: {min(qubits)} - {max(qubits)}")
                print(f"  Time range: {min(times):.3f} - {max(times):.3f} ms")
                if memory:
                    mem_values = [m for m in memory if m > 0]
                    if mem_values:
                        print(f"  Memory range: {min(mem_values):.2f} - {max(mem_values):.2f} MB")
    
    # Compare common qubit counts
    if len(time_datasets) > 1:
        print("\n🔍 Comparison at common qubit counts:")
        print("-" * 70)
        
        # Find common qubit counts
        all_common_qubits = None
        for lib_id, (qubits, _, _) in time_datasets.items():
            if all_common_qubits is None:
                all_common_qubits = set(qubits)
            else:
                all_common_qubits &= set(qubits)
        
        if all_common_qubits:
            common_qubits = sorted(all_common_qubits)
            print(f"{'Qubits':<8}", end="")
            for lib_id in time_datasets.keys():
                print(f"{LIBRARIES[lib_id]['name']:<25}", end="")
            print()
            print("-" * 70)
            
            for q in common_qubits[:5]:  # Show first 5 common qubits
                print(f"{q:<8}", end="")
                baseline_time = None
                for lib_id in time_datasets.keys():
                    qubits, times, _ = time_datasets[lib_id]
                    idx = qubits.index(q)
                    time_val = times[idx]
                    if lib_id == 'logosq':
                        baseline_time = time_val
                    print(f"{time_val:>12.3f} ms  ", end="")
                if baseline_time and len(time_datasets) > 1:
                    # Show relative speedup
                    speedups = []
                    for lib_id in time_datasets.keys():
                        if lib_id != 'logosq':
                            qubits, times, _ = time_datasets[lib_id]
                            if q in qubits:
                                idx = qubits.index(q)
                                speedup = times[idx] / baseline_time if baseline_time > 0 else 0
                                speedups.append(f"{speedup:.2f}x")
                    if speedups:
                        print(f" (speedup: {', '.join(speedups)})", end="")
                print()
        else:
            print("  No common qubit counts found across all libraries")

if __name__ == "__main__":
    main()
