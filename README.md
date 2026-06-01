# NOCOps Sentinel

NOCOps Sentinel is a Streamlit dashboard that simulates NOC, computer operations, production control, and data center infrastructure monitoring.

The project was built to support roles such as:

- NOC Analyst
- Computer Operator
- Data Center Operations Technician
- Infrastructure Support Specialist
- Production Control Analyst
- Security Operations Analyst

## What the app monitors

- Windows, Linux, and AIX-style distributed servers
- CPU, memory, disk, latency, uptime, and patch age
- TPE/BPE production jobs
- SLA-risk detection
- UPS, generator, HVAC/CRAC, fire suppression, and physical security alerts
- ITIL-style incident queue and downloadable incident report

## Project Structure

```text
nocops-sentinel/
├── app.py
├── requirements.txt
├── README.md
├── data/
│   ├── server_health.csv
│   ├── batch_jobs.csv
│   └── environmental_alerts.csv
├── reports/
│   └── sample_incident_report.csv
└── src/
    └── data_generator.py
```

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Push this folder to GitHub.
2. Go to Streamlit Community Cloud.
3. Choose your repository.
4. Set the main file path to:

```text
app.py
```

5. Deploy.

## Resume Bullet

Built a Python and Streamlit NOC monitoring dashboard simulating server health checks, production control workflows, TPE/BPE SLA-risk detection, data center environmental alerts, and ITIL-style incident response reporting.
