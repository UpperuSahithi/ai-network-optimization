"""Reinforcement Learning Environment for Network Optimization.

Provides a clean, Gym-compatible interface for RL agents to interact with
the network simulator.
"""

from typing import Any

from simulation.engine import create_requested_network
from simulation.metrics import NetworkMetrics, calculate_metrics
from simulation.network import Network
from simulation.simulator import SimulationResult, simulate
from simulation.traffic import TrafficDemand, generate_traffic


class NetworkEnv:
    """Standard RL environment wrapping the network simulation engine.

    The state/observation reflects link utilization, traffic volume, latency, and loss.
    The action represents link weight adjustments used for dynamic routing decisions.
    """

    def __init__(
        self,
        number_of_nodes: int = 5,
        topology: str = "ring",
        link_capacity: float = 10.0,
        traffic_load: float = 10.0,
        max_steps: int = 100,
        reward_weights: dict[str, float] | None = None,
    ) -> None:
        self.number_of_nodes = number_of_nodes
        self.topology = topology
        self.link_capacity = link_capacity
        self.traffic_load = traffic_load
        self.max_steps = max_steps

        # Default weights for scalar reward calculation
        self.reward_weights = reward_weights or {
            "throughput": 1.0,
            "latency": -10.0,
            "packet_loss": -100.0,
            "congestion": -20.0,
        }

        self.current_step = 0
        self.network: Network | None = None
        self.demands: list[TrafficDemand] = []
        self.last_metrics: NetworkMetrics | None = None

    def reset(self) -> tuple[dict[str, Any], dict[str, Any]]:
        """Reset the environment to initial state."""
        self.current_step = 0
        self.network = create_requested_network(
            number_of_nodes=self.number_of_nodes,
            topology=self.topology,
            link_capacity=self.link_capacity,
        )
        self.demands = generate_traffic(self.network, traffic_load=self.traffic_load)
        result = simulate(self.network, self.demands)
        self.last_metrics = calculate_metrics(self.network, result)

        obs = self._get_observation()
        info = self._get_info()
        return obs, info

    def step(
        self, action: dict[tuple[int, int], float] | list[float] | None = None
    ) -> tuple[dict[str, Any], float, bool, bool, dict[str, Any]]:
        """Execute one step in the environment by applying routing link weights.

        Args:
            action: A dictionary mapping link tuples (source, dest) to weight,
                    a list of weights matching network links, or None for default.

        Returns:
            (observation, reward, terminated, truncated, info)
        """
        if self.network is None:
            raise RuntimeError("Environment must be reset() before calling step().")

        self.current_step += 1
        link_weights = self._parse_action(action)

        result = simulate(self.network, self.demands, link_weights=link_weights)
        self.last_metrics = calculate_metrics(self.network, result)

        obs = self._get_observation()
        reward = self._calculate_reward(self.last_metrics)
        terminated = False
        truncated = self.current_step >= self.max_steps
        info = self._get_info()

        return obs, reward, terminated, truncated, info

    def _parse_action(
        self, action: dict[tuple[int, int], float] | list[float] | None
    ) -> dict[tuple[int, int], float] | None:
        if action is None:
            return None

        if isinstance(action, dict):
            return action

        if isinstance(action, (list, tuple)):
            links = self.network.get_links() if self.network else []
            if len(action) != len(links):
                raise ValueError(
                    f"Action vector length ({len(action)}) must match network link count ({len(links)})."
                )
            weights = {}
            for link, w in zip(links, action):
                weights[(link.source, link.destination)] = float(w)
            return weights

        raise TypeError(f"Unsupported action type: {type(action)}")

    def _calculate_reward(self, metrics: NetworkMetrics) -> float:
        w = self.reward_weights
        reward = (
            w["throughput"] * metrics.throughput
            + w["latency"] * metrics.latency
            + w["packet_loss"] * metrics.packet_loss
            + w["congestion"] * metrics.congestion
        )
        return round(reward, 4)

    def _get_observation(self) -> dict[str, Any]:
        if self.last_metrics is None or self.network is None:
            return {}

        link_obs = [
            {
                "source": link.source,
                "destination": link.destination,
                "traffic": link.traffic,
                "capacity": link.capacity,
                "utilization": link.utilization,
                "congested": link.congested,
            }
            for link in self.last_metrics.links
        ]

        return {
            "step": self.current_step,
            "throughput": self.last_metrics.throughput,
            "latency": self.last_metrics.latency,
            "packet_loss": self.last_metrics.packet_loss,
            "congestion": self.last_metrics.congestion,
            "link_utilization": self.last_metrics.link_utilization,
            "links": link_obs,
        }

    def _get_info(self) -> dict[str, Any]:
        link_count = len(self.network.get_links()) if self.network else 0
        node_count = len(self.network.get_nodes()) if self.network else 0
        return {
            "node_count": node_count,
            "link_count": link_count,
            "demand_count": len(self.demands),
            "topology": self.topology,
        }
