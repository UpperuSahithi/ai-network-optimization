"""Check topology node/link counts, shape, and connectivity (stdlib only)."""

import unittest
from collections import deque

from simulation.network import Network
from simulation.topology import (
    create_bus_topology,
    create_line_topology,
    create_mesh_topology,
    create_ring_topology,
    create_star_topology,
)

NODE_COUNT = 5


def _is_connected(network: Network) -> bool:
    node_ids = [node.node_id for node in network.get_nodes()]
    if not node_ids:
        return True
    start = node_ids[0]
    seen = {start}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for neighbor in network.neighbors(current):
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return seen == set(node_ids)


def _undirected_edges(network: Network) -> set[tuple[int, int]]:
    edges = set()
    for link in network.get_links():
        edges.add(tuple(sorted((link.source, link.destination))))
    return edges


class TopologyTests(unittest.TestCase):
    def test_line_is_sequential(self) -> None:
        network = create_line_topology(NODE_COUNT)
        self.assertEqual(len(network.get_nodes()), 5)
        self.assertEqual(len(network.get_links()), 4)
        self.assertTrue(_is_connected(network))
        self.assertEqual(
            _undirected_edges(network),
            {(0, 1), (1, 2), (2, 3), (3, 4)},
        )

    def test_bus_uses_linear_backbone(self) -> None:
        network = create_bus_topology(NODE_COUNT)
        line = create_line_topology(NODE_COUNT)
        self.assertEqual(len(network.get_nodes()), 5)
        self.assertEqual(len(network.get_links()), 4)
        self.assertTrue(_is_connected(network))
        self.assertEqual(_undirected_edges(network), _undirected_edges(line))

    def test_star_has_one_center(self) -> None:
        network = create_star_topology(NODE_COUNT)
        self.assertEqual(len(network.get_nodes()), 5)
        self.assertEqual(len(network.get_links()), 4)
        self.assertTrue(_is_connected(network))
        self.assertEqual(
            _undirected_edges(network),
            {(0, 1), (0, 2), (0, 3), (0, 4)},
        )
        self.assertEqual(sorted(set(network.neighbors(0))), [1, 2, 3, 4])
        for leaf in range(1, NODE_COUNT):
            self.assertEqual(set(network.neighbors(leaf)), {0})

    def test_ring_is_a_closed_loop(self) -> None:
        network = create_ring_topology(NODE_COUNT)
        self.assertEqual(len(network.get_nodes()), 5)
        self.assertEqual(len(network.get_links()), 5)
        self.assertTrue(_is_connected(network))
        self.assertEqual(
            _undirected_edges(network),
            {(0, 1), (1, 2), (2, 3), (3, 4), (0, 4)},
        )
        for node_id in range(NODE_COUNT):
            self.assertEqual(len(set(network.neighbors(node_id))), 2)

    def test_mesh_is_fully_connected(self) -> None:
        network = create_mesh_topology(NODE_COUNT)
        self.assertEqual(len(network.get_nodes()), 5)
        self.assertEqual(len(network.get_links()), 10)
        self.assertTrue(_is_connected(network))
        expected = {
            (i, j)
            for i in range(NODE_COUNT)
            for j in range(i + 1, NODE_COUNT)
        }
        self.assertEqual(_undirected_edges(network), expected)


if __name__ == "__main__":
    unittest.main()
