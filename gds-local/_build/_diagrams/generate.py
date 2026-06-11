#!/usr/bin/env python3
"""
Generate D2 architecture diagrams from a Structurizr DSL model.

Parses model.dsl, generates .d2 source files for each view (plus anti-pattern
diagrams), then renders them to SVG via the d2 CLI.

Usage:
    python3 generate.py        (run from the _diagrams/ directory)
"""

import os
import re
import subprocess
import shutil
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
MODEL_PATH = SCRIPT_DIR / "model.dsl"
THEME_PATH = SCRIPT_DIR / "theme.d2"
VIEWS_DIR = SCRIPT_DIR / "views"
OUTPUT_DIR = SCRIPT_DIR / "output"


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def truncate(text, max_len=60):
    """Truncate text to max_len chars, adding ellipsis if needed."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def parse_model(dsl_text):
    """
    Parse Structurizr DSL and return:
      - elements: dict of varname -> {type, name, description, tag}
      - relationships: list of {source, target, label, technology}
      - views: list of {type, element, key, description, include, exclude}
    """
    elements = {}
    relationships = []
    views = []

    # Match element declarations:
    #   varname = type "Name" "Description" "tag"
    elem_re = re.compile(
        r'^\s*(\w+)\s*=\s*(person|softwareSystem)\s+'
        r'"([^"]+)"\s+"([^"]+)"\s*(?:"([^"]+)")?\s*$'
    )

    # Match relationships:
    #   source -> target "label" "technology"
    rel_re = re.compile(
        r'^\s*(\w+)\s*->\s*(\w+)\s+"([^"]+)"\s*(?:"([^"]+)")?\s*$'
    )

    # Match view definitions:
    #   systemContext element "key" "description" {
    view_re = re.compile(
        r'^\s*systemContext\s+(\w+)\s+"([^"]+)"\s+"([^"]+)"\s*\{\s*$'
    )

    # Match include/exclude lines within views
    include_re = re.compile(r'^\s*include\s+(.+)$')
    exclude_re = re.compile(r'^\s*exclude\s+(.+)$')

    in_view = False
    current_view = None

    for line in dsl_text.splitlines():
        # Check for element declaration
        m = elem_re.match(line)
        if m:
            varname, etype, name, desc, tag = m.groups()
            elements[varname] = {
                "type": etype,
                "name": name,
                "description": desc,
                "tag": tag or ("actor" if etype == "person" else "system"),
            }
            continue

        # Check for relationship
        m = rel_re.match(line)
        if m:
            source, target, label, tech = m.groups()
            relationships.append({
                "source": source,
                "target": target,
                "label": label,
                "technology": tech or "",
            })
            continue

        # Check for view definition
        m = view_re.match(line)
        if m:
            elem, key, desc = m.groups()
            current_view = {
                "type": "systemContext",
                "element": elem,
                "key": key,
                "description": desc,
                "include": [],
                "exclude": [],
            }
            in_view = True
            continue

        if in_view:
            # Check for closing brace
            if line.strip() == "}":
                views.append(current_view)
                in_view = False
                current_view = None
                continue

            m = include_re.match(line)
            if m:
                items = m.group(1).strip().split()
                current_view["include"].extend(items)
                continue

            m = exclude_re.match(line)
            if m:
                items = m.group(1).strip().split()
                current_view["exclude"].extend(items)
                continue

    return elements, relationships, views


def resolve_view_elements(view, elements):
    """
    Resolve which element varnames are included in a view.
    Handles `*` (all elements) and explicit include/exclude lists.
    """
    includes = view["include"]
    excludes = view["exclude"]

    if "*" in includes:
        included = set(elements.keys())
    else:
        included = set(includes)

    excluded = set(excludes)
    return included - excluded


# ---------------------------------------------------------------------------
# D2 generation
# ---------------------------------------------------------------------------

def generate_view_d2(view, elements, relationships, theme_content):
    """Generate D2 source for a single view."""
    included = resolve_view_elements(view, elements)

    lines = []
    # Theme
    lines.append(theme_content)
    lines.append("")
    # Layout direction
    lines.append("direction: down")
    lines.append("")
    # Title comment
    lines.append(f"# {view['description']}")
    lines.append("")

    # Nodes
    for varname in sorted(included):
        if varname not in elements:
            continue
        elem = elements[varname]
        label = elem["name"]
        tag = elem["tag"]
        lines.append(f"{varname}: {{")
        lines.append(f'  label: "{label}"')
        lines.append(f"  class: {tag}")
        lines.append("}")
        lines.append("")

    # Edges — only where both source and target are in the view
    for rel in relationships:
        if rel["source"] in included and rel["target"] in included:
            if rel["source"] not in elements or rel["target"] not in elements:
                continue
            lines.append(
                f'{rel["source"]} -> {rel["target"]}: "{rel["label"]}"'
            )

    lines.append("")
    return "\n".join(lines)


def generate_antipattern_d2(key, title, nodes, edges, theme_content):
    """Generate a hard-coded anti-pattern D2 diagram."""
    lines = []
    lines.append(theme_content)
    lines.append("")
    lines.append("direction: down")
    lines.append("")
    lines.append(f"# Anti-pattern: {title}")
    lines.append("")

    for node_id, label in nodes:
        lines.append(f"{node_id}: {{")
        lines.append(f'  label: "{label}"')
        lines.append("  class: antipattern")
        lines.append("}")
        lines.append("")

    for src, tgt, label in edges:
        lines.append(f'{src} -> {tgt}: "{label}"')

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Anti-pattern definitions
# ---------------------------------------------------------------------------

ANTIPATTERNS = [
    {
        "key": "p1-anti",
        "title": "Phase 1 Anti-pattern: Generic e-form producing flat PDF",
        "nodes": [
            ("applicant", "Applicant"),
            ("generic_form", "Generic E-Form\\nNo rules, no validation"),
            ("flat_pdf", "Flat PDF\\nUnstructured submission"),
            ("basic_metadata", "Basic Metadata\\nManual re-keying required"),
            ("back_office", "Back Office\\nOfficer re-types everything"),
        ],
        "edges": [
            ("applicant", "generic_form", "Fills in generic form"),
            ("generic_form", "flat_pdf", "Generates flat PDF"),
            ("generic_form", "basic_metadata", "Captures minimal fields"),
            ("flat_pdf", "back_office", "Emailed to officer"),
            ("basic_metadata", "back_office", "Manually reconciled"),
        ],
    },
    {
        "key": "p2-anti",
        "title": "Phase 2 Anti-pattern: Manual redrawing and email chasing",
        "nodes": [
            ("pdf_plans", "PDF Plans\\nScanned drawings"),
            ("officer", "Officer\\nManual validation"),
            ("gis", "GIS System\\nOfficer redraws polygons"),
            ("email", "Email\\nChases missing info"),
            ("applicant", "Applicant / Agent\\nDelayed response"),
        ],
        "edges": [
            ("pdf_plans", "officer", "Reviews paper plans"),
            ("officer", "gis", "Manually redraws site boundary"),
            ("officer", "email", "Sends missing-info request"),
            ("email", "applicant", "Untracked correspondence"),
            ("applicant", "email", "Replies with attachments"),
        ],
    },
    {
        "key": "p3-anti",
        "title": "Phase 3 Anti-pattern: Contended database for public + officer access",
        "nodes": [
            ("public", "Public\\nViewing applications"),
            ("officer", "Officer\\nProcessing cases"),
            ("single_db", "Single Database\\nContended read/write"),
            ("no_cache", "No Caching\\nEvery request hits DB"),
        ],
        "edges": [
            ("public", "single_db", "Direct DB queries"),
            ("officer", "single_db", "Read/write case data"),
            ("single_db", "no_cache", "No read replica"),
            ("public", "no_cache", "Slow page loads"),
        ],
    },
    {
        "key": "p4-anti",
        "title": "Phase 4 Anti-pattern: Manual ZIP export emailed to PINS",
        "nodes": [
            ("officer", "Officer\\nManual export"),
            ("file_system", "File System\\nScattered documents"),
            ("zip_file", "ZIP Archive\\nManual assembly"),
            ("email", "Email\\nLarge attachment"),
            ("pins", "PINS\\nManual re-upload"),
        ],
        "edges": [
            ("officer", "file_system", "Gathers decision docs"),
            ("file_system", "zip_file", "Manual ZIP creation"),
            ("zip_file", "email", "Attached to email"),
            ("email", "pins", "Sent to inspectorate"),
            ("pins", "pins", "Re-uploaded manually"),
        ],
    },
]


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def render_d2_to_svg(d2_path, svg_path):
    """Render a .d2 file to SVG using the d2 CLI."""
    cmd = ["d2", "--theme", "0", "--pad", "20", str(d2_path), str(svg_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR rendering {d2_path.name}: {result.stderr.strip()}")
        return False
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=== D2 Diagram Generator ===")
    print()

    # Check d2 is available
    if not shutil.which("d2"):
        print("ERROR: d2 CLI not found on PATH.")
        print("Install from https://d2lang.com or via: brew install d2")
        sys.exit(1)

    # Read inputs
    print(f"Reading model: {MODEL_PATH}")
    dsl_text = MODEL_PATH.read_text()

    print(f"Reading theme: {THEME_PATH}")
    theme_content = THEME_PATH.read_text().rstrip()

    # Parse
    elements, relationships, views = parse_model(dsl_text)
    print(f"  Found {len(elements)} elements, {len(relationships)} relationships, {len(views)} views")
    print()

    # Ensure output directories exist
    VIEWS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Generate view D2 files
    print("Generating view D2 files...")
    d2_files = []
    for view in views:
        filename = f"{view['key']}.d2"
        d2_path = VIEWS_DIR / filename
        content = generate_view_d2(view, elements, relationships, theme_content)
        d2_path.write_text(content)
        d2_files.append(d2_path)
        print(f"  Created: views/{filename}")

    print()

    # Generate anti-pattern D2 files
    print("Generating anti-pattern D2 files...")
    for ap in ANTIPATTERNS:
        filename = f"{ap['key']}.d2"
        d2_path = VIEWS_DIR / filename
        content = generate_antipattern_d2(
            ap["key"], ap["title"], ap["nodes"], ap["edges"], theme_content
        )
        d2_path.write_text(content)
        d2_files.append(d2_path)
        print(f"  Created: views/{filename}")

    print()

    # Render all D2 files to SVG
    print("Rendering D2 -> SVG...")
    success_count = 0
    fail_count = 0
    for d2_path in d2_files:
        svg_name = d2_path.stem + ".svg"
        svg_path = OUTPUT_DIR / svg_name
        if render_d2_to_svg(d2_path, svg_path):
            print(f"  Rendered: output/{svg_name}")
            success_count += 1
        else:
            fail_count += 1

    print()
    print(f"Done: {success_count} SVGs rendered, {fail_count} failures.")
    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
