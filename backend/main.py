import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rl.agent import NetworkPPOAgent
from rl.environment import NetworkEnv
from simulation.engine import SUPPORTED_TOPOLOGIES, run_configured_simulation
from simulation.metrics import calculate_metrics
from simulation.simulator import simulate

MODELS_DIR = ROOT / "models"
VALID_PATTERNS = ("hotspot", "asymmetric", "uniform")

# In-memory cache to prevent redundant disk I/O on repeated requests
_MODEL_CACHE: dict[str, NetworkPPOAgent] = {}

app = FastAPI(title="AI Network Optimization API")

# Next.js runs locally on port 3000 by default.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SimulationRequest(BaseModel):
    number_of_nodes: int = Field(ge=1)
    topology: str
    link_capacity: float = Field(gt=0)
    traffic_load: float = Field(ge=0)


class OptimizeRequest(BaseModel):
    number_of_nodes: int = Field(default=5, ge=2, le=50)
    topology: str = Field(default="ring")
    link_capacity: float = Field(default=10.0, gt=0)
    traffic_pattern: str = Field(default="hotspot")


def _find_model_path(topology: str, number_of_nodes: int, traffic_pattern: str) -> Path | None:
    """Find the best matching trained PPO model file."""
    pattern_key = traffic_pattern.strip().lower()
    norm_pattern = "hotspot" if pattern_key in ("hotspot", "asymmetric") else pattern_key

    candidate_files = [
        MODELS_DIR / f"ppo_{topology}_{number_of_nodes}nodes_{norm_pattern}.zip",
        MODELS_DIR / f"ppo_{topology}_{number_of_nodes}nodes.zip",
    ]

    for path in candidate_files:
        if path.exists():
            return path
    return None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/simulate")
