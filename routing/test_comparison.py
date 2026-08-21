"""Tests for Talus route comparison domain logic."""

import pytest

from routing.comparison import compare_routes
from routing.graph import MineRoadGraph


def _two_route_graph() -> MineRoadGraph:
    graph = MineRoadGraph()
    for zone_id in ("A", "B", "C", "D"):
        graph.add_zone(zone_id)

    graph.add_road("A", "B", length=1)
    graph.add_road("B", "C", length=1)
    graph.add_road("A", "D", length=1.5)
    graph.add_road("D", "C", length=1.5)
    return graph


def test_compare_routes_reports_safer_route_and_avoided_zone() -> None:
    comparison = compare_routes(
        _two_route_graph(),
        "A",
        "C",
        zone_risks={"A": 0, "B": 90, "C": 0, "D": 10},
        alpha=0.01,
    )

    assert comparison.shortest_route.path == ["A", "B", "C"]
    assert comparison.shortest_route.total_cost == 2.0
    assert comparison.shortest_route.max_risk_exposed == 90

    assert comparison.risk_aware_route.path == ["A", "D", "C"]
    assert comparison.risk_aware_route.total_cost == pytest.approx(3.3)
    assert comparison.risk_aware_route.max_risk_exposed == 10
    assert comparison.avoided_zones == ["B"]
