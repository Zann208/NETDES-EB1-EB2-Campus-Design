# Portfolio text

Ready to paste. Every claim links to something in the repository that a reviewer can check.

## CV / resume (Projects section)

**Campus Network Design, EB1-EB2, Chiang Mai University** (course project, Group 2) — Oct 2026
- Surveyed two academic buildings and designed a 3-tier campus network for 722 peak users and 1,668 devices:
  14 VLANs summarised to one /19, FortiGate HA as the single L3 point, 57 controller-based Wi-Fi 6 APs, THB 7.45 M sourced BOM.
- Rebuilt the design as code: a YAML source of truth, a Python validator with 143 automated checks
  (subnet sizing, PoE, uplink failure, media limits, budget) running in GitHub Actions; it caught 3 errors in the submitted report.
- Generated 15 Cisco IOS configs with Python/Jinja2 (LACP, Rapid-PVST+, HSRP, DHCP, zone ACLs, DHCP snooping, port security)
  and built a Packet Tracer replica, cabled and addressed through its JavaScript scripting API.

Short form (one line): Designed and validated a 1,668-device campus network (3-tier, 14 VLANs, 57 Wi-Fi 6 APs) with a
Python design-as-code pipeline, 143 automated checks and generated Cisco configs.

Skills line: VLSM / IP planning · VLANs, 802.1Q, LACP, Rapid-PVST+ · HSRP · ACLs · Wi-Fi 6 / WLC design ·
Cisco IOS · Packet Tracer · Python (PyYAML, Jinja2) · GitHub Actions

## LinkedIn post

> I turned a university network design project into a working design-as-code repository.
>
> The brief: design the network for two academic buildings at Chiang Mai University. 722 peak users,
> 1,668 devices, three floors each, a server room, and a campus core that hands over at Layer 2.
>
> What we designed:
> - 3-tier campus with a core in each building, so the second building needs 2 fibre links instead of 6
> - A FortiGate HA pair as the only Layer 3 point, gateway for all 14 VLANs
> - 57 Wi-Fi 6 APs sized by max(coverage, capacity): a 90-seat lecture room at 5 Mbps per user needs 3 APs
> - A THB 7.45 M bill of materials with a price source for every line
>
> What I added afterwards:
> - One YAML file as the source of truth for users, VLANs, links and PoE
> - A Python validator with 143 checks (subnet sizing, PoE budgets, uplink failure, media limits, budget arithmetic)
>   running in GitHub Actions. It found three arithmetic errors in our submitted report.
> - Generated Cisco configs and a Packet Tracer replica of the whole network
> - A web console that shows the design, the configs and the live check results
>
> Repo: https://github.com/Zann208/NETDES-EB1-EB2-Campus-Design
> Console: https://zann208.github.io/NETDES-EB1-EB2-Campus-Design/
>
> Thanks to my Group 2 teammates for the site survey and the original report.
>
> #NetworkEngineering #CCNA #CampusNetworking #WiFi6 #NetworkAutomation #Python

Attach `diagrams/topology.png` (or a screenshot of the console Overview) as the image.

## Portfolio card

- **Title:** NETDES: EB1-EB2 Campus Network
- **One-liner:** A 1,668-device campus design rebuilt as code: validated, generated and emulated.
- **Tags:** Campus LAN · Wi-Fi 6 · Cisco IOS · Python · Packet Tracer
- **Links:** repository, console
