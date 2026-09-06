import sqlite3
import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app) # Allows dashboards to securely connect to our engine
DB_FILE = "infrastructure_telemetry.db"

def initialize_database():
    """Establishes the database schema with indexed fields for high performance."""
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    
    # Create the core system logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            component TEXT NOT NULL,
            severity TEXT NOT NULL,
            message TEXT NOT NULL,
            execution_time_ms INTEGER DEFAULT 0
        )
    ''')
    
    # Robust Tuning: Indexing columns that will be heavily searched/filtered
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_severity ON system_logs(severity)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_component ON system_logs(component)")
    
    connection.commit()
    connection.close()
    print("📢 Database infrastructure initialized with high-performance indexing.")

@app.route('/api/v1/telemetry', methods=['POST'])
def receive_telemetry():
    """Ingestion gate that receives logs from external client apps."""
    try:
        payload = request.get_json()
        
        # Edge Case Validation: Reject empty or corrupted data packets
        required_keys = ['component', 'severity', 'message']
        if not payload or not all(key in payload for key in required_keys):
            return jsonify({"status": "REJECTED", "error": "Invalid log schema format."}), 400
            
        component = payload['component']
        severity = payload['severity'].upper()
        message = payload['message']
        execution_time = payload.get('execution_time_ms', 0)
        timestamp = datetime.datetime.now().isoformat()

        # Instant Notification Override for Critical Errors
        if severity == "CRITICAL":
            dispatch_emergency_alert(component, message)

        # Secure Write Operation to the SQLite Database
        connection = sqlite3.connect(DB_FILE)
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO system_logs (timestamp, component, severity, message, execution_time_ms) VALUES (?, ?, ?, ?, ?)",
            (timestamp, component, severity, message, execution_time)
        )
        connection.commit()
        connection.close()

        return jsonify({"status": "SUCCESS", "message": "Telemetry point tracked securely."}), 201

    except Exception as error:
        return jsonify({"status": "SERVER_ERROR", "details": str(error)}), 500

def dispatch_emergency_alert(service_name, error_details):
    """Simulates an immediate system alert trigger for administrators."""
    print("\n🚨 [ALERT PIPELINE ACTIVE] 🚨")
    print(f"CRITICAL OVERFLOW IDENTIFIED IN RUNTIME MODULE: [{service_name}]")
    print(f"DEVIATION TRACE DETAILS: {error_details}\n")

if __name__ == '__main__':
    initialize_database()
    # Runs the backend pipeline locally on port 5000
    app.run(port=5000, debug=True)
