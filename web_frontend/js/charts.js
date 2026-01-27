function renderRoiChart(ctx, data, username) {
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => d.date),
            datasets: [{
                label: 'ROI (%)',
                data: data.map(d => d.roi),
                borderColor: 'rgb(59, 130, 246)', // blue-500
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                tension: 0.1,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: 'ROI %'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Дата'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: `ROI History: ${username}`
                }
            }
        }
    });
}
