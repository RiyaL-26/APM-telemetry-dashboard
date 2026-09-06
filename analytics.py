import sqlite3
import time

DB_FILE = "infrastructure_telemetry.db"

def analyze_recent_logs(lookback_count=50):
    """Calculates error rates and detects component failures in recent logs."""
    conn = sqlite3.connect(f"file:{DB_FILE}?mode=ro", uri=True)
    cursor = conn.cursor()

    # Get recent logs
    cursor.execute("""
        SELECT component, severity, message 
        FROM system_logs 
        ORDER BY log_id DESC 
        LIMIT ?
    """, (lookback_count,))
    logs = cursor.fetchall()
    conn.close()

    if not logs:
        return {"status": "NO_DATA", "alerts": []}

    # Track metrics per component
    component_errors = {}
    critical_count = 0

    for component, severity, message in logs:
        if severity in ['CRITICAL', 'WARNING']:
            component_errors[component] = component_errors.get(component, 0) + 1
        if severity == 'CRITICAL':
            critical_count += 1

    # Generate Alerts based on thresholds
    alerts = []
    
    # Threshold 1: Overall failure rate too high
    failure_rate = (len([l for l in logs if l[1] != 'INFO']) / len(logs)) * 100
    if failure_rate > 30:
        alerts.append({
            "level": "HIGH",
            "title": "High Error Density Detected",
            "message": f"{failure_rate:.1f}% of recent logs contain errors or warnings."
        })

    # Threshold 2: Single component hotspot
    for comp, count in component_errors.items():
        if count >= 3:
            alerts.append({
                "level": "CRITICAL",
                "title": f"Component Failure Hotspot: {comp}",
                "message": f"{comp} generated {count} non-INFO events in the last {lookback_count} logs."
            })

    return {
        "status": "ANALYZED",
        "sample_size": len(logs),
        "critical_count": critical_count,
        "failure_rate": round(failure_rate, 2),
        "alerts": alerts
    }

if __name__ == "__main__":
    print("--- Running Analytics Engine Diagnostic ---")
    results = analyze_recent_logs()
    print(results)