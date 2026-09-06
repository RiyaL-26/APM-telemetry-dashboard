# ⚡ Enterprise Infrastructure Telemetry & APM Matrix

A real-time Application Performance Monitoring (APM) control console and telemetry pipeline built with Python, Flask, SQLite, Chart.js, and Docker.

![System Status](https://img.shields.io/badge/Status-Active-brightgreen)
![Tech Stack](https://img.shields.io/badge/Stack-Python%20%7C%20Flask%20%7C%20Docker-blue)

---

## 📌 Architecture Overview

```text
[ Simulator Script ] ---> Ingests Telemetry ---> [ SQLite Database ]
                                                         |
                                                         v
                                                [ Analytics Engine ]
                                             (Anomaly & Error Detection)
                                                         |
                                                         v
[ Interactive Dashboard ] <--- REST API Engine <--- [ Flask Server ]
 (Chart.js / Auto-Polling)