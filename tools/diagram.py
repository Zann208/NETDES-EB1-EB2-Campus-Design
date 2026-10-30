#!/usr/bin/env python3
"""Draw the hierarchical physical topology from design/network.yaml.

Writes diagrams/topology.dot and, if Graphviz is installed, diagrams/topology.svg.
Line style encodes the medium: OS2 single-mode (blue, bold), OM4 multimode (teal),
Cat6 copper (grey), HA heartbeat (dashed).
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
D = yaml.safe_load((ROOT / "design" / "network.yaml").read_text())
OUT = ROOT / "diagrams"

STYLE = {
    "OS2": 'color="#1f5fbf", penwidth=2.4',
    "OM4": 'color="#13897a", penwidth=1.8',
    "Cat6": 'color="#7a7a7a", penwidth=1.2',
}
FILL = {"edge": "#fde8e4", "core": "#e3edfb", "dist": "#e6f4f1", "access": "#f3f3f3", "wireless": "#fff4d6", "ext": "#ffffff"}


def node(name: str, label: str, kind: str) -> str:
    return (f'"{name}" [label=<<b>{name}</b><br/><font point-size="9">{label}</font>>, '
            f'fillcolor="{FILL[kind]}"];')


def stack_label(models: list[str]) -> str:
    return " + ".join(m for m in models)


lines = [
    "digraph topology {",
    '  graph [rankdir=TB, splines=true, nodesep=0.35, ranksep=0.6, fontname="Helvetica", '
    'label=<<b>EB1-EB2 Hierarchical Physical Topology</b><br/><font point-size="10">'
    'Generated from design/network.yaml</font>>, labelloc=t, fontsize=16, bgcolor="white"];',
    '  node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, color="#555555"];',
    '  edge [arrowhead=none, fontname="Helvetica", fontsize=8, fontcolor="#333333"];',
    "  " + node("ITSC", "University Core (campus L3)", "ext"),
]

# EB2 MDF cluster: firewalls, core, WLC, servers
fw_model = "FortiGate 200F"
lines += [
    '  subgraph cluster_eb2 { label="Building EB2"; style="rounded"; color="#9aa7b8"; fontsize=12;',
    '    subgraph cluster_mdf { label="EB2-MDF (server room, floor 1)"; style="rounded,dashed"; color="#b5b5b5";',
    "      " + node("EB2-MDF-FW01", f"{fw_model} (active)", "edge"),
    "      " + node("EB2-MDF-FW02", f"{fw_model} (passive)", "edge"),
    "      " + node("EB2-MDF-CS", "C9300-24T x2, StackWise-480, NM-8X", "core"),
    "      " + node("EB2-MDF-WLC01", "C9800-L-F", "wireless"),
    "      " + node("SERVERS", "Servers / NVR (12 hosts)", "ext"),
    '      {rank=same; "EB2-MDF-FW01"; "EB2-MDF-FW02";}',
    "    }",
]
for dist, spec in D["distribution"].items():
    if dist.startswith("EB2"):
        lines.append("    " + node(dist, spec["model"], "dist"))
for idf, cfg in D["idfs"].items():
    if idf.startswith("EB2"):
        f = D["floors"][idf]
        lines.append("    " + node(f"{idf}-AS", f"{len(cfg['stack'])}-switch stack<br/>{f['aps']} APs, "
                                     f"{f['pc']} PC, {f['phone']} phone, {f['cctv']} CCTV", "access"))
lines.append("  }")

lines += [
    '  subgraph cluster_eb1 { label="Building EB1"; style="rounded"; color="#9aa7b8"; fontsize=12;',
    "    " + node("EB1-F1-CS", "C9200L-24T-4X x2 stack (EB1 core)", "core"),
]
for dist, spec in D["distribution"].items():
    if dist.startswith("EB1"):
        lines.append("    " + node(dist, spec["model"], "dist"))
for idf, cfg in D["idfs"].items():
    if idf.startswith("EB1"):
        f = D["floors"][idf]
        lines.append("    " + node(f"{idf}-AS", f"{len(cfg['stack'])}-switch stack<br/>{f['aps']} APs, "
                                     f"{f['pc']} PC, {f['phone']} phone, {f['cctv']} CCTV", "access"))
lines.append("  }")


def edge(a: str, b: str, media: str, label: str, extra: str = "") -> None:
    lines.append(f'  "{a}" -> "{b}" [{STYLE[media]}, label="{label}"{extra}];')


for l in D["links"]:
    a = "ITSC" if l["a"] == "ITSC" else l["a"]
    b = l["b"] if l["b"] not in D["idfs"] else f"{l['b']}-AS"
    speed = f"{l['gbps'] // 10}x10G" if l["gbps"] >= 20 else f"{l['gbps']}G"
    label = f"{l['media']} {speed}"
    if l.get("lacp"):
        label += " LACP"
    if l.get("diverse_paths"):
        label += f"\\n{l['diverse_paths']} diverse paths"
    if l.get("backup_gbps"):
        label += f"\\n+ Cat6 {l['backup_gbps']}G backup"
    edge(a, b, l["media"], label)

lines.append('  "EB2-MDF-FW01" -> "EB2-MDF-FW02" [style=dashed, color="#c0392b", label="HA", constraint=false];')
edge("EB2-MDF-CS", "SERVERS", "Cat6", "Cat6 1G")

# Legend
lines += [
    '  legend [shape=plaintext, style="", label=<<table border="1" color="#cccccc" cellborder="0" cellpadding="3">'
    '<tr><td colspan="2"><b>Legend</b></td></tr>'
    '<tr><td><font color="#1f5fbf"><b>━━━━</b></font></td><td align="left">OS2 single-mode, 10GBASE-LR</td></tr>'
    '<tr><td><font color="#13897a"><b>━━━━</b></font></td><td align="left">OM4 multimode, 10GBASE-SR</td></tr>'
    '<tr><td><font color="#7a7a7a">━━━━</font></td><td align="left">Cat6 U/UTP, 1G</td></tr>'
    '<tr><td><font color="#c0392b">- - - -</font></td><td align="left">FortiGate HA heartbeat</td></tr>'
    '</table>>];',
    '  "ITSC" -> legend [style=invis];',
    '  {rank=same; "ITSC"; legend;}',
    "}",
]

OUT.mkdir(exist_ok=True)
dot_path = OUT / "topology.dot"
dot_path.write_text("\n".join(lines) + "\n")
if shutil.which("dot"):
    subprocess.run(["dot", "-Tsvg", str(dot_path), "-o", str(OUT / "topology.svg")], check=True)
    print("Wrote diagrams/topology.dot and diagrams/topology.svg")
else:
    print("Wrote diagrams/topology.dot (install Graphviz to render the SVG)")
