import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulation.engine import SUPPORTED_TOPOLOGIES, run_configured_simulation

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
