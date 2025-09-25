// Global variables
let benchmarkData = {};
let memoryData = {};

// Color scheme for different libraries
const colors = {
    'LogosQ': '#667eea',
    'Yao.jl': '#52c41a', 
    'C++': '#fa541c',
    'PennyLane': '#13c2c2',
    'Qiskit': '#722ed1'
};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', async function() {
    await loadData();
    initializeDashboard();
});

// Tab switching
function showTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all buttons
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
    });
    
    // Show selected tab and mark button as active
    document.getElementById(tabName).classList.add('active');
    event.target.classList.add('active');
    
    // Load appropriate chart for the tab
    switch(tabName) {
        case 'performance':
            updatePerformanceChart();
            break;
        case 'memory':
            updateMemoryChart();
            updateMemoryScalingChart();
            break;
        case 'scalability':
            updateScalabilityChart();
            updateDepthChart();
            break;
        case 'summary':
            updateSummaryTab();
            break;
    }
}

// Load data from API
async function loadData() {
    try {
        // Show loading indicator
        showLoading();
        
        // Load benchmark results
        const resultsResponse = await fetch('/api/results');
        benchmarkData = await resultsResponse.json();
        
        // Load memory data
        const memoryResponse = await fetch('/api/memory');
        memoryData = await memoryResponse.json();
        
        console.log('Loaded benchmark data:', benchmarkData);
        console.log('Loaded memory data:', memoryData);
        
    } catch (error) {
        console.error('Error loading data:', error);
        showError('Failed to load benchmark data. Please ensure benchmarks have been run.');
    }
}

// Show loading indicator
function showLoading() {
    const loadingHTML = '<div class="loading"><div class="spinner"></div>Loading benchmark data...</div>';
    document.getElementById('performanceChart').innerHTML = loadingHTML;
}

// Show error message
function showError(message) {
    const errorHTML = `<div class="error">Error: ${message}</div>`;
    document.getElementById('performanceChart').innerHTML = errorHTML;
}

// Initialize dashboard with default view
function initializeDashboard() {
    updatePerformanceChart();
}

// Update performance chart
function updatePerformanceChart() {
    const container = d3.select('#performanceChart');
    container.selectAll('*').remove();
    
    if (Object.keys(benchmarkData).length === 0) {
        container.append('div').attr('class', 'loading').text('No benchmark data available');
        return;
    }
    
    const logScale = document.getElementById('logScale').checked;
    const filter = document.getElementById('benchmarkFilter').value;
    
    // Prepare data
    const data = [];
    Object.entries(benchmarkData).forEach(([library, results]) => {
        if (results && results.results && Array.isArray(results.results)) {
            results.results.forEach(result => {
                if (filter === 'all' || result.name.includes(filter)) {
                    data.push({
                        library: library,
                        name: result.name,
                        num_qubits: result.num_qubits,
                        execution_time: result.execution_time_ms,
                        memory_usage: result.memory_usage_mb,
                        num_gates: result.num_gates
                    });
                }
            });
        }
    });
    
    if (data.length === 0) {
        container.append('div').text('No data available for selected filter');
        return;
    }
    
    // Set up dimensions
    const margin = {top: 20, right: 120, bottom: 60, left: 80};
    const width = 800 - margin.left - margin.right;
    const height = 400 - margin.top - margin.bottom;
    
    const svg = container.append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom);
    
    const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Set up scales
    const xScale = d3.scaleBand()
        .domain(data.map(d => `${d.name}`))
        .range([0, width])
        .padding(0.1);
    
    const yScale = logScale ? 
        d3.scaleLog().domain([1, d3.max(data, d => d.execution_time)]).range([height, 0]) :
        d3.scaleLinear().domain([0, d3.max(data, d => d.execution_time)]).range([height, 0]);
    
    // Create tooltip
    const tooltip = d3.select('body').append('div')
        .attr('class', 'tooltip')
        .style('opacity', 0);
    
    // Draw bars
    g.selectAll('.bar')
        .data(data)
        .enter().append('rect')
        .attr('class', 'bar')
        .attr('x', d => xScale(d.name))
        .attr('y', d => yScale(d.execution_time))
        .attr('width', xScale.bandwidth())
        .attr('height', d => height - yScale(d.execution_time))
        .attr('fill', d => colors[d.library] || '#666')
        .on('mouseover', function(event, d) {
            tooltip.transition().duration(200).style('opacity', .9);
            tooltip.html(`
                <strong>${d.library}</strong><br/>
                ${d.name}<br/>
                Time: ${d.execution_time.toFixed(2)}ms<br/>
                Qubits: ${d.num_qubits}<br/>
                Gates: ${d.num_gates}<br/>
                Memory: ${d.memory_usage.toFixed(2)}MB
            `)
            .style('left', (event.pageX + 10) + 'px')
            .style('top', (event.pageY - 28) + 'px');
        })
        .on('mouseout', function() {
            tooltip.transition().duration(500).style('opacity', 0);
        });
    
    // Add axes
    g.append('g')
        .attr('class', 'axis')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(xScale))
        .selectAll('text')
        .style('text-anchor', 'end')
        .attr('dx', '-.8em')
        .attr('dy', '.15em')
        .attr('transform', 'rotate(-45)');
    
    g.append('g')
        .attr('class', 'axis')
        .call(d3.axisLeft(yScale));
    
    // Add axis labels
    g.append('text')
        .attr('class', 'axis-label')
        .attr('transform', 'rotate(-90)')
        .attr('y', 0 - margin.left)
        .attr('x', 0 - (height / 2))
        .attr('dy', '1em')
        .style('text-anchor', 'middle')
        .text('Execution Time (ms)');
    
    // Add legend
    const legend = g.append('g')
        .attr('class', 'legend')
        .attr('transform', `translate(${width + 20}, 20)`);
    
    const libraries = [...new Set(data.map(d => d.library))];
    legend.selectAll('.legend-item')
        .data(libraries)
        .enter().append('g')
        .attr('class', 'legend-item')
        .attr('transform', (d, i) => `translate(0, ${i * 20})`)
        .each(function(d) {
            const item = d3.select(this);
            item.append('rect')
                .attr('width', 15)
                .attr('height', 15)
                .attr('fill', colors[d] || '#666');
            item.append('text')
                .attr('x', 20)
                .attr('y', 12)
                .text(d);
        });
}

