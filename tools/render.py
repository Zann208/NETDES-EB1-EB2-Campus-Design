#!/usr/bin/env python3
"""Render Packet Tracer configs, a cabling table and a test plan.

Inputs : design/network.yaml (the design) + lab/lab.yaml (PT stand-ins and cabling)
Outputs: lab/configs/<device>.txt, lab/cabling.md, lab/tests.md

Lints the lab before writing: every port must exist on its PT model and be
used once, and every trunk must carry at least one VLAN.
"""
from __future__ import annotations

import ipaddress
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

ROOT = Path(__file__).resolve().parent.parent
D = yaml.safe_load((ROOT / "design" / "network.yaml").read_text())
L = yaml.safe_load((ROOT / "lab" / "lab.yaml").read_text())
OUT = ROOT / "lab" / "configs"
env = Environment(loader=FileSystemLoader(ROOT / "tools" / "templates"),
                  undefined=StrictUndefined, keep_trailing_newline=True)

LAB_SECRET = "Lab-Only-ChangeMe"   # placeholder; never reuse outside the lab
DNS = "8.8.8.8"                    # ITSC-R loopback stands in for university DNS
SHORT = {"Gi": "GigabitEthernet", "Fa": "FastEthernet"}
errors: list[str] = []


def full(port: str) -> str:
    return SHORT.get(port[:2], "") + port[2:] if port[:2] in SHORT else port


def expand(spec) -> list[str]:
    """'Gi1/0/1-24,Gi1/1/1-4' -> ['Gi1/0/1', ...]."""
    if isinstance(spec, list):
        return spec
    ports = []
    for part in spec.split(","):
        m = re.match(r"(.+/)(\d+)-(\d+)$", part)
        ports += [f"{m.group(1)}{n}" for n in range(int(m.group(2)), int(m.group(3)) + 1)]
    return ports


def ranges(ports: list[str]) -> list[str]:
    """Compress ports into IOS 'interface range' strings."""
    groups = defaultdict(list)
    for p in ports:
        pre, n = re.match(r"(.+/)(\d+)$", p).groups()
        groups[pre].append(int(n))
    out = []
    for pre, nums in groups.items():
        nums.sort()
        start = prev = nums[0]
        for n in nums[1:] + [None]:
            if n is not None and n == prev + 1:
                prev = n
                continue
            out.append(f"{full(pre)}{start}" + (f" - {prev}" if prev != start else ""))
            if n is not None:
                start = prev = n
    return out


def vlan_str(ids) -> str:
    ids = sorted(set(ids))
    parts, i = [], 0
    while i < len(ids):
        j = i
        while j + 1 < len(ids) and ids[j + 1] == ids[j] + 1:
            j += 1
        parts.append(str(ids[i]) if i == j else f"{ids[i]}-{ids[j]}")
        i = j + 1
    return ",".join(parts)


# --------------------------------------------------------------------------
# Design data
# --------------------------------------------------------------------------
VL = {v["id"]: {**v, "net": ipaddress.ip_network(v["subnet"])} for v in D["vlans"]}
SHARED = [i for i, v in VL.items() if v["scope"] == "shared" and i != 40]   # 40 lives in the MDF only
BLD = {
    "EB1": SHARED + [i for i, v in VL.items() if v["scope"] == "EB1"],
    "EB2": SHARED + [i for i, v in VL.items() if v["scope"] == "EB2"],
    "ALL": list(VL),
}
ZONE_NETS = defaultdict(list)
for v in VL.values():
    ZONE_NETS[v["zone"]].append(v["net"])


def vlan_by_role(building: str, base: str) -> int:
    """'STAFF' in EB2 -> 210; shared names map directly."""
    for i in BLD[building]:
        n = VL[i]["name"]
        if n == base or n == f"{building}-{base}":
            return i
    raise KeyError(f"{base} in {building}")


def wc(net) -> str:
    return f"{net.network_address} {net.hostmask}"


