"""Unit and integration tests for FastAPI backend API endpoints."""

import unittest
from fastapi.testclient import TestClient

from backend.main import app


class BackendApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_health_endpoint(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_simulate_endpoint(self) -> None:
        payload = {
            "number_of_nodes": 4,
            "topology": "ring",
            "link_capacity": 10.0,
            "traffic_load": 5.0,
        }
        response = self.client.post("/simulate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["node_count"], 4)
        self.assertEqual(data["link_count"], 4)
        self.assertIn("metrics", data)

    def test_optimize_success(self) -> None:
        payload = {
            "number_of_nodes": 5,
            "topology": "ring",
            "link_capacity": 10.0,
            "traffic_pattern": "hotspot",
        }
        response = self.client.post("/optimize", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Check top-level structure
        self.assertEqual(data["status"], "success")
        self.assertIn("configuration", data)
        self.assertIn("baseline", data)
        self.assertIn("ppo", data)
        self.assertIn("improvement", data)
        self.assertIn("link_weights", data)
        self.assertIn("links", data)

        # Check configuration reflection
        self.assertEqual(data["configuration"]["number_of_nodes"], 5)
        self.assertEqual(data["configuration"]["topology"], "ring")
        self.assertEqual(data["configuration"]["traffic_pattern"], "hotspot")

        # Check baseline fields
        baseline = data["baseline"]
        for key in ["throughput", "latency", "packet_loss", "congestion", "link_utilization", "reward"]:
            self.assertIn(key, baseline)
            self.assertIsInstance(baseline[key], (int, float))

        # Check PPO fields
        ppo = data["ppo"]
        for key in ["throughput", "latency", "packet_loss", "congestion", "link_utilization", "reward"]:
            self.assertIn(key, ppo)
            self.assertIsInstance(ppo[key], (int, float))

        # Check improvement metrics
        improvement = data["improvement"]
        for key in ["throughput_percent", "latency_percent", "packet_loss_reduction_percent", "reward_percent"]:
            self.assertIn(key, improvement)
            self.assertIsInstance(improvement[key], (int, float))

        # Check link details
        self.assertEqual(len(data["links"]), 5)
        self.assertEqual(len(data["link_weights"]), 5)
        first_link = data["links"][0]
        self.assertIn("traffic_baseline", first_link)
        self.assertIn("traffic_ppo", first_link)
        self.assertIn("utilization_baseline", first_link)
        self.assertIn("utilization_ppo", first_link)
        self.assertIn("weight", first_link)

    def test_optimize_invalid_topology(self) -> None:
        payload = {
            "number_of_nodes": 5,
            "topology": "unsupported_hypercube",
            "link_capacity": 10.0,
            "traffic_pattern": "hotspot",
        }
        response = self.client.post("/optimize", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Unsupported topology", response.json()["detail"])

    def test_optimize_invalid_traffic_pattern(self) -> None:
        payload = {
            "number_of_nodes": 5,
            "topology": "ring",
            "link_capacity": 10.0,
            "traffic_pattern": "invalid_random_burst",
        }
        response = self.client.post("/optimize", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Unsupported traffic pattern", response.json()["detail"])

    def test_optimize_invalid_node_count(self) -> None:
        payload = {
            "number_of_nodes": 1,  # ge=2 constraint
            "topology": "ring",
            "link_capacity": 10.0,
            "traffic_pattern": "hotspot",
        }
        response = self.client.post("/optimize", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_optimize_missing_model_returns_404(self) -> None:
        payload = {
            "number_of_nodes": 19,  # no model trained for 19 nodes
            "topology": "star",
            "link_capacity": 10.0,
            "traffic_pattern": "hotspot",
        }
        response = self.client.post("/optimize", json=payload)
        self.assertEqual(response.status_code, 404)
        self.assertIn("No trained PPO model found", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
