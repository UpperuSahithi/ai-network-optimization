from dataclasses import dataclass

from simulation.network import Network


@dataclass(frozen=True)
class TrafficDemand:
    """Traffic that should travel from one node to another."""

    source: int
    destination: int
    volume: float


def generate_traffic(network: Network, traffic_load: float) -> list[TrafficDemand]:
    """Create a demand from every node to every higher-ID node.

    Each demand uses the same volume (`traffic_load`) so the pattern is
    deterministic and easy to inspect.
    """
    node_ids = [node.node_id for node in network.get_nodes()]
    demands: list[TrafficDemand] = []

    for index, source in enumerate(node_ids):
        for destination in node_ids[index + 1 :]:
            demands.append(
                TrafficDemand(
                    source=source,
                    destination=destination,
                    volume=traffic_load,
                )
            )

    return demands


def generate_hotspot_traffic(
    network: Network,
    base_load: float = 2.0,
    hotspot_multiplier: float = 4.0,
) -> list[TrafficDemand]:
    """Create deterministic asymmetric traffic demands with localized hotspots.

    Generates low background traffic between all node pairs and adds high hotspot
    volume across selected pairs (nodes 0, 1, 2) to produce bottleneck congestion
    on shortest paths that can be alleviated via alternate route diversion.
    """
    node_ids = [node.node_id for node in network.get_nodes()]
    demands: list[TrafficDemand] = []

    for index, source in enumerate(node_ids):
        for destination in node_ids[index + 1 :]:
            # Assign heavy volume to selected pairs (hotspot), background load to others
            if (source, destination) in ((0, 1), (1, 2)):
                vol = base_load * hotspot_multiplier
            elif (source, destination) == (0, 2):
                vol = base_load * (hotspot_multiplier * 0.75)
            else:
                vol = base_load

            demands.append(
                TrafficDemand(
                    source=source,
                    destination=destination,
                    volume=vol,
                )
            )

    return demands

