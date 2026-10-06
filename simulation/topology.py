"""Build simple undirected topologies used by the simulator.

All graphs use node IDs 0 .. n-1. Each link is stored once and treated as
undirected by `Network.neighbors`.

Bus vs line: a real hardware bus is one shared cable. Modeling that as an
extra hidden backbone node would change the requested node count, and
modeling it as a collision domain would need extra simulator logic. This
project therefore uses a **linear backbone**: stations sit in a row on the
cable, so bus has the same graph shape as line (n nodes, n-1 links). The
`topology="bus"` API value is kept so configuration can still name a bus
network; routing and metrics then match the line case on purpose.
"""

from simulation.network import Network


def _empty_network(node_count: int) -> Network:
    if node_count < 1:
        raise ValueError("node_count must be at least 1")

    network = Network()
    for node_id in range(node_count):
        network.add_node(node_id)
    return network


def _add_undirected_link(
    network: Network,
    source: int,
    destination: int,
    capacity: float,
    latency: float,
) -> None:
    network.add_link(source, destination, capacity, latency)


def create_line_topology(
    node_count: int,
    capacity: float = 10.0,
    latency: float = 1.0,
) -> Network:
    """Nodes in a straight line: 0-1-2-...-(n-1)."""
    network = _empty_network(node_count)
    for node_id in range(node_count - 1):
        _add_undirected_link(network, node_id, node_id + 1, capacity, latency)
    return network


def create_bus_topology(
    node_count: int,
    capacity: float = 10.0,
    latency: float = 1.0,
) -> Network:
    """Bus as a linear backbone (same graph shape as a line)."""
    return create_line_topology(node_count, capacity=capacity, latency=latency)


def create_star_topology(
    node_count: int,
    capacity: float = 10.0,
    latency: float = 1.0,
) -> Network:
    """All nodes connect to a center hub (node 0)."""
    network = _empty_network(node_count)
    for node_id in range(1, node_count):
        _add_undirected_link(network, 0, node_id, capacity, latency)
    return network


def create_ring_topology(
    node_count: int,
    capacity: float = 10.0,
    latency: float = 1.0,
) -> Network:
    """Nodes in a circle. A single node has no links."""
    network = _empty_network(node_count)
    if node_count == 1:
        return network

    for node_id in range(node_count - 1):
        _add_undirected_link(network, node_id, node_id + 1, capacity, latency)
    _add_undirected_link(network, node_count - 1, 0, capacity, latency)
    return network


def create_mesh_topology(
    node_count: int,
    capacity: float = 10.0,
    latency: float = 1.0,
) -> Network:
    """Fully connected: every pair of nodes has a link."""
    network = _empty_network(node_count)
    for source in range(node_count):
        for destination in range(source + 1, node_count):
            _add_undirected_link(network, source, destination, capacity, latency)
    return network