// Update memory chart
function updateMemoryChart() {
    const container = d3.select('#memoryChart');
    container.selectAll('*').remove();
    
    if (Object.keys(memoryData).length === 0) {
        container.append('div').text('No memory data available');
        return;
    }
    
    // Implementation for memory timeline chart
    const margin = {top: 20, right: 120, bottom: 40, left: 60};
    const width = 800 - margin.left - margin.right;
    const height = 300 - margin.top - margin.bottom;
    
    const svg = container.append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom);
    
    const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Add placeholder for memory timeline
    g.append('text')
        .attr('x', width / 2)
        .attr('y', height / 2)
        .attr('text-anchor', 'middle')
        .text('Memory usage timeline will be displayed here');
}

// Update memory scaling chart
function updateMemoryScalingChart() {
    const container = d3.select('#memoryScalingChart');
    container.selectAll('*').remove();
    
    if (Object.keys(benchmarkData).length === 0) {
        container.append('div').text('No benchmark data available');
        return;
    }
    
    // Prepare data for memory vs qubits
    const data = [];
    Object.entries(benchmarkData).forEach(([library, results]) => {
        if (results && results.results && Array.isArray(results.results)) {
            results.results.forEach(result => {
                data.push({
                    library: library,
                    num_qubits: result.num_qubits,
                    memory_usage: result.memory_usage_mb
                });
            });
        }
    });
    
    // Set up dimensions
    const margin = {top: 20, right: 120, bottom: 60, left: 80};
    const width = 800 - margin.left - margin.right;
    const height = 400 - margin.top - margin.bottom;
    
    const svg = container.append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom);
    
    const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Set up scales
    const xScale = d3.scaleLinear()
        .domain(d3.extent(data, d => d.num_qubits))
        .range([0, width]);
    
    const yScale = d3.scaleLinear()
        .domain([0, d3.max(data, d => d.memory_usage)])
        .range([height, 0]);
    
    // Group data by library
    const nestedData = d3.group(data, d => d.library);
    
    // Draw lines for each library
    const line = d3.line()
        .x(d => xScale(d.num_qubits))
        .y(d => yScale(d.memory_usage));
    
    nestedData.forEach((values, library) => {
        const sortedValues = values.sort((a, b) => a.num_qubits - b.num_qubits);
        
        g.append('path')
            .datum(sortedValues)
            .attr('class', 'line')
            .attr('d', line)
            .attr('stroke', colors[library] || '#666');
        
        g.selectAll(`.dot-${library}`)
            .data(sortedValues)
            .enter().append('circle')
            .attr('class', `dot dot-${library}`)
            .attr('cx', d => xScale(d.num_qubits))
            .attr('cy', d => yScale(d.memory_usage))
            .attr('r', 4)
            .attr('stroke', colors[library] || '#666');
    });
    
    // Add axes
    g.append('g')
        .attr('class', 'axis')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(xScale));
    
    g.append('g')
        .attr('class', 'axis')
        .call(d3.axisLeft(yScale));
    
    // Add axis labels
    g.append('text')
        .attr('class', 'axis-label')
        .attr('x', width / 2)
        .attr('y', height + margin.bottom - 10)
        .style('text-anchor', 'middle')
        .text('Number of Qubits');
    
    g.append('text')
        .attr('class', 'axis-label')
        .attr('transform', 'rotate(-90)')
        .attr('y', 0 - margin.left)
        .attr('x', 0 - (height / 2))
        .attr('dy', '1em')
        .style('text-anchor', 'middle')
        .text('Memory Usage (MB)');
}

