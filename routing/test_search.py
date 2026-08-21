"""Tests for shortest and risk-aware mine road searches."""

import pytest

from routing.graph import MineRoadGraph
from routing.search import risk_aware_route, shortest_route


def _two_route_graph() -> MineRoadGraph:
    graph = MineRoadGraph()
    for zone_id in ("A", "B", "C", "D"):
        graph.add_zone(zone_id)

    graph.add_road("A", "B", length=1)
    graph.add_road("B", "C", length=1)
    graph.add_road("A", "D", length=1.5)
    graph.add_road("D", "C", length=1.5)
    return graph


def test_shortest_route_chooses_lowest_total_length() -> None:
    path, total_cost = shortest_route(_two_route_graph(), "A", "C")

    assert path == ["A", "B", "C"]
    assert total_cost == 2.0


def test_risk_aware_route_chooses_longer_safer_path() -> None:
    path, total_cost = risk_aware_route(
        _two_route_graph(),
        "A",
        "C",
        zone_risks={"A": 0, "B": 100, "C": 0, "D": 0},
        alpha=0.01,
    )

    assert path == ["A", "D", "C"]
    assert total_cost == 3.0


def test_shortest_route_rejects_missing_start_zone() -> None:
    with pytest.raises(ValueError, match="Start zone 'missing' does not exist"):
        shortest_route(_two_route_graph(), "missing", "C")


def test_shortest_route_rejects_missing_end_zone() -> None:
    with pytest.raises(ValueError, match="End zone 'missing' does not exist"):
        shortest_route(_two_route_graph(), "A", "missing")


def test_shortest_route_rejects_disconnected_zones() -> None:
    graph = MineRoadGraph()
    graph.add_zone("A")
    graph.add_zone("C")

    with pytest.raises(ValueError, match="No route exists between zones 'A' and 'C'"):
        shortest_route(graph, "A", "C")
