"""Baselines for Network Optimization.

Provides reference routing strategies evaluated on the exact same NetworkEnv:
1. Static Shortest Path Baseline: Uniform link weights (1.0), replicating standard OSPF/BFS shortest-hop routing.
2. Random Weights Baseline: Uniformly samples valid continuous weights in the action space.
"""

import sys
from pathlib import Path
from typing import Any
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rl.environment import NetworkEnv


class StaticBaseline:
    """Baseline agent setting uniform link weights (1.0) on all links.

    This represents static shortest-hop routing (standard BFS / default Dijkstra).
    """

    def __init__(self, action_dim: int) -> None:
        self.action_dim = action_dim

    def predict(self, obs: Any = None) -> list[float]:
        """Return static weights of 1.0 for all links."""
        return [1.0] * self.action_dim


class RandomBaseline:
    """Baseline agent sampling random valid continuous weights from the action space."""

    def __init__(
        self,
        action_dim: int,
        low: float = 1.0,
        high: float = 10.0,
        seed: int | None = None,
    ) -> None:
        self.action_dim = action_dim
        self.low = low
        self.high = high
        self.rng = np.random.default_rng(seed)

    def predict(self, obs: Any = None) -> list[float]:
        """Sample uniform random weights within [low, high] for all links."""
        return [float(w) for w in self.rng.uniform(self.low, self.high, size=self.action_dim)]


def evaluate_policy(
    env: NetworkEnv,
    policy: Any,
    episodes: int = 5,
) -> dict[str, float]:
    """Evaluate a policy (Static, Random, or PPO Agent) on the environment.

    Runs `episodes` complete rollouts and calculates average metrics directly from
    the simulator.

    Returns:
        Dictionary containing mean throughput, latency, packet_loss, congestion,
        link_utilization, and reward across all evaluation episodes.
    """
    total_rewards: list[float] = []
    throughputs: list[float] = []
    latencies: list[float] = []
    packet_losses: list[float] = []
    congestions: list[float] = []
    utilizations: list[float] = []

    for _ in range(episodes):
        obs, _ = env.reset()
        episode_reward = 0.0
        terminated = False
        truncated = False

        while not (terminated or truncated):
            # Supports both PPO agent (with predict/predict_weights) and baseline classes
            if hasattr(policy, "predict_weights"):
                action = policy.predict_weights(obs)
            elif hasattr(policy, "predict"):
                pred = policy.predict(obs)
                # If SB3 agent predict was passed directly, unpack tuple
                if isinstance(pred, tuple):
                    pred = pred[0]
                action = list(pred) if hasattr(pred, "__iter__") else pred
            else:
                action = policy(obs)

            obs, reward, terminated, truncated, _ = env.step(action)
            episode_reward += reward

        total_rewards.append(episode_reward)
        if env.last_metrics is not None:
            throughputs.append(env.last_metrics.throughput)
            latencies.append(env.last_metrics.latency)
            packet_losses.append(env.last_metrics.packet_loss)
            congestions.append(env.last_metrics.congestion)
            utilizations.append(env.last_metrics.link_utilization)

    def _mean(values: list[float]) -> float:
        return float(np.mean(values)) if values else 0.0

    return {
        "throughput": round(_mean(throughputs), 4),
        "latency": round(_mean(latencies), 4),
        "packet_loss": round(_mean(packet_losses), 4),
        "congestion": round(_mean(congestions), 4),
        "link_utilization": round(_mean(utilizations), 4),
        "reward": round(_mean(total_rewards), 4),
    }
