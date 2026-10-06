"""PPO Agent for Network Optimization using Stable-Baselines3.

Provides a clean, modular wrapper around Stable-Baselines3 PPO to optimize
routing link weights in NetworkEnv using continuous actions.
"""

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
from stable_baselines3 import PPO

from rl.environment import NetworkEnv


class NetworkPPOAgent:
    """Agent wrapping Stable-Baselines3 PPO for network routing optimization."""

    def __init__(
        self,
        env: NetworkEnv | None = None,
        learning_rate: float = 1e-3,
        n_steps: int = 128,
        batch_size: int = 64,
        ent_coef: float = 0.05,
        gamma: float = 0.99,
        seed: int | None = 42,
        model: PPO | None = None,
        verbose: int = 0,
    ) -> None:
        """Initialize PPO agent with environment and lightweight 2x64 MLP architecture."""
        self.env = env

        if model is not None:
            self.model = model
        else:
            if self.env is None:
                raise ValueError("An environment must be provided to initialize a new PPO model.")

            # Small 2-layer MLP (64 units each) optimized for fast laptop CPU execution
            policy_kwargs = dict(net_arch=dict(pi=[64, 64], vf=[64, 64]))

            self.model = PPO(
                policy="MlpPolicy",
                env=self.env,
                learning_rate=learning_rate,
                n_steps=n_steps,
                batch_size=batch_size,
                ent_coef=ent_coef,
                gamma=gamma,
                seed=seed,
                policy_kwargs=policy_kwargs,
                verbose=verbose,
            )

    def train(self, total_timesteps: int = 5000) -> "NetworkPPOAgent":
        """Train the PPO model for the specified number of timesteps."""
        self.model.learn(total_timesteps=total_timesteps)
        return self

    def predict(
        self, obs: np.ndarray | list[float], deterministic: bool = True
    ) -> tuple[np.ndarray, Any]:
        """Predict continuous action vector for a given observation."""
        if isinstance(obs, list):
            obs = np.array(obs, dtype=np.float32)
        action, state = self.model.predict(obs, deterministic=deterministic)
        return action, state

    def predict_weights(
        self, obs: np.ndarray | list[float], deterministic: bool = True
    ) -> list[float]:
        """Convenience method returning predicted link weights as a Python list of floats."""
        action, _ = self.predict(obs, deterministic=deterministic)
        # Ensure weights are positive floats >= 1.0
        return [float(max(1.0, float(w))) for w in action]

    def save(self, path: str | Path) -> str:
        """Save trained PPO model weights to disk."""
        target_path = Path(path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        # Stable-Baselines3 automatically appends .zip if omitted
        save_dest = str(target_path)
        if save_dest.endswith(".zip"):
            save_dest = save_dest[:-4]
        self.model.save(save_dest)
        return f"{save_dest}.zip"

    @classmethod
    def load(
        cls,
        path: str | Path,
        env: NetworkEnv | None = None,
    ) -> "NetworkPPOAgent":
        """Load trained PPO model weights from disk."""
        model_path = str(path)
        model = PPO.load(model_path, env=env)
        return cls(env=env, model=model)


def create_agent(
    env: NetworkEnv,
    learning_rate: float = 1e-3,
    n_steps: int = 128,
    batch_size: int = 64,
    ent_coef: float = 0.05,
    seed: int | None = 42,
    verbose: int = 0,
) -> NetworkPPOAgent:
    """Helper function to create a new NetworkPPOAgent."""
    return NetworkPPOAgent(
        env=env,
        learning_rate=learning_rate,
        n_steps=n_steps,
        batch_size=batch_size,
        ent_coef=ent_coef,
        seed=seed,
        verbose=verbose,
    )


def train_agent(agent: NetworkPPOAgent, total_timesteps: int = 5000) -> NetworkPPOAgent:
    """Helper function to train an agent."""
    return agent.train(total_timesteps=total_timesteps)


def save_agent(agent: NetworkPPOAgent, path: str | Path) -> str:
    """Helper function to save an agent."""
    return agent.save(path)


def load_agent(path: str | Path, env: NetworkEnv | None = None) -> NetworkPPOAgent:
    """Helper function to load an agent."""
    return NetworkPPOAgent.load(path, env=env)


def predict_action(
    agent: NetworkPPOAgent,
    obs: np.ndarray | list[float],
    deterministic: bool = True,
) -> np.ndarray:
    """Helper function to predict an action from observation."""
    action, _ = agent.predict(obs, deterministic=deterministic)
    return action
