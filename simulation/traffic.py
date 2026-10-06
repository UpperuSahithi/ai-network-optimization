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
