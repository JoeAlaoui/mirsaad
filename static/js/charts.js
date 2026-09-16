/**
 * Wrapper léger autour de Chart.js.
 * Dans une SPA, innerHTML est régulièrement remplacé : les instances Chart.js
 * pointant vers des <canvas> détachés doivent être détruites explicitement,
 * sinon elles fuient en mémoire et Chart.js râle sur des canvas invalides.
 */
const Charts = {
    _instances: {},

    palette: ["#0f4c81", "#1e7a4c", "#b06000", "#8a6d00", "#7a3ea1", "#b3261e", "#4b5568", "#1c8fa6"],

    criticitePalette: {
        "Critique": "#b3261e",
        "Élevée": "#b06000",
        "Moyenne": "#8a6d00",
        "Faible": "#4b5568",
    },

    destroyAll() {
        Object.values(this._instances).forEach((chart) => chart.destroy());
        this._instances = {};
    },

    _baseOptions(extra = {}) {
        return Object.assign(
            {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 700, easing: "easeOutQuart" },
                plugins: {
                    legend: { labels: { font: { family: "Inter", size: 11 }, color: "#4b5568" } },
                },
            },
            extra
        );
    },

    doughnut(canvasId, labels, values, colors) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;
        if (this._instances[canvasId]) this._instances[canvasId].destroy();

        this._instances[canvasId] = new Chart(ctx, {
            type: "doughnut",
            data: {
                labels,
                datasets: [{ data: values, backgroundColor: colors || this.palette, borderWidth: 2, borderColor: "#ffffff" }],
            },
            options: this._baseOptions({
                cutout: "62%",
                plugins: {
                    legend: { position: "right", labels: { font: { family: "Inter", size: 11 }, color: "#4b5568", boxWidth: 12 } },
                },
            }),
        });
    },

    bar(canvasId, labels, values, color) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;
        if (this._instances[canvasId]) this._instances[canvasId].destroy();

        this._instances[canvasId] = new Chart(ctx, {
            type: "bar",
            data: {
                labels,
                datasets: [{ data: values, backgroundColor: color || "#0f4c81", borderRadius: 4, maxBarThickness: 42 }],
            },
            options: this._baseOptions({
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false }, ticks: { font: { family: "Inter", size: 11 }, color: "#4b5568" } },
                    y: { beginAtZero: true, ticks: { precision: 0, font: { family: "Inter", size: 11 }, color: "#4b5568" }, grid: { color: "#eef1f6" } },
                },
            }),
        });
    },

    horizontalBar(canvasId, labels, values, color) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;
        if (this._instances[canvasId]) this._instances[canvasId].destroy();

        this._instances[canvasId] = new Chart(ctx, {
            type: "bar",
            data: {
                labels,
                datasets: [{ data: values, backgroundColor: color || "#0f4c81", borderRadius: 4, maxBarThickness: 22 }],
            },
            options: this._baseOptions({
                indexAxis: "y",
                plugins: { legend: { display: false } },
                scales: {
                    x: { beginAtZero: true, ticks: { precision: 0, font: { family: "Inter", size: 11 }, color: "#4b5568" }, grid: { color: "#eef1f6" } },
                    y: { grid: { display: false }, ticks: { font: { family: "Inter", size: 11 }, color: "#4b5568" } },
                },
            }),
        });
    },
};
