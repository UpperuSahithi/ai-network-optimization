from dataclasses import asdict, dataclass

from simulation.network import Network
from simulation.simulator import SimulationResult


@dataclass
class LinkMetrics:
    source: int
    destination: int
    traffic: float
    capacity: float
    utilization: float
    congested: bool
    latency: float


@dataclass
class NetworkMetrics:
    latency: float
    throughput: float
    packet_loss: float
    congestion: float
    link_utilization: float
    links: list[LinkMetrics]

    def to_dict(self) -> dict:
        return asdict(self)


def _link_utilization(traffic: float, capacity: float) -> float:
    if capacity <= 0:
        return 0.0
    return traffic / capacity


def calculate_metrics(network: Network, result: SimulationResult) -> NetworkMetrics:
    """Compute network-wide metrics from routed traffic.

    - utilization: traffic / capacity on a link (can be above 1.0)
    - congestion: share of links with utilization > 1.0
    - latency: average path delay; congested hops are scaled by utilization
    - throughput: demand volume that still fits after bottleneck links
    - packet_loss: 1 - delivered / offered
    """
    link_metrics: list[LinkMetrics] = []
    utilizations: list[float] = []
    congested_count = 0

    for link in network.get_links():
        traffic = result.traffic_on_link(link)
        utilization = _link_utilization(traffic, link.capacity)
        congested = utilization > 1.0
        if congested:
            congested_count += 1
        utilizations.append(utilization)
        link_metrics.append(
            LinkMetrics(
                source=link.source,
                destination=link.destination,
                traffic=round(traffic, 4),
                capacity=link.capacity,
                utilization=round(utilization, 4),
                congested=congested,
                latency=link.latency,
            )
        )

    offered = 0.0
    delivered = 0.0
    path_latencies: list[float] = []

    for routed in result.routed_demands:
        volume = routed.demand.volume
        offered += volume

        if routed.path is None or len(routed.path) < 2:
            if routed.path is not None and len(routed.path) == 1:
                delivered += volume
                path_latencies.append(0.0)
            continue

        delivery_ratio = 1.0
        path_latency = 0.0
        reachable = True

        for hop_start, hop_end in zip(routed.path, routed.path[1:]):
            link = network.get_link_between(hop_start, hop_end)
            if link is None:
                reachable = False
                break

            traffic = result.traffic_on_link(link)
            utilization = _link_utilization(traffic, link.capacity)
            path_latency += link.latency * max(1.0, utilization)

            if traffic <= 0:
                share = 1.0
            elif link.capacity <= 0:
                share = 0.0
            else:
                share = min(1.0, link.capacity / traffic)
            delivery_ratio = min(delivery_ratio, share)

        if not reachable:
            continue

        delivered += volume * delivery_ratio
        path_latencies.append(path_latency)

    packet_loss = 0.0 if offered == 0 else 1.0 - (delivered / offered)
    average_latency = (
        sum(path_latencies) / len(path_latencies) if path_latencies else 0.0
    )
    average_utilization = (
        sum(utilizations) / len(utilizations) if utilizations else 0.0
    )
    congestion = (
        congested_count / len(link_metrics) if link_metrics else 0.0
    )

    return NetworkMetrics(
        latency=round(average_latency, 4),
        throughput=round(delivered, 4),
        packet_loss=round(packet_loss, 4),
        congestion=round(congestion, 4),
        link_utilization=round(average_utilization, 4),
        links=link_metrics,
    )
