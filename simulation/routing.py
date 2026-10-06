import heapq
from collections import deque

from simulation.network import Network


def shortest_path(
    network: Network,
    source: int,
    destination: int,
    link_weights: dict[tuple[int, int], float] | None = None,
) -> list[int] | None:
    """Return shortest path. If link_weights is None, uses BFS (fewest hops)."""
    if source == destination:
        return [source]
    if source not in network.nodes or destination not in network.nodes:
        return None

    if link_weights is not None:
        return _dijkstra_shortest_path(network, source, destination, link_weights)

    parent: dict[int, int | None] = {source: None}
    queue: deque[int] = deque([source])

    while queue:
        current = queue.popleft()
        for neighbor in sorted(set(network.neighbors(current))):
            if neighbor in parent:
                continue
            parent[neighbor] = current
            if neighbor == destination:
                return _rebuild_path(parent, destination)
            queue.append(neighbor)

    return None


def _dijkstra_shortest_path(
    network: Network,
    source: int,
    destination: int,
    link_weights: dict[tuple[int, int], float],
) -> list[int] | None:
    distances: dict[int, float] = {source: 0.0}
    parent: dict[int, int | None] = {source: None}
    pq: list[tuple[float, int]] = [(0.0, source)]
    visited = set()

    while pq:
        dist, current = heapq.heappop(pq)
        if current in visited:
            continue
        visited.add(current)

        if current == destination:
            return _rebuild_path(parent, destination)

        for neighbor in sorted(set(network.neighbors(current))):
            if neighbor in visited:
                continue
            link = network.get_link_between(current, neighbor)
            if link is None:
                continue
            weight = link_weights.get((link.source, link.destination), 1.0)
            if weight < 0:
                weight = 1.0

            new_dist = dist + weight
            if new_dist < distances.get(neighbor, float("inf")):
                distances[neighbor] = new_dist
                parent[neighbor] = current
                heapq.heappush(pq, (new_dist, neighbor))

    return None


def _rebuild_path(parent: dict[int, int | None], destination: int) -> list[int]:
    path = [destination]
    current = destination
    while parent[current] is not None:
        current = parent[current]
        path.append(current)
    path.reverse()
    return path

