"""Domain results for comparing shortest and risk-aware mine routes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from numbers import Real

from .graph import MineRoadGraph
from .search import risk_aware_route, shortest_route


@dataclass(frozen=True)
class RouteResult:
    """A computed route and the risk exposure along it."""

    path: list[str]
    total_cost: float
    max_risk_exposed: Real


@dataclass(frozen=True)
class RouteComparison:
    """Shortest and risk-aware route results for the same endpoints."""

    risk_aware_route: RouteResult
    shortest_route: RouteResult
    avoided_zones: list[str]


def compare_routes(
    mine_road_graph: MineRoadGraph,
    start_zone_id: str,
    end_zone_id: str,
    zone_risks: Mapping[str, Real],
    alpha: Real,
) -> RouteComparison:
    """Compute both routes and summarize their cost and exposed risks."""
    shortest_path, shortest_cost = shortest_route(
        mine_road_graph, start_zone_id, end_zone_id
    )
    risk_aware_path, risk_aware_cost = risk_aware_route(
        mine_road_graph, start_zone_id, end_zone_id, zone_risks, alpha
    )

    risk_aware_zone_ids = set(risk_aware_path)
    avoided_zones = [
        zone_id for zone_id in shortest_path if zone_id not in risk_aware_zone_ids
    ]

    return RouteComparison(
        risk_aware_route=RouteResult(
            path=risk_aware_path,
            total_cost=risk_aware_cost,
            max_risk_exposed=_max_risk_exposed(
                mine_road_graph, risk_aware_path, zone_risks
            ),
        ),
        shortest_route=RouteResult(
            path=shortest_path,
            total_cost=shortest_cost,
            max_risk_exposed=_max_risk_exposed(
                mine_road_graph, shortest_path, zone_risks
            ),
        ),
        avoided_zones=avoided_zones,
    )


def _max_risk_exposed(
    mine_road_graph: MineRoadGraph,
    path: list[str],
    zone_risks: Mapping[str, Real],
) -> Real:
    """Return the highest risk among route nodes and adjacent edge zones."""
    exposed_zone_ids = list(path)
    for start_zone_id, end_zone_id in zip(path, path[1:]):
        exposed_zone_ids.extend(
            mine_road_graph.graph.edges[start_zone_id, end_zone_id]["adjacent_zones"]
        )

    risks: list[Real] = []
    for zone_id in exposed_zone_ids:
        if zone_id not in zone_risks:
            raise ValueError(f"missing risk for exposed zone {zone_id!r}")
        risks.append(zone_risks[zone_id])

    return max(risks)
