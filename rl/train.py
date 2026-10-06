"""Training and Evaluation Script for AI Network Optimization.

Trains a lightweight PPO agent on NetworkEnv and benchmarks performance against:
1. Static Shortest Path (uniform 1.0 weights, standard BFS/Dijkstra)
2. Random Weights (random continuous weights sampled from the action space)
3. PPO Agent (trained continuous policy)

Evaluates on actual simulator metrics (throughput, latency, packet loss, congestion,
link utilization, reward) and reports percentage improvements relative to the static baseline.
"""

import argparse
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rl.agent import NetworkPPOAgent, create_agent
from rl.baseline import RandomBaseline, StaticBaseline, evaluate_policy
from rl.environment import NetworkEnv

DEFAULT_TIMESTEPS = 10000
DEFAULT_MODEL_DIR = "models"


def run_experiment(
    total_timesteps: int = DEFAULT_TIMESTEPS,
    number_of_nodes: int = 5,
    topology: str = "ring",
    link_capacity: float = 10.0,
    traffic_load: float = 10.0,
    traffic_pattern: str = "hotspot",
    max_steps: int = 50,
    eval_episodes: int = 5,
    model_dir: str = DEFAULT_MODEL_DIR,
    seed: int = 42,
) -> dict[str, Any]:
    """Train PPO and evaluate against Static and Random baselines."""
    print("=" * 80)
    print("  AI NETWORK OPTIMIZATION: PPO TRAINING & EVALUATION BENCHMARK")
    print("=" * 80)
    print(f"Topology: {topology.upper()} ({number_of_nodes} nodes) | Pattern: {traffic_pattern.upper()}")
    print(f"Traffic load parameter: {traffic_load} | Link capacity: {link_capacity}")
    print(f"PPO Budget: {total_timesteps:,} timesteps | Eval episodes: {eval_episodes} | Seed: {seed}")
    print("-" * 80)

    # 1. Instantiate shared environment for all evaluations
    env = NetworkEnv(
        number_of_nodes=number_of_nodes,
        topology=topology,
        link_capacity=link_capacity,
        traffic_load=traffic_load,
        traffic_pattern=traffic_pattern,
        max_steps=max_steps,
        obs_mode="vector",
    )

    # 2. Benchmark Baseline 1: Static Shortest Path
    print("\n[1/3] Evaluating Static Shortest Path (BFS, all weights = 1.0)...")
    static_baseline = StaticBaseline(action_dim=env.action_dim)
    static_results = evaluate_policy(env, static_baseline, episodes=eval_episodes)

    # 3. Benchmark Baseline 2: Random Weights
    print("[2/3] Evaluating Random Weights Baseline...")
    random_baseline = RandomBaseline(action_dim=env.action_dim, seed=seed)
    random_results = evaluate_policy(env, random_baseline, episodes=eval_episodes)

    # 4. Train PPO Agent
    print(f"[3/3] Training PPO Agent for {total_timesteps:,} timesteps...")
    agent = create_agent(env, seed=seed)
    agent.train(total_timesteps=total_timesteps)

    # 5. Save Model
    save_dest = Path(model_dir) / f"ppo_{topology}_{number_of_nodes}nodes_{traffic_pattern}.zip"
    saved_file = agent.save(save_dest)
    print(f"Model saved to: {saved_file}")

    # 6. Evaluate Trained PPO Agent
    print("Evaluating trained PPO Agent...")
    ppo_results = evaluate_policy(env, agent, episodes=eval_episodes)

    # 7. Compare results against Static Baseline
    comparison: dict[str, dict[str, Any]] = {}
    metrics = ["throughput", "latency", "packet_loss", "congestion", "link_utilization", "reward"]

    for m in metrics:
        s_val = static_results[m]
        r_val = random_results[m]
        p_val = ppo_results[m]
        diff = p_val - s_val

        # Higher is better for throughput and reward; lower is better for latency, packet loss, congestion
        if m in ("throughput", "reward"):
            improved = diff > 1e-4
            worsened = diff < -1e-4
            pct_change = ((diff / abs(s_val)) * 100.0) if abs(s_val) > 1e-6 else 0.0
        elif m in ("latency", "packet_loss", "congestion"):
            improved = diff < -1e-4
            worsened = diff > 1e-4
            pct_change = ((-diff / abs(s_val)) * 100.0) if abs(s_val) > 1e-6 else 0.0
        else:  # link_utilization (context-dependent)
            improved = False
            worsened = False
            pct_change = ((diff / abs(s_val)) * 100.0) if abs(s_val) > 1e-6 else 0.0

        status = "IMPROVED" if improved else ("WORSENED" if worsened else "NEUTRAL / BALANCED")
        comparison[m] = {
            "static": s_val,
            "random": r_val,
            "ppo": p_val,
            "difference": round(diff, 4),
            "pct_improvement": round(pct_change, 2),
            "status": status,
        }

    # 8. Print Comparative Table
    print("\n" + "=" * 80)
    print(f"{'METRIC':<18} | {'STATIC (BFS)':<12} | {'RANDOM':<10} | {'PPO AGENT':<10} | {'IMPROVEMENT %':<14} | {'STATUS':<10}")
    print("-" * 80)
    for m in metrics:
        s = f"{comparison[m]['static']:.4f}"
        r = f"{comparison[m]['random']:.4f}"
        p = f"{comparison[m]['ppo']:.4f}"
        pct = f"{comparison[m]['pct_improvement']:+.2f}%"
        st = comparison[m]["status"]
        print(f"{m.replace('_', ' ').capitalize():<18} | {s:<12} | {r:<10} | {p:<10} | {pct:<14} | {st:<10}")
    print("=" * 80)

    return {
        "static": static_results,
        "random": random_results,
        "ppo": ppo_results,
        "comparison": comparison,
        "saved_model": saved_file,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Train and evaluate PPO agent for Network Optimization.")
    parser.add_argument("--timesteps", type=int, default=DEFAULT_TIMESTEPS, help="Training timesteps budget")
    parser.add_argument("--nodes", type=int, default=5, help="Number of nodes in the network")
    parser.add_argument("--topology", type=str, default="ring", help="Network topology (ring, line, star, mesh, bus)")
    parser.add_argument("--capacity", type=float, default=10.0, help="Capacity of each link")
    parser.add_argument("--load", type=float, default=10.0, help="Traffic volume parameter")
    parser.add_argument("--pattern", type=str, default="hotspot", choices=["uniform", "hotspot", "asymmetric"], help="Traffic pattern")
    parser.add_argument("--max-steps", type=int, default=50, help="Max steps per episode")
    parser.add_argument("--eval-episodes", type=int, default=5, help="Number of evaluation episodes")
    parser.add_argument("--model-dir", type=str, default=DEFAULT_MODEL_DIR, help="Directory to save trained model")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()
    run_experiment(
        total_timesteps=args.timesteps,
        number_of_nodes=args.nodes,
        topology=args.topology,
        link_capacity=args.capacity,
        traffic_load=args.load,
        traffic_pattern=args.pattern,
        max_steps=args.max_steps,
        eval_episodes=args.eval_episodes,
        model_dir=args.model_dir,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
