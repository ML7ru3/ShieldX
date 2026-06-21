# Design Doc: Intelligent Endpoint Security Agent (Python)

**Date:** 2026-04-27
**Status:** Draft
**Topic:** Cross-platform security agent with AI anomaly detection and dual-mode response.

## 1. Executive Summary
The Intelligent Endpoint Security Agent is a defensive cybersecurity tool designed to monitor system telemetry (file, process, network) on Linux and Windows. It uses local machine learning (Isolation Forest) to detect behavioral anomalies and provides a dual-response mechanism: continuous auditing of all events and interactive user prompts for high-risk threats.

## 2. Architecture

### 2.1 Component Overview
The agent is a modular Python application structured into specialized layers:

- **Orchestrator (Core):** Manages the lifecycle of monitors, the AI engine, and the communication bus.
- **Monitors (Collectors):** Independent plugins for different telemetry types.
- **Inference Engine:** Handles data vectorization and anomaly scoring.
- **Response Engine:** Executes defensive actions (log, notify, kill).
- **Communication Layer:** Syncs with the central server (API client).

### 2.2 Telemetry Monitors
- **File Monitor:** Uses `watchdog` to monitor creation, modification, and deletion in sensitive directories.
- **Process Monitor:** Uses `psutil` to track process starts, parent-child relationships, and resource usage (CPU/RAM).
- **Network Monitor:** Uses `psutil` or `scapy` to capture metadata (local/remote IP:Port, protocol, byte counts).

## 3. Data & AI Strategy

### 3.1 SecurityEvent Schema
All monitors emit events in a unified JSON format:
```json
{
  "timestamp": "2026-04-27T10:00:00Z",
  "source": "file",
  "action": "modify",
  "actor_pid": 1234,
  "actor_name": "unknown.exe",
  "target": "/etc/shadow",
  "metadata": {
    "size_delta": 1024,
    "entropy": 7.8
  }
}
```

### 3.2 AI Engine (Isolation Forest)
- **Algorithm:** `sklearn.ensemble.IsolationForest`.
- **Learning Phase:** The agent gathers a baseline of "normal" system behavior for a configurable period.
- **Scoring:** Each incoming event is transformed into a feature vector and scored.
  - `score < 0.7`: Normal.
  - `0.7 <= score < 0.85`: Suspicious (Audit & Silent Alert).
  - `score >= 0.85`: High Anomaly (Audit & User Prompt).

## 4. Response Mechanisms

### 4.1 Audit Mode (Passive)
- Every event is recorded in a local SQLite database or JSONL log.
- Telemetry is batched and uploaded to the central server for centralized monitoring.

### 4.2 User-Prompted Mode (Active)
- **Trigger:** High anomaly score.
- **UX:** System notification (toast) with event details.
- **Actions:** 
  - **Suspend:** Optionally pause the process while waiting for user input.
  - **Kill:** Terminate the process tree.
  - **Allow:** Add the specific behavior to a local whitelist.

## 5. Technology Stack
- **Language:** Python 3.10+
- **Core Libraries:**
  - `psutil`: Process and network metadata.
  - `watchdog`: File system events.
  - `scikit-learn`: Isolation Forest model.
  - `pandas/numpy`: Data vectorization.
  - `plyer` or `win10toast`: Cross-platform notifications.
  - `requests`: Server communication.

## 6. Security & Ethics
- **Transparency:** The agent will log its own actions and provide a local interface for the user to see what is being monitored.
- **Isolation:** The agent's own process and config files will be protected via file system permissions.
- **Non-Invasive:** Network monitoring focuses on metadata, not payload inspection.

## 7. Success Criteria
- Successful collection of telemetry on both Linux and Windows.
- Detection of simulated anomalies (e.g., high-frequency file modifications in `/etc` or `%WINDIR%`).
- Functional user notification system for high-score events.
- Audit logs correctly synchronized to a (simulated or real) server endpoint.
