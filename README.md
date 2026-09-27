# AI Network Optimization

This project uses **reinforcement learning (RL)** to help a computer network make better routing and resource decisions. An RL agent learns from a simulated network: it tries actions, sees the results (such as delay or congestion), and improves over time.

This repository is in an early phase. The folders below describe how the system will be organized. Application code, training, and the simulator will be added in later phases.

## High-level architecture

```
┌─────────────┐     REST API      ┌─────────────┐
│  frontend   │ ◄──────────────► │  backend    │
│  (Next.js)  │                   │  (FastAPI)  │
└─────────────┘                   └──────┬──────┘
                                         │
                          ┌──────────────┼──────────────┐
                          │                             │
                          ▼                             ▼
                   ┌─────────────┐               ┌─────────────┐
                   │     rl      │               │ simulation  │
                   │  (agent)    │               │  (network)  │
                   └─────────────┘               └─────────────┘
```

1. The **frontend** is the user interface. You will use it to view the network and results.
2. The **backend** is a REST API. It connects the frontend to the RL system and the simulator.
3. The **simulation** models a network (nodes, links, traffic, and metrics).
4. The **rl** package will contain the learning environment, agent, training, and evaluation.
5. The backend talks to both the RL system and the simulation so the UI does not need to know those internals.

**Note:** This project will use reinforcement learning for network optimization. The agent will interact with the simulated network to learn policies that improve performance (for example, lower latency or better load balance).

## Purpose of each directory

| Directory     | Purpose |
|---------------|---------|
| `frontend/`   | Next.js + TypeScript + Tailwind CSS. User interface and visualization. |
| `backend/`    | Python + FastAPI. REST API between the frontend, RL system, and simulation. |
| `rl/`         | Reinforcement learning environment, agent, training, and evaluation. Implementation will be added later. |
| `simulation/` | Network topology, nodes, traffic, metrics, and simulator. Implementation will be added later. |
| `docs/`       | Project documentation. |

## Current status

Phase 1 is project structure only. Packages are not installed yet, and there is no Next.js app, FastAPI app, RL code, or simulator code in this step.
