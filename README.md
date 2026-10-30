# EB1-EB2 Campus Network Design

Network design for two academic buildings (Faculty of Education, Chiang Mai University):
722 peak concurrent users, 1,668 devices, 57 controller-based Wi-Fi 6 APs, a
FortiGate HA pair as the single routing and security point, and a sourced
budget of THB 7.45 M.

Course project, 261434 Computer Network Design and Management (CMU, 1/2026).
This is a design proposal built from a real site survey. It has not been deployed.

## Design at a glance

| Area | Decision |
|------|----------|
| Architecture | 3-tier: faculty core (EB2 MDF) + EB1 building core, distribution, one access stack per floor |
| Routing / security | FortiGate 200F HA (active-passive) is the gateway for all 14 VLANs; every switch is Layer 2 |
| Wireless | 57 x Cisco C9115AXI on one C9800-L-F (23% of AP capacity), 4 SSIDs, -65/-67/-70 dBm targets |
| Addressing | 10.10.0.0/16 block, one /21 per building, whole plan summarises to 10.10.0.0/19 |
| Access | Catalyst 9200L stacks, 504 ports (161 spare), PoE load <= 73% per switch |
| Backbone | OM4 10GBASE-SR inside buildings, OS2 10GBASE-LR on two diverse paths between buildings |
| Budget | THB 6,964,456 before VAT, THB 7,451,968 with VAT |

## Why it is built this way

- **Campus hands over at Layer 2**, so the faculty needs its own L3 control point. Routing at the
  firewall puts every inter-VLAN flow through policy and IPS and avoids L3 switch licences.
  East-west traffic is small (about 68 Mbps, mostly CCTV to NVR), so the firewall is not a bottleneck.
- **A core in each building** means EB1 needs 2 inter-building links instead of 6; a collapsed core
  would have run out of SFP+ ports.
- **AP count = max(coverage, capacity).** Lecture room EB1302: 90 users x 5 Mbps = 450 Mbps,
  at 150 Mbps per AP = 3 APs. The first-draft layout for EB2 floor 1 had 17 APs; one per room is enough, so it was cut to 10.

## Repository

```
design/network.yaml   source of truth: users, VLANs, subnets, devices, links, PoE
design/bom.csv        equipment list with unit prices and sources
tools/validate.py     recomputes every figure and cross-checks documents (143 checks)
tools/render.py       generates Packet Tracer configs, cabling and test plan from the design
diagrams/             draw.io topology sources
docs/errata.md        corrections to the submitted report, open items
docs/roadmap.md       what is built next
lab/                  Packet Tracer replica: generated configs, cabling, 28-test plan
```

## Verify the design

```
pip install pyyaml
python tools/validate.py
```

Checks subnet sizing and overlaps, switch ports with 20% spare, per-switch PoE budgets,
uplink capacity after a link failure, media distance limits, SFP+ port budgets,
controller scale, BOM arithmetic and that device counts agree between the design and the BOM.
It runs on every push through GitHub Actions, which also re-renders the lab configs and fails if
the committed configs no longer match the design.

## Lab

A scaled Packet Tracer replica (15 network devices, WLC and APs) built from generated configs:
LACP bundles, Rapid-PVST+ with a fixed root, HSRP gateway redundancy standing in for FortiGate HA,
split DHCP, zone-policy ACLs, DHCP snooping, BPDU Guard and port security. See [lab/README.md](lab/README.md).

## Status

Report and presentation delivered October 2026. Open items (heatmap re-runs for two floors,
inter-building fibre distance, ITSC uplink rate, contractor pricing) are listed in
[docs/errata.md](docs/errata.md).

## Team

Group 2, 261434 (CMU). Team credits and individual contributions: see [docs/team.md](docs/team.md).
