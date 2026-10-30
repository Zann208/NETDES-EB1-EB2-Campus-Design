# Design

Condensed from the submitted report (8 Oct 2026), with the corrections in [errata.md](errata.md).
Every figure here is recomputed by `tools/validate.py` from `design/network.yaml`.

## 1. Site and users

Two academic buildings, three floors each. EB2 floor 1 holds the server room (MDF); each floor has
one IDF beside the stairs on the riser path.

| Floor | Main areas | Peak users | Wi-Fi devices | APs |
|-------|-----------|-----------:|--------------:|----:|
| EB1-F1 | Offices EB1101-1104, Club Room | 72 | 132 | 9 |
| EB1-F2 | Offices EB1201-1204, Conference EB1207 (80) | 122 | 232 | 11 |
| EB1-F3 | Lecture EB1301 (64), EB1302 (90) | 156 | 275 | 9 |
| EB2-F1 | Offices EB2101-2107, server room | 92 | 180 | 10 |
| EB2-F2 | Faculty room, offices EB2202-2207 | 128 | 246 | 9 |
| EB2-F3 | Faculty room, offices, Conference EB2321 (80) | 152 | 305 | 9 |
| **Total** | | **722** | **1,370** | **57** |

Wired: 139 PCs, 93 IP phones, 37 printers/AV, 17 CCTV cameras, 12 servers/NVR (1,668 devices in all).
Wi-Fi devices per person: staff 2.0, students 1.7, guests 1.8, plus 84 wireless IoT devices.

## 2. Requirements

| Area | Applications | Per user |
|------|--------------|---------:|
| Lecture rooms | LMS, cloud, video streaming, online tests | 5 Mbps |
| Conference rooms | HD video conferencing, screen sharing, IP phone | 3 Mbps |
| Offices | Video calls, email/cloud, research files, printing | 4 Mbps |
| Club room | Web, streaming, video calls | 2 Mbps |

Voice and video: delay <= 150 ms, jitter < 30 ms, loss < 1%.
Access-layer demand 2.82 Gbps; 40% leaves the faculty (1.13 Gbps), planned at x2 = **2.26 Gbps** of egress.

## 3. Architecture

3-tier, with a core in each building:

```
University Core (ITSC)
        |  OS2 10G LR, transit VLAN 900
FortiGate 200F HA pair (EB2-MDF-FW01/02)        <- only Layer 3 point
        |  OM4 10G 802.1Q trunk
Faculty core  EB2-MDF-CS  (C9300-24T stack)  -- WLC, servers/NVR
   |-- EB2-F1-AS                        (2x10G LACP)
   |-- EB2-F2-DS01 -- EB2-F2-AS, EB2-F3-AS   (10G + 1G STP backup)
   '== EB1-F1-CS  (C9200L stack)        (OS2 2x10G LR, 2 diverse paths)
         |-- EB1-F1-AS
         |-- EB1-F2-DS01 -- EB1-F2-AS
         '-- EB1-F3-DS01 -- EB1-F3-AS
```

| Option | Verdict | Reason |
|--------|---------|--------|
| 3-tier, core per building | Chosen | EB1 needs 2 inter-building links, not 6; floors grow without core ports |
| Collapsed core | Rejected | Core runs out of SFP+; 6 LR links across buildings |
| Spine-leaf | Rejected | Built for east-west data-centre traffic; campus traffic goes north-south |

## 4. Logical design

- **Routing:** the FortiGate HA pair is the `.1` gateway for all 14 VLANs over one 802.1Q trunk.
  Every switch is Layer 2 (no L3 licences). East-west traffic is small (CCTV to NVR is about 68 Mbps),
  so sending it through the firewall costs nothing and puts every inter-VLAN flow under policy and IPS.
- **To the campus:** default route to ITSC over transit VLAN 900; ITSC routes 10.10.0.0/19 back (no NAT).
- **STP:** Rapid-PVST+, faculty core is root, EB1 core is secondary for EB1 VLANs.
  PortFast + BPDU Guard on edge ports, Root Guard on downlinks.
- **Wireless:** APs in VLAN 20 tunnel (CAPWAP) to the WLC, which drops clients into the building's VLAN by policy tag.

## 5. VLANs and addressing

10.10.0.0/16 faculty block; one /21 per building; the whole plan summarises to 10.10.0.0/19.

| Group | EB1 VLAN | EB1 subnet | EB2 VLAN | EB2 subnet | Growth |
|-------|---------:|------------|---------:|------------|-------:|
| Staff | 110 | 10.10.4.0/24 | 210 | 10.10.12.0/23 | 20% |
| Student | 120 | 10.10.0.0/22 | 220 | 10.10.8.0/22 | 30% |
| Guest | 130 | 10.10.5.0/25 | 230 | 10.10.14.0/25 | 100% |
| IoT | 140 | 10.10.5.128/25 | 240 | 10.10.14.128/25 | 40% |
| CCTV | 150 | 10.10.6.0/27 | 250 | 10.10.15.0/27 | 50% |

