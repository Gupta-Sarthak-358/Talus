"""NetworkX route searches over a Talus mine road graph."""

from __future__ import annotations

from collections.abc import Mapping
from numbers import Real

import networkx as nx

from .cost import risk_weighted_edge_cost
from .graph import MineRoadGraph


def shortest_route(
    mine_road_graph: MineRoadGraph,
    start_zone_id: str,
    end_zone_id: str,
) -> tuple[list[str], float]:
    """Return the lowest-length route and its total geographical length."""
    _validate_endpoints(mine_road_graph, start_zone_id, end_zone_id)

    try:
        total_cost, path = nx.single_source_dijkstra(
            mine_road_graph.graph,
            start_zone_id,
            target=end_zone_id,
            weight="length",
        )
    except nx.NetworkXNoPath as error:
        raise ValueError(_no_route_message(start_zone_id, end_zone_id)) from error

    return list(path), float(total_cost)


def risk_aware_route(
    mine_road_graph: MineRoadGraph,
    start_zone_id: str,
    end_zone_id: str,
    zone_risks: Mapping[str, Real],
    alpha: Real,
) -> tuple[list[str], float]:
    """Return the lowest-cost route using Talus's risk-weighted edge cost."""
    _validate_endpoints(mine_road_graph, start_zone_id, end_zone_id)

    def edge_cost(_: str, __: str, edge_data: Mapping[str, object]) -> float:
        return risk_weighted_edge_cost(
            edge_data["length"],  # type: ignore[arg-type]
            edge_data["adjacent_zones"],  # type: ignore[arg-type]
            zone_risks,
            alpha,
        )

    try:
        total_cost, path = nx.single_source_dijkstra(
            mine_road_graph.graph,
            start_zone_id,
            target=end_zone_id,
            weight=edge_cost,
        )
    except nx.NetworkXNoPath as error:
        raise ValueError(_no_route_message(start_zone_id, end_zone_id)) from error

    return list(path), float(total_cost)


def _validate_endpoints(
    mine_road_graph: MineRoadGraph,
    start_zone_id: str,
    end_zone_id: str,
) -> None:
    if start_zone_id not in mine_road_graph.graph:
        raise ValueError(f"Start zone {start_zone_id!r} does not exist in the road graph.")
    if end_zone_id not in mine_road_graph.graph:
        raise ValueError(f"End zone {end_zone_id!r} does not exist in the road graph.")


def _no_route_message(start_zone_id: str, end_zone_id: str) -> str:
    return f"No route exists between zones {start_zone_id!r} and {end_zone_id!r}."
