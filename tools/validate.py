#!/usr/bin/env python3
"""Validate the EB1-EB2 design against itself.

Reads design/network.yaml and design/bom.csv and recomputes every number the
report depends on: users and devices, VLAN sizing, address overlaps, switch
ports, PoE budgets, link capacity, AP/controller scale and the budget.
It also compares the recomputed values with figures quoted in the report, so
an error in a document shows up here instead of in front of an examiner.

Exit code 1 if any check FAILs. WARN lines are known gaps, not failures.
"""
from __future__ import annotations

import csv
import ipaddress
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
D = yaml.safe_load((ROOT / "design" / "network.yaml").read_text())
BOM = list(csv.DictReader((ROOT / "design" / "bom.csv").open()))

results: list[tuple[str, str, str]] = []  # (status, section, message)


def check(section: str, ok: bool, msg: str, warn: bool = False) -> None:
    results.append(("PASS" if ok else ("WARN" if warn else "FAIL"), section, msg))


def claim(section: str, label: str, computed, stated) -> None:
    """Compare a recomputed value with a figure quoted in the report."""
    ok = computed == stated
    check(section, ok, f"{label}: computed {computed:,} vs report {stated:,}" if not ok
          else f"{label}: {computed:,}")


# --------------------------------------------------------------------------
# 1. Users and devices
# --------------------------------------------------------------------------
S = "users"
floors = D["floors"]
users = sum(f["users"] for f in floors.values())
wifi = sum(f["wifi"] for f in floors.values())
wired = sum(f["pc"] + f["phone"] + f["printer_av"] + f["servers"] + f["cctv"] for f in floors.values())
claim(S, "peak concurrent users", users, 722)
claim(S, "Wi-Fi devices", wifi, 1370)
claim(S, "wired devices", wired, 298)
claim(S, "total devices", wifi + wired, 1668)
claim(S, "CCTV cameras", sum(f["cctv"] for f in floors.values()), 17)
claim(S, "IP phones", sum(f["phone"] for f in floors.values()), 93)
claim(S, "PCs", sum(f["pc"] for f in floors.values()), 139)
claim(S, "wireless IoT", sum(D["wireless_iot"].values()), 84)

group_users = sum(g["EB1"] + g["EB2"] for g in D["users"].values())
claim(S, "users by group (faculty+staff+students+guests)", group_users, 722)
group_wifi = sum(round((g["EB1"] + g["EB2"]) * g["wifi_per_person"]) for g in D["users"].values())
gap = wifi - (group_wifi + sum(D["wireless_iot"].values()))
check(S, gap == 0,
      f"Wi-Fi by group {group_wifi:,} + IoT 84 = {group_wifi + 84:,}; per-room total {wifi:,} "
      f"(gap {gap}, per-room rounding, documented in report 1.3)", warn=True)

# --------------------------------------------------------------------------
# 2. Demand and egress
# --------------------------------------------------------------------------
S = "demand"
dm = D["demand"]
access = sum(a["users"] * a["mbps_per_user"] for a in dm["areas"].values())
claim(S, "access-layer demand (Mbps)", access, 2822)
egress = round(access * dm["egress_fraction"])
claim(S, "egress before headroom (Mbps)", egress, 1129)
planned = round(egress * dm["egress_headroom"])
claim(S, "egress x2 headroom (Mbps) (errata E1: report 2.3 printed 2,000)", planned, 2258)
fw_gbps = D["models"]["FortiGate-200F"]["threat_protection_gbps"]
check(S, fw_gbps * 1000 >= planned, f"firewall {fw_gbps} Gbps covers planned egress {planned:,} Mbps")
headroom = round((fw_gbps * 1000 / planned - 1) * 100)
check(S, headroom >= 25, f"firewall headroom over planned egress: {headroom}% "
      f"(errata E2: report 10.1 printed 50%)")

# --------------------------------------------------------------------------
# 3. Wireless
# --------------------------------------------------------------------------
S = "wlan"
crit = D["wlan_criteria"]
total_aps = sum(f["aps"] for f in floors.values())
claim(S, "APs designed", total_aps, 57)
for room, r in D["ap_sizing"].items():
    need = max(math.ceil(r["users"] * r["mbps_per_user"] / crit["ap_planning_mbps"]),
               math.ceil(r["devices"] / crit["max_assoc_per_radio"]))
    check(S, r["installed"] >= need, f"{room}: needs {need} AP(s) by capacity, {r['installed']} installed")
