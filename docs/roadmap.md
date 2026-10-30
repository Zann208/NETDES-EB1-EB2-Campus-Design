# Roadmap

Every output below draws its numbers from `design/network.yaml`, so they cannot drift apart.

| # | Output | What it is | Status |
|---|--------|------------|--------|
| 1 | Source of truth + validator | YAML design, BOM, 143 automated checks, CI | Done |
| 2 | Design docs | docs/design.md, condensed from the report | Done |
| 3 | Physical topology | Generated from the design by tools/diagram.py (SVG + PNG) | Done |
| 4 | Lab | Packet Tracer replica: configured, cabled and addressed by script | Test evidence next |
| 5 | Config generation | Python + Jinja2 renders switch / firewall configs from the YAML | Done |
| 6 | NetDes console | GitHub Pages site built from the design by tools/site.py | Done |
| 7 | LinkedIn post | docs/portfolio.md | Drafted |
| 8 | CV / portfolio | docs/portfolio.md | Drafted |

## Source files: what goes where

| Source file | Destination |
|-------------|-------------|
| Network_Design_Report.pdf (8 Oct) | Master content for docs/ (most complete version) |
| EB1-EB2-Network-Design-20min 2.pptx | Slide content; keep the deck private, reuse figures |
| Presentation Script (3 PDFs) | Superseded drafts of one talk; private |
| Logical_Topology.drawio | diagrams/logical-topology.drawio |
| Physical Topology EB1-EB2 Update (pptx/pdf), EB1-EB2-floorplans.pdf | Floor plans with device IDs; export to assets/ after fixing errata E4 |
| Survey_Data_EB1_EB2.pdf | Source for existing-equipment counts; summarise in docs, do not publish raw |
| Group_2_Network_Project_Master_Guide.pdf, Post_Survey_Plan | Team working notes; private |
| DesignGuideline, Network_Design_Guideline, SurveyShortGuideline, CPE434 slides, survey templates | Instructor material; never publish, cite only |
| Education.pdf (survey request letter) | Never publish: contains 12 students' names and IDs |
| Group photo | Publish only with every member's agreement |
