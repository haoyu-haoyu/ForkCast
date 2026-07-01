from __future__ import annotations

from typing import Any

import networkx as nx


def build_networkx_fallback(case_graph: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    graph = nx.DiGraph()
    case_id = case_graph["case_id"]
    case_node = f"case:{case_id}"
    graph.add_node(case_node, label=case_id, kind="case")

    _add_items(graph, case_node, "entity", "HAS_ENTITY", case_graph.get("entities", []))
    _add_items(graph, case_node, "stakeholder", "HAS_STAKEHOLDER", case_graph.get("stakeholders", []))
    _add_items(graph, case_node, "assumption", "HAS_ASSUMPTION", case_graph.get("assumptions", []))
    _add_items(graph, case_node, "constraint", "HAS_CONSTRAINT", case_graph.get("constraints", []))

    for evidence in case_graph.get("evidence", []):
        fact_id = evidence["fact_id"]
        evidence_node = f"evidence:{fact_id}"
        graph.add_node(evidence_node, label=fact_id, kind="evidence")
        graph.add_edge(case_node, evidence_node, type="HAS_EVIDENCE")

    for collection_name, prefix in [
        ("entities", "entity"),
        ("stakeholders", "stakeholder"),
        ("assumptions", "assumption"),
        ("constraints", "constraint"),
    ]:
        for item in case_graph.get(collection_name, []):
            item_node = f"{prefix}:{item['id']}"
            for fact_id in item.get("evidence_fact_ids", []):
                evidence_node = f"evidence:{fact_id}"
                if evidence_node in graph:
                    graph.add_edge(item_node, evidence_node, type="SUPPORTED_BY")

    return {
        "nodes": [
            {"id": node_id, **data}
            for node_id, data in sorted(graph.nodes(data=True), key=lambda item: item[0])
        ],
        "edges": [
            {"source": source, "target": target, **data}
            for source, target, data in sorted(graph.edges(data=True), key=lambda item: (item[0], item[1]))
        ],
    }


def _add_items(
    graph: nx.DiGraph,
    case_node: str,
    kind: str,
    edge_type: str,
    items: list[dict[str, Any]],
) -> None:
    for item in items:
        node_id = f"{kind}:{item['id']}"
        label = item.get("name") or item.get("statement") or item["id"]
        graph.add_node(node_id, label=label, kind=kind)
        graph.add_edge(case_node, node_id, type=edge_type)