for fl, f in floors.items():
    per_ap = round(f["wifi"] / f["aps"])
    check(S, per_ap <= crit["max_assoc_per_radio"], f"{fl}: {per_ap} Wi-Fi devices per AP")
wlc = D["models"]["C9800-L-F"]
check(S, total_aps <= wlc["max_aps"], f"WLC AP load {total_aps}/{wlc['max_aps']} "
      f"({round(total_aps / wlc['max_aps'] * 100)}%)")
check(S, wifi <= wlc["max_clients"], f"WLC client load {wifi:,}/{wlc['max_clients']:,} "
      f"({round(wifi / wlc['max_clients'] * 100)}%)")

# --------------------------------------------------------------------------
# 4. VLAN / IP plan
# --------------------------------------------------------------------------
S = "ip"
block = ipaddress.ip_network(D["addressing"]["faculty_block"])
summary = ipaddress.ip_network(D["addressing"]["advertised_summary"])
bsum = {k: ipaddress.ip_network(v) for k, v in D["addressing"]["building_summary"].items()}
nets = []
for v in D["vlans"]:
    net = ipaddress.ip_network(v["subnet"])
    usable = net.num_addresses - 2
    hosts = math.ceil(v["endpoints"] * (1 + v["growth"]))
    check(S, usable >= hosts + 1, f"VLAN {v['id']:>3} {v['name']:<12} {str(net):<17} "
          f"needs {hosts}+gw, has {usable}")
    check(S, net.subnet_of(summary), f"VLAN {v['id']} inside {summary}")
    if v["scope"] in bsum:
        check(S, net.subnet_of(bsum[v["scope"]]), f"VLAN {v['id']} inside building summary {bsum[v['scope']]}")
    nets.append((v["id"], net))
overlaps = [(a, b) for i, (a, na) in enumerate(nets) for b, nb in nets[i + 1:] if na.overlaps(nb)]
check(S, not overlaps, f"no subnet overlaps among {len(nets)} VLANs" if not overlaps else f"overlaps: {overlaps}")
check(S, summary.subnet_of(block), f"summary {summary} inside faculty block {block}")
check(S, len(D["vlans"]) == 14, f"{len(D['vlans'])} user/infra VLANs (report says 14)")

stacks = len(D["idfs"]) + len(D["core"]) + len(D["distribution"])
mgmt_endpoints = stacks + 3 + 1 + (len(D["idfs"]) + 1)  # FW x2 + HA IP, WLC, one UPS per rack
mgmt_v = next(v for v in D["vlans"] if v["id"] == 10)
claim(S, "NET-MGMT endpoints (stacks + FW 3 + WLC + UPS)", mgmt_endpoints, mgmt_v["endpoints"])
ap_v = next(v for v in D["vlans"] if v["id"] == 20)
claim(S, "AP-MGMT endpoints = AP count", ap_v["endpoints"], total_aps)

# --------------------------------------------------------------------------
# 5. Access ports and PoE
# --------------------------------------------------------------------------
S = "access"
models = D["models"]
draw = D["poe_draw_w"]
total_ports = total_used = 0
access_switches: Counter = Counter()
for idf, cfg in D["idfs"].items():
    f = floors[idf]
    used = f["pc"] + f["phone"] + f["printer_av"] + f["cctv"] + f["aps"]
    needed = math.ceil(used * (1 + D["spare_port_target"]))
    ports = sum(models[m]["ports"] for m in cfg["stack"])
    access_switches.update(cfg["stack"])
    total_ports += ports
    total_used += used
    check(S, ports >= needed, f"{idf}: {used} used, {needed} needed with 20% spare, {ports} available")
    poe_aps = sum(load.get("ap", 0) for load in cfg["poe_load"].values())
    check(S, poe_aps == f["aps"], f"{idf}: PoE ports assigned to {poe_aps} APs, floor has {f['aps']}")
    for i, (sw, load) in enumerate(cfg["poe_load"].items()):
        model = cfg["stack"][i]
        watts = sum(draw[k] * n for k, n in load.items())
        budget = models[model]["poe_w"]
        pct = round(watts / budget * 100)
        check(S, watts <= budget, f"{idf}-{sw} {model}: {watts:.0f} W / {budget} W ({pct}%)")
claim(S, "access ports total", total_ports, 504)
claim(S, "access ports used", total_used, 343)
claim(S, "spare ports", total_ports - total_used, 161)
n_access = sum(access_switches.values())
claim(S, "access switches in stacks (errata E3: report 8.2 printed 15)", n_access, 14)

