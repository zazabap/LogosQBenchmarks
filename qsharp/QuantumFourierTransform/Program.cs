using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Quantum.Simulation.Core;
using Microsoft.Quantum.Simulation.Simulators;

namespace QuantumFourierTransform
{
    class Program
    {
        static async Task Main(string[] args)
        {
            try
            {
                // Parse Environment Variables or Args
                string outputDir = Environment.GetEnvironmentVariable("QFT_OUTPUT_DIR") ?? ".";
                string outputFile = Path.Combine(outputDir, "qsharp_qft_benchmark_results.json");
                
                // Default range if not specified: 4 to 12, step 1
                int minQubits = 4;
                int maxQubits = 12;
                int step = 1;
                
                if (args.Length >= 1) int.TryParse(args[0], out minQubits);
                if (args.Length >= 2) int.TryParse(args[1], out maxQubits);
                if (args.Length >= 3) int.TryParse(args[2], out step);

                // Validate arguments
                if (minQubits <= 0 || maxQubits < minQubits || step <= 0)
                {
                    Console.Error.WriteLine("Error: Invalid qubit range. Ensure: start > 0, end >= start, step > 0");
                    Environment.Exit(1);
                }

                var results = new List<BenchmarkResult>();
                var sim = new QuantumSimulator();

                Console.WriteLine($"Running QFT benchmark from {minQubits} to {maxQubits} qubits (step: {step})...");

                // Warmup
                await RunQFT.Run(sim, 4);

                for (int n = minQubits; n <= maxQubits; n += step)
                {
                    Console.Write($"  Testing {n} qubits... ");
                    
                    // Measure runtime
                    // Run multiple iterations for better accuracy
                    int iterations = (n <= 8) ? 100 : (n <= 10 ? 20 : 5);
                    if (n > 20) iterations = 1;

                    var times = new List<double>();
                    
                    // Force GC to get cleaner memory reading
                    GC.Collect();
                    GC.WaitForPendingFinalizers();
                    long memBefore = System.Diagnostics.Process.GetCurrentProcess().PrivateMemorySize64;

                    for (int i = 0; i < iterations; i++)
                    {
                        var sw = System.Diagnostics.Stopwatch.StartNew();
                        await RunQFT.Run(sim, n);
                        sw.Stop();
                        times.Add(sw.Elapsed.TotalMilliseconds);
                    }
                    
                    long memAfter = System.Diagnostics.Process.GetCurrentProcess().PrivateMemorySize64;
                    double memoryMb = (memAfter - memBefore) / (1024.0 * 1024.0);
                    // Memory measurement in managed runtimes is tricky. This is a rough delta.
                    // If delta is negative or zero (GC happened), assume minimal or use peak.
                    if (memoryMb < 0) memoryMb = 0;

                    double avgTime = times.Average();
                    double stdDev = Math.Sqrt(times.Sum(t => Math.Pow(t - avgTime, 2)) / times.Count);

                    Console.WriteLine($"{avgTime:F2} ms");

                    results.Add(new BenchmarkResult
                    {
                        n_qubits = n,
                        execution_time_ms = avgTime,
                        std_deviation_ms = stdDev,
                        memory_mb = memoryMb
                    });
                }

                string jsonString = JsonSerializer.Serialize(results, new JsonSerializerOptions { WriteIndented = true });
                File.WriteAllText(outputFile, jsonString);
                Console.WriteLine($"Results saved to {outputFile}");
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"Error: {ex}");
                Environment.Exit(1);
            }
        }
    }

    class BenchmarkResult
    {
        public int n_qubits { get; set; }
        public double execution_time_ms { get; set; }
        public double std_deviation_ms { get; set; }
        public double memory_mb { get; set; }
    }
}

