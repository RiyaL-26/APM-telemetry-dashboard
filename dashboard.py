import sqlite3
from flask import Flask, jsonify, request
from flask_cors import CORS
from analytics import analyze_recent_logs

app = Flask(__name__)
CORS(app)
DB_FILE = "infrastructure_telemetry.db"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Enterprise Telemetry Matrix</title>
    <!-- 1. CHART.JS LIBRARY ADDED HERE IN HEAD -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #0b0f19;
            color: #e2e8f0;
            margin: 0;
            padding: 40px;
        }
        .container { max-width: 1000px; margin: 0 auto; }
        .header {
            border-bottom: 1px solid #1e293b;
            padding-bottom: 20px;
            margin-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        h1 { color: #22d3ee; margin: 0; font-size: 24px; letter-spacing: 1px; }
        .subtitle { color: #64748b; font-size: 11px; margin-top: 5px; }
        .status-badge {
            background-color: #0f172a;
            border: 1px solid #1e293b;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: bold;
            color: #34d399;
        }
        .grid { display: flex; gap: 20px; margin-bottom: 30px; }
        .card {
            background-color: #111827;
            border: 1px solid #1e293b;
            padding: 20px;
            border-radius: 10px;
            flex: 1;
        }
        .card-title { color: #64748b; font-size: 11px; text-transform: uppercase; margin: 0; font-weight: bold; }
        .card-value { font-size: 28px; font-weight: bold; margin-top: 10px; color: #f8fafc; }
        .panel {
            background-color: #111827;
            border: 1px solid #1e293b;
            border-radius: 10px;
            overflow: hidden;
        }
        .panel-header {
            background-color: #0f172a;
            padding: 15px 20px;
            border-bottom: 1px solid #1e293b;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 10px;
        }
        .panel-title { font-size: 13px; font-weight: bold; color: #cbd5e1; margin: 0; }
        .controls { display: flex; gap: 10px; align-items: center; }
        select {
            background-color: #1e293b;
            color: #cbd5e1;
            border: 1px solid #334155;
            padding: 6px 10px;
            border-radius: 4px;
            font-size: 11px;
            outline: none;
        }
        .btn {
            background-color: #22d3ee;
            color: #0f172a;
            border: none;
            padding: 6px 16px;
            font-size: 11px;
            font-weight: bold;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .btn:hover { opacity: 0.85; }
        .btn-toggle {
            background-color: #334155;
            color: #f8fafc;
        }
        table { width: 100%; border-collapse: collapse; text-align: left; font-size: 12px; }
        th { background-color: #0b0f19; color: #94a3b8; padding: 12px 20px; text-transform: uppercase; font-size: 10px; position: sticky; top: 0; }
        td { padding: 14px 20px; border-bottom: 1px solid #1e293b; color: #cbd5e1; font-family: monospace; }
        .badge {
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: bold;
        }
        .badge-CRITICAL { background-color: rgba(244,63,94,0.1); color: #f43f5e; border: 1px solid rgba(244,63,94,0.2); }
        .badge-WARNING { background-color: rgba(245,158,11,0.1); color: #f59e0b; border: 1px solid rgba(245,158,11,0.2); }
        .badge-INFO { background-color: rgba(148,163,184,0.1); color: #94a3b8; border: 1px solid #1e293b; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>⚡ INFRASTRUCTURE TELEMETRY PANEL</h1>
                <div class="subtitle">REAL-TIME APM METRICS CONTROL CONSOLE</div>
            </div>
            <div class="status-badge" id="live-indicator">● MATRIX STATUS: ONLINE</div>
        </div>

        <div id="alert-banner-container"></div>

        <div id="metrics-grid" class="grid"></div>

        <!-- 2. CHART CARD CONTAINER ADDED HERE ABOVE THE TABLE -->
        <div class="card" style="margin-bottom: 30px;">
            <div class="card-title">Live Ingestion Velocity (Total Log Packets)</div>
            <div style="height: 180px; margin-top: 10px;">
                <canvas id="telemetryChart"></canvas>
            </div>
        </div>

        <div class="panel">
            <div class="panel-header">
                <div class="panel-title">📜 Central Ingestion Log Streams</div>
                <div class="controls">
                    <select id="severity-filter" onchange="fetchLatestData()">
                        <option value="ALL">All Severities</option>
                        <option value="INFO">INFO</option>
                        <option value="WARNING">WARNING</option>
                        <option value="CRITICAL">CRITICAL</option>
                    </select>

                    <button id="toggle-poll-btn" onclick="toggleAutoRefresh()" class="btn btn-toggle">AUTO-REFRESH: ON</button>
                    <button onclick="fetchLatestData()" class="btn">REFRESH FEED</button>
                </div>
            </div>
            <div style="max-height: 400px; overflow-y: auto;">
                <table>
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>Component</th>
                            <th>Severity</th>
                            <th>Diagnostic Log Message</th>
                        </tr>
                    </thead>
                    <tbody id="log-table-body"></tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        let autoRefreshInterval = null;
        let telemetryChart = null;

        // 3. CHART INITIALIZATION FUNCTION
        function initChart() {
            const ctx = document.getElementById('telemetryChart').getContext('2d');
            telemetryChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Total Logs',
                        data: [],
                        borderColor: '#22d3ee',
                        backgroundColor: 'rgba(34, 211, 238, 0.1)',
                        fill: true,
                        tension: 0.3
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { grid: { color: '#1e293b' }, ticks: { color: '#64748b' } },
                        y: { grid: { color: '#1e293b' }, ticks: { color: '#64748b' }, beginAtZero: false }
                    },
                    plugins: { legend: { display: false } }
                }
            });
        }

        // 4. FUNCTION TO UPDATE CHART DATA
        function updateChart(totalLogs) {
            if (!telemetryChart) return;
            const now = new Date().toLocaleTimeString();
            
            if (telemetryChart.data.labels.length >= 10) {
                telemetryChart.data.labels.shift();
                telemetryChart.data.datasets[0].data.shift();
            }

            telemetryChart.data.labels.push(now);
            telemetryChart.data.datasets[0].data.push(totalLogs);
            telemetryChart.update();
        }

        async function checkAlerts() {
            try {
                const response = await fetch('/api/v1/dashboard/alerts');
                const data = await response.json();
                const container = document.getElementById('alert-banner-container');
                
                container.innerHTML = '';
                
                if (data.alerts && data.alerts.length > 0) {
                    data.alerts.forEach(alert => {
                        const alertDiv = document.createElement('div');
                        alertDiv.style.cssText = `
                            background-color: rgba(244, 63, 94, 0.15);
                            border: 1px solid #f43f5e;
                            color: #f43f5e;
                            padding: 12px 20px;
                            border-radius: 8px;
                            margin-bottom: 20px;
                            font-size: 13px;
                        `;
                        alertDiv.innerHTML = `<strong>🚨 ${alert.title}:</strong> ${alert.message}`;
                        container.appendChild(alertDiv);
                    });
                }
            } catch (err) {
                console.error("Alert check failed:", err);
            }
        }

        async function fetchLatestData() {
            checkAlerts();

            try {
                const severity = document.getElementById('severity-filter').value;
                const response = await fetch(`/api/v1/dashboard/metrics?severity=${severity}`);
                const data = await response.json();
                
                // Update Line Chart
                updateChart(data.total_logs);

                // Update Cards
                let htmlCards = '<div class="card"><div class="card-title">Total Packets Ingested</div><div class="card-value">' + data.total_logs + '</div></div>';
                htmlCards += '<div class="card"><div class="card-title">Critical Failures</div><div class="card-value" style="color: #f43f5e;">' + data.critical_logs + '</div></div>';
                
                let hColor = '#34d399';
                if (data.health < 50) hColor = '#f43f5e';
                else if (data.health < 90) hColor = '#f59e0b';
                
                htmlCards += '<div class="card"><div class="card-title">System Health Pool</div><div class="card-value" style="color: ' + hColor + ';">' + data.health.toFixed(2) + '%</div></div>';
                
                document.getElementById('metrics-grid').innerHTML = htmlCards;

                // Update Table
                const tbody = document.getElementById('log-table-body');
                tbody.innerHTML = '';
                
                if (data.logs.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:#64748b;">No log records match selected filters.</td></tr>';
                    return;
                }

                data.logs.forEach(log => {
                    let bClass = 'badge-INFO';
                    if (log.severity === 'CRITICAL') bClass = 'badge-CRITICAL';
                    if (log.severity === 'WARNING') bClass = 'badge-WARNING';
                    
                    let cleanTime = log.timestamp ? log.timestamp.substring(11, 19) : "00:00:00";
                    
                    let rowHtml = '<tr>';
                    rowHtml += '<td style="color: #475569;">' + cleanTime + '</td>';
                    rowHtml += '<td style="font-weight: bold; color: #22d3ee;">' + log.component + '</td>';
                    rowHtml += '<td><span class="badge ' + bClass + '">' + log.severity + '</span></td>';
                    rowHtml += '<td style="color: #cbd5e1;">' + log.message + '</td>';
                    rowHtml += '</tr>';
                    
                    tbody.innerHTML += rowHtml;
                });
            } catch (err) {
                console.error("Dashboard Sync Interrupted:", err);
            }
        }

        function toggleAutoRefresh() {
            const btn = document.getElementById('toggle-poll-btn');
            const indicator = document.getElementById('live-indicator');

            if (autoRefreshInterval) {
                clearInterval(autoRefreshInterval);
                autoRefreshInterval = null;
                btn.innerText = "AUTO-REFRESH: OFF";
                btn.style.backgroundColor = "#475569";
                indicator.innerText = "● MATRIX STATUS: PAUSED";
                indicator.style.color = "#f59e0b";
            } else {
                autoRefreshInterval = setInterval(fetchLatestData, 3000);
                btn.innerText = "AUTO-REFRESH: ON";
                btn.style.backgroundColor = "#334155";
                indicator.innerText = "● MATRIX STATUS: ONLINE";
                indicator.style.color = "#34d399";
                fetchLatestData();
            }
        }

        window.onload = () => {
            initChart(); // Initialize chart canvas
            fetchLatestData();
            autoRefreshInterval = setInterval(fetchLatestData, 3000);
        };
    </script>
</body>
</html>
"""

@app.route('/')
def serve_dashboard():
    return HTML_TEMPLATE

@app.route('/api/v1/dashboard/metrics')
def get_dashboard_metrics():
    severity_filter = request.args.get('severity', 'ALL')

    conn = sqlite3.connect(f"file:{DB_FILE}?mode=ro", uri=True)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM system_logs")
    total_logs = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM system_logs WHERE severity = 'CRITICAL'")
    critical_logs = cursor.fetchone()[0]
    
    health = ((total_logs - critical_logs) / total_logs * 100) if total_logs > 0 else 100.00
    
    if severity_filter != 'ALL':
        cursor.execute("SELECT timestamp, component, severity, message FROM system_logs WHERE severity = ? ORDER BY log_id DESC LIMIT 50", (severity_filter,))
    else:
        cursor.execute("SELECT timestamp, component, severity, message FROM system_logs ORDER BY log_id DESC LIMIT 50")
        
    rows = cursor.fetchall()
    
    logs_list = [
        {
            "timestamp": row[0],
            "component": row[1],
            "severity": row[2],
            "message": row[3]
        }
        for row in rows
    ]
        
    conn.close()
    return jsonify({
        "total_logs": total_logs,
        "critical_logs": critical_logs,
        "health": health,
        "logs": logs_list
    })

@app.route('/api/v1/dashboard/alerts')
def get_dashboard_alerts():
    analysis = analyze_recent_logs(lookback_count=50)
    return jsonify(analysis)

if __name__ == '__main__':
    app.run(port=8080, debug=True)