# Roadmap

Every output below draws its numbers from `design/network.yaml`, so they cannot drift apart.

| # | Output | What it is | Status |
|---|--------|------------|--------|
| 1 | Source of truth + validator | YAML design, BOM, 143 automated checks, CI | Done |
| 2 | Design docs | Report rewritten as short Markdown pages (site, WLAN, logical, access, security, budget, decisions) | Next |
| 3 | Physical topology | Clean draw.io diagram in Cisco icons, exported to SVG for README and console | Next |
| 4 | Lab | Scaled emulation of the design (platform to be chosen) with configs and test evidence | Planned |
| 5 | Config generation | Python + Jinja2 renders switch / firewall configs from the YAML | Planned |
| 6 | NetDes console | GitHub Pages site in the same style as the wnet and algo consoles | Planned |
| 7 | LinkedIn post | Project summary with topology image and repo link | After 3 and 4 |
| 8 | CV / portfolio | 2-3 bullets tied to verifiable artefacts in this repo | After 4 |

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
