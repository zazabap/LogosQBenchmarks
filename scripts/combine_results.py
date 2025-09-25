#!/usr/bin/env python3

import json
import os
import glob
import sys
from datetime import datetime
from typing import Dict, List, Any

def load_benchmark_results() -> Dict[str, Any]:
    """Load all benchmark result files"""
    results = {}
    results_dir = '../results'
    
    if not os.path.exists(results_dir):
        print(f"Results directory {results_dir} not found")
        return results
    
    # Look for JSON result files
    pattern = os.path.join(results_dir, '*_results.json')
    result_files = glob.glob(pattern)
    
    for file_path in result_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            # Extract library name from filename
            filename = os.path.basename(file_path)
            library_name = filename.replace('_results.json', '')
            
            results[library_name] = data
            print(f"Loaded results for {library_name}: {len(data.get('results', []))} benchmarks")
            
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    
    return results

def analyze_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze and summarize benchmark results"""
    analysis = {
        'timestamp': datetime.now().isoformat(),
        'summary': {},
        'comparisons': {},
        'best_performers': {}
    }
    
    # Summary statistics for each library
    for library, data in results.items():
        if 'results' not in data:
            continue
            
        benchmarks = data['results']
        if not benchmarks:
            continue
        
        execution_times = [b['execution_time_ms'] for b in benchmarks]
        memory_usage = [b['memory_usage_mb'] for b in benchmarks]
        
        analysis['summary'][library] = {
            'total_benchmarks': len(benchmarks),
            'avg_execution_time_ms': sum(execution_times) / len(execution_times),
            'min_execution_time_ms': min(execution_times),
            'max_execution_time_ms': max(execution_times),
            'avg_memory_usage_mb': sum(memory_usage) / len(memory_usage),
            'min_memory_usage_mb': min(memory_usage),
            'max_memory_usage_mb': max(memory_usage),
            'total_time_ms': data.get('total_time_ms', 0),
            'version': data.get('version', 'unknown')
        }
    
    # Performance comparisons by benchmark type
    benchmark_types = ['GHZ', 'Random', 'QFT']
    
    for bench_type in benchmark_types:
        analysis['comparisons'][bench_type] = {}
        
        for library, data in results.items():
            if 'results' not in data:
                continue
                
            # Filter benchmarks by type
            type_benchmarks = [b for b in data['results'] if bench_type in b['name']]
            
            if type_benchmarks:
                times = [b['execution_time_ms'] for b in type_benchmarks]
                analysis['comparisons'][bench_type][library] = {
                    'count': len(type_benchmarks),
                    'avg_time_ms': sum(times) / len(times),
                    'min_time_ms': min(times),
                    'max_time_ms': max(times)
                }
    
    # Find best performers
    if analysis['summary']:
        # Fastest average execution time
        fastest_lib = min(analysis['summary'].items(), 
                         key=lambda x: x[1]['avg_execution_time_ms'])
        analysis['best_performers']['fastest_avg'] = {
            'library': fastest_lib[0],
            'time_ms': fastest_lib[1]['avg_execution_time_ms']
        }
        
        # Most memory efficient
        most_efficient_lib = min(analysis['summary'].items(), 
                               key=lambda x: x[1]['avg_memory_usage_mb'])
        analysis['best_performers']['most_memory_efficient'] = {
            'library': most_efficient_lib[0],
            'memory_mb': most_efficient_lib[1]['avg_memory_usage_mb']
        }
    
    return analysis

def generate_report(results: Dict[str, Any], analysis: Dict[str, Any]) -> str:
    """Generate a text report"""
    report = []
    report.append("=" * 80)
    report.append("LogosQ Quantum Computing Benchmark Report")
    report.append("=" * 80)
    report.append(f"Generated: {analysis['timestamp']}")
    report.append("")
    
    # Libraries tested
    report.append("Libraries Tested:")
    for library, data in results.items():
        version = data.get('version', 'unknown')
        total_time = data.get('total_time_ms', 0)
        report.append(f"  - {library} (v{version}) - Total time: {total_time:.2f}ms")
    report.append("")
    
    # Summary statistics
    report.append("Summary Statistics:")
    report.append("-" * 40)
    for library, stats in analysis['summary'].items():
        report.append(f"\n{library}:")
        report.append(f"  Benchmarks: {stats['total_benchmarks']}")
        report.append(f"  Avg execution time: {stats['avg_execution_time_ms']:.2f}ms")
        report.append(f"  Avg memory usage: {stats['avg_memory_usage_mb']:.2f}MB")
        report.append(f"  Range: {stats['min_execution_time_ms']:.2f}ms - {stats['max_execution_time_ms']:.2f}ms")
    
    report.append("")
    
    # Best performers
    if 'best_performers' in analysis:
        report.append("Best Performers:")
        report.append("-" * 40)
        if 'fastest_avg' in analysis['best_performers']:
            fastest = analysis['best_performers']['fastest_avg']
            report.append(f"Fastest (avg): {fastest['library']} ({fastest['time_ms']:.2f}ms)")
        
        if 'most_memory_efficient' in analysis['best_performers']:
            efficient = analysis['best_performers']['most_memory_efficient']
            report.append(f"Most memory efficient: {efficient['library']} ({efficient['memory_mb']:.2f}MB)")
        
        report.append("")
    
    # Benchmark type comparisons
    report.append("Benchmark Type Comparisons:")
    report.append("-" * 40)
    for bench_type, comparisons in analysis['comparisons'].items():
        if comparisons:
            report.append(f"\n{bench_type} Benchmarks:")
            for library, stats in comparisons.items():
                report.append(f"  {library}: {stats['avg_time_ms']:.2f}ms avg ({stats['count']} tests)")
    
    return "\n".join(report)

def main():
    print("Combining benchmark results...")
    
    # Load all benchmark results
    results = load_benchmark_results()
    
    if not results:
        print("No benchmark results found!")
        sys.exit(1)
    
    # Analyze results
    analysis = analyze_results(results)
    
    # Save combined results
    combined_data = {
        'results': results,
        'analysis': analysis
    }
    
    output_file = '../results/combined_results.json'
    with open(output_file, 'w') as f:
        json.dump(combined_data, f, indent=2)
    
    print(f"Combined results saved to {output_file}")
    
    # Generate and save report
    report = generate_report(results, analysis)
    report_file = '../results/benchmark_report.txt'
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"Benchmark report saved to {report_file}")
    
    # Print summary to console
    print("\n" + "=" * 50)
    print("BENCHMARK SUMMARY")
    print("=" * 50)
    
    for library, stats in analysis['summary'].items():
        print(f"{library:12}: {stats['avg_execution_time_ms']:8.2f}ms avg, {stats['avg_memory_usage_mb']:6.2f}MB avg")
    
    if 'best_performers' in analysis:
        print("\nBest Performers:")
        if 'fastest_avg' in analysis['best_performers']:
            fastest = analysis['best_performers']['fastest_avg']
            print(f"  Fastest: {fastest['library']} ({fastest['time_ms']:.2f}ms)")
        if 'most_memory_efficient' in analysis['best_performers']:
            efficient = analysis['best_performers']['most_memory_efficient']
            print(f"  Most efficient: {efficient['library']} ({efficient['memory_mb']:.2f}MB)")

if __name__ == "__main__":
    main()