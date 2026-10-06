"""Reinforcement Learning Environment for Network Optimization.

Provides a clean, Gymnasium-compatible interface for RL agents to interact with
the network simulator.
"""

from typing import Any

from simulation.engine import create_requested_network
from simulation.metrics import NetworkMetrics, calculate_metrics
from simulation.network import Network
from simulation.simulator import SimulationResult, simulate
from simulation.traffic import TrafficDemand, generate_hotspot_traffic, generate_traffic

try:
    import gymnasium as gym
    from gymnasium import spaces
    _GYMNASIUM_AVAILABLE = True
except ImportError:
    _GYMNASIUM_AVAILABLE = False
    gym = object  # type: ignore

try:
    import numpy as np
    _NUMPY_AVAILABLE = True
except ImportError:
    _NUMPY_AVAILABLE = False


class SimpleBoxSpace:
    """Lightweight fallback for gymnasium.spaces.Box when gymnasium is not installed."""

    def __init__(self, low: float, high: float, shape: tuple[int, ...], dtype: str = "float32") -> None:
        self.low = low
        self.high = high
        self.shape = shape
        self.dtype = dtype

    def contains(self, x: Any) -> bool:
        if hasattr(x, "shape") and x.shape != self.shape:
            return False
        if isinstance(x, (list, tuple)) and len(x) != self.shape[0]:
            return False
        return True

    def __repr__(self) -> str:
        return f"Box(low={self.low}, high={self.high}, shape={self.shape}, dtype={self.dtype})"


_EnvBase = gym.Env if _GYMNASIUM_AVAILABLE else object