# --------------------------------------------------------------------------
# 6. Links, uplinks, media
# --------------------------------------------------------------------------
S = "links"
up = {l["b"]: l for l in D["links"]}
for idf in D["idfs"]:
    peak = dm["floor_peak_gbps"][idf]
    link = up[idf]
    check(S, link["gbps"] >= peak, f"{idf} uplink {link['gbps']}G carries peak {peak} Gbps")
    surviving = link.get("backup_gbps", link["gbps"] / 2 if link.get("lacp") else 0)
    check(S, surviving >= peak, f"{idf} after one link fails: {surviving}G vs {peak} Gbps")
    access_g = sum(models[m]["ports"] for m in D["idfs"][idf]["stack"])
    ratio = access_g / link["gbps"]
    check(S, ratio <= 20, f"{idf} oversubscription {ratio:.1f}:1")
ib = next(l for l in D["links"] if l["b"] == "EB1-F1-CS")
check(S, ib["gbps"] / ib["diverse_paths"] >= dm["eb1_total_gbps"],
      f"EB1 on one surviving fibre path: {ib['gbps'] / ib['diverse_paths']:.0f}G vs {dm['eb1_total_gbps']} Gbps")
check(S, ib.get("distance_confirmed", False),
      f"EB2-EB1 fibre distance assumed {ib['distance_m']} m, not confirmed on site", warn=True)
lim = D["media_limits_m"]
for l in D["links"]:
    if "distance_m" in l:
        key = f"{l['optic']}/{l['media']}"
        check(S, l["distance_m"] <= lim[key], f"{l['a']}->{l['b']} {l['distance_m']} m within {key} limit {lim[key]} m")
check(S, D["longest_copper_run_m"] <= 90, f"longest Cat6 run {D['longest_copper_run_m']} m <= 90 m")

# SFP+ budget on the two core stacks
core_sfp = defaultdict(int)
for l in D["links"]:
    if l["a"] in D["core"] and l["media"] in ("OM4", "OS2"):
        core_sfp[l["a"]] += max(1, l["gbps"] // 10)
    if l["b"] in D["core"] and l["media"] in ("OM4", "OS2"):
        core_sfp[l["b"]] += max(1, l["gbps"] // 10)
for cs, spec in D["core"].items():
    have = sum(models[m]["sfp_plus"] for m in spec["members"])
    check(S, core_sfp[cs] <= have, f"{cs}: {core_sfp[cs]} of {have} SFP+ ports used")

# --------------------------------------------------------------------------
# 7. Budget
# --------------------------------------------------------------------------
S = "budget"
cat = defaultdict(int)
for row in BOM:
    cat[row["category"]] += int(row["qty"]) * int(row["unit_thb"])
active = sum(v for k, v in cat.items() if k != "Cabling")
claim(S, "active equipment (THB)", active, 5_412_535)
claim(S, "cabling, racks, installation (THB)", cat["Cabling"], 1_551_921)
pre_vat = active + cat["Cabling"]
claim(S, "total before VAT (THB)", pre_vat, 6_964_456)
claim(S, "grand total incl. 7% VAT (THB)", round(pre_vat * 1.07), 7_451_968)

def bom_qty(item_prefix: str) -> int:
    return sum(int(r["qty"]) for r in BOM if r["item"].startswith(item_prefix))

claim(S, "BOM APs = design APs", bom_qty("C9115AXI"), total_aps)
claim(S, "BOM AP licences = design APs", bom_qty("AIR-DNA-E"), total_aps)
for model, n in access_switches.items():
    claim(S, f"BOM {model} = access stacks", bom_qty(model + "-E"), n)
stacked = sum(len(c["stack"]) for c in D["idfs"].values() if len(c["stack"]) > 1)
claim(S, "BOM stack kits = stacked access + EB1 core members", bom_qty("C9200L-STACK-KIT"),
      stacked + len(D["core"]["EB1-F1-CS"]["members"]))
claim(S, "BOM IDF UPS = IDF count", bom_qty("SRT1500XLI"), len(D["idfs"]))
claim(S, "BOM RJ45 jacks = ports used", bom_qty("LINK US-1006A"), total_used)

# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------
width = max(len(s) for _, s, _ in results)
for status, section, msg in results:
    print(f"[{status}] {section:<{width}}  {msg}")
counts = Counter(s for s, _, _ in results)
print(f"\n{counts['PASS']} passed, {counts['WARN']} warnings, {counts['FAIL']} failed")
sys.exit(1 if counts["FAIL"] else 0)
