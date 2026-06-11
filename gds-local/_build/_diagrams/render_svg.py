#!/usr/bin/env python3
"""
Architecture diagram renderer with dagre-powered Sugiyama layout.

Takes a declarative diagram definition (zones, nodes, edges) and uses dagre
(via Node.js subprocess) for layered graph layout, then renders to SVG
matching the GOV.UK block aesthetic.

Layout pipeline:
1. Diagram definition declares nodes (with zone/rank), edges, and zones
2. dagre computes optimal positions using Sugiyama algorithm (layer assignment,
   crossing minimisation, coordinate assignment)
3. Zone boundaries are calculated from the positioned nodes
4. SVG is rendered with GOV.UK styling, connector routing from dagre's edge points

Fallback: if Node.js/dagre unavailable, uses built-in grid layout.

Usage: python3 render_svg.py
"""

import json
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SCRIPT_DIR / "output"

# ---------------------------------------------------------------------------
# Configuration
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

# Layout constants
NODE_W = 180
NODE_H = 50
NODE_PAD_X = 20
NODE_PAD_Y = 20
ZONE_PAD_TOP = 30
ZONE_PAD_BOTTOM = 15
ZONE_PAD_X = 15
ZONE_GAP = 15
CANVAS_PAD = 25


def xml_escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------------------
# Layout Engine
# ---------------------------------------------------------------------------

class Node:
    def __init__(self, id, label, subtitle="", style="system", zone="", row=None, col=0):
        self.id = id
        self.label = label
        self.subtitle = subtitle
        self.style = style
        self.zone = zone
        self.row = row  # Vertical position within zone (0-based)
        self.col = col  # Sub-column within zone (0-based, default 0)
        # Computed by layout:
        self.x = 0
        self.y = 0
        self.w = NODE_W
        self.h = NODE_H

    @property
    def cx(self):
        return self.x + self.w // 2

    @property
    def cy(self):
        return self.y + self.h // 2

    @property
    def right(self):
        return self.x + self.w

    @property
    def bottom(self):
        return self.y + self.h

    def edge_point(self, side):
        """Return (x, y) for the midpoint of a given edge."""
        if side == "left":
            return (self.x, self.cy)
        elif side == "right":
            return (self.right, self.cy)
        elif side == "top":
            return (self.cx, self.y)
        elif side == "bottom":
            return (self.cx, self.bottom)
        return (self.cx, self.cy)


class Edge:
    def __init__(self, source, target, label="", style="connector", dashed=False, route=None):
        self.source = source
        self.target = target
        self.label = label
        self.style = style
        self.dashed = dashed
        self.route = route  # Optional: "above" or "below" to force routing above/below nodes


class Zone:
    def __init__(self, id, label, width=None):
        self.id = id
        self.label = label
        self.width = width  # If None, auto-calculated from node widths
        # Computed:
        self.x = 0
        self.y = 0
        self.w = 0
        self.h = 0
        self.nodes = []


