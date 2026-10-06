"""Unit tests for standard RL NetworkEnv interface."""

import unittest

from rl.environment import NetworkEnv


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


if __name__ == "__main__":
    unittest.main()
