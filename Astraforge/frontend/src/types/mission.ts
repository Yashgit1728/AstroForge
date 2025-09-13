export interface Mission {
  id: string;
  name: string;
  description: string;
  objectives: string[];
  spacecraft_config: SpacecraftConfig;
  trajectory: TrajectoryPlan;
  timeline: MissionTimeline;
  constraints: MissionConstraints;
  created_at: string;
  user_id?: string;
}

export interface SpacecraftConfig {
  vehicle_type: string;
  mass_kg: number;
  fuel_capacity_kg: number;
  thrust_n: number;
  specific_impulse_s: number;
  payload_mass_kg: number;
}

export interface TrajectoryPlan {
  launch_window: DateRange;
  departure_body: string;
  target_body: string;
  transfer_type: string;
  maneuvers: Maneuver[];
  total_delta_v: number;
}

export interface DateRange {
  start: string;
  end: string;
}

export interface Maneuver {
  id: string;
  name: string;
  delta_v: number;
  timestamp: string;
  description: string;
}

export interface MissionTimeline {
  total_duration_days: number;
  phases: MissionPhase[];
}

export interface MissionPhase {
  name: string;
  start_day: number;
  duration_days: number;
  description: string;
}

export interface MissionConstraints {
  max_delta_v: number;
  max_duration_days: number;
  max_mass_kg: number;
  required_capabilities: string[];
}

export interface SimulationResult {
  mission_id: string;
  success_probability: number;
  total_duration_days: number;
  fuel_consumption_kg: number;
  cost_estimate_usd: number;
  risk_factors: RiskFactor[];
  performance_metrics: Record<string, number>;
}

export interface RiskFactor {
  category: string;
  description: string;
  probability: number;
  impact: string;
}