"""Mine road graph primitives for Talus routing.

This module models the MVP road network only.  Route search and risk-weighted
edge costs are intentionally implemented elsewhere in a later iteration.
"""

from __future__ import annotations

from collections.abc import Iterable

import networkx as nx


class MineRoadGraph:
    """Undirected mine road network whose nodes are mine zones.

    Each edge has a physical ``length`` and ``adjacent_zones``.  The latter is
    retained so future routing can apply the risks of zones beside a road.
    """

    def __init__(self) -> None:
        self.graph = nx.Graph()

    def add_zone(self, zone_id: str) -> None:
        """Add a zone location to the road network."""
        self.graph.add_node(zone_id, zone_id=zone_id)

    def add_road(
        self,
        start_zone_id: str,
        end_zone_id: str,
        length: float,
        adjacent_zones: Iterable[str] | None = None,
    ) -> None:
        """Connect two existing zones with a road.

        When no adjacent zones are supplied, the road is adjacent to its two
        endpoint zones.  This is suitable for the MVP's zone-based map.
        """
        if start_zone_id not in self.graph or end_zone_id not in self.graph:
            raise ValueError("Road endpoints must be added as zones first.")

        if length < 0:
            raise ValueError("Road length cannot be negative.")

        zones = tuple(adjacent_zones) if adjacent_zones is not None else (
            start_zone_id,
            end_zone_id,
        )
        self.graph.add_edge(
            start_zone_id,
            end_zone_id,
            length=float(length),
            adjacent_zones=zones,
        )