def run_simulation(config: SimulationRequest):
    try:
        network, demands, _result, metrics = run_configured_simulation(
            number_of_nodes=config.number_of_nodes,
            topology=config.topology,
            link_capacity=config.link_capacity,
            traffic_load=config.traffic_load,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return {
        "config": {
            "number_of_nodes": config.number_of_nodes,
            "topology": config.topology.strip().lower(),
            "link_capacity": config.link_capacity,
            "traffic_load": config.traffic_load,
        },
        "demand_count": len(demands),
        "node_count": len(network.get_nodes()),
        "link_count": len(network.get_links()),
        "metrics": metrics.to_dict(),
        "supported_topologies": list(SUPPORTED_TOPOLOGIES),
    }


@app.post("/optimize")
def optimize_network(config: OptimizeRequest):
    """Run PPO optimization on the specified network and compare with static shortest path."""
    topology = config.topology.strip().lower()
    pattern = config.traffic_pattern.strip().lower()

    # 1. Input validations
    if topology not in SUPPORTED_TOPOLOGIES:
        supported = ", ".join(SUPPORTED_TOPOLOGIES)
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported topology '{config.topology}'. Supported topologies: {supported}",
        )

    if pattern not in VALID_PATTERNS:
        supported_patterns = ", ".join(["hotspot", "uniform"])
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported traffic pattern '{config.traffic_pattern}'. Supported patterns: {supported_patterns}",
        )

    # 2. Locate trained PPO model
    model_path = _find_model_path(topology, config.number_of_nodes, pattern)
    if model_path is None or not model_path.exists():
        available = [f.name for f in MODELS_DIR.glob("*.zip")] if MODELS_DIR.exists() else []
        raise HTTPException(
            status_code=404,
            detail=(
                f"No trained PPO model found for topology '{topology}' with {config.number_of_nodes} nodes "
                f"and pattern '{pattern}'. Available models: {available}"
            ),
        )

    # 3. Create NetworkEnv with the requested configuration
    try:
        env = NetworkEnv(
            number_of_nodes=config.number_of_nodes,
            topology=topology,
            link_capacity=config.link_capacity,
            traffic_pattern=pattern,
            obs_mode="vector",
        )
        obs, _info = env.reset()
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    # 4. Load PPO Agent (cached)
    cache_key = str(model_path.resolve())
    if cache_key not in _MODEL_CACHE:
        try:
            _MODEL_CACHE[cache_key] = NetworkPPOAgent.load(model_path, env=env)
        except Exception as error:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load trained PPO model from {model_path.name}: {error}",
            ) from error

    agent = _MODEL_CACHE[cache_key]

    # 5. Obtain PPO routing action (link weights)
    try:
        link_weights_list = agent.predict_weights(obs, deterministic=True)
        link_weights_dict = env._parse_action(link_weights_list)
    except Exception as error:
        raise HTTPException(
            status_code=500, detail=f"Failed to compute PPO routing weights: {error}"
        ) from error

    # 6. Run simulator with PPO link weights
    ppo_result = simulate(env.network, env.demands, link_weights=link_weights_dict)
    ppo_metrics = calculate_metrics(env.network, ppo_result)
    ppo_reward = env._calculate_reward(ppo_metrics)

    # 7. Run simulator with static shortest path (all weights = 1.0)
    static_result = simulate(env.network, env.demands, link_weights=None)
    static_metrics = calculate_metrics(env.network, static_result)
    static_reward = env._calculate_reward(static_metrics)

    # 8. Compute relative improvements
    t_diff = ppo_metrics.throughput - static_metrics.throughput
    t_pct = (t_diff / static_metrics.throughput * 100.0) if static_metrics.throughput > 0 else 0.0

    l_diff = static_metrics.latency - ppo_metrics.latency
    l_pct = (l_diff / static_metrics.latency * 100.0) if static_metrics.latency > 0 else 0.0

    loss_diff = static_metrics.packet_loss - ppo_metrics.packet_loss
    loss_pct = (loss_diff / static_metrics.packet_loss * 100.0) if static_metrics.packet_loss > 0 else 0.0

    r_diff = ppo_reward - static_reward
    r_pct = (r_diff / abs(static_reward) * 100.0) if abs(static_reward) > 0 else 0.0

    # 9. Format links and weights details
    links = env.network.get_links() if env.network else []
    link_weights_output = []
    links_output = []

    for link in links:
        key = (link.source, link.destination)
        w = round(link_weights_dict.get(key, 1.0), 4) if link_weights_dict else 1.0
        traffic_base = round(static_result.traffic_on_link(link), 4)
        traffic_ppo = round(ppo_result.traffic_on_link(link), 4)
        util_base = round(traffic_base / link.capacity, 4) if link.capacity > 0 else 0.0
        util_ppo = round(traffic_ppo / link.capacity, 4) if link.capacity > 0 else 0.0

        link_weights_output.append({
            "source": link.source,
            "destination": link.destination,
            "weight": w,
        })
        links_output.append({
            "source": link.source,
            "destination": link.destination,
            "capacity": link.capacity,
            "latency": link.latency,
            "traffic_baseline": traffic_base,
            "traffic_ppo": traffic_ppo,
            "utilization_baseline": util_base,
            "utilization_ppo": util_ppo,
            "congested_baseline": util_base > 1.0,
            "congested_ppo": util_ppo > 1.0,
            "weight": w,
        })

    return {
        "status": "success",
        "configuration": {
            "number_of_nodes": config.number_of_nodes,
            "topology": topology,
            "link_capacity": config.link_capacity,
            "traffic_pattern": pattern,
        },
        "baseline": {
            "throughput": static_metrics.throughput,
            "latency": static_metrics.latency,
            "packet_loss": static_metrics.packet_loss,
            "congestion": static_metrics.congestion,
            "link_utilization": static_metrics.link_utilization,
            "reward": round(static_reward, 4),
        },
        "ppo": {
            "throughput": ppo_metrics.throughput,
            "latency": ppo_metrics.latency,
            "packet_loss": ppo_metrics.packet_loss,
            "congestion": ppo_metrics.congestion,
            "link_utilization": ppo_metrics.link_utilization,
            "reward": round(ppo_reward, 4),
        },
        "improvement": {
            "throughput_percent": round(t_pct, 2),
            "latency_percent": round(l_pct, 2),
            "packet_loss_reduction_percent": round(loss_pct, 2),
            "reward_percent": round(r_pct, 2),
        },
        "link_weights": link_weights_output,
        "links": links_output,
    }