# --------------------------------------------------------------------------
# Lint the cabling
# --------------------------------------------------------------------------
used = defaultdict(set)
dev_ports = {}
for name, dev in L["devices"].items():
    m = L["models"][dev["model"]]
    dev_ports[name] = set(expand(m["ports"])) if "ports" in m else None


def take(dev: str, port: str) -> None:
    if dev_ports[dev] is not None and port not in dev_ports[dev]:
        errors.append(f"{dev}: port {port} does not exist on {L['devices'][dev]['model']}")
    if port in used[dev]:
        errors.append(f"{dev}: port {port} used twice")
    used[dev].add(port)


for link in L["links"]:
    for p in link["a_ports"]:
        take(link["a"], p)
    for p in link["b_ports"]:
        take(link["b"], p)
    if len(link["a_ports"]) != len(link["b_ports"]):
        errors.append(f"{link['a']}-{link['b']}: port count mismatch")
for name, dev in L["devices"].items():
    if dev["model"] == "2960-24TT" and name.endswith("-AS"):
        for p in L["access_ports"]:
            take(name, p)
for p in L["core_ports"]:
    take("EB2-MDF-CS", p)


# --------------------------------------------------------------------------
# Switches
# --------------------------------------------------------------------------
def dev_vlans(name: str) -> list[int]:
    dev = L["devices"][name]
    if "vlans" in dev:
        return dev["vlans"]
    return BLD.get(dev.get("building", "ALL"), list(VL))


mgmt = VL[10]["net"]
switch_t = env.get_template("switch.j2")
configs = {}
for name, dev in L["devices"].items():
    model = L["models"][dev["model"]]
    if model["kind"] not in ("l2switch", "l3switch") or name == "ITSC-SW":
        continue
    mine = dev_vlans(name)
    is_access = name.endswith("-AS")
    uplinks, pos = [], {}
    for link in L["links"]:
        if name not in (link["a"], link["b"]):
            continue
        side = "a" if link["a"] == name else "b"
        peer = link["b"] if side == "a" else link["a"]
        if link["kind"] == "fw_trunk":
            allowed = list(VL)
        elif link["kind"] == "wlc_trunk":
            allowed = [v for v in L["devices"][peer]["vlans"] if v in mine]
        else:
            allowed = [v for v in mine if v in dev_vlans(peer)]
        if not allowed:
            errors.append(f"{name}->{peer}: trunk carries no VLANs")
        upper_end = side == "a" and link.get("down")
        lower_end = side == "b" and link.get("down")
        for port in link[f"{side}_ports"]:
            uplinks.append({
                "port": full(port),
                "desc": f"{'BACKUP ' if link.get('backup') else ''}to {peer} ({link['design_link']})",
                "allowed": vlan_str(allowed),
                "root_guard": bool(upper_end) and not link.get("po"),
                "cost": 200 if (lower_end and link.get("backup")) else None,
                "trust": is_access and bool(lower_end) and not link.get("po"),
                "po": link.get("po"),
            })
        if link.get("po"):
            pos[link["po"]] = {"po": link["po"], "desc": f"LACP to {peer}", "allowed": vlan_str(allowed),
                               "root_guard": bool(upper_end), "trust": is_access and bool(lower_end)}
    edges = []
    b = dev.get("building")
    if is_access:
        for port, ap in L["access_ports"].items():
            edges.append({"port": full(port), "desc": ap["role"],
                          "vlan": vlan_by_role(b, ap["vlan"]),
                          "voice": vlan_by_role(b, ap["voice"]) if ap.get("voice") else None,
                          "port_security": ap.get("port_security", False)})
    if name == "EB2-MDF-CS":
        for port, cp in L["core_ports"].items():
            edges.append({"port": full(port), "desc": cp["role"], "vlan": vlan_by_role("ALL", cp["vlan"]),
                          "voice": None, "port_security": False})
    unused = sorted(dev_ports[name] - used[name], key=lambda p: [int(x) for x in re.findall(r"\d+", p)])
    snoop = [i for i in mine if VL[i]["dhcp"] == "pool"]
    configs[name] = switch_t.render(
        name=name, dev=dev, lab_secret=LAB_SECRET,
        vlans=[VL[i] for i in sorted(mine)],
        vlan_list=vlan_str(mine), is_access=is_access, snoop_vlans=vlan_str(snoop),
        l3cap=model["kind"] == "l3switch", uplinks=uplinks, portchannels=list(pos.values()),
        edges=edges, unused=ranges(unused),
        mgmt_mask=str(mgmt.netmask), mgmt_gw=str(mgmt.network_address + 1))

