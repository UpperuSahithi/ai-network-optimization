"""Unit tests for standard RL NetworkEnv interface."""

import unittest
from typing import Any

import numpy as np

from rl.environment import NetworkEnv


class MockArray:
    """Simulates a NumPy array or PyTorch tensor with a .tolist() method."""

    def __init__(self, values: list[float]) -> None:
        self.values = values

    def tolist(self) -> list[float]:
        return list(self.values)


class EnvironmentTests(unittest.TestCase):
    def test_env_without_reset_raises_error(self) -> None:
        env = NetworkEnv()
        with self.assertRaises(RuntimeError):
            env.step()

    def test_env_reset(self) -> None:
        env = NetworkEnv(number_of_nodes=4, topology="ring", link_capacity=10.0)
        obs, info = env.reset()

        self.assertEqual(obs["step"], 0)
        self.assertIn("throughput", obs)
        self.assertIn("latency", obs)
        self.assertIn("packet_loss", obs)
        self.assertIn("links", obs)
        self.assertEqual(info["node_count"], 4)
        self.assertEqual(info["link_count"], 4)
        self.assertEqual(info["topology"], "ring")

    def test_env_step_default_action(self) -> None:
        env = NetworkEnv(number_of_nodes=5, topology="star", max_steps=10)
        env.reset()
        obs, reward, terminated, truncated, info = env.step()

        self.assertEqual(obs["step"], 1)
        self.assertIsInstance(reward, float)
        self.assertFalse(terminated)
        self.assertFalse(truncated)
        self.assertIn("links", obs)

    def test_env_step_with_dict_action(self) -> None:
        env = NetworkEnv(number_of_nodes=3, topology="line")
        env.reset()
        action = {(0, 1): 5.0, (1, 2): 1.0}
        obs, reward, terminated, truncated, _info = env.step(action)

        self.assertEqual(obs["step"], 1)
        self.assertIsInstance(reward, float)

    def test_env_step_with_list_action(self) -> None:
        env = NetworkEnv(number_of_nodes=3, topology="line")
        env.reset()
        # Line topology with 3 nodes has 2 links
        action = [2.0, 10.0]
        obs, reward, _terminated, _truncated, _info = env.step(action)
        self.assertEqual(obs["step"], 1)

    def test_env_step_with_tuple_action(self) -> None:
        env = NetworkEnv(number_of_nodes=3, topology="line")
        env.reset()
        action = (3.0, 4.0)
        obs, reward, _terminated, _truncated, _info = env.step(action)
        self.assertEqual(obs["step"], 1)
        self.assertIsInstance(reward, float)

    def test_env_step_with_array_like_action(self) -> None:
        env = NetworkEnv(number_of_nodes=3, topology="line")
        env.reset()
        action = MockArray([5.0, 7.0])
        obs, reward, _terminated, _truncated, _info = env.step(action)
        self.assertEqual(obs["step"], 1)
        self.assertIsInstance(reward, float)

    def test_env_action_clamping_minimum_weight(self) -> None:
        env = NetworkEnv(number_of_nodes=3, topology="line")
        env.reset()
        # Non-positive or sub-1 weights should be clamped to >= 1.0
        action = [-2.0, 0.5]
        parsed = env._parse_action(action)
        self.assertIsNotNone(parsed)
        for weight in parsed.values():
            self.assertGreaterEqual(weight, 1.0)

    def test_env_spaces_and_dimensions(self) -> None:
        # Ring with 5 nodes has 5 links
        env = NetworkEnv(number_of_nodes=5, topology="ring")
        self.assertEqual(env.action_dim, 5)
        # 4 features per link * 5 links + 6 global features = 26
        self.assertEqual(env.observation_dim, 26)
        self.assertEqual(env.action_space.shape, (5,))
        self.assertEqual(env.observation_space.shape, (26,))

    def test_env_vector_obs_mode(self) -> None:
        env = NetworkEnv(number_of_nodes=4, topology="ring", obs_mode="vector")
        obs, info = env.reset()
        # 4 links * 4 + 6 = 22
        self.assertEqual(len(obs), 22)
        self.assertTrue(isinstance(obs[0], (float, np.floating)))

        obs_next, reward, terminated, truncated, info = env.step([1.0, 2.0, 1.0, 2.0])
        self.assertEqual(len(obs_next), 22)
        self.assertIsInstance(reward, float)

    def test_env_get_observation_vector(self) -> None:
        env = NetworkEnv(number_of_nodes=4, topology="ring")
        env.reset()
        vec = env.get_observation_vector()
        self.assertEqual(len(vec), env.observation_dim)
        for val in vec:
            self.assertTrue(isinstance(val, (float, np.floating)))

    def test_env_step_invalid_action_length(self) -> None:
        env = NetworkEnv(number_of_nodes=3, topology="line")
        env.reset()
        with self.assertRaises(ValueError):
            env.step([1.0])  # Expects 2 link weights

    def test_env_step_invalid_action_type(self) -> None:
        env = NetworkEnv(number_of_nodes=3, topology="line")
        env.reset()
        with self.assertRaises(TypeError):
            env.step("invalid_action")  # type: ignore

    def test_env_truncation(self) -> None:
        env = NetworkEnv(max_steps=3)
        env.reset()
        _, _, _, truncated, _ = env.step()
        self.assertFalse(truncated)
        _, _, _, truncated, _ = env.step()
        self.assertFalse(truncated)
        _, _, _, truncated, _ = env.step()
        self.assertTrue(truncated)


    def test_env_hotspot_traffic_pattern(self) -> None:
        env = NetworkEnv(number_of_nodes=5, topology="ring", traffic_pattern="hotspot")
        obs, info = env.reset()
        # Verify that hotspot demands are populated and (0,1) has high volume
        self.assertEqual(len(env.demands), 10)
        h01 = [d for d in env.demands if (d.source, d.destination) == (0, 1)][0]
        self.assertGreater(h01.volume, 5.0)

    def test_observation_vector_scaling_bounds(self) -> None:
        env = NetworkEnv(number_of_nodes=5, topology="ring", traffic_pattern="hotspot")
        env.reset()
        vec = env.get_observation_vector()
        self.assertEqual(len(vec), env.observation_dim)
        for val in vec:
            # Scaled features should be compact and bounded
            self.assertGreaterEqual(float(val), 0.0)
            self.assertLessEqual(float(val), 5.0)


if __name__ == "__main__":
    unittest.main()
