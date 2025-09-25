cmake_minimum_required(VERSION 3.16)
project(cpp_quantum_benchmark)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find required packages
find_package(Eigen3 REQUIRED)

# Create the executable
add_executable(cpp_benchmark src/main.cpp src/quantum_simulator.cpp)

# Link libraries
target_link_libraries(cpp_benchmark Eigen3::Eigen)

# Compiler flags for optimization
target_compile_options(cpp_benchmark PRIVATE -O3 -march=native)

# Include directories
target_include_directories(cpp_benchmark PRIVATE src)