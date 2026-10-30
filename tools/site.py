#!/usr/bin/env python3
"""Build the design console (site/index.html) from the design.

Everything shown on the page comes from design/network.yaml, design/bom.csv,
lab/configs/, lab/tests.md, diagrams/topology-blueprint.svg and a live run of
tools/validate.py, so the console cannot disagree with the repository.
"""
from __future__ import annotations

import csv
import html
import ipaddress
import json
import shutil
from datetime import date
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
D = yaml.safe_load((ROOT / "design" / "network.yaml").read_text())
BOM = list(csv.DictReader((ROOT / "design" / "bom.csv").open()))
OUT = ROOT / "site"

val = subprocess.run([sys.executable, str(ROOT / "tools" / "validate.py")], capture_output=True, text=True)
checks = []
for line in val.stdout.splitlines():
    if line.startswith("["):
        status, rest = line[1:5], line[7:]
        section, msg = rest.split(None, 1)
        checks.append({"s": status, "sec": section, "msg": msg.strip()})

vlans = []
for v in D["vlans"]:
    net = ipaddress.ip_network(v["subnet"])
    vlans.append({**{k: v[k] for k in ("id", "name", "scope", "subnet", "endpoints", "growth", "zone")},
                  "gw": str(net.network_address + 1), "usable": net.num_addresses - 2,
                  "need": -(-int(v["endpoints"] * (1 + v["growth"]) * 100) // 100)})

floors = [{"id": k, **v} for k, v in D["floors"].items()]
bom = [{**r, "qty": int(r["qty"]), "unit_thb": int(r["unit_thb"])} for r in BOM]
configs = {p.stem: p.read_text() for p in sorted((ROOT / "lab" / "configs").glob("*.txt"))}
tests = []
for line in (ROOT / "lab" / "tests.md").read_text().splitlines():
    cells = [c.strip() for c in line.strip("|").split("|")]
    if line.startswith("| T") and len(cells) >= 4:
        tests.append({"id": cells[0], "what": " / ".join(cells[1:-3]) if len(cells) > 5 else cells[1],
                      "expected": cells[-3], "actual": cells[-2], "status": cells[-1]})
svg = (ROOT / "diagrams" / "topology-blueprint.svg").read_text()
svg = svg[svg.index("<svg"):]

data = {"vlans": vlans, "floors": floors, "bom": bom, "configs": configs, "tests": tests,
        "checks": checks, "ssids": D["ssids"], "policy": D["policy"], "meta": D["meta"],
        "links": D["links"], "idfs": D["idfs"], "build": date.today().isoformat()}

page = (ROOT / "tools" / "templates" / "site.html").read_text()
page = page.replace("/*__DATA__*/null", json.dumps(data, separators=(",", ":"), default=str).replace("</", "<\\/"))
page = page.replace("<!--__SVG__-->", svg)
OUT.mkdir(exist_ok=True)
(OUT / "index.html").write_text(page)
(OUT / ".nojekyll").write_text("")
shutil.copytree(ROOT / "tools" / "templates" / "fonts", OUT / "fonts", dirs_exist_ok=True)
shutil.copy(ROOT / "lab" / "pt-topology.png", OUT / "pt-topology.png")
print(f"Wrote site/index.html ({len(page) // 1024} KB): {len(checks)} checks, {len(configs)} configs, {len(tests)} tests")
