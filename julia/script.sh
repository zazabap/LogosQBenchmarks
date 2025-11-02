#!/bin/bash

echo "Updating Yao.jl and related packages..."

# Create a Julia script to update packages
cat > /tmp/update_yao.jl << 'EOF'
using Pkg

println("Updating packages...")
Pkg.update()

# Ensure we have the latest Yao ecosystem
println("\nInstalling latest Yao.jl ecosystem...")
Pkg.add("Yao")
Pkg.add("YaoBlocks")
Pkg.add("YaoArrayRegister")
Pkg.add("YaoAPI")
Pkg.add("BenchmarkTools")
Pkg.add("JSON")

# Check versions
println("\nInstalled versions:")
for pkg in ["Yao", "YaoBlocks", "YaoArrayRegister", "YaoAPI", "BenchmarkTools", "JSON"]
    deps = Pkg.dependencies()
    uuid = nothing
    for (u, d) in deps
        if d.name == pkg
            uuid = u
            break
        end
    end
    
    if uuid !== nothing
        ver = deps[uuid].version
        println("$pkg: v$ver")
    else
        println("$pkg: not installed")
    end
end

# Check if QFT is built-in
println("\nChecking for built-in QFT function...")
try
    using YaoBlocks
    # Try to access qft method if it exists
    @show methods(qft)
    println("✓ Built-in QFT function found")
catch e
    println("✗ Built-in QFT function not found, will keep custom implementation")
end
EOF

# Make executable and run
chmod +x /tmp/update_yao.jl
julia /tmp/update_yao.jl