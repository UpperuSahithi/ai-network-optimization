export type TopologyType = "ring" | "mesh" | "line" | "star" | "bus";
export type TrafficPatternType = "hotspot" | "uniform";

export interface HealthResponse {
  status: string;
}

export interface SimulationRequest {
  number_of_nodes: number;
  topology: TopologyType;
  link_capacity: number;
  traffic_load: number;
}

export interface SimulationLink {
  source: number;
  destination: number;
  traffic: number;
  capacity: number;
  utilization: number;
  congested: boolean;
  latency: number;
}

export interface SimulationMetrics {
  throughput: number;
  latency: number;
  packet_loss: number;
  congestion: number;
  link_utilization: number;
  links?: SimulationLink[];
}

export interface SimulationResponse {
  config: {
    number_of_nodes: number;
    topology: TopologyType;
    link_capacity: number;
    traffic_load: number;
  };
  demand_count: number;
  node_count: number;
  link_count: number;
  metrics: SimulationMetrics;
  supported_topologies: string[];
}

export interface OptimizeRequest {
  number_of_nodes: number;
  topology: TopologyType;
  link_capacity: number;
  traffic_pattern: TrafficPatternType;
}

export interface LinkWeightItem {
  source: number;
  destination: number;
  weight: number;
}

export interface LinkItem {
  source: number;
  destination: number;
  capacity: number;
  latency: number;
  traffic_baseline: number;
  traffic_ppo: number;
  utilization_baseline: number;
  utilization_ppo: number;
  congested_baseline: boolean;
  congested_ppo: boolean;
  weight: number;
}

export interface OptimizationMetrics {
  throughput: number;
  latency: number;
  packet_loss: number;
  congestion: number;
  link_utilization: number;
  reward?: number;
}

export interface ImprovementMetrics {
  throughput_percent: number;
  latency_percent: number;
  packet_loss_reduction_percent: number;
  reward_percent: number;
}

export interface OptimizeResponse {
  status: "success";
  configuration: {
    number_of_nodes: number;
    topology: TopologyType;
    link_capacity: number;
    traffic_pattern: TrafficPatternType;
  };
  baseline: OptimizationMetrics;
  ppo: OptimizationMetrics;
  improvement: ImprovementMetrics;
  link_weights: LinkWeightItem[];
  links: LinkItem[];
}
