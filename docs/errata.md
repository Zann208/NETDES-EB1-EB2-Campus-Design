# Errata and open items

Corrections to the submitted report (8 Oct 2026) and presentation material.
`design/network.yaml` holds the corrected values; `tools/validate.py` checks them.

## Corrections

| ID | Where | Printed | Correct | Effect on design |
|----|-------|---------|---------|------------------|
| E1 | Report 2.3 | Egress x2 headroom = 2,000 Mbps | 1,129 x 2 = 2,258 Mbps | None. FortiGate 200F (3 Gbps threat protection) still covers it. |
| E2 | Report 10.1 | Firewall headroom 50% | 3,000 / 2,258 = 33% | Still passes; wording only. |
| E3 | Report 8.2 | "15 switches" in access stacks | 14 (2+2+1+3+3+3) | None. 15 is the stack-kit count in the BOM (13 stacked access + 2 EB1 core). |
| E4 | Floor-plan legends (Physical Topology PDF) | EB1-F3 "AP 7", EB2-F1 "AP 17", EB2-F3 "AP 8" | 9, 10, 9 | Images lag the final AP plan; update the legend text. |
| E5 | Report 7.3, script slide 7 | EB2-F1 had 17 "surveyed" APs | 17 was the first-draft layout. The site survey recorded 7 existing APs on EB2-F1 (44 across both buildings). | Say "first-draft layout", not "surveyed". |

## Known, documented gaps (not errors)

- Wi-Fi devices by user group (1,273 + 84 IoT = 1,357) differ from the per-room total (1,370) by 13 because of per-room rounding. The design uses 1,370.
- Rooms EB1205, EB1206 and EB2313 had no occupancy data; spare ports and coverage are reserved for them.

## Open items

- [ ] Re-run heatmaps for EB2-F1 (10 APs) and EB1-F3 (9 APs) with final positions.
- [ ] Confirm EB2-EB1 fibre route and distance (assumed <= 300 m). If <= 300 m, OM4 + SR would save about THB 63,000.
- [ ] Confirm the ITSC uplink rate (design needs >= 2.26 Gbps; optic is 10G).
- [ ] Confirm cabling labour and fibre installation prices with a contractor (current rate is from a 2016 reference).
- [ ] Final hierarchical physical topology in standard Cisco icons (course Minimum Requirement 1).
