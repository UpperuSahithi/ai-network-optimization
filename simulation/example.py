"""Create a network, generate traffic, simulate, and print link loads."""

from simulation.metrics import calculate_metrics
from simulation.simulator import simulate
from simulation.topology import (
    create_bus_topology,
    create_line_topology,
    create_mesh_topology,
    create_ring_topology,
    create_star_topology,
)
from simulation.traffic import generate_traffic


def print_result(name: str, network, demands, result) -> None:
    print(f"=== {name} ===")
    print("Nodes:", [node.node_id for node in network.get_nodes()])
    print("Demands:")
    for demand in demands:
        print(f"  {demand.source} -> {demand.destination}  volume={demand.volume}")

    print("Paths:")
    for routed in result.routed_demands:
        demand = routed.demand
        if routed.path is None:
            print(f"  {demand.source} -> {demand.destination}: unreachable")
        else:
            hops = " -> ".join(str(node_id) for node_id in routed.path)
            print(f"  {demand.source} -> {demand.destination}: {hops}")

    print("Link traffic:")
    for link in network.get_links():
        traffic = result.traffic_on_link(link)
        print(
            f"  {link.source} -> {link.destination}  "
            f"traffic={traffic}  capacity={link.capacity}"
        )

    metrics = calculate_metrics(network, result)
    print("Metrics:")
    print(f"  latency={metrics.latency}")
    print(f"  throughput={metrics.throughput}")
    print(f"  packet_loss={metrics.packet_loss}")
    print(f"  congestion={metrics.congestion}")
    print(f"  link_utilization={metrics.link_utilization}")
    print()


def main() -> None:
    node_count = 5
    capacity = 10.0
    latency = 1.0
    traffic_load = 2.0

    topologies = [
        ("line", create_line_topology),
        ("bus", create_bus_topology),
        ("star", create_star_topology),
        ("ring", create_ring_topology),
        ("mesh", create_mesh_topology),
    ]

    for name, builder in topologies:
        network = builder(node_count, capacity=capacity, latency=latency)
        demands = generate_traffic(network, traffic_load=traffic_load)
        result = simulate(network, demands)
        print_result(name, network, demands, result)


if __name__ == "__main__":
    main()
