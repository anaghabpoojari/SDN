# Multi-Switch Flow Table Analyzer

**SRN:** PES1UG24CS056
**Course:** UE24CS252B — Computer Networks  
**Project:** SDN Mininet-based Simulation  
**Controller:** POX (Python OpenFlow Controller)  
**Emulator:** Mininet + Open vSwitch  

---

## Problem Statement

Design and implement an SDN-based Multi-Switch Flow Table Analyzer using Mininet and the POX OpenFlow controller. The system must:

- Connect a **multi-switch topology** to a POX controller
- Implement **packet_in handling** with a learning switch (match + action logic)
- **Install explicit flow rules** with idle/hard timeouts
- **Poll flow statistics** from every switch every 8 seconds and display them in the terminal, clearly marking each rule as **ACTIVE** or **UNUSED**
- Log **flow-removed events** with the reason (idle timeout / hard timeout / delete)
- Demonstrate two clear test scenarios: normal forwarding and flow expiry

---

## Project Structure

```
SDN/
├── flow_table_analyzer.py   ← POX controller module (copy to pox/ext/)
├── topology.py              ← Mininet topology (run separately)
└── README.md                ← this file
```

---

## Network Topology

```
h1(10.0.0.1) ─┐
               s1 ─── s2 ─── s3 ── h4(10.0.0.4)
h2(10.0.0.2) ─┘       │
                   h3(10.0.0.3)
```

- 3 OpenFlow switches: s1, s2, s3 (linear chain)
- 4 hosts: h1 and h2 on s1 · h3 on s2 · h4 on s3
- All inter-switch links: 100 Mbps, 5 ms delay
- All host links: 100 Mbps, 1 ms delay
- Controller: POX on 127.0.0.1:6633

---

## Prerequisites

Ubuntu 20.04 / 22.04 with:

| Tool | Purpose |
|---|---|
| Mininet | Network emulator |
| Open vSwitch | Software switch |
| Python 3 | Run topology script |
| POX | OpenFlow controller |
| Git | Clone POX |

Install all at once:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y mininet openvswitch-switch python3 git net-tools
```

---

## Setup Instructions

### Step 1 — Clone POX

```bash
cd ~
git clone https://github.com/noxrepo/pox.git
```

### Step 2 — Copy the Controller Module

```bash
cp ~/SDN/flow_table_analyzer.py ~/pox/ext/flow_table_analyzer.py
```

### Step 3 — Start Open vSwitch

```bash
sudo service openvswitch-switch start
sudo ovs-vsctl show
```

---

## Running the Project

> ⚠️ Always **clean up first**, then start **POX before Mininet**.

### Full Cleanup (run before every demo)

```bash
sudo mn -c
sudo pkill -f pox.py
sudo fuser -k 6633/tcp
sudo service openvswitch-switch restart
```

### Terminal 1 — Start POX Controller

```bash
cd ~/pox
sudo ./pox.py log.level --DEBUG flow_table_analyzer
```

Wait for:
```
INFO:core:POX 0.7.0 (gar) is up.
INFO:flow_table_analyzer:Final Clean Flow Analyzer running...
```

### Terminal 2 — Start Mininet Topology

```bash
sudo python3 ~/SDN/topology.py
```

---

## Screenshots

### 1. POX Controller Starting Up
<img width="811" height="245" alt="Screenshot from 2026-04-22 07-55-10" src="https://github.com/user-attachments/assets/3fefaf46-fe14-4276-bee9-db1216d7d8a3" />

---

### 2. Mininet Topology Starting
<img width="1057" height="468" alt="Screenshot from 2026-04-22 07-57-22" src="https://github.com/user-attachments/assets/af3d0a75-7a8a-47b4-8d0d-7e50d392c669" />

---

### 3. Switch Connection in POX (after Mininet starts)
<img width="622" height="383" alt="Screenshot from 2026-04-22 07-58-03" src="https://github.com/user-attachments/assets/9cf5d043-8b86-4774-bee6-599f24750937" />

---

## Test Scenario 1 — Normal Forwarding (`pingall`)

In the Mininet CLI:

```
mininet> pingall
```

Expected output:

```
*** Ping: testing ping reachability
h1 -> h2 h3 h4
h2 -> h1 h3 h4
h3 -> h1 h2 h4
h4 -> h1 h2 h3
*** Results: 0% dropped (12/12 received)
```

### 4. pingall — 0% Packet Loss
<img width="611" height="544" alt="Screenshot from 2026-04-22 08-00-29" src="https://github.com/user-attachments/assets/aabcc5ff-b840-4c3d-b312-76ba4ba106a9" />

<img width="425" height="162" alt="Screenshot from 2026-04-22 08-01-27" src="https://github.com/user-attachments/assets/f6e15530-9de3-49b9-9e4e-04b76af0021d" />

---

## Test Scenario 2 — Flow Expiry (Idle Timeout)

Send a short ping, then stop traffic and wait 20 seconds:

```
mininet> h1 ping h4 -c 3
```

Then wait without sending any more traffic.

### 6. Short Ping from h1 to h4
<img width="642" height="206" alt="Screenshot from 2026-04-22 08-02-13" src="https://github.com/user-attachments/assets/60c11152-2aa5-4ebf-aa20-c427bdb20793" />

---


## Useful Mininet CLI Commands

| Command | What it does |
|---|---|
| `pingall` | Test all-pairs connectivity |
| `h1 ping h4 -c 5` | 5 ICMP packets from h1 to h4 |
| `h1 iperf h4 &` | Background throughput test |
| `h2 ping h3 -c 10 &` | Background ping |
| `dpctl dump-flows` | Dump raw flow tables from OVS |
| `nodes` | List all nodes |
| `net` | Show all links |
| `dump` | Detailed node info |
| `exit` | Exit Mininet |

---

## Cleanup

After every session:

```bash
sudo mn -c
```
