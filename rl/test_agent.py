"""Unit tests for PPO Agent, Baselines, and Training Pipeline."""

import tempfile
import unittest
from pathlib import Path

import numpy as np

from rl.agent import NetworkPPOAgent, create_agent, load_agent, predict_action, save_agent
from rl.baseline import RandomBaseline, StaticBaseline, evaluate_policy
from rl.environment import NetworkEnv
from rl.train import run_experiment


class AgentAndBaselineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.env = NetworkEnv(
            number_of_nodes=4,
            topology="ring",
            link_capacity=10.0,
            traffic_load=5.0,
            max_steps=20,
            obs_mode="vector",
        )

    def test_agent_creation(self) -> None:
        agent = create_agent(self.env, seed=42)
        self.assertIsNotNone(agent.model)
        self.assertEqual(agent.env, self.env)

        # Verify MLP policy architecture (2 hidden layers of 64 units)
        mlp_extractor = agent.model.policy.mlp_extractor
        policy_layers = [l for l in mlp_extractor.policy_net if hasattr(l, "out_features")]
        self.assertEqual(len(policy_layers), 2)
        self.assertEqual(policy_layers[0].out_features, 64)
        self.assertEqual(policy_layers[1].out_features, 64)

    def test_action_shape_and_range(self) -> None:
        agent = create_agent(self.env, seed=42)
        obs, _ = self.env.reset()

        action, _ = agent.predict(obs)
        self.assertIsInstance(action, np.ndarray)
        self.assertEqual(action.shape, (self.env.action_dim,))

        weights = agent.predict_weights(obs)
        self.assertEqual(len(weights), self.env.action_dim)
        for w in weights:
            self.assertGreaterEqual(w, 1.0)

        # Test helper function
        action_helper = predict_action(agent, obs)
        self.assertEqual(action_helper.shape, (self.env.action_dim,))

    def test_model_save_and_load(self) -> None:
        agent = create_agent(self.env, seed=42)
        obs, _ = self.env.reset()
        action_before, _ = agent.predict(obs, deterministic=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "test_ppo_model.zip"
            saved_file = save_agent(agent, save_path)
            self.assertTrue(Path(saved_file).exists())

            # Load model back
            loaded_agent = load_agent(saved_file, env=self.env)
            self.assertIsInstance(loaded_agent, NetworkPPOAgent)

            action_after, _ = loaded_agent.predict(obs, deterministic=True)
            np.testing.assert_allclose(action_before, action_after, rtol=1e-5)

    def test_static_baseline_execution(self) -> None:
        baseline = StaticBaseline(action_dim=self.env.action_dim)
        weights = baseline.predict()
        self.assertEqual(weights, [1.0] * self.env.action_dim)

        results = evaluate_policy(self.env, baseline, episodes=2)
        self.assertIn("throughput", results)
        self.assertIn("latency", results)
        self.assertIn("packet_loss", results)
        self.assertIn("congestion", results)
        self.assertIn("reward", results)
        self.assertIsInstance(results["reward"], float)

    def test_random_baseline_execution(self) -> None:
        baseline = RandomBaseline(action_dim=self.env.action_dim, low=1.0, high=10.0, seed=123)
        weights = baseline.predict()
        self.assertEqual(len(weights), self.env.action_dim)
        for w in weights:
            self.assertTrue(1.0 <= w <= 10.0)

        results = evaluate_policy(self.env, baseline, episodes=2)
        self.assertIn("reward", results)
        self.assertIsInstance(results["reward"], float)

    def test_small_training_and_evaluation_run(self) -> None:
        # Fast mini-training run of 256 steps (2 PPO rollouts of n_steps=128)
        agent = create_agent(self.env, n_steps=128, batch_size=64, seed=42)
        agent.train(total_timesteps=256)

        results = evaluate_policy(self.env, agent, episodes=2)
        self.assertIn("throughput", results)
        self.assertIn("reward", results)
        self.assertIsInstance(results["reward"], float)

    def test_experiment_runner(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            res = run_experiment(
                total_timesteps=256,
                number_of_nodes=3,
                topology="line",
                link_capacity=10.0,
                traffic_load=5.0,
                max_steps=10,
                eval_episodes=2,
                model_dir=tmpdir,
                seed=42,
            )
            self.assertIn("static", res)
            self.assertIn("random", res)
            self.assertIn("ppo", res)
            self.assertIn("comparison", res)
            self.assertTrue(Path(res["saved_model"]).exists())


if __name__ == "__main__":
    unittest.main()
