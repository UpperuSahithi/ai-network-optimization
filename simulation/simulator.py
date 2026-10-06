from dataclasses import dataclass

from simulation.network import Link, Network
from simulation.routing import shortest_path
from simulation.traffic import TrafficDemand


@dataclass
class RoutedDemand:
    demand: TrafficDemand
    path: list[int] | None


@dataclass
class SimulationResult:
    routed_demands: list[RoutedDemand]
    link_traffic: dict[tuple[int, int], float]

    def traffic_on_link(self, link: Link) -> float:
        return self.link_traffic.get((link.source, link.destination), 0.0)


def simulate(
    network: Network,
    demands: list[TrafficDemand],
    link_weights: dict[tuple[int, int], float] | None = None,
) -> SimulationResult:
    """Send each demand along a shortest path and add its volume to every hop."""
    link_traffic = {
        (link.source, link.destination): 0.0 for link in network.get_links()
    }
    routed_demands: list[RoutedDemand] = []

    for demand in demands:
        path = shortest_path(
            network,
            demand.source,
            demand.destination,
            link_weights=link_weights,
        )
        routed_demands.append(RoutedDemand(demand=demand, path=path))
        if path is None:
            continue

        for hop_start, hop_end in zip(path, path[1:]):
            link = network.get_link_between(hop_start, hop_end)
            if link is None:
                continue
            key = (link.source, link.destination)
            link_traffic[key] += demand.volume

    return SimulationResult(routed_demands=routed_demands, link_traffic=link_traffic)