class Diagram:
    def __init__(self, zones=None, nodes=None, edges=None, title=""):
        self.zones = zones or []
        self.nodes = nodes or []
        self.edges = edges or []
        self.title = title
        self._node_map = {}

    def layout(self):
        """Calculate positions using dagre if available, else grid fallback."""
        self._node_map = {n.id: n for n in self.nodes}
        if self._try_dagre_layout():
            return self._canvas_w, self._canvas_h
        return self._grid_layout()

    def _try_dagre_layout(self):
        """Attempt layout via dagre (Node.js). Returns True on success."""
        layout_script = SCRIPT_DIR / "layout.js"
        if not layout_script.exists():
            return False

        # Build dagre input — rank maps to our zone ordering
        zone_order = {z.id: i for i, z in enumerate(self.zones)}
        dagre_input = {
            "nodes": [
                {
                    "id": n.id,
                    "width": n.w,
                    "height": n.h,
                    "rank": zone_order.get(n.zone, 0),
                }
                for n in self.nodes
            ],
            "edges": [
                {"source": e.source, "target": e.target}
                for e in self.edges
                if not e.dashed  # Skip dashed/special edges from layout
            ],
            "config": {
                "rankdir": "LR",
                "nodesep": 25,
                "ranksep": 60,
                "marginx": CANVAS_PAD,
                "marginy": CANVAS_PAD,
            },
        }

        try:
            result = subprocess.run(
                ["node", str(layout_script)],
                input=json.dumps(dagre_input),
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                return False

            output = json.loads(result.stdout)
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            return False

        # Apply dagre positions to our nodes
        pos_map = {n["id"]: n for n in output["nodes"]}
        for node in self.nodes:
            if node.id in pos_map:
                p = pos_map[node.id]
                node.x = p["x"]
                node.y = p["y"]

        # Store edge routing points
        self._dagre_edges = {
            (e["source"], e["target"]): e["points"]
            for e in output["edges"]
        }

        # Calculate zone boundaries from node positions
        self._compute_zones_from_positions()

        self._canvas_w = output["graph"]["width"]
        self._canvas_h = output["graph"]["height"]
        return True

    def _compute_zones_from_positions(self):
        """Calculate zone boundaries by finding the bounding box of nodes in each zone."""
        zone_map = {z.id: z for z in self.zones}
        for zone in self.zones:
            zone_nodes = [n for n in self.nodes if n.zone == zone.id]
            if not zone_nodes:
                continue
            min_x = min(n.x for n in zone_nodes) - ZONE_PAD_X
            max_x = max(n.x + n.w for n in zone_nodes) + ZONE_PAD_X
            min_y = min(n.y for n in zone_nodes) - ZONE_PAD_TOP
            max_y = max(n.y + n.h for n in zone_nodes) + ZONE_PAD_BOTTOM
            zone.x = min_x
            zone.y = min_y
            zone.w = max_x - min_x
            zone.h = max_y - min_y

    def _grid_layout(self):
        """Fallback: grid-based sub-column layout."""

        # Assign nodes to zones
        zone_map = {z.id: z for z in self.zones}
        for node in self.nodes:
            if node.zone in zone_map:
                zone_map[node.zone].nodes.append(node)

        # For each zone, determine grid dimensions (max_col+1 × max_row+1)
        for zone in self.zones:
            if not zone.nodes:
                continue
            # Auto-assign rows if not specified
            col_counters = {}
            for node in zone.nodes:
                if node.row is None:
                    node.row = col_counters.get(node.col, 0)
                col_counters[node.col] = max(col_counters.get(node.col, 0), node.row + 1)

        # Calculate zone widths based on number of sub-columns
        for zone in self.zones:
            zone._n_cols = max((n.col for n in zone.nodes), default=0) + 1
            if zone.width:
                zone.w = zone.width
            else:
                zone.w = zone._n_cols * (NODE_W + NODE_PAD_X) + ZONE_PAD_X * 2

        # Calculate zone heights based on tallest sub-column
        for zone in self.zones:
            max_rows = 0
            for c in range(zone._n_cols):
                col_nodes = [n for n in zone.nodes if n.col == c]
                if col_nodes:
                    max_row = max(n.row for n in col_nodes) + 1
                    max_rows = max(max_rows, max_row)
            zone.h = ZONE_PAD_TOP + max_rows * (NODE_H + NODE_PAD_Y) + ZONE_PAD_BOTTOM

        # All zones same height
        max_zone_h = max((z.h for z in self.zones), default=200)
        for zone in self.zones:
            zone.h = max_zone_h

        # Position zones left-to-right
        x_cursor = CANVAS_PAD
        for zone in self.zones:
            zone.x = x_cursor
            zone.y = CANVAS_PAD
            x_cursor += zone.w + ZONE_GAP

        # Position nodes within zones using grid (col, row)
        for zone in self.zones:
            col_width = (zone.w - ZONE_PAD_X * 2) // max(zone._n_cols, 1)
            for node in zone.nodes:
                node.x = zone.x + ZONE_PAD_X + node.col * col_width + (col_width - node.w) // 2
                node.y = zone.y + ZONE_PAD_TOP + node.row * (NODE_H + NODE_PAD_Y)

        # Calculate canvas size
        total_w = x_cursor - ZONE_GAP + CANVAS_PAD
        total_h = max_zone_h + CANVAS_PAD * 2
        return total_w, total_h

    def get_node(self, id):
        return self._node_map.get(id)

    def _build_edge_ports(self):
        """Assign port positions for edges, distributing evenly along node edges."""
        # Count connections per node per side
        # side_counts[node_id][side] = list of edge ids connecting on that side
        self._edge_ports = {}  # edge_id -> (src_point, tgt_point)

        # First pass: determine which side each edge connects on
        edge_sides = []
        for edge in self.edges:
            if edge.route == "above" or edge.dashed:
                edge_sides.append((edge, None, None, None, None))
                continue
            src = self.get_node(edge.source)
            tgt = self.get_node(edge.target)
            if not src or not tgt:
                edge_sides.append((edge, None, None, None, None))
                continue
            src_side, tgt_side = self._determine_sides(src, tgt)
            edge_sides.append((edge, src, tgt, src_side, tgt_side))

        # Group edges by (node_id, side) to count ports
        from collections import defaultdict
        port_groups = defaultdict(list)  # (node_id, side) -> [edge]
        for edge, src, tgt, src_side, tgt_side in edge_sides:
            if src_side is None:
                continue
            port_groups[(edge.source, src_side)].append(("source", edge))
            port_groups[(edge.target, tgt_side)].append(("target", edge))

        # Assign port positions
        for (node_id, side), connections in port_groups.items():
            node = self.get_node(node_id)
            if not node:
                continue
            n = len(connections)
            for i, (role, edge) in enumerate(connections):
                point = self._port_position(node, side, i, n)
                key = id(edge)
                if key not in self._edge_ports:
                    self._edge_ports[key] = [None, None]
                if role == "source":
                    self._edge_ports[key][0] = point
                else:
                    self._edge_ports[key][1] = point

    def _determine_sides(self, src, tgt):
        """Determine which sides of src and tgt to connect."""
        # Primarily horizontal
        if abs(src.cy - tgt.cy) < NODE_H:
            if src.cx < tgt.cx:
                return "right", "left"
            else:
                return "left", "right"
        # Primarily vertical
        if abs(src.cx - tgt.cx) < NODE_W:
            if src.cy < tgt.cy:
                return "bottom", "top"
            else:
                return "top", "bottom"
        # Diagonal
        if src.cx < tgt.cx:
            src_side = "right"
        else:
            src_side = "left"
        if src.cy < tgt.cy:
            tgt_side = "top"
        else:
            tgt_side = "bottom"
        return src_side, tgt_side

    def _port_position(self, node, side, index, total):
        """Calculate a distributed port position along a node's edge."""
        # Distribute evenly: divide edge length into (total+1) segments
        fraction = (index + 1) / (total + 1)

        if side == "left":
            return (node.x, node.y + int(node.h * fraction))
        elif side == "right":
            return (node.right, node.y + int(node.h * fraction))
        elif side == "top":
            return (node.x + int(node.w * fraction), node.y)
        elif side == "bottom":
            return (node.x + int(node.w * fraction), node.bottom)
        return (node.cx, node.cy)

    def render(self):
        """Layout and render to SVG string."""
        w, h = self.layout()
        self._build_edge_ports()
        parts = []
        parts.append(
            f'<svg viewBox="0 0 {w} {h}" width="100%" height="100%" '
            f"xmlns=\"http://www.w3.org/2000/svg\" "
            f"style=\"font-family: 'GDS Transport', Arial, sans-serif;\">\n"
        )
        parts.append(
            '  <defs>\n'
            '    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" '
            'markerWidth="6" markerHeight="6" orient="auto-start-reverse">\n'
            f'      <path d="M 0 0 L 10 5 L 0 10 z" fill="{COLOURS["connector"]}" />\n'
            '    </marker>\n'
            '    <marker id="arrow-blue" viewBox="0 0 10 10" refX="9" refY="5" '
            'markerWidth="6" markerHeight="6" orient="auto-start-reverse">\n'
            f'      <path d="M 0 0 L 10 5 L 0 10 z" fill="{COLOURS["connector-blue"]}" />\n'
            '    </marker>\n'
            '  </defs>\n'
        )

        # Render order: zones (background) → edges (mid) → nodes (foreground)
        for zone in self.zones:
            parts.append(self._render_zone(zone))

        for edge in self.edges:
            parts.append(self._render_edge(edge))

        for node in self.nodes:
            parts.append(self._render_node(node))

        parts.append('</svg>\n')
        return "".join(parts)

    def _render_zone(self, zone):
        return (
            f'  <rect x="{zone.x}" y="{zone.y}" width="{zone.w}" height="{zone.h}" '
            f'fill="{COLOURS["zone-fill"]}" stroke="{COLOURS["zone-stroke"]}" '
            f'stroke-dasharray="4" rx="4"/>\n'
            f'  <text x="{zone.x + 10}" y="{zone.y + 16}" font-size="11" '
            f'font-weight="bold" fill="{COLOURS["text-light"]}">'
            f'{xml_escape(zone.label)}</text>\n'
        )

    def _render_node(self, node):
        stroke = COLOURS.get(node.style, COLOURS["system"])
        fill = COLOURS["white"]

        # Special case: filled nodes (integration style)
        if node.style == "integration":
            return self._render_filled_node(node)

        # Special case: database shape
        if node.style == "database":
            return self._render_database(node)

        lines = []
        lines.append(
            f'  <rect x="{node.x}" y="{node.y}" width="{node.w}" height="{node.h}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="2" rx="4"/>\n'
        )
        if node.subtitle:
            lines.append(
                f'  <text x="{node.cx}" y="{node.cy - 5}" font-size="14" '
                f'font-weight="bold" text-anchor="middle" fill="{COLOURS["text"]}">'
                f'{xml_escape(node.label)}</text>\n'
            )
            lines.append(
                f'  <text x="{node.cx}" y="{node.cy + 12}" font-size="11" '
                f'text-anchor="middle" fill="{COLOURS["text-light"]}">'
                f'{xml_escape(node.subtitle)}</text>\n'
            )
        else:
            lines.append(
                f'  <text x="{node.cx}" y="{node.cy + 5}" font-size="14" '
                f'font-weight="bold" text-anchor="middle" fill="{COLOURS["text"]}">'
                f'{xml_escape(node.label)}</text>\n'
            )
        return "".join(lines)

    def _render_filled_node(self, node):
        colour = COLOURS.get(node.style, COLOURS["system"])
        lines = []
        lines.append(
            f'  <rect x="{node.x}" y="{node.y}" width="{node.w}" height="{node.h}" '
            f'fill="{colour}" rx="4"/>\n'
        )
        # Rotate text if node is taller than wide
        if node.h > node.w * 1.5:
            lines.append(
                f'  <text x="{node.cx}" y="{node.cy}" font-size="14" font-weight="bold" '
                f'text-anchor="middle" fill="#ffffff" '
                f'transform="rotate(-90 {node.cx} {node.cy})">'
                f'{xml_escape(node.label)}</text>\n'
            )
        else:
            lines.append(
                f'  <text x="{node.cx}" y="{node.cy + 5}" font-size="14" font-weight="bold" '
                f'text-anchor="middle" fill="#ffffff">{xml_escape(node.label)}</text>\n'
            )
        return "".join(lines)

    def _render_database(self, node):
        stroke = COLOURS["database"]
        fill = COLOURS["white"]
        x, y, w, h = node.x, node.y, node.w, node.h
        lines = []
        lines.append(
            f'  <path d="M {x} {y+12} L {x+w} {y+12} L {x+w} {y+h} L {x} {y+h} Z" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="2"/>\n'
        )
        lines.append(
            f'  <path d="M {x} {y+12} Q {x+w//2} {y+22} {x+w} {y+12}" '
            f'fill="none" stroke="{stroke}" stroke-width="1"/>\n'
        )
        lines.append(
            f'  <ellipse cx="{x+w//2}" cy="{y+12}" rx="{w//2}" ry="10" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="2"/>\n'
        )
        lines.append(
            f'  <text x="{node.cx}" y="{node.cy + 8}" font-size="14" '
            f'font-weight="bold" text-anchor="middle" fill="{COLOURS["text"]}">'
            f'{xml_escape(node.label)}</text>\n'
        )
        return "".join(lines)

    def _render_edge(self, edge):
        src = self.get_node(edge.source)
        tgt = self.get_node(edge.target)
        if not src or not tgt:
            return ""

        colour = COLOURS.get(edge.style, COLOURS["connector"])
        marker = "arrow-blue" if "blue" in edge.style else "arrow"
        dash = ' stroke-dasharray="4"' if edge.dashed else ""

        lines = []

        # Route "above" — connector goes up from source, across the top, down to target
        if edge.route == "above":
            top_y = CANVAS_PAD - 5  # Above all zones
            sx, sy = src.edge_point("top")
            tx, ty = tgt.edge_point("top")
            lines.append(
                f'  <path d="M {sx} {sy} L {sx} {top_y} L {tx} {top_y} L {tx} {ty}" '
                f'fill="none" stroke="{colour}" stroke-width="2"{dash} '
                f'marker-end="url(#{marker})"/>\n'
            )
            if edge.label:
                lx = (sx + tx) // 2
                ly = top_y - 6
                lines.append(
                    f'  <text x="{lx}" y="{ly}" font-size="11" font-style="italic" '
                    f'text-anchor="middle" fill="{colour}">{xml_escape(edge.label)}</text>\n'
                )
            return "".join(lines)

        # Use dagre edge points if available
        dagre_points = getattr(self, "_dagre_edges", {}).get((edge.source, edge.target))
        if dagre_points and len(dagre_points) >= 2:
            d = " ".join(
                f"{'M' if i == 0 else 'L'} {p['x']} {p['y']}"
                for i, p in enumerate(dagre_points)
            )
            lines.append(
                f'  <path d="{d}" fill="none" stroke="{colour}" stroke-width="2"{dash} '
                f'marker-end="url(#{marker})"/>\n'
            )
            if edge.label:
                mid = dagre_points[len(dagre_points) // 2]
                lines.append(
                    f'  <text x="{mid["x"]}" y="{mid["y"] - 10}" font-size="11" '
                    f'font-style="italic" text-anchor="middle" fill="{colour}">'
                    f'{xml_escape(edge.label)}</text>\n'
                )
            return "".join(lines)

        # Use distributed port positions
        ports = self._edge_ports.get(id(edge))
        if ports and ports[0] and ports[1]:
            sx, sy = ports[0]
            tx, ty = ports[1]
        else:
            sx, sy, tx, ty = self._route_edge(src, tgt)

        # Route connector with orthogonal segments, ensuring the final
        # segment is perpendicular to the target edge (so arrows point inward)
        if abs(sy - ty) < 5:
            # Horizontal: straight line
            lines.append(
                f'  <line x1="{sx}" y1="{sy}" x2="{tx}" y2="{ty}" '
                f'stroke="{colour}" stroke-width="2"{dash} '
                f'marker-end="url(#{marker})"/>\n'
            )
        elif abs(sx - tx) < 5:
            # Vertical: straight line
            lines.append(
                f'  <line x1="{sx}" y1="{sy}" x2="{tx}" y2="{ty}" '
                f'stroke="{colour}" stroke-width="2"{dash} '
                f'marker-end="url(#{marker})"/>\n'
            )
        else:
            # L-shaped: route so the LAST segment is perpendicular to target edge
            # Determine target side from port position relative to target node
            tgt_side = self._determine_sides(src, tgt)[1] if ports else "left"
            if tgt_side in ("left", "right"):
                # Target is on a vertical edge: final segment must be horizontal
                # So go vertical first, then horizontal into target
                lines.append(
                    f'  <path d="M {sx} {sy} L {sx} {ty} L {tx} {ty}" '
                    f'fill="none" stroke="{colour}" stroke-width="2"{dash} '
                    f'marker-end="url(#{marker})"/>\n'
                )
            else:
                # Target is on a horizontal edge: final segment must be vertical
                # So go horizontal first, then vertical into target
                lines.append(
                    f'  <path d="M {sx} {sy} L {tx} {sy} L {tx} {ty}" '
                    f'fill="none" stroke="{colour}" stroke-width="2"{dash} '
                    f'marker-end="url(#{marker})"/>\n'
                )

        # Label
        if edge.label:
            lx = (sx + tx) // 2
            ly = min(sy, ty) - 8
            lines.append(
                f'  <text x="{lx}" y="{ly}" font-size="11" font-style="italic" '
                f'text-anchor="middle" fill="{colour}">{xml_escape(edge.label)}</text>\n'
            )

        return "".join(lines)

    def _route_edge(self, src, tgt):
        """Determine connection points with clearance padding."""
        PAD = 4  # Clearance so arrows don't overlap borders

        # Horizontal relationship (nodes in different zones, same-ish row)
        if abs(src.cy - tgt.cy) < NODE_H:
            if src.cx < tgt.cx:
                sx, sy = src.edge_point("right")
                tx, ty = tgt.edge_point("left")
                return (sx + PAD, sy, tx - PAD, ty)
            else:
                sx, sy = src.edge_point("left")
                tx, ty = tgt.edge_point("right")
                return (sx - PAD, sy, tx + PAD, ty)

        # Vertical relationship (same zone or close X)
        if abs(src.cx - tgt.cx) < NODE_W:
            if src.cy < tgt.cy:
                sx, sy = src.edge_point("bottom")
                tx, ty = tgt.edge_point("top")
                return (sx, sy + PAD, tx, ty - PAD)
            else:
                sx, sy = src.edge_point("top")
                tx, ty = tgt.edge_point("bottom")
                return (sx, sy - PAD, tx, ty + PAD)

        # Diagonal — connect nearest edges
        if src.cx < tgt.cx:
            sx, sy = src.edge_point("right")
            sx += PAD
        else:
            sx, sy = src.edge_point("left")
            sx -= PAD
        if src.cy < tgt.cy:
            tx, ty = tgt.edge_point("top")
            ty -= PAD
        else:
            tx, ty = tgt.edge_point("bottom")
            ty += PAD
        return (sx, sy, tx, ty)


# ---------------------------------------------------------------------------
# Diagram Definitions
# ---------------------------------------------------------------------------

def build_overview_strategic():
    """Define the overview diagram declaratively."""
    zones = [
        Zone("presentation", "PUBLIC / PRESENTATION", width=220),
        Zone("integration", "INTEGRATION", width=110),
        Zone("backoffice", "CORE BACK-OFFICE & DATA"),  # Auto-width from 2 sub-columns
    ]

    nodes = [
        # Presentation (single column)
        Node("rules", "Rules Engine (Forms)", "e.g. PlanX", "system-green", "presentation", row=0, col=0),
        Node("identity", "Identity / Auth", "Agent SSO (OIDC)", "system", "presentation", row=1, col=0),
        Node("register", "Public Register", "Edge-cached / Read-replica", "system-green", "presentation", row=3, col=0),
        # Integration (single column, tall gateway)
        Node("gateway", "API Gateway", "", "integration", "integration", row=0, col=0),
        # Back-office col 0: core processing systems
        Node("workflow", "Case Management", "(Workflow Engine)", "system", "backoffice", row=0, col=0),
        Node("statutory", "Statutory Consultees", "External APIs", "external", "backoffice", row=1, col=0),
        Node("payment", "Payment Gateway", "GOV.UK Pay", "system", "backoffice", row=2, col=0),
        # Back-office col 1: data stores and outputs
        Node("spatial", "Spatial DB", "", "database", "backoffice", row=0, col=1),
        Node("edrms", "EDRMS (Docs)", "", "database", "backoffice", row=1, col=1),
        Node("broker", "Event Broker", "Pub/Sub", "system", "backoffice", row=2, col=1),
        Node("notify", "GOV.UK Notify", "", "external", "backoffice", row=3, col=1),
    ]

    # Make gateway tall and narrow
    for n in nodes:
        if n.id == "gateway":
            n.w = 80
            n.h = 250

    edges = [
        Edge("rules", "gateway"),
        Edge("identity", "gateway"),
        Edge("gateway", "workflow"),
        Edge("workflow", "gateway"),  # Bidirectional with above
        Edge("workflow", "spatial", "", "connector-blue"),
        Edge("workflow", "edrms", "", "connector-blue"),
        Edge("workflow", "statutory"),
        Edge("workflow", "payment"),
        Edge("workflow", "broker", "", "connector-blue"),
        Edge("broker", "notify"),
        Edge("gateway", "statutory"),
        Edge("statutory", "gateway"),  # Bidirectional responses
        Edge("gateway", "register"),   # Async replication to public register
        Edge("rules", "spatial", "Direct UPRN / Constraint Queries", "connector-blue", dashed=True, route="above"),
    ]

    return Diagram(zones=zones, nodes=nodes, edges=edges, title="overview-strategic")


def build_p1_anti():
    """Phase 1 anti-pattern."""
    zones = [
        Zone("input", "CITIZEN INPUT", width=200),
        Zone("processing", "PROCESSING", width=210),
        Zone("storage", "STORAGE", width=200),
    ]

    nodes = [
        Node("applicant", "Applicant", "", "external", "input", row=0),
        Node("eform", "Generic E-Form", "No rules, no validation", "antipattern", "processing", row=0),
        Node("pdf", "Flat PDF", "Unstructured", "antipattern", "storage", row=0),
        Node("metadata", "Basic Metadata", "Manual re-keying needed", "antipattern", "storage", row=1),
    ]

    edges = [
        Edge("applicant", "eform", "Fills in form"),
        Edge("eform", "pdf", "Generates flat PDF"),
        Edge("eform", "metadata", "Captures minimal fields"),
    ]

    return Diagram(zones=zones, nodes=nodes, edges=edges, title="p1-anti")


def build_p1_target_strategic():
    """Phase 1 target: Rules-as-code submission."""
    zones = [
        Zone("input", "CITIZEN INPUT", width=200),
        Zone("frontend", "RULES ENGINE", width=210),
        Zone("backend", "BACK-OFFICE", width=200),
    ]

    nodes = [
        Node("agent", "Agent", "(OIDC Identity)", "external", "input", row=0),
        Node("rules", "Rules-as-code", "Dynamic Frontend", "system-green", "frontend", row=0),
        Node("geo", "Geospatial API", "", "system", "backend", row=0),
        Node("workflow", "Workflow Engine", "", "system", "backend", row=1),
        Node("payment", "Payment Gateway", "", "system", "backend", row=2),
    ]

    edges = [
        Edge("agent", "rules"),
        Edge("rules", "geo", "Live spatial lookup", "connector-blue"),
        Edge("rules", "workflow", "Structured JSON"),
        Edge("rules", "payment", "Calculates fee", "connector-blue"),
    ]

    return Diagram(zones=zones, nodes=nodes, edges=edges, title="p1-target-strategic")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

DIAGRAMS = [
    build_overview_strategic,
    build_p1_anti,
    build_p1_target_strategic,
]


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=== SVG Layout Engine ===\n")
    for build_fn in DIAGRAMS:
        diagram = build_fn()
        svg = diagram.render()
        out_path = OUTPUT_DIR / f"{diagram.title}.svg"
        out_path.write_text(svg)
        print(f"  [rendered] output/{diagram.title}.svg")

    print(f"\nDone. {len(DIAGRAMS)} diagrams rendered.")


if __name__ == "__main__":
    main()
