#!/usr/bin/env node
/**
 * Compute layered graph layout using dagre's Sugiyama implementation.
 *
 * Input (JSON on stdin):
 *   { nodes: [{id, width, height, rank}], edges: [{source, target}], config: {rankdir, nodesep, ranksep} }
 *
 * Output (JSON on stdout):
 *   { nodes: [{id, x, y, width, height}], edges: [{source, target, points: [{x,y}]}] }
 *
 * The `rank` field on nodes constrains which layer they appear in (maps to our zone concept).
 */

const dagre = require("@dagrejs/dagre");

const input = [];
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => input.push(chunk));
process.stdin.on("end", () => {
  const data = JSON.parse(input.join(""));
  const result = computeLayout(data);
  process.stdout.write(JSON.stringify(result, null, 2));
});

function computeLayout(data) {
  const config = data.config || {};

  const g = new dagre.graphlib.Graph({ compound: true });
  g.setGraph({
    rankdir: config.rankdir || "LR",
    nodesep: config.nodesep || 30,
    ranksep: config.ranksep || 60,
    edgesep: config.edgesep || 15,
    marginx: config.marginx || 20,
    marginy: config.marginy || 20,
  });
  g.setDefaultEdgeLabel(() => ({}));

  // Add nodes
  for (const node of data.nodes) {
    const opts = {
      width: node.width || 180,
      height: node.height || 50,
    };
    if (node.rank !== undefined) {
      opts.rank = node.rank;
    }
    g.setNode(node.id, opts);
  }

  // Add rank constraints via invisible edges if nodes specify a rank group
  // dagre doesn't have native rank constraints, so we use subgraphs
  // Actually, we can use the 'rank' property with 'min'/'max'/'same' constraints
  // But the simplest approach: group nodes by rank and use compound graphs
  const rankGroups = {};
  for (const node of data.nodes) {
    if (node.rank !== undefined) {
      if (!rankGroups[node.rank]) rankGroups[node.rank] = [];
      rankGroups[node.rank].push(node.id);
    }
  }

  // Create cluster nodes for rank groups
  for (const [rank, nodeIds] of Object.entries(rankGroups)) {
    const clusterId = `_rank_${rank}`;
    g.setNode(clusterId, { clusterLabelPos: "top" });
    for (const nodeId of nodeIds) {
      g.setParent(nodeId, clusterId);
    }
  }

  // Add edges
  for (const edge of data.edges) {
    g.setEdge(edge.source, edge.target, {
      minlen: edge.minlen || 1,
      weight: edge.weight || 1,
    });
  }

  // Run layout
  dagre.layout(g);

  // Extract results
  const nodes = data.nodes.map((n) => {
    const laid = g.node(n.id);
    return {
      id: n.id,
      x: Math.round(laid.x - laid.width / 2),
      y: Math.round(laid.y - laid.height / 2),
      width: laid.width,
      height: laid.height,
    };
  });

  const edges = data.edges.map((e) => {
    const edgeData = g.edge(e.source, e.target);
    return {
      source: e.source,
      target: e.target,
      points: edgeData && edgeData.points
        ? edgeData.points.map((p) => ({ x: Math.round(p.x), y: Math.round(p.y) }))
        : [],
    };
  });

  return {
    nodes,
    edges,
    graph: {
      width: Math.round(g.graph().width || 800),
      height: Math.round(g.graph().height || 400),
    },
  };
}
