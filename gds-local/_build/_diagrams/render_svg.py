#!/usr/bin/env python3
"""
Renders architecture diagrams as SVG from a structured layout definition.

Produces compact, grid-aligned diagrams matching the GOV.UK aesthetic:
- Zone containers (dashed background boxes with headers)
- Rectangular nodes with two-line labels, coloured borders
- Straight-line connectors with arrowheads (horizontal/vertical/L-shaped)
- Database cylinder shapes for data stores
- Consistent spacing and alignment

Usage: python3 render_svg.py
"""

import os
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SCRIPT_DIR / "output"

# ---------------------------------------------------------------------------
# GOV.UK Colour Palette
# ---------------------------------------------------------------------------

COLOURS = {
    "system": "#1d70b8",
    "system-green": "#00703c",
    "antipattern": "#d4351c",
    "database": "#505a5f",
    "integration": "#1d70b8",
    "external": "#0b0c0c",
    "zone-fill": "#f8f8f8",
    "zone-stroke": "#b1b4b6",
    "text": "#0b0c0c",
    "text-light": "#505a5f",
    "connector": "#0b0c0c",
    "connector-blue": "#1d70b8",
    "white": "#ffffff",
}

FONT = "'GDS Transport', Arial, sans-serif"


def xml_escape(text):
    """Escape text for safe inclusion in SVG/XML."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# ---------------------------------------------------------------------------
# SVG Primitives
# ---------------------------------------------------------------------------


def svg_header(width, height):
    return (
        f'<svg viewBox="0 0 {width} {height}" width="100%" height="100%" '
        f'xmlns="http://www.w3.org/2000/svg" '
        f'style="font-family: {FONT};">\n'
        f'  <defs>\n'
        f'    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" '
        f'markerWidth="6" markerHeight="6" orient="auto-start-reverse">\n'
        f'      <path d="M 0 0 L 10 5 L 0 10 z" fill="{COLOURS["connector"]}" />\n'
        f'    </marker>\n'
        f'    <marker id="arrow-blue" viewBox="0 0 10 10" refX="9" refY="5" '
        f'markerWidth="6" markerHeight="6" orient="auto-start-reverse">\n'
        f'      <path d="M 0 0 L 10 5 L 0 10 z" fill="{COLOURS["connector-blue"]}" />\n'
        f'    </marker>\n'
        f'  </defs>\n'
    )


def svg_footer():
    return '</svg>\n'


def svg_zone(x, y, w, h, label):
    """Render a zone container (dashed background box with header label)."""
    return (
        f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" '
        f'fill="{COLOURS["zone-fill"]}" stroke="{COLOURS["zone-stroke"]}" '
        f'stroke-dasharray="4" rx="4"/>\n'
        f'  <text x="{x + 10}" y="{y + 16}" font-size="11" font-weight="bold" '
        f'fill="{COLOURS["text-light"]}">{xml_escape(label)}</text>\n'
    )


def svg_node(x, y, w, h, label, subtitle="", style="system"):
    """Render a rectangular node with border colour based on style."""
    stroke = COLOURS.get(style, COLOURS["system"])
    fill = COLOURS["white"]
    text_fill = COLOURS["text"]

    lines = []
    lines.append(
        f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="2" rx="4"/>\n'
    )
    if subtitle:
        lines.append(
            f'  <text x="{x + w // 2}" y="{y + h // 2 - 5}" font-size="14" '
            f'font-weight="bold" text-anchor="middle" fill="{text_fill}">{xml_escape(label)}</text>\n'
        )
        lines.append(
            f'  <text x="{x + w // 2}" y="{y + h // 2 + 12}" font-size="11" '
            f'text-anchor="middle" fill="{COLOURS["text-light"]}">{xml_escape(subtitle)}</text>\n'
        )
    else:
        lines.append(
            f'  <text x="{x + w // 2}" y="{y + h // 2 + 5}" font-size="14" '
            f'font-weight="bold" text-anchor="middle" fill="{text_fill}">{xml_escape(label)}</text>\n'
        )
    return "".join(lines)


def svg_node_filled(x, y, w, h, label, fill_colour, text_colour="#ffffff"):
    """Render a solid-filled node (e.g. API Gateway)."""
    lines = []
    lines.append(
        f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" '
        f'fill="{fill_colour}" rx="4"/>\n'
    )
    # Rotated text for tall narrow nodes
    if h > w * 1.5:
        cx, cy = x + w // 2, y + h // 2
        lines.append(
            f'  <text x="{cx}" y="{cy}" font-size="14" font-weight="bold" '
            f'text-anchor="middle" fill="{text_colour}" '
            f'transform="rotate(-90 {cx} {cy})">{xml_escape(label)}</text>\n'
        )
    else:
        lines.append(
            f'  <text x="{x + w // 2}" y="{y + h // 2 + 5}" font-size="14" '
            f'font-weight="bold" text-anchor="middle" fill="{text_colour}">{xml_escape(label)}</text>\n'
        )
    return "".join(lines)


def svg_database(x, y, w, h, label, style="database"):
    """Render a database cylinder shape."""
    stroke = COLOURS.get(style, COLOURS["database"])
    fill = COLOURS["white"]
    # Cylinder: rect with curved top
    lines = []
    lines.append(
        f'  <path d="M {x} {y + 15} L {x + w} {y + 15} L {x + w} {y + h} L {x} {y + h} Z" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="2"/>\n'
    )
    lines.append(
        f'  <path d="M {x} {y + 15} Q {x + w // 2} {y + 25} {x + w} {y + 15}" '
        f'fill="none" stroke="{stroke}" stroke-width="1"/>\n'
    )
    # Top ellipse
    lines.append(
        f'  <ellipse cx="{x + w // 2}" cy="{y + 15}" rx="{w // 2}" ry="10" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="2"/>\n'
    )
    lines.append(
        f'  <text x="{x + w // 2}" y="{y + h // 2 + 12}" font-size="14" '
        f'font-weight="bold" text-anchor="middle" fill="{COLOURS["text"]}">{xml_escape(label)}</text>\n'
    )
    return "".join(lines)


def svg_line(x1, y1, x2, y2, style="connector", dashed=False):
    """Draw a straight line with arrowhead."""
    colour = COLOURS.get(style, COLOURS["connector"])
    marker = "arrow-blue" if "blue" in style else "arrow"
    dash = ' stroke-dasharray="4"' if dashed else ""
    return (
        f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
        f'stroke="{colour}" stroke-width="2"{dash} marker-end="url(#{marker})"/>\n'
    )


def svg_path(points, style="connector", dashed=False):
    """Draw a multi-segment path with arrowhead. Points is list of (x, y) tuples."""
    colour = COLOURS.get(style, COLOURS["connector"])
    marker = "arrow-blue" if "blue" in style else "arrow"
    dash = ' stroke-dasharray="4"' if dashed else ""
    d = f"M {points[0][0]} {points[0][1]}"
    for px, py in points[1:]:
        d += f" L {px} {py}"
    return (
        f'  <path d="{d}" fill="none" stroke="{colour}" stroke-width="2"{dash} '
        f'marker-end="url(#{marker})"/>\n'
    )


def svg_label(x, y, text, style="connector"):
    """Draw a connector label at a specific position."""
    colour = COLOURS.get(style, COLOURS["connector"])
    return (
        f'  <text x="{x}" y="{y}" font-size="11" font-style="italic" '
        f'text-anchor="middle" fill="{colour}">{xml_escape(text)}</text>\n'
    )


def svg_connector(x1, y1, x2, y2, label="", style="connector", dashed=False):
    """Draw a straight or L-shaped connector with arrowhead (convenience wrapper)."""
    lines = []
    if abs(y2 - y1) < 5 or abs(x2 - x1) < 5:
        lines.append(svg_line(x1, y1, x2, y2, style, dashed))
    else:
        lines.append(svg_path([(x1, y1), (x2, y1), (x2, y2)], style, dashed))

    if label:
        lx = (x1 + x2) // 2
        ly = min(y1, y2) - 8
        lines.append(svg_label(lx, ly, label, style))

    return "".join(lines)


# ---------------------------------------------------------------------------
# Diagram Definitions (layout + content)
# ---------------------------------------------------------------------------

def render_overview_strategic():
    """Render the main overview diagram matching the original aesthetic."""
    W, H = 920, 490
    svg = svg_header(W, H)

    # Zone containers (3 columns) — top pushed down to leave room for UPRN label
    svg += svg_zone(10, 50, 230, 420, "PUBLIC / PRESENTATION")
    svg += svg_zone(255, 50, 140, 420, "INTEGRATION")
    svg += svg_zone(410, 50, 500, 420, "CORE BACK-OFFICE & DATA")

    # Public / Presentation nodes
    svg += svg_node(30, 95, 190, 50, "Rules Engine (Forms)", "e.g. PlanX", "system")
    svg += svg_node(30, 175, 190, 50, "Identity / Auth", "Agent SSO (OIDC)", "system")
    svg += svg_node(30, 375, 190, 50, "Public Register", "Edge-cached / Read-replica", "system-green")

    # Integration: tall filled gateway
    svg += svg_node_filled(275, 95, 100, 295, "API Gateway", COLOURS["integration"])

    # Core Back-Office nodes
    svg += svg_node(440, 120, 210, 60, "Case Management", "(Workflow Engine)", "system")
    svg += svg_node(440, 250, 210, 60, "Statutory Consultees", "External API Integrations", "system")
    svg += svg_node(440, 370, 210, 50, "Payment Gateway", "GOV.UK Pay", "system")
    svg += svg_database(720, 90, 140, 60, "Spatial DB")
    svg += svg_database(720, 180, 140, 60, "EDRMS (Docs)")
    svg += svg_node(720, 290, 140, 50, "Event Broker", "Pub/Sub", "system")
    svg += svg_node(720, 380, 140, 40, "GOV.UK Notify", "", "external")
    svg += svg_node(720, 435, 140, 30, "planning.data.gov.uk", "", "external")

    # --- Connectors ---

    # Direct UPRN query (dashed, above zone headers)
    svg += svg_path([(375, 35), (785, 35), (785, 90)], "connector-blue", dashed=True)
    svg += svg_label(580, 27, "Direct UPRN / Constraint Queries", "connector-blue")

    # Presentation → Gateway (horizontal)
    svg += svg_line(220, 120, 270, 120)  # Rules Engine → Gateway
    svg += svg_line(220, 200, 270, 200)  # Identity → Gateway

    # Gateway → Case Management (bidirectional, offset)
    svg += svg_line(375, 145, 435, 145)  # Gateway → CM
    svg += svg_line(435, 158, 375, 158)  # CM → Gateway

    # Gateway ← Public Register (register receives data from back-office)
    svg += svg_line(325, 390, 225, 400)

    # Case Management ↔ Spatial DB (bidirectional)
    svg += svg_line(650, 130, 715, 110, "connector-blue")  # CM → Spatial
    svg += svg_line(715, 125, 650, 145, "connector-blue")  # Spatial → CM

    # Case Management → EDRMS
    svg += svg_line(650, 155, 715, 200, "connector-blue")

    # Case Management → Statutory Consultees (vertical down)
    svg += svg_line(545, 180, 545, 245)

    # Statutory ↔ Gateway (bidirectional)
    svg += svg_line(440, 270, 375, 270)  # Statutory → Gateway
    svg += svg_line(375, 285, 440, 285)  # Gateway → Statutory

    # Case Management → Payment Gateway (vertical down, left side)
    svg += svg_line(480, 180, 480, 365)

    # Case Management → Event Broker (L-shaped, avoids Statutory)
    svg += svg_path([(650, 150), (690, 150), (690, 310), (715, 310)], "connector-blue")

    # Event Broker → GOV.UK Notify (vertical down)
    svg += svg_line(790, 340, 790, 375)

    # Event Broker → planning.data.gov.uk (vertical down)
    svg += svg_line(790, 340, 790, 430)

    svg += svg_footer()
    return svg


def render_p1_anti():
    """Phase 1 anti-pattern: Generic E-Form to PDF."""
    W, H = 820, 200
    svg = svg_header(W, H)

    svg += svg_node(20, 75, 130, 50, "Applicant", "", "external")
    svg += svg_node(210, 75, 170, 50, "Generic E-Form", "", "antipattern")
    svg += svg_node(490, 20, 170, 50, "Doc Repository", "", "database")
    svg += svg_node(490, 130, 170, 50, "Workflow DB", "", "database")

    svg += svg_connector(150, 100, 205, 100)
    svg += svg_connector(380, 80, 485, 45, "Generates Flat PDF", "antipattern")
    svg += svg_connector(380, 120, 485, 155, "Basic Metadata", "connector")

    svg += svg_footer()
    return svg


def render_p1_target_strategic():
    """Phase 1 target: Rules-as-code submission (strategic)."""
    W, H = 820, 250
    svg = svg_header(W, H)

    svg += svg_node(20, 100, 110, 50, "Agent", "(OIDC Identity)", "external")
    svg += svg_node(190, 100, 170, 50, "Rules-as-code", "Dynamic Frontend", "system-green")
    svg += svg_node(480, 20, 170, 45, "Geospatial API", "", "system")
    svg += svg_node(480, 100, 170, 45, "Workflow Engine", "", "system")
    svg += svg_node(480, 185, 170, 45, "Payment Gateway", "", "system")

    svg += svg_connector(130, 125, 185, 125)
    svg += svg_connector(360, 110, 475, 42, "Live spatial intersection", "connector-blue")
    svg += svg_connector(360, 125, 475, 122, "Structured JSON")
    svg += svg_connector(360, 140, 475, 207, "Calculates fee upfront", "connector-blue")

    svg += svg_footer()
    return svg


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

DIAGRAMS = {
    "overview-strategic": render_overview_strategic,
    "p1-anti": render_p1_anti,
    "p1-target-strategic": render_p1_target_strategic,
}


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=== SVG Diagram Renderer ===\n")
    for name, render_fn in DIAGRAMS.items():
        svg_content = render_fn()
        out_path = OUTPUT_DIR / f"{name}.svg"
        out_path.write_text(svg_content)
        print(f"  [rendered] output/{name}.svg")

    print(f"\nDone. {len(DIAGRAMS)} diagrams rendered.")
    print("(Remaining diagrams still use D2 auto-layout — convert incrementally)")


if __name__ == "__main__":
    main()
