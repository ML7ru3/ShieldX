# Task for final project


## 06.02.2026

Done ShieldX_agent:
    -[x] Can collect system information.
    -[x] Can add firewall to the local machine.
    -[x] Can sniff capture packet from local machine.
    -[x] Disable DoH on local machine.
        - [x] On startup, block all well-known public DoH endpoints using firewall.
    -[] Implement Dohlyzer to the agent.
        -[x] Processing data from pcap files to chunk.
        -[] Make and train a model (choosing RandomForest for best accuracy), datasets can take from original website Doh2020 or on Kaggle.
        -[] Make it predict that it is malware or not.
