#!/usr/bin/env python3
"""
Lab 69.1 -- one intent, four vendors, from the same data.

Chapter 69 sec 5: keep the INTENT in the data and the SYNTAX in the template,
and a new vendor is one new template against data you already have. This renders
the same vendor-neutral interface intent to four vendors with real Jinja, and
shows the render is idempotent (sec 3).

    python3 one_template_four_vendors.py     # needs jinja2 (pip install jinja2)
"""
from jinja2 import Template

# INTENT -- vendor-neutral, straight from the source of truth (ch68). No syntax here.
INTENT = {"name_id": 8, "description": "server-07", "mode": "access", "vlan": 30}

# One template per vendor -- syntax lives here, intent does not.
TEMPLATES = {
    "Cisco IOS-XE": Template(
        "interface Ethernet1/{{ name_id }}\n"
        " description {{ description }}\n"
        " switchport mode access\n switchport access vlan {{ vlan }}"),
    "Arista EOS": Template(
        "interface Ethernet{{ name_id }}\n"
        " description {{ description }}\n"
        " switchport access vlan {{ vlan }}"),
    "Nokia SR Linux": Template(
        "interface ethernet-1/{{ name_id }} {\n"
        "  description \"{{ description }}\"\n"
        "  vlan { access { vlan-id {{ vlan }} } }\n}"),
    "Juniper Junos": Template(
        "interfaces ge-0/0/{{ name_id }} {\n"
        "  description \"{{ description }}\";\n"
        "  unit 0 { family ethernet-switching { vlan { members {{ vlan }} } } }\n}"),
}

if __name__ == "__main__":
    print("One access-port intent, rendered to four vendors (sec 5):\n")
    print(f"  intent = {INTENT}\n")
    first = {}
    for vendor, tmpl in TEMPLATES.items():
        out = tmpl.render(**INTENT)
        first[vendor] = out
        print(f"--- {vendor} ---\n{out}\n")

    # idempotency: rendering again from the same data yields identical output (sec 3)
    same = all(TEMPLATES[v].render(**INTENT) == first[v] for v in TEMPLATES)
    print(f"Idempotent render (same data -> same config, sec 3): {same}")
    print("Adding a fifth vendor is ONE new template against this same intent --")
    print("no data change, and every automation that reads the intent is untouched.")
