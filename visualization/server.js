const express = require('express');
const path = require('path');
const fs = require('fs');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 8080;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Serve static files
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// API endpoint to get benchmark results
app.get('/api/results', (req, res) => {
    const resultsDir = path.join(__dirname, '..', 'results');
    const results = {};
    
    try {
        // Read all result files
        const files = fs.readdirSync(resultsDir);
        
        for (const file of files) {
            if (file.endsWith('.json')) {
                const filePath = path.join(resultsDir, file);
                const content = fs.readFileSync(filePath, 'utf8');
                const library = file.replace('_results.json', '');
                results[library] = JSON.parse(content);
            }
        }
        
        res.json(results);
    } catch (error) {
        console.error('Error reading results:', error);
        res.status(500).json({ error: 'Failed to read benchmark results' });
    }
});

// API endpoint to get memory usage logs
app.get('/api/memory', (req, res) => {
    const logsDir = path.join(__dirname, '..', 'logs');
    const memoryData = {};
    
    try {
        const files = fs.readdirSync(logsDir);
        
        for (const file of files) {
            if (file.endsWith('_memory.log')) {
                const filePath = path.join(logsDir, file);
                const content = fs.readFileSync(filePath, 'utf8');
                const library = file.replace('_memory.log', '');
                
                // Parse memory log data
                const lines = content.split('\n').filter(line => line.trim());
                const memoryPoints = lines.map((line, index) => {
                    const parts = line.trim().split(/\s+/);
                    return {
                        time: index,
                        memory: parseFloat(parts[3]) || 0, // %MEM column
                        cpu: parseFloat(parts[4]) || 0     // %CPU column
                    };
                });
                
                memoryData[library] = memoryPoints;
            }
        }
        
        res.json(memoryData);
    } catch (error) {
        console.error('Error reading memory logs:', error);
        res.status(500).json({ error: 'Failed to read memory logs' });
    }
});

app.listen(PORT, () => {
    console.log(`LogosQ Benchmark Visualization Server running on port ${PORT}`);
    console.log(`Visit http://localhost:${PORT} to view the dashboard`);
});