class NetworkEnv(_EnvBase):
    """Standard RL environment wrapping the network simulation engine.

    The state/observation reflects link utilization, traffic volume, latency, and loss.
    The action represents link weight adjustments used for dynamic routing decisions.
    Supports both dictionary observations (for inspection/UI) and flat numerical vectors
    (for RL agents and neural network policies).
    """

    def __init__(
        self,
        number_of_nodes: int = 5,
        topology: str = "ring",
        link_capacity: float = 10.0,
        traffic_load: float = 10.0,
        max_steps: int = 100,
        reward_weights: dict[str, float] | None = None,
        obs_mode: str = "dict",
        traffic_pattern: str = "uniform",
        custom_demands: list[TrafficDemand] | None = None,
    ) -> None:
        if _GYMNASIUM_AVAILABLE:
            super().__init__()

        self.number_of_nodes = number_of_nodes
        self.topology = topology
        self.link_capacity = link_capacity
        self.traffic_load = traffic_load
        self.max_steps = max_steps
        self.obs_mode = obs_mode
        self.traffic_pattern = traffic_pattern
        self.custom_demands = custom_demands

        # Default weights for scalar reward calculation
        self.reward_weights = reward_weights or {
            "throughput": 1.0,
            "latency": -10.0,
            "packet_loss": -100.0,
            "congestion": -20.0,
        }

        # Inspect network structure to establish action and observation dimensions
        initial_net = create_requested_network(
            number_of_nodes=self.number_of_nodes,
            topology=self.topology,
            link_capacity=self.link_capacity,
        )
        self._action_dim = len(initial_net.get_links())
        # 4 features per link (utilization, traffic, capacity, congested) + 6 global features
        self._observation_dim = 4 * self._action_dim + 6

        # Action space: continuous weights for each link [1.0, 10.0]
        # Observation space: bounded/unbounded non-negative metric features
        if _GYMNASIUM_AVAILABLE and _NUMPY_AVAILABLE:
            self.action_space = spaces.Box(
                low=1.0, high=10.0, shape=(self._action_dim,), dtype=np.float32
            )
            self.observation_space = spaces.Box(
                low=0.0, high=float("inf"), shape=(self._observation_dim,), dtype=np.float32
            )
        else:
            self.action_space = SimpleBoxSpace(
                low=1.0, high=10.0, shape=(self._action_dim,), dtype="float32"
            )
            self.observation_space = SimpleBoxSpace(
                low=0.0, high=float("inf"), shape=(self._observation_dim,), dtype="float32"
            )

        self.current_step = 0
        self.network: Network | None = None
        self.demands: list[TrafficDemand] = []
        self.last_metrics: NetworkMetrics | None = None

    @property
    def action_dim(self) -> int:
        """Number of links in network that receive routing weights."""
        return self._action_dim

    @property
    def observation_dim(self) -> int:
        """Length of the flat numeric observation vector."""
        return self._observation_dim

    def reset(
        self,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any] | list[float] | Any, dict[str, Any]]:
        """Reset the environment to initial state."""
        self.current_step = 0
        self.network = create_requested_network(
            number_of_nodes=self.number_of_nodes,
            topology=self.topology,
            link_capacity=self.link_capacity,
        )

        if self.custom_demands is not None:
            self.demands = list(self.custom_demands)
        elif self.traffic_pattern in ("hotspot", "asymmetric"):
            self.demands = generate_hotspot_traffic(
                self.network,
                base_load=max(1.0, self.traffic_load * 0.2),
                hotspot_multiplier=4.0,
            )
        else:
            self.demands = generate_traffic(self.network, traffic_load=self.traffic_load)

        result = simulate(self.network, self.demands)
        self.last_metrics = calculate_metrics(self.network, result)

        obs = self._get_observation()
        info = self._get_info()
        return obs, info

    def step(
        self, action: Any = None
    ) -> tuple[dict[str, Any] | list[float] | Any, float, bool, bool, dict[str, Any]]:
        """Execute one step in the environment by applying routing link weights.

        Args:
            action: A dictionary mapping link tuples (source, dest) to weight,
                    a list/array of weights matching network links, or None for default.

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

    def get_observation_vector(self) -> list[float] | Any:
        """Return a normalized 1D numeric observation vector for RL algorithms."""
        if self.last_metrics is None or self.network is None:
            vec = [0.0] * self._observation_dim
        else:
            vec = []
            base_cap = max(1.0, float(self.link_capacity))
            total_offered = sum(d.volume for d in self.demands) if self.demands else 1.0

            # Per-link local features (4 per link)
            for link in self.last_metrics.links:
                # 1. Utilization ratio (traffic / capacity, typically 0.0 - 2.0)
                vec.append(float(link.utilization))
                # 2. Normalized traffic relative to link capacity (0.0 - 2.0)
                vec.append(float(link.traffic / max(1.0, link.capacity)))
                # 3. Normalized capacity relative to base link capacity (~1.0)
                vec.append(float(link.capacity / base_cap))
                # 4. Congestion indicator (0.0 or 1.0)
                vec.append(1.0 if link.congested else 0.0)

            # Global network-wide health features (5)
            # 5. Normalized throughput: delivered fraction of offered traffic in [0.0, 1.0]
            norm_throughput = self.last_metrics.throughput / max(1.0, total_offered)
            vec.append(float(norm_throughput))

            # 6. Normalized latency: path delay scaled by node diameter in [0.1, 2.0]
            norm_latency = self.last_metrics.latency / max(1.0, float(self.number_of_nodes))
            vec.append(float(norm_latency))

            # 7. Packet loss ratio in [0.0, 1.0]
            vec.append(float(self.last_metrics.packet_loss))

            # 8. Congestion ratio in [0.0, 1.0]
            vec.append(float(self.last_metrics.congestion))

            # 9. Average link utilization in [0.0, 2.0]
            vec.append(float(self.last_metrics.link_utilization))

            # Progress feature (1)
            # 10. Episode progress in [0.0, 1.0]
            progress = (self.current_step / self.max_steps) if self.max_steps > 0 else 0.0
            vec.append(float(progress))

        if _NUMPY_AVAILABLE:
            return np.array(vec, dtype=np.float32)
        return vec

    def _parse_action(
        self, action: Any
    ) -> dict[tuple[int, int], float] | None:
        if action is None:
            return None

        if isinstance(action, dict):
            return action

        if hasattr(action, "tolist"):
            action = action.tolist()

        if isinstance(action, (list, tuple)):
            links = self.network.get_links() if self.network else []
            if len(action) != len(links):
                raise ValueError(
                    f"Action vector length ({len(action)}) must match network link count ({len(links)})."
                )
            weights = {}
            for link, w in zip(links, action):
                # Ensure weight is at least 1.0 (positive routing weight for Dijkstra)
                weights[(link.source, link.destination)] = max(1.0, float(w))
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

    def _get_observation(self) -> dict[str, Any] | list[float] | Any:
        if self.obs_mode == "vector":
            return self.get_observation_vector()

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