# --------------------------------------------------------------------------
# Firewalls (ISR4331 stand-ins)
# --------------------------------------------------------------------------
svc = D["services"]
transit = ipaddress.ip_network(svc["transit"]["subnet"])


def acl_rules(zone: str) -> list[str]:
    rules = ["permit udp any any eq bootps",                 # DHCP to the gateway
             "permit udp any host 224.0.0.2 eq 1985"]   # HSRP hellos between FW01/FW02
    for rule in D["policy"][zone]:
        (action, target), = rule.items()
        if target == "any":
            rules.append(f"{action} ip any any")
        elif target == "internal":
            rules.append(f"{action} ip any {wc(ipaddress.ip_network(D['addressing']['faculty_block']))}")
        elif action == "permit_host":
            rules.append(f"permit ip any host {svc[target]}")
        elif action == "permit_return":
            for n in ZONE_NETS[target]:
                rules.append(f"permit tcp any {wc(n)} established")
                rules.append(f"permit icmp any {wc(n)} echo-reply")
        else:
            rules += [f"{action} ip any {wc(n)}" for n in ZONE_NETS[target]]
    return rules


acls = [{"name": f"ZONE-{z}-IN", "rules": acl_rules(z)} for z in D["policy"]]
fw_t = env.get_template("firewall.j2")
fws = [n for n, d in L["devices"].items() if d.get("role") == "firewall"]
for idx, name in enumerate(fws):
    dev = L["devices"][name]
    subifs, pools = [], []
    for i in sorted(VL):
        v = VL[i]
        net = v["net"]
        subifs.append({"id": i, "name": v["name"], "ip": str(net.network_address + 2 + idx),
                       "mask": str(net.netmask), "gateway": str(net.network_address + 1),
                       "acl": f"ZONE-{v['zone']}-IN" if v["zone"] in D["policy"] else None})
        if v["dhcp"] != "pool":
            continue
        first, last = int(net.network_address) + 11, int(net.broadcast_address) - 1
        mid = (first + last) // 2
        mine = (first, mid) if idx == 0 else (mid + 1, last)
        other = (mid + 1, last) if idx == 0 else (first, mid)
        ip = ipaddress.ip_address
        pools.append({"name": v["name"], "network": str(net.network_address), "mask": str(net.netmask),
                      "gateway": str(net.network_address + 1),
                      "net_first": str(net.network_address + 1), "reserved_last": str(net.network_address + 10),
                      "other_first": str(ip(other[0])), "other_last": str(ip(other[1])),
                      "serves": f"{ip(mine[0])}-{ip(mine[1])}",
                      "option43": svc["wlc_mgmt"] if i == 20 else None})
    configs[name] = fw_t.render(
        name=name, dev=dev, lab_secret=LAB_SECRET, pools=pools, acls=acls, subifs=subifs, dns=DNS,
        outside_ip=str(transit.network_address + 2 + idx), outside_mask=str(transit.netmask),
        outside_vip=svc["transit"]["fw_vip"], itsc_ip=svc["transit"]["itsc"],
        ha_ip=f"192.168.255.{1 + idx}")
    if idx == 0:
        fw01_pools = pools

