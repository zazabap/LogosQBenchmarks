using System;
using System.IO;
using System.Linq;
using System.Numerics;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Quantum.Simulation.Core;
using Microsoft.Quantum.Simulation.Simulators;

namespace XYZHeisenberg
{
    class Program
    {
        static async Task Main(string[] args)
        {
            try
            {
                // Parse Environment Variables
                int numQubits = int.Parse(Environment.GetEnvironmentVariable("XYZ_QUBITS") ?? "4");
                int timeSteps = int.Parse(Environment.GetEnvironmentVariable("XYZ_STEPS") ?? "10");
                double dt = double.Parse(Environment.GetEnvironmentVariable("XYZ_DT") ?? "0.1");
                double jx = double.Parse(Environment.GetEnvironmentVariable("XYZ_JX") ?? "1.0");
                double jy = double.Parse(Environment.GetEnvironmentVariable("XYZ_JY") ?? "1.0");
                double jz = double.Parse(Environment.GetEnvironmentVariable("XYZ_JZ") ?? "1.0");
                double field = double.Parse(Environment.GetEnvironmentVariable("XYZ_FIELD") ?? "0.0");
                string outputFile = Environment.GetEnvironmentVariable("XYZ_OUTPUT_FILE") ?? "qsharp_xyz.json";

                var sim = new QuantumSimulator();
                
                // Clean up previous dump
                string dumpFile = "state_dump.txt";
                if (File.Exists(dumpFile)) File.Delete(dumpFile);

                var stopwatch = System.Diagnostics.Stopwatch.StartNew();
                
                // Run Q# operation
                await RunTimeEvolution.Run(sim, numQubits, jx, jy, jz, field, timeSteps, dt);
                
                stopwatch.Stop();
                double runtimeMs = stopwatch.Elapsed.TotalMilliseconds;

                // Read State Vector
                Complex[] finalState = ReadStateVector(dumpFile, numQubits);
                
                // Initial State |11...1> (all spins down in some conventions, or up? Check Qiskit.)
                // Qiskit: initial_state_vector[-1] = 1.0. This is |11...1>.
                // Q#: We initialized with X on all qubits. |00..0> --X--> |11..1>.
                // So initial state is index 2^N - 1.
                Complex[] initialState = new Complex[1 << numQubits];
                initialState[(1 << numQubits) - 1] = 1.0;

                double initialEnergy = CalculateEnergy(initialState, numQubits, jx, jy, jz, field);
                double finalEnergy = CalculateEnergy(finalState, numQubits, jx, jy, jz, field);
                double energyChange = finalEnergy - initialEnergy;
                
                // Operations count
                int numInteractions = (numQubits > 1) ? 3 * (numQubits - 1) : 0;
                int numFieldTerms = (Math.Abs(field) > 1e-10) ? numQubits : 0;
                int numOperations = timeSteps * (numInteractions + numFieldTerms) + numQubits;

                var result = new
                {
                    framework = "Q# (.NET)",
                    qubits = numQubits,
                    time_steps = timeSteps,
                    dt = dt,
                    jx = jx,
                    jy = jy,
                    jz = jz,
                    external_field = field,
                    initial_energy = initialEnergy,
                    final_energy = finalEnergy,
                    energy_change = energyChange,
                    runtime_ms = runtimeMs,
                    num_operations = numOperations
                };

                string jsonString = JsonSerializer.Serialize(result, new JsonSerializerOptions { WriteIndented = true });
                File.WriteAllText(outputFile, jsonString);
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"Error running Q# benchmark: {ex}");
                Environment.Exit(1);
            }
        }

