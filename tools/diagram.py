#!/usr/bin/env python3
"""Draw the hierarchical physical topology from design/network.yaml.

Writes two drawings of the same graph:
  diagrams/topology.dot / .svg            paper style (README): media by colour
  diagrams/topology-blueprint.dot / .svg  blueprint style (console): white linework,
                                          media by line pattern so it reads without colour
SVGs are rendered only when Graphviz is installed.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
D = yaml.safe_load((ROOT / "design" / "network.yaml").read_text())
OUT = ROOT / "diagrams"

PAPER = {
    "graph": 'fontname="Helvetica", bgcolor="white", '
             'label=<<b>EB1-EB2 Hierarchical Physical Topology</b><br/><font point-size="10">'
             'Generated from design/network.yaml</font>>, labelloc=t, fontsize=16',
    "node": 'shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, color="#555555"',
    "edge": 'arrowhead=none, fontname="Helvetica", fontsize=8, fontcolor="#333333"',
    "media": {
        "OS2": 'color="#1f5fbf", penwidth=2.4',
        "OM4": 'color="#13897a", penwidth=1.8',
        "Cat6": 'color="#7a7a7a", penwidth=1.2',
    },
    "ha": 'style=dashed, color="#c0392b"',
    "fill": {"edge": "#fde8e4", "core": "#e3edfb", "dist": "#e6f4f1", "access": "#f3f3f3", "wireless": "#fff4d6", "ext": "#ffffff"},
    "building": 'style="rounded"; color="#9aa7b8"; fontsize=12;',
    "mdf": 'style="rounded,dashed"; color="#b5b5b5";',
    "legend": ('<table border="1" color="#cccccc" cellborder="0" cellpadding="3">'
               '<tr><td colspan="2"><b>Legend</b></td></tr>'
               '<tr><td><font color="#1f5fbf"><b>━━━━</b></font></td><td align="left">OS2 single-mode, 10GBASE-LR</td></tr>'
               '<tr><td><font color="#13897a"><b>━━━━</b></font></td><td align="left">OM4 multimode, 10GBASE-SR</td></tr>'
               '<tr><td><font color="#7a7a7a">━━━━</font></td><td align="left">Cat6 U/UTP, 1G</td></tr>'
               '<tr><td><font color="#c0392b">- - - -</font></td><td align="left">FortiGate HA heartbeat</td></tr>'
               '</table>'),
}

# Blueprint: white ink on a transparent ground (the console draws the blue grid).
# Courier is used for layout metrics; the SVG is then switched to IBM Plex Mono,
# which has the same 0.6 em advance, so labels keep fitting their boxes.
INK, DIM = "#f2f6fb", "#b9cde6"
BLUEPRINT = {
    "graph": 'fontname="Courier", bgcolor="transparent", fontcolor="%s", pad=0.3' % INK,
    "node": 'shape=box, style="rounded", fontname="Courier", fontsize=11, color="%s", fontcolor="%s", penwidth=1.1, margin="0.16,0.07"' % (INK, INK),
    "edge": 'arrowhead=none, fontname="Courier", fontsize=8.5, fontcolor="%s"' % DIM,
    "media": {
        "OS2": 'color="%s:transparent:%s", penwidth=1.1' % (INK, INK),  # double line
        "OM4": 'color="%s", penwidth=1.6' % INK,                          # single line
        "Cat6": 'color="%s", penwidth=1.1, style=dashed' % DIM,           # dashed
    },
    "ha": 'style=dotted, color="%s", penwidth=1.6' % INK,
    "fill": None,
    "building": 'style="rounded,dashed"; color="%s"; fontcolor="%s"; fontsize=12;' % (DIM, INK),
    "mdf": 'style="dotted"; color="%s"; fontcolor="%s";' % (DIM, DIM),
    "legend": ('<table border="1" color="%s" cellborder="0" cellpadding="4" cellspacing="0">'
               '<tr><td colspan="2" align="left"><font color="%s"><b>LEGEND</b></font></td></tr>'
               '<tr><td><font color="%s">══════</font></td><td align="left"><font color="%s">OS2 single-mode, 10GBASE-LR</font></td></tr>'
               '<tr><td><font color="%s">━━━━━━</font></td><td align="left"><font color="%s">OM4 multimode, 10GBASE-SR</font></td></tr>'
               '<tr><td><font color="%s">─ ─ ─ ─</font></td><td align="left"><font color="%s">Cat6 U/UTP, 1G</font></td></tr>'
               '<tr><td><font color="%s">· · · · ·</font></td><td align="left"><font color="%s">FortiGate HA heartbeat</font></td></tr>'
               '</table>') % ((DIM, INK) + (INK, INK) * 2 + (DIM, INK) + (INK, INK)),
}


def build(T: dict) -> str:
    def node(name: str, label: str, kind: str) -> str:
        fill = f', style="rounded,filled", fillcolor="{T["fill"][kind]}"' if T["fill"] else ""
        return f'"{name}" [label=<<b>{name}</b><br/><font point-size="9">{label}</font>>{fill}];'

    lines = [
        "digraph topology {",
        f"  graph [rankdir=TB, splines=true, nodesep=0.35, ranksep=0.6, {T['graph']}];",
        f"  node [{T['node']}];",
        f"  edge [{T['edge']}];",
        "  " + node("ITSC", "University Core (campus L3)", "ext"),
    ]
    fw_model = "FortiGate 200F"
    lines += [
        f'  subgraph cluster_eb2 {{ label="Building EB2"; {T["building"]}',
        f'    subgraph cluster_mdf {{ label="EB2-MDF (server room, floor 1)"; {T["mdf"]}',
        "      " + node("EB2-MDF-FW01", f"{fw_model} (active)", "edge"),
        "      " + node("EB2-MDF-FW02", f"{fw_model} (passive)", "edge"),
        "      " + node("EB2-MDF-CS", "C9300-24T x2, StackWise-480, NM-8X", "core"),
        "      " + node("EB2-MDF-WLC01", "C9800-L-F", "wireless"),
        "      " + node("SERVERS", "Servers / NVR (12 hosts)", "ext"),
        '      {rank=same; "EB2-MDF-FW01"; "EB2-MDF-FW02";}',
        "    }",
    ]

    def access(prefix: str) -> None:
        for dist, spec in D["distribution"].items():
            if dist.startswith(prefix):
                lines.append("    " + node(dist, spec["model"], "dist"))
        for idf, cfg in D["idfs"].items():
            if idf.startswith(prefix):
                f = D["floors"][idf]
                lines.append("    " + node(f"{idf}-AS", f"{len(cfg['stack'])}-switch stack<br/>{f['aps']} APs, "
                                             f"{f['pc']} PC, {f['phone']} phone, {f['cctv']} CCTV", "access"))

    access("EB2")
    lines.append("  }")
    lines += [
        f'  subgraph cluster_eb1 {{ label="Building EB1"; {T["building"]}',
        "    " + node("EB1-F1-CS", "C9200L-24T-4X x2 stack (EB1 core)", "core"),
    ]
    access("EB1")
    lines.append("  }")

    def edge(a: str, b: str, media: str, label: str) -> None:
        lines.append(f'  "{a}" -> "{b}" [{T["media"][media]}, label="{label}"];')

    for l in D["links"]:
        b = l["b"] if l["b"] not in D["idfs"] else f"{l['b']}-AS"
        speed = f"{l['gbps'] // 10}x10G" if l["gbps"] >= 20 else f"{l['gbps']}G"
        label = f"{l['media']} {speed}"
        if l.get("lacp"):
            label += " LACP"
        if l.get("diverse_paths"):
            label += f"\\n{l['diverse_paths']} diverse paths"
        if l.get("backup_gbps"):
            label += f"\\n+ Cat6 {l['backup_gbps']}G backup"
        edge(l["a"], b, l["media"], label)

    lines.append(f'  "EB2-MDF-FW01" -> "EB2-MDF-FW02" [{T["ha"]}, label="HA", constraint=false];')
    edge("EB2-MDF-CS", "SERVERS", "Cat6", "Cat6 1G")
    lines += [
        f'  legend [shape=plaintext, style="", label=<{T["legend"]}>];',
        '  "ITSC" -> legend [style=invis];',
        '  {rank=same; "ITSC"; legend;}',
        "}",
    ]
    return "\n".join(lines) + "\n"


def render(name: str, dot_text: str, post=None) -> None:
    dot_path = OUT / f"{name}.dot"
    dot_path.write_text(dot_text)
    if not shutil.which("dot"):
        print(f"Wrote diagrams/{name}.dot (install Graphviz to render the SVG)")
        return
    svg_path = OUT / f"{name}.svg"
    subprocess.run(["dot", "-Tsvg", str(dot_path), "-o", str(svg_path)], check=True)
    if post:
        svg_path.write_text(post(svg_path.read_text()))
    print(f"Wrote diagrams/{name}.dot and diagrams/{name}.svg")


OUT.mkdir(exist_ok=True)
render("topology", build(PAPER))
render("topology-blueprint", build(BLUEPRINT),
       post=lambda s: s.replace('font-family="Courier,monospace"', 'font-family="IBM Plex Mono, ui-monospace, monospace"')
                        .replace('font-family="Courier"', 'font-family="IBM Plex Mono, ui-monospace, monospace"'))