# --------------------------------------------------------------------------
# ITSC stand-ins
# --------------------------------------------------------------------------
summary = ipaddress.ip_network(D["addressing"]["advertised_summary"])
configs["ITSC-R"] = f"""! ITSC-R - stand-in for the University Core (ITSC)
! Generated by tools/render.py. Do not edit by hand.
!
enable
configure terminal
hostname ITSC-R
no ip domain-lookup
interface GigabitEthernet0/0
 description Transit VLAN 900 to Faculty of Education (via ITSC-SW)
 ip address {svc['transit']['itsc']} {transit.netmask}
 no shutdown
interface Loopback0
 description Stand-in for the Internet and university DNS
 ip address {DNS} 255.255.255.255
! Return route for the faculty summary, next hop = firewall HA virtual IP (no NAT)
ip route {summary.network_address} {summary.netmask} {svc['transit']['fw_vip']}
end
write memory
"""
configs["ITSC-SW"] = """! ITSC-SW - ITSC handover segment, VLAN 900
! Generated by tools/render.py. Do not edit by hand.
!
enable
configure terminal
hostname ITSC-SW
no ip domain-lookup
vlan 900
 name OUTSIDE
interface range FastEthernet0/1 - 3
 description transit: ITSC-R, FW01, FW02
 switchport mode access
 switchport access vlan 900
 spanning-tree portfast
 no shutdown
interface range FastEthernet0/4 - 24 , GigabitEthernet0/1 - 2
 shutdown
end
write memory
"""

if errors:
    print("Lab lint failed:")
    print("\n".join(f"  - {e}" for e in errors))
    sys.exit(1)

# --------------------------------------------------------------------------
# Write outputs
# --------------------------------------------------------------------------
OUT.mkdir(parents=True, exist_ok=True)
for old in OUT.glob("*.txt"):
    old.unlink()
for name, text in configs.items():
    (OUT / f"{name}.txt").write_text(text)

rows = ["| # | Device A | Port(s) A | Device B | Port(s) B | Lab cable | Real design link |",
        "|---|----------|-----------|----------|-----------|-----------|------------------|"]
for n, link in enumerate(L["links"], 1):
    cable = "Copper straight-through" if link["kind"] != "ha" else "Copper cross-over"
    bundle = f" (Po{link['po']}, LACP)" if link.get("po") else ""
    rows.append(f"| {n} | {link['a']} | {', '.join(link['a_ports'])}{bundle} | {link['b']} | "
                f"{', '.join(link['b_ports'])} | {cable} | {link['design_link']} |")
edge_rows = ["| Port | Role | VLAN (EB1 / EB2) |", "|------|------|------------------|"]
for port, ap in L["access_ports"].items():
    v1, v2 = vlan_by_role("EB1", ap["vlan"]), vlan_by_role("EB2", ap["vlan"])
    voice = f" + voice {vlan_by_role('EB1', ap['voice'])}" if ap.get("voice") else ""
    edge_rows.append(f"| {port} | {ap['role']} | {v1} / {v2}{voice} |")
(ROOT / "lab" / "cabling.md").write_text(
    "# Lab cabling\n\nGenerated by `tools/render.py`. Each lab link stands for the real link in the last column; "
    "PT links are 1G copper, the design uses 10G fibre.\n\n" + "\n".join(rows) +
    "\n\n## Access switch edge ports (every access switch)\n\n" + "\n".join(edge_rows) +
    "\n\nCore edge ports: Gi1/0/23 admin PC (VLAN 10), Gi1/0/24 NVR (VLAN 40). "
    "Unused ports are shut down in VLAN 999.\n\n## Static hosts\n\n| Host | IP | VLAN | Where |\n|---|---|---|---|\n" +
    "\n".join(f"| {h} | {s['ip']} | {s['vlan']} | {s['where']} |" for h, s in L["static_hosts"].items()) +
    "\n\n## DHCP split (FW01 serves the lower half, FW02 the upper half)\n\n| Pool | Network | FW01 range |\n|---|---|---|\n" +
    "\n".join(f"| {p['name']} | {p['network']}/{ipaddress.ip_network(p['network'] + '/' + p['mask']).prefixlen} | {p['serves']} |"
              for p in fw01_pools) + "\n")

env.get_template("tests.md.j2").stream(
    vl=VL, svc=svc, dns=DNS, hosts=L["static_hosts"], devices=L["devices"]).dump(str(ROOT / "lab" / "tests.md"))

print(f"Rendered {len(configs)} configs to {OUT.relative_to(ROOT)}/, plus lab/cabling.md and lab/tests.md")