        static Complex[] ReadStateVector(string filename, int numQubits)
        {
             var state = new Complex[1 << numQubits];
             if (!File.Exists(filename)) return state;

             foreach (var line in File.ReadLines(filename))
             {
                 var trim = line.Trim();
                 if (!trim.StartsWith("|")) continue;
                 
                 int endKet = trim.IndexOf("⟩");
                 if (endKet == -1) endKet = trim.IndexOf(">");
                 if (endKet == -1) continue;
                 
                 string basisStr = trim.Substring(1, endKet - 1);
                 
                 int index = 0;
                 try {
                     // Try binary parsing
                     index = Convert.ToInt32(basisStr, 2);
                 } catch {
                     try { index = int.Parse(basisStr); } catch { continue; }
                 }
                 
                 if (index >= state.Length) continue;

                 string valPart = trim.Substring(endKet + 1).Trim(); 
                 // Format: "0.7071... + 0 i" or "0.7071... - 0.5 i"
                 // Often followed by "==" or similar in DumpMachine output
                 int endVal = valPart.IndexOf("==");
                 if (endVal != -1) valPart = valPart.Substring(0, endVal).Trim();
                 
                 try {
                     // Normalize spaces
                     valPart = valPart.Replace("\t", " ");
                     var parts = valPart.Split(new[]{' '}, StringSplitOptions.RemoveEmptyEntries);
                     
                     // Expect [REAL, "+", IMAG, "i"] or [REAL, "+", IMAG, "i"]
                     // Example: -0.989992 + 0.141120 i
                     
                     if (parts.Length >= 4 && parts[3] == "i")
                     {
                         double re = double.Parse(parts[0]);
                         double im = double.Parse(parts[2]);
                         // The sign is usually in parts[2] if explicit negative?
                         // Actually output is: "RE + IM i". IM can be negative like "-0.0000".
                         // The separator is always "+"?
                         // Let's check if parts[1] is "+" or "-"
                         
                         if (parts[1] == "-") im = -im; // If format is "RE - IM i"
                         
                         state[index] = new Complex(re, im);
                     }
                 } catch {}
             }
             return state;
        }

        static double CalculateEnergy(Complex[] state, int numQubits, double jx, double jy, double jz, double h)
        {
            double sumXX = 0;
            double sumYY = 0;
            double sumZZ = 0;
            double sumZ = 0;
            int dim = 1 << numQubits;
            
            for (int idx = 0; idx < dim; idx++)
            {
                Complex amp = state[idx];
                if (amp == Complex.Zero) continue;
                double magSq = amp.Magnitude * amp.Magnitude; // Manual sq to match type

                // Z terms
                if (Math.Abs(h) > 1e-9) {
                    double zVal = 0;
                    for (int k=0; k<numQubits; k++) {
                        zVal += ((idx >> k) & 1) == 0 ? 1.0 : -1.0;
                    }
                    sumZ += magSq * zVal;
                }
                
                // ZZ terms
                if (Math.Abs(jz) > 1e-9) {
                     for (int k=0; k<numQubits-1; k++) {
                         int b1 = (idx >> k) & 1;
                         int b2 = (idx >> (k+1)) & 1;
                         double val = (b1 == b2) ? 1.0 : -1.0;
                         sumZZ += magSq * val;
                     }
                }
                
                // XX terms
                if (Math.Abs(jx) > 1e-9) {
                    for (int k=0; k<numQubits-1; k++) {
                         int mask = (1 << k) | (1 << (k+1));
                         int flipped = idx ^ mask;
                         if (flipped < dim) {
                             sumXX += (Complex.Conjugate(amp) * state[flipped]).Real;
                         }
                    }
                }
                
                // YY terms
                if (Math.Abs(jy) > 1e-9) {
                     for (int k=0; k<numQubits-1; k++) {
                         int mask = (1 << k) | (1 << (k+1));
                         int flipped = idx ^ mask;
                         int b1 = (idx >> k) & 1;
                         int b2 = (idx >> (k+1)) & 1;
                         double factor = (b1 != b2) ? 1.0 : -1.0; 
                         if (flipped < dim) {
                             sumYY += (Complex.Conjugate(amp) * state[flipped] * factor).Real;
                         }
                     }
                }
            }
            
            return -jx * sumXX - jy * sumYY - jz * sumZZ - h * sumZ;
        }
    }
}

