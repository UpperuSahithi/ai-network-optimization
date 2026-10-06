"""Unit tests for network simulator, routing edge cases, and metric calculations."""

import unittest

from simulation.engine import run_configured_simulation
from simulation.metrics import calculate_metrics
from simulation.network import Network
from simulation.simulator import simulate
from simulation.topology import create_line_topology
from simulation.traffic import TrafficDemand


class SimulatorTests(unittest.TestCase):
    def test_simulate_empty_demands(self) -> None:
        network = create_line_topology(node_count=3, capacity=10.0, latency=1.0)
        result = simulate(network, [])
        self.assertEqual(len(result.routed_demands), 0)
        for traffic in result.link_traffic.values():
            self.assertEqual(traffic, 0.0)

        metrics = calculate_metrics(network, result)
        self.assertEqual(metrics.throughput, 0.0)
        self.assertEqual(metrics.packet_loss, 0.0)
        self.assertEqual(metrics.congestion, 0.0)
        self.assertEqual(metrics.link_utilization, 0.0)

    def test_single_demand_routing(self) -> None:
        network = create_line_topology(node_count=3, capacity=10.0, latency=2.0)
        demand = TrafficDemand(source=0, destination=2, volume=5.0)
        result = simulate(network, [demand])

        self.assertEqual(len(result.routed_demands), 1)
        self.assertEqual(result.routed_demands[0].path, [0, 1, 2])

        metrics = calculate_metrics(network, result)
        self.assertEqual(metrics.throughput, 5.0)
        self.assertEqual(metrics.packet_loss, 0.0)
        self.assertEqual(metrics.latency, 4.0)  # 2 hops * latency 2.0
        self.assertEqual(metrics.congestion, 0.0)

    def test_disconnected_node_demand(self) -> None:
        network = Network()
        network.add_node(0)
        network.add_node(1)
        network.add_node(2)
        # Link only between 0 and 1, node 2 is isolated
        network.add_link(0, 1, capacity=10.0, latency=1.0)

        demand = TrafficDemand(source=0, destination=2, volume=5.0)
        result = simulate(network, [demand])

        self.assertIsNone(result.routed_demands[0].path)
        metrics = calculate_metrics(network, result)
        self.assertEqual(metrics.throughput, 0.0)
        self.assertEqual(metrics.packet_loss, 1.0)

    def test_congested_link_metrics(self) -> None:
        network = create_line_topology(node_count=2, capacity=10.0, latency=1.0)
        # Offered volume is 20.0 on a capacity of 10.0
        demand = TrafficDemand(source=0, destination=1, volume=20.0)
        result = simulate(network, [demand])

        metrics = calculate_metrics(network, result)
        self.assertEqual(metrics.throughput, 10.0)  # capped by capacity
        self.assertEqual(metrics.packet_loss, 0.5)  # 10 delivered / 20 offered = 0.5 loss
        self.assertEqual(metrics.congestion, 1.0)  # 1 link out of 1 is congested
        self.assertGreater(metrics.latency, 1.0)  # latency scaled by utilization (2.0)

    def test_run_configured_simulation_all_topologies(self) -> None:
        topologies = ["line", "bus", "star", "ring", "mesh"]
        for topo in topologies:
            with self.subTest(topology=topo):
                net, demands, res, metrics = run_configured_simulation(
                    number_of_nodes=4,
                    topology=topo,
                    link_capacity=10.0,
                    traffic_load=15.0,
                )
                self.assertEqual(len(net.get_nodes()), 4)
                self.assertIsNotNone(metrics)
                self.assertGreaterEqual(metrics.throughput, 0.0)
                self.assertGreaterEqual(metrics.packet_loss, 0.0)
                self.assertLessEqual(metrics.packet_loss, 1.0)


if __name__ == "__main__":
    unittest.main()
