document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('simulationForm');
    if (form) {
        form.addEventListener('submit', handleSimulation);
    }
});

let raceChartInstance = null;

async function handleSimulation(e) {
    e.preventDefault();

    // UI Loading State
    const loader = document.getElementById('loader');
    const resultsPanel = document.getElementById('resultsPanel');
    const btn = e.target.querySelector('button');

    loader.style.display = 'block';
    btn.disabled = true;
    resultsPanel.style.display = 'none';

    // Gather Data
    const data = {
        driver: document.getElementById('driver').value,
        track: document.getElementById('track').value,
        compound: document.getElementById('compound').value,
        weather: document.getElementById('weather').value,
        laps: parseInt(document.getElementById('laps').value)
    };

    try {
        const response = await fetch('/api/simulate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) throw new Error("Simulation failed");

        const result = await response.json();

        // Artificial Delay for "Simulation" effect
        setTimeout(() => {
            renderResults(result);
            loader.style.display = 'none';
            btn.disabled = false;
        }, 800);

    } catch (error) {
        console.error(error);
        alert("Simulation failed. Check console.");
        loader.style.display = 'none';
        btn.disabled = false;
    }
}

function renderResults(data) {
    const resultsPanel = document.getElementById('resultsPanel');
    resultsPanel.style.display = 'block';

    // Update Stats
    document.getElementById('finalPos').innerText = `P${data.final_position}`;
    document.getElementById('avgLap').innerText = data.avg_lap_time;
    document.getElementById('totalTime').innerText = data.total_time;
    document.getElementById('strategyText').innerText = data.pit_strategy;

    // Render Chart
    const ctx = document.getElementById('raceChart').getContext('2d');

    if (raceChartInstance) {
        raceChartInstance.destroy();
    }

    const labels = Array.from({ length: data.lap_data.length }, (_, i) => i + 1);

    raceChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Lap Time (s)',
                    data: data.lap_data,
                    borderColor: '#00f0ff',
                    backgroundColor: 'rgba(0, 240, 255, 0.1)',
                    yAxisID: 'y',
                    tension: 0.4
                },
                {
                    label: 'Tyre Health (%)',
                    data: data.tyre_data,
                    borderColor: '#e10600',
                    backgroundColor: 'rgba(225, 6, 0, 0.1)',
                    yAxisID: 'y1',
                    tension: 0.1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                x: {
                    grid: { color: '#333' },
                    ticks: { color: '#888' }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    grid: { color: '#333' },
                    ticks: { color: '#00f0ff' },
                    title: { display: true, text: 'Lap Time (s)', color: '#888' }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    grid: { drawOnChartArea: false },
                    ticks: { color: '#e10600' },
                    title: { display: true, text: 'Tyre (%)', color: '#888' },
                    min: 0,
                    max: 100
                }
            },
            plugins: {
                legend: {
                    labels: { color: 'white' }
                }
            }
        }
    });

    resultsPanel.scrollIntoView({ behavior: 'smooth' });
}
