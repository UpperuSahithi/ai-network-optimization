from dataclasses import dataclass, field


@dataclass(frozen=True)
class Node:
    """A network node identified by an integer ID."""

    node_id: int


@dataclass(frozen=True)
class Link:
    """A connection from one node to another."""

    source: int
    destination: int
    capacity: float
    latency: float


@dataclass
class Network:
    """Stores nodes and links and provides basic lookup helpers."""

    nodes: dict[int, Node] = field(default_factory=dict)
    links: list[Link] = field(default_factory=list)

    def add_node(self, node_id: int) -> Node:
        if node_id not in self.nodes:
            self.nodes[node_id] = Node(node_id=node_id)
        return self.nodes[node_id]

    def add_link(
        self,
        source: int,
        destination: int,
        capacity: float,
        latency: float,
    ) -> Link:
        if source not in self.nodes:
            raise ValueError(f"Unknown source node: {source}")
        if destination not in self.nodes:
            raise ValueError(f"Unknown destination node: {destination}")

        link = Link(
            source=source,
            destination=destination,
            capacity=capacity,
            latency=latency,
        )
        self.links.append(link)
        return link

    def get_nodes(self) -> list[Node]:
        return [self.nodes[node_id] for node_id in sorted(self.nodes)]

    def get_links(self) -> list[Link]:
        return list(self.links)

    def neighbors(self, node_id: int) -> list[int]:
        connected = []
        for link in self.links:
            if link.source == node_id:
                connected.append(link.destination)
            elif link.destination == node_id:
                connected.append(link.source)
        return connected

    def get_link_between(self, node_a: int, node_b: int) -> Link | None:
        for link in self.links:
            same_direction = link.source == node_a and link.destination == node_b
            reverse_direction = link.source == node_b and link.destination == node_a
            if same_direction or reverse_direction:
                return link
        return None
