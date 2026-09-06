import requests
import random
import time

# FIXED TARGET URL: Double-check that this line is copied exactly as shown!
TARGET_URL = "http://127.0.0"

SERVICES = ["AuthGateway", "PaymentProcessor", "BillingEngine", "UserDatabase", "NotificationRouter", "FrontendLoadBalancer"]
SEVERITIES = ["INFO", "INFO", "INFO", "WARNING", "WARNING", "CRITICAL"]

MOCK_MESSAGES = {
    "INFO": [
        "User session token generated successfully.",
        "Database sync operation completed cleanly.",
        "Cache layer flushed for updated configurations.",
        "API health check verified status: green."
    ],
    "WARNING": [
        "Database read execution took longer than 500ms.",
        "API rate limit reached 85% capacity for client IP address.",
        "Memory consumption thresholds elevated above normal baseline.",
        "Connection retries initiated for secondary node."
    ],
    "CRITICAL": [
        "FATAL: Database connection timeout. Active nodes unreachable.",
        "SECURITY ALERT: Brute-force pattern identified on admin portal.",
        "OUT OF MEMORY: Core workflow pipeline forced into shutdown.",
        "CRITICAL ERROR: Payment gateway connection dropped mid-transaction."
    ]
}

def generate_bulk_traffic(total_logs=1000):
    print(f"⚡ Initializing automated stress simulator pipeline...")
    # This print statement will now display the FULL URL to verify it works
    print(f"📦 Preparing to stream {total_logs} telemetry logs to {TARGET_URL}\n")
    
    success_count = 0
    failure_count = 0
    start_time = time.time()

    for i in range(1, total_logs + 1):
        component = random.choice(SERVICES)
        severity = random.choice(SEVERITIES)
        message = random.choice(MOCK_MESSAGES[severity])
        execution_time = random.randint(5, 45) if severity == "INFO" else random.randint(200, 1500)

        payload = {
            "component": component,
            "severity": severity,
            "message": f"[{i}] {message}",
            "execution_time_ms": execution_time
        }

        try:
            response = requests.post(TARGET_URL, json=payload)
            # Checking for clean creation status code
            if response.status_code == 201:
                success_count += 1
            else:
                failure_count += 1
        except Exception:
            failure_count += 1

        if i % 100 == 0:
            print(f"🔄 Progress Update: {i}/{total_logs} data logs pushed down the pipe...")

    end_time = time.time()
    total_execution_time = round(end_time - start_time, 2)
    
    print("\n🏁 [TRAFFIC STREAM OPERATION COMPLETED]")
    print(f"✅ Packets Ingested Successfully: {success_count}")
    print(f"❌ Dropped or Failed Requests: {failure_count}")
    print(f"⏱️ Total Simulation Processing Velocity: {total_execution_time} seconds\n")

if __name__ == '__main__':
    generate_bulk_traffic(1000)
