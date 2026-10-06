from simulation.metrics import NetworkMetrics, calculate_metrics
from simulation.network import Network
from simulation.simulator import SimulationResult, simulate
from simulation.topology import (
    create_bus_topology,
    create_line_topology,
    create_mesh_topology,
    create_ring_topology,
    create_star_topology,
)
from simulation.traffic import TrafficDemand, generate_traffic

TOPOLOGY_BUILDERS = {
    "line": create_line_topology,
    "bus": create_bus_topology,
    "star": create_star_topology,
    "ring": create_ring_topology,
    "mesh": create_mesh_topology,
}

SUPPORTED_TOPOLOGIES = tuple(TOPOLOGY_BUILDERS)


def create_requested_network(
    number_of_nodes: int,
    topology: str,
    link_capacity: float,
    latency: float = 1.0,
) -> Network:
    key = topology.strip().lower()
    if key not in TOPOLOGY_BUILDERS:
        supported = ", ".join(SUPPORTED_TOPOLOGIES)
        raise ValueError(f"Unknown topology '{topology}'. Use one of: {supported}")

    return TOPOLOGY_BUILDERS[key](
        node_count=number_of_nodes,
        capacity=link_capacity,
        latency=latency,
    )


def run_configured_simulation(
    number_of_nodes: int,
    topology: str,
    link_capacity: float,
    traffic_load: float,
    latency: float = 1.0,
    link_weights: dict[tuple[int, int], float] | None = None,
) -> tuple[Network, list[TrafficDemand], SimulationResult, NetworkMetrics]:
    network = create_requested_network(
        number_of_nodes=number_of_nodes,
        topology=topology,
        link_capacity=link_capacity,
        latency=latency,
    )
    demands = generate_traffic(network, traffic_load=traffic_load)
    result = simulate(network, demands, link_weights=link_weights)
    metrics = calculate_metrics(network, result)
    return network, demands, result, metrics