Shared: NET-MGMT 10 (10.10.16.0/26), AP-MGMT 20 (10.10.17.0/25), VOICE 30 (10.10.18.0/24),
SERVER 40 (10.10.16.64/27). Reserved for growth: 10.10.19.0-10.10.31.255.

| SSID | Security | VLAN EB1 / EB2 |
|------|----------|----------------|
| EB-Staff | WPA3-Enterprise 802.1X, PMF | 110 / 210 |
| EB-Student | WPA3-Enterprise 802.1X | 120 / 220 |
| EB-Guest | OWE + captive portal, client isolation | 130 / 230 |
| EB-IoT | Hidden, per-device PSK | 140 / 240 |

## 6. Wireless

- AP count = max(coverage, capacity) at 150 Mbps and <= 150 clients per AP.
  EB1302: 90 users x 5 Mbps = 450 Mbps -> 3 APs.
- RSSI targets: -65 dBm lecture/conference/voice, -67 dBm offices, -70 dBm corridors; SNR >= 25 dB (20 in corridors).
- 20 MHz channels on 5 GHz, 12 Mbps minimum data rate, 802.11b off, RRM for channel and power.
- Ruijie Cloud AI Heatmap: 98% of EB1 and 90% of EB2 at -60 dBm or better.
- 57 Cisco C9115AXI on one C9800-L-F (23% of AP capacity, 27% of client capacity).

## 7. Access, uplinks, media

- One C9200L stack per IDF: 504 ports, 343 used, 161 spare (>= 20% on every floor).
- PoE worst case (AP 30 W, phone and camera 15.4 W): highest switch at 73% of its budget.
- Uplinks: 2x10G LACP everywhere except EB2-F2-DS01 to floors 2-3 (10G + Cat6 1G STP backup).
  One surviving link still carries the peak floor load (<= 0.8 Gbps); oversubscription <= 12:1.
- OM4 10GBASE-SR inside buildings (runs <= 45 m, SR optics about 2.5x cheaper than LR).
  OS2 10GBASE-LR between buildings on two separate paths. Cat6 U/UTP LSZH to endpoints, longest run 56 m.

## 8. Security

Zone = the same VLAN group in both buildings. Default deny, every policy logged.

| From \ To | Internet | Servers | CCTV | Management |
|-----------|----------|---------|------|------------|
| Staff | Allow + IPS, AV, web filter | Published services | Deny (admins to NVR) | Admins only |
| Student | Allow + IPS, app control | Selected services | Deny | Deny |
| Guest | Internet only, web filter, rate cap | Deny | Deny | Deny |
| IoT | DNS, NTP, vendor cloud | Required only | Deny | Deny |
| CCTV | Deny | NVR only | Same zone | Deny |

Layers: NGFW HA at the edge; 802.1X/WPA3 and rogue-AP detection on Wi-Fi; DHCP snooping, DAI,
BPDU Guard, port security and unused ports in VLAN 999 at access; SSH/HTTPS/SNMPv3 on VLAN 10 only;
firewall and WLC logs kept 90 days (Computer Crime Act s.26); locked racks and UPS in every rack.

## 9. Equipment and budget

| Role | Model | Qty |
|------|-------|----:|
| Firewall | FortiGate 200F (HA, 3-yr UTP) | 2 |
| Faculty core | Catalyst C9300-24T-E + NM-8X | 2 |
| EB1 core / distribution | Catalyst C9200L-24T-4X-E | 5 |
| Access | Catalyst C9200L-48P-4X / 24P-4G / 48T-4G / 24T-4G | 14 |
| Wireless | C9800-L-F controller, C9115AXI APs | 1 + 57 |
| UPS | Smart-UPS SRT3000XLI (MDF), SRT1500XLI (IDF) | 1 + 6 |

| | THB |
|---|---:|
| Active equipment | 5,412,535 |
| Cabling, racks, installation | 1,551,921 |
| Total before VAT | 6,964,456 |
| **Grand total incl. 7% VAT** | **7,451,968** |

Full line items with sources: [design/bom.csv](../design/bom.csv).

## 10. Trade-offs accepted

- EB2-F2-DS01 is one switch serving two floors (a second stack member costs about THB 111,000).
- One WLC (HA SSO with a second unit costs about THB 140,000).
- Two firewalls rather than one (+THB 388,500) to remove the single exit point for 1,668 devices.