// Placeholder functions for other charts
function updateScalabilityChart() {
    const container = d3.select('#scalabilityChart');
    container.selectAll('*').remove();
    container.append('div').text('Scalability analysis chart will be implemented here');
}

function updateDepthChart() {
    const container = d3.select('#depthChart');
    container.selectAll('*').remove();
    container.append('div').text('Circuit depth analysis chart will be implemented here');
}

function updateSummaryTab() {
    updateLibraryComparison();
    updatePerformanceRanking();
    updateMemoryEfficiency();
    updateUseCases();
}

function updateLibraryComparison() {
    const container = d3.select('#libraryComparison');
    container.selectAll('*').remove();
    
    if (Object.keys(benchmarkData).length === 0) {
        container.append('div').text('No data available');
        return;
    }
    
    const summary = Object.entries(benchmarkData).map(([library, results]) => {
        if (!results || !results.results || !Array.isArray(results.results)) return null;
        
        const avgTime = results.results.reduce((sum, r) => sum + r.execution_time_ms, 0) / results.results.length;
        const avgMemory = results.results.reduce((sum, r) => sum + r.memory_usage_mb, 0) / results.results.length;
        
        return {
            library,
            avgTime: avgTime.toFixed(2),
            avgMemory: avgMemory.toFixed(2),
            totalTests: results.results.length
        };
    }).filter(Boolean);
    
    const table = container.append('table').style('width', '100%');
    const header = table.append('thead').append('tr');
    header.selectAll('th')
        .data(['Library', 'Avg Time (ms)', 'Avg Memory (MB)', 'Tests'])
        .enter().append('th').text(d => d);
    
    const tbody = table.append('tbody');
    tbody.selectAll('tr')
        .data(summary)
        .enter().append('tr')
        .selectAll('td')
        .data(d => [d.library, d.avgTime, d.avgMemory, d.totalTests])
        .enter().append('td').text(d => d);
}

function updatePerformanceRanking() {
    const container = d3.select('#performanceRanking');
    container.selectAll('*').remove();
    container.append('div').text('Performance ranking analysis will be displayed here');
}

function updateMemoryEfficiency() {
    const container = d3.select('#memoryEfficiency');
    container.selectAll('*').remove();
    container.append('div').text('Memory efficiency analysis will be displayed here');
}

function updateUseCases() {
    const container = d3.select('#useCases');
    container.selectAll('*').remove();
    
    const useCases = [
        { library: 'LogosQ', useCase: 'High-performance quantum simulation' },
        { library: 'Yao.jl', useCase: 'Research and algorithm development' },
        { library: 'C++', useCase: 'Low-level optimization and performance' },
        { library: 'PennyLane', useCase: 'Quantum machine learning' },
        { library: 'Qiskit', useCase: 'General-purpose quantum computing' }
    ];
    
    const list = container.append('ul');
    list.selectAll('li')
        .data(useCases)
        .enter().append('li')
        .html(d => `<strong>${d.library}:</strong> ${d.useCase}`);
}