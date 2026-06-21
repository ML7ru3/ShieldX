# Task for final project


## 06.02.2026

Done ShieldX_agent:
    -[x] Can collect system information.
    -[x] Can add firewall to the local machine.
    -[x] Can sniff capture packet from local machine.
    -[x] Disable DoH on local machine.
        - [x] On startup, block all well-known public DoH endpoints using firewall.
    -[] Implement Dohlyzer to the agent.
        -[x] Processing data from pcap files to chunk like in datasets/.
        -[x] Make and train a model (choosing RandomForest for best accuracy), datasets can take from original website Doh2020 or on Kaggle.
        -[] Make it predict that it is malware or not.

## Classroom Feature Proposals

The following features are suggested to adapt ShieldX for educational/classroom environments:

### Student Agent Groups
- [] Group agents by class/course, with dashboard filtering by group for instructors.

### Classroom Threat Demo
- [] Create predefined scenarios with fake malicious flow datasets so students can observe the full detection pipeline (capture -> feature extraction -> classify).

### Model Competition / Leaderboard
- [] Allow students to train their own models (RF, SVM, LightGBM, XGBoost) and compare accuracy/F1 scores on a shared leaderboard.

### Capture Challenge
- [] Students run the agent on their own machines to collect real traffic and observe whether anomalies are detected.

### Lab Assignment Dashboard
- [] Integrate assignment submission and auto-grading based on agent detection results.

### Real-time Alert Feed
- [] Display real-time alerts on dashboard with filtering by class/student for instructor monitoring.

### Whitelist Exercise
- [] Assign exercises where students configure allow/block domain policies and deploy them on their own agents.

### Visualization Module
- [] Add time-series charts (flow counts, malicious/benign ratios, feature distributions) for teaching purposes.
