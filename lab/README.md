# Packet Tracer lab

A working, scaled replica of the design. Every config here is generated from
`design/network.yaml`, so the lab and the design cannot drift apart.

```
python tools/render.py     # writes lab/configs/, lab/cabling.md, lab/tests.md
```

## What stands in for what

| Design device | Lab device (PT 8.x) | Why this stand-in |
|---------------|---------------------|-------------------|
| University Core (ITSC) | 2911 router `ITSC-R` + 2960 `ITSC-SW` | Transit VLAN 900; loopback 8.8.8.8 stands for the Internet |
| FortiGate 200F HA pair | 2 x ISR4331 `EB2-MDF-FW01/02` | PT has no FortiGate. HSRP gives the same shared .1 gateway; zone policy becomes inbound ACLs |
| C9300 core stack | 3650-24PS `EB2-MDF-CS` | One PT switch per stack (PT cannot stack) |
| C9200L-24T-4X (EB1 core, distribution) | 3650-24PS | Same role, Layer 2 only |
| C9200L access stack | 2960-24TT `<bldg>-F<n>-AS` | One per IDF |
| C9800-L-F + 57 C9115AXI | WLC-3504 + LAP 3702i | Controller-based APs, CAPWAP, DHCP option 43 |

**Scaled down, stated plainly:** links are 1G copper (design: 10G fibre); one switch per stack;
HSRP instead of FortiGate HA; stateless ACLs instead of a stateful NGFW with IPS;
no HSRP tracking; WPA2 instead of WPA3-Enterprise and 802.1X; PT's WLC maps an SSID to one VLAN, so the
per-building policy tag becomes EB2 VLANs only. The lab proves the logical design
(VLANs, trunks, LACP, STP roles, gateway redundancy, DHCP, zone policy, AP join),
not RF coverage or throughput. Coverage evidence is the Ruijie heatmaps.

## Build steps

1. **Place devices** from the table above, named exactly as in `cabling.md`.
2. **Power the 3650s**: in each 3650's Physical tab, drag in the AC power supply module,
   then switch it on. PT ships them unpowered.
3. **Cable** every row in `cabling.md` (copper straight-through; cross-over for the HA link).
4. **Paste configs**: open each device's CLI, paste `lab/configs/<device>.txt`. Order:
   ITSC-SW, ITSC-R, both firewalls, EB2-MDF-CS, EB1-F1-CS, distribution, access.
5. **SSH keys** (per switch, optional): `conf t` then `crypto key generate rsa`, modulus 1024,
   then `ip ssh version 2`.
6. **Hosts**: put a DHCP PC on Fa0/2, Fa0/6 and Fa0/7 of EB2-F1-AS and on Fa0/2 of EB1-F3-AS.
   Add the static hosts listed in `cabling.md` (NVR, admin PC, cameras, printers).
7. **WLC** (GUI from ADMIN-PC, http://10.10.16.10 after the first-boot wizard):
   - Management interface 10.10.16.10/26, gateway 10.10.16.1, VLAN 10.
   - Dynamic interfaces: VLANs 210, 220, 230, 240 with gateway .1 of each subnet.
   - WLANs: EB-Staff -> 210 (WPA2-PSK), EB-Student -> 220 (WPA2-PSK), EB-Guest -> 230 (open), EB-IoT -> 240.
8. **APs**: plug a LAP 3702i into Fa0/1 of any access switch. It gets an address in VLAN 20
   and joins the WLC through option 43. Give a laptop a wireless card and join EB-Student.
9. **Test** with `tests.md`. Save a screenshot per test to `lab/evidence/T<nn>.png` and fill in
   the Actual and Status columns.
10. **Save** the topology as `lab/NETDES-EB1-EB2.pkt` and commit it.

## Expected control-plane state

- STP root for every VLAN: EB2-MDF-CS (priority 4096); EB1-F1-CS is secondary for EB1 VLANs (8192).
- EB2-F2-AS and EB2-F3-AS: Gi0/1 forwarding, Gi0/2 alternate (cost 200 stands in for 10G vs 1G).
- HSRP: FW01 active (110), FW02 standby (100). Packet Tracer does not support HSRP interface or object
  tracking, so an outside-link failure moves only the outside group; FortiGate HA link monitoring covers this in the real design.
- DHCP: FW01 leases the lower half of each pool, FW02 the upper half; either can fail.
